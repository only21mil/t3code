import * as Option from "effect/Option";

export type JoinPath = (first: string, ...segments: string[]) => string;
export type ResolvePath = (path: string) => string;

function normalizeConfiguredBaseDir(t3Home: Option.Option<string>): Option.Option<string> {
  if (Option.isNone(t3Home)) {
    return Option.none();
  }
  const trimmed = t3Home.value.trim();
  return trimmed.length > 0 ? Option.some(trimmed) : Option.none();
}

// Mirrors the server's resolveBaseDir. The backend runs in a different cwd, so desktop
// passes it an absolute path or the two would read different state directories.
export function resolveDesktopBaseDir(input: {
  readonly homeDirectory: string;
  readonly joinPath: JoinPath;
  readonly resolvePath: ResolvePath;
  readonly t3Home: Option.Option<string>;
}): string {
  return Option.match(normalizeConfiguredBaseDir(input.t3Home), {
    onNone: () => input.joinPath(input.homeDirectory, ".t3"),
    onSome: (configured) => {
      if (configured === "~") {
        return input.resolvePath(input.homeDirectory);
      }
      if (configured.startsWith("~/") || configured.startsWith("~\\")) {
        return input.resolvePath(input.joinPath(input.homeDirectory, configured.slice(2)));
      }
      return input.resolvePath(configured);
    },
  });
}

export function resolveDesktopStateDir(input: {
  readonly baseDir: string;
  readonly isDevelopment: boolean;
  readonly joinPath: JoinPath;
  readonly t3Home: Option.Option<string>;
}): string {
  const useDevSubdir =
    input.isDevelopment && Option.isNone(normalizeConfiguredBaseDir(input.t3Home));
  return input.joinPath(input.baseDir, useDevSubdir ? "dev" : "userdata");
}
