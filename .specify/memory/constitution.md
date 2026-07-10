# rev4-admin (fork260509-rev4) Constitution

> **本檔為 rev4 設計凍結權威**：與活書（docs/arc42/ARCHITECTURE.md）、ADR、生成物衝突時以本檔為準。
> v1.0.0 由 B6 逐筆過目拍板重鑄（user 在場逐筆點頭、17 題；拍板紀錄與 rev3 出處＝ADR 0001）。
> 改動本檔一律走 Amendment 流程（§V.2）；spec-kit `/speckit-plan` 必須對照本檔跑 Constitution Check（§IV）。

---

## I. Core Principles

### I.1 base-web 為權威（NON-NEGOTIABLE）

**規則**：base-web（`rev4-admin-base-web` 分支實碼、自 upstream soybeanjs example 最新 HEAD 衍生）有的功能，rust-api 都要提供對應 endpoint。設計範圍嚴格、不縮減。

**含義**：
- base-web 的 wire／type／endpoint／route shape，rust-api 必須對齊
- 「v1 從簡」只能是交付排程、不能簡化設計範圍
- 不動 base-web inline（例外見 §III 軌道授權；授權後的變動執行紀律見 §III fork-delta 紀律）
- upstream rebase 友善——不留 upstream 衝突風險高的改動；fork 差異全程 `rev4-inline` 標記可定位

### I.2 menu 權限 Casbin enforce

**規則**：menu 由 Casbin RBAC enforce、有權才顯示。

**含義**：
- 業務 menu 走 `/route/getUserRoutes` → 後端 Casbin enforce 過濾 → 前端顯示
- demo menu 處理：demo view **全部進 `sys_menu` seed、初始僅勾給 `R_SUPER`**——全集完整、可見性由角色勾選層（casbin menu 維度）治理下放；`hideInMenu`／頁面排除等前端隱藏機制**皆不啟用**
- constantRoutes（login／404／403）前端寫死、與 menu 無關、不動

### I.3 wire 契約權威序與不變式（NON-NEGOTIABLE）

**權威序**（對賬裁決）：
1. **base-web 實碼**（`rev4-admin-base-web` 分支：`typings/api/*.d.ts`＋`service/api/*.ts`＋`.env`＋`views/**`）＝ wire **唯一權威**
2. 官方 docs 站＝解釋性文件，僅紀律性約束引為規範
3. mock 實測＝補充回歸 fixture，**不當 shape oracle**

**鎖定不變式**：
- envelope `{data, code, msg}`（無 `success` bool）；`code`＝string `"0000"` 非 number；business error 走 **HTTP 200** 信封
- **id 序列化＝逐欄位忠實 typings**：typings 宣告 number 的欄位回 JSON number、宣告 string 的欄位（如 `MenuRoute.id`／`UserInfo.userId`）於序列化邊界轉字串；DB 一律 i64 自增；serializer 帶 2^53 fail-loud 守衛；**型別謊言帳本歸零起算**（每筆顯式偏離＝拍板、立 ADR）
- **13 碼矩陣整組凍結**：`0000`/`1000`/`2222`/`3333`/`7777`/`7778`/`8888`/`8889`/`9998`/`9999`/`4040`/`5003`/`5000`；HTTP status 例外僅 `4040`→404、`5003`→403，**內部錯誤 `5000` 一律 HTTP 200 信封**；4 保留碼（`7778`/`8889`/`9998`/`9999` 組內後端從不發出者）僅前端 `.env` 分組認得、contract test 斷言後端從不發出；新需求優先 reuse 既有碼
- `msg` 載穩定 i18n key（後端語言無關、不在地化；前端 `$t` 翻譯、未命中 graceful fallback）——「wire 凍結事實」指錯誤碼本身、`msg` 非人話字串；觀測側可讀性補強候選掛 BACKLOG
- 業務驗證 error code＝`2222`；`5xxx` 段為授權／基建、非業務；refresh 類 critical code 絕不用在業務驗證
- 分頁形 `PageRes<T>`＝`{current, size, total, records}`（camelCase、無 `pages`/`success`、空頁 `records:[]`）
- envelope universal 例外僅 2：`/health`（plain text）與 `/metrics`（Prometheus exposition）
- 預設帳號：`Super / Admin / User`（login req）＋ User → User01 alias（getUserInfo response）
- **契約機器化**：typings 抽 JSON Schema 當 contract test 裁判（唯讀、不動官方檔）＋coverage gate（每條 route 必有 contract case）＋碼表 table-driven case；機制隨 wire 地基刀落地

