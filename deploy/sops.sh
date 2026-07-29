#!/usr/bin/env bash
# deploy/sops.sh — sops 官方容器 wrapper（019-secrets-sops；契約＝contracts/secret-pipeline.md §P1）
#
# 用法：自 repo 根執行 ./deploy/sops.sh <sops 參數...>
#   例：./deploy/sops.sh -e --filename-override deploy/secrets.dev.enc.yaml tmp/plain.yaml
#       ./deploy/sops.sh -d deploy/secrets.dev.enc.yaml
#
# 契約要點（P1.1~P1.7）：
#   P1.1 映像 digest 釘版（registry 與 digest 成對；tag 可被重推、digest 不可變）
#   P1.2 互動旗標條件化：stdin 是 tty 才配 -i -t；非互動時 sops 需要互動會自己吵鬧失敗、不 hang
#        （★stdout 重導向＋-t 並存時，容器 pty 會把輸出換行改 CRLF、且 passphrase 提示行與
#          stdout 同流——呼叫端須自行剝 CR 並濾掉非資料行，deploy/decrypt-secrets.sh 的
#          key 行 parser 即此設計；人工呼叫端同受此限＝RUNBOOK §15.7 步驟 1 之正規化片段。
#          ★不需 passphrase 的子命令（-e 等）呼叫端補 `< /dev/null` 即讓本分支不成立、
#          從根上不生 CRLF 與併流——RUNBOOK §15.7 步驟 3 用的就是這一招）
#   P1.3 不轉發 host EDITOR（映像已內建 EDITOR=vim；host 值多指向容器內不存在的程式）
#   P1.4 顯式 -e 三變數（docker 未以 -e 列出的環境變數一律被靜默丟棄）
#   P1.5 必須自 repo 根執行——否則容器內 /work 無 .sops.yaml、sops 自己吵鬧失敗
#        （config file not found＝可接受的失敗訊息、即指引）
#   P1.6 明文產物一律 host shell 收 stdout＋umask 077；不用 sops 的 --output／-i（in-place）
#        產明文（映像以 root 執行、容器直寫產物＝root:root）——此為呼叫端紀律、wrapper 不產檔
#   P1.7 exec bit 以 git update-index --chmod=+x 落 index（drvfs 上 chmod 不落 index）

set -euo pipefail

# P1.1 digest 釘版常數（T002 拍板：ghcr.io v3.13.3-alpine 之 multi-arch index digest）
SOPS_IMAGE="ghcr.io/getsops/sops@sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea"

# P1.2 互動旗標條件化（stdin 有 tty 才配；B′ passphrase 提示需要容器內 tty）
TTY_FLAGS=()
if [ -t 0 ]; then
    TTY_FLAGS=(-i -t)
fi

# 私鑰目錄唯讀掛載（存在才掛；容器內 HOME=/root → 對位 sops 預設尋鑰路徑
# /root/.config/sops/age/keys.txt）
AGE_KEY_DIR="${HOME}/.config/sops/age"
KEY_MOUNT=()
if [ -d "$AGE_KEY_DIR" ]; then
    KEY_MOUNT=(-v "${AGE_KEY_DIR}:/root/.config/sops/age:ro")
fi

# P1.3／P1.4：只顯式轉發 SOPS_AGE_* 三變數；EDITOR 一律不轉發
exec docker run --rm \
    "${TTY_FLAGS[@]}" \
    "${KEY_MOUNT[@]}" \
    -e SOPS_AGE_KEY -e SOPS_AGE_KEY_FILE -e SOPS_AGE_KEY_CMD \
    -v "${PWD}:/work" -w /work \
    "$SOPS_IMAGE" "$@"
