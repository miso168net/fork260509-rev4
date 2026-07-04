# Quickstart: 003-wire-foundation 驗證指南

命令級驗證（spec 三 story＋SC 的可執行化）。比對規則見
[contracts/envelope-contract.md](contracts/envelope-contract.md) 與
[contracts/contract-machinery.md](contracts/contract-machinery.md)、機器基準見
[data-model.md](data-model.md)；本檔不含實作碼。約定 `CF="docker compose -f
docker-compose.yml -f docker-compose.dev.yml"`（repo 根執行）。

## 前置

- 001 dev stack 可用且在跑（五常駐 healthy）；002 基線就位（本刀不依賴 DB 內容、
  但整波驗收共用同一 stack）。
- 路徑口徑（001 路由契約）：front-nginx `location /api/` **strip 前綴**轉發——對外形
  `/api/demo-wire`（port 42080 HTTP／42443 HTTPS）＝後端形 `/demo-wire`（rust-api
  直連 port 42079）。驗收以對外形為主（user 面真相）、直連形抽驗一次等價。

## A. 信封實形（US1／SC-001）

```bash
curl -s http://127.0.0.1:42080/api/demo-wire | python3 -m json.tool
#   期望：{"data": {...}, "code": "0000", "msg": "common.success"}——欄序 data→code→msg；
#   data 內 createdAt 帶時區偏移（RFC3339）、id 為 JSON string
curl -s http://127.0.0.1:42079/demo-wire | python3 -m json.tool   # 直連等價抽驗（同 body）
curl -s http://127.0.0.1:42079/health
#   期望：plain text ok（不套信封）
```

## B. 錯誤形與 HTTP 例外（US1／SC-002 部分）

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:42080/api/no-such-route
#   期望：404
curl -s http://127.0.0.1:42080/api/no-such-route | python3 -m json.tool
#   期望：{"data": null, "code": "4040", "msg": "system.notFound"}——data 為 null 且不省略
```

## C. 三類守門＋覆蓋閘（US2／SC-002/SC-003/SC-005）

```bash
$CF exec -T rust-api cargo test --workspace     # 全綠（serial；含：
#   13 碼 table-driven（13/13）＋保留碼列舉完整性（可發碼恰 9）＋
#   時間欄 offset 斷言＋覆蓋閘（註冊表↔case registry 雙向）＋契約裁判通用形）
```

## D. 契約管線（US3／SC-004）

```bash
python3 tools/wire-schema extract               # 需 stack；寫 server/tests/fixtures/wire-schema.json
git -C rust-api diff --stat server/tests/fixtures/wire-schema.json   # 首抽後再抽應零 diff
git -C base-web status --porcelain              # 空（唯讀抽取、零 fork 改動）
# 覆蓋閘負面（驗畢還原）：暫時註解掉 demo 路由的 contract case →
$CF exec -T rust-api cargo test --workspace     # 紅、指名該路由缺 case
# 還原 → 重跑全綠
```

## E. 波 0 不變式（SC-006）

```bash
git -C base-web status --porcelain              # 空
git submodule status | grep base-web           # pin 停 9c6f223
docker ps --format '{{.Names}} {{.Status}}' | grep '^rev3-admin'   # 前後對照無異狀
```

## F. 波 0 出口整波重跑（SC-007；收刀時執行）

收 003 時六組檢查表全綠才宣告波 0 收口（清單＝wave-0-plan §3）：第 1 組一鍵環境
（down -v 歸零重來）→ 第 2 組基線資料（\dt＋seed 抽查＋gate1/gate2 綠）→ 第 3 組
wire 地基（本檔 A~D）→ 第 4 組文件面 → 第 5 組紀律面 → 第 6 組波 1 就緒判定。