**錨定註**：本節錨定 `rev4-admin-base-web` 分支實碼；若上游演進使碼表／typings 與本節分叉，於 wire 地基刀對賬現形、走 Amendment 校正。

### I.4 SDD＋TDD 混合工作流（NON-NEGOTIABLE）

- **階段 0 brainstorm**：產出存 `docs/brainstorms/<NNN>-<name>.md`；期間拍板→ADR draft
- **階段 1 SDD 設計鏈**：`/speckit-specify`（**手動起手**）→ `/speckit-clarify` → `/speckit-plan`（對照本 constitution！）→ `/speckit-tasks` → `/speckit-analyze`
- **階段 2 TDD 實作**：superpowers executing-plans（**不是 `/speckit-implement`**）
- **收尾**：finishing-a-development-branch → `git merge --no-ff` 回 `rev4-admin-root`（保留 feature branch 供 audit）
- `git push`／`git merge` 不得出現於 finishing 之前
- 收刀簿記三步：events append＋NOTES＋docs-sync generate（一筆簿記 commit）；拍板全文歸 ADR
- 詳細操作＝CLAUDE.md §2/§3（本檔不重複）

### I.5 rust-api 全新寫、對前代 source 受控參照（RUSTAPI-SOURCE-ISOLATION）

**規則**：rev4 rust-api 整棵樹自源倉 main（Initial commit）起全新寫；設計以 rev3 已驗證結論為輸入（承接經 ADR provenance），**code 不拷貝**。

**前代 source 立場（rev3 為主、rev2 溯源，皆唯讀參考庫）**：
- **讀允許**：可 grep／閱讀前代 source 對照驗證（施工參考）
- **拷貝禁止**：實作必須重新打字消化、不可整段複製
- **防回歸條款**：參照前代 code 時，凡 rev4 拍板已推翻的行為**不得帶回**

**例外**：`sea-orm-adapter`／`xdb` 工具性 crate 整檔拷貝（已驗證、工具性質）。

### I.6 業務表審計欄標準（SCHEMA-AUDIT-COLUMNS）

**規則**：業務主表建表（create migration）時 MUST 含 6 審計欄——
`created_at` / `created_by` / `updated_at` / `updated_by` / `deleted_at` / `deleted_by`。

**型與約束**：
- `*_at`：`timestamptz`。`created_at` NOT NULL default `now()`；`updated_at`／`deleted_at` nullable
- `*_by`：operator 的 `user_id`（`bigint` nullable／`Option<i64>`，**非 user_name 字串**）；system seed／migration／未認證情境無 operator → `null`
- **成對**：`deleted_at` 必與 `deleted_by` 同寫；`updated_at`＋`updated_by` 同理

**archetype 四變體**（整組凍結；各表歸屬隨 schema 刀入活書與 generated/reference/schema）：
- **A 業務全 6 欄**（例：使用者／角色／選單／系統設定表）：如上；soft-delete 表配 partial-uniq `WHERE deleted_at IS NULL`（PK 本身總體唯一者除外）
- **B append-only 日誌**（例：三 log 表）：只 `created_at` NN（＋operator 類 domain 欄）；**無 soft-delete、無 update、不可竄改**；MUST NOT 加 `updated_*`/`deleted_*`
- **C join／狀態機**（例：user-role join＝零審計硬刪；token 表＝僅 `created_at`＋status 狀態機）
- **D 治理變體**（例：casbin 規則表＝`protected`/`created_at`/`created_by` 對 stock adapter 隱形；archive 表＝原 grant 欄＋`archived_at/by`＋`archive_reason`、無 update/delete 欄）

