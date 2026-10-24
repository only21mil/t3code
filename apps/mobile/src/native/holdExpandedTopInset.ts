// Kept free of react-native imports so it stays unit-testable in node.

export type HeldTopInset = {
  readonly width: number;
  readonly height: number;
  readonly top: number;
};

/**
 * A minimizing navigation bar (iOS 27, the Duo's default) lowers the safe-area top on every
 * scroll frame. Only a window resize, from folding or rotation, lowers it for good.
 */
export function holdExpandedTopInset(held: HeldTopInset, next: HeldTopInset): HeldTopInset {
  const sameWindow = held.width === next.width && held.height === next.height;
  return sameWindow && held.top >= next.top ? held : next;
}
