#!/usr/bin/env bash
# deploy/generate-secrets.sh — rev4-admin 十機密一鍵生成（001-compose-stack；007 增 captcha_secret；
# 016 增 reaper_password／reaper_database_url／alert_webhook_url）
# 用法：./deploy/generate-secrets.sh [--force]
#
# 十機密（deploy/secrets/*.txt）：
#   leaf      postgres_password（hex 24、URL-safe）／redis_password（hex 24、URL-safe）
#   leaf      jwt_secret（base64 48）／refresh_token_secret（base64 48）
#   leaf      captcha_secret（base64 48；007-login-throttle challenge HS256）
#   leaf      reaper_password（hex 24、URL-safe；016 reaper 最小權限 DB 身分、設密另走部署腳本）
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
#   - --force：亂數生成的九支全重生；alert_webhook_url 屬 user 自填設定值、
#     不在 --force 範圍（重生佔位無輪替價值、反毀 user 已填真值）。
#   - dual-write 連動：composite 以「期望值 vs 檔案現值」逐位元組比對判定——涵蓋
#     ①leaf 本次重生 ②leaf 曾單獨改動（比 composite 新） ③僅缺 composite
#     三種情境，任何不一致一律重寫 composite、絕不留兩處不一致。
#   - 摘要只印檔名＋狀態（GENERATED／SKIPPED）、絕不印機密值。

set -euo pipefail
# 機密檔出生即 600（原生 Linux 檔系統生效；Step 4 的 chmod 變成雙保險）
umask 077

FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_DIR="$SCRIPT_DIR/secrets"
mkdir -p "$SECRETS_DIR"

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
# Step 1: leaf secret ×6
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

gen_leaf "postgres_password"    -hex 24
gen_leaf "redis_password"       -hex 24
gen_leaf "jwt_secret"           -base64 48
gen_leaf "refresh_token_secret" -base64 48
gen_leaf "captcha_secret"       -base64 48
# reaper_password（016 obs）：reaper 最小權限 DB 身分之密碼；hex＝URL-safe（嵌入
# reaper_database_url 不被 + / = 破壞）；ALTER ROLE 設密走部署腳本、密碼絕不進 migration。
gen_leaf "reaper_password"      -hex 24

# ============================================================
# Step 2: composite secret ×3（由 leaf 組合、dual-write 連動）
# ============================================================
echo "=== Step 2: 生成 composite secret（dual-write 由 leaf 組合）==="

# gen_composite <name> <expected-value>：
#   檔案缺、--force、或現值 ≠ 期望值（leaf 重生／單獨改動＝drift）→ 重寫（GENERATED）；
#   否則 SKIPPED。內容比對取代「本次是否重生」旗標——連 leaf 在腳本之外被改動的 drift 也修復。
gen_composite() {
    local name="$1"
    local value="$2"
    local file="$SECRETS_DIR/${name}.txt"
    clear_dir_placeholder "$file"
    if [ -f "$file" ] && [ "$FORCE" -eq 0 ] && [ "$(cat "$file")" = "$value" ]; then
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

gen_placeholder "alert_webhook_url" "https://CHANGE-ME.invalid/alert-webhook-placeholder"

# ============================================================
# Step 4: 權限收緊
# ============================================================
# WSL2 drvfs（/mnt/*）上 chmod 為 no-op、仍照做（原生 Linux 檔系統正確生效）
chmod 600 "$SECRETS_DIR"/*.txt

# ============================================================
# Step 5: 摘要（只印檔名＋狀態、絕不印值）
# ============================================================
echo ""
echo "=== Secret 生成摘要 ==="
for name in postgres_password redis_password jwt_secret refresh_token_secret \
            captcha_secret reaper_password database_url redis_url \
            reaper_database_url alert_webhook_url; do
    printf "  %-26s %s\n" "${name}.txt" "${STATUS[$name]}"
done
echo ""
echo "完成。deploy/secrets/*.txt 已就緒（gitignored、不進版本庫）。"
