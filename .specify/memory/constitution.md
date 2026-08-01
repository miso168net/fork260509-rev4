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
- constantRoutes（login／404／403）前端寫死、與 menu 無關、不動；constant route 集合可經 §III.2 授權新增（如 (k) 強制改密頁）——builtin 三頁不動與 Casbin 豁免語意不變

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
- **B append-only 日誌**（例：三 log 表）：只 `created_at` NN（＋operator 類 domain 欄）；**無 soft-delete、無 update、不可竄改**；MUST NOT 加 `updated_*`/`deleted_*`（retention 水平線刪除不屬「竄改」——權威釋義＝§I.7 島 J3）
- **C join／狀態機**（例：user-role join＝零審計硬刪；token 表＝僅 `created_at`＋status 狀態機）；★變體 C upsert 釋義（020、ADR 0085 權威釋義）：1:1 已驗證值衛星表（`sys_user_email_verify`）之 upsert 刷新＝重驗事件覆寫、`verified_at` 即其時戳、不設 `updated_*`——「成對」條款不因此觸發
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
  - **E2 防枚舉延伸**：判定鍵＝所送出帳號名原文（不存在帳號同計、同鎖、同要 captcha），其正規化 MUST 與帳號身分解析的正規化嚴格一致；鎖定與 captcha 要求皆回 `2222` ＋靜態一般化訊息，MUST NOT 洩觸發維度、剩餘時間、帳號存在性。★**射程釐清（008、ADR 0044）**：此「判定鍵＝帳號名原文、不依賴來源 IP」之射程為**帳號維度的判定鍵**；來源維度（島 F）為獨立並列維度、兩者不衝突（FR-030）。
  - **E3 審計邊界**：**僅**被密碼雜湊實際驗證的登入終局落恰一列；L1 命中短路、L2 再判鎖、captcha-gate 拒絕、輸入形制超限 MUST NOT 落稽核列，量級訊號走觀測層麵包屑（非稽核表、best-effort）。鎖的最長存續＝一個時窗（非 L1 TTL）。
  - **E4 captcha gate 與硬鎖優先**：軟區要求 captcha；challenge MUST 綁定帳號名、**提交即消耗**（單次標記寫入先於答案比對）、且其答案 MUST NOT 可自 challenge 本身還原。缺／錯／過期／重放之 captcha 嘗試 MUST NOT 計入失敗數（落列規範見 E3）。硬鎖優先於 captcha——鎖中附有效 captcha 亦不受理、且該 captcha 不被消耗。
- **島 F — IP 存取控制閘＋信任錨＋來源維節流**（008、ADR 0043 真實 IP 還原／0044 本島／0045 來源維節流／0046 region）
  - **F1 判定序與集合語意**：閘門判定 MUST 依固定序——①健康/觀測放行 ②請求上下文缺席放行 ③結構性豁免網段放行 ④命中放行規則放行 ⑤命中阻擋規則拒絕（reuse `5003`→403）⑥其餘放行；規則集為 any-match 集合語意、**白＞黑＞default-allow、無順序化規則鏈或優先權欄**。
  - **F2 真相分層**：DB 規則表為真相、記憶體 ArcSwap 判定面（每請求零 DB/Redis）；真相暫不可讀時判定面**沿用上一份已知良好規則集**（keep-last-good、不清空）。
  - **F3 fail-OPEN 與唯一例外**：全鏈 fail-OPEN（信任模型壞損→全空 all-direct、規則載入失敗→空集、快取/門鈴/GeoIP 故障→放行或降級）；**唯一 fail-closed 例外＝寫端自鎖拒寫**。每次降級 MUST 發結構化告警。★**入憲後 fail-OPEN 方向反轉＝MAJOR。**（來源維節流的解鎖標記讀故障 fail-closed 屬島 E1 降級⑤的既有例外、對稱擴充至來源維、非島 F 新例外。）
  - **F4 信任錨為唯一輸入、同源對稱**：來源維度一切機制（閘門、來源維節流、稽核來源）的位址輸入 MUST 為信任錨還原結果；信任集與跳過集 MUST **同源對稱**導出（含通道來源集與驗證閘出口集）。CDN 位置錨的傳輸層背書為承重部署前提（ADR 0043、與 DNAT 同級）。
  - **F5 放行跳節流只認顯式規則**：命中**顯式**放行規則的來源跳過來源維節流（含快取層）；**結構性豁免網段 MUST NOT 跳節流**（結構豁免只豁免阻擋、不豁免節流）。來源維節流計數下界只取兩源（時窗起點＋解鎖標記、**拔 reset-on-success**、ADR 0045）。
