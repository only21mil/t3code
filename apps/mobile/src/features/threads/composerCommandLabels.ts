import type { ComposerTriggerKind } from "@t3tools/shared/composerTrigger";

export function groupLabel(
  triggerKind: ComposerTriggerKind | null,
  searchesThreads: boolean,
): string | null {
  switch (triggerKind) {
    case "pull-request":
      return "Pull requests";
    case "slash-command":
      return "Commands";
    case "skill":
      return "Skills";
    case "path":
      return searchesThreads ? "Threads and files" : "Files";
    default:
      return null;
  }
}

export function emptyText(
  triggerKind: ComposerTriggerKind | null,
  isLoading: boolean,
  searchesThreads: boolean,
): string {
  if (isLoading) {
    return triggerKind === "path"
      ? searchesThreads
        ? "Searching threads and files…"
        : "Searching files…"
      : "Loading…";
  }
  switch (triggerKind) {
    case "pull-request":
      return "No matching pull requests.";
    case "path":
      return searchesThreads
        ? "No matching threads, files, or folders."
        : "No matching files or folders.";
    case "skill":
      return "No skills found.";
    case "slash-command":
      return "No matching commands.";
    default:
      return "No results.";
  }
}

// File-search errors stay visible beside matching thread rows.
export function commandMenuNotice(input: {
  readonly triggerKind: ComposerTriggerKind | null;
  readonly itemCount: number;
  readonly isLoading: boolean;
  readonly searchesThreads: boolean;
  readonly error?: string | null | undefined;
}): string | null {
  if (input.error != null) return input.error;
  return input.itemCount === 0
    ? emptyText(input.triggerKind, input.isLoading, input.searchesThreads)
    : null;
}
