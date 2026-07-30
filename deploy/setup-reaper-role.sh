#!/usr/bin/env bash
# deploy/setup-reaper-role.sh — 016-observability T022：reaper role 設密＋LOGIN（部署腳本側）。
#
# 分工（data-model §5、research R5、ADR 0072）：
#   m012 migration＝CREATE ROLE reaper NOLOGIN＋GRANT（零密碼）；本腳本＝ALTER ROLE reaper
#   LOGIN PASSWORD（密碼讀自 $SECRETS_DIR/reaper_password.txt；★019 US3 起落點由 repo 根 .env
#   的 SECRETS_DIR 決定、未設才回退 repo 內 deploy/secrets——解析口徑見下）。
# 密碼紀律（FR-013）：SQL 走 psql stdin heredoc——密碼零進 host process list、零進版本庫；
#   輸出只印狀態不印值。可重跑（ALTER ROLE 冪等）。
# 前置：stack 已 up（postgres healthy）＋m012 已套用（role 不存在→psql 非零退出 fail-loud）
#   ＋deploy/generate-secrets.sh 已產 reaper_password.txt。
# 用法：bash deploy/setup-reaper-role.sh
set -euo pipefail

cd "$(dirname "$0")/.."

# SECRETS_DIR 解析（019 P5.2 五支賦值型消費者同刀齊改之一；generate／preflight／decrypt
# ／tools/secret-value-guard.py 同口徑，消費者聯集七處＝契約 P5.1）：
# 環境變數優先（與 compose 口徑一致）→ repo 根 .env 只嚴格解析 SECRETS_DIR 一行
# （★不整檔 source——compose 的 .env 允許不加引號的含空白值、井號語意亦與 shell 不同，
# 含錢字號小括號／反引號之值 source 時會被執行）→ 皆缺回退 repo 內 deploy/secrets。
# ★偵測寬、取值窄（019 U4 quality 修；五處解析器同刀齊改）：compose 的 .env 解析器接受
# UTF-8 BOM／行首空白／export 前綴／等號兩側空白／CRLF 行尾，行首錨定 `SECRETS_DIR=` 的窄
# 樣式對這五形一律漏認並**靜默回退**舊落點（實測 compose v5.3.1 五形皆解析為新落點）＝契約
# P5.1 違反後果欄的「compose 讀新落點、腳本查舊落點」。故偵測用寬樣式撈出 compose 會讀到的
# 那一行、再對其值套下方嚴格白名單：寬進窄出，永不落入靜默回退。
# ★空字串邊界（019 U4 quality 修；五支賦值型解析器同刀齊改）：「已匯出但為空」≠「未設」——
# shell 環境已勝出 .env，compose 的 ${SECRETS_DIR:-./deploy/secrets} 對空字串直接吃預設值、
# 回退 repo 內舊落點且**不讀 .env 該鍵**；而 [ -z ] 把空字串當未設、續往 .env 取新落點＝
# 腳本讀新落點、compose 掛舊落點，即 P5.1 違反後果欄那條路的另一入口，且破在靜默方向。
# 空字串無合法用途（要走回退請 unset），故吵鬧失敗指名真因、不代 operator 猜邊。
if [ "${SECRETS_DIR+set}" = set ] && [ -z "$SECRETS_DIR" ]; then
  echo "FAIL：SECRETS_DIR 已匯出為空字串——compose 會忽略 .env 並回退 ./deploy/secrets（repo 內舊落點）。" >&2
  echo "→ 要用 .env 的值：先 unset SECRETS_DIR；要指定他處落點：匯出絕對路徑。" >&2
  exit 1
fi
if [ -z "${SECRETS_DIR:-}" ] && [ -f .env ]; then
  _line="$(sed -e "1s/^$(printf '\357\273\277')//" -e 's/\r$//' .env \
           | grep -E '^[[:space:]]*(export[[:space:]]+)?SECRETS_DIR[[:space:]]*=' | tail -n 1 || true)"
  if [ -n "$_line" ]; then
    _val="$(printf '%s\n' "$_line" \
            | sed -E 's/^[[:space:]]*(export[[:space:]]+)?SECRETS_DIR[[:space:]]*=[[:space:]]*//; s/[[:space:]]+$//')"
    case "$_val" in
      *[!A-Za-z0-9_/.-]*|"")
        echo "FAIL：.env 之 SECRETS_DIR 為空或含空白／shell 元字元——拒用（產檔約束見 .env.example）" >&2
        exit 1 ;;
      /*) SECRETS_DIR="$_val" ;;
      *)
        echo "FAIL：.env 之 SECRETS_DIR 必須為絕對路徑字面（compose 不做 shell 展開）——見 .env.example" >&2
        exit 1 ;;
    esac
  fi
fi
SECRETS_DIR="${SECRETS_DIR:-deploy/secrets}"
# ★相對值錨定基準＝repo 根（019 U4 quality 修；五支同刀齊改、契約 P5.1）：此處 `$PWD` 並非
# 呼叫端 CWD——本腳本首行 `cd "$(dirname "$0")/.."` 已把 CWD 換成**自腳本位置推導**的 repo 根，
# 故 `$PWD` 等同該推導值、與呼叫端無關（★若日後移除該 `cd`，本行須同步改為自 BASH_SOURCE
# 推導，否則落點改隨呼叫端漂、與 compose 分裂）。
case "$SECRETS_DIR" in /*) ;; *) SECRETS_DIR="$PWD/$SECRETS_DIR" ;; esac

PW_FILE="$SECRETS_DIR/reaper_password.txt"
if [ ! -s "$PW_FILE" ]; then
  echo "錯誤：$PW_FILE 缺席或為空（先跑 deploy/decrypt-secrets.sh；無加密檔情境＝generate-secrets.sh）" >&2
  exit 1
fi
PW="$(cat "$PW_FILE")"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.dev.yml)

# 設密＋LOGIN（psql 沿 tools/schema-gate.py exec -T 慣例；SQL 走 stdin heredoc、密碼不進 argv）。
"${COMPOSE[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U soybean -d soybean_admin_rust \
  --quiet --no-align --tuples-only <<SQL
ALTER ROLE reaper LOGIN PASSWORD '${PW}';
SQL
echo "ok: role reaper 已設 LOGIN＋密碼（值不回顯）"

# 自驗：以 reaper 憑證 SELECT 1——★必走 -h postgres 容器網段（scram 真驗密）；容器內
# 127.0.0.1 在 pg_hba 屬 trust、密碼不參與認證＝驗不到密碼（L-154）。與 reaper_database_url
# 同認證路徑（host=postgres、scram-sha-256）。密碼經 stdin 管線交給容器內 read→PGPASSWORD
# env（env 不進 process list）。
RESULT="$(printf '%s\n' "$PW" | "${COMPOSE[@]}" exec -T postgres sh -c \
  'read -r RPW; PGPASSWORD="$RPW" psql -h postgres -U reaper -d soybean_admin_rust -Atc "SELECT 1"')"
if [ "$RESULT" = "1" ]; then
  echo "ok: reaper 憑證連線驗證通過（SELECT 1）"
else
  echo "錯誤：reaper 憑證連線驗證失敗（回值：${RESULT}）" >&2
  exit 1
fi
