const graphemeSegmenter = new Intl.Segmenter(undefined, { granularity: "grapheme" });

// Splits on graphemes so a wrap opportunity never lands inside an emoji, a
// surrogate pair or a combining sequence.
export function splitExternalLinkText(text: string): { leading: string; breakable: string[] } {
  const graphemes = Array.from(graphemeSegmenter.segment(text), ({ segment }) => segment);
  const leadingCount = /^https?:\/\//i.exec(text)?.[0].length ?? Math.min(graphemes.length, 1);
  return {
    leading: graphemes.slice(0, leadingCount).join(""),
    breakable: graphemes.slice(leadingCount),
  };
}