**無 retrofit 條款（含範圍釋義）**：本標準自第一條 migration 即生效——建表即帶 archetype 全欄，**不允許「建表漏審計欄、事後補」**。釋義：本條款標的**僅限 archetype 審計欄**；既有表因功能需要加業務／鑑識欄的**刻意、規劃、可逆**演進不在此限——前提是 archetype 欄規則不變（如變體 B 永不加 `updated_*`/`deleted_*`、不可竄改性維持），且非「忘帶事後補」的意外債。

### I.7 行為島 invariants（隨刀進場）

**本節為行為島狀態機不變式的凍結位，隨刀填充（006 起首度填充、見本節末「已入憲行為島」）。**

**進場規則**：每台狀態機（如 token rotation／policy governance／single-session）隨其刀的 brainstorm 拍板後，以 **MINOR Amendment** 將不變式條文入本節；rev3 已驗證的三台狀態機之不變式為對應刀 brainstorm 的直接輸入（出處經 ADR provenance 溯源）。入本節後，動任一條不變式走 Amendment；方向性反轉（fail-OPEN/closed 方向、DB-first、踢人雙通道分離等）＝MAJOR。常數值與欄級細節留活書（非凍結面）。

**已入憲行為島**（方向性面凍結、反轉＝MAJOR；常數/欄級留活書）：

- **島 A — single-session**（006、ADR 0033）
  - **A1 碼語意固定**：`7777` 恆＝他處登入 modal 通道、`8888` 恆＝silent 通道，兩碼語意永不互換（Redis-down 無 reason 時 kicked 可降級 `8888`＝降級非語意互換）。
  - **A2 政策解析階層**：per-user `session_policy` 覆寫優先於全域 `single_session_default`；`inherit` 讀全域。
- **島 B — token rotation**（006、ADR 0033）
  - **B1 reuse fail-secure**：已用/已撤 refresh 再現→撤整條 `rotation_chain` family（限該被盜會話、不及該使用者他會話）；例外＝grace 窗內、直接前驅之良性並發/重試→冪等回既發後繼、不撤。
  - **B2 寫端 lock-then-redecide＋chain 級序列化**：發放/撤銷決策在 `FOR UPDATE` 鎖住列鎖後重判、revoke loop-until-0-active、永不信 pre-read（L-075）。
- **島 C — denylist／即時撤銷**（006、ADR 0033）
  - **C1 撤銷寫序 PG 優先**：先 PG（family→revoked）再 Redis denylist，PG 為真相。
  - **C2 檢查分層**：Redis 連線故障→退 PG（fail-closed、不盲目放行）；denylist 為 blocklist、absence＝權威「未撤」；逐出/寫窗之 stale-allow 為有界 fail-open ≤access_TTL。
- **島 D — 閒置／sliding refresh**（006、ADR 0033、supersede 0030）
  - **D1 閒置唯一登出、無絕對上限**：連續活躍永不強制重登；不設絕對 session 壽命上限。
  - **D2 idle-clock 推進來源固定**：last_activity 僅由通過驗證的受保護請求推進（含 refresh 後 client 重試的原請求）；refresh 端點本身絕不推進（防背景 refresh-loop 繞過閒置）。
  - **D3 降級方向**：last_activity 熱快取不可用→退 refresh token TTL 為界（偏晚登出、絕不提前誤踢活躍者）；此為 idle-liveness fail 方向、與島 C 撤銷 fail-closed 各司其職不衝突。
