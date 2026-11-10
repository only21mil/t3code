import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it, vi } from "vite-plus/test";

import type { MarkdownImageSourceResolver } from "../../native/SelectableMarkdownText";

const mocks = vi.hoisted(() => ({
  project: null as { readonly workspaceRoot: string } | null,
  resolveImageSource: undefined as MarkdownImageSourceResolver | undefined,
  refreshAssetUrl: vi.fn(),
  Passthrough: ({ children }: { children?: unknown }) => children,
}));

vi.mock("react-native", () => ({ View: mocks.Passthrough }));
vi.mock("../../state/entities", () => ({ useProject: () => mocks.project }));
vi.mock("./usePullRequestDiff", () => ({
  pullRequestTarget: (params: { environmentId: string; projectId: string }) => ({
    environmentId: params.environmentId,
    input: { projectId: params.projectId },
  }),
}));
vi.mock("../../state/session", () => ({
  usePreparedConnection: () => ({ _tag: "Some", value: { httpBaseUrl: "https://env.test" } }),
}));
vi.mock("../../state/assets", () => ({
  assetEnvironment: { createUrl: {} },
  refreshAssetUrl: mocks.refreshAssetUrl,
}));
vi.mock("../../state/use-atom-query-runner", () => ({
  useAtomQueryRunner: () => async () => ({ _tag: "Success", value: { url: "/signed" } }),
}));
vi.mock("./PullRequestMedia", async () => {
  const { createContext } = await import("react");
  return {
    PullRequestMedia: () => null,
    PullRequestMediaContext: createContext(null),
    usePullRequestMediaUrl: () => ({ uri: null, unavailable: false }),
  };
});
vi.mock("../../native/useOpenPullRequest", () => ({ useOpenPullRequest: () => vi.fn() }));
vi.mock("../../native/SelectableMarkdownText", () => ({
  SelectableMarkdownText: (props: { resolveImageSource?: MarkdownImageSourceResolver }) => {
    mocks.resolveImageSource = props.resolveImageSource;
    return null;
  },
}));
vi.mock("../files/FileMarkdownPreview", () => ({ useMarkdownPreviewStyles: () => ({}) }));
vi.mock("../../components/ui/FilePreviewGallery", () => ({
  FilePreviewGallery: mocks.Passthrough,
  useFilePreviewGallery: () => (source: unknown) => source,
}));
vi.mock("../../components/ui/FilePreviewModal", () => ({ FilePreviewModal: () => null }));
vi.mock("../threads/ThreadMarkdownImage", () => ({ ThreadMarkdownImageView: () => null }));

import { PullRequestMarkdown, PullRequestMarkdownRepository } from "./PullRequestMarkdown";

const upload = "https://forgejo.test/owner/repo/attachments/0b1f6c2e-4a3d-4c6b-9e2f-7a8b9c0d1e2f";

it("keeps a forge upload pending until its project is known, then loads it", async () => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  mocks.project = null;
  mocks.refreshAssetUrl.mockResolvedValue("https://env.test/signed");
  const root = createRoot(document.createElement("div"));
  const view = () => (
    <PullRequestMarkdownRepository
      changeRequest={{ provider: "forgejo", url: "https://forgejo.test/owner/repo/pulls/1" }}
      params={{
        environmentId: "environment",
        projectId: "project",
        repository: "owner/repo",
        number: 1,
      }}
    >
      <PullRequestMarkdown markdown={`![shot](${upload})`} />
    </PullRequestMarkdownRepository>
  );
  try {
    await act(async () => root.render(view()));
    const image = { href: upload, alt: "shot", title: null };
    await expect(mocks.resolveImageSource!(image)).rejects.toThrow();

    mocks.project = { workspaceRoot: "/repo" };
    await act(async () => root.render(view()));
    await expect(mocks.resolveImageSource!(image)).resolves.toEqual({
      uri: "https://env.test/signed",
    });
  } finally {
    act(() => root.unmount());
  }
});