- **島 G — casbin 授權治理**（009、ADR 0048 本島／0049 歸檔 role_id／0050 明細通道）
  - **G1 真相唯一與同步失敗契約**：授權真相＝DB 政策表；授權變更與其操作稽核 MUST 同一交易落地、絕不走判定引擎管理 API 寫面（DB-first）；判定面由真相全量重載導出（Applied 含空 diff 才觸發、Rejected/NoOp/NotFound 不觸發）。★同步失敗契約：重載 MUST 以「**重建成功才 swap**」實現、絕不對 live 判定面就地 clear-then-load；失敗→**保留上一份已知良好判定面**（絕不空窗或半載）＋結構化告警＋有界重試，耗盡仍失敗→維持舊面持續告警。★方向反轉（同步失敗改為清空／全 deny）＝MAJOR。
  - **G2 受保護拒絕**：撤銷集觸及 protected 政策→整批拒絕、零變更（任何寫之前判定）＋結構化明細；un-protect／re-protect 經一般管理介面永不提供（防鎖死 by-design；保護集變更屬 seed 基線層級決策）。
  - **G3 撤銷必歸檔**：revoke＝archive-move（完整快照＋來源角色識別 role_id＋reason 區分）、grant＝INSERT 補齊治理欄（protected=false＋created_at/by）；刪角色 MUST 同交易全維連動歸檔（含 protected 列、reason=`role_soft_delete`）；`role_soft_delete` 列 MUST NOT 可手動復原；角色刪除單向、無 role restore。
  - **G4 刪除守門與批次原子**：刪除依固定序三層守門（①seeded ②in-use ③self-role）；批次逐項驗證、任一違規**整批拒**（no-partial）、單一交易。
  - **G5 復原同實例與全端點鎖序**：一切向現役授權寫入、或改動角色活性／啟用狀態的寫端（三維寫入、授權復原、刪除、停用）MUST 同交易 `FOR UPDATE` 鎖標的角色列、**鎖內重判前提**後才落寫（lock-then-redecide——與島 B2 同範式的授權面對應〔類比引用、L-075；B2 射程仍限 token 面〕、永不信 pre-read）；復原判定＝reason≠`role_soft_delete` **且** 現存同 code 活角色 `id == 歸檔列 role_id`（同實例；NULL→不可復原、誠實退化）。★未來 `sys_user_role` 指派寫端落地時 MUST 同納本鎖序。
- **島 H — 選單域生命週期與授權連動**（010、ADR 0051 總綱／0052 Amendment）
  - **H1 選單域寫入序列化域**：選單樹五寫端（新增／編輯／刪除／批次刪除／復原）與選單維、按鈕維授權寫端（含授權回收桶復原之選單／按鈕維分支）MUST 於單一序列化域內互斥執行（DB 交易級 advisory 域鎖為載體、key 值留活書）；每一寫端 MUST 於域內鎖定標的並**重驗全部守門前提後才落寫**（lock-then-redecide、永不信 pre-read；與島 G5／B2 同範式）。端點維授權寫入不涉選單域、不屬本域。★方向反轉（拆散序列化域、改回無域逐列鎖或無鎖 pre-read）＝MAJOR。
  - **H2 同鍵重建零繼承**：選單軟刪 MUST 同交易將其選單維授權（跨全角色）連動歸檔（reason=`menu_soft_delete`）；該選單「獨有」按鈕代碼（刪除後不再屬任何未刪選單）之按鈕維授權亦同交易歸檔；編輯移除按鈕代碼致其全域絕版時同理（reason=`menu_button_removed`）。此三類 reason 之歸檔列 MUST NOT 可手動復原（gate enforce 於復原權威判定）。同路由鍵重建之新選單 MUST NOT 經任何路徑（現役殘留、回收桶復原）繼承舊實例授權（單向不變式，與島 G3 撤銷必歸檔同源、選單實體側對偶）。
  - **H3 樹結構不變式**：選單樹恆無環（改父層 MUST 過防環檢查）；活性子項 MUST NOT 掛於已軟刪父層之下；受保護種子選單 MUST NOT 可刪；存在未刪子項（不論啟用停用）之目錄 MUST NOT 可刪；批次刪除逐項驗證、任一違規**整批拒**（no-partial、單一交易、child-first 拓撲序）。此對偶島 G4 之選單實體側。
  - **H4 不可變錨欄與治理域／顯示域分層**：`route_name`（授權列 v1 錨／i18n 錨）與 `menu_type` 建後不可變（寫端 MUST 顯式拒變更、MUST NOT 靜默忽略）；選單讀端分兩域——**治理域**（授權候選與映射）以「未軟刪」全集為準（含停用）、**顯示域**（使用者可見性）以「啟用且未軟刪」為準；停用 MUST NOT 使全量替換語意誤撤停用選單的授權（停用＝暫時下架、非撤銷）。
  - **H5 復原不回灌**：選單復原 MUST 於序列化域內鎖定並重驗守門（同路由鍵活性衝突／父層未刪）；復原 MUST NOT 回灌任何授權——復原後選單零授權，可見性一律經授權面板重新勾選下放（與新增選單之兩步流一致）。
