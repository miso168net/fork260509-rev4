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

# ---- 落點解析：source .env（存在時）→ 未設回退 deploy/secrets（與 tools/secret-value-guard.py 同口徑）----
if [ -f .env ]; then
    # shellcheck disable=SC1091
    . ./.env
fi
SECRETS_DIR="${SECRETS_DIR:-deploy/secrets}"

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

# ---- 單次 sops -d 收全 YAML 至 repo 內 gitignored 暫存（umask 077 已生效）----
mkdir -p tmp
TMP_DIR="$(mktemp -d tmp/decrypt-secrets.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT
RAW="$TMP_DIR/raw.out"

echo "即將解密：sops 會要求輸入 identity passphrase（提示可能不顯示於畫面）——請直接輸入後按 Enter。"
SOPS_RC=0
./deploy/sops.sh -d deploy/secrets.dev.enc.yaml > "$RAW" || SOPS_RC=$?
if [ "$SOPS_RC" -ne 0 ]; then
    echo "FAIL：sops 解密失敗（rc=$SOPS_RC）——sops 輸出如下（解密失敗、不含明文）：" >&2
    tr -d '\r' < "$RAW" >&2 || true
    exit "$SOPS_RC"
fi

# ---- 本地拆 key（不重呼容器）----
# 暫存流雜訊＝passphrase 提示行＋ANSI 清行序列＋容器 pty 的 CRLF（wrapper P1.2 註）：
#   ①CR 一律轉行界 ②剝 ANSI CSI 序列 ③只認「key: value」行、值只切第一個「冒號空白」
ESC=$'\x1b'
CLEAN="$TMP_DIR/clean.yaml"
tr '\r' '\n' < "$RAW" | sed -E "s/${ESC}\[[0-9;]*[A-Za-z]//g" > "$CLEAN"

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
if [ "${#MISSING[@]}" -ne 0 ] || [ "${#EXTRA[@]}" -ne 0 ]; then
    [ "${#MISSING[@]}" -ne 0 ] && echo "FAIL：解密結果缺 key（或值為空）：${MISSING[*]}" >&2
    [ "${#EXTRA[@]}" -ne 0 ] && echo "FAIL：解密結果含非預期 key：${EXTRA[*]}" >&2
    echo "FAIL：key 斷言不符＝零寫入退出。修復加密檔後重跑；絕不落到 generate 造亂數路徑。" >&2
    exit 1
fi

# ---- 寫入（斷言全過後才進入；P4.1／P4.5／P4.7）----
NEW_SAVED=()
for k in "${EXPECTED_KEYS[@]}"; do
    dst="$SECRETS_DIR/$k.txt"
    v="${VALS[$k]}"
    if [ -f "$dst" ] && ! printf '%s' "$v" | cmp -s - "$dst"; then
        # 現值 ≠ 解密值：另存 .new、不覆寫（decrypt 不得成為靜默覆寫路徑）
        printf '%s' "$v" > "$dst.new"
        chmod 600 "$dst.new"
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
