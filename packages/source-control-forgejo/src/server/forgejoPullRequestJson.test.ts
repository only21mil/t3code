import { assert, describe, it } from "@effect/vitest";
import * as Schema from "effect/Schema";

import {
  ForgejoComment,
  ForgejoReview,
  forgejoComment,
  forgejoReview,
} from "./forgejoPullRequestJson.ts";

const decodeForgejoComment = Schema.decodeSync(ForgejoComment);
const decodeForgejoReview = Schema.decodeSync(ForgejoReview);

describe("forgejoComment", () => {
  const createdAt = "2026-10-10T19:52:40Z";
  const comment = (updatedAt: string | null | undefined) =>
    forgejoComment(
      decodeForgejoComment({
        id: 29061,
        body: "Performance: five rounds complete",
        user: { login: "forgejo-actions" },
        created_at: createdAt,
        ...(updatedAt === undefined ? {} : { updated_at: updatedAt }),
      }),
    );

  it.each([undefined, null, createdAt, "2026-10-10T19:52:40.000Z"])(
    "reads no edit from an updated_at of %s",
    (updatedAt) => {
      const mapped = comment(updatedAt);
      assert.strictEqual(mapped.createdAt, "2026-10-10T19:52:40.000Z");
      assert.isUndefined(mapped.editedAt);
    },
  );

  it("reads a later updated_at as an edit, in UTC milliseconds", () => {
    const mapped = comment("2026-10-10T20:04:50Z");
    assert.strictEqual(mapped.id, "29061");
    assert.strictEqual(mapped.author?.login, "forgejo-actions");
    assert.strictEqual(mapped.editedAt, "2026-10-10T20:04:50.000Z");
  });
});

describe("forgejoReview", () => {
  const review = (state: string, dismissed?: boolean) =>
    forgejoReview(
      decodeForgejoReview({
        id: 29062,
        body: "Review body",
        user: { login: "reviewer" },
        state,
        submitted_at: "2026-10-10T19:52:40Z",
        comments_count: 0,
        ...(dismissed === undefined ? {} : { dismissed }),
      }),
    );

  it("honors the separate dismissed flag without changing ordinary review states", () => {
    assert.strictEqual(review("APPROVED", true).reviewState, "DISMISSED");
    assert.strictEqual(review("REQUEST_CHANGES", true).reviewState, "DISMISSED");
    assert.strictEqual(review("APPROVED").reviewState, "APPROVED");
    assert.strictEqual(review("REQUEST_CHANGES", false).reviewState, "CHANGES_REQUESTED");
    assert.strictEqual(review("COMMENT", false).reviewState, "COMMENTED");
  });
});
