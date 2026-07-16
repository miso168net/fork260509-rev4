<!-- next: B-098 -->
# BACKLOG — 待辦

條目格式 `- B-NNN｜<一句話>｜<觸發條件或期限（選）>`；配號取檔頭 next-id 後 bump、號碼永不回收；完成即刪列、git 即史。

- B-007｜觀測側 msg 可讀性補強候選（log 附 key→預設語言譯文、或維運字典對照表；ADR 0001 第 8 題配套）｜obs 層刀或維運痛點實際出現時
- B-011｜儀表板做不做／怎麼做（傾向 v1＝固定版面零新表）｜入波排程時｜出處：rev3:DECISIONS§1-待決⑥a（K1-06）
- B-012｜報表匯出 PDF/CSV（傾向 v1＝同步匯出零新表）｜入波排程時｜出處：rev3:DECISIONS§1-待決⑥b（K1-07）
- B-013｜靜態資料加密（傾向磁碟／tablespace 層）｜prod 部署定稿前必拍｜出處：rev3:DECISIONS§1-待決⑥c（K1-08）
- B-014｜合規姿態升級（傾向維持現姿態）｜對外開放／多租戶需求時｜出處：rev3:DECISIONS§1-待決⑥d（K1-09）
- B-015｜設定熱讀推廣 keyed map（單鍵 swap 夠用）｜swap 不敷用時｜出處：rev3:DECISIONS§1-⚠️l（K1-21）
- B-016｜稽核 log retention 政策（v1 只容量監控）｜容量警示時｜出處：rev3:DECISIONS§1-⚠️n（K1-23）
- B-018｜帳號級鎖定被第三方惡意鎖人的 DoS 面重估（漸進延遲/CAPTCHA）（★部分消化 2026-07-10：007 三層緩解已落＝captcha 軟區抬自動化成本＋unlockLogin 手動解鎖＋鎖存續≤window 自解〔③零稽核列、sticky 續鎖構造上不可能〕；殘餘＝漸進延遲未做、第三方觸鎖本身仍可達成——per-user 節流結構性如此；★2026-07-11 008 IP 閘：IP 白名單跳節流〔U11〕落地＝第三方觸鎖徹底緩解手段之一，per-user 結構性殘餘不變）｜節流延伸或 IP 閘刀｜出處：rev3:REVIEW§6（K2-02）
- B-026｜部分更新契約內建顯式 clear 語意｜部分更新 wire 設計時（★2026-07-14 011 部分兌現：字串欄 Some("")=清空已落 user 域〔FR-007〕；非字串欄〔user_gender〕清空機制明文不引入；殘餘＝通用顯式 clear wire 設計）｜出處：rev3:REVIEW§3.4（K2-10）
- B-027｜alt-login 補全知識包（確認密碼規則值快照 race 的 toRef 範式等）（註 2026-07-10：007 captcha 底座〔無狀態簽題＋提交即消耗〕可複用；★alt-login 端點的節流 seam 不自動涵蓋——throttle 判定序只掛 login，屆時需自行接）｜B-008 拍板後施工輸入｜出處：rev3:CHECKLIST§4.2（K2-11）
- B-028｜手機/信箱真實驗證＋驗證碼改密（與 alt-login 共享 captcha 基建、宜同刀或緊接）（註 2026-07-10：007 captcha 底座可複用——loginCaptcha 端點形＋無狀態簽題直接搬）｜user-center/auth 波排程｜出處：rev3:CHECKLIST§4.2（K2-12）
- B-030｜新帳號初始密碼政策化（隨機生成＋首登強制改密）｜★自助改密（B-090）落地後（2026-07-14 011 已做 admin 指定初始密碼＋政策驗證、ADR 0055 拆階段；殘餘＝隨機生成＋首登強制改密〔需 sys_user 加欄＋login 插閘＋強制改密頁〕）｜出處：rev3:CHECKLIST§4.2＋REVIEW§3.3-F-7（K2-14）
- B-031｜obs 告警通知投遞 channel 最小一條納首發｜觀測層刀｜出處：rev3:CHECKLIST§4.2（K2-15）
- B-033｜節流快取遞延組（壓制告警/廣度估計/TTL 拆分）＋誤鎖緩解優先級提前（★部分消化 2026-07-10：007 已落壓制麵包屑結構化告警＋unlockLogin 誤鎖緩解；殘餘＝grafana 告警規則＋HLL 廣度估計＋IP 維 TTL 拆分）｜obs 刀（grafana/HLL）＋IP 閘刀（TTL 拆分）｜出處：rev3:CHECKLIST§4.2＋§3.H（K2-17）
- B-036｜列表排序 per-column 索引評估＋三端白名單單一來源或 parity 檢查｜列表排序刀｜出處：rev3:CHECKLIST§4.2（K2-20）
- B-037｜prod TLS/信任拓樸落地組做成部署 checklist＋自動化驗收（★2026-07-11 008 final review #1 加：CDN origin 防火牆鎖定〔僅受 CDN 邊緣連線／Authenticated Origin Pulls〕＝Tier-1 位置錨承重前提、與 DNAT 同級）｜prod 部署刀｜出處：rev3:CHECKLIST§4.2＋§3.E（K2-21）
- B-038｜prod 多副本橫向擴展拓樸留位（LB＋共用 DB/Redis）｜含水平擴展目標時｜出處：rev3:CHECKLIST§4.2（K2-22）
- B-040｜cleanup sidecar 最小權限 DB 憑證（背景 job secret 最小權限＝預設）｜首個背景 job 設計期｜出處：rev3:CHECKLIST§3.A（K2-25）
- B-041｜obs 採集容器非-root 硬化起手照配（docker.sock 窄化）｜觀測層刀起手｜出處：rev3:CHECKLIST§3.A（K2-26）
- B-042｜prod nginx 完整資源 CSP 收緊內建部署驗收｜prod 部署刀｜出處：rev3:CHECKLIST§3.J（K2-27）
- B-045｜低位殘項 checklist（trace_id 控制字元/XFF 空 token/計數 race/migration down 非對稱/CDN 錨）｜重寫對應模組時逐項內建｜出處：rev3:CHECKLIST§3.J（K2-30）
- B-053｜obs 面板與 metrics 慣例（docker 友善板/計數器 pre-register/pushgateway 持久卷）｜觀測層刀起手｜出處：rev3:CHECKLIST§3.I（K2-38）
- B-054｜completion log 噪音治理（預留 path 級過濾開關）｜request log 設計時｜出處：rev3:CHECKLIST§3.I（K2-39）
- B-059｜settings 頁 tooltip 顯示的 description＝DB seed 繁體名（7/8 與 i18n label 同文、zh-CN/en 下腳本不符、tooltip 冗餘）→ enrich 成真正 localized 說明（偵察 2026-07-10 薦案 a＝tooltip 改 $t help 鍵、seed description 留 DB 作 fallback、零 migration；005 遺漏 session_idle_timeout 的 label 鍵〔三語 UI 直顯 seed 繁體〕宜同刀補；★007 已落 login_throttle_* 三鍵、同檔 index.vue labelKeyMap＋三語 locale 已動——先後次序顧慮已解、enrich 屆時直接改）｜enrich settings 說明的刀｜出處：004 單元⑧ user 拍板 B（保留＋BACKLOG）
- B-060｜demo 選單清理：002 casbin menu seed 給 R_SUPER 全 soybean template demo（about/document/plugin/alova/pro-naive/multi-menu/function）menu policy，rev4 真選單應只 home/manage/user-center｜動 002 casbin/sys_menu seed（新 migration；偵察 2026-07-10：demo＝67 menu＋77 casbin 列、keep＝11〔含 B-061 三未建頁項不動〕；casbin_rule 無 deleted_at→policy 硬刪不可避、gate2 缺列紅需 SEED_REMOVAL_ALLOWLIST＋新 ADR〔0032 只放寬新增〕；拍板點＝sys_menu hard vs 軟刪／exception 樹入否；受影響測試＝sys_menu facade list_active 計數＋route handler R_USER_COMMON 正向斷言）（★2026-07-13 010 拍板不折入；★2026-07-14 011 拍板 user 寫端全 super-only、R_ADMIN user:edit 有鈕無權不對稱留置＝誠實 5003 拒因、隨本項 demo 清理一併處理〔D1 親決、FR-004〕）｜出處：005 CDP item#2 拍板 2026-07-06
- B-061｜manage_ip-rule 子項 i18n：已 002 seed 選單項但 locale 三語無 route.manage_ip-rule 譯文→dynamic 選單顯 raw key（未建頁、前端無 route/view→點擊 404）｜ip-rule 頁刀建時補譯文（★route locale 鍵無「獨立新增」授權、須隨建頁走 MODAL-WIRING(e)＝憲法 §III.2；004 manage_system-settings 即此範式）｜出處：005 CDP item#2 拍板 2026-07-06（★2026-07-15 012 已兌現 manage_audit 項＝隨稽核中心建頁補三語 route locale〔U9〕、殘餘 ip-rule 一項續待）
- B-063｜孤兒/背景 reaper：sys_token 跨 session 孤兒＋rotated 過期列完整回收（006 refresh-time prune_expired_rotated 已止血同 chain；跨 session/背景批次遞延）｜obs/維運刀｜出處：006 R6/SC-009
- B-065｜denylist 逐出/命中監控＋enforce PG-fallback 負載觀測（每受保護請求一次 ttl_from_settings SELECT、admin 規模可接受）｜obs 刀｜出處：006 U4/final review minor
- B-067｜session_event 膨脹治理：reuse 同票重放逐次累積稽核列（006 SC-009 只列 sys_token 回收、未列 session_event；曝險有界於 refresh JWT exp、無安全風險）｜obs 刀｜出處：006 final review minor
- B-069｜alova 棧接入真實 auth 時：補 idle toast 副本＋修 onError raw msg 未 $t（現 demo-only dormant、ADR 0035/0036 觸發再議＝alova 接入真實 auth）｜前端/alova 刀｜出處：006 U11/ADR 0035-0036
- B-074｜軟區決策負快取：軟區缺-captcha 熱路徑永不計數故永不被 L1 短路，每發 1×unlock marker 讀＋1×settings 三鍵＋1×L2 count（成本誠實記載＝ADR 0038「軟區為未被負快取隔離的熱路徑」節；仍比 argon2 主宰的正常登入便宜）｜登入端點負載量測顯示成問題時｜出處：ADR 0038
- B-075｜captcha 強化包：產圖對抗性（干擾強度/字型多樣）＋UX 觀察——「碼對密錯」（captcha 相符、密碼錯）該題已提交即消耗、前端不主動換題 ⇒ 下一發必 captchaRequired 多一輪往返｜captcha 對抗性或 UX 痛點實際出現時｜出處：007 U5/U6 觀察
- B-076｜schema-gate 白名單整批重凍退路：ADR 0039 建立 STRUCT/SEED additive 白名單範式（只放寬新增），白名單隨刀累積會稀釋「凍結基準」語意；需保留「重擷取 fixtures 整批重凍＋清空白名單」退路（基準改動、拍板級）｜白名單膨脹或下次大 schema 刀｜出處：ADR 0039／007 U3
- B-080｜CDN 錨碼層硬化：Tier-1 CDN 位置錨僅檢查「最右 CDN 段」、不檢查該 CDN 由傳輸層背書，origin 對外裸露時可偽造 XFF 注入公開 CDN 邊緣 IP 當錨繞過閘（final review #1、ADR 0043）；候選＝Tier-1 錨要求「錨右鄰起全受信基建」；★留獨立後續刀（避免誤傷合法多層 CDN/LB 拓樸）｜ingress 硬化刀｜出處：008 final holistic review #1
- B-081｜prod Dockerfile xdb 資料檔 COPY：xdb/resources/ip2region.xdb 已 git-tracked，但現僅 dev stage、prod 多階段建置需 COPY 進映像＋設 XDB_FILEPATH（否則 prod xdb_ready=false、region 恆空）｜prod 多階段建置刀｜出處：008 U12 as-built（L-083/L-084）- B-083｜寫端授權下放前置複合條目（M-6 no-escalation 授權上限檢查＋seeded 護欄複評＋明細通道受眾邊界重評）——任何「寫端授權下放非 super」或「role CRUD 政策列下放非 super」之前 MUST 先建：①非超管寫端「不得授出超過自身所有」上限檢查（FR-045、本刀結構上不可達故未建）；②seeded 受保護護欄與「超管恆禁停用」結構護欄複評（FR-015／FR-018）；③明細通道受眾邊界重評（FR-035／ADR 0050——明細「自查等價」前提隨受眾改變即失效）｜寫端授權下放刀｜出處：009 FR-035/FR-045／ADR 0050
- B-085｜ADR 0050 protectedRevoke 命名 as-built 漂移：ADR 0050 line 20 字面列命名空間為 `biz.policy.protectedRevoke`，as-built（rust-api handler role.rs／契約表／base-web 三語 locale）一律用 `biz.role.protectedRevoke`（distinct key 一因一鍵、與其餘 biz.role.* 拒因同命名空間）——★文檔漂移、實作正確（ADR accepted body 不可變、不回灌）；翻案／再動明細通道 key 命名時 MUST 立新 ADR 校正字面｜明細通道再設計或 ADR 0050 翻案觸發時｜出處：009 U16 收刀 as-built 核對
- B-086｜restorePolicy menu 維孤兒檢查用 list_active vs 治理域一致性：sys_casbin_archive.rs restore_archived 判標的選單存在以 list_active（顯示域），停用選單（status=2、未刪、屬治理域）之歸檔授權復原會誤判 NotRestorable、與 010 FR-019「治理域＝未刪含停用、停用≠撤銷」有張力；010 R2 明列且僅列四治理讀端換源點、restorePolicy 非其一、屬 U8/009 授權回收桶路徑，010 正確 surgical 未動｜授權回收桶再設計或 restore 停用選單語義釐清時｜出處：010 U10 spec/quality review minor- B-090｜使用者自助改密（user-center、驗舊密改密；B-030 隨機生成＋首登強制改密之前置依賴）｜user-center 刀或需求觸發（出處：011 clarification user 親決＋ADR 0055）
- B-092｜update_setting 忽略 update_by_key Option＝TOCTOU 誤報成功（現不可達、加刪除端點即現形）——防禦性小修｜設定域擴充時（出處：REVIEW-001-010 F004-1）
- B-094｜未刪選單列表分頁裝飾性、>100 頂層將靜默截斷｜選單規模成長時（出處：REVIEW-001-010 F010-1）- B-096｜稽核中心四 search 卡 daterange 邏輯逐字重複×4（audit-search-{operation,access,login,session}.vue 各約 25 行 dateRange ref＋applyDateRange＋defaultModel/resetModel/search 純函式段）——提煉輕量 composable（建議形 useAuditSearchDateRange(model, emit)）｜下次觸及稽核 search 卡時（出處：012 final review code-quality 觀察 1）
- B-097｜「共享表絕對計數／併發狀態」flaky 家族殘餘二例（013-pre B-087 sweep 全量跑掃出、非原三例）：①`handler::audit::purge_oplog_water_line_writes_self_audit`（audit.rs：deletedCount ≥ 自種 2 得 0＝purge 水平線自種舊列被平行測 purge/計數擾動）②`handler::auth::throttle_no_false_lock_on_concurrent_success_and_failure`（併發失敗把帳號推進 captcha 軟區→again 登入得 captchaRequired 非放行）——同 B-087 家族、修法候選 delta 斷言／序列化／軟區狀態隔離｜該假紅再現或下次動對應測時（出處：013-pre test-hygiene sweep 全量跑掃出）
