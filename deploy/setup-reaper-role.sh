#!/usr/bin/env bash
# deploy/setup-reaper-role.sh — 016-observability T022：reaper role 設密＋LOGIN（部署腳本側）。
#
# 分工（data-model §5、research R5、ADR 0072）：
#   m012 migration＝CREATE ROLE reaper NOLOGIN＋GRANT（零密碼）；本腳本＝ALTER ROLE reaper
#   LOGIN PASSWORD（密碼讀自 deploy/secrets/reaper_password.txt、gitignored）。
# 密碼紀律（FR-013）：SQL 走 psql stdin heredoc——密碼零進 host process list、零進版本庫；
#   輸出只印狀態不印值。可重跑（ALTER ROLE 冪等）。
# 前置：stack 已 up（postgres healthy）＋m012 已套用（role 不存在→psql 非零退出 fail-loud）
#   ＋deploy/generate-secrets.sh 已產 reaper_password.txt。
# 用法：bash deploy/setup-reaper-role.sh
set -euo pipefail

cd "$(dirname "$0")/.."

PW_FILE=deploy/secrets/reaper_password.txt
if [ ! -s "$PW_FILE" ]; then
  echo "錯誤：$PW_FILE 缺席或為空（先跑 deploy/generate-secrets.sh）" >&2
  exit 1
fi
PW="$(cat "$PW_FILE")"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.dev.yml)

# 設密＋LOGIN（psql 沿 tools/schema-gate exec -T 慣例；SQL 走 stdin heredoc、密碼不進 argv）。
"${COMPOSE[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U soybean -d soybean_admin_rust \
  --quiet --no-align --tuples-only <<SQL
ALTER ROLE reaper LOGIN PASSWORD '${PW}';
SQL
echo "ok: role reaper 已設 LOGIN＋密碼（值不回顯）"

# 自驗：以 reaper 憑證（TCP 密碼認證、走與 reaper_database_url 同認證路徑）SELECT 1。
# 密碼經 stdin 管線交給容器內 read→PGPASSWORD env（env 不進 process list）。
RESULT="$(printf '%s\n' "$PW" | "${COMPOSE[@]}" exec -T postgres sh -c \
  'read -r RPW; PGPASSWORD="$RPW" psql -h 127.0.0.1 -U reaper -d soybean_admin_rust -Atc "SELECT 1"')"
if [ "$RESULT" = "1" ]; then
  echo "ok: reaper 憑證連線驗證通過（SELECT 1）"
else
  echo "錯誤：reaper 憑證連線驗證失敗（回值：$RESULT）" >&2
  exit 1
fi
