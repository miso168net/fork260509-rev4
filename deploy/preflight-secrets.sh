#!/usr/bin/env bash
# deploy/preflight-secrets.sh — up 前十三機密檔預檢（001-compose-stack；007 增 captcha_secret、REVIEW-001-010 F001-1 補列；016 增 reaper_password／reaper_database_url／alert_webhook_url／grafana_admin_password；019 T027 增 CR 護欄＋composite↔leaf 一致性；B-123 增權限面三斷言、B-119 增佔位字面 WARN；020 增 smtp_password／email_verify_secret）
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
# SECRETS_DIR 解析（019 P5.2 五支賦值型消費者同刀齊改之一；generate／decrypt／
# setup-reaper-role／tools/secret-value-guard.py 同口徑，消費者聯集七處＝契約 P5.1）：
# 環境變數優先（與 compose 口徑一致）→ repo 根 .env 只嚴格解析 SECRETS_DIR 一行
# （★不整檔 source——compose 的 .env 允許不加引號的含空白值、井號語意亦與 shell 不同，
# 含錢字號小括號／反引號之值 source 時會被執行）→ 皆缺回退 repo 內 deploy/secrets。
# ★偵測寬、取值窄（019 U4 quality 修；五處解析器同刀齊改）：compose 的 .env 解析器接受
# UTF-8 BOM／行首空白／export 前綴／等號兩側空白／CRLF 行尾，行首錨定 `SECRETS_DIR=` 的窄
# 樣式對這五形一律漏認並**靜默回退**舊落點（實測 compose v5.3.1 五形皆解析為新落點）＝契約
# P5.1 違反後果欄的「compose 讀新落點、腳本查舊落點」——本腳本正是 fail-loud 承載者，回退
# 即「preflight 查舊落點回 OK、compose 掛新落點」。故偵測用寬樣式撈出 compose 會讀到的那一
# 行、再對其值套下方嚴格白名單：寬進窄出，永不落入靜默回退。
# ★空字串邊界（019 U4 quality 修；五支賦值型解析器同刀齊改）：「已匯出但為空」≠「未設」——
#   shell 環境已勝出 .env，compose 的 ${SECRETS_DIR:-./deploy/secrets} 對空字串直接吃預設值、
#   回退 repo 內舊落點且**不讀 .env 該鍵**；而 [ -z ] 把空字串當未設、續往 .env 取新落點＝
#   腳本查新落點、compose 掛舊落點，即 P5.1 違反後果欄那條路的另一入口，且破在靜默方向
#   （本腳本印「可 up」rc=0，compose 卻在 repo 內自動建空目錄當 secret 掛入容器）。
#   空字串無合法用途（要走回退請 unset），故吵鬧失敗指名真因、不代 operator 猜邊。
if [ "${SECRETS_DIR+set}" = set ] && [ -z "$SECRETS_DIR" ]; then
    echo "FAIL：SECRETS_DIR 已匯出為空字串——compose 會忽略 .env 並回退 ./deploy/secrets（repo 內舊落點）。" >&2
    echo "→ 要用 .env 的值：先 unset SECRETS_DIR；要指定他處落點：匯出絕對路徑。" >&2
    exit 1
