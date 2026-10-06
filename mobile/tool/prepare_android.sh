#!/usr/bin/env bash
set -euo pipefail

flutter create \
  --platforms=android \
  --project-name mbolo_mobile \
  --org ga.mbolo \
  .

manifest="android/app/src/main/AndroidManifest.xml"

if ! grep -q 'android.permission.INTERNET' "$manifest"; then
  sed -i '/<manifest/a\    <uses-permission android:name="android.permission.INTERNET" />' "$manifest"
fi

sed -i 's/android:label="mbolo_mobile"/android:label="MBOLO"/' "$manifest"

if ! grep -q 'android:usesCleartextTraffic="false"' "$manifest"; then
  sed -i '/<application/a\        android:usesCleartextTraffic="false"' "$manifest"
fi

grep -q 'android.permission.INTERNET' "$manifest"
grep -q 'android:label="MBOLO"' "$manifest"
grep -q 'android:usesCleartextTraffic="false"' "$manifest"
