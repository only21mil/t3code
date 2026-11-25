const { AndroidConfig, withAndroidManifest, withMainActivity } = require("expo/config-plugins");

// Android opens a second T3 Code window (Z Fold, tablets) as another MainActivity in a task of its
// own. Expo's template launches singleTask, which allows one instance. t3-native-controls resolves
// the launch mode by API level, since singleInstancePerTask exists from Android 12 only.
const LAUNCH_MODE = "@integer/t3_main_activity_launch_mode";
// Android 15+ offers "New window" in the launcher and taskbar for apps that declare it.
const MULTI_INSTANCE_PROPERTY = "android.window.PROPERTY_SUPPORTS_MULTI_INSTANCE_SYSTEM_UI";
const DELEGATE = "T3WindowReactActivityDelegate";

function replaceOnce(contents, anchor, replacement, description) {
  if (!contents.includes(anchor)) {
    throw new Error(
      `withAndroidMultipleWindows: could not find ${description} in MainActivity — the Expo template changed; update the plugin anchors.`,
    );
  }
  return contents.replace(anchor, replacement);
}

module.exports = function withAndroidMultipleWindows(config) {
  config = withAndroidManifest(config, (nextConfig) => {
    const mainActivity = AndroidConfig.Manifest.getMainActivityOrThrow(nextConfig.modResults);
    mainActivity.$["android:launchMode"] = LAUNCH_MODE;
    const properties = (mainActivity.property ?? []).filter(
      (property) => property.$["android:name"] !== MULTI_INSTANCE_PROPERTY,
    );
    mainActivity.property = [
      ...properties,
      { $: { "android:name": MULTI_INSTANCE_PROPERTY, "android:value": "true" } },
    ];
    return nextConfig;
  });
  // Every window shares one React host; this delegate keeps it resumed while any window is.
  return withMainActivity(config, (nextConfig) => {
    let contents = nextConfig.modResults.contents;
    if (nextConfig.modResults.language !== "kt") {
      throw new Error("withAndroidMultipleWindows: MainActivity must be Kotlin.");
    }
    if (contents.includes(DELEGATE)) return nextConfig;
    contents = replaceOnce(
      contents,
      "import com.facebook.react.defaults.DefaultReactActivityDelegate",
      `import expo.modules.t3nativecontrols.${DELEGATE}`,
      "the DefaultReactActivityDelegate import",
    );
    contents = replaceOnce(
      contents,
      "object : DefaultReactActivityDelegate(",
      `object : ${DELEGATE}(`,
      "the delegate passed to ReactActivityDelegateWrapper",
    );
    nextConfig.modResults.contents = contents;
    return nextConfig;
  });
};
