# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）＋admin 家族 role(009)、menu(010)、**user(011) 已收刀**。
  **011-user-admin 收刀——admin 管理面家族第三刀**（使用者域 10 端點全新地＋六刀遞延承諾兌現）：US1 CRUD＋
  指派寫端（B-084）／US2 停用踢除刪除即時斷 session（B-064）／US3 重設密碼＋政策 enforcement（B-029）／
  US4 回收桶／US5 session_policy／US6 解鎖 UI（B-061 note）／US7 拒因三語。核心＝島 I 五條入憲 v1.9.0＋
  ★B1 login/refresh 鎖內重驗＋撤銷觸發端 reason 映射（TTL=refresh_secs）＋密碼三重不洩；ADR 0053~0055；
  m008 純 seed 8 列；零 schema/零新錯誤碼。cargo 624 綠＋gate2 244/244＋CDP S1~S6 全 PASS＋final review
  零 blocker。詳 events/STATE。merge --no-ff 回 default（user 同意 2026-07-14、★未 push）。
- 下一步（★家族序 role→menu→user→audit→ip-rule，前三刀已收）＝**audit 刀（稽核/操作日誌管理面）**。
  ★BACKLOG 處置紀律照舊（觸發命中折入該刀）：audit 刀＝B-061 audit 項＋B-077/B-044/B-039＋B-089
  （sys_token 孤兒順帶）；ip-rule 頁刀＝B-061 ip-rule 項；未命中者（prod 組 B-037/080/081、obs 組、
  B-076、B-082/083 等觸發制項）續留原觸發、不提前做。
- 011 遺留/追蹤：B-088（notRestorable dead-key＋四文件漂移、errata 紀律四處一併）；B-086（010 restorePolicy
  一致性）；009 B-085（protectedRevoke 命名漂移）；minor（另刀順手）＝audit helper 四支 pub→pub(crate) 收斂
  ＋010 殘留 DEC-* 註解/U6 unused 型/U9 縮排（pnpm format/errata 一併）；★LESSONS 23.7k 逼近 25k 上限、
  宜擇機分卷（L7 警告中）。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite 未必熱載新字典、否則顯 raw key、L-015）。
- ★Workflow 發射前 Bash 持久 CWD 須在 repo 根（hook/wf-watchdog 走相對路徑、漂進 submodule 會 404、L-137）；
  ★Workflow script prompt body 模板字串勿含 `${...}`（會被 JS 插值、node --check 只 parse 漏抓——發射前須執行期評估）；
  ★防呆②長度下限 400（固定 800 在短前綴單元誤觸、L-140）；mac2 中文 bash 工具 LC_ALL=C（L-142）＋新機先 generate-dev-cert 再 compose up（L-141）。
- ★CDP 自駕（rev4-cdp 速查）：Edge@9229 `/json/list` 取 42080 page target→Node WebSocket `Runtime.evaluate`；
  quick-login 點 `超級管理員`（Super/123456）；i18n 驗 `$t('backend.<msg>')` 回 raw 即缺鍵；登入表單三坑 L-121~123。
