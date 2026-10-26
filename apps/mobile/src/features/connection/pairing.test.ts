import { describe, expect, it } from "vite-plus/test";

import {
  buildPairingUrl,
  buildManualPairingUrl,
  initialPairingFields,
  DEFAULT_PAIRING_HOST,
  extractPairingUrlFromQrPayload,
  PairingQrPayloadEmptyError,
  parsePairingUrl,
} from "./pairing";

describe("buildPairingUrl", () => {
  it("uses HTTP for a schemeless IP address", () => {
    expect(buildPairingUrl("192.168.1.100:3773", "pairing-token")).toBe(
      "http://192.168.1.100:3773/#token=pairing-token",
    );
  });

  it("keeps HTTPS as the default for a schemeless hostname", () => {
    expect(buildPairingUrl("remote.example.com", "pairing-token")).toBe(
      "https://remote.example.com/#token=pairing-token",
    );
  });

  it("preserves an explicit scheme for an IP address", () => {
    expect(buildPairingUrl("https://192.168.1.100:3773", "pairing-token")).toBe(
      "https://192.168.1.100:3773/#token=pairing-token",
    );
  });
});

describe("extractPairingUrlFromQrPayload", () => {
  it("trims raw pairing urls from qr payloads", () => {
    expect(
      extractPairingUrlFromQrPayload("  https://remote.example.com/pair#token=pairing-token  "),
    ).toBe("https://remote.example.com/pair#token=pairing-token");
  });

  it("unwraps mobile deep links that carry an encoded pairing url", () => {
    expect(
      extractPairingUrlFromQrPayload(
        "t3code://pair?pairingUrl=https%3A%2F%2Fremote.example.com%2Fpair%23token%3Dpairing-token",
      ),
    ).toBe("https://remote.example.com/pair#token=pairing-token");
  });

  it("rejects empty qr payloads", () => {
    expect(() => extractPairingUrlFromQrPayload("   ")).toThrowError(PairingQrPayloadEmptyError);
    expect(() => extractPairingUrlFromQrPayload("   ")).toThrowError(
      "Scanned QR code did not contain a pairing URL.",
    );
  });
});

describe("parsePairingUrl", () => {
  it("reads hosted pairing links into backend host fields", () => {
    expect(
      parsePairingUrl(
        "https://app.t3.codes/pair?host=https%3A%2F%2Fdesktop.tailnet.ts.net%2F#token=pairing-token",
      ),
    ).toEqual({
      host: "https://desktop.tailnet.ts.net",
      code: "pairing-token",
    });
  });
});

describe("Framework setup", () => {
  it("presets only the host on empty setup", () => {
    expect(initialPairingFields("")).toEqual({ host: DEFAULT_PAIRING_HOST, code: "" });
    expect(new URL(DEFAULT_PAIRING_HOST).protocol).toBe("https:");
    expect(new URL(DEFAULT_PAIRING_HOST).hash).toBe("");
    expect(new URL(DEFAULT_PAIRING_HOST).search).toBe("");
  });

  it("preserves an explicitly entered or scanned environment", () => {
    expect(initialPairingFields("https://other.example/pair#token=test-code")).toEqual({
      host: "https://other.example",
      code: "test-code",
    });
  });

  it("accepts a manual code and a full link for the displayed host", () => {
    const expected = buildPairingUrl(DEFAULT_PAIRING_HOST, "test-code");
    expect(buildManualPairingUrl(DEFAULT_PAIRING_HOST, "  test-code  ")).toBe(expected);
    expect(
      buildManualPairingUrl(DEFAULT_PAIRING_HOST, `${DEFAULT_PAIRING_HOST}/pair#token=test-code`),
    ).toBe(expected);
  });

  it("accepts an official hosted link for the displayed backend", () => {
    const link = `https://app.t3.codes/pair?host=${encodeURIComponent(DEFAULT_PAIRING_HOST)}#token=test-code`;
    expect(buildManualPairingUrl(DEFAULT_PAIRING_HOST, link)).toBe(
      buildPairingUrl(DEFAULT_PAIRING_HOST, "test-code"),
    );
  });

  it("rejects a full link for another host without changing the target", () => {
    expect(() =>
      buildManualPairingUrl(DEFAULT_PAIRING_HOST, "https://other.example/pair#token=test-code"),
    ).toThrow("does not match");
    expect(() =>
      buildManualPairingUrl(
        DEFAULT_PAIRING_HOST,
        "http://framework-desktop.tail69757d.ts.net:33774/pair#token=test-code",
      ),
    ).toThrow("does not match");
  });

  it("requires a fresh code and rejects URLs containing user info", () => {
    expect(() => buildManualPairingUrl(DEFAULT_PAIRING_HOST, " ")).toThrow("pairing code");
    expect(() =>
      buildManualPairingUrl(DEFAULT_PAIRING_HOST, `${DEFAULT_PAIRING_HOST}/pair`),
    ).toThrow("pairing code");
    expect(() =>
      buildManualPairingUrl(
        DEFAULT_PAIRING_HOST,
        "https://user:pass@framework-desktop.tail69757d.ts.net:33774/pair#token=test-code",
      ),
    ).toThrow("Invalid pairing link");
  });
});

