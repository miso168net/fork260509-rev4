# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008 auth family 五刀）＋**admin 管理面家族五刀全收**：role(009)、
  menu(010)、user(011)、audit(012)、**ip-rule(013) 已收刀**。**013-ip-rule-admin 收刀——家族第五刀**
  （IP 規則管理面：008 IP 閘後端做成 super-only 管理頁）：US1 讀端（getIpRuleList 三 filter
  additive＋審計欄 enrich＋混排回收桶清單＋三維搜尋卡）／US2 寫端（drawer 四欄＋NPopconfirm
  刪除復原＋拒因攔截層）／US3 授權預留（m010 casbin 四按鈕碼＋buttons 物件形 jsonb 回填＋
  SEED_CONTENT_OVERRIDE_ALLOWLIST 新軌道＋hasAuth）／US4 三語（B-061 兌現＋五拒因鍵）／
  U10 收刀前 user 拍板 UI 調整（列表欄序＋drawer 審計四項唯讀）。核心＝憲法 v1.11.0 (d) 擴字串＋
  ADR 0061~0064；零 schema／零新錯誤碼／零新依賴／零新島（純消費島 F）。cargo 全綠＋gate2
  244/244（override 軌生效）＋負向五條實證（⑤實驗證偽→勘誤＋B-099）＋CDP S1~S6 全 PASS＋
  final review 雙 Opus 零 merge-blocker。merge --no-ff 9d4b47c＋push（user 同意 2026-07-16）。詳 events/STATE。
- **下一步＝B-059 settings tooltip 三語化**（user 定向 2026-07-16；重偵察已落 B-059 條目——
  殘餘僅 tooltip 一處 help 鍵化、單一單元量級、零 migration 零後端）。新 session 起手：階段 0
  brainstorm（可短）→SDD 五步→實作。後續候選：B-060 demo 選單清理（010/011 兩度拍板折入、
  需 SEED_REMOVAL_ALLOWLIST 姊妹軌道＋ADR；★動工前重偵察——keep=11 前提已因 013 建頁漂移）、
  B-090 自助改密（解 B-030 前置）、prod 組（B-037/080/081）、obs 組（B-031/033）。
- 013 遺留/追蹤：B-098（ip_rule enrich 測試清理段不耐 panic、殘留污染 gate2——下次動 ip_rule
  測試時改 guard 形）；B-099（契約層對 query 形零判別力、防護實由 endpoint 測試承載）；
  B-100（系統軟刪掃描通用刀）；B-101（casbin 按鈕碼與 buttons 聯集漂移、011 缺口）；
  B-096（稽核 daterange 重複×4）；B-086（010 restorePolicy）；B-085（protectedRevoke 命名）。
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
