# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004~008）＋admin 家族（009~013）＋014-user-center＋015-pwd-custody＋
  016-observability＋017-audit-retention＋018-governance-hardening＋019-secrets-sops＋
  輕量軌三例（B-059／B-104／維護批）全收；憲法現版 v1.14.0。各刀成果與判準詳
  events/STATE、git 即史。
- ★維運待辦（016 遺留）：`$SECRETS_DIR/alert_webhook_url.txt` 現值＝dev 收器 URL（收器已撤、
  投遞失敗重試無害）、正式接收端 URL 待 user 自填——★019 起落點已遷出 repo、密文權威來源＝
  `deploy/secrets.dev.enc.yaml`，改值後須依 RUNBOOK §15.4 回寫加密檔；觀測件（obs／metrics
  profiles）現非常駐、要用再 up；jobs sidecar 屬 opt-in 未常駐。
- **019-secrets-sops 已收刀**（2026-07-30）：機密管理——SOPS+age 密文入版控（8 key 單檔＋
  digest 釘版 wrapper＋P4 fail-loud 解密管線）＋明文遷出 repo（SECRETS_DIR 三級解析五消費端
  同口徑）＋三層掃描防線（Betterleaks×L16×value-guard、pre-push 三 repo）＋RUNBOOK §15 十小節
  ＋ADR 0079~0083；收刀金鑰儀式完成（user 真鑰上位、暫代鑰原子撤銷五準則、7 leaf 實值輪替、
  SC-007 保全）；測試 347→349、pin 逐字未變。詳 events/STATE。
- **下一步：待 user 拍板下一波範圍**（BACKLOG 候選：B-102 changePassword 節流、B-027/B-028
  auth 家族、B-037/B-042/B-081/B-013 prod 部署組等；另 B-125〔host 暫存命名雙軌統一〕屬
  拍板級、觸發時機見該列）。
- 遺留/追蹤：B-102（changePassword 舊密暴力試節流——throttle 綁死 login 不可直掛）；B-103（滯後卷）；
  B-099（契約層對 query 形零判別力）；B-100（軟刪掃描通用刀、016 已留 --job 位）；B-101（casbin
  按鈕碼與 buttons 聯集漂移）；B-094（未刪選單分頁截斷）。
- base-web 改動走 fork-delta 原行紀律（★lint 一律 `python3 tools/fork-delta-lint.py` 直跑——bash 跑假紅
  ＝L-143；以 example 為基線機器強制、掛 pre-commit 於 base-web pin 變動時擋）；★**base-web worktree
  commit 的 `--no-verify` 慣例已廢止**（019）——hooksPath 指向外層即結構性旁路上游 husky、原始理由
  （躲 husky 跑 pnpm install）消失，而 `--no-verify` 會同時繞過機密掃描（事件型：繞過一次即真進 git、
  下次不再抓）；詳 ADR 0082 決策 5；★`.vue` template 標記用 `<!-- -->`（L-119）。
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