- **島 E — 登入失敗節流**（007、ADR 0037、負快取層 ADR 0038 supersede 0016）
  - **E1 真相分層與 fail 方向**：鎖定真相＝PG `sys_login_attempt` 滑動窗（L2）；Redis 負快取（L1）為快路徑、其職僅短路已鎖判定、absence 非權威，且 **L1 僅由 L2 再判路徑寫入**（保證恆衍生自新鮮 L2 讀、杜絕假鎖）；L1 TTL 不長於時窗、命中不續期。全鏈 fail-OPEN（＝不因基建故障而拒絕本應放行的登入）：L1 讀故障→退 L2 並停用 captcha 要求；L2 count 故障→視 0 放行、若快取可用則無條件要求 captcha；稽核寫故障→不改登入回應；settings 缺值→退預設常數。★**唯一例外**：解鎖標記讀故障→視為無標記（可能 re-lock 剛解鎖之帳號、admin 可重解）。每一次降級 MUST 發結構化告警訊號。
  - **E2 防枚舉延伸**：判定鍵＝所送出帳號名原文（不存在帳號同計、同鎖、同要 captcha），其正規化 MUST 與帳號身分解析的正規化嚴格一致；鎖定與 captcha 要求皆回 `2222` ＋靜態一般化訊息，MUST NOT 洩觸發維度、剩餘時間、帳號存在性。
  - **E3 審計邊界**：**僅**被密碼雜湊實際驗證的登入終局落恰一列；L1 命中短路、L2 再判鎖、captcha-gate 拒絕、輸入形制超限 MUST NOT 落稽核列，量級訊號走觀測層麵包屑（非稽核表、best-effort）。鎖的最長存續＝一個時窗（非 L1 TTL）。
  - **E4 captcha gate 與硬鎖優先**：軟區要求 captcha；challenge MUST 綁定帳號名、**提交即消耗**（單次標記寫入先於答案比對）、且其答案 MUST NOT 可自 challenge 本身還原。缺／錯／過期／重放之 captcha 嘗試 MUST NOT 計入失敗數（落列規範見 E3）。硬鎖優先於 captcha——鎖中附有效 captcha 亦不受理、且該 captcha 不被消耗。

---

## II. 設計拍板凍結

隨 §I 未承載的獨立小拍板（拍板現況機器索引＝docs/generated/DECISIONS-INDEX.md）：

| # | 主題 | 拍板凍結 |
|---|---|---|
| #1 | unknown header | rust-api 忽略不認識的 header（如 apifoxToken）；base-web 不動 |
| #2 | auth route mode | dynamic（後端控 menu；`.env` `VITE_AUTH_ROUTE_MODE=dynamic`、ADAPT 軌道） |
| #3 | prod 路徑前綴 | `/api/*` 主流（front-nginx strip 轉發、`/api/metrics` 擋塊） |

**排程性拍板註記**：排程性結論（何時做／先做哪個，如 alova 端點包、obs 漸進排程、alt-login stub 排程）**不預載於本檔**——入波排程時逐筆重審立 ADR；重議既有排程性拍板仍走 §V.2 Amendment、**不得默改**。

---

## III. 軌道授權邊界

**跨軌道 fork-delta 執行紀律**（upstream 常態更新，本紀律使 fork 差異在 rebase 時可快速定位）：
- **修改型**（既有行語意被改變）：**原行註解保留**、緊鄰新行之上，含標記（如 `// [rev4-inline MW(a)] 原行: ...`）——rebase 衝突塊自含對照基準
- **新增型**（純插入新行／區塊／檔）：插入區塊以 `[rev4-inline ...+]` 標記圈界；新檔僅檔頭一行標記
- **標記統一含 `rev4-inline` token**：全 repo grep 即得完整 fork patch set（upstream 大重構時的災難重建索引）
- **rebase 同步紀律**：解衝突時，註解內「原行」同步更新為 upstream 現行版（防對照基準過時）

### III.1 預設可動軌道（無需額外授權）

| 軌道 | 範圍 | 紀律 |
|---|---|---|
| **BASE-WEB-ADAPT** | `.env*`＋`src/typings/api/` 新檔 | 新增為主、不改 inline；禁止刪除既有 type／field |
| **BASE-WEB-WRAPPER** | `src/service/api/rev4-*.ts` 新檔 | 一律新檔（`rev4-` 前綴）；不改既有 service 檔 |
| **RUSTAPI-SOURCE-ISOLATION** | rust-api 整棵樹 | 全新寫；前代受控參照不拷貝（§I.5） |

### III.2 ★ 需 constitution 顯式授權軌道（本檔已授權）

#### MODAL-WIRING ★ — 本檔授權七用途 (a)~(g)（皆 rev3 已落地驗證邊界、一次全授；**新用途 (h) 起走 Amendment**）

