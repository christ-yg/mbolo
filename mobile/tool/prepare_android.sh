#!/usr/bin/env bash
set -euo pipefail

flutter create \
  --platforms=android \
  --project-name mbolo_mobile \
  --org ga.mbolo \
  .

manifest="android/app/src/main/AndroidManifest.xml"
gradle="android/app/build.gradle.kts"
app_id="ga.mbolo.app"

if ! grep -q 'android.permission.INTERNET' "$manifest"; then
  sed -i '/<manifest/a\    <uses-permission android:name="android.permission.INTERNET" />' "$manifest"
fi

if ! grep -q 'android.permission.CAMERA' "$manifest"; then
  sed -i '/<manifest/a\    <uses-permission android:name="android.permission.CAMERA" />' "$manifest"
fi

sed -i 's/android:label="mbolo_mobile"/android:label="MBOLO"/' "$manifest"

# The store identity must never depend on Flutter's generated project name.
# Once an applicationId is published, Google Play does not allow changing it.
sed -i -E "s/namespace = \"[^\"]+\"/namespace = \"$app_id\"/" "$gradle"
sed -i -E "s/applicationId = \"[^\"]+\"/applicationId = \"$app_id\"/" "$gradle"

# Google Play requires API 36 for new apps and updates from 31 August 2026.
sed -i -E 's/targetSdk = flutter\.targetSdkVersion/targetSdk = 36/' "$gradle"

if ! grep -q 'android:usesCleartextTraffic="false"' "$manifest"; then
  sed -i '/<application/a\        android:usesCleartextTraffic="false"' "$manifest"
fi

grep -q 'android.permission.INTERNET' "$manifest"
grep -q 'android.permission.CAMERA' "$manifest"
grep -q 'android:label="MBOLO"' "$manifest"
grep -q 'android:usesCleartextTraffic="false"' "$manifest"
grep -q 'namespace = "ga.mbolo.app"' "$gradle"
grep -q 'applicationId = "ga.mbolo.app"' "$gradle"
grep -q 'targetSdk = 36' "$gradle"
