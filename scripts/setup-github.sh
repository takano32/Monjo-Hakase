#!/usr/bin/env bash
# GitHub 側に、deploy.yml が参照する変数とシークレットを登録する。
# 値は setup-wif.sh が作るリソースに対応した決定的な値。
# 前提: gh CLI が対象リポジトリにアクセスできる状態でログイン済み。
set -euo pipefail

REPO="takano32/Monjo-Hakase"
PROJECT_ID="takano32"
PROJECT_NUMBER="630684811101"
REGION="asia-northeast1"
SERVICE="monjo-hakase"
POOL="github-pool"
PROVIDER="github-provider"
SA_EMAIL="gh-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

echo "== Variables =="
gh variable set GCP_PROJECT_ID    -R "${REPO}" -b "${PROJECT_ID}"
gh variable set GCP_REGION        -R "${REPO}" -b "${REGION}"
gh variable set CLOUD_RUN_SERVICE -R "${REPO}" -b "${SERVICE}"

echo "== Secrets =="
gh secret set WIF_PROVIDER -R "${REPO}" \
  -b "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
gh secret set WIF_SERVICE_ACCOUNT -R "${REPO}" -b "${SA_EMAIL}"

echo "done."
