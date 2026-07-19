# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008）＋admin 家族（009~013）＋014-user-center＋015-pwd-custody＋
  輕量軌三例（B-059／B-104／維護批）全收；憲法現版 v1.14.0。詳 events/STATE、git 即史。
- **016-observability 已收刀**（2026-07-19、013 級大刀）：rev3 018 觀測底座全套移植（obs/metrics
  兩段 opt-in profiles、八映像最新穩定釘版）＋全環境 JSON log＋trace_id sanitize 單一 seam＋
  completion event＋/metrics 與 HTTP 層（pre-register 慣例首發）＋新埋點（B-065/HLL 兩維/軟區）＋
  告警 11 條全覆蓋四島義務＋webhook $__file 投遞＋reaper sidecar（m012 最小權限 role＝B-040 首案、
  九格判準）＋機生兩語拒因字典＋sock 窄化。ADR 0069~0075 accepted、零 Amendment；U1~U8 雙審＋
  final review 雙 Opus 零 merge-blocker；S1~S8 全機判單通、FR18/SC10 勾稽全 PASS。★維運注意：
  deploy/secrets/alert_webhook_url.txt 現值＝dev 收器 URL（收器已撤、投遞失敗重試無害）、正式
  接收端 URL 待 user 自填；obs＋metrics 觀測件現全 up、jobs sidecar 屬 opt-in 未常駐。詳 events/STATE。
- **下一步：待 user 拍板下一波範圍**（先前拍板 auth/prod 組後移；BACKLOG 候選：B-102 changePassword
  節流、B-027/B-028 auth 家族、B-037/B-042/B-081/B-013 prod 部署組、B-016 retention 本體等）。
- 遺留/追蹤：B-102（changePassword 舊密暴力試節流——throttle 綁死 login 不可直掛）；B-103（滯後卷）；
  B-099（契約層對 query 形零判別力）；B-100（軟刪掃描通用刀、016 已留 --job 位）；B-101（casbin
  按鈕碼與 buttons 聯集漂移）；B-094（未刪選單分頁截斷）。
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
