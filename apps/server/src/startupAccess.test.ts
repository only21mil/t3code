import { expect, it } from "@effect/vitest";
import * as NetAddress from "effect/net/NetAddress";

import { listenerUrlHostForAddress, resolveHeadlessConnectionString } from "./startupAccess.ts";

it("resolves wildcard hosts to a concrete external interface when one is available", () => {
  const connectionString = resolveHeadlessConnectionString("0.0.0.0", 3773, {
    en0: [
      {
        address: "192.168.1.42",
        netmask: "255.255.255.0",
        family: "IPv4",
        mac: "00:00:00:00:00:00",
        internal: false,
        cidr: "192.168.1.42/24",
      },
    ],
    lo0: [
      {
        address: "127.0.0.1",
        netmask: "255.0.0.0",
        family: "IPv4",
        mac: "00:00:00:00:00:00",
        internal: true,
        cidr: "127.0.0.1/8",
      },
    ],
  });

  expect(connectionString).toBe("http://192.168.1.42:3773");
});

it.each([
  ["192.168.1.42", "192.168.1.42"],
  ["fd7a:115c:a1e0::1", "[fd7a:115c:a1e0::1]"],
  ["::1", "[::1]"],
  ["0.0.0.0", "127.0.0.1"],
  ["::", "127.0.0.1"],
])("reaches a server bound to %s at %s", (boundHost, urlHost) => {
  expect(listenerUrlHostForAddress(NetAddress.inetAddressFromIpStringUnsafe(boundHost, 3773))).toBe(
    urlHost,
  );
});