describe("pasted-link trust boundary", () => {
  it.each([
    "https://framework-desktop.tail69757d.ts.net:33775/pair#token=test-code",
    "https://framework-desktop.tail69757d.ts.net.evil.example:33774/pair#token=test-code",
    "https://evil.example/pair?host=https%3A%2F%2Fframework-desktop.tail69757d.ts.net%3A33774#token=test-code",
    "http://app.t3.codes/pair?host=https%3A%2F%2Fframework-desktop.tail69757d.ts.net%3A33774#token=test-code",
    "https://app.t3.codes.evil.example/pair?host=https%3A%2F%2Fframework-desktop.tail69757d.ts.net%3A33774#token=test-code",
    "https://app.t3.codes/pair?host=https%3A%2F%2Fother.example#token=test-code",
    "https://app.t3.codes/pair?host=https%3A%2F%2Fuser%3Apass%40framework-desktop.tail69757d.ts.net%3A33774#token=test-code",
    "https://app.t3.codes/pair?host=https%3A%2F%2Fframework-desktop.tail69757d.ts.net%3A33774&host=https%3A%2F%2Fevil.example#token=test-code",
    "https://framework-desktop.tail69757d.ts.net:33774/pair?token=first#token=second",
    "https://framework-desktop.tail69757d.ts.net:33774/pair#token=first&token=second",
    "https://framework-desktop.tail69757d.ts.net:33774/other#token=test-code",
    "ftp://framework-desktop.tail69757d.ts.net:33774/pair#token=test-code",
    "https://[bad/pair#token=test-code",
  ])("rejects deceptive or malformed fixture %s", (link) => {
    expect(() => buildManualPairingUrl(DEFAULT_PAIRING_HOST, link)).toThrow();
  });

  it("retains explicit non-Framework manual pairing", () => {
    expect(buildManualPairingUrl("http://10.0.2.2:38754", "test-code")).toBe(
      "http://10.0.2.2:38754/#token=test-code",
    );
  });
});

describe("manual Host normalization", () => {
  it.each([
    ["192.168.1.100:3773", "http://192.168.1.100:3773"],
    ["remote.example.com", "https://remote.example.com"],
    ["localhost:3773", "https://localhost:3773"],
    ["http://192.168.1.100:3773", "http://192.168.1.100:3773"],
    ["https://remote.example.com", "https://remote.example.com"],
    [DEFAULT_PAIRING_HOST, DEFAULT_PAIRING_HOST],
  ])("preserves the existing Host origin for %s", (host, origin) => {
    const expected = buildPairingUrl(host, "test-code");
    expect(new URL(expected).origin).toBe(origin);
    expect(buildManualPairingUrl(host, "test-code")).toBe(expected);
    expect(buildManualPairingUrl(host, `${origin}/pair#token=test-code`)).toBe(expected);
    expect(() => buildManualPairingUrl(host, "https://other.example/pair#token=test-code")).toThrow(
      "does not match",
    );
  });
});
