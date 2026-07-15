# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）＋admin 家族 role(009)、menu(010)、user(011)、
  **audit(012) 已收刀**。**012-audit-admin 收刀——admin 管理面家族第四刀**（稽核中心：四源稽核查詢＋
  存取軌跡記錄＋水平線清理）：US1 讀端四源（操作日誌/存取日誌/登入嘗試/會話事件 GET、read-only super-only
  ＋打碼單點＋ILIKE trigram＋人員過濾解析＋時間閉開）／US2 access-log 首個寫入端（fail-open layer、不記
  body・query、未認證零列）／US3 purge 水平線（表白名單×天數、下限 30、同交易 DELETE＋PURGE 自記＋固定
  豁免）／US4 品質（unlock PG-first B-077＋idle 冪等 B-093）／US5 稽核中心頁四分頁＋purge modal＋三語。
  核心＝島 J 五條入憲 v1.10.0＋MODAL-WIRING (i)＋ADR 0057~0060；m009（pg_trgm＋GIN×2＋casbin 2 列＋
  B-089 孤兒清理）；零 schema／零新錯誤碼／零新依賴。cargo 687 綠＋契約 63＋gate2 244/244＋CDP S1~S7 全
  PASS＋final review 雙 Opus 零 merge-blocker。詳 events/STATE。merge --no-ff 回 default＋push（user 同意
  2026-07-15、Telegram merge+push）。
- 下一步（★家族序 role→menu→user→audit→ip-rule，前四刀已收）＝**ip-rule 頁刀（IP 規則管理面）**。
  ★BACKLOG 處置紀律照舊（觸發命中折入該刀）：ip-rule 頁刀＝B-061 ip-rule 項；未命中者（prod 組
  B-037/080/081、obs 組、B-076、B-082/083 等觸發制項）續留原觸發、不提前做。
- 012 遺留/追蹤：B-095（sys_menu 測試隔離 flake、下次動 sys_menu 測試時）；B-096（稽核四 search 卡
  daterange 邏輯重複×4、下次觸及稽核 search 卡時提煉 composable）；B-086（010 restorePolicy 一致性）；
  009 B-085（protectedRevoke 命名漂移）。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite 未必熱載新字典、否則顯 raw key、L-015）；
  ★base-web 容器易 OOMKilled（137）、CDP/spike 前先驗 healthy＋vite 200、掛了主線 compose up -d 復活（012 U8 實證）。
- ★Workflow 發射前 Bash 持久 CWD 須在 repo 根（hook/wf-watchdog 走相對路徑、漂進 submodule 會 404、L-137）；
  ★Workflow script prompt body 模板字串勿含 `${...}`（會被 JS 插值、node --check 只 parse 漏抓——發射前須執行期評估）；
  ★防呆②長度下限 400（固定 800 在短前綴單元誤觸、L-140）；★agent StructuredOutput 字串欄勿含角括號 `<>`（破壞
  參數解析、5 次重試全滅——prompt 明令禁用、012 U8 實證）；mac2 中文 bash 工具 LC_ALL=C（L-142、wf-watchdog 已內建）。
- ★CDP 自駕（rev4-cdp 速查）：Edge@9229 `/json/list` 取 42080 page target→Node WebSocket `Runtime.evaluate`；
  quick-login 點 `超級管理員`（Super/123456）；i18n 驗 `$t('backend.<msg>')` 回 raw 即缺鍵；登入表單三坑 L-121~123。