- **島 I — 使用者域治理**（011、ADR 0053 總綱／0054 密碼政策；I6＝015、ADR 0067）
  - **I1 統一序列化與固定鎖序**：一切以既有使用者為標的之使用者域寫端（含撤 session 者：更新、刪除、批刪、重設密碼、踢除、復原、會話策略）MUST 於交易起手取得與登入／換發同源的每使用者序列化鎖（DB 交易級 advisory 鎖、key＝使用者識別、與 login/refresh 共鎖）；域內固定鎖序 MUST 為①標的使用者列 `FOR UPDATE`（復原用已刪列版）→②角色列（僅指派路、識別升序、複用角色域鎖讀）→③指派列寫入，禁反向；一切守門判定 MUST 鎖內重驗（lock-then-redecide、永不信 pre-read；與島 G5／B2／H1 同範式）。新增使用者豁免每使用者鎖（新識別對並發不可見；並發同名保護＝帳號名活性唯一約束）。帳號名活性 partial-uniq 索引為復原同名衝突守門之顯式前提。★方向反轉（拆散統一序列化、改回無鎖 pre-read）＝MAJOR。
  - **I2 撤銷連動同交易＋權威優先＋登入鎖內重驗**：停用／刪除／改密 MUST 同交易撤銷標的使用者全部既有 session（撤銷類、靜默）〔★釋義：操作者＝標的之改密＝撤銷全部**其他** session、保留當前操作 session（不自斷）；出處 011 FR-025／ADR 0055 不變式〕；踢除＝踢除類（阻斷）；兩類體驗碼 MUST NOT 互換。動作序 MUST 權威優先（業務寫＋session 作廢＋稽核同交易落定→commit→失效廣播 best-effort、存活時間覆蓋換發憑證壽命）；即時性契約＝廣播成功即時、失敗殘留窗上界 access token 壽命（換發期活性守門兜底、沿島 C fail-open），MUST NOT 為此新增每請求活性判定。登入流程 MUST 於序列化鎖內、發 token 前重讀標的列並重驗活性與密碼雜湊（與驗證階段所讀一致、純比對不重跑雜湊），任一不符 MUST 中止不發 token；換發流程 MUST 於換發憑證列鎖內重驗使用者活性（不另重驗密碼雜湊）；被合法撤銷者換發 MUST 靜默拒絕、MUST NOT 誤判為憑證盜用。★方向反轉（拔登入鎖內重驗、改廣播優先）＝MAJOR。
  - **I3 seed 帳號結構保護**：前三個種子帳號 MUST 不可刪；第一個（Super）MUST 恆禁停用、恆禁解除其超管角色指派（不因操作者身分而異）——系統恆有至少一個活躍且啟用的超級管理員（結構保證、不需動態計數）；Super MAY 被踢除、被重設密碼。操作者 MUST NOT 刪除／停用／踢除自己、MUST NOT 變更自己的角色指派。
  - **I4 刪除清指派＋復原不回灌**：使用者軟刪 MUST 同交易硬刪其全部角色指派列（零幽靈掛載、角色域掛載計數守門保持誠實）；復原 MUST NOT 回灌任何指派（復原後零角色、須重新指派）、狀態保留刪除前原值；同帳號名重建之新使用者 MUST NOT 經任何路徑繼承舊實例角色。批次刪除逐項驗證、任一違規（含已刪識別）**整批拒**（fail-fast、單一交易、識別去重升序取鎖）。
  - **I5 密碼政策單一驗證點＋密碼三重不洩**：密碼政策驗證 MUST 為單一驗證點（建帳與重設共用、零分叉）、政策鍵單一快照讀取；長度單位＝字元、另加固定位元組上界 ≤登入端形制上限；「禁止密碼與帳號名相同」＝大小寫不敏感相等。密碼明文與雜湊 MUST NOT 洩漏於任何面：承載密碼之 DTO 除錯輸出 MUST 遮蔽（不得預設印出）；操作稽核 payload MUST NOT 含密碼明文／雜湊／會話識別；API 回應 MUST NOT 含密碼與會話識別（列表逐欄構造、不序列化原始列）；密碼雜湊 MUST NOT 於持有列鎖期間計算。★方向反轉（拆單一驗證點、拔遮蔽）＝MAJOR。
  - **I6 密碼經手與首登強制換密**（015、ADR 0067）：經手判定單一規則——標的名下存在任一筆「操作者≠標的」經手記錄→登入後強制換密；判定 MUST 登入後動態求值（非簽發時快照）且收斂為單一純函式 seam 三處共用（身分投影／API 硬閘／測試）、MUST NOT 各處內聯分叉。寫入規則 MUST 與密碼更新同交易原子：他人設密＝upsert 該（標的×操作者）對；本人改密＝全刪標的名下全部經手記錄＋寫一筆自改記錄（「全刪」範圍恆＝標的名下、絕非操作者名下）。設密冷卻＝端點固有規則——排各端點既有拒因全過之後、鎖內、UPDATE 前，MUST NOT 入 I5 單一驗證點；一體適用零例外（含強制換密狀態下本人改密）、拒絕提示攜剩餘秒數。強制換密硬閘 MUST 僅放行改密必需白名單（改密／政策讀取／本人身分／路由查詢；登出與憑證換發結構性不經閘）且 MUST 同時覆蓋一般已認證與帶權限管理端點。★硬閘每請求 EXISTS 判定與島 I2「MUST NOT 為此新增每請求活性判定」之射程區隔：該禁令限撤銷即時性（session 活性）、custody 閘＝改密強制判定、不在其射程。
- **島 J — 稽核域 reporting 與 retention**（012、ADR 0057 四源讀端／0058 purge 執行面／0059 PII 打碼／0060 access-log 寫入端）
  - **J1 讀端 read-only＋僅超管**：稽核查詢面（操作日誌／存取軌跡／登入嘗試／會話事件四源）MUST 純唯讀（handler 零業務寫入、零狀態變更；存取軌跡由統一記錄層承載、非查詢職責）且僅授權超級管理員；回應逐欄構造、不序列化原始列；資料源增減＝新 ADR。
  - **J2 access-log 寫入 fail-open**：存取軌跡記錄 MUST best-effort——寫入故障僅結構化告警、MUST NOT 影響業務請求成敗與延遲語意（與島 E1／F3 同向）；MUST NOT 記錄請求內文與查詢字串；未認證請求 MUST NOT 落列（構造保證＝記錄層位於認證下游＋created_by NOT NULL）；位址輸入取信任錨（島 F4）。★方向反轉（改 fail-closed／記 body・query）＝MAJOR。
  - **J3 purge 唯一形狀＝時間水平線**：稽核資料唯一刪除路徑＝表白名單×天數（下限守門）之水平線整段刪除——構造上禁挑列／任意條件刪；每次 purge MUST 同交易自落操作稽核（含刪除筆數、0 列照落）；操作日誌源 MUST 固定豁免 PURGE 類型稽核列（後設證據永久保留）。水平線 retention 刪除不屬 §I.6 變體 B 所禁之「竄改」——本條為其權威釋義。★方向反轉（開挑列刪、拆自記／豁免）＝MAJOR。
  - **J4 PII 顯示打碼單點**：稽核讀端 payload 個資遮蔽 MUST 於後端序列化單點完成（前端 MUST NOT 經手原值）；遮蔽鍵清單＝常數（擴充＝改常數＋補測試）；落庫面白名單（密碼雜湊／會話識別永不入列、島 I5）為政策本體、不回溯清洗。
  - **J5 解鎖稽核先於生效**：手動解鎖動作序 MUST 為操作稽核於權威儲存落定成功後才執行生效步；稽核寫入失敗 MUST 中止生效——「生效但零稽核列」構造不可達（生效步失敗後重試多記嘗試列＝明文接受）。

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

