# Contract: 快照管線與正典表（002-schema-baseline；B-003／B-004）

docs-sync 的 refresh→快照→reference 兩表契約。設計約束＝pre-commit（generate／check／
lint）維持秒級離線；需 docker 的步驟隔離在顯式 refresh 命令（spec FR-008／FR-014 分工）。

## 1. `tools/docs-sync refresh`（新子命令；需 stack 在）

- 行為：docker compose exec -T postgres psql 唯讀撈取 →確定性排序→ 寫兩支追蹤快照檔
  （半自動材質、同 events.jsonl 類；人不手編、由本命令重寫）：
  - `docs/ops/reference-src/schema-snapshot.json`：12 表全量欄明細——表｜欄名｜
    ordinal_position｜型別（PG 正規形）｜可空｜預設；＋索引與約束定義清單。
  - `docs/ops/reference-src/accounts-snapshot.json`：sys_user（id／user_name／nick_name／
    status；**排除 password——雜湊值也不入快照**）＋sys_role（id／role_code／role_name／
    status）＋sys_user_role 綁定。
- 失敗語意：stack 不在→非零退出＋提示啟動命令；絕不寫入部分結果（原子替換）。
- 範圍：seaql_migrations 除外；快照含產生時點欄位（date、非時刻——保確定性重跑友善）。

## 2. generate／check（離線；沿 U5 ports 的 REFERENCE_LIVE 擴充點）

- generate：解析兩快照 → `docs/generated/reference/schema.md`（表｜欄｜型別｜可空｜預設，
  逐表分節；GEN_HEADER 慣例）＋`docs/generated/reference/accounts.md`（帳號｜暱稱｜狀態｜
  角色綁定；零密碼欄）；stub 轉真（REFERENCE_LIVE 各加一筆、STATE 對賬區兩行轉真、
  剩 routes／screens 兩 stub）。
- check：L2 對賬——快照重算生成物 vs 磁碟生成物 diff（快照改動未 generate＝紅、指名）；
  快照檔缺失＝紅（轉真後即為表的存在前提、fail-loud）。
- 確定性：同快照同 byte 輸出；快照本身確定性排序（表名→ordinal）。

## 3. 新鮮度紀律（守門句、入活書 §8）

- 「加 migration 的刀 MUST 於單元邊界重跑 refresh→generate 並隨 commit」——漂移窗口
  由刀內紀律＋收官 gate2 收斂；002 收刀證據＝refresh 後 git diff 空（快照＝實庫）。
- 快照為「輸入中繼」非生成物：docs/generated 嚴禁手改條款不涵蓋它、但人工手編快照
  視同偽造帳（禁止；只准 refresh 命令寫入）。

## 4. 密碼與機密面

- 明文密碼零出現（DB 只有 PHC 雜湊；快照與 reference 連雜湊都不載——SC-007）。
- accounts 正典表定位＝「有哪些帳號／角色／綁定」的查閱面；認證細節（密碼策略等）
  不在其範圍。