fi
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
# ★相對值錨定基準＝repo 根（019 U4 quality 修；五支賦值型解析器同刀齊改、契約 P5.1）：
# compose 以**專案目錄**（＝repo 根）解析相對值、guard 以 repo 根 join；本腳本若逕用相對值
# 即以 **CWD** 錨定＝自 repo 子目錄執行時本檢查與 compose 看的是**不同目錄**，於是出現
# 「preflight 全綠、compose 掛空目錄」的假綠（本檢查正是 fail-loud 承載者、假綠最致命）。
case "$SECRETS_DIR" in /*) ;; *) SECRETS_DIR="$REPO_ROOT/$SECRETS_DIR" ;; esac

# 與 generate-secrets.sh 同一份十三機密清單（grafana_admin_password 僅 grafana[profiles:obs,metrics]
# 消費、但一律生成納入預檢——免 --profile obs 時 compose 對缺檔自動建空目錄、grafana $__file{}
# 讀到空密碼、admin 登入靜默壞；020 增 smtp_password／email_verify_secret 兩 leaf）
REQUIRED=(postgres_password redis_password jwt_secret refresh_token_secret database_url redis_url captcha_secret reaper_password reaper_database_url alert_webhook_url grafana_admin_password smtp_password email_verify_secret)

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
    echo "→ SOPS 管線重建：./deploy/decrypt-secrets.sh（10 支）→ ./deploy/generate-secrets.sh --compose-only（3 composite）。"
    echo "  （無加密檔情境仍可 ./deploy/generate-secrets.sh 一鍵生成 dev 亂數、缺的才補。）"
    exit 1
fi

# B-123：權限面三斷言（縱深防禦、超出契約 P5.6 要求面）——目錄 mode 700／檔 mode 644／
# 檔 owner 非 root。decrypt-secrets.sh 每次寫出即自證此形（P4.4／P4.6 目錄 700、P4.7 檔 644），
# 但落點檔被人手改（chmod 600、目錄 777、sudo 建檔）後現檢照樣全綠——而那正是 P4.5／P4.7
# 自陳「只在開 obs／metrics 軌時才炸」的失敗形（grafana uid 472／postgres-exporter 65534／
# redis-exporter 59000 讀 /run/secrets/* 全 Permission denied）。本斷言把它前移到 up 之前指名。
# 置於 CR／composite 檢查之前：owner=root＋600 之檔會讓後方 cat 直接 Permission denied，
# 先斷言權限才能保證後方檢查的錯誤訊息不失真。
perm_hit=()
DIR_MODE="$(stat -c '%a' "$SECRETS_DIR")"
if [ "$DIR_MODE" != "700" ]; then
    perm_hit+=("（目錄）$SECRETS_DIR mode=$DIR_MODE｜修復：chmod 700 $SECRETS_DIR")
fi
for name in "${REQUIRED[@]}"; do
    f="$SECRETS_DIR/${name}.txt"
    F_MODE="$(stat -c '%a' "$f")"
    F_UID="$(stat -c '%u' "$f")"
    if [ "$F_MODE" != "644" ]; then
        perm_hit+=("${name}.txt mode=$F_MODE｜修復：chmod 644 $f")
    fi
    if [ "$F_UID" -eq 0 ]; then
        perm_hit+=("${name}.txt owner=$(stat -c '%U' "$f")（不得為 root）｜修復：sudo chown $(id -un) $f")
    fi
done
if [ "${#perm_hit[@]}" -gt 0 ]; then
    echo "FAIL：權限面不符（目錄須 700、檔須 644 且 owner 非 root）——這正是 P4.5／P4.7 自陳"
    echo "      「只在開 obs／metrics 軌才炸」的失敗形（grafana uid 472／postgres-exporter 65534／"
    echo "      redis-exporter 59000 讀 /run/secrets/* 全 Permission denied）；本斷言把它前移到 up 之前："
    for p in "${perm_hit[@]}"; do echo "   - $p"; done
    if [ "$(stat -f -c '%T' "$SECRETS_DIR")" = "v9fs" ]; then
        echo "→ 落點在 /mnt/* 之 drvfs（9p）：chmod 結構性 no-op、mode 恆讀 777，本紅字是特性不是誤報——"
        echo "  拍板落點應在 ext4（如 \$HOME/.cache/fork260509-rev4/secrets；ADR 0080／0084），請遷落點而非改本檢查。"
    fi
    exit 1
fi

# 019 T027①：CR 護欄——printf '%s' 管線寫檔應零 CR；任何 CR＝內容已劣化
# （CRLF 編輯器覆存／pty 流未剝 CR 直落檔），值進 URL／密碼尾即靜默壞。
# ★U4 quality 補 LF 護欄：CR 護欄照不到「尾端多一個 LF」，而下方 composite 一致性檢查用
#   命令替換取值比較（$(cat) 剝尾端換行）對它**結構性失明**——實測 redis_password.txt 尾多
#   一個 LF 時 preflight 仍回「齊備且健康、可 up」rc=0，而 compose 會把 15 byte 的密碼掛進
#   redis 容器、把內嵌 14 byte 版本的 redis_url 掛進 rust-api，認證必失敗。尾端換行正是編輯器
#   覆存最常見的產物（與 CRLF 同一個編輯器、同一次覆存）。
#   判準＝檔案零換行字元（P4.1／P5.7 之 printf '%s' 寫檔形不變式的可機檢投影）：
#   比對 stat 位元組數與剝除 CR／LF 後的位元組數，兩者不等即劣化。
CR="$(printf '\r')"
cr_hit=()
nl_hit=()
for name in "${REQUIRED[@]}"; do
    f="$SECRETS_DIR/${name}.txt"
    if LC_ALL=C grep -q "$CR" "$f"; then
        cr_hit+=("${name}.txt")
    elif [ "$(stat -c '%s' "$f")" -ne "$(LC_ALL=C tr -d '\n' < "$f" | wc -c)" ]; then
        nl_hit+=("${name}.txt")
    fi
done
if [ "${#cr_hit[@]}" -gt 0 ]; then
    echo "FAIL：下列 secret 檔含 CR 字元（內容劣化、值進連線字串即靜默壞）：${cr_hit[*]}"
    echo "→ 重跑 ./deploy/decrypt-secrets.sh（printf 管線寫檔、零 CR）後再驗。"
    exit 1
fi
if [ "${#nl_hit[@]}" -gt 0 ]; then
    echo "FAIL：下列 secret 檔含換行字元（printf '%s' 寫檔形應零換行；尾端換行會讓 composite"
    echo "      一致性檢查失明、容器拿到與 composite 不符的值）：${nl_hit[*]}"
    echo "→ 重跑 ./deploy/decrypt-secrets.sh（10 支）＋ ./deploy/generate-secrets.sh --compose-only（3 composite）後再驗。"
    exit 1
fi

# 019 T027②：composite↔leaf 一致性（複用 generate-secrets.sh 之期望值組合式）——
# 防「塞入密碼已過期的 database_url 也回 OK」；訊息只指名檔案、絕不印值。
# ★比對走 printf 接 cmp 的**位元組**比對（與 decrypt P4.5 同一形）：命令替換會剝尾端換行，
#   字串相等比較對尾端換行失明（上方 LF 護欄已先擋、此處為縱深防禦、不靠護欄的執行序）。
PG_PASS="$(cat "$SECRETS_DIR/postgres_password.txt")"
RD_PASS="$(cat "$SECRETS_DIR/redis_password.txt")"
RP_PASS="$(cat "$SECRETS_DIR/reaper_password.txt")"
drift=()
printf '%s' "postgres://soybean:${PG_PASS}@postgres:5432/soybean_admin_rust" | cmp -s - "$SECRETS_DIR/database_url.txt" || drift+=("database_url.txt")
printf '%s' "redis://:${RD_PASS}@redis:6379" | cmp -s - "$SECRETS_DIR/redis_url.txt" || drift+=("redis_url.txt")
printf '%s' "postgres://reaper:${RP_PASS}@postgres:5432/soybean_admin_rust" | cmp -s - "$SECRETS_DIR/reaper_database_url.txt" || drift+=("reaper_database_url.txt")
if [ "${#drift[@]}" -gt 0 ]; then
    echo "FAIL：composite 與 leaf 不一致（drift）：${drift[*]}"
    echo "→ 跑 ./deploy/generate-secrets.sh --compose-only 由 leaf 現值重組 composite。"
    exit 1
fi

# B-119：已知佔位字面清單比對（★WARN 不阻擋、rc 不因它非零——佔位期照設計是可過的合法
# 狀態；升級成阻擋屬拍板級、本單元明文不做）。清單字面逐字取自 generate-secrets.sh 之
# gen_placeholder 呼叫處（唯一佔位源頭）；清單形設計、未來新增佔位即加一元素。
# 比對走 printf 接 cmp 的位元組比對（與 composite 檢查同一形）、只指名檔案、絕不印內容。
PLACEHOLDER_LITERALS=("https://CHANGE-ME.invalid/alert-webhook-placeholder")
ph_hit=()
for name in "${REQUIRED[@]}"; do
    f="$SECRETS_DIR/${name}.txt"
    for lit in "${PLACEHOLDER_LITERALS[@]}"; do
        if printf '%s' "$lit" | cmp -s - "$f"; then
            ph_hit+=("${name}.txt")
            break
        fi
    done
done
if [ "${#ph_hit[@]}" -gt 0 ]; then
    echo "WARN：下列 secret 檔仍為生成腳本的佔位字面（照設計可 up；留佔位的唯一徵狀＝該功能"
    echo "      靜默失效，如告警投遞不出）：${ph_hit[*]}"
    echo "→ 填真值走 RUNBOOK §7 對應列（alert_webhook_url＝直接編輯檔＋restart grafana）；"
    echo "  填完必接 §15.4 re-encrypt 回寫加密檔，否則下次 decrypt 判 DIFF 另存 .new。"
fi

echo "OK：${#REQUIRED[@]} 個必須 secret 檔齊備且健康（$SECRETS_DIR；權限 700/644、CR 零命中、composite 一致）。可 up。"