#### MODAL-WIRING ★ — 本檔授權十一用途 (a)~(k)（(a)~(g)＝rev3 已落地驗證邊界一次全授、(h)＝011 Amendment、(i)＝012 Amendment、(j)＝B-104 Amendment、(k)＝015 Amendment；**新用途 (l) 起走 Amendment**）

**邊界**：`base-web/src/views/manage/**` 內〔(a)~(f)、(h)~(i)；(g)(j) 為樹外例外；(k) 跨樹內外〕——
- **(a)** `// request` placeholder 接線：`modules/*-operate-{modal,drawer}.vue`（create/update）與 `index.vue` 的 delete/batchDelete handler，及同頁 `modules/*-auth-modal.vue` 既有 placeholder 接線；附屬模板行為小修（如 search reset 補 emit('search')）同屬本用途（ADR 0048）；create/update 接線所必要之表單控件屬本用途（如 user drawer add 模式密碼欄＋政策提示、edit 模式 session_policy 選擇器——payload 必要欄之輸入載體），仍限既有 operate-modal/drawer 檔內、不含新 modal（ADR 0053）
- **(b)** 業務頁操作按鈕 `hasAuth(<button_code>)` 可見性 gating：`index.vue` 操作鈕 `v-if` 與共用元件 `table-header-operation.vue` 的附加顯隱 prop
- **(c)** 同模式新權限 modal＋trigger：角色編輯區新增 `*-auth-modal.vue`（鏡像 menu/button-auth-modal）＋觸發鈕＋對應 i18n key——嚴格限「角色 × 某權限維度」runtime 編輯介面
- **(d)** 選單／使用者／IP 規則復原、re-parent 維運控制：`menu-operate-modal.vue` edit 模式 parentId selector＋`views/manage/menu/index.vue` 與 `views/manage/user/index.vue` 的「顯示已刪除」列表切換（toggle）＋逐列 restore 鈕＋`views/manage/ip-rule/index.vue` 混排清單（含已刪列顯示與狀態欄辨識）之搜尋卡「狀態」三態過濾控件（現役／已刪除／全部——承載已刪視圖切換、取代 toggle 形）＋逐列 restore 鈕＋對應 i18n key——嚴格限「選單樹復原／父層級調整／使用者回收桶復原／IP 規則回收桶復原」
- **(e)** 同 manage 範式新管理頁：`views/manage/<page>/index.vue`＋可選 `modules/*`（嚴格鏡像既有 user/role/menu 結構）、消費 rust-api 端點、含對應 route 與 i18n key——不擴張到任意新 UI／非 manage 頁／自訂佈局；可見性走 §I.2
- **(f)** 列表欄位排序掛載：column 定義加 naive-ui `sorter` props＋受控 `sortOrder`＋`@update:sorter` 綁定＋查詢參數 sort；於列表 view 工具列掛「清除排序」控制（有 `TableHeaderOperation` 的頁用其 `#suffix` slot、自有工具列的頁 inline）——嚴格限「列表排序」、**不改 `table-header-operation.vue` 元件本體**；配套新檔循 ADAPT/WRAPPER
- **(g)** 非-manage 頂層自助頁：`views/user-center/index.vue`＋可選 `modules/*`——登入者本人 profile 自助檢視／編輯＋改密碼＋信箱驗證流（發碼／回填驗證／解除綁定／其 captcha 取題），消費 auth-only 自助端點（operator＝本人）＋對應 i18n key（鍵集＝1.12.0 敘明之 30 鍵＋020 信箱驗證流新鍵集）；`hideInMenu:true`、經頭像下拉入口、非 Casbin menu——**嚴格限「登入者本人自助」、不擴張到管理他人資料／任意新 UI**
- **(h)** manage 頁維運動作：`views/manage/user/index.vue` 頁首維運 modal 觸發鈕＋net-new `modules/user-unlock-modal.vue`（登入解鎖：dimension 選擇＋目標輸入→既有 unlockLogin 端點）＋operate 欄維運動作（kick／reset-pwd、NDropdown 收納）＋對應 i18n key——嚴格限「使用者頁既有後端維運端點之觸發 UI」、不擴張到新後端能力／任意新 UI（ADR 0053）
- **(i)** 稽核中心唯讀報表頁：`views/manage/audit/index.vue` 一頁多分頁（NTabs 四源）唯讀報表佈局＋`modules/audit-search-*.vue` 搜尋卡（含時間區間選擇控件、全庫首例）＋`modules/audit-purge-modal.vue`（天數輸入＋二次確認→purge 端點）＋對應 route 與 i18n key——嚴格限「稽核四源唯讀查詢與其清理維運觸發 UI」、不擴張到任意新 UI／寫端管理功能（ADR 0057/0058）
- **(j)** layout 上游缺陷修補：`src/layouts/modules/**` 與其配套樣式（`src/styles/css/transition.css`）之可重現上游 bug workaround——嚴格限「修復有重現法與行為對照記錄之上游缺陷、一案一 ADR」、**不擴張到 layout 重設計／新 UI／行為性新功能**（ADR 0066）
- **(k)** 首登強制換密控制流：`views/_builtin/force-change-pwd/index.vue` 強制改密頁（constant route、hideInMenu、免曝光鏈）＋`build/plugins/router.ts` constantRoutes 名單觸點（修改型）＋`src/router/guard/route.ts` 全域攔截控制流（isLogin＋needChangePwd→改寫導向強制頁、置於路由存在性解析之先）＋`src/store/modules/auth/*` needChangePwd 承載 inline＋`views/manage/user/index.vue` operate 欄「密碼」動作與其隨機專用浮層觸發（(h) 維運動作同型擴充、沿用既有「重設密碼」按鈕碼）＋`views/manage/user/modules/user-operate-drawer.vue` add 密碼欄旁隨機鈕（(a) 接線必要控件同型）＋`views/user-center/modules/password-card.vue` 隨機鈕（(g) 本人自助射程確認）＋`src/components/` 產密浮層共用元件（新檔、新增型圈界——十用途原不涵蓋 src/components/、本款顯式授權）＋對應 i18n key——嚴格限「首登強制換密＋隨機產密」控制流與其掛載點、不擴張到任意新 UI／新攔截器控制流／其他 guard 邏輯（ADR 0067）

