#!/usr/bin/env bash
# deploy/decrypt-secrets.sh — 019 解密管線：deploy/secrets.dev.enc.yaml → $SECRETS_DIR/*.txt
# 契約＝contracts/secret-pipeline.md §P4（fail-loud：斷言不符＝零寫入＋非零退出＋指名）
#
# 用法：自 repo 根、有 tty 的終端執行 ./deploy/decrypt-secrets.sh
#   B′ 私鑰＝passphrase 加殼 identity → 每次執行恰跳 1 次 passphrase 提示（單 recipient 基線）。
#   ★提示行與解密輸出同流被暫存檔捕捉（wrapper -t＝容器 pty、docker 單流輸出）——畫面可能
#     不顯示提示，依本腳本印出的預告直接輸入 passphrase 後按 Enter 即可。
#
# 要點對照：
#   P4.2 tty 守衛：非互動吵鬧失敗、不 hang、不寫壞檔
#   P4.4／P4.6 自建 0700 子目錄＋權限自證（縱深防禦、與落點無關；ADR 0080 決策 4）
#   P4.3 key 數與名稱斷言：缺／多 key＝零寫入＋非零退出＋指名（絕不落到 generate 造亂數路徑）
#   P4.1／P5.7 逐檔 printf '%s' 寫入（無尾端換行）；P4.7 檔 644
#   P4.5 現值 ≠ 解密值 → 另存 <name>.txt.new＋警示、不覆寫；現值＝解密值 → 照寫（冪等）
#   FR-021／SC-005 明文暫存落點：$XDG_CACHE_HOME（回退 $HOME/.cache）之 0700 暫存目錄、
#     非 repo 內 tmp/（/mnt/d＝9p、chmod no-op＝實效 777）；落點性質不符即 fail-loud
#   單次 sops -d 收全 YAML 再本地拆 key——B′ 下每次容器呼叫都要 1 次 passphrase，
#   絕不逐 key --extract 重呼容器

set -euo pipefail

# ---- P4.2 tty 守衛 ----
if [ ! -t 0 ]; then
    echo "FAIL：decrypt-secrets.sh 需要互動終端（B′ passphrase 解密提示需 tty）。" >&2
    echo "      命令替換／管線／CI 等非互動情境不支援；請在真實終端執行。" >&2
    exit 1
fi

# ---- 必須自 repo 根執行（wrapper P1.5 同前提）----
if [ ! -f .sops.yaml ] || [ ! -f deploy/secrets.dev.enc.yaml ]; then
    echo "FAIL：請自 repo 根執行（當前目錄找不到 .sops.yaml 或 deploy/secrets.dev.enc.yaml）。" >&2
    exit 1
fi

