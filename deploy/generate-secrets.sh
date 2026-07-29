#!/usr/bin/env bash
# deploy/generate-secrets.sh — rev4-admin 十一機密一鍵生成（001-compose-stack；007 增 captcha_secret；
# 016 增 reaper_password／reaper_database_url／alert_webhook_url／grafana_admin_password）
# 用法：./deploy/generate-secrets.sh [--force|--compose-only]
#
# 十一機密（$SECRETS_DIR/*.txt；落點解析見下、未設回退 deploy/secrets）：
#   leaf      postgres_password（hex 24、URL-safe）／redis_password（hex 24、URL-safe）
#   leaf      jwt_secret（base64 48）／refresh_token_secret（base64 48）
#   leaf      captcha_secret（base64 48；007-login-throttle challenge HS256）
#   leaf      reaper_password（hex 24、URL-safe；016 reaper 最小權限 DB 身分、設密另走部署腳本）
#   leaf      grafana_admin_password（base64 24；016 grafana GF $__file{} 檔注入、非 URL）
#   composite database_url ＝ postgres://soybean:<postgres_password>@postgres:5432/soybean_admin_rust
#   composite redis_url    ＝ redis://:<redis_password>@redis:6379
#   composite reaper_database_url ＝ postgres://reaper:<reaper_password>@postgres:5432/soybean_admin_rust
#   佔位      alert_webhook_url（顯眼佔位 URL；真值 user 自填、--force 不重置——重置法＝刪檔重跑）
#
# 設計：
#   - openssl 全跑 alpine/openssl 容器——host 除 docker 外零依賴。
#     （輔助映像沿 latest 浮動 tag＝拍板豁免 ADR 0022；勿改釘數字版。）
#   - jwt／refresh 用 base64（不進 URL）；postgres／redis 密碼用 hex（URL-safe，
#     嵌入連線字串不被 + / = 破壞）。
#   - composite 由 leaf 檔案內容組合（dual-write 同源）、絕不獨立亂數生成。
#
# 冪等語意：
#   - 零參數：已存在跳過（SKIPPED）、缺則補（GENERATED）。
#   - --force：亂數生成的十支全重生；alert_webhook_url 屬 user 自填設定值、
#     不在 --force 範圍（重生佔位無輪替價值、反毀 user 已填真值）。
#   - --compose-only（019 P5.5）：只重組 3 composite；8 支來源檔（7 leaf＋alert_webhook_url）
#     缺任一＝報錯退出、絕不代生成——防靜默造新亂數（每台機器各拿到不同值、與加密檔脫鉤）。
#   - dual-write 連動：composite 以「期望值 vs 檔案現值」逐位元組比對判定——涵蓋
#     ①leaf 本次重生 ②leaf 曾單獨改動（比 composite 新） ③僅缺 composite
#     三種情境，任何不一致一律重寫 composite、絕不留兩處不一致。
#   - 摘要只印檔名＋狀態（GENERATED／SKIPPED）、絕不印機密值。

set -euo pipefail
# 機密檔出生即 600（原生 Linux 檔系統生效）；終值於 Step 4 收斂＝目錄 700／檔 644（019 P4.7）
umask 077

FORCE=0
COMPOSE_ONLY=0
case "${1:-}" in
    --force)        FORCE=1 ;;
    --compose-only) COMPOSE_ONLY=1 ;;
    "")             ;;
    *) echo "用法：$0 [--force|--compose-only]" >&2; exit 64 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# SECRETS_DIR 解析（019 P5.2 五支賦值型消費者同刀齊改之一；decrypt／preflight／
# setup-reaper-role／tools/secret-value-guard.py 同口徑，消費者聯集七處＝契約 P5.1）：
# 環境變數優先（與 compose 口徑一致）→ repo 根 .env 只嚴格解析 SECRETS_DIR 一行
# （★不整檔 source——compose 的 .env 允許不加引號的含空白值、井號語意亦與 shell 不同，
# 含錢字號小括號／反引號之值 source 時會被執行）→ 皆缺回退 repo 內 deploy/secrets。
# ★偵測寬、取值窄（019 U4 quality 修；五處解析器同刀齊改）：compose 的 .env 解析器接受
# UTF-8 BOM／行首空白／export 前綴／等號兩側空白／CRLF 行尾，行首錨定 `SECRETS_DIR=` 的窄
# 樣式對這五形一律漏認並**靜默回退**舊落點（實測 compose v5.3.1 五形皆解析為新落點）＝契約
# P5.1 違反後果欄的「compose 讀新落點、腳本查舊落點」。故偵測用寬樣式撈出 compose 會讀到的
# 那一行、再對其值套下方嚴格白名單：寬進窄出，永不落入靜默回退。
if [ -z "${SECRETS_DIR:-}" ] && [ -f "$REPO_ROOT/.env" ]; then
    _line="$(sed -e "1s/^$(printf '\357\273\277')//" -e 's/\r$//' "$REPO_ROOT/.env" \
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
SECRETS_DIR="${SECRETS_DIR:-$SCRIPT_DIR/secrets}"
mkdir -p "$SECRETS_DIR"

