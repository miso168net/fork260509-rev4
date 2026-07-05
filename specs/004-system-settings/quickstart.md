# Quickstart: 004-system-settings 驗證指南

命令級驗證（spec 三 story＋SC 可執行化）。比對規則見 contracts/settings-api.md 與
contracts/frontend-track.md、機器基準見 data-model.md。約定 `CF="docker compose -f
docker-compose.yml -f docker-compose.dev.yml"`（repo 根執行）。

## 前置

- 001 dev stack 在跑（五常駐 healthy）；002 baseline（system_settings 8 seed＋casbin R_SUPER
  policy＋R_SUPER user-role seed）就位。本刀零 migration。
- 授權測試身分：以同 JWT secret 手工 sign 一個 super Claims 的 test token（uid＝seed 的 super
  user、無需登入端點）；一個非-super token 供負面。

## A. 設定列表（US1／SC-001）

```bash
# super token → 全 8 設定信封陣列（不分頁、camelCase settingType）
curl -s -H "Authorization: Bearer $SUPER_TOKEN" http://127.0.0.1:42079/systemManage/getSystemSettings | python3 -m json.tool
#   期望：{"data":[{"settingKey":"...","settingValue":"...","settingType":"...","description":...}, ...8項], "code":"0000","msg":"common.success"}
#   無審計欄；欄序 data→code→msg
```

## B. 設定更新＋型驗（US1／US2／SC-001/SC-002）

```bash
# 有效更新（number 界內）→ 持久化＋op-log
curl -s -H "Authorization: Bearer $SUPER_TOKEN" -H 'Content-Type: application/json' \
  -d '{"settingKey":"password_min_length","settingValue":"10"}' \
  http://127.0.0.1:42079/systemManage/updateSystemSetting
#   期望：{"data":null,"code":"0000","msg":"common.success"}；再 GET 得 10
# 無效值（number 界外）→ 2222 invalidValue、不寫入
curl -s -H "Authorization: Bearer $SUPER_TOKEN" -H 'Content-Type: application/json' \
  -d '{"settingKey":"password_min_length","settingValue":"9999"}' \
  http://127.0.0.1:42079/systemManage/updateSystemSetting
#   期望：{"data":null,"code":"2222","msg":"biz.systemSettings.invalidValue"}；GET 值不變
# 不存在 key → 2222 notFound、不新增
curl -s ... -d '{"settingKey":"no_such_key","settingValue":"x"}' .../updateSystemSetting
#   期望：code "2222" msg "biz.systemSettings.notFound"
```

## C. 授權（US3／SC-003）

```bash
# 非-super token → 5003
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $NONSUPER_TOKEN" \
  http://127.0.0.1:42079/systemManage/getSystemSettings   # 期望 403
curl -s -H "Authorization: Bearer $NONSUPER_TOKEN" http://127.0.0.1:42079/systemManage/getSystemSettings
#   期望：{"data":null,"code":"5003","msg":"system.forbidden"}
# 無 token → 擋下（3333/401 區）
```

## D. 後端守門（US2/US3／SC-004）

```bash
$CF exec -T rust-api cargo test --workspace   # 全綠（serial；含：
#   型別 registry 單元（number 正規化/範圍、enum、未知型拒、notFound）＋facade op-log 同 txn＋
#   authz（super/非-super 注入身分）＋contract case＋覆蓋閘（雙向、demo 移除後對齊）＋entity_access_lint）
```

## E. audit op-log 落庫（SC-001 佐證）

```bash
DBURL=$(cat deploy/secrets/database_url.txt)
$CF exec -T postgres psql "$DBURL" -tAc \
  "SELECT operation,entity_table,entity_id,payload_after->>'setting_key' FROM sys_operation_log WHERE entity_table='system_settings' ORDER BY id DESC LIMIT 1;"
#   期望：UPDATE | system_settings | (null) | password_min_length（KV String-PK：entity_id null、key 在 payload）
```

## F. 前端守門（SC-005；typecheck+lint、無 runtime 測試）

```bash
$CF exec -T base-web sh -c 'pnpm gen-route && pnpm typecheck'   # vue-tsc 綠（LangType/Schema/RouteKey 型閘門）
$CF exec -T base-web sh -c 'pnpm lint'                          # oxlint+eslint 綠
# locale 對等 lint（全字典 zh-tw/zh-cn/en-us 鍵集一致；工具形實作定，可先以 typecheck Record<LangType> 把關）
git -C base-web status --porcelain   # 全走軌道、rev4-inline 標記；改動皆授權內
```

## G. demo 清償＋波0 守門不退化（SC-007）

```bash
# demo 端點已刪（router/handler/contract）；再抽 wire-schema 快照（typings 新增）
python3 tools/wire-schema extract && git -C rust-api diff --stat server/tests/fixtures/wire-schema.json  # 再抽 diff 空
$CF exec -T rust-api cargo test --workspace   # 移除 demo 後守門/覆蓋閘全綠、無殘留
grep -rniE 'rev2|rev3|soybean|anew' rust-api/server/src/{handler,model,auth}/ 2>/dev/null   # FR-015 零命中
```

## H. Constitution／fork-delta（SC-005）

```bash
python3 tools/docs-sync lint          # 0 錯 0 警（constitution v1.1.0、ADR 0026/0027/0028）
grep -rn 'rev4-inline' base-web/src/  # base-web inline 改動全帶標記（fork-delta 紀律）
```
