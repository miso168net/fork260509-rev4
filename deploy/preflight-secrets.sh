#!/usr/bin/env bash
# deploy/preflight-secrets.sh — up 前六機密檔預檢（001-compose-stack）
# 用法：./deploy/preflight-secrets.sh
#
# 為何：docker compose secrets 用 `file: ./deploy/secrets/*.txt` bind；source 檔缺時
#   compose 不報「缺 X 檔」而是自動建空目錄 → 容器拿到空／目錄 secret、錯誤訊息誤導
#   （如 DB 連線失敗、boot panic）、不指向真因。本預檢在 up 前指名缺檔。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_DIR="$SCRIPT_DIR/secrets"

# 與 generate-secrets.sh 同一份六機密清單
REQUIRED=(postgres_password redis_password jwt_secret refresh_token_secret database_url redis_url)

missing=()
for name in "${REQUIRED[@]}"; do
    f="$SECRETS_DIR/${name}.txt"
    # 缺檔、或為目錄（compose 對缺 bind source 自動建的空目錄）、或空檔 → 視為缺
    if [ ! -f "$f" ] || [ ! -s "$f" ]; then
        missing+=("${name}.txt")
    fi
done

if [ "${#missing[@]}" -gt 0 ]; then
    echo "FAIL：缺少 ${#missing[@]} 個 secret 檔（deploy/secrets/）："
    for m in "${missing[@]}"; do echo "   - $m"; done
    echo ""
    echo "→ 跑 ./deploy/generate-secrets.sh 一鍵生成（缺的才補、冪等）。"
    exit 1
fi

echo "OK：六個必須 secret 檔齊備（deploy/secrets/）。可 up。"
