# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）已收刀。**009-role-admin 收刀——admin 管理面家族
  第一刀**（把基線預埋角色域 20 端點接成活的）：US1 角色生命週期／US2 三維授權治理狀態機／US3 停用即斷權／
  US4 授權回收桶〔Blocker 1 restore 七步鎖序封繼承旁路〕／US5 拒因明細（B-047）／US6 roleHome 讀端兜底；
  Blocker 2 casbin reload 重建-swap。前端建檔一對＋三 auth-modal〔endpoint net-new〕＋回收桶新頁＋明細通道。
  治理＝新島 G 入憲 v1.7.0＋ADR 0048/0049/0050；m007 唯一結構變更＝archive.role_id；零新錯誤碼/新表/新依賴。
  cargo test 408 綠、三 schema 閘＋typecheck＋fork-delta-lint＋六負向自證＋CDP S1/S2/S4/S6 綠。pins/summary/ADR
  見 events/STATE。消化 B-034/047/049/050；新增 B-082/083/084/085。
- 下一步（★方向覆蓋 2026-07-12：**menu 刀先行**、使用者管理刀順延；家族序其餘不變＝role→menu→user→
  audit→ip-rule）：**010-menu-admin brainstorm 已定案**（2026-07-13、docs/brainstorms/010-menu-admin.md；
  D1~D5 五拍板＋對抗式審查〔7 鏡頭×3 異質核驗、confirmed 23 全折入〕；核心＝menu 域 7 端點接活＋
  ★選單域序列化域〔advisory lock、封跨實體 grant 競態繼承旁路〕＋治理域/顯示域分層〔改 009 讀端〕；
  **零 seed 變更**——★B-060 拍板不折入、續留原觸發、收刀時註記）。下一步＝SDD 5 步：/speckit-specify
  （input＝brainstorm 檔、★手動起手）→clarify→plan→tasks→analyze、每步後 commit。
  ★BACKLOG 處置紀律（user 拍板）照舊：觸發命中折入該刀（使用者管理刀＝B-064 核心＋★B-084 MUST
  鎖序鉤子＋B-025/B-029/B-030、視 wire 設計 B-026、前端 unlock UI〔B-061 note〕；audit 刀＝B-061 audit
  項＋B-077/B-044/B-039；ip-rule 頁刀＝B-061 ip-rule 項）；未命中者（prod 組 B-037/080/081、obs 組、
  B-076、B-082/B-083 等觸發制項）續留原觸發條件、不提前做。
- 009 遺留/追蹤：B-082（committed-row 測試 panic-safe teardown——auth 節流 flaky 遺留 gate2 假紅、本刀清 2 次）／
  B-085（ADR 0050 protectedRevoke 命名 as-built 用 biz.role、ADR 字面 biz.policy＝文檔漂移、翻案時新 ADR）。
  ★LESSONS.md 近單卷 25000 token 上限（docs-sync L7 警告）、宜擇機分卷。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite 未必熱載新字典、否則顯 raw key、L-015）。
- ★Workflow 發射前 Bash 持久 CWD 須在 repo 根（hook/wf-watchdog 走相對路徑、漂進 submodule 會 404、L-137）。
- ★CDP 自駕（rev4-cdp 速查）：Edge@9229 `/json/list` 取 42080 page target→Node WebSocket `Runtime.evaluate`；
  quick-login 點 `超級管理員`（Super/123456）；i18n 驗 `$t('backend.<msg>')` 回 raw 即缺鍵；登入表單三坑 L-121~123。
