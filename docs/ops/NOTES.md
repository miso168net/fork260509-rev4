# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）＋admin 家族 role(009)、**menu(010) 已收刀**。
  **010-menu-admin 收刀——admin 管理面家族第二刀**（把基線預埋選單域 7 端點接成活的）：US1 選單生命週期／
  US2 刪除不留幽靈授權〔零繼承雙封＋button 絕版＋併發序列化〕／US3 回收桶／US4 停用兩域分層／US5 拒因明細。
  核心＝選單域 advisory 序列化域（島 H1）＋治理域·顯示域分層（H4、換 009 讀端四處）＋同鍵重建零繼承（H2）；
  憲法 v1.8.0（島 H 五條）＋ADR 0051/0052；零 migration/新表/seed/錯誤碼/依賴。cargo test 478 綠＋gate2
  244/244＋typecheck/fork-delta-lint＋5 負向自證＋3 併發機器證＋CDP 實機 S1/S3/S4/S5 綠。pins/summary/ADR
  見 events/STATE。merge --no-ff 回 default（user 同意 2026-07-13、★未 push）。
- 下一步（★家族序 role→menu→user→audit→ip-rule，role/menu 已收）＝**使用者管理刀（user）**。
  ★BACKLOG 處置紀律照舊（觸發命中折入該刀）：使用者管理刀＝B-064 核心＋★B-084 MUST 鎖序鉤子＋
  B-025/B-029/B-030、視 wire 設計 B-026、前端 unlock UI〔B-061 note〕；audit 刀＝B-061 audit 項＋
  B-077/B-044/B-039；ip-rule 頁刀＝B-061 ip-rule 項；未命中者（prod 組 B-037/080/081、obs 組、B-076、
  B-082/083 等觸發制項）續留原觸發、不提前做。★010 收刀前 minor 清理待跟進（非阻塞）：程式碼註解殘留
  DEC-* 編排代號（U4/U5）／U6 unused BatchDeleteMenuReq/RestoreMenuReq 型／U9 operate 三元縮排——另刀 pnpm
  format／docs-sync errata 一併。
- 010 遺留/追蹤：B-086（restorePolicy list_active vs 治理域一致性、U10 review surfaced）；009 B-085
  （protectedRevoke 命名漂移、翻案時新 ADR）；★LESSONS.md 近單卷 25000 token 上限（docs-sync L7 警告）、宜擇機分卷。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite 未必熱載新字典、否則顯 raw key、L-015）。
- ★Workflow 發射前 Bash 持久 CWD 須在 repo 根（hook/wf-watchdog 走相對路徑、漂進 submodule 會 404、L-137）；
  ★Workflow script prompt body 模板字串勿含 `${...}`（會被 JS 插值、node --check 只 parse 漏抓——發射前須執行期評估）。
- ★CDP 自駕（rev4-cdp 速查）：Edge@9229 `/json/list` 取 42080 page target→Node WebSocket `Runtime.evaluate`；
  quick-login 點 `超級管理員`（Super/123456）；i18n 驗 `$t('backend.<msg>')` 回 raw 即缺鍵；登入表單三坑 L-121~123。
