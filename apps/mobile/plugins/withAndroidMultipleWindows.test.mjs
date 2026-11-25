import * as NodeChildProcess from "node:child_process";
import * as NodeFS from "node:fs";
import * as NodeModule from "node:module";
import * as NodeOS from "node:os";
import * as NodePath from "node:path";
import { afterEach, describe, expect, it } from "vite-plus/test";

const require = NodeModule.createRequire(import.meta.url);
const { AndroidConfig, compileModsAsync, XML } = require("expo/config-plugins");
const { getConfig } = require("expo/config");
const templateSource = "package/android/app/src/main";
function templateFile(path) {
  return NodeChildProcess.execFileSync(
    "tar",
    [
      "-xOf",
      NodePath.join(NodePath.dirname(require.resolve("expo/package.json")), "template.tgz"),
      `${templateSource}/${path}`,
    ],
    { encoding: "utf8" },
  );
}
const template = {
  manifest: templateFile("AndroidManifest.xml"),
  mainActivity: templateFile("java/com/helloworld/MainActivity.kt"),
};
const projectRoots = [];

afterEach(() => {
  for (const root of projectRoots.splice(0)) NodeFS.rmSync(root, { recursive: true, force: true });
});

// Runs the app's own manifest and MainActivity mods over the files `expo prebuild` starts from.
async function prebuildAndroid(input) {
  const projectRoot = NodeFS.mkdtempSync(NodePath.join(NodeOS.tmpdir(), "multiple-windows-"));
  projectRoots.push(projectRoot);
  const sourceRoot = NodePath.join(projectRoot, "android/app/src/main");
  const manifestPath = NodePath.join(sourceRoot, "AndroidManifest.xml");
  const activityPath = NodePath.join(sourceRoot, "java/com/helloworld/MainActivity.kt");
  NodeFS.mkdirSync(NodePath.dirname(activityPath), { recursive: true });
  NodeFS.writeFileSync(manifestPath, input.manifest);
  NodeFS.writeFileSync(activityPath, input.mainActivity);
  const { exp } = getConfig(NodePath.resolve(import.meta.dirname, ".."), {
    isModdedConfig: true,
  });
  const { manifest, mainActivity } = exp.mods?.android ?? {};
  await compileModsAsync(
    {
      ...exp,
      mods: { android: { ...(manifest && { manifest }), ...(mainActivity && { mainActivity }) } },
    },
    { projectRoot, platforms: ["android"] },
  );
  return {
    manifest: NodeFS.readFileSync(manifestPath, "utf8"),
    mainActivity: NodeFS.readFileSync(activityPath, "utf8"),
  };
}

async function mainActivityElement(manifest) {
  return AndroidConfig.Manifest.getMainActivityOrThrow(await XML.parseXMLAsync(manifest));
}

describe("withAndroidMultipleWindows", () => {
  it("lets Android open MainActivity in more than one window, all sharing one guarded React host", async () => {
    const { manifest, mainActivity } = await prebuildAndroid(template);
    const activity = await mainActivityElement(manifest);

    // singleTask allows a single instance; the resource is singleInstancePerTask from Android 12.
    expect(activity.$["android:launchMode"]).toBe("@integer/t3_main_activity_launch_mode");
    expect(activity.property).toEqual([
      {
        $: {
          "android:name": "android.window.PROPERTY_SUPPORTS_MULTI_INSTANCE_SYSTEM_UI",
          "android:value": "true",
        },
      },
    ]);
    expect(mainActivity).toContain(
      "import expo.modules.t3nativecontrols.T3WindowReactActivityDelegate",
    );
    expect(mainActivity).toMatch(/object : T3WindowReactActivityDelegate\(\s+this,/);
    expect(mainActivity).not.toMatch(
      /DefaultReactActivityDelegate[(]|import .*DefaultReactActivityDelegate/,
    );
  });

  it("leaves the prebuilt project unchanged when prebuild runs again", async () => {
    const once = await prebuildAndroid(template);
    const twice = await prebuildAndroid(once);

    expect(twice).toEqual(once);
  });
});

describe("t3-native-controls launch mode", () => {
  const res = NodePath.resolve(
    import.meta.dirname,
    "../modules/t3-native-controls/android/src/main/res",
  );
  const launchMode = (folder) =>
    NodeFS.readFileSync(NodePath.join(res, folder, "t3_windows.xml"), "utf8").match(
      /<integer name="t3_main_activity_launch_mode">(\d)<\/integer>/,
    )?.[1];

  it("stays singleTask before Android 12 and allows a window per task from it", () => {
    // android.content.pm.ActivityInfo: LAUNCH_SINGLE_TASK = 2, LAUNCH_SINGLE_INSTANCE_PER_TASK = 4.
    expect(launchMode("values")).toBe("2");
    expect(launchMode("values-v31")).toBe("4");
  });
});