**邊界**：`base-web/src/views/manage/**` 內〔(a)~(f)；(g) 為樹外例外〕——
- **(a)** `// request` placeholder 接線：`modules/*-operate-{modal,drawer}.vue`（create/update）與 `index.vue` 的 delete/batchDelete handler
- **(b)** 業務頁操作按鈕 `hasAuth(<button_code>)` 可見性 gating：`index.vue` 操作鈕 `v-if` 與共用元件 `table-header-operation.vue` 的附加顯隱 prop
- **(c)** 同模式新權限 modal＋trigger：角色編輯區新增 `*-auth-modal.vue`（鏡像 menu/button-auth-modal）＋觸發鈕＋對應 i18n key——嚴格限「角色 × 某權限維度」runtime 編輯介面
- **(d)** 選單復原／re-parent 維運控制：`menu-operate-modal.vue` edit 模式 parentId selector＋「顯示已刪除」toggle＋restore 鈕＋對應 i18n key——嚴格限「選單樹復原／父層級調整」
- **(e)** 同 manage 範式新管理頁：`views/manage/<page>/index.vue`＋可選 `modules/*`（嚴格鏡像既有 user/role/menu 結構）、消費 rust-api 端點、含對應 route 與 i18n key——不擴張到任意新 UI／非 manage 頁／自訂佈局；可見性走 §I.2
- **(f)** 列表欄位排序掛載：column 定義加 naive-ui `sorter` props＋受控 `sortOrder`＋`@update:sorter` 綁定＋查詢參數 sort；於列表 view 工具列掛「清除排序」控制（有 `TableHeaderOperation` 的頁用其 `#suffix` slot、自有工具列的頁 inline）——嚴格限「列表排序」、**不改 `table-header-operation.vue` 元件本體**；配套新檔循 ADAPT/WRAPPER
- **(g)** 非-manage 頂層自助頁：`views/user-center/index.vue`＋可選 `modules/*`——登入者本人 profile 自助檢視／編輯＋改密碼＋驗證 UI 佔位，消費 auth-only 自助端點（operator＝本人）；`hideInMenu:true`、經頭像下拉入口、非 Casbin menu——**嚴格限「登入者本人自助」、不擴張到管理他人資料／任意新 UI**

**紀律**：
- 嚴格限七用途，絕不擴張到其他 inline 邏輯；第 (h) 種用途 → §V.2 Amendment
- **補完 vs 新能力判準**：既有授權頁內「單頁、純加、復用既有 wrapper、零新 key/元件/路由」四條件全中的 dispatcher 補完（如同頁補一種值型別的 render 控件分支）＝**用途補完、不 bump 本檔**；跨多頁新能力＝**須 Amendment**
  - **「零新 key」釋義**（ADR 0041）：指**新 i18n 命名空間／新元件／新路由等「面」級新增**；**不含**既有授權頁、既有子命名空間之下的**資料級 label key**（如 `page.manage.systemSettings.items.<newKey>` 三語譯文與型別鏡像）。★仍受約束：新增 top-level i18n 命名空間走 I18N-WIRING (ii)；route locale key 須隨建頁走；新元件／路由／跨頁能力仍須 Amendment；動 upstream 既有命名空間之下的 key 不在此釋義範圍。判準其餘三條件仍須全中。
- 每改一處在 spec 內紀錄（位置＋改動內容＋upstream 衝突風險評估）
- 共用元件改動 MUST 用附加 prop＋安全預設（不變既有呼叫端行為）

#### BASE-WEB-I18N-WIRING ★ — 本檔授權四範圍 (i)~(iv)（§I.3「msg＝i18n key」的接線載體；(iv)＝ADR 0028）

