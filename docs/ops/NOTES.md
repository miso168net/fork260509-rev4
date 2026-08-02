# NOTES — 當前意圖／下一步

- 波 0~1（001~008）＋admin 家族（009~013）＋014~020 各刀＋輕量軌（B-059／B-104／維護批×2）
  全收；憲法現版 v1.15.0。各刀成果與判準詳 events/STATE、git 即史。
- ★維運待辦（016 遺留）：`$SECRETS_DIR/alert_webhook_url.txt` 現值＝dev 收器 URL（收器已撤、
  投遞失敗重試無害）、正式接收端 URL 待 user 自填——★019 起落點已遷出 repo、密文權威來源＝
  `deploy/secrets.dev.enc.yaml`，改值後須依 RUNBOOK §15.4 回寫加密檔；觀測件（obs／metrics
  profiles）現非常駐、要用再 up；jobs sidecar 屬 opt-in 未常駐。
- **020-email-verify-smtp 已收刀**（2026-08-01、B-028＋SMTP 基建；憲法 v1.15.0＋ADR 0085/0086）。
- **維護批已收**（2026-08-01~02 詳 events）：B-128／B-112／B-129／B-101 全收／lint 提速＋
  條款改名／B-045＋B-018 結清／B-110 階段 0（b8c7ad9）／B-133＋B-134（b89f3be：Lint24
  契約閘＋backend.system 補二鍵＋ADR 0088；源起＝graphify trace 輪機器對賬）。
- ★樣板 repo **docs-governance-template** 已建（2026-08-03、P1 文件批收單＝治理架構
  可移植化教義＋零件表；P2~P4 追蹤詳該 repo BACKLOG、rev4 側指標＝B-136）。
- ★repo 已建 graphify 圖譜（graphify-out/、7c53bca）：碼結構問題可先 graphify query；已知
  邊界＝Vue template／TS ambient／router 動態 import 不進圖、rust↔web 碼邊 0（跨語族防線）
  ——跨端契約問題走 wire-schema.py／直讀、勿問圖。
- **下一步：待 user 拍板**——推薦 B-102 changePassword 舊密試錯節流（既有
  password_change_min_interval 只擋「成功設密」、錯舊密永不觸發＝缺口實在；020
  send_email_code 即完整範本；★須先拍兩題：redis 故障 fail-open〔傾向〕vs closed、門檻走
  settings 鍵〔傾向；同端點已有一鍵〕vs 常數——後者決定要不要多一支 migration）。
- 遺留/追蹤（詳 BACKLOG）：B-103 滯後卷／B-099／B-100／B-094。
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
