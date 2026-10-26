import { readHostedPairingRequest } from "@t3tools/shared/remote";
import * as Schema from "effect/Schema";

const MOBILE_PAIRING_URL_PARAM = "pairingUrl";

function isIpLiteral(host: string): boolean {
  try {
    const hostname = new URL(`http://${host}`).hostname.replace(/^\[|\]$/g, "");
    if (hostname.includes(":")) return true;

    const octets = hostname.split(".");
    return (
      octets.length === 4 &&
      octets.every((octet) => /^\d{1,3}$/.test(octet) && Number(octet) <= 255)
    );
  } catch {
    return false;
  }
}

export class PairingQrPayloadEmptyError extends Schema.TaggedError<PairingQrPayloadEmptyError>()(
  "PairingQrPayloadEmptyError",
  {},
) {
  override get message(): string {
    return "Scanned QR code did not contain a pairing URL.";
  }
}

export function buildPairingUrl(host: string, code: string): string {
  const h = host.trim();
  const c = code.trim();
  if (!h) return "";
  if (!c) return h;

  try {
    const url = new URL(h.includes("://") ? h : `${isIpLiteral(h) ? "http" : "https"}://${h}`);
    url.hash = new URLSearchParams([["token", c]]).toString();
    return url.toString();
  } catch {
    return `${h}#token=${c}`;
  }
}

export function parsePairingUrl(url: string): { host: string; code: string } {
  const trimmed = url.trim();
  if (!trimmed) return { host: "", code: "" };

  try {
    const parsed = new URL(trimmed);
    const hostedPairingRequest = readHostedPairingRequest(parsed);
    if (hostedPairingRequest) {
      return {
        host: hostedPairingRequest.host.replace(/\/$/, ""),
        code: hostedPairingRequest.token,
      };
    }

    const hashParams = new URLSearchParams(parsed.hash.slice(1));
    const hashToken = hashParams.get("token");
    const queryToken = parsed.searchParams.get("token");
    const code = hashToken || queryToken || "";

    parsed.hash = "";
    parsed.search = "";
    parsed.pathname = "/";
    return { host: parsed.toString().replace(/\/$/, ""), code };
  } catch {
    return { host: trimmed, code: "" };
  }
}

export function extractPairingUrlFromQrPayload(payload: string): string {
  const trimmed = payload.trim();
  if (!trimmed) {
    throw new PairingQrPayloadEmptyError({});
  }

  try {
    const url = new URL(trimmed);
    if (url.protocol === "t3code:") {
      const pairingUrl = url.searchParams.get(MOBILE_PAIRING_URL_PARAM)?.trim() ?? "";
      if (pairingUrl.length > 0) {
        return pairingUrl;
      }
    }
  } catch {
    // Treat non-URL payloads as raw pairing-url text so the normal input validation can decide.
  }

  return trimmed;
}

// Local Fold preview setup contains an endpoint only. Enrollment is always an
// explicit exchange of a fresh server-issued one-time credential.
export const DEFAULT_PAIRING_HOST = "https://framework-desktop.tail69757d.ts.net:33774";

export function initialPairingFields(pairingUrl: string): { host: string; code: string } {
  const fields = parsePairingUrl(pairingUrl);
  return { ...fields, host: fields.host || DEFAULT_PAIRING_HOST };
}

export function buildManualPairingUrl(host: string, codeOrUrl: string): string {
  const invalid = () => new Error("Invalid pairing link. Use a T3 pairing code or QR code.");
  // A nonempty synthetic code takes the existing scheme-normalization path.
  // Only this URL’s origin is used; the placeholder is never submitted.
  const displayedHost = new URL(buildPairingUrl(host, "origin-validation"));
  if (
    !["https:", "http:"].includes(displayedHost.protocol) ||
    displayedHost.username ||
    displayedHost.password
  ) {
    throw invalid();
  }
  const input = codeOrUrl.trim();
  if (!input) throw new Error("Enter a fresh pairing code or scan a pairing QR code.");
  if (!input.includes("://")) return buildPairingUrl(host, input);

  const link = new URL(input);
  if (
    !["https:", "http:"].includes(link.protocol) ||
    link.username ||
    link.password ||
    !["/", "/pair"].includes(link.pathname)
  ) {
    throw invalid();
  }
  const hash = new URLSearchParams(link.hash.slice(1));
  const tokens = [...link.searchParams.getAll("token"), ...hash.getAll("token")];
  if (tokens.length === 0 || !tokens[0]?.trim()) {
    throw new Error("This link has no pairing code. Get a fresh pairing link.");
  }
  if (tokens.length !== 1 || [...hash.keys()].some((key) => key !== "token")) throw invalid();

  const hosts = link.searchParams.getAll("host");
  let target = link;
  if (hosts.length > 0) {
    if (
      hosts.length !== 1 ||
      link.origin !== "https://app.t3.codes" ||
      link.pathname !== "/pair" ||
      [...link.searchParams.keys()].some((key) => !["host", "label", "token"].includes(key))
    ) {
      throw invalid();
    }
    target = new URL(hosts[0]!);
    if (
      target.username ||
      target.password ||
      target.search ||
      target.hash ||
      target.pathname !== "/"
    )
      throw invalid();
  } else if ([...link.searchParams.keys()].some((key) => key !== "token")) {
    throw invalid();
  }
  if (target.origin !== displayedHost.origin) {
    throw new Error(
      "This pairing link does not match the displayed host. Scan its QR code or update Host first.",
    );
  }
  return buildPairingUrl(host, tokens[0]!);
}