**邊界**（base-web，嚴格限以下三範圍）：
- **(i)** 請求攔截器 msg 翻譯接線：`src/service/request/` 的 msg 顯示點——**僅**為「wire `msg`（key）經 `$t` 譯為在地化文字再顯示」之最小接線；**不改**攔截器的碼分組／logout／refresh／retry 等控制流語意
- **(ii)** locale 字典 backend 命名空間：`src/locales/langs/*` 新增 top-level `backend` 命名空間（key 形＝`backend.<root>.<entity>.<condition>`）＋對應譯文——純新增、不改既有命名空間；zh-TW 首發 locale 的字典建置同循本範圍
- **(iii)** i18n typed-key Schema：`src/typings/app.d.ts` 的 `App.I18n.Schema` 擴充 `backend` 型別＋視需要翻譯 helper——純新增型／匯出
- **(iv)** zh-TW 首發 locale 完整建置（ADR 0028）：`src/locales/langs/zh-tw.ts` 全字典新檔（對齊 zh-cn 鍵集）＋註冊 inline（`src/locales/locale.ts` locale map、`src/typings/app.d.ts` `LangType` 加 `'zh-TW'`、`src/locales/naive.ts`、`src/locales/dayjs.ts`）＋語言選單（`src/store/modules/app/index.ts` `localeOptions` 加「繁體中文」）＋預設 locale（`src/locales/index.ts`／app store fallback `'zh-CN'`→`'zh-TW'`）——一次性建置授權、皆走 fork-delta `rev4-inline` 紀律

**紀律**：嚴格限四範圍；第五種範圍 → §V.2 Amendment；每改一處在 spec／plan 內紀錄；走 fork-delta `rev4-inline` 紀律。

#### BASE-WEB-AUTH-WIRING ★ — 本檔授權三接线 (a)~(c)（auth 刀 dynamic 落地＋alt-login stub 收斂；ADR 0031）

**邊界**（base-web，嚴格限以下三處 inline 接线，皆走 fork-delta `rev4-inline` 修改型帶 `原行:`＋fork-delta-lint 機器強制）：
- **(a)** 動態常數路由合併修：`src/store/modules/route/index.ts` 的 `initConstantRoute` dynamic 分支——`addConstantRoutes(data)` → `addConstantRoutes([...staticRoute.constantRoutes, ...data])`；嚴格限「dynamic 模式保前端 builtin 常數頁（login/404/403）、防 No-match-for-login 破口」，不改其他 route store 邏輯（rev3 010 已驗證；§II #2 dynamic 落地必要接线）
- **(b)** alt-login 表單 stub 接线：`src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue` 的 handleSubmit——假 success 改為呼叫 stub wrapper（WRAPPER 新檔）、回應經 `backend.*` i18n 顯示；嚴格限「三替代登入表單提交改真打後端 stub」，不改 pwd-login、不改表單結構（ADR 0029 帳實收斂）
- **(c)** captcha stub 接线：`src/hooks/business/captcha.ts` 的 getCaptcha——setTimeout 假動作改為呼叫 sendCaptcha stub（WRAPPER）、成功才啟動倒數；嚴格限「取驗證碼改真打 stub」（ADR 0029）

**紀律**：嚴格限三處接线；第四處 → §V.2 Amendment；每改一處在 spec／plan 內紀錄（位置＋改動＋upstream 衝突風險）；走 fork-delta `rev4-inline` 紀律＋fork-delta-lint 機器強制。

#### BASE-WEB-LOGOUT-UX-WIRING ★ — 本檔授權兩用途 (i)~(ii)（session 刀 logout 伺服器端撤銷＋閒置登出 UX；ADR 0034）

**邊界**（base-web，嚴格限以下兩處，皆走 fork-delta `rev4-inline` 修改型帶 `原行:`＋fork-delta-lint 機器強制）：
- **(i)** logout server-call 接线：`src/layouts/modules/global-header/components/user-avatar.vue` 主動登出——`authStore.resetStore()` 前先呼 `POST /auth/logout`（帶 refresh 憑證）；嚴格限「登出改先撤伺服器端會話」，不改 auth store 其他邏輯。
- **(ii)** logoutCodes 靜默分支登出前 toast：`src/service/request/index.ts`＋`src/service-alova/request/index.ts` onBackendFail 的 `logoutCodes`(8888) 分支——`handleLogout()` 前顯輕量 toast（`$t(backend.auth.session.reLogin)`）；嚴格限「靜默登出前顯 toast」、不改碼分組/logout/refresh 其餘控制流語意。

