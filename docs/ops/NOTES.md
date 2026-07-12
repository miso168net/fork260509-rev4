# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）已收刀。**009-role-admin 收刀——admin 管理面家族
  第一刀**（把基線預埋角色域 20 端點接成活的）：US1 角色生命週期／US2 三維授權治理狀態機／US3 停用即斷權／
  US4 授權回收桶〔Blocker 1 restore 七步鎖序封繼承旁路〕／US5 拒因明細（B-047）／US6 roleHome 讀端兜底；
  Blocker 2 casbin reload 重建-swap。前端建檔一對＋三 auth-modal〔endpoint net-new〕＋回收桶新頁＋明細通道。
  治理＝新島 G 入憲 v1.7.0＋ADR 0048/0049/0050；m007 唯一結構變更＝archive.role_id；零新錯誤碼/新表/新依賴。
  cargo test 408 綠、三 schema 閘＋typecheck＋fork-delta-lint＋六負向自證＋CDP S1/S2/S4/S6 綠。pins/summary/ADR
  見 events/STATE。消化 B-034/047/049/050；新增 B-082/083/084/085。
- 下一步：**009 已收官、無既定下一刀**——下一個方向待 brainstorm 拍板。候選線索（見 BACKLOG）：
  ①admin 家族續刀：使用者管理〔B-064 停用帳號/改密/admin 踢除端點，消費 006 revoke primitive；★角色指派
  寫端落地必納 sys_role 鎖序 B-084〕、B-025/026 使用者編輯縫隙；②寫端授權下放前置〔B-083 no-escalation
  上限檢查＋seeded 護欄複評＋明細通道受眾邊界重評，任何非-super 寫端下放前必建〕；③prod 部署硬化
  〔B-037 TLS/信任拓樸＋B-080 CDN 錨碼＋B-081 xdb COPY〕；④殘餘清理〔B-060 demo 選單、B-061 audit/ip-rule
  三語、B-063 reaper、B-074~077〕。
- 009 遺留/追蹤：B-082（committed-row 測試 panic-safe teardown——auth 節流 flaky 遺留 gate2 假紅、本刀清 2 次）／
  B-085（ADR 0050 protectedRevoke 命名 as-built 用 biz.role、ADR 字面 biz.policy＝文檔漂移、翻案時新 ADR）。
  ★LESSONS.md 近單卷 25000 token 上限（docs-sync L7 警告）、宜擇機分卷。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite 未必熱載新字典、否則顯 raw key、L-015）。
- ★Workflow 發射前 Bash 持久 CWD 須在 repo 根（hook/wf-watchdog 走相對路徑、漂進 submodule 會 404、L-137）。
- ★CDP 自駕（rev4-cdp 速查）：Edge@9229 `/json/list` 取 42080 page target→Node WebSocket `Runtime.evaluate`；
  quick-login 點 `超級管理員`（Super/123456）；i18n 驗 `$t('backend.<msg>')` 回 raw 即缺鍵；登入表單三坑 L-121~123。
