<!-- next: B-112 -->
# BACKLOG — 待辦

條目格式 `- B-NNN｜<一句話>｜<觸發條件或期限（選）>`；配號取檔頭 next-id 後 bump、號碼永不回收；完成即刪列、git 即史。

- B-011｜儀表板做不做／怎麼做（傾向 v1＝固定版面零新表）｜入波排程時｜出處：rev3:DECISIONS§1-待決⑥a（K1-06）
- B-012｜報表匯出 PDF/CSV（傾向 v1＝同步匯出零新表）｜入波排程時｜出處：rev3:DECISIONS§1-待決⑥b（K1-07）
- B-013｜靜態資料加密（傾向磁碟／tablespace 層）｜prod 部署定稿前必拍｜出處：rev3:DECISIONS§1-待決⑥c（K1-08）
- B-014｜合規姿態升級（傾向維持現姿態）｜對外開放／多租戶需求時｜出處：rev3:DECISIONS§1-待決⑥d（K1-09）
- B-015｜設定熱讀推廣 keyed map（單鍵 swap 夠用）｜swap 不敷用時｜出處：rev3:DECISIONS§1-⚠️l（K1-21）
- B-018｜帳號級鎖定被第三方惡意鎖人的 DoS 面重估（漸進延遲/CAPTCHA）（★部分消化 2026-07-10：007 三層緩解已落＝captcha 軟區抬自動化成本＋unlockLogin 手動解鎖＋鎖存續≤window 自解〔③零稽核列、sticky 續鎖構造上不可能〕；殘餘＝漸進延遲未做、第三方觸鎖本身仍可達成——per-user 節流結構性如此；★2026-07-11 008 IP 閘：IP 白名單跳節流〔U11〕落地＝第三方觸鎖徹底緩解手段之一，per-user 結構性殘餘不變）｜節流延伸或 IP 閘刀｜出處：rev3:REVIEW§6（K2-02）
- B-026｜部分更新契約內建顯式 clear 語意｜部分更新 wire 設計時（★2026-07-14 011 部分兌現：字串欄 Some("")=清空已落 user 域〔FR-007〕；非字串欄〔user_gender〕清空機制明文不引入；殘餘＝通用顯式 clear wire 設計）｜出處：rev3:REVIEW§3.4（K2-10）
- B-027｜alt-login 補全知識包（確認密碼規則值快照 race 的 toRef 範式等）（註 2026-07-10：007 captcha 底座〔無狀態簽題＋提交即消耗〕可複用；★alt-login 端點的節流 seam 不自動涵蓋——throttle 判定序只掛 login，屆時需自行接）｜B-008 拍板後施工輸入｜出處：rev3:CHECKLIST§4.2（K2-11）
- B-028｜手機/信箱真實驗證＋驗證碼改密（與 alt-login 共享 captcha 基建、宜同刀或緊接）（註 2026-07-10：007 captcha 底座可複用——loginCaptcha 端點形＋無狀態簽題直接搬）｜user-center/auth 波排程｜出處：rev3:CHECKLIST§4.2（K2-12）
- B-036｜列表排序 per-column 索引評估＋三端白名單單一來源或 parity 檢查｜列表排序刀｜出處：rev3:CHECKLIST§4.2（K2-20）
- B-037｜prod TLS/信任拓樸落地組做成部署 checklist＋自動化驗收（★2026-07-11 008 final review #1 加：CDN origin 防火牆鎖定〔僅受 CDN 邊緣連線／Authenticated Origin Pulls〕＝Tier-1 位置錨承重前提、與 DNAT 同級）｜prod 部署刀｜出處：rev3:CHECKLIST§4.2＋§3.E（K2-21）
- B-038｜prod 多副本橫向擴展拓樸留位（LB＋共用 DB/Redis）｜含水平擴展目標時｜出處：rev3:CHECKLIST§4.2（K2-22）；instance 維已由 016 留位（rust 不自造 instance label、面板 query 不硬編碼單值＝FR-017）
- B-042｜prod nginx 完整資源 CSP 收緊內建部署驗收｜prod 部署刀｜出處：rev3:CHECKLIST§3.J（K2-27）
- B-045｜低位殘項 checklist（XFF 空 token/計數 race/migration down 非對稱/CDN 錨；trace_id 控制字元子項已由 016 sanitize 單一 seam 收單）｜重寫對應模組時逐項內建｜出處：rev3:CHECKLIST§3.J（K2-30）
- B-069｜alova 棧接入真實 auth 時：補 idle toast 副本＋修 onError raw msg 未 $t（現 demo-only dormant、ADR 0035/0036 觸發再議＝alova 接入真實 auth）｜前端/alova 刀｜出處：006 U11/ADR 0035-0036
- B-074｜軟區決策負快取本體：軟區缺-captcha 熱路徑永不計數故永不被 L1 短路，每發 1×unlock marker 讀＋1×settings 三鍵＋1×L2 count（成本誠實記載＝ADR 0038「軟區為未被負快取隔離的熱路徑」節；仍比 argon2 主宰的正常登入便宜；016 已落 throttle_soft_zone_total 命中量測、負載證據面板可查）｜量測顯示成問題時｜出處：ADR 0038
- B-075｜captcha 強化包：產圖對抗性（干擾強度/字型多樣）＋UX 觀察——「碼對密錯」（captcha 相符、密碼錯）該題已提交即消耗、前端不主動換題 ⇒ 下一發必 captchaRequired 多一輪往返｜captcha 對抗性或 UX 痛點實際出現時｜出處：007 U5/U6 觀察
- B-076｜schema-gate 白名單整批重凍退路：ADR 0039 建立 STRUCT/SEED additive 白名單範式（只放寬新增），白名單隨刀累積會稀釋「凍結基準」語意；需保留「重擷取 fixtures 整批重凍＋清空白名單」退路（基準改動、拍板級）｜白名單膨脹或下次大 schema 刀｜出處：ADR 0039／007 U3
- B-080｜CDN 錨碼層硬化：Tier-1 CDN 位置錨僅檢查「最右 CDN 段」、不檢查該 CDN 由傳輸層背書，origin 對外裸露時可偽造 XFF 注入公開 CDN 邊緣 IP 當錨繞過閘（final review #1、ADR 0043）；候選＝Tier-1 錨要求「錨右鄰起全受信基建」；★留獨立後續刀（避免誤傷合法多層 CDN/LB 拓樸）｜ingress 硬化刀｜出處：008 final holistic review #1
- B-081｜prod Dockerfile xdb 資料檔 COPY：xdb/resources/ip2region.xdb 已 git-tracked，但現僅 dev stage、prod 多階段建置需 COPY 進映像＋設 XDB_FILEPATH（否則 prod xdb_ready=false、region 恆空）｜prod 多階段建置刀｜出處：008 U12 as-built（L-083/L-084）
- B-083｜寫端授權下放前置複合條目（M-6 no-escalation 授權上限檢查＋seeded 護欄複評＋明細通道受眾邊界重評）——任何「寫端授權下放非 super」或「role CRUD 政策列下放非 super」之前 MUST 先建：①非超管寫端「不得授出超過自身所有」上限檢查（FR-045、本刀結構上不可達故未建）；②seeded 受保護護欄與「超管恆禁停用」結構護欄複評（FR-015／FR-018）；③明細通道受眾邊界重評（FR-035／ADR 0050——明細「自查等價」前提隨受眾改變即失效）｜寫端授權下放刀｜出處：009 FR-035/FR-045／ADR 0050
- B-094｜未刪選單列表分頁裝飾性、>100 頂層將靜默截斷｜選單規模成長時（出處：REVIEW-001-010 F010-1）
- B-099｜契約測試（contract.rs registry cases）對 request query 形零判別力——case 僅斷 registry 完整性＋保護碼、query 不解析且 DTO 無 deny_unknown_fields；query 契約防護實由 DB-backed endpoint 測試承載（013 U8 拆除實驗證偽 quickstart 原宣稱、已勘誤）；若未來需契約層把關 query 形→另立掃源/樣本裁判｜下次動 contract.rs 架構或新增 query 契約時
- B-100｜系統軟刪掃描通用刀：島 H2 之通用正確性——各軟刪路徑（選單/角色/使用者…）下 casbin 碼與 sys_menu.buttons 聯集的歸檔一致性全面掃描（013 D8 明文 decouple、ADR 0064「不做」節）｜未來排程（入波時拍範圍）｜出處：013 spec D8＋ADR 0063/0064；016 reaper bin 已留 --job 擴充位可承載未來掃描 job
- B-101｜casbin 按鈕碼與 sys_menu.buttons 聯集漂移追蹤：m008 user 四碼（reset-pwd/kick/restore/unlock）中 buttons 欄未同步回填之 011 缺口＋013 ip-rule 四碼已同步——兩源（casbin 政策 vs buttons 面板候選）無機器一致性檢查、會靜默漂移｜下次動按鈕碼 seed 或角色頁按鈕面板時｜出處：013 tasks T033＋ADR 0063
- B-102｜changePassword 舊密暴力試節流（攻擊前提＝已劫持 session、舊密 gate 即既有防線＝風險有限；007/008 throttle 狀態機綁死 login 流程〔sys_login_attempt 計數＋captcha gate〕不可直掛、需另做 per-user 節流 seam）｜auth 安全補強刀或與 B-027/B-028 同刀｜出處：014 spec 設計取捨（自拍 9、2026-07-17）
- B-107｜備份自動化：pg_dump 排程＋卷快照＋還原演練（現況零工具、僅手動命令形＝RUNBOOK §6；secrets 檔與 postgres_data 卷配對備份一併納入）｜資料價值升高或 prod 部署刀前｜出處：RUNBOOK 落地盤點（2026-07-19）
- B-109｜rust-api 編譯迴圈量測與 dev profile 評估刀：容器內 cargo build --timings 建基線（macOS＋WSL2 各冷編＋單檔增量一輪；動機＝L-004 冷編約 240s〔rev3 數據、絕對值以重測為準〕＋macOS link 峰值 OOM 實載＋serial TDD 每輪 fix 付一次增量 build），數據支持才加 profile.dev debuginfo 裁剪（line-tables-only＋依賴 debug=false 兩行、可逆、不動 release 重現性）；linker（mold/lld）與映像變更排除在預設範圍、須量測證明 macOS link 段為主要瓶頸後另拍板並連動 L-005 雙機清卷；Cranelift（nightly-only、與 stable 1.96.1 釘版衝突）與 subsecond（實驗性＋需引入 dx 工具鏈；經查可 hot-patch 任意 Rust 專案含 axum、排除理由勿寫「純前端」）排除據實簿記｜下次 rust-api 施工波起手順跑，或增量編譯體感惡化／healthcheck start_period 120s 被突破（up --wait 假失敗形）時｜出處：JetBrains Rust Web 2026 文章研究輪 m07 裁決 partial（2026-07-21）
- B-110｜sea-orm Entity First 評估刀：sea-orm 2.x 沉澱後評估「entity 對實庫僅驗不生成的漂移檢查＋additive DDL 草稿生成輔助」（動機＝entity 與 migration 同一 schema 事實雙手寫、現無機器互驗——m001 gate1 抓漏 2 索引為既遂案例、型別手滑僅 runtime 炸開；草稿可省未來新表 toil）；邊界＝產物入庫人審過三閘、raw SQL 逃生門與 up/down 對稱不動、casbin_rule 入 skip-list（ADR 0015）、欄序仍 user 定稿（ADR 0021）、絕不開 runtime schema-sync｜sea-orm 2.x 數個 patch 版沉澱＋vendored sea-orm-adapter 2.0 相容路徑 ADR 拍板、或 1.1 維護窗關閉、或單一 feature 內出現兩支以上新表 DDL（高頻建表期——此況可先做零升級的草稿工具階段 0、無人用即停損）｜出處：JetBrains Rust Web 2026 文章研究輪 m03 裁決 defer（2026-07-21）
- B-111｜tools/ 四支 python 工具補 .py 副檔名（docs-sync／schema-gate／fork-delta-lint／wire-schema；bootstrap／wf-watchdog 屬 bash 不在範圍；候選 A＝直接改名＋僅更新活引用〔.githooks／.claude hooks／CLAUDE.md／README／RUNBOOK／NOTES／memory；歷史 specs／brainstorms／reviews 屬過去式不改〕、候選 B＝原名留薄殼轉發＋本體改 .py 零引用更新；引用面實測 323 處散佈約 100 檔、多數屬歷史檔；改名後 drvfs exec bit 用 git update-index --chmod=+x 落索引）｜下次動 tools/ 任一支時同刀、或獨立小刀｜出處：user 指示（2026-07-28）
