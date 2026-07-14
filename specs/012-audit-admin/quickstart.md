# Quickstart: 012-audit-admin

**Branch**: `012-audit-admin` | **Date**: 2026-07-15 | **Plan**: [plan.md](plan.md)

端到端驗收指南（非實作碼）。契約細節 ☞ [contracts/audit-admin-endpoints.md](contracts/audit-admin-endpoints.md)；
資料形 ☞ [data-model.md](data-model.md)。

## 前置

```bash
# 容器內、serial（host 無 toolchain；平行 cargo 互撞 target）
docker compose exec rust-api cargo test --workspace        # 全綠（含契約 63、負向自證五條）
docker compose exec rust-api sh -c 'ls migration/src/m009*'  # m009 存在（extension＋GIN×2＋seed 2＋清理）
tools/schema-gate gate2   # 244 present＋allowlist 容差（casbin extra 10＝m008 8＋m009 2；另含既有 system_settings 條目、全集以實跑為準）
# pg_trgm 生效驗證（repo 首例 extension）；憑證＝compose 實值（POSTGRES_USER=soybean、POSTGRES_DB=soybean_admin_rust）
docker compose exec postgres psql -U soybean -d soybean_admin_rust -c "\dx pg_trgm"
docker compose exec postgres psql -U soybean -d soybean_admin_rust -c "\di idx_login_attempt_user_name_trgm idx_access_log_path_trgm"
# B-089 清理驗證（孤兒歸零、活列不誤刪）
docker compose exec postgres psql -U soybean -d soybean_admin_rust -c \
  "SELECT count(*) FROM sys_token WHERE created_by NOT IN (SELECT id FROM sys_user)"   # =0
```

## 全量閘清單（收刀閘）

- **cargo test --workspace**（容器內、serial）全綠：既有零轉紅（FR-018 回歸）＋本刀新測。
- **契約 registry**：58→**63**（4 讀端＋purge）；覆蓋閘雙射（每 route 必有 case）；
  wire_schema **datetime offset 斷言重建**（B-091：本刀 createTime＋既有已上 wire 時間欄）。
- **gate2**：凍結 244 全 present＋SEED_ADDITIVE_ALLOWLIST 容差（casbin extra 10＝m008 8＋
  m009 2；另含既有 system_settings 條目〔m003×1＋m005×3＋m006×3〕、容差全集以 gate2 實跑
  為準）、fixtures 零改寫；m001~m008 一字不動。
- **負向自證五條**（拆除守門即轉紅）：①mask 拆除→讀端回應含電話原值→紅（SC-003）
  ②purge 挑列參數構造不可達＋beforeDays<30 拒（SC-005）③access-log 寫故障（斷 DB 模擬）→
  業務請求照常成功（SC-004）④同 sid 重複 idle→恰一列（SC-006）⑤unlock 之 op-log 失敗→
  Redis 全不動、回 5000（SC-006）。
- **typecheck＋fork-delta-lint**（base-web 動即跑；新檔零原行、inline 圈界）。
- **治理前置**（前端執行單元前 user 親決）：島 J 入憲 v1.10.0＋MODAL-WIRING (i)＋
  ADR 0057~0060 → accepted。

## CDP 實機場景（Edge@9229、quick-login Super/123456；S 前綴＝cdp012_）

### S1 四分頁顯示與查詢（US1）
1. 進 `/manage/audit`：選單「稽核中心」三語正確（`route.manage_audit` 兌現 B-061；SC-008）、
   四分頁齊（操作日誌／存取日誌／登入嘗試／會話事件）。
2. 操作日誌分頁：`fetchGetOperationLog` 200、新到舊、分頁翻頁正確；以 entityTable＋operation＋
   時間區間過濾各命中預期（SC-001）。
3. 人員過濾：以帳號名（如 `Admin`）過濾 op-log→解析為識別集合命中；同傳 operatorId 優先
   （clarify Q1；SC-001）。
