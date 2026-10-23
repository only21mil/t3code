import { scopeThreadRef } from "@t3tools/client-runtime/environment";
import { EnvironmentId, ThreadId } from "@t3tools/contracts";
import { describe, expect, it } from "vite-plus/test";

import { useComposerDraftStore } from "../../composerDraftStore";
import { collectInlineContextIds } from "../../lib/composerContextReferences";
import { restoreRewoundMessageDraft } from "./chatViewSend";
import { reconcileAttachmentContextReferences } from "./composerContextUndo";

describe("restoreRewoundMessageDraft", () => {
  it("keeps restored files when the user edits the restored prompt", () => {
    const draftTarget = scopeThreadRef(
      EnvironmentId.make("environment-local"),
      ThreadId.make("thread-rewind-files"),
    );
    const notes = new File(["notes"], "notes.txt", { type: "text/plain" });

    const prompt = restoreRewoundMessageDraft(
      draftTarget,
      {
        text: "summarize this",
        attachments: [
          {
            type: "file",
            id: "attachment-notes",
            name: notes.name,
            mimeType: notes.type,
            sizeBytes: notes.size,
          },
        ],
      },
      [notes],
    );
    const draft = useComposerDraftStore.getState().getComposerDraft(draftTarget);

    // The composer runs this on every prompt edit with the chips the editor still shows.
    const changes = reconcileAttachmentContextReferences({
      referencedContextIds: new Set(collectInlineContextIds(`${prompt} please`)),
      files: draft?.files ?? [],
      images: draft?.images ?? [],
      previewAnnotations: [],
      retained: { files: new Map(), previewAnnotations: new Map() },
    });

    expect(draft?.files.map((file) => file.name)).toEqual(["notes.txt"]);
    expect(changes.filesToRemove).toEqual([]);
  });
});