**紀律**：
- 嚴格限十一用途，絕不擴張到其他 inline 邏輯；第 (l) 種用途 → §V.2 Amendment
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

#### BASE-WEB-LOGIN-CAPTCHA-WIRING ★ — 本檔授權二用途 (i)~(ii)（(i)＝節流刀 CAPTCHA 軟區登入表單接线、ADR 0040；(ii)＝011 密碼登入表單規則放寬、ADR 0053）

**邊界**（base-web，嚴格限以下二處，走 fork-delta `rev4-inline` 紀律＋fork-delta-lint 機器強制）：
- **(i)** 密碼登入表單的圖形驗證碼接线：`src/views/_builtin/login/modules/pwd-login.vue` 於收到「需要驗證碼」回應（`2222`＋`auth.login.captchaRequired`）時條件渲染驗證碼圖與輸入欄；支援點圖換題、帳號名變更時重新取題、答錯後自動重取新題（提交即消耗、舊題已失效）。**含其資料取得所需之最小 store/service 接线**——使 pwd-login 能取得後端 `msg` 以區分 `locked` 與 `captchaRequired`（兩態同為 `2222`、僅 `msg` 相異，而 `authStore.login` 現吞掉 `msg`）。
- **(ii)** 密碼登入表單前端規則放寬：`src/views/_builtin/login/modules/pwd-login.vue` 的 REG_PWD／REG_USER_NAME 表單規則降為 required-only（後端政策為唯一權威守門；消滅「政策合法密碼／帳號名被前端硬正則擋死＝設得進登不進」）——嚴格限「規則放寬」、不改表單結構／不改攔截器控制流／修改型帶 `原行:`（ADR 0053）

**紀律**：
- 嚴格限此二用途；第三用途 → §V.2 Amendment。
- ★**不改攔截器碼分組／logout／refresh／retry 控制流語意**（`2222` 走既有一般錯誤提示通道）；**`.env` 三個碼分組清單不動**。
- 修改型帶 `原行:`：`<script>` 區用 `//`、★`<template>` 區用 `<!-- [rev4-inline …] 原行: … -->`；新增型走圈界標記。
- 新 typing／service wrapper 走既有預設軌道（ADAPT 新 `.d.ts` declaration merging、WRAPPER `rev4-*.ts` 新檔），**不動凍結的 `typings/api/auth.d.ts`**。
- 每改一處在 spec／plan 內紀錄（位置＋改動＋upstream 衝突風險）。

#### BASE-WEB-DEVPROXY-WIRING ★ — 本檔授權三處 (i)~(iii)（IP 閘刀 S0 dev 反代拓樸修正；ADR 0042）

**邊界**（base-web，嚴格限以下三處，皆走 fork-delta `rev4-inline` 紀律＋fork-delta-lint 機器強制）：
- **(i)** 同源前綴：`src/utils/service.ts` `createProxyPattern` 預設值 `/proxy-default`→`/api`（修改型帶 `原行:`）——dev 的 API 請求與 prod 同形（同源相對前綴、單跳）。
- **(ii)** proxy target 推導：`build/config/proxy.ts` target 由 `item.baseURL` 改讀新 env key `VITE_PROXY_TARGET`（值＝`http://rust-api:8080`；修改型帶 `原行:`）——vite dev proxy 直指 rust-api、消除雙穿 front-nginx 迴圈（L-125）。
- **(iii)** env key 宣告：`src/typings/vite-env.d.ts` 新增 `VITE_PROXY_TARGET` 宣告（新增型圈界）——upstream 既有檔、不落 ADAPT，須本軌道顯式授權（ADR 0042＝env key 案）。

**紀律**：嚴格限此三處、嚴限「dev 反代拓樸」用途；第四處／其他用途 → §V.2 Amendment；`.env`／`.env.test`／`.env.prod` 值變更走既有 ADAPT、不屬本軌道射程；每改一處在 spec／plan 內紀錄（位置＋改動＋upstream 衝突風險）。

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

**Version**: 1.15.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-31

