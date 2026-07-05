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
| 0016 | accepted | 2026-07-03 | 已生效鎖定加 Redis 負快取層（DB 真相、fail-OPEN） | — | — | — |
| 0017 | accepted | 2026-07-03 | IP 存取控制閘——白＞黑＞default-allow、DB 真相＋記憶體微秒判定、fail-OPEN | — | — | — |
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
| 0030 | accepted | 2026-07-05 | 會話閒置逾時＝無狀態 sliding refresh（設定可調、無絕對上限） | — | — | — |
| 0031 | accepted | 2026-07-05 | 新增 ★BASE-WEB-AUTH-WIRING 軌道（auth 刀三處 base-web inline 接线授權） | — | — | — |
| 0032 | accepted | 2026-07-05 | schema-gate 閘 2 seed 契約放寬——容 post-baseline rev4 新增 seed（additive 白名單） | — | — | — |
