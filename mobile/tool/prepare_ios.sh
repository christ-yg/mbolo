#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "La préparation iOS exige macOS avec Xcode 26 ou supérieur." >&2
  exit 1
fi

command -v flutter >/dev/null
command -v xcodebuild >/dev/null

flutter create \
  --platforms=ios \
  --project-name mbolo_mobile \
  --org ga.mbolo \
  .

project="ios/Runner.xcodeproj/project.pbxproj"
plist="ios/Runner/Info.plist"

# Stable App Store identity and the current Apple minimum deployment target.
sed -i '' -E 's/PRODUCT_BUNDLE_IDENTIFIER = [^;]+;/PRODUCT_BUNDLE_IDENTIFIER = ga.mbolo.app;/g' "$project"
sed -i '' -E 's/IPHONEOS_DEPLOYMENT_TARGET = [^;]+;/IPHONEOS_DEPLOYMENT_TARGET = 13.0;/g' "$project"

/usr/libexec/PlistBuddy -c 'Set :CFBundleDisplayName MBOLO' "$plist" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c 'Add :CFBundleDisplayName string MBOLO' "$plist"
/usr/libexec/PlistBuddy -c 'Set :NSPhotoLibraryUsageDescription MBOLO utilise les photos que vous choisissez pour compléter votre profil.' "$plist" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c 'Add :NSPhotoLibraryUsageDescription string MBOLO utilise les photos que vous choisissez pour compléter votre profil.' "$plist"

grep -q 'PRODUCT_BUNDLE_IDENTIFIER = ga.mbolo.app;' "$project"
grep -q 'IPHONEOS_DEPLOYMENT_TARGET = 13.0;' "$project"
/usr/libexec/PlistBuddy -c 'Print :NSPhotoLibraryUsageDescription' "$plist" >/dev/null

echo "Projet iOS MBOLO prêt pour la configuration de signature dans Xcode."
