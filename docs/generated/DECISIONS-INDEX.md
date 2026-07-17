<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# DECISIONS-INDEX — ADR 索引

| id | status | date | title | feature | supersedes | superseded_by |
|---|---|---|---|---|---|---|
| 0001 | accepted | 2026-07-03 | constitution v1.0 重鑄——B6 逐筆過目拍板（17 題） | — | — | — |
| 0002 | accepted | 2026-07-03 | datetime 地基慣例——UTC 存、offset 傳、單點顯示 | — | — | — |
| 0003 | accepted | 2026-07-03 | i18n 地基——zh-TW 為 primary locale、對等 lint 守門 | — | — | — |
| 0004 | accepted | 2026-07-03 | 錯誤碼系統執行面——碼表 table-driven 守門 | — | — | — |
| 0005 | accepted | 2026-07-03 | 審計欄 archetype 執行面——migration 檢查與往返驗證守門 | — | — | — |
| 0006 | accepted | 2026-07-03 | soft-delete 慣例——成對寫入、讀端過濾、partial-uniq | — | — | — |
| 0007 | accepted | 2026-07-03 | 後端路由單檔逐條寫＋端點覆蓋 lint 鎖三源一致 | — | — | — |
| 0008 | accepted | 2026-07-03 | 縱切第一刀選最輕的系統設定打樣整條管線 | — | — | — |
| 0009 | accepted | 2026-07-03 | 選擇性外鍵——純關聯硬刪表加 FK、軟刪語意表零 FK | — | — | — |
| 0010 | accepted | 2026-07-03 | 效能與可用性目標——保守 p95 組＋99.5% 月可用 | — | — | — |
| 0011 | accepted | 2026-07-03 | 稽核三表補查詢讀端＋僅超管管理 UI、殿後排程 | — | — | — |
| 0012 | accepted | 2026-07-03 | redis 映像建 stack 即 pin 數字版 | — | — | — |
| 0013 | accepted | 2026-07-03 | migration 檔名採短編號＋語意名 | — | — | — |
| 0014 | superseded | 2026-07-03 | schema 基線＝rev3 終態語意 squash＋欄序重設計、兩道閘驗證 | — | — | 0021 |
| 0015 | accepted | 2026-07-03 | casbin 規則表採委派式建表（adapter 建基底＋同檔 ALTER 補治理欄） | — | — | — |
| 0016 | superseded | 2026-07-03 | 已生效鎖定加 Redis 負快取層（DB 真相、fail-OPEN） | — | — | 0038 |
| 0017 | superseded | 2026-07-03 | IP 存取控制閘——白＞黑＞default-allow、DB 真相＋記憶體微秒判定、fail-OPEN | — | — | 0043 |
| 0018 | accepted | 2026-07-03 | B8 處置流水總帳——K1 27 筆去向＋K2 全量轉 BACKLOG | — | — | — |
| 0019 | accepted | 2026-07-03 | rev4 port 配號——host 4xxxx、容器內回歸預設值 | — | — | — |
| 0020 | accepted | 2026-07-03 | 波 0 規劃定案——三刀組成串行、compose 五服務、部署資產裁剪帶入、wire 後端縱深 | — | — | — |
| 0021 | accepted | 2026-07-03 | schema 基線改 user 定稿制——欄序親排＋seed 過目定稿、兩道閘分工對應調整 | — | 0014 | — |
| 0022 | accepted | 2026-07-03 | 部署腳本輔助映像沿 latest——FR-013 釘版義務的邊界豁免 | — | — | — |
| 0023 | accepted | 2026-07-04 | casbin 授權政策 seed 移入基線——連動一致性優先 | — | — | — |
| 0024 | accepted | 2026-07-04 | 定稿工作坊產物的 provenance 認定——非前代 source、採認不觸 §I.5 拷貝禁令 | — | — | — |
| 0025 | accepted | 2026-07-04 | wire 契約機器化執行面——typings 抽 JSON Schema 快照管線＋coverage gate cargo test 形 | — | — | — |
| 0026 | accepted | 2026-07-05 | 系統設定值型驗證——可擴型別 registry＋per-key 可宣告範圍＋正規化落庫＋未知型拒收 | — | — | — |
| 0027 | accepted | 2026-07-05 | 第一功能刀最小授權骨架——require_policy casbin enforce＋enforce_mw 骨架、登入延 auth 刀 | — | — | — |
| 0028 | accepted | 2026-07-05 | ★I18N-WIRING 軌道擴範圍 (iv)——授權 zh-TW 首發 locale 完整建置（全字典＋註冊＋語言選單） | — | — | — |
| 0029 | accepted | 2026-07-05 | 替代登入端點包處置＝後端 stub（B-008 三選一收斂） | — | — | — |
| 0030 | superseded | 2026-07-05 | 會話閒置逾時＝無狀態 sliding refresh（設定可調、無絕對上限） | — | — | 0033 |
| 0031 | accepted | 2026-07-05 | 新增 ★BASE-WEB-AUTH-WIRING 軌道（auth 刀三處 base-web inline 接线授權） | — | — | — |
| 0032 | accepted | 2026-07-05 | schema-gate 閘 2 seed 契約放寬——容 post-baseline rev4 新增 seed（additive 白名單） | — | — | — |
| 0033 | accepted | 2026-07-06 | 會話生命週期改採 DB-stateful rotation（rotation＋reuse 偵測＋denylist 即時撤銷＋single-session＋精確 idle） | — | 0030 | — |
| 0034 | accepted | 2026-07-06 | 新增 ★BASE-WEB-LOGOUT-UX-WIRING 軌道（logout server-call 接线＋閒置登出 toast 兩用途） | — | — | — |
| 0035 | accepted | 2026-07-06 | T034 前端跨棧共用 refresh 在途承諾 won't-fix（by-design：alova 對真實 auth dormant＋後端 grace 冪等為並發正確性防線） | — | — | — |
| 0036 | accepted | 2026-07-06 | FR-017(ii) service-alova 閒置 toast 副本 by-design 省略（alova 對真實 auth dormant＋既有 showErrorMsg 雙彈＋乾淨做須動 showErrorMsg 出軌道） | — | — | — |
| 0037 | accepted | 2026-07-10 | 登入失敗節流合成終態（per-user 滑動窗＋負快取＋CAPTCHA 軟區＋手動解鎖；§I.7 島 E 進場） | — | — | — |
| 0038 | superseded | 2026-07-10 | 節流負快取層（DB 真相、fail-OPEN、TTL 不長於時窗、僅由 L2 再判路徑寫入） | — | 0016 | 0045 |
| 0039 | accepted | 2026-07-10 | schema 閘批次修復（gate1 結構 additive 容差＋B-055 varchar 長度 sidecar＋archetype-map 補登記＋快照重擷取） | — | — | — |
| 0040 | accepted | 2026-07-10 | 新增 ★BASE-WEB-LOGIN-CAPTCHA-WIRING 軌道（密碼登入表單圖形驗證碼接线，嚴限一用途） | — | — | — |
| 0041 | accepted | 2026-07-10 | §III.2「補完 vs 新能力判準」之「零新 key」釋義（不含既有授權頁既有子命名空間下的資料級 label key） | — | — | — |
| 0042 | accepted | 2026-07-11 | 新增 ★BASE-WEB-DEVPROXY-WIRING 軌道（dev 反代拓樸修正，嚴限三處） | — | — | — |
| 0043 | accepted | 2026-07-11 | 真實來源位址還原——三層信任錨＋兩 overlay＋七態信心（supersede ADR 0017 還原節、四項改善） | — | 0017 | — |
| 0044 | accepted | 2026-07-11 | 憲法 §I.7 行為島進場——島 F（IP 存取控制閘＋信任錨＋來源維節流）＋島 E2 射程釐清 | — | — | — |
| 0045 | accepted | 2026-07-11 | 來源維度節流啟用——GREATEST 兩源（拔 reset-on-success）＋負快取沿 0038（supersede 0038 調整項二） | — | 0038 | — |
| 0046 | accepted | 2026-07-11 | 稽核 region 欄 GeoIP 填值——xdb §I.5 例外整檔拷貝、best-effort、boot 守門 | — | — | — |
| 0047 | accepted | 2026-07-11 | 鎖定專屬審計欄——won't-fix（島 E3 鎖定零稽核列⇒該審計區分無標的） | — | — | — |
| 0048 | accepted | 2026-07-12 | 憲法 §I.7 行為島進場——島 G（casbin 授權治理）＋MODAL-WIRING (a) 檔名枚舉澄清 | — | — | — |
| 0049 | accepted | 2026-07-12 | 授權歸檔表加「來源角色識別」欄（m007 role_id）——restorability 去牆鐘化＋protected 欄 won't-add 分析 | — | — | — |
| 0050 | accepted | 2026-07-12 | 業務錯誤結構化明細通道——信封 data 欄載 i18n 插值參數（含洩漏面評估與 §I.3 讀法確認） | — | — | — |
| 0051 | accepted | 2026-07-13 | 選單域狀態機總綱——序列化域＋同鍵重建零繼承＋治理域／顯示域分層（島 H 設計理據） | — | — | — |
| 0052 | accepted | 2026-07-13 | 憲法 §I.7 行為島進場——島 H（選單域生命週期與授權連動）＋§III.2(d) 錨點擴充＋1.7.0 log 補記（v1.8.0） | — | — | — |
| 0053 | accepted | 2026-07-14 | 使用者域狀態機總綱——統一序列化鎖序＋撤 session 連動＋seed 帳號結構保護＋B1 login/refresh 鎖內重驗（島 I 設計理據） | — | — | — |
| 0054 | accepted | 2026-07-14 | 密碼政策 enforcement——單一驗證點＋chars/bytes 雙約束＋forbid_username 相等語意＋密碼載體三重不洩（島 I5 設計理據） | — | — | — |
| 0055 | accepted | 2026-07-14 | B-030 初始密碼拆階段——admin 指定＋政策驗證先行；隨機生成＋首登強制改密延後、綁自助改密 | — | — | — |
| 0056 | accepted | 2026-07-14 | REVIEW-001-010 十筆 no-action findings 定調——won't-fix／by-design／時序校準備查 | — | — | — |
| 0057 | accepted | 2026-07-14 | 稽核讀端四源＋查詢能力——兌現並增補 ADR 0011（三表→四源、pg_trgm 本刀落地） | — | — | — |
| 0058 | accepted | 2026-07-14 | 稽核 purge 執行面——時間水平線唯一形狀、下限守門、自落 op-log；保留天數政策 B-016 續留 | — | — | — |
| 0059 | accepted | 2026-07-14 | op-log payload PII 政策——落庫白名單定調＋讀端顯示面打碼（收 B-044） | — | — | — |
| 0060 | accepted | 2026-07-14 | sys_access_log 寫入端啟用——protected 全請求、fail-open、不記 body/query | — | — | — |
| 0061 | accepted | 2026-07-16 | 憲法 amend——MODAL-WIRING (d) 擴字串涵蓋 IP 規則回收桶復原（v1.10.0→v1.11.0 MINOR） | — | — | — |
| 0062 | accepted | 2026-07-16 | 008 IP 規則讀端契約擴充——getIpRuleList 加 filter＋IpRuleRecord 審計欄上 wire＋enrich（最小誠實形→管理頁完整形） | — | — | — |
| 0063 | accepted | 2026-07-16 | ip-rule RBAC 按鈕碼 seed＋sys_menu.buttons 回填——為未來非-super 授權下放預留完整基建（B-083 前置鏈） | — | — | — |
| 0064 | accepted | 2026-07-16 | schema-gate seed 內容變更受管軌道——SEED_CONTENT_OVERRIDE_ALLOWLIST（既有 seed 列內容合法演進） | — | — | — |
| 0065 | accepted | 2026-07-17 | getUserRoutes 恆附掛 self-service 路由白名單——自助頁可達性與 RBAC 授權表脫鉤 | — | — | — |
| 0066 | accepted | 2026-07-17 | global-content 頁面切換 Transition 去 out-in＋fade-slide leave absolute——上游 isLeaving 卡死 workaround | — | — | — |
