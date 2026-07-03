# Contract: HTTP Surface（001-compose-stack）

本刀對外的全部 HTTP 介面。信封與 13 碼不在本刀（隨 003 wire 刀）；本刀端點皆屬憲法 §I.3
信封例外或代理層自答。

## 1. rust-api 直連（127.0.0.1:42079）

| Method | Path | Response | 說明 |
|---|---|---|---|
| GET | /health | `200 OK`、`text/plain`、body 恰為 `ok` | 憲法信封例外；探針與驗收共用 |

其餘路徑：axum 預設 404（本刀不定義任何其他 route）。

## 2. front-nginx 代理（127.0.0.1:42080 HTTP／42443 HTTPS）

| Path | 行為 | 契約要點 |
|---|---|---|
| `= /health` | nginx 自答 `200`、body `ok` | 不轉發；探針、驗收用 |
| `= /api/metrics` | `404` | **擋門**：metrics 永不對外（憲法 §II #3）；先於觀測刀存在 |
| `/api/` | 轉 `rust-api:8080/`（**strip `/api` 前綴**） | proxy_pass 末尾斜線＝路由契約：後端 route 不帶 /api 前綴（003 刀依此設計）；`/api/health` → 後端 `/health` 回 `ok`（驗收連通點） |
| `/` | 轉 `base-web:80` | SPA／vite dev server |

- 42443＝TLS 終端：自簽憑證（`deploy/dev-certs/fullchain.pem`＋`privkey.pem`、SAN
  localhost＋127.0.0.1）；路由行為與 42080 完全一致（同 include `_locations.inc`）。
- 附加 header：`X-Request-Id` 注入（json access log 關聯欄）。
- 裁剪聲明：rev3 的 CF-Connecting-IP 覆寫與 limit_req 不在本刀（歸 ip-gate／auth 功能刀）。

## 3. base-web 直連（127.0.0.1:42081）

vite dev server 原生行為：`GET /` 回 HTML（含 doctype）。本刀不約束其內容，僅驗連通。

## 4. 探針矩陣（compose healthcheck 用）

| 目標 | 探針 | 成功判準 |
|---|---|---|
| front-nginx | `wget -qO- http://127.0.0.1/health` | 輸出含 `ok` |
| base-web | `wget -qO- http://127.0.0.1:80/` | 輸出含 doctype／html |
| rust-api | `bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080'` | TCP 可連（dev 映像無 curl／wget） |

探針一律打 127.0.0.1 非 localhost（alpine 將 localhost 先解 ::1、nginx 只綁 IPv4——rev3 坑）。