# --compose-only 前置斷言（019 P5.5）：8 支來源檔在位且非空、缺任一即報錯退出（絕不代生成）
if [ "$COMPOSE_ONLY" -eq 1 ]; then
    MISSING_SRC=()
    for name in postgres_password redis_password jwt_secret refresh_token_secret \
                captcha_secret reaper_password grafana_admin_password alert_webhook_url; do
        [ -s "$SECRETS_DIR/${name}.txt" ] || MISSING_SRC+=("${name}.txt")
    done
    if [ "${#MISSING_SRC[@]}" -ne 0 ]; then
        echo "FAIL：--compose-only 缺來源檔（不生成、防靜默造新亂數）：${MISSING_SRC[*]}" >&2
        echo "      → 先跑 ./deploy/decrypt-secrets.sh 重建 8 支（7 leaf＋alert_webhook_url）後重試。" >&2
        exit 1
    fi
fi

OPENSSL_IMG="alpine/openssl:latest"
# 離線／限流時 image 已 cache 則免 pull（docker pull 在 set -e 下會 abort、即使本機已有）；
# inspect 命中即跳過。
docker image inspect "$OPENSSL_IMG" >/dev/null 2>&1 || docker pull -q "$OPENSSL_IMG" >/dev/null

# gen_rand <openssl-rand-args...>：回傳隨機值（command substitution 已去尾換行）
gen_rand() {
    docker run --rm "$OPENSSL_IMG" rand "$@"
}

# 各機密狀態（GENERATED／SKIPPED）
declare -A STATUS

# 機密檔缺席時 docker 可能於該路徑自動建出「目錄」佔位（缺檔直接 up 的殘骸）——
# 空目錄自動清除、非空指名退出，讓 preflight→generate 的恢復路徑自足
clear_dir_placeholder() {
    local file="$1"
    if [ -d "$file" ]; then
        rmdir "$file" 2>/dev/null || {
            echo "FAIL：$file 是非空目錄（無法自動清除）——請手動移除後重跑" >&2
            exit 1
        }
        echo "  $(basename "$file") 為目錄佔位（缺檔曾直接 up 的殘骸）→ 已清除"
    fi
}

# ============================================================
# Step 1: leaf secret ×7
# ============================================================
echo "=== Step 1: 生成 leaf secret ==="

gen_leaf() {
    local name="$1"; shift
    local file="$SECRETS_DIR/${name}.txt"
    clear_dir_placeholder "$file"
    if [ ! -f "$file" ] || [ "$FORCE" -eq 1 ]; then
        local val
        val="$(gen_rand "$@")"
        printf '%s' "$val" > "$file"
        STATUS["$name"]="GENERATED"
    else
        STATUS["$name"]="SKIPPED"
    fi
}

if [ "$COMPOSE_ONLY" -eq 0 ]; then
    gen_leaf "postgres_password"    -hex 24
    gen_leaf "redis_password"       -hex 24
    gen_leaf "jwt_secret"           -base64 48
    gen_leaf "refresh_token_secret" -base64 48
    gen_leaf "captcha_secret"       -base64 48
    # reaper_password（016 obs）：reaper 最小權限 DB 身分之密碼；hex＝URL-safe（嵌入
    # reaper_database_url 不被 + / = 破壞）；ALTER ROLE 設密走部署腳本、密碼絕不進 migration。
    gen_leaf "reaper_password"      -hex 24
    # grafana_admin_password（016 obs）：僅經 GF_SECURITY_ADMIN_PASSWORD=$__file{...} 檔注入、
    # 非 URL → base64 安全（rev3 018 同形）。
    gen_leaf "grafana_admin_password" -base64 24
else
    # --compose-only：前置斷言已證 7 leaf 在位非空、此處只記狀態（不生成、不改動）
    for name in postgres_password redis_password jwt_secret refresh_token_secret \
                captcha_secret reaper_password grafana_admin_password; do
        STATUS["$name"]="PRESENT"
    done
fi

