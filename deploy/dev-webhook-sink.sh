#!/bin/sh
# 016-observability T013：dev webhook 收器（★dev 驗收專用、不入 compose 正式段）。
# 一次性輕量收器容器：reuse 本機既有 node:26.4.0-alpine 映像（dev override base-web 同映像、
# 零新拉映像）、掛 rev4-admin_rev4_net、收 POST 落證於容器內 /tmp/webhook-evidence.jsonl
# （host 側以 docker exec cat 取證或 docker logs 看流水）。
# 用法：
#   sh deploy/dev-webhook-sink.sh start   # 起收器（冪等：既存先撤再起）
#   sh deploy/dev-webhook-sink.sh stop    # 撤收器（S4 驗畢即撤、硬性還原項）
#   sh deploy/dev-webhook-sink.sh cat     # 印出證檔（每 POST 一行 JSON：時戳＋body）
# 搭配：$SECRETS_DIR/alert_webhook_url.txt 填本收器位址（形如 http://<下方 NAME 變數值>:8080/alert
#   ——★019 起不在文件寫出完整字面：該欄位是機密欄位，dev 佔位值一旦與文件示例逐字相同，
#   值比對層就會在下次有人動到本行時擋下 commit〔而人只會學會 --no-verify〕；L-190）
# ★誠實登記（019 U6）：上述「不完整形」只消除**逐字共用**、**不消除可推導性**——本欄現值仍可由
#   本檔下方 NAME 常數＋埠 8080＋路徑 /alert 逐 byte 重建（機判：重建值與落點現值 sha256 相符、
#   39 bytes；不印值）。判定＝**dev-only 已接受殘餘**（值是收器的容器內部位址、僅 docker 網段
#   可解析、無憑證材料、收器已撤）；換成正式接收端 URL 後即不可由 tracked 檔推導。★真機密不可
#   套用本形——真值的示例必須「完全不敘述其構成」才成立（L-190 防法①）。
# （★019 US3 起落點由 repo 根 .env 的 SECRETS_DIR 決定、未設才回退 repo 內 deploy/secrets；
#   真值不入版控，權威來源＝deploy/secrets.dev.enc.yaml 之 alert_webhook_url key。
#   ★改該檔後必依 RUNBOOK §15.4 re-encrypt 回加密檔，否則下次 decrypt 觸發 .txt.new 守衛；
#   grafana restart 後 provisioning $__file 讀入）。
set -eu

NAME=rev4-dev-webhook-sink
NET=rev4-admin_rev4_net
IMG=node:26.4.0-alpine

case "${1:-}" in
  start)
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    docker run -d --name "$NAME" --network "$NET" --memory 64m --restart no \
      "$IMG" node -e '
const http = require("http");
const fs = require("fs");
http.createServer((req, res) => {
  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    const line = JSON.stringify({ ts: new Date().toISOString(), method: req.method, url: req.url, body });
    fs.appendFileSync("/tmp/webhook-evidence.jsonl", line + "\n");
    console.log(line);
    res.writeHead(200); res.end("ok");
  });
}).listen(8080, "0.0.0.0", () => console.log("sink listening :8080"));
'
    echo "started: $NAME on $NET (evidence: /tmp/webhook-evidence.jsonl in container)"
    ;;
  stop)
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    echo "stopped: $NAME"
    ;;
  cat)
    docker exec "$NAME" cat /tmp/webhook-evidence.jsonl
    ;;
  *)
    echo "usage: $0 start|stop|cat" >&2
    exit 1
    ;;
esac
