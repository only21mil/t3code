import { EnvironmentId, MessageId, ThreadId } from "@t3tools/contracts";
import * as Option from "effect/Option";
import * as Schema from "effect/Schema";

import { writeFileAtomically } from "../lib/atomic-file";
import {
  decodeQueuedThreadMessage,
  encodeQueuedThreadMessage,
  type QueuedThreadMessage,
} from "./thread-outbox-model";

const THREAD_OUTBOX_DIRECTORY = "thread-outbox";

const inFlightWrites = new Set<Promise<void>>();

function trackInFlightWrite(operation: Promise<void>): Promise<void> {
  inFlightWrites.add(operation);
  void operation.catch(() => undefined).finally(() => inFlightWrites.delete(operation));
  return operation;
}

/**
 * Awaits queued-message writes so an app update restart cannot tear down the
 * runtime while one is mid-file.
 */
export async function flushThreadOutboxWrites(): Promise<void> {
  while (inFlightWrites.size > 0) {
    await Promise.allSettled(inFlightWrites);
  }
}

export class ThreadOutboxStorageError extends Schema.TaggedError<ThreadOutboxStorageError>()(
  "ThreadOutboxStorageError",
  {
    operation: Schema.Literals(["load", "read-message", "decode-message", "write", "remove"]),
    environmentId: Schema.NullOr(EnvironmentId),
    threadId: Schema.NullOr(ThreadId),
    messageId: Schema.NullOr(MessageId),
    fileName: Schema.NullOr(Schema.String),
    cause: Schema.Defect(),
  },
) {
  override get message(): string {
    return `Thread outbox storage operation ${this.operation} failed for environment ${this.environmentId ?? "unknown"}, thread ${this.threadId ?? "unknown"}, message ${this.messageId ?? "unknown"}, file ${this.fileName ?? "unknown"}.`;
  }
}

export interface ThreadOutboxLoadResult {
  readonly messages: ReadonlyArray<QueuedThreadMessage>;
  readonly errors: ReadonlyArray<ThreadOutboxStorageError>;
}

export interface ThreadOutboxStorage {
  readonly load: () => Promise<ThreadOutboxLoadResult>;
  readonly write: (message: QueuedThreadMessage) => Promise<void>;
  readonly remove: (message: QueuedThreadMessage) => Promise<void>;
}

function messageFileName(messageId: MessageId): string {
  return `${encodeURIComponent(messageId)}.json`;
}

const decodeMessageId = Schema.decodeUnknownOption(MessageId);

// A record that fails to read or decode still names, through its file, the
// message whose write would replace it.
function messageIdFromFileName(fileName: string): MessageId | null {
  try {
    return Option.getOrNull(
      decodeMessageId(decodeURIComponent(fileName.slice(0, -".json".length))),
    );
  } catch {
    return null;
  }
}

async function getOutboxDirectory() {
  const { Directory, Paths } = await import("expo-file-system");
  const directory = new Directory(Paths.document, THREAD_OUTBOX_DIRECTORY);
  directory.create({ idempotent: true, intermediates: true });
  return directory;
}

async function getMessageFile(messageId: MessageId) {
  const { File } = await import("expo-file-system");
  return new File(await getOutboxDirectory(), messageFileName(messageId));
}

export const expoThreadOutboxStorage: ThreadOutboxStorage = {
  load: async () => {
    const messages: QueuedThreadMessage[] = [];
    const errors: ThreadOutboxStorageError[] = [];
    try {
      const { File } = await import("expo-file-system");
      const directory = await getOutboxDirectory();

      for (const entry of directory.list()) {
        if (!(entry instanceof File) || !entry.name.endsWith(".json")) {
          continue;
        }
        let operation: "read-message" | "decode-message" = "read-message";
        try {
          const text = await entry.text();
          operation = "decode-message";
          messages.push(decodeQueuedThreadMessage(JSON.parse(text) as unknown));
        } catch (cause) {
          errors.push(
            new ThreadOutboxStorageError({
              operation,
              environmentId: null,
              threadId: null,
              messageId: messageIdFromFileName(entry.name),
              fileName: entry.name,
              cause,
            }),
          );
        }
      }
    } catch (cause) {
      throw new ThreadOutboxStorageError({
        operation: "load",
        environmentId: null,
        threadId: null,
        messageId: null,
        fileName: null,
        cause,
      });
    }
    return { messages, errors };
  },
  write: async (message) => {
    const fileName = messageFileName(message.messageId);
    try {
      await trackInFlightWrite(
        (async () => {
          const file = await getMessageFile(message.messageId);
          await writeFileAtomically(file, JSON.stringify(encodeQueuedThreadMessage(message)));
        })(),
      );
    } catch (cause) {
      throw new ThreadOutboxStorageError({
        operation: "write",
        environmentId: message.environmentId,
        threadId: message.threadId,
        messageId: message.messageId,
        fileName,
        cause,
      });
    }
  },
  remove: async (message) => {
    const fileName = messageFileName(message.messageId);
    try {
      const file = await getMessageFile(message.messageId);
      if (file.exists) {
        file.delete();
      }
    } catch (cause) {
      throw new ThreadOutboxStorageError({
        operation: "remove",
        environmentId: message.environmentId,
        threadId: message.threadId,
        messageId: message.messageId,
        fileName,
        cause,
      });
    }
  },
};
