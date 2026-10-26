const { withProjectBuildGradle } = require("expo/config-plugins");

// Shiki requests fbjni:+. 0.8.1 uses NDK 28 symbols absent from RN 0.86.3's
// NDK 27 libc++; keep the native dependency aligned with RN's version catalog.
const FBJNI_VERSION = "0.7.0";
const marker = "// T3 Android fbjni compatibility";
const constraint = `${marker}
allprojects {
    configurations.all {
        resolutionStrategy.force 'com.facebook.fbjni:fbjni:${FBJNI_VERSION}'
    }
}
`;

module.exports = function withAndroidFbjniCompat(config) {
  return withProjectBuildGradle(config, (nextConfig) => {
    if (nextConfig.modResults.language !== "groovy") {
      throw new Error("fbjni compatibility requires the Expo Groovy Gradle template");
    }
    if (!nextConfig.modResults.contents.includes(marker)) {
      nextConfig.modResults.contents += `\n${constraint}`;
    }
    return nextConfig;
  });
};
