# BACKLOG-DEFERRED — 滯後卷

條目格式同主檔 BACKLOG.md；本卷收 user 拍板滯後的待辦——不排入 NOTES 近期 roadmap、STATE 分開
計數（滯後≠完成、lint 視為仍開放）。配號永遠只在主檔（本卷無 next-id）；移入／移回＝整行搬＋
滯後戳記；完成＝照舊刪列＋事件 backlog_done；各條目觸發欄寫回收時點。

- B-060｜demo 選單清理：002 casbin menu seed 給 R_SUPER 全 soybean template demo（about/document/plugin/alova/pro-naive/multi-menu/function）menu policy，rev4 真選單應只 home/manage/user-center｜動 002 casbin/sys_menu seed（新 migration；偵察 2026-07-10：demo＝67 menu＋77 casbin 列、keep＝11〔含 B-061 三未建頁項不動〕；casbin_rule 無 deleted_at→policy 硬刪不可避、gate2 缺列紅需 SEED_REMOVAL_ALLOWLIST＋新 ADR〔0032 只放寬新增〕；拍板點＝sys_menu hard vs 軟刪／exception 樹入否；受影響測試＝sys_menu facade list_active 計數＋route handler R_USER_COMMON 正向斷言）（★2026-07-13 010 拍板不折入；★2026-07-14 011 拍板 user 寫端全 super-only、R_ADMIN user:edit 有鈕無權不對稱留置＝誠實 5003 拒因、隨本項 demo 清理一併處理〔D1 親決、FR-004〕）｜出處：005 CDP item#2 拍板 2026-07-06｜★滯後 2026-07-19 user 拍板：正式 release 前清理批；屆時動工仍先重偵察——keep 前提已因 013 建頁漂移、本行 keep＝11 為 2026-07-10 快照勿當現況＋順路收 B-101／裁 B-094（原 NOTES 方案）
- B-103｜user-center email/phone 雙卡同構重複（各約 85 行、僅差欄名／title 鍵／pattern rule 四處字面）——提煉共用 ContactCard 候選（rev3 藍本本即雙卡、012 B-096 同構容忍先例、收刀不強修）｜下次觸及 user-center 卡片時｜出處：014 final review 品質鏡頭建議 1（2026-07-17）｜★滯後 2026-07-19 user 拍板：正式 release 前清理批；若 auth 組 B-028 先觸及 user-center 可順路提前收回
- B-132｜app shell 頁首 320px 窄屏橫向溢出：documentElement scrollWidth 349 vs clientWidth 320——元凶＝頁首右側工具列（含一顆 107px 按鈕）、與任何卡片/浮窗無關（U10 verifier 以浮窗未開基線對照量測證實既存）｜行動裝置支援或版面調整刀｜出處：020 U10 verifier 320px 實測（2026-08-01）｜★滯後 2026-08-01 user 拍板移滯後；回收時點＝行動裝置支援或頁首版面調整刀（元凶屬上游 layout 工具列、修改型 inline 負擔高）
