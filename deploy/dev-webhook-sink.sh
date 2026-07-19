#!/bin/sh
# 016-observability T013：dev webhook 收器（★dev 驗收專用、不入 compose 正式段）。
# 一次性輕量收器容器：reuse 本機既有 node:26.4.0-alpine 映像（dev override base-web 同映像、
# 零新拉映像）、掛 rev4-admin_rev4_net、收 POST 落證於容器內 /tmp/webhook-evidence.jsonl
# （host 側以 docker exec cat 取證或 docker logs 看流水）。
# 用法：
#   sh deploy/dev-webhook-sink.sh start   # 起收器（冪等：既存先撤再起）
#   sh deploy/dev-webhook-sink.sh stop    # 撤收器（S4 驗畢即撤、硬性還原項）
#   sh deploy/dev-webhook-sink.sh cat     # 印出證檔（每 POST 一行 JSON：時戳＋body）
# 搭配：deploy/secrets/alert_webhook_url.txt 填 http://rev4-dev-webhook-sink:8080/alert
# （gitignored 真值；grafana restart 後 provisioning $__file 讀入）。
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
