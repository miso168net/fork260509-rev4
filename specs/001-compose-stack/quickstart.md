# Quickstart: 001-compose-stack 驗證指南

命令級驗證（spec 驗收八組的可執行化）。契約細節見
[contracts/http-surface.md](contracts/http-surface.md) 與
[contracts/env-secrets.md](contracts/env-secrets.md)、結構見 [data-model.md](data-model.md)；
本檔不含實作碼。

## 前置

- WSL2＋Docker Engine＋Compose v2 可用（`docker compose version`）。
- repo 根執行；rust-api worktree 已接妥。
- host 不需要 rust／node／psql／redis-cli——DB 與快取的驗證可改用容器內 client（下方已給
  兩種形）。

## A. 從零一鍵起（驗收 1）

```bash
./deploy/generate-secrets.sh          # 六機密；重跑應全 SKIPPED（冪等）
./deploy/generate-dev-cert.sh         # 自簽 TLS
./deploy/preflight-secrets.sh         # 應綠；刪任一 .txt 重跑應指名缺檔
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait
echo $?                                # 0
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps -a
# 期望：front-nginx／base-web／rust-api／postgres／redis 五者 healthy；migrate Exited (0)
```

## B. 七連通點＋負面驗證（驗收 2）

```bash
curl -s  http://127.0.0.1:42080/health          # ok（nginx 自答）
curl -sk https://127.0.0.1:42443/health         # ok（TLS）
curl -s  http://127.0.0.1:42080/api/health      # ok（strip /api → rust-api:8080 全鏈）
curl -s  http://127.0.0.1:42079/health          # ok（axum 直連）
curl -s  http://127.0.0.1:42081 | head -1       # <!DOCTYPE html>…
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres \
  psql -U soybean -d soybean_admin_rust -c 'SELECT 1'   # 1 row
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec redis \
  sh -c 'redis-cli -a "$(cat /run/secrets/redis_password)" --no-auth-warning ping'  # PONG
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:42080/api/metrics  # 404（擋門）
```

（host 有 psql／redis-cli 時亦可直連 45432／46379，密碼取 `deploy/secrets/*.txt`。）

## C. migrate gate 時序（驗收 3）

```bash
docker inspect --format '{{.Name}} {{.State.StartedAt}}' \
  $(docker compose -f docker-compose.yml -f docker-compose.dev.yml ps -aq) | sort -k2
# 期望順序：postgres → migrate → rust-api（migrate Exited(0) 先於 rust-api 起）
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres \
  psql -U soybean -d soybean_admin_rust -c '\dt'   # 見 seaql_migrations
```

負面（story 2 scenario 2）：暫時把 migrate 的 command 改為必敗（如 `["not-a-cmd"]`）→
`up -d --wait` 非零退出且 rust-api 不啟動；驗畢改回。

## D. 冪等（驗收 4）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait   # 更快、全綠
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v        # 歸零（含卷）
# 重跑 A 全段仍綠
```

## E. 熱重載（驗收 5）

```bash
# 暫改 rust-api/server/src/main.rs 的 /health 回應字串（如 "ok-hot"）
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f rust-api &
# 期望：watchexec 偵測（--poll 1s）→ 重編 → 重啟；≤60s 內：
curl -s http://127.0.0.1:42079/health   # ok-hot
# 改回、確認恢復 ok
```

前端：改 base-web 原始碼由 vite 熱更新即時反映（**驗畢必須還原——base-web 零改動不變式**，
`git -C base-web status --porcelain` 應為空）。

## F. 容器內測試（驗收 6）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api \
  cargo test --workspace          # 全綠；serial（勿並行第二個 cargo）
```

## G. 文件面＋不變式（驗收 7、8）

```bash
tools/docs-sync generate && tools/docs-sync check   # 綠；reference/ports 與 compose 一致
git -C base-web status --porcelain                  # 空
git submodule status | grep base-web                # pin 停在 9c6f223
```
