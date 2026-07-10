<!-- next: B-080 -->
# BACKLOG — 待辦

條目格式 `- B-NNN｜<一句話>｜<觸發條件或期限（選）>`；配號取檔頭 next-id 後 bump、號碼永不回收；完成即刪列、git 即史。

- B-007｜觀測側 msg 可讀性補強候選（log 附 key→預設語言譯文、或維運字典對照表；ADR 0001 第 8 題配套）｜obs 層刀或維運痛點實際出現時
- B-011｜儀表板做不做／怎麼做（傾向 v1＝固定版面零新表）｜入波排程時｜出處：rev3:DECISIONS§1-待決⑥a（K1-06）
- B-012｜報表匯出 PDF/CSV（傾向 v1＝同步匯出零新表）｜入波排程時｜出處：rev3:DECISIONS§1-待決⑥b（K1-07）
- B-013｜靜態資料加密（傾向磁碟／tablespace 層）｜prod 部署定稿前必拍｜出處：rev3:DECISIONS§1-待決⑥c（K1-08）
- B-014｜合規姿態升級（傾向維持現姿態）｜對外開放／多租戶需求時｜出處：rev3:DECISIONS§1-待決⑥d（K1-09）
- B-015｜設定熱讀推廣 keyed map（單鍵 swap 夠用）｜swap 不敷用時｜出處：rev3:DECISIONS§1-⚠️l（K1-21）
- B-016｜稽核 log retention 政策（v1 只容量監控）｜容量警示時｜出處：rev3:DECISIONS§1-⚠️n（K1-23）
- B-018｜帳號級鎖定被第三方惡意鎖人的 DoS 面重估（漸進延遲/CAPTCHA）（★部分消化 2026-07-10：007 三層緩解已落＝captcha 軟區抬自動化成本＋unlockLogin 手動解鎖＋鎖存續≤window 自解〔③零稽核列、sticky 續鎖構造上不可能〕；殘餘＝漸進延遲未做、第三方觸鎖本身仍可達成——per-user 節流結構性如此、IP 維防護遞延 B-032）｜節流延伸或 IP 閘刀｜出處：rev3:REVIEW§6（K2-02）
- B-019｜XFF 信任模型改最小化信任錨（勘誤 2026-07-10：rev3 有完整三層信任模型〔peer-gate → CDN 位置錨 → rightmost-untrusted〕，internal_default 僅 Tier-2 skip 集之一參數、住 operator TOML；rev3 REVIEW 將「寬 internal_default 信任」登記為 accepted 取捨、非 open 缺陷）｜IP/ingress 刀｜出處：rev3:REVIEW§6＋CLAUDE.md§8.2（K2-03）
- B-020｜CDN 位置錨是否上真驗證重估｜ingress 拓樸簡化時｜出處：rev3:REVIEW§6（K2-04）
- B-024｜先枚舉 ingress 拓樸全貌再定 IP 取證欄位形｜首次重設計 IP 取證欄形的刀（002 基線＝承襲 rev3 形＋user 定稿、不觸發）｜出處：rev3:REVIEW§5（K2-08）
- B-025｜使用者編輯模式帳號名欄鎖定（消滅靜默 no-op 縫隙）｜使用者管理刀｜出處：rev3:REVIEW§3.2-F-5（K2-09）
- B-026｜部分更新契約內建顯式 clear 語意｜部分更新 wire 設計時｜出處：rev3:REVIEW§3.4（K2-10）
- B-027｜alt-login 補全知識包（確認密碼規則值快照 race 的 toRef 範式等）（註 2026-07-10：007 captcha 底座〔無狀態簽題＋提交即消耗〕可複用；★alt-login 端點的節流 seam 不自動涵蓋——throttle 判定序只掛 login，屆時需自行接）｜B-008 拍板後施工輸入｜出處：rev3:CHECKLIST§4.2（K2-11）
- B-028｜手機/信箱真實驗證＋驗證碼改密（與 alt-login 共享 captcha 基建、宜同刀或緊接）（註 2026-07-10：007 captcha 底座可複用——loginCaptcha 端點形＋無狀態簽題直接搬）｜user-center/auth 波排程｜出處：rev3:CHECKLIST§4.2（K2-12）
- B-029｜改密後撤既有 session＋密碼政策前端提示補完｜auth 設計期內建｜出處：rev3:CHECKLIST§4.2（K2-13）
- B-030｜新帳號初始密碼政策化（隨機生成＋首登強制改密）｜建用戶功能刀｜出處：rev3:CHECKLIST§4.2＋REVIEW§3.3-F-7（K2-14）
- B-031｜obs 告警通知投遞 channel 最小一條納首發｜觀測層刀｜出處：rev3:CHECKLIST§4.2（K2-15）
- B-032｜節流強化包（IPv6 前綴鍵/可調門檻/白名單/CAPTCHA/手動解鎖/審計區分）（★部分消化 2026-07-10：007 已落可調門檻三鍵＋CAPTCHA 軟區＋unlockLogin 手動解鎖；殘餘＝IPv6 前綴鍵＋IP 白名單跳節流＋鎖定專屬審計欄——全繫真實 IP 信任錨／審計欄形）｜IP/ingress 刀或審計刀｜出處：rev3:CHECKLIST§4.2（K2-16）
- B-033｜節流快取遞延組（壓制告警/廣度估計/TTL 拆分）＋誤鎖緩解優先級提前（★部分消化 2026-07-10：007 已落壓制麵包屑結構化告警＋unlockLogin 誤鎖緩解；殘餘＝grafana 告警規則＋HLL 廣度估計＋IP 維 TTL 拆分）｜obs 刀（grafana/HLL）＋IP 閘刀（TTL 拆分）｜出處：rev3:CHECKLIST§4.2＋§3.H（K2-17）
- B-034｜policy 回收桶來源過濾器＋復原判定去牆鐘化（archive 入來源角色 id 欄）｜角色刪除/archive 刀 schema 期｜出處：rev3:CHECKLIST§4.2（K2-18）
- B-035｜public tunnel origin 做一等信任集（非內網子集特例）｜信任模型/ingress 刀｜出處：rev3:CHECKLIST§4.2（K2-19）
- B-036｜列表排序 per-column 索引評估＋三端白名單單一來源或 parity 檢查｜列表排序刀｜出處：rev3:CHECKLIST§4.2（K2-20）
- B-037｜prod TLS/信任拓樸落地組做成部署 checklist＋自動化驗收｜prod 部署刀｜出處：rev3:CHECKLIST§4.2＋§3.E（K2-21）
- B-038｜prod 多副本橫向擴展拓樸留位（LB＋共用 DB/Redis）｜含水平擴展目標時｜出處：rev3:CHECKLIST§4.2（K2-22）
- B-039｜審計 scale：pg_trgm 索引＋purge 執行面（政策本體＝B-016）｜審計功能刀 schema 期｜出處：rev3:CHECKLIST§4.2＋§5（K2-23）
- B-040｜cleanup sidecar 最小權限 DB 憑證（背景 job secret 最小權限＝預設）｜首個背景 job 設計期｜出處：rev3:CHECKLIST§3.A（K2-25）
- B-041｜obs 採集容器非-root 硬化起手照配（docker.sock 窄化）｜觀測層刀起手｜出處：rev3:CHECKLIST§3.A（K2-26）
- B-042｜prod nginx 完整資源 CSP 收緊內建部署驗收｜prod 部署刀｜出處：rev3:CHECKLIST§3.J（K2-27）
- B-044｜op-log payload PII 遮蔽策略先拍再落庫｜審計 payload 設計期｜出處：rev3:CHECKLIST§3.J（K2-29）
- B-045｜低位殘項 checklist（trace_id 控制字元/XFF 空 token/計數 race/migration down 非對稱/CDN 錨）｜重寫對應模組時逐項內建｜出處：rev3:CHECKLIST§3.J（K2-30）
- B-046｜IP 閘門政策判定單一來源（純函式回命中規則、middleware 只呼叫）｜IP 閘刀設計期｜出處：rev3:CHECKLIST§3.E（K2-31）
- B-047｜protected-reject 錯誤訊息具體化（detail 插值通道＋洩漏評估；信封加欄＝憲法 §I.3 Amendment 級、payload 形等治理刀 brainstorm 定）｜治理刀（casbin 寫端設計期；003 錯誤信封刀已收且明拒本項、rev4 現零發射點）｜出處：rev3:CHECKLIST§3.H（K2-32）
- B-049｜批次軟刪自管 transaction（去 sentinel DbErr 控制流）｜首個批次寫端刀｜出處：rev3:CHECKLIST§3.H（K2-34）
- B-050｜部分更新全 None 提前 no-op 入 handler/facade 慣例｜部分更新語意設計時｜出處：rev3:CHECKLIST§3.H（K2-35）
- B-053｜obs 面板與 metrics 慣例（docker 友善板/計數器 pre-register/pushgateway 持久卷）｜觀測層刀起手｜出處：rev3:CHECKLIST§3.I（K2-38）
- B-054｜completion log 噪音治理（預留 path 級過濾開關）｜request log 設計時｜出處：rev3:CHECKLIST§3.I（K2-39）
- B-059｜settings 頁 tooltip 顯示的 description＝DB seed 繁體名（7/8 與 i18n label 同文、zh-CN/en 下腳本不符、tooltip 冗餘）→ enrich 成真正 localized 說明（偵察 2026-07-10 薦案 a＝tooltip 改 $t help 鍵、seed description 留 DB 作 fallback、零 migration；005 遺漏 session_idle_timeout 的 label 鍵〔三語 UI 直顯 seed 繁體〕宜同刀補；★007 已落 login_throttle_* 三鍵、同檔 index.vue labelKeyMap＋三語 locale 已動——先後次序顧慮已解、enrich 屆時直接改）｜enrich settings 說明的刀｜出處：004 單元⑧ user 拍板 B（保留＋BACKLOG）
- B-060｜demo 選單清理：002 casbin menu seed 給 R_SUPER 全 soybean template demo（about/document/plugin/alova/pro-naive/multi-menu/function）menu policy，rev4 真選單應只 home/manage/user-center｜動 002 casbin/sys_menu seed（新 migration；偵察 2026-07-10：demo＝67 menu＋77 casbin 列、keep＝11〔含 B-061 三未建頁項不動〕；casbin_rule 無 deleted_at→policy 硬刪不可避、gate2 缺列紅需 SEED_REMOVAL_ALLOWLIST＋新 ADR〔0032 只放寬新增〕；拍板點＝sys_menu hard vs 軟刪／exception 樹入否；受影響測試＝sys_menu facade list_active 計數＋route handler R_USER_COMMON 正向斷言）｜出處：005 CDP item#2 拍板 2026-07-06
- B-061｜3 manage 子項 i18n：manage_audit/ip-rule/policy-archive 已 002 seed 選單項但 locale 三語無 route.manage_* 譯文→dynamic 選單顯 raw key（未建頁、前端無 route/view→點擊 404）｜各子系統刀建時補譯文（★route locale 鍵無「獨立新增」授權、須隨建頁走 MODAL-WIRING(e)＝憲法 §III.2；004 manage_system-settings 即此範式；2026-07-06 定案延後、非 quick win；註 2026-07-10：007 /systemManage/unlockLogin 純 API、零選單項零譯文需求、不擴本清單——前端解鎖 UI 屆時隨使用者管理刀建頁同軌道補）｜出處：005 CDP item#2 拍板 2026-07-06
- B-063｜孤兒/背景 reaper：sys_token 跨 session 孤兒＋rotated 過期列完整回收（006 refresh-time prune_expired_rotated 已止血同 chain；跨 session/背景批次遞延）｜obs/維運刀｜出處：006 R6/SC-009
- B-064｜停用帳號/管理員踢除 端點接线：消費 revoke_others_of_user primitive＋發 session_event(revoked)＋denylist(kicked/revoked)；006 只出 primitive、觸發端點遞延（併 B-029 改密撤 session）｜使用者管理刀｜出處：006 FR-008
- B-065｜denylist 逐出/命中監控＋enforce PG-fallback 負載觀測（每受保護請求一次 ttl_from_settings SELECT、admin 規模可接受）｜obs 刀｜出處：006 U4/final review minor
- B-067｜session_event 膨脹治理：reuse 同票重放逐次累積稽核列（006 SC-009 只列 sys_token 回收、未列 session_event；曝險有界於 refresh JWT exp、無安全風險）｜obs 刀｜出處：006 final review minor
- B-069｜alova 棧接入真實 auth 時：補 idle toast 副本＋修 onError raw msg 未 $t（現 demo-only dormant、ADR 0035/0036 觸發再議＝alova 接入真實 auth）｜前端/alova 刀｜出處：006 U11/ADR 0035-0036
- B-072｜refreshToken/logout 端點零節流：007 app 層節流（鍵＝帳號名）只掛 login，nginx auth_limit 兩塊 exact-match 亦僅蓋 /api/auth/login＋/api/auth/loginCaptcha；refreshToken/logout 為 Public 且帶 DB 寫路徑（rotation 插列／revoke family），暴力灌打僅受一般容量約束｜auth family 防護延伸或 obs 刀｜出處：007 U12 收刀盤點
- B-073｜sys_login_attempt.region 地理解析恆空：005 建欄、007 facade insert 仍 Set(None)（IP 最小版、無 GeoIP 基建）；去處＝IP 閘刀併真實 IP 還原後接 GeoIP、或屆時拍板廢欄｜IP/ingress 刀（併 B-019/B-024）｜出處：007 U4 as-built
- B-074｜軟區決策負快取：軟區缺-captcha 熱路徑永不計數故永不被 L1 短路，每發 1×unlock marker 讀＋1×settings 三鍵＋1×L2 count（成本誠實記載＝ADR 0038「軟區為未被負快取隔離的熱路徑」節；仍比 argon2 主宰的正常登入便宜）｜登入端點負載量測顯示成問題時｜出處：ADR 0038
- B-075｜captcha 強化包：產圖對抗性（干擾強度/字型多樣）＋UX 觀察兩則——①pwd-login watch userName 每鍵擊觸發 fetchLoginCaptcha、可 debounce；②「碼對密錯」（captcha 相符、密碼錯）該題已提交即消耗、前端不主動換題 ⇒ 下一發必 captchaRequired 多一輪往返｜captcha 對抗性或 UX 痛點實際出現時｜出處：007 U5/U6 觀察
- B-076｜schema-gate 白名單整批重凍退路：ADR 0039 建立 STRUCT/SEED additive 白名單範式（只放寬新增），白名單隨刀累積會稀釋「凍結基準」語意；需保留「重擷取 fixtures 整批重凍＋清空白名單」退路（基準改動、拍板級）｜白名單膨脹或下次大 schema 刀｜出處：ADR 0039／007 U3
- B-077｜unlock op-log 持久化強化：unlockLogin 動作序＝SET marker→DEL lock→op-log insert（Redis 兩步成功後 best-effort、失敗僅告警不回滾）⇒ 管理動作可能零審計列；候選＝失敗重試/事後補記/回報 caller｜審計功能刀｜出處：007 U7／data-model §5.4
- B-078｜既有 flaky：handler::auth::tests::refresh_valid_super_returns_new_pair_public 的 ±5s 時鐘容差於全量並行（argon2 吃滿 CPU）下偶發超窗、單跑綠；候選解＝放寬容差或降時間敏感度｜再度復發或 rust 測試整備刀｜出處：007 U2 發現
- B-079｜dev 反代拓樸修正（拍板 2026-07-10＝「同源 /api＋proxy 直指 rust-api」）：瀏覽器面 baseURL 改同源相對
  /api（serve/build 同值）＋vite proxy 改 key `^/api(/|$)`、target http://rust-api:8080（rewrite strip /api、
  鏡射 nginx strip）＋.env.prod 同批改 /api 拆 apifox mock 地雷。已驗證前提＝L-125（雙穿迴圈＋env 雙重身分）／
  L-126（loopback publish 常數桶——本修正不解 dev per-IP 常數桶；效益＝:42080 單跳 prod 同形＋XFF 一元素＋
  build:test 修復＋429 可瀏覽器驗）；:42080 之 /api/* 被 nginx location 先攔不達 vite（容器內 vite 8.0.12
  urlJoin 實碼驗證）、rust-api 路由不帶 /api 前綴且只聽 8080（容器內探針實測）。實作面＝service.ts
  createProxyPattern＋proxy.ts target 推導解耦（兩檔皆該檔首筆修改型 fork-delta；target 來源新 env key 或寫死
  屆時定、含 vite-env.d.ts 新增型）＋.env.test/.env.prod 修改型；是否登記新★軌道屆時拍。附帶已拍＝:42081 成
  零限流直達（與 :42079 同級、非新威脅面）記入活書 dev 曝露、活書 §7 分桶語意按新拓樸重寫（落收刀簿記
  commit、L-124）、勘誤點＝L-111 終局／L-122①／L-125 結案註記／NOTES CDP 三坑句、429/T084 型驗收此後必打
  :42080。遺留＝對外 0.0.0.0 publish 之 DNAT 是否保留外部來源 IP 未實測（決定 FR-017 prod 粗閘與否、需外部
  機器或改 publish 形實測）｜IP 閘刀（B-019/B-024）前置清理批次｜出處：2026-07-10 反代拓樸偵察＋user 拍板
