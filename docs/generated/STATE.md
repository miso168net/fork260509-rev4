<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=b390a34

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：75（accepted 70、superseded 5）
- BACKLOG 待辦：28（next：B-108）｜滯後：2
- LESSONS：152 筆（next：L-153）
- events：25 筆（feature_close 16、misc 8、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-19｜feature_close｜016-observability｜016-observability 收刀——觀測層全套刀（obs 九項＋B-040＋三搭車、013 級大刀）。底座＝rev3 018 全套移植：obs profile（loki 3.7.3＋alloy v1.17.1 非 root＋grafana 13.1.0＋wollomatic socket-proxy 1.12.3）＋metrics profile（prometheus v3.13.1 LTS＋postgres-exporter v0.20.1＋redis_exporter v1.87.0-alpine＋pushgateway v1.11.3 持久卷）、八映像全最新穩定（user 拍板甲案）、全 mem_limit＋unless-stopped、S1 六服務不變式＋S8 全滅零影響（docker kill 屬手動停止 restart 不套用＝as-built 勘誤、真故障 SIGTERM 自回復實證）。rust 側＝全環境 JSON log（fmt().json() 單一形）＋request span trace_id（sanitize 單一 seam：白名單+64、B-045 子項）＋completion event（target=http.request、ipgate 外亦記、APP_LOG_EXCLUDE_PATHS fail-default 全記、B-054）＋/metrics 端點（obs.rs recorder 單份＋pre-register 顯式 0 慣例首發：三既有 counter 全 label＋新增五 counter）＋axum-prometheus HTTP 層（endpoint label 收斂 unmatched 防無界基數）＋B-065 denylist_hit/settings_select＋HLL 兩維 PFADD/PFCOUNT（島 E3 麵包屑範疇、fail-open＋fail counter、B-033殘）＋軟區命中計數（B-074 量測）。告警＝11 條 as-code（baseline 三＋壓制窗內任一即紅 5m＋降級四子③a~③d 全覆蓋四島義務 E1/F3/G1/J2＋容量④ n_live_tup 四表 100 萬＋reaper ⑤超時/⑤b 誤配雙規則）逐條綁 webhook 投遞（$__file 讀 secret 主案源碼實證成立、B-031/B-053）；S4 六規則實轉紅＋收器收到＋annotation 零原始 log 行。reaper＝m012 最小權限 role（NOLOGIN＋SELECT,DELETE ON sys_token＋施工抓包補 USAGE ON SCHEMA public、零密碼、B-040 首案）＋設密腳本 stdin heredoc＋facade 九格判準矩陣（expires_at 逾 G、status 不入判準、單語句 DELETE）＋bin（dry-run 預設/--execute/--job 擴充位/失敗不推心跳）＋jobs profile sidecar（明文 --execute、entrypoint 分派器）；S5 守恆＋越權雙打 permission denied＋⑤/⑤b 轉紅投遞全驗（B-063/B-067 閉環）。字典＝docs-sync 生成器（TS locale 直解、兩語 69 鍵、雙產物＋check 守門延伸、B-007）。品質＝U1~U8 八單元 implementer＋spec/quality 雙審（quality 審累計抓 7 真 blocker：axum-prometheus endpoint 基數、HLL 測試共享 key 互踩、PFCOUNT delta flaky、sidecar PID1 吞 SIGTERM、ureq 無 timeout、rust-api 板殭屍分位格、redis 板 k8s 殘留變數——全修畢複審零）＋final review 雙 Opus 零 merge-blocker；容器 --lib 726/0；quickstart S1~S8 全機判單通；FR 18 條/SC 10 條勾稽全 PASS 零缺口。BACKLOG 收刀帳：全刪 B-007/031/033/040/041/053/054/063/065/067（B-033 之 IP TTL 拆分經偵察實證 008 已併刀消化、008 漏改去處欄之簿記缺口就此補正）；縮殘改寫 B-016（剩 retention 本體）/B-045（刪 trace_id 子項）/B-074（剩負快取本體）；留位註記 B-038（instance 維）/B-100（--job 擴充位）。★維運交接：alert_webhook_url.txt 現值＝dev 收器 URL（已撤）、正式接收端待 user 自填。
- 2026-07-19｜misc｜B-086 收單（user 拍板 2026-07-19 甲案：停用選單歸檔授權可復原）——restore 第⑥步 menu 存在判準換源 list_active→list_governed（治理域＝未刪含停用、對齊 010 FR-019 停用≠撤銷；軟刪 orphan 照舊 NotRestorable）；不一致實錘＝授權樹讀端已走治理域可對停用選單新授、唯復原被顯示域擋。Workflow 單元 wf_b9edde7d（implementer TDD＋spec/quality 雙審、3 agents 首輪零 blocker）；紅測 restore_menu_disabled_target_applies_governed 先紅後綠＋守恆補測軟刪案、容器內 --lib 694/0（基線 692＋2）；主線親驗硬錨（git 6c8ee72＋模組 20/0 親跑）；rust-api pin 531b412→6c8ee72；無 ADR（對齊既定 FR-019 語義之修正、比照維護批先例）；另錄 L-151（cd/pwd 生成慣性事故）
- 2026-07-19｜misc｜B-085 收單（user 拍板提前立案）——ADR 0068 accepted：校正 ADR 0050 字面漂移、protectedRevoke 拒因 key 正典＝biz.role.protectedRevoke（as-built 三處一致：rust handler／契約表／三語 locale；憲章路徑＝實作推翻拍板立新 ADR、0050 body 不動）；實作零改動、純文檔治理

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
