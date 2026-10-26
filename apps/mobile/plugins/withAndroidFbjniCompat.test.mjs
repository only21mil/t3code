import { describe, expect, it } from "vitest";
import * as NodeFS from "node:fs";
import * as NodeModule from "node:module";
import * as NodePath from "node:path";
import withAndroidFbjniCompat from "./withAndroidFbjniCompat.cjs";

async function transform(contents, language = "groovy") {
  const config = withAndroidFbjniCompat({ name: "Test", slug: "test" });
  const result = await config.mods.android.projectBuildGradle({
    ...config,
    modRequest: { platform: "android", modName: "projectBuildGradle", introspect: false },
    modResults: { language, contents },
  });
  return result.modResults.contents;
}

describe("Android fbjni ABI compatibility", () => {
  it("constrains every project to React Native's actual native dependency", async () => {
    const require = NodeModule.createRequire(import.meta.url);
    const rnRoot = NodePath.dirname(require.resolve("react-native/package.json"));
    const catalog = NodeFS.readFileSync(NodePath.join(rnRoot, "gradle/libs.versions.toml"), "utf8");
    const rnVersion = catalog.match(/^fbjni\s*=\s*"([^"]+)"/m)?.[1];
    expect(rnVersion).toBeDefined();
    const generated = await transform("allprojects { repositories { mavenCentral() } }");
    const forced = generated.match(
      /resolutionStrategy\.force 'com\.facebook\.fbjni:fbjni:([^']+)'/,
    )?.[1];
    expect(forced).toBe(rnVersion);
  });
  it("retains one constraint through repeated prebuilds", async () => {
    const once = await transform("allprojects { repositories { mavenCentral() } }");
    expect(await transform(once)).toBe(once);
    expect(once.match(/resolutionStrategy\.force/g)).toHaveLength(1);
  });
  it("fails clearly if the Gradle template changes language", async () => {
    await expect(transform("", "kotlin")).rejects.toThrow("Groovy");
  });
});
