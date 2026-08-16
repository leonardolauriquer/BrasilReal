# Redeploy Brasil Real → Firebase + Cloud Run
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$Root\firebase.json")) { $Root = "D:\GameDev\BrasilReal" }
$ApiUrl = "https://brasil-real-api-928790342045.southamerica-east1.run.app"

Write-Host "==> API Cloud Run"
Set-Location $Root
gcloud run deploy brasil-real-api `
  --project=brasilreal-atlas `
  --region=southamerica-east1 `
  --source=. `
  --allow-unauthenticated `
  --port=8080 `
  --memory=1Gi `
  --env-vars-file=infra/cloudrun-api.env.yaml

Write-Host "==> Integrity canary"
python "$Root\scripts\canary_api.py" --url $ApiUrl
if ($LASTEXITCODE -ne 0) { throw "Canary failed; hosting was not deployed" }

Write-Host "==> Web build + Firebase Hosting"
Set-Location "$Root\apps\web"
$env:FIREBASE_HOSTING = "1"
$env:NEXT_PUBLIC_API_URL = $ApiUrl
npm run build
Set-Location $Root
firebase deploy --only hosting --project brasilreal-atlas

Write-Host "Site: https://brasilreal-atlas.web.app"
Write-Host "API:  $ApiUrl"
