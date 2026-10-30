import { ComposerContextRecord, ForwardCompatibleArray } from "@t3tools/contracts";
import * as Schema from "effect/Schema";
import { create } from "zustand";

import {
  PersistedComposerFileAttachment,
  PersistedComposerImageAttachment,
} from "./composerDraftStore";
import { createMemoryStorage, type StateStorage } from "./lib/storage";

export const PROMPT_STASH_STORAGE_KEY = "t3code:prompt-stash:v2";
const LEGACY_PROMPT_STASH_STORAGE_KEY = "t3code:prompt-stash:v1";
const PROMPT_STASH_STORAGE_VERSION = 2;

export const MAX_STASH_ENTRIES = 20;
/**
 * Budget for an entry's serialized attachment payload. localStorage is a
 * ~5MB origin-wide quota shared with the composer draft store, so oversized
 * images are dropped (tracked in `droppedImageNames`) rather than persisted.
 */
export const MAX_STASH_ENTRY_ATTACHMENT_CHARS = 2_700_000;

const StashEntrySchema = Schema.Struct({
  id: Schema.String,
  createdAt: Schema.String,
  prompt: Schema.String,
  attachments: Schema.Array(PersistedComposerImageAttachment),
  files: Schema.optionalKey(Schema.Array(PersistedComposerFileAttachment)),
  droppedImageNames: Schema.Array(Schema.String),
  unreadableImageNames: Schema.optionalKey(Schema.Array(Schema.String)),
  pendingImageCount: Schema.optionalKey(Schema.Number),
  records: Schema.optionalKey(ForwardCompatibleArray(ComposerContextRecord)),
});
export type PromptStashEntry = typeof StashEntrySchema.Type;

const PersistedPromptStashState = Schema.Struct({
  entries: Schema.Array(StashEntrySchema),
});
type PersistedPromptStashState = typeof PersistedPromptStashState.Type;

const decodePersistedPromptStashState = Schema.decodeUnknownSync(PersistedPromptStashState);

/**
 * How long a stash's image encode may plausibly run. `compressImageForStash`
 * re-encodes images one at a time, up to the composer's attachment limit, with
 * several quality and scale passes each, so this sits well past the worst case.
 */
const PENDING_IMAGE_ENCODE_WINDOW_MS = 15 * 60 * 1000;

/**
 * `pendingImageCount` is cleared only by the encode loop of the tab that
 * stashed the entry, and that loop does not survive a reload. An entry still
 * pending past the encode window was orphaned by a closed tab or a crash
 * mid-encode, so a loading tab settles it — otherwise it would be stuck
 * showing "saving…" and refuse to restore forever. A younger entry may still
 * be encoding in another open tab; settling it would let it restore without
 * its images and make that tab's finalize find nothing to attach to.
 * Returns null when nothing settled.
 */
function settleOrphanedPendingImages(
  entries: ReadonlyArray<PromptStashEntry>,
  now: number,
): ReadonlyArray<PromptStashEntry> | null {
  let settledAny = false;
  const settled = entries.map((entry) => {
    if (!entry.pendingImageCount) return entry;
    const startedAt = Date.parse(entry.createdAt);
    if (!Number.isNaN(startedAt) && now - startedAt <= PENDING_IMAGE_ENCODE_WINDOW_MS) {
      return entry;
    }
    settledAny = true;
    const lostCount = entry.pendingImageCount;
    return {
      ...entry,
      pendingImageCount: 0,
      unreadableImageNames: [
        ...(entry.unreadableImageNames ?? []),
        ...Array.from(
          { length: lostCount },
          (_, index) => `image ${index + 1} (not saved before reload)`,
        ),
      ],
    };
  });
  return settledAny ? settled : null;
}

export function partitionStashAttachments(
  attachments: ReadonlyArray<PersistedComposerImageAttachment>,
): {
  kept: PersistedComposerImageAttachment[];
  droppedNames: string[];
} {
  const kept: PersistedComposerImageAttachment[] = [];
  const droppedNames: string[] = [];
  let usedChars = 0;
  for (const attachment of attachments) {
    if (usedChars + attachment.dataUrl.length > MAX_STASH_ENTRY_ATTACHMENT_CHARS) {
      droppedNames.push(attachment.name);
      continue;
    }
    usedChars += attachment.dataUrl.length;
    kept.push(attachment);
  }
  return { kept, droppedNames };
}

