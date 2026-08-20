#!/usr/bin/env bash
# GitHub Actions → Cloud Run のキーレス認証（Workload Identity Federation）を
# GCP 側にセットアップする。冪等になるよう「既存なら作らない」で書いてある。
# 一度だけ実行すればよい。実行後、表示される WIF_PROVIDER / WIF_SERVICE_ACCOUNT を
# GitHub の Secrets に登録する（scripts/setup-github.sh が自動でやる）。
set -euo pipefail

PROJECT_ID="takano32"
PROJECT_NUMBER="630684811101"
REGION="asia-northeast1"
REPO="takano32/Monjo-Hakase"

SA_NAME="gh-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL="github-pool"
PROVIDER="github-provider"

echo "== 必要 API を有効化 =="
gcloud services enable \
  iamcredentials.googleapis.com sts.googleapis.com \
  run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  --project "${PROJECT_ID}"

echo "== デプロイ用サービスアカウント =="
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" --project "${PROJECT_ID}" \
    --display-name="GitHub Actions deployer (Cloud Run)"
fi

echo "== ロール付与（gcloud run deploy --source に必要な最小構成）=="
for ROLE in \
  roles/run.admin \
  roles/cloudbuild.builds.editor \
  roles/artifactregistry.writer \
  roles/storage.admin \
  roles/iam.serviceAccountUser ; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="${ROLE}" \
    --condition=None >/dev/null
  echo "  granted ${ROLE}"
done

echo "== Workload Identity プール =="
if ! gcloud iam workload-identity-pools describe "${POOL}" \
      --project "${PROJECT_ID}" --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${POOL}" \
    --project "${PROJECT_ID}" --location=global \
    --display-name="GitHub Actions pool"
fi

echo "== OIDC プロバイダ（GitHub）=="
if ! gcloud iam workload-identity-pools providers describe "${PROVIDER}" \
      --project "${PROJECT_ID}" --location=global \
      --workload-identity-pool="${POOL}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER}" \
    --project "${PROJECT_ID}" --location=global \
    --workload-identity-pool="${POOL}" \
    --display-name="GitHub provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository_owner=='takano32'"
fi

echo "== リポジトリ ${REPO} だけが SA を借用できるよう紐付け =="
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project "${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}" \
  >/dev/null

echo
echo "== 完了。GitHub に登録する値 =="
echo "WIF_PROVIDER        = projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
echo "WIF_SERVICE_ACCOUNT = ${SA_EMAIL}"