4. 空字串條件查詢＝未設（不落空、不 400；SC-002）。

### S2 模糊搜尋（US1／D3）
1. 登入嘗試分頁輸入部分帳號名（如 `adm`）→ 命中含該字串之列（大小寫不敏感；SC-002）。
2. 存取日誌分頁輸入部分路徑（如 `/user`）→ 命中；輸入 `%` 字面→字面比對、零萬用注入（SC-002）。

### S3 打碼渲染（US1／D5）
1. 對含 phone/email 的使用者做一次編輯（產生 op-log 快照）→ 稽核中心檢視該列 payload：
   `091****78`／`a***@example.com` 形；DevTools Network 檢回應 JSON **無原值**（SC-003）。

### S4 purge 全流程（US3）
1. 任一分頁點清理→modal 天數輸入＋後果說明；輸入 7→拒因三語含「至少 30 天」明細（SC-005/008）。
2. 輸入 ≥30 合法值→確認→回報刪除筆數；操作日誌分頁可查到 PURGE 自記列
   （payload 含 table/before_days/deleted_count；SC-005）。
3. （資料層）歷次 PURGE 列於再次清理 op-log 後仍在（固定豁免；SC-005）。

### S5 三語零 raw key（US5）
1. zh-TW／zh-CN／en-US 逐語切換：選單、四分頁標題欄位、清理 modal、拒因 toast 全在地化、
   0 原始鍵字面（SC-008）；登入嘗試分頁語意說明可見（FR-021）。

### S6 access-log 即時落列（US2）
1. 點任一管理頁（觸發已認證 API）→ 存取日誌分頁刷新即見新列（method/path/status/操作者
   帳號名俱全；含稽核讀端自身請求＝無豁免；SC-004）。
2. 登出→登入（Public 請求）→ 存取日誌零新列（登入行為在登入嘗試分頁；SC-004）。

## rust 併發／整合機器證

- purge × 併發寫入：purge 執行中新 op-log 寫入照常（水平線無交集；終態兩者俱在）。
- idle 冪等：同 sid 連續兩次觸發 idle 拒發→session_event 恰一列（第二次 8888 照回）。
- unlock PG-first 次序：既有次序測試 `unlock_handler_source_order_set_marker_before_del_lock`
  （011 期編號 T056）由本刀 T020 調和為 op-log→SET→DEL 新固定序（改寫、非拆除）。

## 驗收對照（10 SC → 佐證場景）

| SC | 佐證 |
|---|---|
| SC-001 四分頁走通＋權限 | S1＋非超管 CDP 抽驗（選單不可見＋直呼 5003） |
| SC-002 模糊／空字串／字面化 | S2＋S1.4＋單元測試（escape 表驅動） |
| SC-003 打碼 100%＋負向 | S3＋負向自證①＋mask 表驅動窮舉 |
| SC-004 access-log 恰一列／零列／fail-open | S6＋負向自證③＋layer 整合測試 |
| SC-005 purge 水平線／下限／自記／豁免 | S4＋負向自證②＋併發機器證 |
| SC-006 unlock 必留痕＋idle 冪等 | 負向自證④⑤＋idle 機器證 |
| SC-007 既有行為回歸 | cargo 全綠（既有零轉紅）＋E3 短路零列既有測試 |
| SC-008 三語零 raw key | S5＋S1.1＋S4.1 |
| SC-009 零結構變更／seed 恰 2／孤兒清理 | gate2＋前置 psql 驗證＋m009 down 對稱 |
| SC-010 讀端唯讀 | handler 零寫斷言＋entity_access_lint 照跑 |

## agent context

rev4 CLAUDE.md 為手維薄操作手冊（≤250 行 lint 強制），**不走 speckit auto agent-context 機制**
——本步 N/A（009/010/011 先例；架構影響於收刀走活書 arch-impact＋docs-sync generate）。