/**
 * Reading the `localStorage` property itself can throw `SecurityError` when
 * storage is blocked by policy or the page is a sandboxed iframe — so the
 * access has to be guarded, not just the get/set calls on it.
 */
function resolveBaseStorage(): { storage: StateStorage; durable: boolean } {
  try {
    if (typeof localStorage !== "undefined") {
      return { storage: localStorage, durable: true };
    }
  } catch {}
  return { storage: createMemoryStorage(), durable: false };
}

const { storage: baseStashStorage, durable: storageIsDurable } = resolveBaseStorage();

interface StashEntryImages {
  attachments: ReadonlyArray<PersistedComposerImageAttachment>;
  droppedImageNames: ReadonlyArray<string>;
  unreadableImageNames: ReadonlyArray<string>;
}

/**
 * Finalized images storage refused (quota), by entry id. Storage gets the
 * entry with those images listed as dropped, so a reload or another tab
 * reports them missing; this tab keeps them until it reloads, as the stash
 * toast promises.
 */
const unsavedImagesByEntryId = new Map<string, StashEntryImages>();

function withUnsavedImages(entry: PromptStashEntry): PromptStashEntry {
  const images = unsavedImagesByEntryId.get(entry.id);
  return images ? { ...entry, ...images, pendingImageCount: 0 } : entry;
}

function withoutUnsavedImages(entry: PromptStashEntry): PromptStashEntry {
  const images = unsavedImagesByEntryId.get(entry.id);
  if (!images) return entry;
  return {
    ...entry,
    attachments: [],
    droppedImageNames: [
      ...images.droppedImageNames,
      ...images.attachments.map((attachment) => attachment.name),
    ],
    unreadableImageNames: images.unreadableImageNames,
    pendingImageCount: 0,
  };
}

/** Storage's entries as this tab shows them, forgetting images of entries now gone. */
function visibleEntries(entries: ReadonlyArray<PromptStashEntry>): ReadonlyArray<PromptStashEntry> {
  for (const entryId of unsavedImagesByEntryId.keys()) {
    if (!entries.some((entry) => entry.id === entryId)) unsavedImagesByEntryId.delete(entryId);
  }
  return unsavedImagesByEntryId.size === 0 ? entries : entries.map(withUnsavedImages);
}

/**
 * Persists the queue, immediately rather than debounced. Stashing is a
 * deliberate, infrequent keystroke — not a per-character autosave — so there
 * is nothing to coalesce, and the caller clears the composer on the strength
 * of this write landing, which a debounce timer cannot honestly report.
 */
function persistEntries(entries: ReadonlyArray<PromptStashEntry>): {
  written: boolean;
  durable: boolean;
} {
  try {
    baseStashStorage.setItem(
      PROMPT_STASH_STORAGE_KEY,
      JSON.stringify({
        version: PROMPT_STASH_STORAGE_VERSION,
        state: {
          entries: unsavedImagesByEntryId.size === 0 ? entries : entries.map(withoutUnsavedImages),
        },
      }),
    );
    return { written: true, durable: storageIsDurable };
  } catch (error) {
    console.error("[PROMPT-STASH] Could not persist stash (storage quota?).", error);
    return { written: false, durable: false };
  }
}

function readPersistedEntries(): ReadonlyArray<PromptStashEntry> | null {
  try {
    const raw = baseStashStorage.getItem(PROMPT_STASH_STORAGE_KEY);
    if (typeof raw !== "string" || raw.length === 0) return null;
    const parsed: unknown = JSON.parse(raw);
    const state = (parsed as { state?: unknown } | null)?.state;
    if (!state) return null;
    return decodePersistedPromptStashState(state).entries;
  } catch {
    return null;
  }
}

/**
 * Every tab of the origin shares one stash. A change starts from what storage
 * holds now rather than this tab's copy, so writing it back cannot erase an
 * entry another tab stashed since this tab last read.
 */
function latestEntries(current: ReadonlyArray<PromptStashEntry>): ReadonlyArray<PromptStashEntry> {
  return readPersistedEntries() ?? current;
}

function loadPersistedEntries(): ReadonlyArray<PromptStashEntry> | null {
  const persisted = readPersistedEntries();
  const settled = persisted && settleOrphanedPendingImages(persisted, Date.now());
  if (!settled) return persisted;
  // Later changes start from storage, so the settled counts must land there too.
  persistEntries(settled);
  return settled;
}