# ---- 落點解析（019 P5.2 五支賦值型消費者之一；generate／preflight／setup-reaper-role
#      ／tools/secret-value-guard.py 同口徑，消費者聯集七處＝契約 P5.1）：環境變數優先
#      （與 compose 口徑一致）→ repo 根 .env 只嚴格解析 SECRETS_DIR 一行（★不整檔 source
#      ——compose 的 .env 允許不加引號的含空白值、井號語意亦與 shell 不同，含錢字號小括號
#      ／反引號之值 source 時會被執行）→ 皆缺回退 deploy/secrets ----
# ★偵測寬、取值窄（019 U4 quality 修；五處解析器同刀齊改）：compose 的 .env 解析器接受
#   UTF-8 BOM／行首空白／export 前綴／等號兩側空白／CRLF 行尾，而行首錨定 `SECRETS_DIR=`
#   的窄樣式對這五形一律漏認並**靜默回退**舊落點——實測 compose v5.3.1 五形全部解析為新
#   落點，即契約 P5.1 違反後果欄的「compose 讀新落點、腳本查舊落點」（decrypt 更會據此把
#   8 支明文寫回 repo 內 /mnt/d 舊落點＝違反 FR-021／SC-005）。故偵測改用寬樣式撈出
#   compose 會讀到的那一行（同 tail -n 1 後者勝口徑），再對其值套下方嚴格白名單：寬進窄出，
#   四形一律「正確採用」或「吵鬧失敗」，永不落入靜默回退。
# ★空字串邊界（019 U4 quality 修；五支賦值型解析器同刀齊改）：「已匯出但為空」≠「未設」——
#   shell 環境已勝出 .env，compose 的 ${SECRETS_DIR:-./deploy/secrets} 對空字串直接吃預設值、
#   回退 repo 內舊落點且**不讀 .env 該鍵**；而 [ -z ] 把空字串當未設、續往 .env 取新落點＝
#   本腳本把 8 支明文寫進 .env 新落點、compose 卻掛 repo 內舊落點，即 P5.1 違反後果欄那條路
#   的另一入口，且破在靜默方向。空字串無合法用途（要走回退請 unset），故吵鬧失敗指名真因。
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
# ★相對值錨定基準＝repo 根（019 U4 quality 修；五支同刀齊改、契約 P5.1）：本腳本 :31 已斷言
# CWD＝repo 根，故相對值本就等價；此處**顯式錨定**是為與 generate／preflight 同形——依賴
# 「CWD 恰為 repo 根」屬隱性保證，斷言若日後被放寬即靜默改變落點。
case "$SECRETS_DIR" in /*) ;; *) SECRETS_DIR="$PWD/$SECRETS_DIR" ;; esac

# ---- P4.4／P4.6 自建 0700 子目錄＋權限自證 ----
umask 077
mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR"
DIR_MODE="$(stat -c '%a' "$SECRETS_DIR")"
if [ "$DIR_MODE" != "700" ]; then
    FS_TYPE="$(stat -f -c '%T' "$SECRETS_DIR")"
    if [ "$FS_TYPE" = "v9fs" ]; then
        # drvfs（/mnt/*）：chmod 結構性 no-op、權限恆 777——現行落點已知限制（US3 遷移消滅）
        echo "WARN：$SECRETS_DIR 權限=$DIR_MODE（fs=$FS_TYPE、chmod 為 no-op；US3 遷移後消失）" >&2
    else
        echo "FAIL：$SECRETS_DIR chmod 700 未生效（實際 $DIR_MODE、fs=$FS_TYPE）。" >&2
        exit 1
    fi
fi

# ---- 8 key 名單（＝deploy/secrets.dev.enc.yaml 全集；7 leaf＋alert_webhook_url；
#      composite 三支由 generate-secrets.sh 自 leaf 重生、不進加密檔）----
EXPECTED_KEYS=(postgres_password redis_password jwt_secret refresh_token_secret
               captcha_secret reaper_password grafana_admin_password alert_webhook_url)

# ---- 單次 sops -d 收全 YAML 至暫存（明文中間產物；落點必須離開 /mnt/d）----
# ★不得落 repo 內 tmp/：/mnt/d＝9p（v9fs），umask／chmod 皆結構性 no-op（同上方 SECRETS_DIR
#   權限自證分支所承認的性質）——暫存檔會以實效 777、Windows 側可見的形式承載 8 支完整明文，
#   正是 FR-021／SC-005「/mnt/d 全樹零明文機密檔」要消滅的暴露面，且不隨 US3 落點遷移而消失。
# ★本檔由 host shell 重導向產生、不進容器（wrapper 只掛載 $PWD 供 sops 讀 enc 檔），故不受
#   contracts §P4「合併衝突」列之「暫存明文必須落 repo 內」限制——該限只適用於要餵回 sops
#   加密的檔（wrapper 只掛載 $PWD、repo 外的檔容器讀不到）。
TMP_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$TMP_ROOT"
TMP_DIR="$(mktemp -d "$TMP_ROOT/rev4-decrypt.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT
TMP_FS="$(stat -f -c '%T' "$TMP_DIR")"
TMP_MODE="$(stat -c '%a' "$TMP_DIR")"
if [ "$TMP_FS" = "v9fs" ] || [ "$TMP_MODE" != "700" ]; then
    echo "FAIL：暫存明文落點 $TMP_DIR 不安全（fs=$TMP_FS、mode=$TMP_MODE；需非 v9fs 且 700）。" >&2
    echo "      成因＝\$HOME（或 \$XDG_CACHE_HOME）落在 /mnt/* 之 9p 上、chmod 為 no-op。" >&2
    echo "      處置＝將 XDG_CACHE_HOME 指到 ext4 路徑（如 /home/\$USER/.cache）後重跑。" >&2
    exit 1
fi
RAW="$TMP_DIR/raw.out"

# 暫存流雜訊＝passphrase 提示行＋ANSI 清行序列＋容器 pty 的 CRLF（wrapper P1.2 註／L-168）：
#   ①CR 一律轉行界 ②剝 ANSI CSI 序列（失敗診斷與拆 key 兩路共用此正規化）
ESC=$'\x1b'
normalize_raw() {
    tr '\r' '\n' < "$RAW" | sed -E "s/${ESC}\[[0-9;]*[A-Za-z]//g"
}

echo "即將解密：sops 會要求輸入 identity passphrase（提示可能不顯示於畫面）——請直接輸入後按 Enter。"
SOPS_RC=0
./deploy/sops.sh -d deploy/secrets.dev.enc.yaml > "$RAW" || SOPS_RC=$?
if [ "$SOPS_RC" -ne 0 ]; then
    echo "FAIL：sops 解密失敗（rc=$SOPS_RC）——sops 輸出如下（資料行已濾除）：" >&2
    # ★RAW 同時承載容器 stdout 與 stderr（wrapper -t＝單一 pty 流、L-168），故「解密失敗
    #   就不含明文」只是 sops 正常錯誤路徑（MAC 檢查早於 Emit）的性質、不是本腳本的保證：
    #   已 Emit 才異常結束者（stdout 寫入失敗、passphrase 過關後收 SIGINT）RAW 即含明文。
    #   註解斷言防不了洩漏——倒出前先濾掉 key 行（含已知 key 名任意位置）及其縮排續行
    #   （＝解密 YAML 的全部承載面，涵蓋引號形與區塊純量形），只留診斷訊息。
    KEY_RE="($(IFS='|'; echo "${EXPECTED_KEYS[*]}")):|^[a-z_]+:"
    normalize_raw | awk -v keyre="$KEY_RE" '
        $0 ~ keyre         { skip = 1; redacted++; next }
        /^[ \t]*$/         { next }               # CRLF 轉行界留下的空殘行（不計數、不解除 skip）
        skip && /^[ \t]/   { redacted++; next }   # 區塊純量的縮排續行＝仍是資料
                           { skip = 0; print }
        END { if (redacted) printf "      （另有 %d 行疑似機密資料已濾除、不顯示）\n", redacted }
    ' >&2 || true
    exit "$SOPS_RC"
fi

# ---- 本地拆 key（不重呼容器）----
# 正規化後只認「key: value」行、值只切第一個「冒號空白」
CLEAN="$TMP_DIR/clean.yaml"
normalize_raw > "$CLEAN"

declare -A VALS
while IFS= read -r line; do
    case "$line" in
        [a-z_]*": "*)
            VALS["${line%%: *}"]="${line#*: }"
            ;;
    esac
done < "$CLEAN"

# ---- P4.3 key 數與名稱斷言（不符＝零寫入＋非零退出＋指名）----
MISSING=()
for k in "${EXPECTED_KEYS[@]}"; do
    if [ -z "${VALS[$k]+x}" ] || [ -z "${VALS[$k]}" ]; then
        MISSING+=("$k")
    fi
done
EXTRA=()
for k in "${!VALS[@]}"; do
    case " ${EXPECTED_KEYS[*]} " in
        *" $k "*) ;;
        *) EXTRA+=("$k") ;;
    esac
done
# 非裸量純量斷言（P4.3 同族：靜默壞值一律翻成吵鬧失敗）
#   sops（go-yaml v3）只在值能當裸量純量時吐裸量；否則吐雙引號／單引號／區塊純量形，
#   而本腳本逐行拆 key 拿到的是「含引號字元的原樣 token」、無法還原原值——逐字寫入即壞值。
#   ★空值案更會架空上面的「值為空」判定：吐出的是 2 字元的 ""、非空。
#   2026-07-29 sops v3.13.3-alpine 實測形制（隔離沙箱、暫代金鑰、假值探針）：
#     空字串→ ""｜含「冒號空白」→ 'a: b'｜含「井號」→ 'v #f'｜前後帶空白→ 'trail '｜
#     含換行→ |- 加縮排續行｜以 " ' | > 以外字元開頭（含 - : ~ =）→ 裸量、逐行拆解正確。
#   故判準＝值首字元落 " ' | > 四者即 FAIL 指名（零新依賴、不誤傷任何裸量值）。
NONPLAIN=()
for k in "${EXPECTED_KEYS[@]}"; do
    [ -z "${VALS[$k]+x}" ] && continue
    case "${VALS[$k]}" in
        '"'*|"'"*|'|'*|'>'*) NONPLAIN+=("$k") ;;
    esac
done
if [ "${#MISSING[@]}" -ne 0 ] || [ "${#EXTRA[@]}" -ne 0 ] || [ "${#NONPLAIN[@]}" -ne 0 ]; then
    [ "${#MISSING[@]}" -ne 0 ] && echo "FAIL：解密結果缺 key（或值為空）：${MISSING[*]}" >&2
    [ "${#EXTRA[@]}" -ne 0 ] && echo "FAIL：解密結果含非預期 key：${EXTRA[*]}" >&2
    if [ "${#NONPLAIN[@]}" -ne 0 ]; then
        echo "FAIL：下列 key 的值不是 YAML 裸量純量（引號形或區塊純量形），本腳本無法還原原值：${NONPLAIN[*]}" >&2
        echo "      成因＝該值為空、含「冒號空白」或「井號」、前後帶空白、或含換行。" >&2
        echo "      處置＝./deploy/sops.sh edit deploy/secrets.dev.enc.yaml 改成不需引號的單行值後重跑。" >&2
    fi
    echo "FAIL：key 斷言不符＝零寫入退出。修復加密檔後重跑；絕不落到 generate 造亂數路徑。" >&2
    exit 1
fi

# ---- 既有 .txt.new 偵測（019 U3 遺留 advisory 三）：值重新一致後，先前 DIFF 產下的舊 .new
#      不會再被觸碰＝長存落點；此處只提醒、★不自動刪（避免吃掉人工待決資料）----
STALE_NEW=()
for f in "$SECRETS_DIR"/*.txt.new; do
    [ -e "$f" ] && STALE_NEW+=("$(basename "$f")")
done
if [ "${#STALE_NEW[@]}" -ne 0 ]; then
    echo "WARN：落點已有先前遺留的待決 .txt.new：${STALE_NEW[*]}——請人工比對處置（本腳本不自動刪）。" >&2
fi

# ---- 寫入（斷言全過後才進入；P4.1／P4.5／P4.7）----
NEW_SAVED=()
for k in "${EXPECTED_KEYS[@]}"; do
    dst="$SECRETS_DIR/$k.txt"
    v="${VALS[$k]}"
    if [ -f "$dst" ] && ! printf '%s' "$v" | cmp -s - "$dst"; then
        # 現值 ≠ 解密值：另存 .new、不覆寫（decrypt 不得成為靜默覆寫路徑）
        # ★.new 亦為 644（不是 600）：WARN 指示的補救＝`mv .new` 蓋回，mv 於同 fs＝rename、
        #   mode 原樣保留——.new 若為 600，蓋回後落點檔終值即 600、違反 P4.7／FR-022，
        #   且只在開 obs／metrics 軌時才炸（grafana 472／postgres-exporter 65534／
        #   redis-exporter 59000 全部 Permission denied）。目錄本身 700，644 不擴大暴露面。
        printf '%s' "$v" > "$dst.new"
        chmod 644 "$dst.new"
        NEW_SAVED+=("$k")
        echo "  ${k}.txt DIFF→已另存 ${k}.txt.new（原檔不動、請人工比對取捨）"
    else
        # 缺檔＝新寫；現值＝解密值＝冪等照寫
        printf '%s' "$v" > "$dst"
        chmod 644 "$dst"
        echo "  ${k}.txt WRITTEN"
    fi
done

echo ""
if [ "${#NEW_SAVED[@]}" -ne 0 ]; then
    echo "WARN：下列機密現值與加密檔不一致、已另存 .txt.new（原檔未覆寫）：${NEW_SAVED[*]}" >&2
    echo "      人工比對後：採加密檔值＝mv .new 蓋回；保留現值＝刪 .new 並依 RUNBOOK 輪替程序回寫加密檔。" >&2
fi
echo "完成：$SECRETS_DIR 之 8 支 key 檔已就緒（composite 另跑 ./deploy/generate-secrets.sh 重組）。"
