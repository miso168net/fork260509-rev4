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

- Req（擴充）：`{ userName, dimension? }`。★`dimension` **選用**：未帶→預設 `"user"`（帳號維、向後相容 007）；`"ip"`＝來源維（顯式指明）。
- 動作序（不可換序、測試機器強制）：SET marker→DEL lock→op-log；`DIM_USER` 字面隨 `dimension` 參數化。
- op-log `payload_after` 加 `dimension` 資訊。
- **契約案覆蓋兩案**：①`{userName}`（未帶維度欄）→ 作用帳號維；②`{userName, dimension:"ip"}` → 作用來源維。

---

## 契約測試落點

- `contract.rs`：五規則端點各補 case（`Request::get/post/delete`）；unlock 補「未帶維度」「顯式來源維」兩案；registry 計數斷言 16→（16+新端點數）。
- `docs-sync`：`ROUTE_METHODS` 加 `"Delete":"DELETE"`；self-test 探針 `HttpMethod::Delete`→`Patch`（未知 variant fail-loud 測試不失效）。
- 覆蓋閘：每條新 route 必有 contract case（§I.3 coverage gate）。
