# Quickstart: 002-schema-baseline 驗證指南

命令級驗證（spec 五 story＋SC 的可執行化）。契約細節見 [contracts/gates.md](contracts/gates.md)
與 [contracts/snapshot-reference.md](contracts/snapshot-reference.md)、定稿見
[data-model.md](data-model.md)；本檔不含實作碼。約定 `CF="docker compose -f
docker-compose.yml -f docker-compose.dev.yml"`（repo 根執行）。

## 前置

- 001 dev stack 可用（機密與憑證已生成；`$CF up -d --wait` 曾全綠）。
- fixtures 已拷入 `specs/002-schema-baseline/fixtures/`；data-model §3 轉錄互驗已過
  （research R7——`tools/schema-gate` 對 fixtures/scratch-columns.txt 的 selfcheck 形）。

## A. 基線一鍵就位（US1／SC-001）

```bash
$CF down -v && $CF up -d --wait && echo $?            # 0；五常駐 healthy＋migrate Exited(0)
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c '\dt'
#   期望：11 業務表＋casbin_rule＋seaql_migrations
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -tc \
  'SELECT version FROM seaql_migrations ORDER BY version'
#   期望：恰兩筆——m001_baseline_schema、m002_baseline_seeds
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -tc \
  "SELECT (SELECT count(*) FROM sys_user)||'/'||(SELECT count(*) FROM sys_role)||'/'||
          (SELECT count(*) FROM sys_user_role)||'/'||(SELECT count(*) FROM sys_menu)||'/'||
          (SELECT count(*) FROM casbin_rule)||'/'||(SELECT count(*) FROM system_settings)"
#   期望：3/3/3/78/149/8（合計 244）
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -tc \
  "SELECT count(*) FROM sys_user WHERE password LIKE '\$argon2id\$%'"   # 3（零明文、SC-007）
```

## B. 閘 1 結構零漂移（US2／SC-002）

```bash
tools/schema-gate gate1                     # 綠；逐表結論、白名單外差異=0
tools/schema-gate gate1 --live-rev3         # rev3 在機時：live 直比交叉驗證、結論一致
# 負面（驗畢還原）：
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c \
  'ALTER TABLE sys_user ADD COLUMN t_gate1_probe text'
tools/schema-gate gate1                     # 紅、指名 sys_user.t_gate1_probe
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c \
  'ALTER TABLE sys_user DROP COLUMN t_gate1_probe'
tools/schema-gate gate1                     # 綠
```

## C. 閘 2 定稿落實＋審計守門（US3／SC-003／SC-004）

```bash
tools/schema-gate gate2                     # 綠：12 表欄序逐欄＋seed 244 列全配對
tools/schema-gate audit                     # 綠：12 表四變體歸屬全過
# gate2 負面（驗畢還原；natural key 定義見 contracts/gates.md §3、實值見 fixtures json）：
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c \
  "DELETE FROM system_settings WHERE setting_key='password_min_length'"
tools/schema-gate gate2                     # 紅、指名該 setting_key
#   還原＝回捲並重放 m002（重跑 migrate 服務是 no-op——seaql_migrations 已記錄、框架跳過）：
$CF exec -T rust-api cargo run --bin migration -- down    # 回捲 m002（一支）
$CF exec -T rust-api cargo run --bin migration -- up      # 重放 m002、seed 補回
tools/schema-gate gate2                     # 綠
# audit 負面（主庫暫建未登記 probe 表、驗清單守門；驗畢還原）：
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c \
  'CREATE TABLE t_audit_probe(id bigint)'
tools/schema-gate audit                     # 紅（清單外業務表 t_audit_probe）
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c 'DROP TABLE t_audit_probe'
tools/schema-gate audit                     # 綠
```

## D. 冪等與可逆（US1 場景 3／SC-005）

```bash
$CF up -d --force-recreate migrate          # 二次套用（框架跳過已套用＝no-op）
docker wait $($CF ps -aq migrate)           # 期望輸出 0（one-shot 退出碼）
#   A 段計數重驗應不變
# down→up 可逆（容器內 migration CLI；serial）：
$CF exec -T rust-api cargo run --bin migration -- down -n 2   # 全卸（m002＋m001 含 adapter down）
$CF exec -T postgres psql -U soybean -d soybean_admin_rust -c '\dt'
#   中間觀測：只剩 seaql_migrations（防半卸假綠）
$CF exec -T rust-api cargo run --bin migration -- up     # 重套兩支
tools/schema-gate gate2                     # 綠（列數複現）
$CF down -v && $CF up -d --wait && echo $?  # 歸零重來仍 0；A 段計數重驗
```

## E. entity 編譯（US4）

```bash
$CF exec -T rust-api cargo test --workspace   # 全綠（含 entity 編譯；serial）
# 欄序宣告 vs 定稿：閘 2 已驗實庫＝定稿；entity 欄集合另由 tasks 內建測試/對照驗證
```

## F. 快照管線與正典文件（US5／SC-006）

```bash
python3 tools/docs-sync refresh             # 需 stack；寫兩支快照
python3 tools/docs-sync generate && python3 tools/docs-sync check   # 綠；schema/accounts 轉真
grep -c 'stub' docs/generated/STATE.md      # 對賬區剩 routes、screens 兩行 stub
# 漂移攔截（驗畢還原）：手改 schema-snapshot.json 任一欄→check 紅→git checkout 還原→綠
# 新鮮度證據：再跑 refresh → git diff docs/ops/reference-src/ 空（快照＝實庫）
```

## G. 不變式與時效迴歸（SC-008＋001 SC-007 迴歸）

```bash
git -C base-web status --porcelain          # 空
git submodule status | grep base-web        # pin 停 9c6f223
docker ps --format '{{.Names}} {{.Status}}' | grep '^rev3-admin'   # 基線對照（前後一致）
$CF down && time $CF up -d --wait           # 熱起 ≤5min（001 SC-007 迴歸；migration 變重後實測）
```