**紀律**：嚴格限兩用途；第三用途 → §V.2 Amendment；每改一處在 spec／plan 內紀錄（位置＋改動＋upstream 衝突風險）；走 fork-delta `rev4-inline` 紀律＋fork-delta-lint 機器強制。

#### BASE-WEB-LOGIN-CAPTCHA-WIRING ★ — 本檔授權一用途 (i)（節流刀 CAPTCHA 軟區的登入表單接线；ADR 0040）

**邊界**（base-web，嚴格限以下一處，走 fork-delta `rev4-inline` 紀律＋fork-delta-lint 機器強制）：
- **(i)** 密碼登入表單的圖形驗證碼接线：`src/views/_builtin/login/modules/pwd-login.vue` 於收到「需要驗證碼」回應（`2222`＋`auth.login.captchaRequired`）時條件渲染驗證碼圖與輸入欄；支援點圖換題、帳號名變更時重新取題、答錯後自動重取新題（提交即消耗、舊題已失效）。**含其資料取得所需之最小 store/service 接线**——使 pwd-login 能取得後端 `msg` 以區分 `locked` 與 `captchaRequired`（兩態同為 `2222`、僅 `msg` 相異，而 `authStore.login` 現吞掉 `msg`）。

**紀律**：
- 嚴格限此一用途；第二用途 → §V.2 Amendment。
- ★**不改攔截器碼分組／logout／refresh／retry 控制流語意**（`2222` 走既有一般錯誤提示通道）；**`.env` 三個碼分組清單不動**。
- 修改型帶 `原行:`：`<script>` 區用 `//`、★`<template>` 區用 `<!-- [rev4-inline …] 原行: … -->`；新增型走圈界標記。
- 新 typing／service wrapper 走既有預設軌道（ADAPT 新 `.d.ts` declaration merging、WRAPPER `rev4-*.ts` 新檔），**不動凍結的 `typings/api/auth.d.ts`**。
- 每改一處在 spec／plan 內紀錄（位置＋改動＋upstream 衝突風險）。

---

## IV. Compliance Check（spec-kit `/speckit-plan` 用）

`/speckit-plan` 必須對照本 constitution 逐項 yes/no：

1. **此 plan 是否違反 §I.1 base-web 為權威紀律？** rust-api 是否未提供 base-web 用到的對應 endpoint？
2. **此 plan 是否動到 base-web inline？** 若是、屬 §III.2 哪個用途／範圍？授權邊界內？是否依 fork-delta 紀律（修改型原行註解／新增型圈界、`rev4-inline` token）？
3. **此 plan 涉及 menu 顯示是否走 Casbin enforce？**（§I.2；demo menu 是否進 seed 而非隱藏？）
4. **此 plan 的 wire 設計是否對齊 §I.3 權威序與不變式？**（envelope／逐欄位 id 型／13 碼矩陣／msg=key；mock 僅補充 fixture）
5. **此 plan 是否從前代 source 拷貝 code？** 若是、屬 §I.5 例外清單嗎？參照處是否觸發防回歸條款？
6. **此 plan 是否抵觸 §II 拍板？** 任一拍板需改變、必先走 Amendment
7. **此 plan 是否觸及 §III ★ 軌道？** 若是、在授權邊界內？屬「補完」還是「新能力」（§III.2 判準）？
8. **此 plan 是否新建業務表（create migration）？** 若是，是否含 §I.6 六審計欄（建表即帶、無 retrofit）？append-only／join 表是否依變體處理？
9. **此 plan 是否觸及 §I.7 已入憲的行為島？** 若是、各 invariants 是否保持？是否用 state-machine 鏡頭設計（非 CRUD 格子）？若屬「該入憲而未入憲」的新行為島、是否隨本刀排入 Amendment？

任一檢查不通過 → plan 須回 brainstorm 或申請 Amendment（§V.2）。

註：本題組承接 rev3 九題制；「不增列 push/merge 自查題」為已封案事項、日後不再議（該紀律由 CLAUDE.md 硬禁令＋agent prompt 烤入承載）。

---

## V. Governance

