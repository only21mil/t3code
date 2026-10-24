import { expect, it } from "vite-plus/test";

import { startSourceLineJump } from "./source-line-jump";

const ROW_HEIGHT = 20;
const VIEWPORT_HEIGHT = 800;

// Follows React Native's `VirtualizedList` without `getItemLayout`: rows past the highest
// measured one have no offset, so `scrollToIndex` reports them to `onScrollToIndexFailed`, or
// throws without one. Unless `measures` is false, each frame first lays out the rows down to two
// viewports past the current offset, as the list does after a scroll.
function wrappedSourceList(input: { readonly measures: boolean }) {
  // Every other line wraps onto three rows, so measured rows average two row heights.
  const heights = Array.from({ length: 500 }, (_, index) =>
    index % 2 === 0 ? ROW_HEIGHT * 3 : ROW_HEIGHT,
  );
  const top = (index: number) => heights.slice(0, index).reduce((sum, height) => sum + height, 0);
  const frames: Array<() => void> = [];
  const state = { highestMeasured: 79, offset: 0, lineInView: null as number | null };
  let onScrollToIndexFailed: ((info: { readonly averageItemLength: number }) => void) | null = null;

  const list = {
    scrollToIndex(params: { readonly index: number; readonly viewPosition?: number }) {
      if (params.index > state.highestMeasured) {
        if (onScrollToIndexFailed === null) {
          throw new Error(
            "scrollToIndex should be used in conjunction with getItemLayout or onScrollToIndexFailed",
          );
        }
        const measured = heights.slice(0, state.highestMeasured + 1);
        onScrollToIndexFailed({
          averageItemLength: measured.reduce((sum, height) => sum + height, 0) / measured.length,
        });
        return;
      }
      state.offset = top(params.index) - (params.viewPosition ?? 0) * VIEWPORT_HEIGHT;
      state.lineInView = params.index;
    },
    scrollToOffset(params: { readonly offset: number }) {
      state.offset = params.offset;
    },
  };

  return {
    list,
    state,
    handleScrollToIndexFailed(handler: NonNullable<typeof onScrollToIndexFailed>) {
      onScrollToIndexFailed = handler;
    },
    scheduleFrame(run: () => void) {
      frames.push(run);
      return () => frames.splice(frames.indexOf(run), 1);
    },
    drainFrames() {
      while (frames.length > 0) {
        if (input.measures) {
          while (top(state.highestMeasured + 1) < state.offset + 2 * VIEWPORT_HEIGHT) {
            state.highestMeasured += 1;
          }
        }
        frames.shift()?.();
      }
    },
  };
}

it("lands on a wrapped line past the measured rows once the rows near it lay out", () => {
  const source = wrappedSourceList({ measures: true });
  const jump = startSourceLineJump(() => source.list, 199, source.scheduleFrame);
  source.handleScrollToIndexFailed((info) => jump.retry(info.averageItemLength, ROW_HEIGHT));

  source.drainFrames();

  expect(source.state.lineInView).toBe(199);
});

it("stops at the estimated offset when the rows near it never lay out", () => {
  const source = wrappedSourceList({ measures: false });
  const jump = startSourceLineJump(() => source.list, 199, source.scheduleFrame);
  source.handleScrollToIndexFailed((info) => jump.retry(info.averageItemLength, ROW_HEIGHT));

  source.drainFrames();

  expect(source.state).toMatchObject({ lineInView: null, offset: 199 * 2 * ROW_HEIGHT });
});
