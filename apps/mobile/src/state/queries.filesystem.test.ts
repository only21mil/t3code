import { AuthFilesystemReadScope, EnvironmentId, type AuthSessionState } from "@t3tools/contracts";
import { beforeEach, expect, it, vi } from "vite-plus/test";

const state = vi.hoisted(() => ({
  session: null as Pick<AuthSessionState, "authenticated" | "scopes"> | null,
  sessionError: null as string | null,
  searchError: null as string | null,
  debouncedQuery: null as string | null,
  phase: "connected" as "connected" | "offline",
  sessionAtom: {},
  searchAtom: {},
}));

vi.mock("react", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react")>()),
  useCallback: <A>(callback: A) => callback,
  useEffect: () => {},
  useMemo: <A>(factory: () => A) => factory(),
  // The only useState on this path is useDebouncedValue; a set query holds the settled search.
  useState: <A>(value: A) => [
    state.debouncedQuery === null ? value : { ...value, query: state.debouncedQuery },
    vi.fn(),
  ],
}));
vi.mock("./session", () => ({
  environmentSession: { sessionStateAtom: () => state.sessionAtom },
}));
vi.mock("./presentation", () => ({
  useEnvironmentPresentation: () => ({
    isReady: true,
    presentation: { connection: { phase: state.phase, error: null } },
  }),
}));
vi.mock("./pull-requests", () => ({ composerPullRequests: {} }));
vi.mock("./projects", () => ({
  projectEnvironment: { searchEntries: () => state.searchAtom },
}));
vi.mock("./atom-registry", () => ({ appAtomRegistry: {} }));
vi.mock("./orchestration", () => ({ orchestrationEnvironment: {} }));
vi.mock("./threads", () => ({ useEnvironmentThread: vi.fn() }));
vi.mock("./vcs", () => ({ vcsEnvironment: {} }));
vi.mock("./query", () => ({
  useEnvironmentQuery: (atom: unknown) => ({
    data:
      atom === state.sessionAtom
        ? state.session
        : atom === state.searchAtom
          ? { entries: [{ path: "src/index.ts", kind: "file" }] }
          : null,
    error:
      atom === state.sessionAtom
        ? state.sessionError
        : atom === state.searchAtom
          ? state.searchError
          : null,
    isPending: atom === state.sessionAtom && state.session === null && state.sessionError === null,
    refresh: vi.fn(),
  }),
}));

import { useComposerPathSearch } from "./queries";

const target = {
  environmentId: EnvironmentId.make("test-environment"),
  cwd: "/repo",
  query: "src",
};

beforeEach(() => {
  state.session = null;
  state.sessionError = null;
  state.searchError = null;
  state.debouncedQuery = null;
  state.phase = "connected";
});

it("keeps a file search pending until its grant loads, then shows matches", () => {
  expect(useComposerPathSearch(target)).toMatchObject({
    entries: [],
    error: null,
    isPending: true,
  });
  state.session = { authenticated: true, scopes: [AuthFilesystemReadScope] };
  expect(useComposerPathSearch(target)).toMatchObject({
    entries: [{ path: "src/index.ts", kind: "file" }],
    error: null,
    isPending: false,
  });
});

it("hides a failed file search's error while the next query debounces", () => {
  state.session = { authenticated: true, scopes: [AuthFilesystemReadScope] };
  state.searchError = "File search failed.";
  expect(useComposerPathSearch(target)).toMatchObject({
    error: "File search failed.",
    isPending: false,
  });
  state.debouncedQuery = target.query;
  expect(useComposerPathSearch({ ...target, query: "srcx" })).toMatchObject({
    error: null,
    isPending: true,
  });
});
