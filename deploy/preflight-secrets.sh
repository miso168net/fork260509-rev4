#!/usr/bin/env bash
# deploy/preflight-secrets.sh — up 前十一機密檔預檢（001-compose-stack；007 增 captcha_secret、REVIEW-001-010 F001-1 補列；016 增 reaper_password／reaper_database_url／alert_webhook_url／grafana_admin_password；019 T027 增 CR 護欄＋composite↔leaf 一致性）
# 用法：./deploy/preflight-secrets.sh
#
# 為何：docker compose secrets 用 `file: …/*.txt` bind；source 檔缺時
#   compose 不報「缺 X 檔」而是自動建空目錄 → 容器拿到空／目錄 secret、錯誤訊息誤導
#   （如 DB 連線失敗、boot panic）、不指向真因。本預檢在 up 前指名缺檔。
#   019 起本腳本＝落點接線的 fail-loud 承載者（contracts P5.4）：缺檔／CR 劣化／
#   composite drift 一律非零退出＋指名，絕不讓服務靜默啟動失敗。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# SECRETS_DIR 解析（019 P5.1／P5.2 三處同刀齊改；generate／decrypt 同口徑）：
# 環境變數優先（與 compose 口徑一致）→ repo 根 .env 只嚴格解析 SECRETS_DIR 一行
# （★不整檔 source——compose 的 .env 允許不加引號的含空白值、井號語意亦與 shell 不同，
# 含錢字號小括號／反引號之值 source 時會被執行）→ 皆缺回退 repo 內 deploy/secrets。
if [ -z "${SECRETS_DIR:-}" ] && [ -f "$REPO_ROOT/.env" ]; then
    _line="$(grep '^SECRETS_DIR=' "$REPO_ROOT/.env" | tail -n 1 || true)"
    if [ -n "$_line" ]; then
        _val="${_line#SECRETS_DIR=}"
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
SECRETS_DIR="${SECRETS_DIR:-$SCRIPT_DIR/secrets}"

# 與 generate-secrets.sh 同一份十一機密清單（grafana_admin_password 僅 grafana[profiles:obs,metrics]
# 消費、但一律生成納入預檢——免 --profile obs 時 compose 對缺檔自動建空目錄、grafana $__file{}
# 讀到空密碼、admin 登入靜默壞）
REQUIRED=(postgres_password redis_password jwt_secret refresh_token_secret database_url redis_url captcha_secret reaper_password reaper_database_url alert_webhook_url grafana_admin_password)

missing=()
for name in "${REQUIRED[@]}"; do
    f="$SECRETS_DIR/${name}.txt"
    # 缺檔、或為目錄（compose 對缺 bind source 自動建的空目錄）、或空檔 → 視為缺
    if [ ! -f "$f" ] || [ ! -s "$f" ]; then
        missing+=("${name}.txt")
    fi
done

if [ "${#missing[@]}" -gt 0 ]; then
    echo "FAIL：缺少 ${#missing[@]} 個 secret 檔（$SECRETS_DIR）："
    for m in "${missing[@]}"; do echo "   - $m"; done
    echo ""
    echo "→ SOPS 管線重建：./deploy/decrypt-secrets.sh（8 支）→ ./deploy/generate-secrets.sh --compose-only（3 composite）。"
    echo "  （無加密檔情境仍可 ./deploy/generate-secrets.sh 一鍵生成 dev 亂數、缺的才補。）"
    exit 1
fi

# 019 T027①：CR 護欄——printf '%s' 管線寫檔應零 CR；任何 CR＝內容已劣化
# （CRLF 編輯器覆存／pty 流未剝 CR 直落檔），值進 URL／密碼尾即靜默壞。
CR="$(printf '\r')"
cr_hit=()
for name in "${REQUIRED[@]}"; do
    if LC_ALL=C grep -q "$CR" "$SECRETS_DIR/${name}.txt"; then
        cr_hit+=("${name}.txt")
    fi
done
if [ "${#cr_hit[@]}" -gt 0 ]; then
    echo "FAIL：下列 secret 檔含 CR 字元（內容劣化、值進連線字串即靜默壞）：${cr_hit[*]}"
    echo "→ 重跑 ./deploy/decrypt-secrets.sh（printf 管線寫檔、零 CR）後再驗。"
    exit 1
fi

# 019 T027②：composite↔leaf 一致性（複用 generate-secrets.sh 之期望值組合式）——
# 防「塞入密碼已過期的 database_url 也回 OK」；訊息只指名檔案、絕不印值。
PG_PASS="$(cat "$SECRETS_DIR/postgres_password.txt")"
RD_PASS="$(cat "$SECRETS_DIR/redis_password.txt")"
RP_PASS="$(cat "$SECRETS_DIR/reaper_password.txt")"
drift=()
[ "$(cat "$SECRETS_DIR/database_url.txt")" = "postgres://soybean:${PG_PASS}@postgres:5432/soybean_admin_rust" ] || drift+=("database_url.txt")
[ "$(cat "$SECRETS_DIR/redis_url.txt")" = "redis://:${RD_PASS}@redis:6379" ] || drift+=("redis_url.txt")
[ "$(cat "$SECRETS_DIR/reaper_database_url.txt")" = "postgres://reaper:${RP_PASS}@postgres:5432/soybean_admin_rust" ] || drift+=("reaper_database_url.txt")
if [ "${#drift[@]}" -gt 0 ]; then
    echo "FAIL：composite 與 leaf 不一致（drift）：${drift[*]}"
    echo "→ 跑 ./deploy/generate-secrets.sh --compose-only 由 leaf 現值重組 composite。"
    exit 1
fi

echo "OK：${#REQUIRED[@]} 個必須 secret 檔齊備且健康（$SECRETS_DIR；CR 零命中、composite 一致）。可 up。"
