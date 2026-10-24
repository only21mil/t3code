import type { FlatList } from "react-native";

type SourceLineList = Pick<FlatList<string>, "scrollToIndex" | "scrollToOffset">;

type ScheduleFrame = (run: () => void) => () => void;

// A list that never measures the rows near its estimate stops here, at the estimated offset.
const MAX_SOURCE_LINE_JUMP_RETRIES = 10;

const nextAnimationFrame: ScheduleFrame = (run) => {
  const frame = requestAnimationFrame(run);
  return () => cancelAnimationFrame(frame);
};

/**
 * Scrolls a line list to `index` on the next frame. Wrapped rows have no fixed height, so a
 * line past the measured rows reaches `retry` through `onScrollToIndexFailed`. Without that
 * handler React Native throws. `retry` scrolls to an estimated offset so the rows there lay
 * out, then aims at the line again on the next frame.
 */
export function startSourceLineJump(
  list: () => SourceLineList | null,
  index: number,
  scheduleFrame: ScheduleFrame = nextAnimationFrame,
) {
  let cancelFrame: (() => void) | null = null;
  let retries = 0;
  const aim = () => {
    cancelFrame = scheduleFrame(() => {
      cancelFrame = null;
      list()?.scrollToIndex({ index, animated: false, viewPosition: 0.3 });
    });
  };
  aim();

  return {
    retry(averageItemLength: number, rowHeight: number) {
      // Rows are at least `rowHeight` tall, and the average is 0 before any row is measured.
      const offset = index * Math.max(averageItemLength, rowHeight);
      list()?.scrollToOffset({ offset, animated: false });
      if (retries < MAX_SOURCE_LINE_JUMP_RETRIES) {
        retries += 1;
        aim();
      }
    },
    cancel() {
      cancelFrame?.();
      cancelFrame = null;
    },
  };
}