interface PromptStashStoreState {
  entries: ReadonlyArray<PromptStashEntry>;
  stashEntry: (entry: PromptStashEntry) => {
    evicted: PromptStashEntry | null;
    /** False when the write failed outright (e.g. quota); nothing was kept. */
    written: boolean;
    /**
     * False when the write will not survive a reload: either it failed, or it
     * landed only in the in-memory fallback because localStorage is blocked.
     */
    durable: boolean;
  };
  /**
   * `durable` is false when the removal could not be persisted, meaning a
   * reload would resurrect the entry.
   */
  takeEntry: (entryId: string) => { entry: PromptStashEntry | null; durable: boolean };
  /**
   * Returns attached=false when the entry is gone (restored or deleted while
   * encoding was still running) so the caller can tell the user their images
   * did not make it.
   */
  finalizeEntryImages: (
    entryId: string,
    images: StashEntryImages,
  ) => { attached: boolean; durable: boolean };
}

export const usePromptStashStore = create<PromptStashStoreState>()((set, get) => ({
  entries: [],
  stashEntry: (entry) => {
    const nextEntries = [entry, ...latestEntries(get().entries)];
    const evicted = nextEntries.length > MAX_STASH_ENTRIES ? (nextEntries.pop() ?? null) : null;
    const { written, durable } = persistEntries(nextEntries);
    // A rejected write must not leave the entry visible either: the caller
    // keeps the composer intact on failure, so a stashed copy would
    // duplicate the prompt. Eviction likewise only sticks on success.
    if (!written) {
      return { evicted: null, written: false, durable: false };
    }
    set(() => ({ entries: visibleEntries(nextEntries) }));
    return { evicted, written: true, durable };
  },
  takeEntry: (entryId) => {
    const entries = latestEntries(get().entries);
    const stored = entries.find((candidate) => candidate.id === entryId);
    if (!stored) return { entry: null, durable: true };
    const entry = withUnsavedImages(stored);
    const nextEntries = entries.filter((candidate) => candidate.id !== entryId);
    const { durable } = persistEntries(nextEntries);
    set(() => ({ entries: visibleEntries(nextEntries) }));
    return { entry, durable };
  },
  finalizeEntryImages: (entryId, images) => {
    const entries = latestEntries(get().entries);
    const index = entries.findIndex((candidate) => candidate.id === entryId);
    const existing = index === -1 ? undefined : entries[index];
    if (!existing) return { attached: false, durable: true };
    const nextEntries = [...entries];
    nextEntries[index] = {
      ...existing,
      attachments: images.attachments,
      droppedImageNames: images.droppedImageNames,
      unreadableImageNames: images.unreadableImageNames,
      pendingImageCount: 0,
    };
    const { written, durable } = persistEntries(nextEntries);
    if (!written) {
      // The smaller write without the images settles the stored entry, so it
      // never shows "saving…" again with no encoder left to finish it.
      unsavedImagesByEntryId.set(entryId, {
        attachments: images.attachments,
        droppedImageNames: images.droppedImageNames,
        unreadableImageNames: images.unreadableImageNames,
      });
      persistEntries(nextEntries);
    }
    set(() => ({ entries: visibleEntries(nextEntries) }));
    return { attached: true, durable };
  },
}));

{
  try {
    baseStashStorage.removeItem(LEGACY_PROMPT_STASH_STORAGE_KEY);
  } catch {}
  const persisted = loadPersistedEntries();
  if (persisted) {
    usePromptStashStore.setState({ entries: persisted });
  }
  // Fires only for writes from other tabs, keeping this tab's list current.
  if (storageIsDurable && typeof window !== "undefined") {
    window.addEventListener("storage", (event) => {
      if (event.key !== PROMPT_STASH_STORAGE_KEY && event.key !== null) return;
      usePromptStashStore.setState({ entries: visibleEntries(readPersistedEntries() ?? []) });
    });
  }
}

export function writePromptStashStorageForTest(raw: string): void {
  baseStashStorage.setItem(PROMPT_STASH_STORAGE_KEY, raw);
  usePromptStashStore.setState({ entries: loadPersistedEntries() ?? [] });
}
