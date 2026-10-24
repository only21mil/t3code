import { isValidElement, type ReactNode } from "react";
import { describe, expect, it, vi } from "vite-plus/test";

const state = vi.hoisted(() => ({
  refreshes: 0,
  creates: [] as string[],
  runs: [] as unknown[],
  refreshResult: null as ReadonlyArray<{ name: string; isRemote: boolean }> | null,
  pending: Promise.resolve() as Promise<unknown>,
}));

vi.mock("react", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react")>()),
  useCallback: <T,>(callback: T) => callback,
  useMemo: <T,>(factory: () => T) => factory(),
}));
vi.mock("react-native", () => ({
  Platform: { OS: "ios" },
  useWindowDimensions: () => ({ height: 800, width: 400 }),
  ScrollView: "ScrollView",
  View: "View",
}));
vi.mock("@react-navigation/native", () => ({
  StackActions: { replace: () => null },
  useNavigation: () => ({ dispatch: () => undefined, goBack: () => undefined }),
}));
vi.mock("react-native-safe-area-context", () => ({
  useSafeAreaInsets: () => ({ bottom: 0 }),
}));
vi.mock("../../../components/ui/AndroidScreenHeader", () => ({
  AndroidSheetHeader: "AndroidSheetHeader",
}));
vi.mock("../../../components/ui/ScreenContent", () => ({ ScreenContent: "ScreenContent" }));
vi.mock("../../../native/StackHeader", () => ({
  NativeStackScreenOptions: "NativeStackScreenOptions",
}));
vi.mock("../../../components/ui/AppText", () => ({ AppText: "Text" }));
vi.mock("./gitSheetComponents", () => ({ SheetActionButton: "SheetActionButton" }));
vi.mock("../../../state/use-selected-thread-git-state", () => ({
  useSelectedThreadGitState: () => ({ selectedThreadBranches: [] }),
}));
vi.mock("../../../state/use-selected-thread-git-actions", () => ({
  useSelectedThreadGitActions: () => ({
    canWriteSourceControl: true,
    canChangeThreadBranch: true,
    refreshSelectedThreadBranches: () => {
      state.refreshes++;
      return (state.pending = Promise.resolve(state.refreshResult));
    },
    onCreateSelectedThreadBranch: (name: string) => {
      state.creates.push(name);
      return (state.pending = Promise.resolve({ refName: name }));
    },
    onRunSelectedThreadGitAction: (input: unknown) => {
      state.runs.push(input);
      return (state.pending = Promise.resolve());
    },
  }),
}));

import { GitConfirmSheet } from "./GitConfirmSheet";

type ControlProps = { label?: string; onPress?: () => unknown; children?: ReactNode };

function findControl(node: ReactNode, label: string): ControlProps | null {
  if (Array.isArray(node)) {
    for (const child of node) {
      const control = findControl(child, label);
      if (control) return control;
    }
    return null;
  }
  if (!isValidElement<ControlProps>(node)) return null;
  if (node.props.label === label) return node.props;
  return findControl(node.props.children, label);
}

async function pressFeatureBranch() {
  state.refreshes = 0;
  state.creates = [];
  state.runs = [];
  const sheet = GitConfirmSheet({
    route: {
      params: {
        environmentId: "environment",
        threadId: "thread",
        confirmAction: "push",
        branchName: "main",
      },
    },
  });
  const press = findControl(sheet, "Feature branch & continue")?.onPress;
  if (!press) throw new Error("Missing feature-branch action");
  press();
  // The sheet awaits each action before the test does, so its continuation runs first.
  await state.pending; // ref refresh
  await state.pending; // branch creation, when the refresh returned refs
}

describe("feature-branch confirmation", () => {
  it("stops before branch creation and the git action when the ref refresh fails", async () => {
    state.refreshResult = null;
    await pressFeatureBranch();

    expect(state.refreshes).toBe(1);
    expect(state.creates).toEqual([]);
    expect(state.runs).toEqual([]);
  });

  it("names the branch from refreshed refs, then runs the action", async () => {
    state.refreshResult = [{ name: "feature/update", isRemote: false }];
    await pressFeatureBranch();

    expect(state.creates).toEqual(["feature/update-2"]);
    expect(state.runs).toEqual([{ action: "push" }]);
  });
});
