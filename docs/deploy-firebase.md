# Deploy Brasil Real (Firebase Hosting + Cloud Run API)

## URLs

| Serviço | URL |
|---|---|
| Site | https://brasilreal-atlas.web.app |
| API | https://brasil-real-api-928790342045.southamerica-east1.run.app |
| Console | https://console.firebase.google.com/project/brasilreal-atlas/overview |

Projeto Firebase/GCP: `brasilreal-atlas` · região API: `southamerica-east1`.

## Redeploy rápido

### API (Cloud Run)

```powershell
cd D:\GameDev\BrasilReal
gcloud run deploy brasil-real-api `
  --project=brasilreal-atlas `
  --region=southamerica-east1 `
  --source=. `
  --allow-unauthenticated `
  --port=8080 `
  --memory=1Gi `
  --env-vars-file=infra/cloudrun-api.env.yaml
```

### Web (Firebase Hosting)

```powershell
cd D:\GameDev\BrasilReal\apps\web
$env:FIREBASE_HOSTING="1"
$env:NEXT_PUBLIC_API_URL="https://brasil-real-api-928790342045.southamerica-east1.run.app"
npm run build
cd ..\..
firebase deploy --only hosting --project brasilreal-atlas
```

## Notas

- Front é export estático (`output: "export"`); a API é chamada via `NEXT_PUBLIC_API_URL`.
- CORS da API inclui `brasilreal-atlas.web.app` / `.firebaseapp.com`.
- Env aceitos: `DATA_MODE` / `BR_DATA_MODE`, `API_CORS_ORIGINS`, `SEED_ON_STARTUP` / `BR_SEED_ON_STARTUP`.
- Cache de freshness da API fica no container (efêmero); fixtures vão na imagem.
