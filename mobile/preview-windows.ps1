$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    throw 'Flutter introuvable. Installe Flutter et ajoute son dossier bin au PATH, puis rouvre PowerShell.'
}
flutter pub get
if ($LASTEXITCODE -ne 0) { throw 'Installation des dependances echouee.' }
Write-Host 'DEMO LOCALE : demo@mbolo.test / MboloDemo! / code 123456'
flutter run -d edge -t lib/main_preview.dart --web-hostname 127.0.0.1 --web-port 7357
if ($LASTEXITCODE -ne 0) { throw 'Apercu interrompu ou lancement impossible. Voir le message Flutter ci-dessus.' }
