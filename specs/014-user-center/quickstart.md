# Quickstart: 014-user-center 驗證指南（Phase 1）

## 前置

- dev 五 service healthy（`docker ps`）；base-web 容器易 OOMKilled——CDP 前先驗 healthy＋vite 200。
- rust 全程容器內單一 cargo 進程 serial；fork-delta-lint 一律 `python3 tools/fork-delta-lint` 直跑（bash 跑假紅 L-143）。
- 新 i18n 鍵後 CDP 前 restart base-web（L-015）。

## 機器閘（全綠才過單元）

```bash
# 後端全量（容器內 serial）
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test --workspace'
# 契約閘：registry +4、4 case 結構斷言、wire_schema RFC3339
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test -p server --test contract && cargo test -p server --test wire_schema'
# schema-gate（預期 244/244 零變——本刀零 migration 零 seed）
# 前端型閘（typecheck 驗 i18n Schema 鏡像＋I18nKey typed literal）
docker exec rev4-admin-base-web-1 sh -c 'cd /app && pnpm typecheck'
# fork-delta（index.vue 修改型原行＋新檔圈界）
python3 tools/fork-delta-lint
```

## 重點單元測（新增、拆除即紅）

- **keep-sid 語意測**（負向自證①）：雙 session 下 change_own_password→本 sid 存活、他 sid 撤銷＋session_event(revoked, password_reset) 逐筆、廣播 8888 發出；拆 revoke_others 呼叫即紅。
- **單一驗證點零分叉**（負向自證②）：change_own_password 政策違規路徑斷言走 `validate_against_policy`（與 011 同函式）；「新≠舊」斷言**不在**該函式內（端點固有規則）。
- **getUserRoutes 白名單兩向＋home 交互**：零 menu policy 角色得 user-center 路由且 home 兜底落 user-center；白名單外路由不因此外洩。
- **updateProfile**：全 None no-op（零時戳 bump）、值域外 gender 不動、部分更新零串擾、鎖內查無 notFound。
- **固定序拒因**：oldMismatch／passwordMismatch／passwordSameAsOld／policy violations 各自可達且序正確。
- **redact**：ChangePwdReq Debug 輸出零明文；op-log payload 零密碼。

## CDP 實機驗收（S1~S6；cdp014_ 前綴測試資料、驗畢歸零）

| S | 場景 | 過門 |
|---|------|------|
| S1 | **非-super 帳號**登入→頭像下拉「個人中心」 | 進頁不 404（SC-001）；四卡版面與 rev3 快照逐項一致（SC-004） |
| S2 | 改密全流程（雙 session：Edge 42080＋curl 模擬他裝置） | 成功 toast 含「其他裝置已登出」；當前續用、他 session 下次請求 8888 被拒（SC-002） |
| S3 | 拒因五類逐一觸發（舊密錯／confirm 不一致／新同舊／政策違規多條／—） | 各自明確可區分；政策違規 toast 逐條明細（SC-003）；表單即時提示：政策 6+1 鍵＋confirm＋新同舊 |
| S4 | 佔位三處（改密卡兩 radio 路徑＋信箱/手機驗證碼組） | 點擊「功能建置中」toast、零寫入請求；radio 切換清空憑證欄 |
| S5 | 基本資料／信箱／手機各卡部分更新 | 單卡儲存零串擾（SC-006）；三態後綴與「未修改」語意正確 |
| S6 | 三語切換（zh-TW→zh-CN→en-US） | 全頁＋改密全流程零 raw key（SC-005）；zh-TW 在地化用語 |

CDP 要領：Edge@9229→42080 page target；quick-login 超級管理員；非-super 用 cdp014_ 測試帳號（psql 建、驗畢刪）；語系切換＝SOY_lang＋reload。

## 治理閘（實作前）

- amendment 親決 GATE（analyze 後）：(g) 擴字串 v1.12.0＋ADR 0065 轉 accepted→`docs(constitution): amend` 獨立 commit＋docs-sync generate 綠。

## 對帳文件

契約細節→[contracts/user-center-endpoints.md](./contracts/user-center-endpoints.md)；DTO 與固定序→[data-model.md](./data-model.md)；接地決策→[research.md](./research.md)。