**Amendment log**:
- 1.15.0（2026-07-31）：§III.2 MODAL-WIRING **(g) 擴字串**——「＋驗證 UI 佔位」→「＋信箱驗證流（發碼／回填驗證／解除綁定／其 captcha 取題）」＋鍵集敘明擴至 020 信箱驗證流新集合（1.11.0/1.12.0 擴字串判例第五度；(g)「登入者本人自助、auth-only 端點」語意不動）＋§I.6 **變體 C upsert 釋義句**（1:1 已驗證值衛星表 sys_user_email_verify 之 upsert 刷新＝重驗事件覆寫、verified_at 即其時戳、不設 updated_*——比照 1.10.0 J3 對變體 B 之權威釋義形；020 plan 三鏡頭對抗式驗證判「m011 同形」單獨引法不足、本句即補強）。ADR 0085（帳號 email 驗證＝驗證即提交×已驗證值衛星表×partial unique——B-028 信箱半邊選型；十決策含 clarify 四拍板〔解除綁定／captcha 前置機器語境欄／admin 格式守門無值未變豁免／冷卻拒因攜秒數〕與 plan 校正〔節流原子先佔／updateUser 三態契約〕）／ADR 0086（SMTP 寄信基建＝lettre 0.11.22×設定全靜態 env×mailpit dev 驗收）隨本 Amendment 轉 accepted；MINOR（§V.3「軌道授權邊界擴展」＋「已入憲 invariant 細項調整」）——觸發＝020-email-verify-smtp plan Constitution Check Q2/Q7/Q8＋analyze 三鏡頭（user 親決 2026-07-31、A 案照定稿全過）。
- 1.14.0（2026-07-18）：§III.2 MODAL-WIRING **新用途 (k)** 首登強制換密控制流（強制改密頁 constant route＋constantRoutes 名單觸點 build/plugins/router.ts 修改型＋route guard 全域攔截＋auth store needChangePwd inline＋manage「密碼」動作與隨機專用浮層〔(h) 同型擴充、沿重設密碼按鈕碼〕＋add 抽屜隨機鈕〔(a) 接線必要控件同型〕＋user-center 改密卡隨機鈕〔(g) 自助射程確認〕＋src/components/ 產密浮層共用元件新檔〔新增型圈界〕＋對應 i18n key——兩檔位錨〔015 analyze U1〕）＋§I.2 constantRoutes 射程釋義一句（constant route 集合可經 §III.2 授權新增、builtin 三頁與 Casbin 豁免語意不變〔015 analyze C1〕）＋§I.7 島 I 新細項 I6 密碼經手與首登強制換密（經手判定單一規則純函式 seam／三入口同交易寫入＋全刪恆標的名下／冷卻端點固有規則不入 I5 單一驗證點＋一體適用零例外攜剩餘秒數／硬閘白名單語意含帶權限管理端點；硬閘每請求 EXISTS 與島 I2「MUST NOT 每請求活性判定」射程區隔＝該禁令限撤銷即時性）＋§III.2 紀律行「嚴格限九用途」→「嚴格限十一用途」失步勘誤（v1.13.0 加 (j) 時漏改）。ADR 0067（經手表 sys_pwd_custody 模型＋鎖態 token 硬閘選型；specify 期親決收斂＝冷卻一體適用零例外＋拒絕攜剩餘秒數、豁免殘句已刪）隨本 Amendment 轉 accepted；MINOR（§V.3「軌道授權邊界擴展（新用途）」＋「行為島隨刀進場（§I.7 填充）」）——觸發＝015-pwd-custody plan Constitution Check Q2/Q7/Q9（user 親決 2026-07-18、A 案照定稿全過）。
- 1.13.0（2026-07-17）：§III.2 MODAL-WIRING **新用途 (j)** layout 上游缺陷修補（`src/layouts/modules/**`＋配套樣式 `transition.css`；嚴格限「有重現法與行為對照記錄之上游缺陷、一案一 ADR」、不擴張到 layout 重設計／新 UI／行為性新功能）——首案＝B-104：global-content 頁面切換 Transition（mode=out-in＋KeepAlive）快速連續導航 race 使 Vue BaseTransition state.isLeaving 卡 true、main 永久空渲染（僅整頁 F5 可復原；80ms 連打 14 次可重現、CDP 診斷證據鏈＋spike 實證存 ADR 0066）；workaround 選型 user 親決（2026-07-17）＝去 mode=out-in＋fade-slide-leave-active 加 position:absolute（並行交疊淡出、零版面跳動、isLeaving 卡死路徑根除）。ADR 0066 隨本 Amendment 轉 accepted；MINOR（§V.3「軌道授權邊界擴展（新用途）」）——觸發＝user 實機回報 bug＋輕量軌拍板（B-104 A 案改提前施工）。
- 1.12.0（2026-07-17）：兩筆一次收（user 親決 2026-07-17）——①§III.2 MODAL-WIRING **(g) 擴字串**：用途加「＋對應 i18n key」（page.userCenter.* 射程＝29 承襲鍵＋改密成功 toast 鍵共 30；(c)(d)(e)(h)(i) 五用途本已明寫、014 前唯 (g) 獨缺＝字面縫隙以擴字串正名、013 v1.11.0 (d) 判例第四度）；②§I.7 **島 I2 釋義字面**：改密撤銷句補「操作者＝標的＝撤全部其他 session、保留當前操作 session（不自斷）」（照 1.6.0 島 E2 射程釐清前例＝已入憲 invariant 細項調整；意圖鏈本已完整——011 spec FR-025 MUST 字面＋as-built u9 keep-sid 測試錨定；★同時裁決 accepted ADR 互牴：ADR 0053 島 I2 內文「改密消費 revoke_all_of_user 不留 keep_sid」與 ADR 0055 不變式「保留當前操作 session」不一致、**以 0055 為準**——本釋義入憲後依 §V.1 字面優先壓住 0053 偏差句、0053 body 照 accepted 不可變紀律不動）。ADR 0065（getUserRoutes 恆附掛 self-service 路由白名單＝(g) 非 Casbin menu 頁級豁免在路由樹組裝層的實作；casbin 業務 menu 過濾零改動）隨本 Amendment 轉 accepted；MINOR（§V.3「軌道授權邊界擴展」＋「已入憲 invariant 細項調整」）——觸發＝014-user-center plan Constitution Check Q2/Q7＋analyze 一致性掃描 C1（HIGH、對抗覆核屬實：keep-sid 為 FR-005/SC-002 核心驗收、僅靠 ADR 寬讀撐字面 supremacy 站不穩）。
- 1.11.0（2026-07-16）：§III.2 MODAL-WIRING **(d) 擴字串**——用途加「IP 規則回收桶復原」、錨點加 `views/manage/ip-rule/index.vue` 混排清單（含已刪列顯示與狀態欄辨識）之搜尋卡「狀態」三態過濾控件〔現役／已刪除／全部——★承載已刪視圖切換、取代 menu/user 的 toggle 形；搜尋卡之網段模糊／類型精確兩維仍屬 (e) 鏡像〕＋逐列 restore 鈕；標頭 (a)~(i) 用途款集不動（不立新用途 (j)）。★**零新行為島**（013 純消費島 F、不動判定邏輯——家族首刀）。ADR 0061 本 Amendment／0062 008 IP 規則讀端契約擴充〔getIpRuleList 三 filter＋IpRuleRecord 審計欄上 wire＋批次 enrich〕／0063 ip-rule RBAC 按鈕碼 seed＋sys_menu.buttons 回填〔B-083 行為級 forward-link、無機器強制之殘餘風險明載〕／0064 schema-gate seed 內容變更受管軌道 `SEED_CONTENT_OVERRIDE_ALLOWLIST`〔0062~0064 為 feature/工具級 ADR、非憲法變更，隨本 gate 同批轉 accepted〕——四筆隨本 Amendment 轉 accepted；MINOR（§V.3「軌道授權邊界擴展（新用途／新範圍）」；v1.8.0 擴 (d) 至 menu 頁、v1.9.0 擴 (d) 至 user 頁回收桶＝同判例第三度）——觸發＝013-ip-rule-admin plan Constitution Check Q2/Q7＋clarify Q1（搜尋卡加狀態三態）＋analyze D1（user 親決 2026-07-16「狀態三態下拉明寫進 (d) 錨點字面」——該控件承載已刪視圖切換、不寫則落 (d)/(e) 縫隙）。
- 1.10.0（2026-07-15）：§I.7 行為島進場——島 J 稽核域 reporting 與 retention（J1 讀端 read-only＋僅超管＋逐欄構造／J2 access-log 寫入 fail-open〔不記 body・query、未認證零列、信任錨；反轉＝MAJOR〕／J3 purge 時間水平線唯一形狀＋同交易自落 op-log＋PURGE 固定豁免＝§I.6 變體 B「不可竄改」之 retention 權威釋義〔反轉＝MAJOR〕／J4 PII 顯示打碼單點＋落庫白名單為政策本體／J5 解鎖稽核先於生效；ADR 0057 四源讀端／0058 purge 執行面／0059 PII 打碼／0060 access-log 寫入端啟用、四筆隨本 Amendment 轉 accepted）＋§I.6 變體 B 加 J3 交叉釋義＋§III.2 MODAL-WIRING 新用途 (i) 稽核中心唯讀報表頁；MINOR（§V.3「行為島隨刀進場」＋「軌道授權邊界擴展」）——觸發＝012-audit-admin plan Constitution Check Q9/Q2/Q7＋analyze C1 時序修正（user 親決 2026-07-15「先修後親決、A 案照 draft 全過」）。
- 1.9.0（2026-07-14）：§I.7 行為島進場——島 I 使用者域治理（I1 統一序列化＋固定鎖序〔與 login/refresh 共鎖、user 列→role 列→指派列禁反向、lock-then-redecide、addUser 豁免、partial-uniq 為復原守門顯式前提；反轉＝MAJOR〕／I2 撤銷連動同交易＋權威優先＋登入鎖內重驗〔revoked/kicked 體驗碼不互換、廣播 best-effort 殘留窗明文接受、login 鎖內重驗活性＋密碼雜湊、換發不另重驗雜湊、合法撤銷換發靜默；反轉＝MAJOR〕／I3 seed 帳號結構保護〔三帳號不可刪、Super 恆禁停用/解超管指派、self 刪/停/踢/改指派四不〕／I4 刪除硬刪指派＋復原不回灌＋status 保留＋批刪整批拒／I5 密碼政策單一驗證點＋密碼三重不洩〔反轉＝MAJOR〕；ADR 0053 總綱／0054 密碼政策／0055 B-030 拆階段）＋§III.2 軌道擴展四處〔MODAL-WIRING (d) 擴 user 頁回收桶／新用途 (h) manage 頁維運動作／(a) 分類釐清 drawer 接線必要控件／LOGIN-CAPTCHA-WIRING 新用途 (ii) pwd-login 表單規則放寬〕；MINOR（§V.3「行為島隨刀進場」＋「軌道授權邊界擴展」）——觸發＝011-user-admin plan Constitution Check Q9/Q2/Q7（user 親決 2026-07-14、A 案照 draft 全過）。
- 1.8.0（2026-07-13）：§I.7 行為島進場——島 H 選單域生命週期與授權連動（H1 選單域寫入序列化域＋鎖內重驗〔反轉＝MAJOR〕／H2 同鍵重建零繼承〔連動歸檔 menu_soft_delete／menu_button_removed、reason gate 不可手動復原〕／H3 樹結構不變式〔無環／未刪子掛未刪父／protected 與非空目錄不可刪／批刪 no-partial child-first 拓撲序〕／H4 不可變錨欄 route_name·menu_type＋治理域／顯示域分層／H5 復原不回灌；ADR 0051 選單域狀態機總綱／0052 本 Amendment）＋§III.2(d) 軌道錨點擴充〔「顯示已刪除」toggle＋逐列 restore 鈕錨點自 menu-operate-modal.vue 擴至 views/manage/menu/index.vue、用途字串不動〕；MINOR（§V.3「行為島隨刀進場」＋「軌道授權邊界擴展」）——觸發＝010-menu-admin plan Constitution Check Q9/Q2/Q7（user 親決 2026-07-13）。
- 1.7.0（2026-07-12）：§I.7 行為島進場——島 G casbin 授權治理（G1 真相唯一與同步失敗契約〔重建成功才 swap、失敗保留已知良好、反轉＝MAJOR〕／G2 受保護拒絕／G3 撤銷必歸檔〔role_id＋reason〕／G4 刪除守門＋批次 no-partial／G5 復原同實例＋現役寫入全端點 lock-then-redecide；ADR 0048 本島／0049 歸檔 role_id／0050 明細通道）＋MODAL-WIRING (a) 檔名枚舉澄清〔擴句涵蓋同頁 *-auth-modal.vue 既有 placeholder 接線與附屬模板行為小修〕；MINOR（§V.3「行為島隨刀進場」＋「軌道授權邊界擴展」）——觸發＝009-role-admin plan Constitution Check Q9＋analyze A1 甲案（user 親決 2026-07-12）。★本 log 行為 010 plan 期補記（009 收刀遺漏、PATCH 級勘誤、隨 v1.8.0 一併）。
- 1.6.0（2026-07-11）：§I.7 行為島進場——島 F IP 存取控制閘＋信任錨＋來源維節流（F1 判定序白＞黑＞default-allow／F2 真相分層 keep-last-good／F3 全鏈 fail-OPEN 唯一例外＝寫端自鎖、反轉＝MAJOR／F4 信任錨唯一輸入且信任集與跳過集同源對稱、CDN 錨傳輸層背書為承重部署前提／F5 放行跳節流只認顯式規則；ADR 0043 真實 IP 還原 supersede 0017 還原節、0044 本島、0045 來源維節流 supersede 0038 調整項二、0046 region GeoIP、0047 鎖定審計欄 won't-fix）＋島 E2 射程釐清（帳號維判定鍵射程與來源維並列不衝突、FR-030）；MINOR（§V.3「行為島隨刀進場」＋「已入憲 invariant 細項調整」）——觸發＝008-ip-gate plan Constitution Check Q9＋final review #1 CDN 錨承重前提（user 親決 2026-07-11）。
- 1.5.0（2026-07-11）：新增 ★BASE-WEB-DEVPROXY-WIRING 軌道三處〔(i) `service.ts` `createProxyPattern` 同源前綴 `/proxy-default`→`/api`／(ii) `proxy.ts` target 改讀新 env key `VITE_PROXY_TARGET`／(iii) `vite-env.d.ts` 宣告 `VITE_PROXY_TARGET`〕（ADR 0042）；MINOR（§V.3「新增 ★ 軌道」）——觸發＝008-ip-gate plan Constitution Check Q2/Q7（B-079 dev 反代拓樸修正、analyze C1 拍板 env key 案）。
- 1.4.1（2026-07-10）：§III.2「補完 vs 新能力判準」加「零新 key」釋義——指新 i18n 命名空間／新元件／新路由等「面」級新增，不含既有授權頁既有子命名空間下的資料級 label key（ADR 0041）；PATCH（§V.3「文字校正、釐清」）——觸發＝007-login-throttle `/speckit-analyze` 的 C1 finding（CRITICAL）＋user 親決。★非授權擴展：判準其餘三條件與其他軌道邊界不受影響。
- 1.4.0（2026-07-10）：§I.7 行為島進場——島 E 登入失敗節流（E1 真相分層與 fail 方向〔含唯一 fail-closed 例外〕／E2 防枚舉延伸／E3 審計邊界／E4 captcha gate 與硬鎖優先；ADR 0037，負快取層 ADR 0038 supersede 0016）＋新增 ★BASE-WEB-LOGIN-CAPTCHA-WIRING 軌道一用途〔(i) 密碼登入表單圖形驗證碼接线，含其資料取得所需之最小 store/service 接线〕（ADR 0040）；MINOR（§V.3「行為島隨刀進場」＋「新增 ★ 軌道」）——觸發＝007-login-throttle plan Constitution Check Q2/Q7/Q9。
- 1.3.0（2026-07-06）：§I.7 行為島首度填充——島 A single-session／B token rotation／C denylist／D 閒置sliding refresh（ADR 0033、supersede 0030）＋新增 ★BASE-WEB-LOGOUT-UX-WIRING 軌道兩用途〔(i) logout server-call 接线／(ii) logoutCodes 靜默分支 toast〕（ADR 0034）；MINOR（§V.3「行為島隨刀進場」＋「新增 ★ 軌道」）——觸發＝006-session-lifecycle plan Constitution Check Q2/Q7/Q9。
- 1.2.0（2026-07-05）：新增 ★BASE-WEB-AUTH-WIRING 軌道（ADR 0031；授權 auth 刀三處 base-web inline 接线 (a) route store 常數合併修／(b) alt-login 三表單 stub／(c) captcha stub；MINOR 新增 ★ 軌道、§V.3）——觸發＝005-auth-login plan Constitution Check Q2/Q7。
- 1.1.0（2026-07-05）：★BASE-WEB-I18N-WIRING 加 (iv) zh-TW 首發 locale 完整建置授權（ADR 0028；MINOR 軌道授權邊界擴展、§V.3）——觸發＝004-system-settings plan Constitution Check Q7。
