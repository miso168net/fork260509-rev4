# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）＋admin 管理面家族五刀（009~013）＋B-059 輕量刀
  全收。**014-user-center 已收刀**（個人中心自助頁、B-090 兌現＋rev3 025 全頁承襲）：US1 自助改密
  全鏈（固定驗證序五拒因＋keep-sid 撤他裝置 8888＋島 I1/I2/I5 合規時序）／US2 profile 三卡部分更新
  （三態折疊不洩 operator）／US3 getUserRoutes self-service 白名單（ADR 0065、人人可達＋零 policy
  角色 home 兜底新行為）／US4 三語 31＋3 鍵（D2 統一單句 pwdPolicyNotMet＝實作期盤點缺口 user 親決
  補鍵、量詞勘誤 30→31）。核心＝憲法 v1.12.0（(g) 擴 i18n key＋島 I2 keep-sid 釋義）＋ADR 0065；
  零 migration／零 schema／零新錯誤碼／零新依賴／零新島。全量閘綠＋CDP S1~S6 全 PASS（U9 抓獲
  D4 比對源錯位並修——authStore.userName＝nick_name 別名〔憲法 L45〕、改走 getProfile 真帳號 prop）＋
  final review 雙 Opus 零 merge-blocker。merge --no-ff 0a3f790＋push（user 同意 2026-07-17）。詳 events/STATE。
- **B-104 Transition 卡死 workaround 已收刀**（2026-07-17、輕量軌第二例——user 拍板提前施工；
  憲法 v1.13.0 新用途 (j) 首案＋ADR 0066；詳 events/STATE）。
- **下一步（user 拍板 2026-07-17 roadmap）**：①B-030 首登強制改密（★014 已解鎖觸發條件、
  ADR 0055 拆階段；需 sys_user 加欄＋login 插閘＋強制改密頁；順路評 B-103；★新 session
  brainstorm 起手）→②維護批輕量刀（B-098＋B-096＋B-092 三條打包、各自獨立 commit）→
  ③B-060 demo 選單清理（順路收 B-101、順路裁 B-094；★動工前重偵察——keep=11 前提已因
  013 建頁漂移）→之後 auth 延伸組（B-027/028/102）vs prod 組（B-013/037/038/042/080/081）擇定。
- 014 遺留/追蹤：B-102（changePassword 舊密暴力試節流——throttle 綁死 login 不可直掛）；
  B-103（email/phone 雙卡同構重複、B-096 同構容忍先例）。013 前遺留：B-098（ip_rule enrich 測試
  清理段不耐 panic）；B-099（契約層對 query 形零判別力）；B-100（系統軟刪掃描通用刀）；
  B-101（casbin 按鈕碼與 buttons 聯集漂移）；B-096（稽核 daterange 重複×4）；B-086（010
  restorePolicy）；B-085（protectedRevoke 命名）。
- base-web 改動走 fork-delta 原行紀律（★lint 一律 `python3 tools/fork-delta-lint` 直跑——bash 跑假紅
  ＝L-143；以 example 為基線機器強制、掛 pre-commit 於 base-web pin 變動時擋）；base-web worktree
  commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite 未必熱載新字典、否則顯 raw key、L-015）；
  ★base-web 容器易 OOMKilled（137）、CDP/spike 前先驗 healthy＋vite 200，掛了主線 compose up -d 復活；
  ★dev 熱套含 casbin 列的 migration 後須 restart rust-api 重載 enforcer＋重新登入（否則 hasAuth
  全 false、L-145）。
- ★Workflow 發射前 Bash 持久 CWD 須在 repo 根（L-137）；★script prompt body 勿含 `${...}`（JS 插值、
  node --check 漏抓）；★防呆②長度下限 400（L-140）；★agent StructuredOutput 字串欄勿含角括號
  （012 U8 實證）；★看門狗 ARMED 首行必核 run-id 與 launch 回傳一致、不符即 TaskStop 重掛
  （wf 目錄晚於掃描窗建立會被舊目錄搶答、L-144）；mac2 中文 bash 工具 LC_ALL=C（L-142）。
- ★CDP 自駕（rev4-cdp 速查）：Edge@9229 `/json/list` 取 42080 page target→Node WebSocket
  `Runtime.evaluate`；quick-login 點 `超級管理員`（Super/123456）；i18n 驗 `$t('backend.<msg>')` 回
  raw 即缺鍵；登入表單三坑 L-121~123；★NTree 大清單虛擬滾動——textContent 斷言前先捲底（013 S6 實證）。