# ============================================================
# Step 2: composite secret ×3（由 leaf 組合、dual-write 連動）
# ============================================================
echo "=== Step 2: 生成 composite secret（dual-write 由 leaf 組合）==="

# gen_composite <name> <expected-value>：
#   檔案缺、--force、或現值 ≠ 期望值（leaf 重生／單獨改動＝drift）→ 重寫（GENERATED）；
#   否則 SKIPPED。內容比對取代「本次是否重生」旗標——連 leaf 在腳本之外被改動的 drift 也修復。
# ★比對走 printf 接 cmp 的**位元組**比對（與 decrypt P4.5、preflight T027② 同一形；019 U4
#   quality 修）：命令替換 $(cat) 會剝掉尾端換行，字串相等比較對「檔尾多一個 LF」結構性失明
#   ——實測 redis_url.txt 尾多一個 LF 時判為相等、印 SKIPPED、rc=0，劣化未修復（P5.7 之
#   byte-identical 不變式失效）。
gen_composite() {
    local name="$1"
    local value="$2"
    local file="$SECRETS_DIR/${name}.txt"
    clear_dir_placeholder "$file"
    if [ -f "$file" ] && [ "$FORCE" -eq 0 ] && printf '%s' "$value" | cmp -s - "$file"; then
        STATUS["$name"]="SKIPPED"
    else
        if [ -f "$file" ] && [ "$FORCE" -eq 0 ]; then
            echo "  ${name}.txt 與依賴 leaf 不一致（dual-write drift）→ 連動重寫"
        fi
        printf '%s' "$value" > "$file"
        STATUS["$name"]="GENERATED"
    fi
}

PG_PASS="$(cat "$SECRETS_DIR/postgres_password.txt")"
RD_PASS="$(cat "$SECRETS_DIR/redis_password.txt")"
RP_PASS="$(cat "$SECRETS_DIR/reaper_password.txt")"

gen_composite "database_url" "postgres://soybean:${PG_PASS}@postgres:5432/soybean_admin_rust"
gen_composite "redis_url"    "redis://:${RD_PASS}@redis:6379"
gen_composite "reaper_database_url" "postgres://reaper:${RP_PASS}@postgres:5432/soybean_admin_rust"

# ============================================================
# Step 3: 佔位 secret ×1（user 自填、--force 不重置）
# ============================================================
echo "=== Step 3: 佔位 secret（真值 user 自填）==="

# alert_webhook_url（016 obs）：grafana contact point 經 $__file{/run/secrets/alert_webhook_url}
# 讀取；僅缺檔才寫入顯眼佔位 URL（.invalid TLD 保留域、必不可達）、既有檔（含 user 已填
# 真值）一律不動——--force 也不重置；要重置＝刪檔重跑。
gen_placeholder() {
    local name="$1"
    local value="$2"
    local file="$SECRETS_DIR/${name}.txt"
    clear_dir_placeholder "$file"
    if [ -f "$file" ]; then
        STATUS["$name"]="SKIPPED"
    else
        printf '%s' "$value" > "$file"
        STATUS["$name"]="GENERATED"
    fi
}

if [ "$COMPOSE_ONLY" -eq 0 ]; then
    gen_placeholder "alert_webhook_url" "https://CHANGE-ME.invalid/alert-webhook-placeholder"
else
    # --compose-only：前置斷言已證在位非空（值多為 user 已填真值、絕不動）
    STATUS["alert_webhook_url"]="PRESENT"
fi

# ============================================================
# Step 4: 權限收斂（019 T026／P4.7）
# ============================================================
# WSL2 drvfs（/mnt/*）上 chmod 為 no-op、仍照做（原生 Linux 檔系統正確生效）。
# 檔 644（非 600）：grafana(472)／postgres-exporter(65534)／redis-exporter(59000) 三個
# 非 root service 要讀 /run/secrets——600 只在開 obs／metrics 軌時才炸；暴露面由目錄 700 承載。
chmod 700 "$SECRETS_DIR"
chmod 644 "$SECRETS_DIR"/*.txt

# ============================================================
# Step 5: 摘要（只印檔名＋狀態、絕不印值）
# ============================================================
echo ""
echo "=== Secret 生成摘要 ==="
for name in postgres_password redis_password jwt_secret refresh_token_secret \
            captcha_secret reaper_password grafana_admin_password database_url \
            redis_url reaper_database_url alert_webhook_url; do
    printf "  %-26s %s\n" "${name}.txt" "${STATUS[$name]}"
done
echo ""
echo "完成。$SECRETS_DIR/*.txt 已就緒（明文不進版本庫）。"
