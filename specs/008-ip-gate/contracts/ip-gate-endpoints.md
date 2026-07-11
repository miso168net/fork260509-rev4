# Contracts: 008-ip-gate 端點契約

**基準**：§I.3 wire 不變式（envelope `{data, code, msg}`、13 碼凍結、msg=i18n key、business error 走 HTTP 200）。★**零新錯誤碼**——阻擋 reuse `5003`→403、衝突/驗證 `2222`、自鎖走既有業務碼。

契約案覆蓋閘（`contract.rs`）為純 case_key 雙向 bijection、不含 method 維度；新增 DELETE 路由照常補 case（`Request::delete`）＋registry 計數斷言 +N。

---

## 規則管理五端點（casbin 政策 m002:348-352 已 seed、R_SUPER）

| 端點 | HTTP | 路徑 | casbin act |
|---|---|---|---|
| 列表 | GET | `/systemManage/getIpRuleList` | GET |
| 新增 | POST | `/systemManage/addIpRule` | POST |
| 修改 | POST | `/systemManage/updateIpRule` | POST |
| 刪除 | **DELETE** | `/systemManage/deleteIpRule` | **DELETE**（P-Q1：擴 HttpMethod::Delete、對齊 seed） |
| 復原 | POST | `/systemManage/restoreIpRule` | POST |

### 共通回應

- 成功：`{ data, code:"0000", msg:"..." }`。
- 自鎖拒寫（FR-022）：`code:"2222"`＋`msg` 業務 key（如 `biz.ipRule.selfLock`）——變更後規則集會阻擋操作者當下 client_ip。
- 重複（FR-023）：`code:"2222"`＋衝突 key（partial-uniq 23505 remap）。
- 阻擋回應（閘門攔非本端點、對任意被 deny 的請求）：`5003`→HTTP 403（reuse、§I.3 例外 status）。

### getIpRuleList（GET）
- 回 hybrid 回收桶清單（含軟刪、active 沉頂）；分頁形 `PageRes<T>`（§I.3）。

### addIpRule / updateIpRule（POST）
- Req：`{ wbipCidr, wbipType, wbipMemo?, order? }`（camelCase wire）。
- 守門：`normalize_cidr`（正規化落庫）＋`validate` type∈{allow,deny}。
- ★自鎖檢查（FR-022）：組「變更後 RuleSet'」→ `decide(RuleSet', ctx.client_ip).verdict == Deny` → 拒 selfLock。allow 規則永不自鎖。
- 寫成功→`reload_and_publish`（本機 store＋PUBLISH `ipgate:invalidate`）。

### deleteIpRule（DELETE）/ restoreIpRule（POST）
- delete＝軟刪（set deleted_at/by）；restore＝清 deleted_at/by。
- ★自鎖檢查覆蓋此二路徑（FR-022）：delete 一條為操作者提供豁免的 allow、restore 一條涵蓋操作者的 deny → 皆模擬變更後規則集判定、命中即拒。
- 同 txn 寫 op-log（FR-024）。

---

## unlockLogin（既有端點擴維度欄、FR-033）

| 端點 | HTTP | 路徑 | casbin act |
|---|---|---|---|
| 手動解鎖 | POST | `/systemManage/unlockLogin` | POST（既有、m002 已 seed） |

- Req（擴充）：`{ userName?, dimension?, target? }`（camelCase wire、FR-033）。
  - `dimension` **選用**：未帶→預設 `"user"`（帳號維、向後相容 007）；`"ip"`＝來源維。**非 {user,ip} 值→回 `2222`**（業務驗證碼、零新碼）。
  - **解鎖標的**：`dimension="user"`（或未帶）時以既有 `userName` 欄承載帳號名（此維度 `userName` 必填、向後相容 `{userName}`）；`dimension="ip"` 時以 `target` 欄承載來源位址字面（`userName` 於此維度可省）。★`target` 的 IP MUST 經與計數鍵相同的粒度導出（IPv6 先聚合 /64、與 FR-026 一致），否則解鎖鍵與鎖定鍵不符、解不到。
- 動作序（不可換序、測試機器強制）：SET marker→DEL lock→op-log；`DIM_USER` 字面隨 `dimension` 參數化；解鎖鍵 value＝帳號維用 `userName`、來源維用 `target`（經 /64 聚合）。
- op-log `payload_after` 加 `dimension`（與標的）資訊。
- **契約案覆蓋三案**：①`{userName}`（未帶維度欄）→ 作用帳號維；②`{dimension:"ip", target:"<IP>"}` → 作用來源維（IPv6 經 /64 聚合導鍵）；③非法 `dimension` 值 → `2222`。

---

## 契約測試落點

- `contract.rs`（純 case_key↔route 雙向 bijection、形狀級）：五規則端點各補一 registry case（`Request::get/post/delete`）；registry 計數斷言 16→21（現 16 案＋5 規則端點；unlock-login 既有 case 不動）。
- ★unlock 的三行為案（未帶維度／顯式來源維帶 target／非法維度）落 `handler/throttle.rs` 的 `mod tests`（**非** contract.rs——同一 unlock-login 路由無法再補 keyed case、bijection 機制不容）；FR-033「契約案覆蓋」指此三行為測試案。
- 規則重複寫入→`2222`（partial-uniq 23505 remap）之行為案落 `handler/ip_rule.rs` 的 `mod tests`（同非 registry case）。
- **list record wire 型**：五端點回應的 record `id` 欄依 §I.3 預設——DB `i64`→JSON `number`、序列化帶 2^53 fail-loud 守衛；本刀無 base-web typings oracle（FR-042 不建頁），若任何 id 欄偏離 number＝型別謊言、須立 ADR。
- `docs-sync`：`ROUTE_METHODS` 加 `"Delete":"DELETE"`；self-test 探針 `HttpMethod::Delete`→`Patch`（未知 variant fail-loud 測試不失效）。
- 覆蓋閘：每條新 route 必有 contract case（§I.3 coverage gate）。
