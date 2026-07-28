# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008）＋admin 家族（009~013）＋014-user-center＋015-pwd-custody＋
  016-observability＋017-audit-retention＋輕量軌三例（B-059／B-104／維護批）全收；憲法現版
  v1.14.0。各刀成果與判準詳 events/STATE、git 即史。
- ★維運待辦（016 遺留）：`deploy/secrets/alert_webhook_url.txt` 現值＝dev 收器 URL（收器已撤、
  投遞失敗重試無害）、正式接收端 URL 待 user 自填；obs＋metrics 觀測件現全 up、jobs sidecar
  屬 opt-in 未常駐。
- **進行中：018-governance-hardening**（治理工具鏈與編排紀律硬化；SDD 五步全落、TDD 分六執行單元
  編排）——U1 已收（B-111 改名＋CLAUDE.md 範本三件）；序：U2 G1 憑證掃描→U3 G2/G3 帳本自證
  ＋短 SHA 正規化→U4 G5/G7 真表與自測接線→U5 G4/G6 誠實輸出→U6 polish 終驗。收刀後待 user
  拍板下一波（BACKLOG 候選：B-102 changePassword 節流、B-027/B-028 auth 家族、B-037/B-042/
  B-081/B-013 prod 部署組等）。
- 遺留/追蹤：B-102（changePassword 舊密暴力試節流——throttle 綁死 login 不可直掛）；B-103（滯後卷）；
  B-099（契約層對 query 形零判別力）；B-100（軟刪掃描通用刀、016 已留 --job 位）；B-101（casbin
  按鈕碼與 buttons 聯集漂移）；B-094（未刪選單分頁截斷）。
- base-web 改動走 fork-delta 原行紀律（★lint 一律 `python3 tools/fork-delta-lint.py` 直跑——bash 跑假紅
  ＝L-143；以 example 為基線機器強制、掛 pre-commit 於 base-web pin 變動時擋）；base-web worktree
  commit 一律 `--no-verify`；★`.vue` template 標記用 `<!-- -->`（L-119）。
- ★治理工具已改名補 `.py`（B-111／018 U1）：`tools/docs-sync.py`／`schema-gate.py`／`fork-delta-lint.py`
  ／`wire-schema.py`——他機舊 session 照打舊名＝檔不存在即 fail-loud；隨 git sync 自然傳播。
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
