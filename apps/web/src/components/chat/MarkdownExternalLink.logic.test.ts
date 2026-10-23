import { describe, expect, it } from "vite-plus/test";

import { splitExternalLinkText } from "./MarkdownExternalLink.logic";

describe("splitExternalLinkText", () => {
  it.each([
    ["🔗 API", "🔗", [" ", "A", "P", "I"]],
    ["𠮷野", "𠮷", ["野"]],
    ["👩🏽‍💻 Docs", "👩🏽‍💻", [" ", "D", "o", "c", "s"]],
    ["été", "é", ["t", "é"]],
    ["Docs 👩🏽‍💻", "D", ["o", "c", "s", " ", "👩🏽‍💻"]],
    ["https://x.io", "https://", ["x", ".", "i", "o"]],
  ])("keeps every character of %j whole", (text, leading, breakable) => {
    expect(splitExternalLinkText(text)).toEqual({ leading, breakable });
  });
});