### V.1 凍結權威性

本 constitution 為 rev4 的**凍結權威**；與其他文件衝突時**以本檔為準**。文件權威鏈：

> constitution（凍結權威）＞ ADR accepted（拍板全文；索引＝docs/generated/DECISIONS-INDEX.md）＞ 活書 docs/arc42/ARCHITECTURE.md（as-built 敘事）＞ docs/generated/（機器鏡像）

本檔與 accepted ADR 不一致＝Amendment 未同步的程序錯誤，以本檔為準並立即補同步。

### V.2 Amendment 流程

1. **提案**：立 ADR draft（背景／決定／後果；註明改本檔哪一節）
2. **討論**：user 親決（本檔內容皆為 user 拍板項，Claude 不主動 amend）
3. **凍結**：ADR 轉 accepted＋更新本檔對應段＋bump version（§V.3）
4. **commit**：獨立 commit `docs(constitution): amend <條目>`（憲法改動＋ADR 同 commit）＋`docs-sync generate`

### V.3 Version 規則

- **MAJOR**（2.0.0）：鐵紀律（§I 原則）改變、§I.7 方向性不變式反轉、§II 拍板撤回、★ 軌道授權撤銷
- **MINOR**（1.1.0）：新拍板固化（§II 加項）、軌道授權邊界擴展（新用途／新範圍）、新增 ★ 軌道、**行為島隨刀進場（§I.7 填充）**、已入憲 invariant 細項調整
- **PATCH**（1.0.1）：文字校正、釐清、reference 更新、Compliance Check 增補

---

**Version**: 1.4.1 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-10

**Amendment log**:
- 1.4.1（2026-07-10）：§III.2「補完 vs 新能力判準」加「零新 key」釋義——指新 i18n 命名空間／新元件／新路由等「面」級新增，不含既有授權頁既有子命名空間下的資料級 label key（ADR 0041）；PATCH（§V.3「文字校正、釐清」）——觸發＝007-login-throttle `/speckit-analyze` 的 C1 finding（CRITICAL）＋user 親決。★非授權擴展：判準其餘三條件與其他軌道邊界不受影響。
- 1.4.0（2026-07-10）：§I.7 行為島進場——島 E 登入失敗節流（E1 真相分層與 fail 方向〔含唯一 fail-closed 例外〕／E2 防枚舉延伸／E3 審計邊界／E4 captcha gate 與硬鎖優先；ADR 0037，負快取層 ADR 0038 supersede 0016）＋新增 ★BASE-WEB-LOGIN-CAPTCHA-WIRING 軌道一用途〔(i) 密碼登入表單圖形驗證碼接线，含其資料取得所需之最小 store/service 接线〕（ADR 0040）；MINOR（§V.3「行為島隨刀進場」＋「新增 ★ 軌道」）——觸發＝007-login-throttle plan Constitution Check Q2/Q7/Q9。
- 1.3.0（2026-07-06）：§I.7 行為島首度填充——島 A single-session／B token rotation／C denylist／D 閒置sliding refresh（ADR 0033、supersede 0030）＋新增 ★BASE-WEB-LOGOUT-UX-WIRING 軌道兩用途〔(i) logout server-call 接线／(ii) logoutCodes 靜默分支 toast〕（ADR 0034）；MINOR（§V.3「行為島隨刀進場」＋「新增 ★ 軌道」）——觸發＝006-session-lifecycle plan Constitution Check Q2/Q7/Q9。
- 1.2.0（2026-07-05）：新增 ★BASE-WEB-AUTH-WIRING 軌道（ADR 0031；授權 auth 刀三處 base-web inline 接线 (a) route store 常數合併修／(b) alt-login 三表單 stub／(c) captcha stub；MINOR 新增 ★ 軌道、§V.3）——觸發＝005-auth-login plan Constitution Check Q2/Q7。
- 1.1.0（2026-07-05）：★BASE-WEB-I18N-WIRING 加 (iv) zh-TW 首發 locale 完整建置授權（ADR 0028；MINOR 軌道授權邊界擴展、§V.3）——觸發＝004-system-settings plan Constitution Check Q7。
