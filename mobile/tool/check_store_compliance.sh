#!/usr/bin/env bash
set -euo pipefail

grep -q "MBOLO_STORE_BILLING_REQUIRED" lib/premium.dart
grep -q "defaultValue: true" lib/premium.dart
grep -q "deleteAccount" lib/auth_contract.dart
grep -q "reportProfile" lib/auth_contract.dart
grep -q "blockProfile" lib/auth_contract.dart
grep -q 'android:usesCleartextTraffic="false"' tool/prepare_android.sh
grep -q 'android.permission.CAMERA' tool/prepare_android.sh
grep -q 'NSCameraUsageDescription' tool/prepare_ios.sh
grep -q 'NSPhotoLibraryUsageDescription' tool/prepare_ios.sh

if grep -RInE 'READ_CONTACTS|READ_SMS|ACCESS_FINE_LOCATION|QUERY_ALL_PACKAGES' android 2>/dev/null; then
  echo "Permission Android sensible non autorisée détectée." >&2
  exit 1
fi

echo "Store compliance guard: OK"
