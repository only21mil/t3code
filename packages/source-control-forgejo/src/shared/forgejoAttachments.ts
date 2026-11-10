import type { SourceControlMediaUrl } from "@t3tools/source-control-core/shared/definition";

const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";

/**
 * Forgejo serves an upload at `/attachments/<uuid>` below its mount, or below a repository. No
 * Forgejo owner name starts with `_`, which leaves `_apis/` paths, such as Azure DevOps
 * attachments, to their own host.
 */
const ATTACHMENT_PATH = new RegExp(`^(?:/[^/_][^/]*)*/attachments/(${UUID})$`, "iu");

/**
 * Forgejo's editor writes a pasted upload as a link relative to the server, `/attachments/<uuid>`,
 * which means nothing once the body is shown anywhere else.
 */
const RELATIVE_ATTACHMENT_URL = new RegExp(`^/?(attachments/${UUID})$`, "iu");

/** The server's mount: everything in a repository's path before `/<owner>/<repo>`. */
const REPOSITORY_PATH = /^(.*)\/[^/]+\/[^/]+\/?$/u;

/** Forgejo serves an upload with the visibility of the repository it was posted in. */
export function forgejoMediaUrl(url: URL): SourceControlMediaUrl | null {
  if (url.protocol !== "https:") return null;
  const uuid = ATTACHMENT_PATH.exec(url.pathname)?.[1];
  return uuid === undefined ? null : { fetchUrl: `${url.origin}${url.pathname}`, fileName: uuid };
}

export function resolveForgejoAttachmentUrl(url: string, repositoryUrl: string): string | null {
  const path = RELATIVE_ATTACHMENT_URL.exec(url)?.[1];
  if (path === undefined) return null;
  const repository = URL.parse(repositoryUrl);
  const mount = repository ? REPOSITORY_PATH.exec(repository.pathname)?.[1] : undefined;
  return repository && mount !== undefined ? `${repository.origin}${mount}/${path}` : null;
}
