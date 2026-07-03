# INTEGRATION-rev4-arc42.md — rev4 文件架構與啟動書

> **定位**：本檔是 rev4 的**單一自包含設計文件＋啟動書**——文件架構、流程規則、bootstrap 程序、rev3 知識匯出包全部收在這一份。由 rev3 workspace 的問答收斂產出（2026-07-02）。
> **自包含紀律**：本檔不依賴 rev3 repo 內任何檔案。提及 rev3 文件與編號時一律是「史料標註」（帶 `rev3:` 前綴、純文字非連結）——讀者不開 rev3 repo 也能完整理解本檔；要回溯抽查時，rev3 workspace 作為唯讀參考庫存在。
> **本檔命運**：rev4 bootstrap 完成後轉存 `docs/brainstorms/000-doc-architecture.md` 退役成史料（屆時規則已由 CLAUDE.md／constitution／lint 實碼承接、不再被任何活文件引用）。
> **自我豁免聲明**：本檔為 one-shot 啟動書（~38k tokens），**不受** §0 準則 2 與 lint L7 的活文件預算約束——該約束的對象是 rev4 的活文件；本檔退役後即史料、brainstorms/ 目錄本就不設預算。

---

## 0. 目的與成功準則

**目的**：rev1→rev2→rev3 每次重建，文件架構都是主因之一（rev2→rev3 的重建動機明文是「命名整頓＋文件/工作區衛生重置」，非程式失敗）。rev4 要一次把文件架構設計對，讓「漏東漏西→積累→乾脆重開一版」的循環終止——**不再有 rev5**。

**成功準則（機械可驗）**：
1. 任何單一事件的人工簿記位置 ≤2（收刀＝1 筆事件＋NOTES 幾行；拍板＝1 個 ADR 檔）；其餘鏡像一律機器生成或不存在。
2. 任何**活文件**不因專案推進而超出單次可讀上限（≤25k tokens；成長型檔案有分卷機制，L7 明列受管清單）；每 session 注入合計 ≤5k tokens（rev3 為 29k）。lint 硬擋；token 計數以 `UTF-8 bytes ÷ 3` 保守近似（docs-sync 自帶測試鎖定算法）。
3. 文件對自身契約（不可變、預算、必填欄）全部 lint 化——違反在 **commit 當下**被擋，不是幾週後 review 才發現。
4. 「查現況」永遠只有一個地方（`generated/STATE.md`＋`generated/reference/`），且與實碼機器對賬保證一致。
5. 長期健康指標：docs commit 佔比顯著低於 rev3 的 57%；收刀「補遺」commit 歸零（rev3 為 25 刀中 ≥8 刀）；cumulative review 的 doc-drift findings 歸零。

---

## 1. 拍板前提（Q&A 全紀錄）

| # | 問題 | 拍板 | 對設計的含意 |
|---|---|---|---|
| Q1 | rev4 與 rev3 程式碼/設計的關係 | **設計也重新檢視、藉機翻案部分決策** | 文件架構**先於設計存在**（骨架先立、內容隨 brainstorm→拍板→逐刀實作填入）；rev3 設計結論只是候選輸入非定案 |
| Q2 | 文件讀者與維護者 | **user＋Claude（機器優先）** | 文件優先設計成好注入、好驗證、難漂移；人類可讀性退居第二；arc42 只取骨架概念不照單全收 |
| Q3 | 開發流程骨幹動不動 | **骨幹沿用、簿記層全面重設（可自動化）** | spec-kit SDD＋superpowers TDD＋Workflow 編排、傘狀 repo＋worktree/submodule 兩段 commit 都保留；簿記規則全面重設、防漂移做成 hook/腳本而非紀律條文 |
| Q4 | 五大根因痛點排序 | **A~E 全選、全數根治權重** | 不做取捨式設計；同時治雙寫（A）、人腦簿記（B）、摺回失效（C）、膨脹失控（D）、引用脆弱（E） |
| Q5 | 自動化信任邊界 | **混合：鏡像全自動、敘事人寫機驗** | 可推導內容一律機器生成（人只審 diff）；決策全文、設計敘事由 Claude/user 寫、hook 機械驗證完整性 |
| Q6 | 交付物範圍 | **架構＋精簡知識匯出包** | 本檔附 K1 設計結論候選／K2 翻案遞延候選／K3 教訓種子三張清單（見 §5） |
| Q7 | 整體架構方案（三案擇一） | **方案 A「活書＋ADR＋機器帳」** | 活書 living as-built＋ADR 一決策一檔＋單一事件源生成鏡像。否決 B「凍結＋硬閘摺回」（rev3 實證摺回不會發生）與 C「無架構書」（rev1 前後端漂移死因重現） |
| Q8 | 目錄樹（user 三輪調整） | **活書單檔＋ops/ 收目錄＋brainstorms 路徑覆蓋** | 活書不拆分節檔（單檔 12 節、`arch_impact` 以節號＋標題解析驗 diff）；營運檔收 `docs/ops/`；brainstorm 產出存 `docs/brainstorms/`（skill 預設路徑由 CLAUDE.md 一行覆蓋、rev3 已驗證可行）；「人寫」＝對話產出、Claude 執筆、user 拍板審 diff |
| Q9 | 碼衍生策略（bootstrap B9） | **從上游重來**（工程推薦原為碼繼承、user 權衡後選重來、月級重跑成本已知情接受） | 理由四項：文件流要從第一刀就全程驗證／翻案要從地基生效不 retrofit／吃最新上游＋乾淨血緣／重跑本身有學習與再驗證價值。K1/K2 升級為每刀 brainstorm 的直接輸入 |
| Q10 | 橫切工作（i18n、datetime 等在 rev3 無插入點） | **三條一般解＋bootstrap 地基化** | 活書 §8 慣例必附守門機制；橫切刀一級公民；bootstrap 期明列橫切慣例清單（重來模式下零 retrofit 成本），詳 §3.5 |

---

## 2. rev3 痛點診斷（2026-07-02 實證盤點——本設計的依據）

> 方法：7 個平行調查（四大 INTEGRATION 文件精讀＋review 統整報告分類＋git 全史考古＋全文件面雙寫地圖），所有數字皆 git/檔案實測。

### 2.1 核心洞察：病灶會轉移

rev3 的四文件制（凍結 DESIGN＋DECISIONS 活帳＋CHECKLIST 動態＋MILESTONES 永久）**本身就是對 rev2 文件病的矯正設計**（rev2 DESIGN 被改 65 次、膨脹 +50% 到 247KB）。結果：DESIGN 真的凍住了（21 天僅 +0.6%），**但膨脹與雙寫轉移到另外三檔**——CHECKLIST 58KB／DECISIONS 133KB／MILESTONES 100KB，三檔全部超過單次讀取上限。教訓：**只重新切檔案不會治病；要治的是「同一事實手工維護 N 份投影」這個生成機制**。

### 2.2 五大結構性根因

**根因 A｜同一事實手抄 N 份（雙寫地圖）**
- 一次 feature 收刀的同一段摘要 ≥8 處（CLAUDE.md 檔頭進度行＋active-feature marker×2、CHECKLIST 階段/最新進展/下一步/波節、DECISIONS 決策列、MILESTONES 表列），其中 4 處近乎同文長段各自手抄。
- dev 帳號表 ≥7 類載體 20+ 處；port 值散佈 30+ 個 spec 檔；軌道授權定義 4 檔（一次 amendment 實測補 3 檔 5 處）；route 計數散 9 檔。
- 實測成本：末刀收刀簿記＝5 檔、跨 4 筆 commit、≥20 個編輯位置——**規則全跑完仍漏**。

**根因 B｜簿記靠散文規則＋人腦執行、零機械驗證**
- 歸檔流程是指引文件裡 14 條散文規則（四路分流），每刀收刀 7~9 個分散位置起跳。
- 25 刀中 ≥8 刀需要第 2~3 筆「補遺/補完/補正」commit 收拾首輪漏網（倒數第二刀的波節漏到末刀收刀才補；第一刀就漏登 7 條）。
- 全史 499 commits 中 **57% 是 docs commits**；一刀 ≈18 個 outer commit 中純簿記 ≥8 個。

**根因 C｜「凍結藍圖＋活帳摺回」單向失效**
- 摺回機制（低頻重鑄）設計上存在、**21 天內 0 次執行**：38 筆已決未摺回、藍圖本文殘留 38 處「待決」字樣（實際已決）、wire 全集表凍在 41 條（實況 54）、port 表還是 rev2 值、roadmap 耗盡（末 7 刀無處掛）但兩個活檔仍指「下一步看 roadmap」。
- 勘誤入口半套執行：一次勘誤自己點名 3 處、只修 2 處；勘誤實務退化成「加新節宣告舊文作廢」而非修舊文——讀藍圖任一段都要跳決策帳比對才可信。

**根因 D｜文件違反自身契約、形態失控**
- CHECKLIST「永不膨脹」破功：de-bloat 後 10 天位元組反超峰值；膨脹改以「超長單行」吸收（最長一行 3,262 字）；每 session 注入 ≈29k tokens。
- MILESTONES「一行一筆 append-only」破功：單列膨脹到 4,722 字（= 對應 commit message 的 8.5 倍）；刪檔整併時被迫回改已 append 的列。
- DECISIONS 163 行卻 133KB：單列 9,282 字、單行 diff 不可 review；記帳慣例 21 天內漂移 3 次（同類事件落點不一致）。
- 混合生命週期：todo、won't-fix 紀錄、決策鏡像、歷史指標住同一檔，checkbox 語意失真到需要內嵌「為什麼這些 todo 收不掉」的辯護註記。

**根因 E｜引用與 ID 系統脆弱、blast radius 失控**
- § 錨會 rot：CHECKLIST 一次內部重組迫使 MILESTONES 維護「舊→新錨對照表」善後。
- 手工流水碼（⚠️a~⚠️ah）撞號一次＝跨 10 檔 34 處重命名；單一碼被引用 100 次；review 出身的拍板又用另一套編號破格插入。
- 刪 4 份 review 報告＝連動修 4 檔 7 處引用點；下游 spec 用揮發行號引藍圖、行號一改即 rot。

### 2.3 漂移類型學（哪類資訊會漂、哪類不會）

來自 4 輪 review（25 feature 全覆蓋＋live/CDP 實測）的分類實證：

| 資訊類型 | 漂移實績 | 教訓 |
|---|---|---|
| spec 字面 vs as-built 演進 | **最大宗**：26 列 supersession 映射（後刀合法推翻前刀、實作中 pivot） | 漂移是常態不是 bug；需要可機讀的 supersession 關係而非人工映射表 |
| 節錄型 reference 表 | 使用者表欄位僅列 5/16 欄 → 實際誤導過一次規劃、拖兩輪 review 才修 | **節錄表必漂** |
| 全量正典型 reference 表 | port 表、卷清單 4 輪 review **零 findings** | **全量正典表不漂**——reference data 一律全量或明標 partial |
| code 內註解/檔頭 doc | 檔頭寫 3 端點實為 4；勘誤只修同檔兩處之一 | 勘誤動作缺「同語意全檔掃描」步驟 |
| 隱式契約（無人寫下的預期） | 查全表無 ORDER BY 依賴 heap 序 | 靜態 review 抓不到、只有 runtime 實測會浮現 |

發現時滯：靜態 review 對 runtime 類漂移結構性失明，平均拖到下一次 CDP/live 輪才被抓——防漂移機制必須含「機器對賬」（文件宣稱 vs 實碼/實環境）。

### 2.4 rev3 做對的部分（rev4 保留清單）

- **藍圖凍結本身成功**（churn 極低）——「權威不當狀態板」方向正確，敗在摺回無排程無自動化。
- **全量正典表零漂移**（見 2.3）。
- **spec-kit per-feature artifacts＋雙 review 軌道有效**：25/25 PASS、刀內攔截多起真缺陷；per-feature 文件生命週期清楚、收刀即凍結成史料，**不是**漏東漏西的來源。
- **SessionStart hook 注入機制有效**（跨 session 進度錨概念成立），問題只在注入物膨脹失控。
- **兩段 commit＋pin 即時 bump 紀律成熟**。
- repo 內已有「lint 測試擋紀律」文化（端點覆蓋 lint 等）——文件對賬 lint 有現成模式可循。

### 2.5 rev2→rev3 重建動機（防止 rev5 的直接依據）

rev2→rev3 明文動機＝命名整頓＋文件衛生重置（rev2 藍圖膨脹 247KB、計畫與實錄混寫）；rev1→rev2 僅間接線索（前後端契約漂移）。**兩次重建都不是程式失敗，是文件/契約失控**。rev4 文件架構解決根因 A~E 之後，重建誘因即消失。

---

## 3. rev4 文件架構設計（方案 A「活書＋ADR＋機器帳」）

### 3.1 文件全集與職責邊界

**核心規則**：每個事實只有一個人寫的家；所有鏡像不是機器生成、就是不存在。三種材質——**人寫**（對話產出、Claude 執筆、user 拍板審 diff）／**事件源**（半自動 append）／**機器生成**（嚴禁手改）。

```
rev4-root/
├── CLAUDE.md                    人寫｜薄操作手冊（≤250 行；骨架見 §4.3）
├── .claude/（hook）              SessionStart＝git 健檢＋cat ops/NOTES.md＋generated/STATE.md
│                                pre-commit＝docs-sync check＋lint 套件
├── tools/docs-sync              生成器＋lint（python 標準庫單檔、自帶測試）
├── docs/
│   ├── arc42/
│   │   ├── ARCHITECTURE.md      人寫｜活書單檔（12 節裁切、≤700 行且 ≤25k tokens）
│   │   └── decisions/           人寫｜ADR 一決策一檔（0001-<slug>.md、accepted 後不可變）
│   ├── ops/
│   │   ├── NOTES.md             人寫｜當前意圖/下一步（≤40 行）——唯一手寫進度敘事
│   │   ├── BACKLOG.md           人寫｜待辦（B-NNN 穩定 ID；完成即刪列、git 即史）
│   │   ├── LESSONS.md           人寫｜教訓 registry（L-NNN、append-only；初始內容＝§5.3）
│   │   └── events.jsonl         事件源｜一刀收刀＝append 一筆 JSON（schema 見 §4.4）
│   ├── generated/               機器｜嚴禁手改（lint 擋）、任何檔案可刪除重算
│   │   ├── STATE.md             session 注入主體（events 尾 3 筆＋git 狀態＋統計＋對賬結果）
│   │   ├── MILESTONES.md        里程碑表（全 events 表格化）
│   │   ├── DECISIONS-INDEX.md   ADR 索引（front-matter 掃描＋supersedes 對稱回填）
│   │   └── reference/           全量正典表（routes/ports/schema/帳號/screens，從實碼生成＋對賬）
│   ├── brainstorms/             人寫｜Phase 0 brainstorm（superpowers 產出、路徑由 CLAUDE.md 覆蓋）
│   └── reviews/                 人寫｜review 報告史料
├── specs/<NNN>-<feature>/       spec-kit 原樣（rev3 實證生命週期健康）
└── .specify/memory/constitution.md  人寫｜凍結權威（amendment＝ADR＋版本 bump；不設任何鏡像快查表）
```

**收刀簿記對比**：rev3＝4~5 檔 ≥20 處手抄＋常態補遺 commit → rev4＝①events.jsonl append 一筆＋②NOTES.md 改兩三行（＋若有架構影響、該刀 branch 內已更新活書對應節），其餘全部 `docs-sync generate` 重算、一筆簿記 commit。

**「完成即刪、git 即史」**：檔案永遠只呈現「現在還活著的事」——待辦做完＝刪列、決策翻案＝新檔。沒有任何歸檔搬運手續（rev3 的批次搬運制度實證 20 天各只執行 2 次即停擺）。歷史只有兩個家：git 史、events.jsonl（一刀一行）。

**rev3→rev4 檔案命運**：凍結藍圖→活書；決策表→ADR 目錄；波次帳→events＋generated/MILESTONES；CHECKLIST 進度區→ops/NOTES、backlog 區→ops/BACKLOG（won't-fix 改立 ADR）、拍板索引→generated/DECISIONS-INDEX、軌道快查→**消滅**（constitution 唯一權威）；MILESTONES→generated/（人永不編輯）；指引文件的 reference 表→generated/reference/；散落 gotcha＋per-machine memory→ops/LESSONS.md。

### 3.2 活書 `arc42/ARCHITECTURE.md`

**時態分離總原則**：書永遠**現在式**（系統現在長怎樣）；未來式住 ops/（roadmap/待辦/候選刀→BACKLOG、當前意圖→NOTES）；過去式住 git＋events。rev3 藍圖的 roadmap 耗盡、波次表過期、「待決」殘留全是時態混寫的病——rev4 書內這三種內容不存在。

**12 節內容與行數配額**（單檔內 `## §N` 標題、節號穩定可引用；全檔 ≤700 行且 ≤25k tokens 硬擋、單節超配額警告）：

| 節 | 寫什麼（人寫敘事） | 快變事實去處 | 配額 | churn 預期 |
|---|---|---|---|---|
| §1 簡介與目標 | 系統一句話、能力級清單、NFR 摘要、明確不做 | — | 40 | 極低 |
| §2 約束 | 技術棧鎖定、repo/worktree 拓樸、WSL2/LF 環境 | — | 30 | 極低 |
| §3 系統脈絡 | C4 context 級 ASCII 圖、ingress 信任邊界表、外部依賴 | — | 50 | 低 |
| §4 解法策略 | 雙脊椎、facade-only、casbin DB-first、島狀縱切、機器優先文件觀 | — | 40 | 極低 |
| §5 Building blocks | crate/facade 地圖、前端結構、資料模型敘事（ER 關係＋audit archetype 理由） | 欄位明細☞generated/reference/schema | 90 | 低 |
| §6 Runtime | 登入鏈/RBAC 判定鏈/IP gate 判定序、狀態機 ASCII 圖 | — | 120 | 中（行為刀） |
| §7 部署 | compose 拓樸敘事、dev/prod/acme 三模式、卷與 secret 命名策略 | port/卷實值☞generated/reference/ports | 60 | 低 |
| §8 橫切概念 | 審計欄 archetype、錯誤碼系統、i18n 規則、datetime 慣例、wire contract 紀律——**每條慣例必附「守門機制」欄**（見 §3.5） | route 全集☞generated/reference/routes | 90 | 低 |
| §9 架構決策 | 兩行指標：全文住 decisions/、索引住 generated/——不承載內容 | — | 5 | 靜態 |
| §10 品質要求 | **fail-open/closed 語意總表**（rev3 散在各 spec、聚合為新增價值）、併發正確性、效能目標 | — | 40 | 極低 |
| §11 風險與技術債 | 一行指標 ☞ ops/BACKLOG＋ops/LESSONS | — | 3 | 靜態 |
| §12 名詞表 | 短名/長名、刀、島、軌道、C-V 等 | — | 30 | 極低 |

**更新契約（lint 強制）**：
1. **收刀聲明制**：事件 `arch_impact` 聲明動了哪些節（或 none）；lint 解析標題切節、比對該刀 diff，**雙向驗**（聲明未改＝擋、改了未聲明＝擋）。僅收刀簿記 commit 觸發；平時書的 typo/勘誤修正為獨立 commit、不觸發。
2. **勘誤全掃描**：`docs-sync errata <關鍵詞>` 機器枚舉全 repo 同語意命中、逐處處置——堵「點名 3 處只修 2 處」型半套勘誤。
3. **預算 lint**：每 commit 輸出各節行數表；單節超額警告、全檔超額硬擋。
4. **禁入詞典**：port 實值、route 計數、seed 密碼等快變字面值 pattern 出現在書內＝警告＋提示正確去處（generated/reference/）。
5. **時態禁詞**：書內出現「待決」「TBD」「⏳」「已完成」「下一步」＝擋、訊息附去處。

**刻意排除**（rev3 藍圖有、rev4 書沒有）：交付計畫/roadmap（→BACKLOG 候選刀區；rev3 實證 roadmap 表必耗盡失真）；前代遷移附錄（one-shot 史料不隨行）；constitution 凍結快照（本尊唯一權威；rev3 實證快照分岔 3 週）；決策表（→ADR）；「待決/⚠️」標記系統（時態分離後不需存在）。

### 3.3 ADR＋事件源＋生成管線

**ADR（`arc42/decisions/NNNN-<slug>.md`）**：
- front-matter：`id / title / date / status(draft|accepted|superseded|rejected) / feature / supersedes[] / superseded_by[]（工具回填、人不填）/ provenance（選填、rev3 族譜純字串）/ tags[]`；body 四段：背景／決定／後果／替代案（選擇性）。
- 生命週期：draft（可隨意改）→ accepted（**body 不可變**；lint 偵測 diff 即擋、commit message 帶 `[adr-amend]` 豁免 typo 級）→ 翻案＝新檔 `supersedes: [舊號]`、工具回填舊檔 `superseded_by`。rejected 也留檔（否決案是知識）。
- 刻意設計：won't-fix／by-design 也立 ADR（body 可極短）；**as-built 不回灌 ADR**（拍板歸 ADR、實作結果歸收刀事件、實作推翻拍板＝新 ADR）——根治 rev3 決策列膨脹至 4,000+ 字；編號＝檔名、永不重用、禁刪除——撞號在 git 層直接衝突現形、引用永不 rot。

**事件源（`ops/events.jsonl`）**：一行一 JSON、三型別（欄位規格見 §4.4）。JSON Schema 隨 repo 逐行驗、漏必填欄位當場擋；append 為常態但可修（source 非聖物、git diff 可審）。肥大無虞：一刀一行 ~300 字、不整檔注入（STATE 只取尾 3 筆）、必要時可 rotate。人不讀 jsonl、讀 generated/MILESTONES。

**營運檔規格**：
- `NOTES.md`：自由格式、≤40 行（L7）——唯一手寫進度敘事；不記 push 狀態類揮發 git state。
- `BACKLOG.md`：檔頭一行 next-id 計數器（`<!-- next: B-023 -->`），條目格式 `- B-021｜<一句話>｜<觸發條件或期限（選）>`；配號＝取 next-id 後 bump（**號碼永不回收**——完成刪列後號碼留在 git 史與 events 引用裡，L9 驗新號必 ≥ next-id 且 next-id 單調遞增）；預算 ≤200 行（L7、backlog 爆量＝該開刀了的訊號）。
- `LESSONS.md`：一教訓一段（`L-NNN｜坑＋防法`）、檔頭 next-id 計數器同 BACKLOG 制；單卷逼近 25k tokens 時分卷（滿卷改名 `LESSONS-<起迄號>.md` 封存、主檔續寫，L 號跨卷連號、docs-sync 掃全卷驗 L9）。

**生成管線（`tools/docs-sync`）**：
| 子命令 | 做什麼 | 何時跑 |
|---|---|---|
| `generate` | 重算 generated/ 全部 | 收刀後、拍板後、任何 source 變動後（Claude 跑） |
| `check` | 重算到暫存與現況 diff、不一致 exit 1 | pre-commit（同時防「忘跑 generate」與「手改 generated/」） |
| `errata <詞>` | 全 repo 同語意枚舉報告 | 勘誤時 |

生成物←來源：STATE←events 尾 3 筆＋git branch/pins＋constitution 版本＋ADR/BACKLOG 統計＋對賬結果（≤4k tokens）；MILESTONES←全 events；DECISIONS-INDEX←ADR front-matter；reference/routes←rust 路由註冊、ports←compose、schema←migration/entity、accounts←seed、screens←前端 route。

**extractor 漸進落地＋兩層防線**：bootstrap 期 extractor 為 stub（表標「來源未就緒」＋各立 BACKLOG 項、隨對應子系統首刀落地）；做不出來的表退回「人寫全量表＋對賬 lint 保底」（對賬只驗計數/關鍵值；rev3 端點覆蓋 lint 已證明此模式可行）——**生成優先、對賬保底**，兩層皆失才會漂（rev3 是零層）。

### 3.4 防漂移 lint 套件＋feature 生命週期文件流

**lint 套件（pre-commit 一次跑完、秒級；✗＝擋 commit、⚠＝警告）**：

| 組 | # | 驗什麼 | 級 |
|---|---|---|---|
| G1 生成一致 | L1 | generated/ 與重算結果 diff（抓「忘跑 generate」＋「手改 generated」） | ✗ |
| | L2 | reference 對賬：每表關鍵值/計數 vs 實碼（extractor 缺位期保底） | ✗ |
| G2 簿記完整 | L3 | events.jsonl 逐行 JSON Schema | ✗ |
| | L4 | 收刀事件存在性：default branch 的 feature merge（`NNN-name`＋`--no-ff` 訊息模式判定）必有對應 feature_close（**merge commit 本身豁免**、自其後首筆 commit 起算狀態檢查） | ✗ |
| | L5 | review findings 分流對賬——**雙源**：事件 `findings.total` 必須等於報告檔 front-matter `findings_total`（報告最小規格：front-matter 必含此欄），且 fixed＋len(to_backlog)＋len(wontfix_adr)＝total | ✗ |
| | L6 | arch_impact 雙向驗（聲明↔diff；僅收刀簿記 commit 觸發） | ✗ |
| G3 檔案契約 | L7 | 預算（tokens ≈ UTF-8 bytes÷3）：活書 ≤700 行/25k tok、單節配額、NOTES ≤40 行、STATE ≤4k tok、CLAUDE.md ≤250 行、BACKLOG ≤200 行、LESSONS 單卷 ≤25k tok（達標分卷、規格見 §3.3 營運檔規格）；generated/MILESTONES 由生成器按年分卷 | 全檔✗/單節⚠ |
| | L8 | ADR front-matter schema＋accepted body 不可變＋supersedes 對稱 | ✗ |
| | L9 | ID 唯一性：B-NNN/L-NNN 依檔頭 next-id 計數器驗（新號 ≥ next-id、next-id 單調遞增、LESSONS 掃全卷）；ADR 編號＝檔名不重用 | ✗ |
| | L10 | 活書時態禁詞（待決/TBD/⏳/已完成/下一步） | ✗ |
| | L11 | 禁入詞典（活書與 CLAUDE.md 內快變字面值＋rev3 碼 pattern 反走私：`⚠️[a-z]`、`待決[①-⑩]`、裸 `F-\d+`） | ⚠ |
| G4 引用健康 | L12 | md 內部連結指向存在檔案 | ✗ |
| | L13 | 禁行號引用（`xxx.md:123`） | ✗ |
| | L14 | 禁 deep-link 揮發區內部錨（BACKLOG/NOTES/STATE 只可整檔引用） | ✗ |
| | L15 | repo 文件禁引 per-machine memory 路徑（pattern 只匹配實路徑如 `~/.claude/**/memory/`；帶 `rev3:` 前綴的純文字史料標註不算引用、豁免） | ✗ |

rev3 每種實證漏法對映：波節漏補→L4；review 分流漏登→L5；書該更新沒更新→L6；三本帳膨脹→L7；流水碼撞號→L9＋ADR 檔名機制；「待決」殘留→L10；port 表停舊值→L1/L2；刪檔連動 7 處引用→L12。

**運作模式**：被擋的是 Claude、解決的也是 Claude（同回合修復、錯誤訊息附去處提示）；lint 只掃文件面、純碼 commit 幾乎全 skip；L1/L4 為狀態型檢查（`--no-verify` 逃生只延後、不消失）；只裝 outer repo、worktree 不碰。user 僅介入：①lint 抓到真決策（如 won't-fix 需拍板立 ADR）②lint 調規（Claude 提案、user 拍板）。

**feature 生命週期文件流**：

```
Phase 0  brainstorm        → docs/brainstorms/NNN-name.md＋（期間拍板）draft ADR
Phase 1  SDD 設計鏈        → specs/NNN/…（spec 引 ADR 編號、不複寫決策全文）
Phase 2  TDD 實作（隨做隨記）→ 新拍板→ADR draft→accepted
                             架構影響→活書對應節【就在 feature branch 內改】
                             踩坑→LESSONS append（L-NNN）
                             衍生工作→BACKLOG append（B-NNN）
                             per-unit pin bump（原樣）
收刀     finishing branch   → merge --no-ff 回 default
                             ①events append feature_close ②NOTES 改下一步
                             ③docs-sync generate → 一筆簿記 commit、lint 全綠放行
review 輪（不定期）          → docs/reviews/YYYYMMDD-scope.md
                             findings 三分流：修／B-NNN／won't-fix ADR＋review 事件（L5 對賬）
```

**人工觸點對照（rev3 實測→rev4）**：收刀 4~5 檔 ≥20 處常態補遺 → **2 處 1 commit**；拍板 2 檔 3 處 → **1 檔**；軌道級 amendment 4 檔 5 處 → **2 檔**（constitution＋ADR）；review 分流 4 檔多節 → **1 筆事件＋各去處**；勘誤人腦枚舉 → errata 機器枚舉。

**spec supersession 機讀化**：後刀推翻前刀 spec 條文→收刀事件選填 `spec_supersessions`；前刀 spec 本文不回改（史料）；docs-sync 生成 supersession 索引。誠實界線：選填欄仍可能漏記，靠 review 輪抓漏、抓到補事件即入索引（rev3 是抓到後人工維護 26 列映射表）。

### 3.5 橫切工作制度

rev3 的縱切刀制容不下橫切工作（zh-TW locale、datetime 慣例在 rev3 全程無插入點、堆在 future 區）。rev4 三條一般解：

1. **活書 §8 每條橫切慣例必附「守門機制」欄**（lint/測試/型別/review 軌）——無守門不准入 §8。沒有守門的慣例＝願望（rev3 datetime 慣例從未被拍板、25 刀各自長，實證）。
2. **橫切刀一級公民**：事件 `kind` 欄支援 `horizontal`；中途新增橫切慣例的標準模式＝「retrofit 存量＋守門增量」一把橫切刀（rev3 教訓：加了新機制卻無人回頭盤存量消費點）。
3. **bootstrap 期（B7.5）明列橫切慣例清單並各立地基 ADR**、於功能刀開跑前生效（重來模式下零 retrofit 成本）。首批：
   - **datetime（地基 ADR）**：DB `timestamptz` 一律存 UTC；wire 一律 ISO-8601 帶 offset、**禁 naive datetime**；前端唯一 datetime formatter util（以用戶瀏覽器時區顯示＋帶時區資訊；「用戶偏好時區設定」留參數位掛 BACKLOG、到時只改一處）。守門＝wire 驗收 offset 斷言＋前端禁裸 format lint。
   - **i18n（地基 ADR）**：起步即建 zh-tw.ts＋語言切換「簡體/繁體」；**locale 對等 lint**（zh-cn/zh-tw 鍵集合一致、pre-commit 擋——少寫一個 locale 當場紅燈）；primary locale（傾向 zh-TW 為主、zh-CN 留作上游同步）同批拍板。
   - 其餘：錯誤碼系統、audit archetype、soft-delete 慣例（皆沿 rev3 驗證形、各立 ADR）。

---

## 4. rev4 啟動

### 4.1 碼衍生（Q9 拍板：從上游重來）

- **base-web**：從 upstream `example` **最新 HEAD** 開 `rev4-admin-base-web`（順帶吃到 rev3 之後的上游更新）；**rust-api**：從源倉 `main`（Initial commit）開 `rev4-admin-rust-api`、API 隨刀重建；GitHub repo 名照舊（含前代字樣的是永久名、不動）。
- rev4 刀號 001 起＝真實重跑刀序；文件流從第一刀就全程陪跑。**K1/K2（§5）是每刀 brainstorm 的直接輸入**：沿用項照 rev3 已驗證結論施工、翻案項用新設計。
- rev3 workspace 凍結為**唯讀參考庫**：本檔零依賴它，但重跑每刀時其 specs/實碼是現成施工參考（K 清單出處欄的 `rev3:` 標註即回溯座標）。重跑速度遠快於首跑（照已驗證的圖施工、首次探索成本不再）。
- 成本：月級工程、已知情接受（rev3 首跑 20 天）。

### 4.2 bootstrap 序列（波 -1「文件地基」，全部完成才開功能刀）

```
B1   傘狀 repo 建置：git init＋.gitattributes（LF 強制）＋.gitignore 最小集
     （排除：fork 源倉目錄、個人化 cache/credentials；不排除 base-web/rust-api
      ——它們是 submodule gitlink）
B2   目錄骨架：docs/{arc42/decisions, ops, generated, brainstorms, reviews}＋tools/
     ＋本檔就位＋ops/LESSONS.md 以 §5.3 全量 101 筆初始化（含檔頭 next-id）
B2.5 spec-kit 安裝：選穩定 release tag（禁 dev/alpha 預發布、裝後驗版本；
     release tag 與 cli 套件自報版本是兩條版本軸、落差非異常）＋重建
     feature-branch pre-hook extension（行為規格：specify 起手前 mandatory 觸發、
     從 default branch 衍生 <NNN>-<name> local branch、只建不 push）
B3   CLAUDE.md 薄版落地（骨架見 §4.3）
B4   tools/docs-sync v0（第一把刀、走 TDD）：generate/check/errata
     ＋lint L3/L7~L15（L1/L2/L4/L5/L6 隨事件源與實碼逐步啟用；extractor 為 stub）
B5   hook 接線：SessionStart（git 健檢＋cat NOTES＋STATE）＋pre-commit（check＋lint）
B6   constitution v1.0 重鑄：K1 中 constitution 級條目先行逐筆過目——
     ★ 此過目即該批的正式拍板（user 在場逐筆點頭、非默認繼承），以其結果
     ＋rev4 新拍板鑄 v1.0；其餘 K1 條目續走 B8 流水
B7   ARCHITECTURE.md 骨架（12 節標題全立；§1/§2/§4 先填、其餘隨刀）
B7.5 地基橫切慣例定案（datetime/i18n/錯誤碼/audit/soft-delete 各立 ADR，見 §3.5）
B8   K1＋K2 處置流水：K1 逐筆（沿用→立 ADR 記 provenance、重審/翻案→brainstorm；
     可分批、未處置掛 BACKLOG——沒有默認繼承）；
     ★ K2 全量轉 B-NNN 掛 ops/BACKLOG（條目附 rev3: provenance 字串）——
     本檔退役後 K2 知識由 BACKLOG 承接、後續 brainstorm 引 B-NNN 不引本檔
B9   worktree/submodule 建置（§4.1 重來模式；操作程序見下）
B10  第一把功能刀（spec-kit 流程原樣、新文件流全面生效）
```

**B9 操作程序**（worktree＋手寫 .gitmodules；**不可用 `git submodule add`**、會與 worktree 衝突）：

```bash
# 兩源倉各開 rev4 分支並推上 remote（分支先在 remote、submodule 才有 url 可指）
cd <base-web 源倉> && git fetch upstream \
  && git branch rev4-admin-base-web upstream/example \
  && git push -u origin rev4-admin-base-web \
  && git worktree add <rev4-root>/base-web rev4-admin-base-web
cd <rust-api 源倉> && git branch rev4-admin-rust-api main \
  && git push -u origin rev4-admin-rust-api \
  && git worktree add <rev4-root>/rust-api rev4-admin-rust-api
# 外層：手寫 .gitmodules（兩組 path/url/branch）→ git submodule init
#       → git add .gitmodules base-web rust-api → commit
# 心智模型（沿 rev3 驗證慣例）：外層只記 gitlink SHA；本機 worktree 模式下
# `git submodule status` 行首「-」永遠出現、屬正常；絕不跑 git submodule update
# （會 reset worktree）；worktree 內 push 一律顯式指定 remote/branch
```

**DoD（可驗收才算 bootstrap 完成）**：hook 注入實測 ≤5k tokens；docs-sync 自帶測試綠；pre-commit 擋得住（故意做一個違規 commit 驗證）；constitution v1.0 存在；活書 ≥3 節有內容；ops/LESSONS.md 已初始化（101 筆＋next-id）；ops/BACKLOG.md 已含 K2 全量轉入項；第一筆 `misc` 事件（「rev4 bootstrap 完成」）進 events.jsonl 且 MILESTONES 生成正確。

### 4.3 rev4 CLAUDE.md 薄版章節骨架（B3 依據）

```
1. workspace 用途與 repo 拓樸（傘狀＋worktree/submodule 雙身分、短名/長名分工）
2. feature 工作流（階段 0 brainstorm〔產出存 docs/brainstorms/<NNN>-<name>.md、
   此行即覆蓋 superpowers skill 預設路徑〕→ SDD 5 步 → TDD Workflow 編排
   〔驅動提示詞〕→ finishing → 收刀簿記三步〔事件＋NOTES＋generate〕）
3. git／submodule 操作手冊（兩段式 commit、pin 即時 bump、session 健檢判讀、
   初始化/新機器/upstream rebase；故障排除→一行指標指 ops/LESSONS.md）
4. 文件系統規則（三材質表、時態分離、lint 運作模式與 [adr-amend] 豁免、errata 流程）
5. 提問／決策紀律（工程自拍、拍板級才問、大白話選項、granular 攤開）
6. 不要做的事（精選硬禁令）
※ 明確不含：reference data（→generated/reference）、進度 marker（→ops/NOTES＋
   generated/STATE）、gotcha 長註記（→ops/LESSONS）、repo 目錄樹全景（→活書 §5）
預算：≤250 行（lint L7 強制）
```

**骨架第 2 節的兩個內嵌範本**（B3 直接取用、免跨 rev 重寫走樣）：
- **SDD 5 步**＝specify（input＝brainstorm 檔）→ clarify → plan → tasks → analyze，每步後 commit；specify 必**手動**起手、不排進 brainstorm 流程內自動觸發（否則 feature-branch pre-hook 不會跑——rev3 實證教訓、亦見 §5.3）。
- **TDD 驅動提示詞範本**（隨 rev4 環境實況微調）：

```
讀 specs/<NNN>-<name>/tasks.md → act-on-code 接地、依實際相依把 tasks 分執行單元；
驗收對照 spec.md。編排用 Workflow 工具：每執行單元一支，內部 serial 跑
implementer(TDD) → spec-compliance review → fix 迴圈 → code-quality review → fix 迴圈。
每個 agent prompt 烤進不可違反項：rust 全程 serial、容器內 build/test、
review agent 只讀不寫 repo 檔、★絕不 push/merge。
主線只在單元邊界醒：復核＋load-bearing 自驗＋bump submodule pin → 啟下一支。
全單元完成 → final holistic review → finishing-a-development-branch
（push/merge 需 user 同意）→ 收刀簿記三步（events append＋NOTES＋docs-sync generate）。
```

### 4.4 events.jsonl 欄位規格（L3 schema 依據）

```
feature_close（收刀；必填除非標「選」）：
  type:"feature_close"｜feature:"NNN-slug"｜merge:"短SHA"｜date:"YYYY-MM-DD"
  summary:"一句話"｜pins:{web:"SHA",api:"SHA"}｜adrs:["0007",…]（無則空陣列）
  arch_impact:["§6",…] 或 "none"｜backlog_add:["B-021",…]｜backlog_done:["B-014",…]
  kind:"vertical"|"horizontal"（選、預設 vertical）
  spec_supersessions:[{feature,item,note},…]（選）｜notes:"…"（選）

review（審查輪）：
  type:"review"｜date｜scope:"001-005 cumulative"｜report:"reviews/YYYYMMDD-….md"
  findings:{total:N, fixed:N, to_backlog:["B-…"], wontfix_adr:["00NN"]}
  ★ L5 斷言：fixed＋len(to_backlog)＋len(wontfix_adr)＝total

misc：
  type:"misc"｜date｜summary（infra 級里程碑：bootstrap 完成、graphify 重建…）
```

---

## 5. 知識匯出包

### 5.0 讀法與編號降級規則

三張清單是 rev4 重審設計的原料（K1/K2＝每刀 brainstorm 直接輸入；K3＝`ops/LESSONS.md` 初始內容）。萃取方式：多 agent 平行讀 rev3 的決策帳／review 統整／backlog／工作區指引／per-machine memory，每筆附出處供抽查；清單為**候選性質**——真正拍板在 rev4 逐筆重審時。

**編號降級規則（本清單的產製紀律、也是 rev4 引用 rev3 的永久規則）**：①rev3 編號只出現在出處欄、以 `rev3:` 前綴開頭標示——**出處欄內後續座標視同同源、免重複前綴**（如「rev3:CHECKLIST§4.2＋§5-⚠️n」）；②條目本文自解釋、禁裸用 rev3 編號——**內容過境、編號不過境**；③每筆配新編號（K1-NN/K2-NN/L-NNN）、條目互引只用新編號；④本文內 rev3 刀號寫全稱 `rev3-NNN` 或刀名（出處欄內免此規則）；⑤K1 轉正式 ADR 時 front-matter 記 `provenance: "rev3:…"`（純字串族譜、非依賴）；⑥rev4 lint L11 詞典含 rev3 碼 pattern 反走私——**「｜出處：」起始的行整行豁免**。

### 5.1 K1｜rev3 設計結論候選（44 筆＝rev3 決策表全列、零跳過）

> 讀法：〔狀態·建議〕已決 37＋開放 7；建議標記僅為萃取時的初判（沿用 30／重審 5／— 9），**真正拍板在 rev4 逐筆重審時**（處置時點與批次劃分見 §4.2 B6／B8）。開放項＝rev3 未決、直接成為 rev4 待拍板輸入。

- **K1-01｜後端路由結構**〔已決·沿用〕｜出處：rev3:DECISIONS§1-待決①
  後端路由維持全部逐條寫在單一 main.rs（不重整成獨立 router 目錄樹），配合端點覆蓋 lint 鎖「路由表＝端點註冊表＝權限 seed」三源一致；重整樹被否，因 lint 第一源會從單檔變多檔、丟掉已驗證模式。（建議理由：沿用前代已驗證模式、無疊層或反轉訊號的穩定決策。）
- **K1-02｜wire 契約機器化**〔已決·沿用〕｜出處：rev3:DECISIONS§1-待決②
  wire 契約驗證採「前端 typings 為裁判」：從型別宣告抽 JSON Schema 唯讀比對、每條路由必有 contract case 的覆蓋 gate、錯誤碼表 table-driven；瀏覽器捕獲降為補充回歸素材，顯式契約覆寫記入帳本（初始為空）。（建議理由：穩定執行中；列內僅留「端點增速時再評 OpenAPI 案」的再評條件、未觸發。）
- **K1-03｜縱切第一刀選定**〔已決·沿用〕｜出處：rev3:DECISIONS§1-待決③
  縱切第一刀選最輕、低風險、欄位最少的系統設定功能打樣整條管線（migration→facade→handler→授權→wire→前端），骨架先打通再上最重的使用者管理刀；user 親決、推翻先前「使用者直刀」傾向。（建議理由：排序決策已執行且「便宜打樣先行」模式實證有效；惟列內註明 user 親決的實際理由待補。）
- **K1-04｜選擇性外鍵**〔已決·沿用〕｜出處：rev3:DECISIONS§1-待決④
  資料庫外鍵採選擇性：僅使用者-角色 join 表加 FK（純關聯＋硬刪＋無 soft-delete 互動＝零代價擋懸空列），其餘 11 表維持零 FK（soft-delete 與系統操作者 null 語意與 FK 相棘）；零 FK 處以應用層參照完整性集中清單補義務。（建議理由：工程預設直接批准、無疊層訊號的穩定決策。）
- **K1-05｜凍結邊界劃分**〔已決·沿用〕｜出處：rev3:DECISIONS§1-待決⑤
  constitution 凍結邊界拍定：表格原型四變體整組＋行為島狀態機不變式＋wire 錯誤碼表（含分頁形與信封例外）入凍結；欄級字典與常數值（grace 秒數等）留設計書。配套修訂分級：方向性不變式反轉＝MAJOR、其餘細項調整＝MINOR。（建議理由：治理骨架決策、後續多次修憲皆循此分級運作無礙。）
- **K1-06｜儀表板取向**〔開放·—〕｜出處：rev3:DECISIONS§1-待決⑥a
  user-facing 儀表板是否做、怎麼做仍未決；目前工程預設傾向 v1＝固定儀表板、零新表；入波排程時才需拍板、不阻塞既有波次。
- **K1-07｜報表匯出取向**〔開放·—〕｜出處：rev3:DECISIONS§1-待決⑥b
  報表匯出（PDF/CSV）仍未決；目前工程預設傾向 v1＝同步匯出、零新表；入波排程時才需拍板。
- **K1-08｜靜態加密取向**〔開放·—〕｜出處：rev3:DECISIONS§1-待決⑥c
  靜態資料 AES-256 加密仍未決；目前傾向 v1 在磁碟/tablespace 層處理（加密卷屬部署期決策），最晚於 prod 部署定稿前拍板。
- **K1-09｜合規姿態**〔開放·—〕｜出處：rev3:DECISIONS§1-待決⑥d
  合規姿態是否升級仍未決；目前傾向維持現姿態，待對外開放或多租戶需求觸發時再議。
- **K1-10｜效能可用性目標**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️a
  批准保守預設：列表讀 p95<300ms、寫（含同交易審計）p95<500ms、登入 p95<1s（argon2id 為主成本）、可用性 99.5%/月（容許計畫性維護、恢復＝重啟容器）；場景鎖定 ≤50 並發 admin 後台、不設吞吐 SLA。（建議理由：保守數字批准後全程作驗收目標、無反例訊號。）
- **K1-11｜審計讀端與UI**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️b
  三張稽核 log 表（操作/存取/登入嘗試）補查詢讀端＋僅超管可見的管理 UI，定位 read-only reporting、刻意排在核心 CRUD 資料島之後殿後做；wire 從零設計（前代零讀端、無 mock 可鏡像），配套讀端 filter 索引與選單 seed。（建議理由：排程與範圍決策已如期落地、無疊層訊號。）
- **K1-12｜認證錯誤端點翻案**〔已決·重審〕｜出處：rev3:DECISIONS§1-⚠️c
  翻案改「做」：補認證錯誤 echo 端點＋三個請求 demo 頁進選單 seed（初始僅勾超管）＋驗證碼收發兩端點採 stub 雙模＋時間查詢端點；原「不做」清單同步翻案。（建議理由：包內驗證碼兩端點拍定後實測未落地，連同替代登入 stub 被後續決策延後出波——套件內容與實況已分叉。）
- **K1-13｜redis 映像鎖版**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️d
  redis-stack 映像於建 stack 當下即 pin 數字版，升版一律走顯式 bump commit，對齊「版本鎖點」哲學。（建議理由：簡單明確的版本紀律、無爭議。）
- **K1-14｜內部錯誤走200信封**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️e
  內部錯誤業務碼（5000）一律走 HTTP 200 信封回傳（前端訊息顯示通道僅 200 生效＋「business error 走 200」總則）；內部錯誤映 HTTP 500 的路徑標 test-only 或刪除，contract test 鎖住配對。（建議理由：與前端顯示通道對齊的契約決策、四輪 review 無事。）
- **K1-15｜錯誤碼矩陣凍結**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️f
  13 個業務錯誤碼矩陣整組凍結（含 4 個保留碼——保留碼是前端環境設定分組的實值、刪碼即破壞契約）；contract test 斷言後端從不發出保留碼。（建議理由：後續多刀（節流、IP 閘）皆刻意 reuse 既有碼不新增、凍結持續被尊重。）
- **K1-16｜rev2 源碼受控參照**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️g
  授權中介層改述為「enforce 層全新寫（in-tree、無獨立 crate）」；對前代原始碼立場＝受控參照——允許閱讀對照驗證、禁止拷貝（重新打字消化）、加防回歸條款（rev3 已推翻的行為不得帶回）；僅工具 crate（ORM adapter、IP 定位庫）例外整檔拷貝。（建議理由：血緣治理決策、全程被遵循且無反轉。）
- **K1-17｜排程拍板重議規則**〔開放·—〕｜出處：rev3:DECISIONS§1-⚠️h
  排程性拍板（stub 模式等排程類結論）若要重議，必須走正式 amendment 流程、不得默改；屬常備治理規則、目前無重議觸發。
- **K1-18｜inline 授權窄邊界**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️i
  前端 inline 改動授權採窄邊界起點：管理頁接線軌道一次授權五種前代已驗證用途、之後每個新用途一律走 amendment；建置設定軌道不收錄（其議題已消解）、日後需要再另行新授。（建議理由：後續兩次新用途擴充均照 amendment 程序走、治理模式如設計運作。）
- **K1-19｜後端源倉沿用**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️j
  後端源倉沿用既有 GitHub repo（倉名含前代字樣為永久名、不改），僅另開 rev3 整合新分支；不另建新倉。（建議理由：一次性基礎設施決策、已落地無爭議。）
- **K1-20｜migration 短編號**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️k
  migration 檔名採短編號加語意名（編號遞增、依檔名序執行、語意在檔名），棄長零串時間戳——前代 live 稽核實證長編號抄錄必錯（8 條引用多打一個 0）。（建議理由：有前代實證支撐的命名紀律、全程沿用無礙。）
- **K1-21｜設定多鍵熱讀**〔開放·—〕｜出處：rev3:DECISIONS§1-⚠️l
  系統設定多 key 熱讀仍未決：現行單鍵 swap 夠用，需要時再把它推廣為 keyed map（屬設計變更、非預設）；不阻塞任何刀。
- **K1-22｜替代登入延後**〔已決·重審〕｜出處：rev3:DECISIONS§1-⚠️m
  替代登入四流程 stub（重設密碼/驗證碼登入/註冊/綁微信）＋其驗證碼端點延後到核心授權波之後的 v1 完備性補完時段（前端表單已完整但後端全缺、v1 功能價值低）；「v1 啟 stub 模式」原拍板不變、僅重排時程，並循 amendment 程序非默改。（建議理由：延後項至今未排程落地，且列內註明驗證碼端點先前隨完整包拍定卻實測未落地，rev4 須重新決定取捨。）
- **K1-23｜log 表保留政策**〔開放·—〕｜出處：rev3:DECISIONS§1-⚠️n
  三張稽核 log 表的 DB retention 政策仍未決；v1 僅做容量監控、清理策略 defer，容量警示觸發時再拍。
- **K1-24｜應用層RI分層**〔已決·重審〕｜出處：rev3:DECISIONS§1-⚠️o
  應用層參照完整性驗證採 hybrid 分層（user 親決）：單一 entity 內純參照檢查下沉 facade 自驗（slim error enum、不依賴全域錯誤型免層級倒置）；跨 facade、需上下文、還原跳驗類留 handler 編排；DB 能擋的（unique）續走 DB 錯誤映業務碼。取代「全 handler 層驗」舊取向。（建議理由：列內明言接受代價（每個自驗 method 多一個 error enum＋handler match），rev4 可重看分層切線是否仍最優。）
- **K1-25｜demo 頁全入seed**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️p
  翻案：全部 demo 頁進選單 seed、初始僅勾給超管角色；不啟用任何前端隱藏機制（hideInMenu／頁面排除皆不用），可見性全交角色勾選層（casbin 選單維度）治理下放；推翻前代的隱藏取向。配套盤點確認僅 4 頁依賴 API、零新端點需求。（建議理由：翻案後一次定案、治理下放模式與整體 RBAC 設計一致。）
- **K1-26｜worktree 起點血緣**〔已決·—〕｜出處：rev3:DECISIONS§1-⚠️q
  前端 worktree 取 clean-slate 血緣（自官方 example 分支衍生）＋整批移植前代完成接線再改名；後端依波次從零重寫（自 Initial commit 起）。★ one-shot 史料、已消費完畢：其中「整批移植前代接線」已被 Q9「從上游重來」推翻、**不得作為 rev4 施工指引**；僅「clean-slate 血緣自官方 example 衍生」續用（§4.1 已採）。
- **K1-27｜id 忠實序列化**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️r
  廢除前代「id 全字串」凍結，改逐欄位忠實前端 typings：DB 一律 i64 自增，僅 typings 宣告 string 的少數欄位在序列化邊界轉字串、其餘回 JSON number，並加 2^53 fail-loud 守衛；型別謊言帳本自此歸零起算。刻意偏離前代拍板。（建議理由：根治前代型別謊言之痛的決策、user 對契約靜默漂移高度敏感且此案全程無事。）
- **K1-28｜fork差異標記紀律**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️s
  fork 差異執行紀律＝雙模式＋統一標記：修改型保留 upstream 原行註解緊鄰新行；新增型以標記圈界（新檔僅檔頭一行）；標記統一含可 grep 的 token（一次 grep＝完整 fork patch set）；rebase 解衝突時同步把原行註解更新為 upstream 現行版。（建議理由：為 upstream 常態 rebase 而設的紀律、全程執行無礙。）
- **K1-29｜schema squash 基線**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️t
  schema 交付採「前代終態 squash 基線＋rev3 delta 顯式分離、rev3 首波一次全建」：一支 migration 忠實濃縮建全部表（零 FK 原樣）＋一支 seed 淨效果，rev3 新拍板差異另起顯式 migration；以雙庫互 diff（pristine 重放＋正規化）驗證 squash 零漂移；後續刀改「驗表已在＋補刀特有 seed」。（建議理由：列內兩處勘誤皆為數字口徑校正、決策本體未動且驗證閉環完備。）
- **K1-30｜自查題組不增題**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️u
  否決在 constitution 自查題組增列「plan/tasks 是否把 push/merge 排入實作期」一題、日後不再議——該紀律已固化於工作區指引核心紀律＋凍結令＋人工 review，增題冗餘。（建議理由：顯式 close 且註明日後不再議。）
- **K1-31｜casbin 委派建表**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️v
  casbin 規則表採委派式建表：migration 內呼叫 adapter 的建表函式建基底欄＋同檔 ALTER 補治理欄成終態；adapter sub-crate 併入 schema 基線刀（整檔拷貝例外）、獨立刀消解。否決手寫 CREATE：雙 schema 來源＋唯一鍵約束細節手抄成本＋adapter 升版漂移隱患。（建議理由：保「單一 schema 來源」紀律且與 runtime 自建行為一致、無後續爭議。）
- **K1-32｜登入失敗節流**〔已決·重審〕｜出處：rev3:DECISIONS§1-⚠️w（019-login-lockout 刀）
  登入失敗節流：唯讀消費既有登入嘗試表、登入前置以滑動 15 分窗計失敗數，單帳號 5 次／單 IP 20 次任一達標即短路擋（reuse 既有業務碼；回靜態一般化訊息、不洩剩餘時間/維度/帳號存在性防枚舉）；計數查詢失敗 fail-OPEN 放行；被擋嘗試仍匯流既有單一寫點留審計痕、滑動窗自動解鎖。（建議理由：列內留原案疊層（「前端顯示鎖定 N 分鐘」措辭已被推翻改一般化訊息），且「gated 列必寫審計」半條後被 redis 負快取刀有意識反轉——rev4 應以合成後終態重新表述。）
- **K1-33｜覆蓋lint換波豁免**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️x
  端點覆蓋 lint 結構上需首個受保護業務端點存在才立得起來，而 rev3 波 0（純地基波）零 gated 業務端點——故該波出口三守恆豁免此項、移交波 1 第一刀隨首個 gated 端點接線時一併建立；其餘二守恆（entity 存取 lint、migration 往返）照常。（建議理由：一次性換波豁免、已如期兌現且 lint 後續持續守恆。）
- **K1-34｜錯誤訊息前端翻譯**〔已決·重審〕｜出處：rev3:DECISIONS§1-⚠️y
  業務錯誤訊息多語系採前端翻譯：wire 的 msg 欄改載穩定 i18n key（後端語言無關、不在地化），前端攔截器以 $t 翻譯、未命中 key 時原字串 graceful fallback；key 文法＝四根命名空間＋「根.實體.條件」、前端 locale 外包一層 backend 前綴。否決後端在地化（免雙邊翻譯漂移）。（建議理由：列內明言接受代價——後端 log/curl/審計裡 msg 全變 key、人話可讀性下降；rev4 可重評是否補齊觀測側可讀性。）
- **K1-35｜編號接續慣例**〔已決·—〕｜出處：rev3:DECISIONS§1-⚠️z
  決策點編號單字母用盡後改雙字母接續往後排的登記慣例（純表格管理規則）。
- **K1-36｜i18n 接線軌道**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️aa
  為後端訊息翻譯接線新增專屬前端接線軌道（MINOR 修憲）：授權三範圍——請求攔截器的 msg 翻譯接線（限指定顯示點、不改控制流）、locale 檔新增 backend 命名空間、i18n Schema 型別＋翻譯 helper；否決塞進既有純新檔軌道（語意混淆、audit 不清）與不修憲（治理鏈留洞）。（建議理由：補齊治理鏈的必要軌道、user 親決且後續各刀 i18n 皆循此軌。）
- **K1-37｜wire 凍結措辭釐清**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️ab
  constitution 措辭 PATCH：釐清「wire 凍結事實」指錯誤碼本身；msg 自改載 i18n key 起即非人話字串（後端語言無關、前端翻譯）。非新決策、純消除早於 i18n 拍板的措辭 staleness。（建議理由：釐清型 PATCH、對齊既決事項無獨立爭點。）
- **K1-38｜角色軟刪清授權**〔已決·沿用〕｜出處：rev3:DECISIONS§1-P-011-1（020-role-delete-policy-archive 刀）
  角色軟刪不清授權＋代碼可重用會讓重建同代碼靜默繼承舊授權（高危提權）；修向＝刪時同交易把該代碼全維度授權歸檔（資料不丟）並自規則表移除，歸檔列讀時衍生判定為不可手動復原（零 migration）、復原請求回業務碼拒絕；並收緊並發窗——四類 casbin 寫端一律先 FOR-UPDATE 鎖角色列、角色已刪即拒授權。（建議理由：root-cause 修向、user 親決收緊案並明文推翻舊「軟刪殘留無害」前提，落地後全綠穩定。）
- **K1-39｜無retrofit釐清**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️ac
  constitution 釐清 PATCH：「無 retrofit」的標的是表格原型審計欄（防「建表漏審計欄事後補」的前代債）；既有表加業務/鑑識欄的刻意、規劃、可逆演進不在此限（前提＝審計欄規則不變、非意外債）。非新決策、釐清原意。（建議理由：釐清型 PATCH、為後續合規演進提供正式背書且無爭議。）
- **K1-40｜鎖定負快取層**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️ad（021-login-lockout-redis-cache 刀）
  對「已生效鎖定」在登入閘最前加 Redis 負快取層（帳號/IP 雙維度 key、固定 900 秒 TTL 且命中不續期防攻擊者永久鎖死帳號）、DB 維持鎖定真相——堵分散式打單帳號下的 DB 讀寫放大；Redis 掛掉 fail-OPEN 退回 DB 滑動窗。鎖中命中不逐筆寫稽核、量級改節流麵包屑進觀測層＝有意識反轉「每終端結果恰一列稽核」與「gated 列必寫」的既有要求（上鎖前歷程仍照寫、非違憲）。（建議理由：user 親決；列內歸屬勘誤僅為文件標註錯誤已修正，決策本體穩定，反轉舊要求屬本列刻意設計而非被翻。）
- **K1-41｜IP存取控制閘**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️ae（022-ip-access-control 刀）
  IP 存取控制閘＋第 3 ingress 正式化：全站每請求比對真實來源 IP，白名單命中放行＞黑名單命中阻擋（reuse 既有 403 碼、不增新碼）＞其餘 default-allow；DB 規則表為真相、載入 lock-free 記憶體結構 μs 判定（被擋成本有界、DoS-resilient）＋門鈴熱刷新，全程 fail-OPEN；配套寫端自鎖防護、私網結構豁免、白名單跳登入節流、admin 手動解鎖。CF Tunnel 直連後端以窄信任來源＋標頭 fallback 還原真實 IP（內網非 tunnel 來源偽造不採信）；部署 footgun（tunnel 來源必須包含於內網信任集、否則 fallback 不觸發）經驗證 code fix 不足、以文件化約束處理。（建議理由：user 親決＋三位獨立冷讀 reviewer 全數通過；footgun 的文件化處理是驗證後的有意識選擇而非妥協。）
- **K1-42｜列表排序授權**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️af（023-list-column-sort 刀）
  前端接線軌道 MINOR 修憲加新用途：授權在既有管理列表頁 inline 掛欄位排序（sorter props、受控排序狀態、工具列清除排序控制），嚴格限「列表排序」、不擴張其他 inline、不改共用表頭元件本體；配套 composable/元件/typings 循既有新檔軌道，非法排序回業務碼由前端翻譯；再下一個新用途仍走 amendment。（建議理由：循 amendment 程序的邊界擴展、授權範圍如實落地且冷讀 review 通過。）
- **K1-43｜管理頁補控件判準**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️ag（024-password-policy 刀）
  既有「管理頁鏡像」授權用途涵蓋事後在同頁補 render 控件分支（數值型輸入控件）——判定屬該頁本就按值型別分派的 dispatcher 補完（單頁、純加、復用既有 wrapper、零新 key/元件/路由），不算新用途、constitution 不 bump；與跨多頁新能力（須修憲）畫出「補完 vs 新能力」判準線。（建議理由：治理判準清晰、user 親決且如實落地，為後續同類判定提供先例。）
- **K1-44｜自助頁軌道授權**〔已決·沿用〕｜出處：rev3:DECISIONS§1-⚠️ah（025-user-center 刀）
  前端接線軌道 MINOR 修憲加新用途：授權在管理頁樹之外新增登入者本人自助頁（profile 檢視/編輯＋改密碼消費密碼複雜度政策＋手機/郵箱驗證佔位），嚴格限「本人自助」、不擴及管理他人資料或任意新 UI。收尾另拍修改時間語意：一律顯示 raw 更新時間（null 顯「未修改」）＋操作者分類（system/self/admin、本人不標註、不洩操作者），推翻原「僅管理員改動才顯示」設計（user 給具體渲染範例校正）。（建議理由：user 親決 amendment、收尾語意經具體渲染範例校正後定案並如實落地全綠。）

### 5.2 K2｜翻案／遞延候選（39 筆）

> 讀法：「設計域重想」＝rev3 已露疲態的決策域（多次改向、當時妥協的接受理由可重估）；「遞延補全」＝rev3 登記未做、rev4 可內建或首發的能力。與 K1 重疊者已刪（K1 開放項為準）；儀表板／報表匯出／靜態加密／合規／settings 多鍵熱讀見 K1 開放項。

**〔設計域重想〕**

- **K2-01｜登入節流計數失敗時 fail-OPEN 放行**｜出處：rev3:REVIEW§6（019-login-lockout research.md D-07）
  當時接受「節流計數查詢出錯即視為零次失敗、照常放行登入」，理由＝節流定位為 best-effort 縱深防禦、DB/快取抖動不可鎖死全站登入入口；代價是儲存層異常期間暴力嘗試完全不受節流，rev4 可重新權衡 fail-OPEN 的適用範圍或至少加降級告警。
- **K2-02｜帳號級鎖定可被第三方惡意觸發（鎖他人帳號的 DoS）**｜出處：rev3:REVIEW§6
  當時接受任何人對目標帳號連續錯密即可將其鎖住的拒絕服務面，理由＝滑動窗最長約十五分鐘自動解鎖、傷害自限；rev4 若門檻/窗值改為可調、或引入漸進延遲/CAPTCHA 類手段，此妥協值得重估。
- **K2-03｜XFF 信任模型整段內網預設信任**｜出處：rev3:REVIEW§6（013-xff 刀明示排除）＋rev3:CLAUDE.md§8.2 tunnel footgun
  當時接受「內網整段皆可信其轉發標頭」的寬信任錨（來源刀 spec 明示排除收窄），後續 tunnel 直連 ingress 又疊上「tunnel origin 必須落在該寬段內、fallback 才會觸發」的隱性耦合；rev4 值得改成最小化信任錨（僅列舉真實 proxy origin）。
- **K2-04｜XFF 鏈的 CDN 位置錨不驗證不受信段**｜出處：rev3:REVIEW§6（CONFIRMED-low）＋rev3:CHECKLIST§3.J
  當時拍板 CDN 錨只做位置錨定、不做硬驗證，防偽造靠網路層主防線＋帶內「有錨≠已驗證」的信心訊號，review 判為已確認的低風險弱點並接受；rev4 若 ingress 拓樸簡化，可重估是否對錨點上真驗證。
- **K2-05｜session 踢除策略域三度改向**｜出處：rev3:REVIEW§5（006→014、009→014 映射列）
  此域 rev3 至少改三次：單一 session 從「永遠踢舊」反轉為「政策感知、政策關閉時放行多 session」，再補「停用/刪除帳號即時硬撤 session」與 refresh token 輪替/黑名單——rev4 值得先把 session 生命週期（併發、踢除、撤銷、輪替）一次設計完整再動工。
- **K2-06｜登入嘗試審計「恰寫一筆」不變式反覆反轉**｜出處：rev3:REVIEW§5（007→021、019→022 映射列）＋§2（019 列）
  「每個登入終局恰寫一筆嘗試紀錄」先被 redis 第一層快取短路命中不落庫推翻、再被白名單 IP 整段跳過節流推翻，前刀 spec 只能靠 as-built 勘誤註記續命——審計完整性與快取短路的邊界值得 rev4 第一性重想。
- **K2-07｜系統設定域「先打樋後回填」被回填三次以上**｜出處：rev3:REVIEW§5（008→014→024 映射列）
  系統設定最初以最小 KV 打樋（單設定列、值明文直通、熱套用明示不做、簡陋版面），之後被熱套用 watcher 反轉、再被版面重構＋型別驗證＋密碼政策七列擴充——rev4 若仍走打樋策略，值得先定型別驗證/熱套用/UI 分區的骨架再留空。
- **K2-08｜IP 取證欄位與信任模型逐 ingress 重挖**｜出處：rev3:REVIEW§5（004/005→013→022 映射列）
  日誌實體從單 IP 欄擴成四欄取證（動了可逆 ALTER 回填舊表），信任鏈之後又為 tunnel 直連第三 ingress 加 fallback 擴充——每新增一種入口就重挖一次 IP 語意；rev4 可先枚舉 ingress 拓樸全貌再定 IP 欄位形。
- **K2-09｜編輯模式帳號名欄可改但後端靜默不寫**｜出處：rev3:REVIEW§3.2-F-5
  當時 user 拍板維持 upstream 原樣（零 fork-delta 優先於 UX 縫隙），接受「改帳號名按確定顯示更新成功但實際未變」的欄位級靜默 no-op（安全無虞）；rev4 若重做使用者管理頁，編輯模式直接鎖該欄即可消滅此縫隙。
- **K2-10｜個人資料部分更新缺「清空欄位」語意**｜出處：rev3:REVIEW§3.4（025-user-center 項）
  wire 約定 null＝整欄跳過、前端空字串就存空字串，已設欄位無法清回 NULL——當時以「spec 容忍空值＋與管理端路徑行為一致」接受、明言要清空需 wire 契約擴充；rev4 設計部分更新契約時可內建顯式 clear 語意。
**〔遞延補全〕**

- **K2-11｜alt-login 四流程後端補全（驗證碼登入/註冊/重設密碼/綁定微信）**｜出處：rev3:CHECKLIST§4.2-alt-login（⚠️m、原§3.D）
  rev3 前端三張表單完整但後端四流程全缺，整包（stub 端點＋captcha 發送/驗證＋錯誤頁）從波次規劃一路排到版本收尾都沒進場；rev4 若沿用同款登入頁應開場就拍做真或砍表單，且啟用註冊/重設密碼表單時必同修既存的確認密碼規則值快照 race（个人中心刀已立 toRef 修法範式、這兩頁 rev3 刻意未動）。
- **K2-12｜手機/信箱真實驗證＋驗證碼改密路徑**｜出處：rev3:CHECKLIST§4.2（025-user-center 刀）
  rev3 个人中心自助頁的手機/信箱驗證與驗證碼改密全是 UI 佔位（按了 toast 建置中、僅舊密碼路徑真改密），接 SMS/信箱服務明確劃為未來版本；與 alt-login 共享 captcha/簡訊基礎設施，rev4 宜同刀或緊接排程、避免佔位控件長期掛在 UI 上。
- **K2-13｜改密後撤既有 session＋密碼政策前端提示補完**｜出處：rev3:CHECKLIST§4.2（025-user-center 刀、接 014 session 原語）
  rev3 改密刻意不動 token rotation/單一 session 不變式（改密後其他既有 session 不強制重登、留給日後 auth 安全 review），且七項密碼政策中「禁止含使用者名」一項無前端即時提示（需把使用者名傳進密碼卡比對、僅後端權威把關）；改密撤 session 是業界常見安全預設，rev4 可在 auth 設計期直接內建。
- **K2-14｜新帳號初始密碼政策化（可配置/隨機生成＋強迫首登改密）**｜出處：rev3:CHECKLIST§4.2（REVIEW-20260702 F-7 登記）；另 rev3:REVIEW§3.3-F-7（登記 CHECKLIST§4.2）
  rev3 建用戶端點初始密碼寫死 123456 且不經密碼複雜度政策驗證——admin 設嚴政策後新帳號一出生就不合政策（rev3 判符合原假設非缺陷、僅登記候選）；rev4 若同時有密碼政策與建用戶功能，初始密碼生成應開場就納入政策管轄並配首登強制改密。
- **K2-15｜obs 告警通知投遞 channel**｜出處：rev3:CHECKLIST§4.2（018-observability 刀）
  rev3 觀測層只 provision 三條 baseline grafana alert rule（條件成立轉 Alerting、僅介面可見），通知投遞（contact point＋notification policy＋email/webhook/IM creds）明確排除在第一版外；沒有投遞的告警實務上等於沒人看見，rev4 排觀測層時值得把最小一條通知管道納入首發。
- **K2-16｜登入節流強化包（IPv6 前綴計數/可調門檻/信任白名單/CAPTCHA/手動解鎖）**｜出處：rev3:CHECKLIST§4.2（019-login-lockout 刀）；另 rev3:REVIEW§6（登記 CHECKLIST§4.2）
  rev3 登入失敗節流以精確 IP 計數，IPv6 來源可在 /64 內輪替前綴規避 per-IP 維度（靠 per-user 維度當主防線硬撐）；門檻寫死不可 runtime 調、無 NAT 共用出口白名單、無鎖後 CAPTCHA、無 admin 手動解鎖介面、鎖定攔截與真 auth 失敗共用審計欄難區分——整組 v2 強化已登記待未來安全 review，rev4 設計節流時可把 IPv6 群組鍵與可調門檻直接收進首版。
- **K2-17｜節流快取遞延組（鎖定壓制告警規則/來源廣度估計/TTL 拆分）＋誤鎖風險升高**｜出處：rev3:CHECKLIST§4.2＋§3.H（021-login-lockout-redis-cache 刀、DECISIONS§1-⚠️ad）；另 rev3:REVIEW§3.4（021 刀項、登記 CHECKLIST§4.2）
  rev3 把鎖後判定移入 Redis 負快取後只發結構化告警訊號、具體「鎖定壓制中」grafana 規則遞延維運；不同來源 IP 數估計（HyperLogLog）不做、IP 維度鎖定鍵 TTL 借用 per-user 窗值待可調門檻時拆分、節流告警麵包屑三步非原子（併發同窗可能重複記一筆、接受為 best-effort）；關鍵教訓是快取讓鎖「更穩定生效」反而推高誤鎖合法帳號風險，帳號-DoS 緩解（白名單/CAPTCHA）優先級應隨之提前。
- **K2-18｜policy 回收桶來源過濾器＋復原判定時鐘硬化**｜出處：rev3:CHECKLIST§4.2（020-role-delete-policy-archive 刀）
  rev3 角色刪除的授權 archive 回收桶第一版只有欄位標示、無按封存來源過濾/分頁器，且「可否復原」判定依牆鐘時間戳假設刪除→重建間時鐘單調（NTP 向後跳錶的極窄窗接受不防、硬化需 archive 存角色 id 當序列 tiebreak＝動 schema）；rev4 設計 archive 表時把來源角色 id 直接入欄、回收桶 UX 一併做齊，可同時消掉兩項。
- **K2-19｜public tunnel origin 支援（信任模型的隧道來源限制解除）**｜出處：rev3:CHECKLIST§4.2（022-ip-access-control 刀、DECISIONS§1-⚠️ae）
  rev3 的 CF Tunnel 直連信任僅在 tunnel origin 落在內網預設段內才成立（靠組態檔註記的 footgun 約束擋著），若未來 cloudflared origin 是公網位址、真實 client IP 還原不會觸發，需把 tunnel 集納入信任鏈第二層跳過集（reviewer 提的簡單併集修法已被主線驗證不足、是真 code change）；rev4 重寫信任模型時應把 tunnel 來源一開始就做成一等信任集而非內網子集特例。
- **K2-20｜列表排序 per-column 索引＋三端白名單同步紀律**｜出處：rev3:CHECKLIST§4.2（023-list-column-sort 刀）
  rev3 列表排序刻意 best-effort（只補登入嘗試表時間欄一支索引），大型日誌表對非索引欄排序可能 seq-scan 慢、拍板「個別欄證實慢再補」；另排序欄白名單分散在後端 match、前端合法鍵表、欄件掛載三端靠人工同步（漏配非破壞性但該欄默默不可排）——rev4 可考慮單一來源生成三端或至少內建 parity 檢查。
- **K2-21｜prod 部署 TLS/信任拓樸落地（cert 卷、trust-model 填值、CF IP 段單一來源、隧道路徑 e2e）**｜出處：rev3:CHECKLIST§4.2＋§3.E（001/013/022 跨刀彙整）
  rev3 一切需要真 prod 環境的項全數遞延：憑證卷是否外部管理未定、信任模型組態待 operator 填實際拓樸、CF 官方 IP 段在 nginx geo 與 trust-model 兩處各維護一份有漂移風險（已登記評估單一來源）、且隧道真實 IP 還原與 IPv6 規則只有單元測未穿全 HTTP e2e（容器內模擬隧道 peer 困難而 defer）；rev4 若有 prod 部署目標，這組應做成部署 checklist＋自動化驗收而非散裝備忘。
- **K2-22｜prod 多副本橫向擴展**｜出處：rev3:CHECKLIST§4.2（014-session 刀 research 拍板不做 v1）
  rev3 明確不做第一版：dev 已驗過雙後端副本的跨副本 policy 收斂不變式，但 prod nginx 仍單一 proxy_pass、無負載均衡；rev4 若目標含水平擴展，LB＋共用 DB/Redis 的拓樸值得在 compose/部署設計期就留位。
- **K2-23｜審計資料 scale：模糊搜尋 trigram 索引＋log/archive retention purge**｜出處：rev3:CHECKLIST§4.2＋§5-⚠️n（012/015/017 審計刀群）
  rev3 審計中心模糊搜尋是 LIKE seq-scan（pg_trgm GIN 需 CREATE EXTENSION＋migration、拍板規模增長再做），三張 log 表與 policy archive 表第一版只有容量監控、無 retention/purge 政策；審計量單調成長，rev4 若審計是核心功能，索引與保留政策宜在 schema 設計期一起定而非事後補 migration。（retention 政策的拍板本體＝K1-23 開放項；本條淨新部分為 trigram 索引與 purge 執行面。）
- **K2-24｜zh-TW 繁體 locale feature**｜出處：rev3:CLAUDE.md§6-下一步；另 rev3:memory/future-zh-tw-locale-feature
  rev3 全程刻意以 zh-CN 為主（密碼政策與个人中心兩刀甚至留了簡繁混用、已標明勿當 bug 修），繁體字典＋語言切換「中文」改「簡體/繁體」整包登記為未來刀；使用方是繁中環境，rev4 可直接把 zh-TW 當首發 locale 而不是事後轉換刀。
- **K2-25｜cleanup sidecar 最小權限 DB 憑證**｜出處：rev3:CHECKLIST§3.A（014-session 刀 cleanup-job 殘項）
  rev3 的清理排程容器直接復用全權資料庫連線 secret（已登記應另立僅能刪過期列的最小權限帳號、low）；rev4 凡有背景 job 接 DB，secret 最小權限應是部署設計預設而非 prod 硬化補丁。
- **K2-26｜obs 採集容器非-root 硬化**｜出處：rev3:CHECKLIST§3.A（018-observability 刀 brainstorm defer）
  rev3 log 採集容器（alloy）以 root 讀 docker.sock 做全容器 stdout 採集、prod 硬化時才改非-root user＋docker group/sock 權限；docker.sock 幾乎等於 host root 權限，rev4 建觀測層起手就照非-root＋權限窄化配置成本最低。
- **K2-27｜prod nginx 完整資源 CSP**｜出處：rev3:CHECKLIST§3.J（correctness/security review 殘項）；另 rev3:REVIEW§6（open low、CHECKLIST§3.J）
  rev3 prod 硬化只上了結構性 CSP（連同 Referrer/Permissions 標頭與登入限流），完整 script/style/connect-src 白名單需 prod-mode 下 CDP 逐源驗證後才敢收緊、仍 open；rev4 前端資源來源固定後可把這步內建進部署驗收流程。
- **K2-28｜登入時序 oracle 拉平**｜出處：rev3:CHECKLIST§3.J-🟡；另 rev3:REVIEW§6（open low、CHECKLIST§3.J）
  rev3 登入對不存在帳號不跑密碼雜湊、回應時間可被用來探測帳號存在性（登記 low、修向＝not-found 也跑 dummy argon2 拉平時間）；rev4 寫 login handler 時一行 dummy hash 就能內建、不必留成安全 review 尾巴。
- **K2-29｜op-log payload PII redaction**｜出處：rev3:CHECKLIST§3.J-🟡；另 rev3:REVIEW§6（open low、CHECKLIST§3.J）
  rev3 操作審計的 payload 前後快照原樣落庫、電話/信箱等 PII 未 redact（登記視合規需求處理）；rev4 設計審計 payload 時應先拍 PII 欄位遮蔽策略——落庫後再遮等於已對所有 DB 讀者外洩。
- **K2-30｜低位安全/正確性殘項群（log injection 上游、XFF 空 token、鎖定計數 race、migration down 非對稱）**｜出處：rev3:CHECKLIST§3.J-🟡（CONFIRMED-low 群）
  rev3 review 留下一組確認過但判 low 的殘項：trace_id 未濾控制字元（log injection 上游、CSV 出口已另行阻斷）、XFF 取前 32 個 token 時含空 token、登入失敗計數讀改寫非原子有 race、早期 migration down 的 casbin 刪除與 up 非對稱、CDN 位置錨對不受信段不驗證；單項皆小，rev4 重寫對應模組時值得當 checklist 逐項內建。
- **K2-31｜IP 閘門政策單一來源（純函式 vs middleware 內聯雙實作）**｜出處：rev3:CHECKLIST§3.E（022-ip-access-control 遺留）
  rev3 IP 存取控制的「白>黑>default-allow」判定有兩份實作——被單元測的純函式與 middleware 內聯版（後者需要命中的 CIDR 做被擋請求的節流觀測麵包屑計數所以沒呼叫前者），目前一致但無 parity 測、改其一恐靜默漂移；rev4 設計時讓純函式直接回傳命中規則、middleware 只做一次呼叫即可根除。
- **K2-32｜protected-reject 錯誤訊息具體化**｜出處：rev3:CHECKLIST§3.H（011/016 治理刀群 own-cut）
  rev3 治理寫端撤到受保護核心授權時整批拒絕，但使用者只看到泛化訊息——facade 已攜被擋明細，缺錯誤型攜帶＋i18n 插值＋「暴露明細是否洩漏」安全評估三件事；rev4 設計錯誤信封時把結構化 detail 插值通道做進去、免得每個守門訊息都停在泛化版。
- **K2-33｜Redis 基建補課（連線自動重連＋session pointer 熱快取）**｜出處：rev3:CHECKLIST§3.H（014-session 刀 robustness＋021 acceptance 實證）
  rev3 的 Redis 連線用 MultiplexedConnection、redis 重啟後卡 broken-pipe 走 fail-open 降級、要重啟後端才恢復（影響 denylist/session/節流全部 redis 功能；修向＝ConnectionManager 或 reconnect/health-loop），另有已批准但 QPS 高才啟用的 session 指標熱快取；rev4 起手選 ConnectionManager 幾乎零成本、可整組消掉。
- **K2-34｜批次軟刪的交易控制去 sentinel 化**｜出處：rev3:CHECKLIST§3.H（010-menu 刀 own-cut）
  rev3 選單批次軟刪用 sentinel DbErr 觸發 rollback（借錯誤型當交易控制流）、登記併下次 menu 治理刀改自管 transaction；rev4 寫批次寫端時直接自管 txn＋顯式整批拒、別再借 error 型繞。
- **K2-35｜空 body 部分更新的提前 no-op**｜出處：rev3:CHECKLIST§3.H（025-user-center 遺留、觸發時做）
  rev3 个人中心的部分更新在 crafted 空 body（全欄位皆缺）時仍 bump 修改時間＋寫一筆前後相同的審計列（前端不可達、只有直打 API 觸發、review 判 low 接受）；rev4 設計部分更新語意時把「全 None 提前 no-op」直接寫進 handler/facade 慣例。
- **K2-36｜settings 值型驗證健壯化（新值型守門＋number 正規化落庫）**｜出處：rev3:CHECKLIST§3.E＋§3.H（008/024 settings 刀群）
  rev3 設定值驗證對非 enum 值型保守放行（新增值型 seed 時要記得補驗證分支＋守恆斷言），number 型寬鬆收「+8」「0008」且照原字串落庫（僅 curl 直送可觸發、UI 數字控件恆正規形）；rev4 設計 KV 設定驗證時把「未知型拒收＋parse 後正規形落庫」當預設、消掉這兩個觸發式備忘。
- **K2-37｜守門 lint 健壯化與 fork-delta 覆蓋 lint 補位**｜出處：rev3:CHECKLIST§3.E＋§3.H（008 lint、⚠️s 候選）
  rev3 端點覆蓋 lint 的抽取假設 route 註冊都用字面字串（改用常數引用就會漏抓、登記須加守門或 self-test），另有 fork-delta inline 標記覆蓋 lint 只停在候選沒建；rev4 若沿用「lint 當憲法執法」策略，抽取健壯性與標記覆蓋應一起進首版。
- **K2-38｜obs 面板與 metrics 慣例補強（docker 友善 dashboard、計數器 pre-register、pushgateway 持久卷）**｜出處：rev3:CHECKLIST§3.I（018-observability 刀）
  rev3 postgres dashboard 用了依賴 k8s label 的 community 板、docker 下部分 filter 面板恆空態（修向＝換 docker 友善板或改寫變數 query）；casbin deny 計數器未 pre-register 0（重啟至首次 deny 前序列不存在、面板空態非 0）、pushgateway 無持久卷重啟失憶——rev4 建觀測層時把這三個 docker/metrics 慣例直接當起手規範。
- **K2-39｜completion log 噪音治理**｜出處：rev3:CHECKLIST§3.I（018-observability by-design＋022 ipgate 註記）
  rev3 觀測層「每請求一行」設計連無認證請求都輸出（healthcheck 每次、metrics scrape 每 15 秒各一行 INFO），IP 閘門阻擋的洪水請求同樣每請求一行——皆 by-design 靠 72 小時 retention 界範圍，可選的 path 過濾/降採樣要權衡 trace_id join 完整性；rev4 設計 request log 時可預留 path 級過濾開關而非全有全無。

### 5.3 K3｜教訓種子（101 筆＝rev4 `ops/LESSONS.md` 初始內容）

> 讀法：L 編號即 rev4 正式編號（LESSONS.md 直接以此檔起手、後續 append）。〔流程〕前綴＝協作/編排類教訓。三源合併去重（review 方法論＋工作區指引 gotcha＋per-machine memory 正式提取進 repo）。

**〔環境與工具鏈（WSL2／docker／cargo／vite）〕**

- **L-001**｜Windows host 的 git autocrlf 會把 .sh/.yaml/.conf 換行改成 CRLF，容器內腳本與設定檔直接壞掉。
  防：repo 以 .gitattributes 強制 LF。｜出處：rev3:CLAUDE.md§2-目錄樹註
- **L-002**｜WSL2 NAT 網路模式下，host 的 127.0.0.1 打不進容器映射 port，curl 全失敗看似服務沒起。
  防：設 .wslconfig 的 mirrored networking（Win11 22H2 以上預設），或用 wsl hostname -I 拿 WSL IP 連。｜出處：rev3:CLAUDE.md§8.2.1
- **L-003**｜Docker Desktop WSL2 重度 churn 後，host 經 127.0.0.1 打容器 port 單請求可慢到超過 4 秒，短 --max-time 的 curl 回 000 看似 port-forward 死、實則 server 活著——曾因此誤判「網路全斷」還多請 user 重啟 Docker Desktop。
  防：別用短 timeout 判生死：改 curl localhost（走 IPv6 快路徑）或拉長 timeout；最可靠是容器網路內驗（docker compose exec 進 base-web 用 node http.request 直打 rust-api），完全繞過 host port-forward。｜出處：rev3:memory/wsl-host-portforward-slow-use-localhost-or-container-net
- **L-004**｜down -v 後或新機器首次 up --wait，base-web（約 140 秒 pnpm install）與 rust-api（約 240 秒 cargo build）冷編譯期間 healthcheck 會 flap、up --wait 可能非零退出，看似啟動失敗實為還在編譯。
  防：先 docker compose ps 判斷是否仍在編譯（非真失敗），待穩後重跑 up --wait 即過。｜出處：rev3:CLAUDE.md§8.2.1
- **L-005**｜dev image 升級 rust toolchain 後，cargo cache named volume 仍掛著舊 toolchain 內容、遮蓋 image 內新版。
  防：手動 docker volume rm 該 cargo cache 卷後重 build。｜出處：rev3:CLAUDE.md§8.2.1
- **L-006**｜host 開機過久後，glibc 基底容器（rust-api dev）內每次 cargo 都崩 ld.so 的 R_X86_64_RELATIVE 不一致、容器 exit 127——連純 cargo --version 都崩，代表是 host 層 WSL2 loader 故障，不是 volume 或容器狀態壞（alpine 基底映像不受影響）。
  防：重啟 Docker Desktop（完整 Quit 再開）或 wsl --shutdown 後重啟 stack 即復原；別誤刪 volume 重編，worktree 改動在 /mnt/d 安全。｜出處：rev3:CLAUDE.md§8.2.1
- **L-007**｜rust 各 task 即使被標為可平行，平行跑 cargo 會互撞共用 target 目錄。
  防：rust build/test 全程 serial，不平行 cargo。｜出處：rev3:CLAUDE.md§3-階段2
- **L-008**｜WSL2 /mnt/d 上改完 .rs 後 cargo 可能因 stale mtime 沒察覺變更、跑舊 binary 回假綠——沒重編、handler 簽名不符仍顯示通過。
  防：容器內編譯/測試前先 force-touch 對應 crate 的所有 .rs（find 加 exec touch）再 build。｜出處：rev3:CLAUDE.md§8.2.1
- **L-009**｜cargo test 後面裸接測試名會被當成 test-function 名 filter，0 命中卻顯示「ok. 0 passed; N filtered out」——測試根本沒跑卻看似綠。
  防：跑整支整合測試 binary 必用 --test 旗標指名；看到「0 passed / N filtered out」立即當警訊而非通過。｜出處：rev3:CLAUDE.md§8.2.1
- **L-010**｜server 是 bin-only crate（無 lib.rs），tests 目錄的整合測試無法 use 該 crate 的內部 API，硬寫就編不過。
  防：需呼叫 crate 內部 API 的測試放 in-crate 的 cfg(test) 模組、掛 ignore 標記加環境變數 gate——預設測試跳過（無 DB 仍綠），live 跑時加 --ignored --test-threads=1。｜出處：rev3:CLAUDE.md§8.2.1
- **L-011**｜WSL2 drvfs（/mnt/d 的 NTFS 掛載）上用 Edit 工具連發多筆編輯會間歇報 ENOENT statx 或「file modified since read」，但寫入多半其實已成功——當失敗重做會重複寫入或腦補錯誤狀態。
  防：逐一編輯不連發；報錯時先用 grep/Read 回讀磁碟驗證是否已生效，已生效就跳過不重做；大量改動時以確定性 grep 驗證為準、不信 Edit 回傳訊息。｜出處：rev3:memory/wsl-drvfs-edit-flakiness；另 rev3:CLAUDE.md§8.2.1
- **L-012**｜[流程] 工具環境抖動時 Write/驗證可能假性回報成功而檔案未落地（另見 stdout 重複、工具結果混入模型敘述）——「回報成功」不等於「真的成功」。
  防：關鍵寫檔（commit、不可重得資料、交棒文件）後用獨立命令二次驗證（git cat-file、wc -c、json.load）並展示輸出；結果錯亂就停下明說不可信、絕不腦補填補。｜出處：rev3:memory/tool-result-flakiness-incident
- **L-013**｜rust-api dev 用 cargo watch 的 poll 模式（刻意，因 WSL2/9p inotify 不可靠），重編有偵測延遲、且 stale mtime 可能讓它重編到舊碼——活體驗收會打到舊 binary、新 endpoint 回 404。
  防：跑 curl/psql/CDP 活體前先確認 rust-api log 有重編完成且新 endpoint 回 200；沒上就 force-touch 加 restart rust-api。｜出處：rev3:CLAUDE.md§8.2.1
- **L-014**｜base-web vite 沒熱載新加的 service fn 時，瀏覽器丟「does not provide an export named …」SyntaxError、該頁掛不起來、list API 完全不發。
  防：症狀出現即 restart base-web（pnpm install 走卷快取、秒級就緒）。｜出處：rev3:CLAUDE.md§8.2.1
- **L-015**｜新增 i18n locale 鍵後 dev vite 可能沒熱載新字典，瀏覽器 toast 顯 raw key 而非譯文——curl（回業務碼＋key 看似正常）、typecheck、source grep 三者全綠都掩蓋，靜默無 error、唯 CDP 實渲染抓得到（curl 不等於 modal 的 i18n 變體）。
  防：加 i18n 鍵的 feature 跑 CDP toast 驗收前先 restart base-web，且腳本斷言頁面無 raw key（不只看有 toast）；committed 碼本身正確、prod build 會把 locale 編進去。｜出處：rev3:memory/vite-stale-locale-new-key-raw-toast；另 rev3:REVIEW§4（019 已閉合項）；rev3:CLAUDE.md§8.2.1
- **L-016**｜front-nginx 是 bind-mount 單一 conf 檔，改完 conf 跑 restart 會炸 OCI runtime mount not found（Docker Desktop WSL2 bind-mount 快照路徑失效）。
  防：front-nginx 改 conf 後一律 up -d --force-recreate 該 service，不能用 restart。｜出處：rev3:CLAUDE.md§8.2.1
- **L-017**｜prod baseline 模式不啟 acme、憑證不會自動取得，named certs volume 沒先 seed 憑證時 HTTPS 端無 cert 可用。
  防：啟 prod 前先把 fullchain/privkey 複製進 front-nginx 的 certs named volume。｜出處：rev3:CLAUDE.md§8.2.1
- **L-018**｜graphify 圖譜抓不全 .vue 檔的 template 與 import 關係，問 Vue SFC 之間 wiring 會得到殘缺答案。
  防：Vue component composition 問題直接讀 SFC，不靠圖譜推論。｜出處：rev3:CLAUDE.md§8.3
- **L-019**｜graphify 增量更新的標準 build_merge 預設開全域 fuzzy-label dedup，會把同名/近似 label 的 distinct 真節點誤併（實測一次誤刪約 700 個未變更真節點）；另 manifest 與 graph.json 會 desync（manifest 宣稱已索引、圖裡實缺整棵子樹），純 manifest-diff 增量補不了洞；obsidian export 也不清孤兒舊 note。
  防：增量一律外科式：顯式 prune 變更檔舊節點→build_merge 帶 dedup=False（prune_sources 只給已刪除檔）；merge 後節點數必須成長、縮水即停手不寫檔；update 前先 grep graph.json 實際 source 覆蓋、別只信 manifest；export obsidian 前先清舊 .md。｜出處：rev3:memory/graphify-update-fuzzy-dedup
- **L-020**｜spec-kit 有兩條獨立版本軸：repo release tag（如 v0.10.x）與 specify-cli 套件自報版本（如 0.8.x）本來就不相等，且安裝器把 tag 解析成 commit 釘著裝、uv 顯示裸 commit hash——看到落差容易誤判成裝錯或裝到 main HEAD。
  防：驗證是否釘在 release：比對 install log 的 build commit 是否等於該 tag peel 後的 commit（git ls-remote --tags）且不等於 HEAD；specify --version 只用來查 dev/rc/alpha/beta/pre 後綴、有就重裝穩定 tag。｜出處：rev3:memory/speckit-version-axes

**〔git／worktree／submodule〕**

- **L-021**｜git push 或 git merge 出現在開發收尾階段之前（直接執行、或被排進 tasks 清單）會把未審完狀態推上共享 remote、事後難收回。
  防：push/merge 只允許在 finishing-a-development-branch 收尾階段出現，push 前需 user 明確同意，tasks 清單不得排入。｜出處：rev3:CLAUDE.md§3
- **L-022**｜merge 收尾想用「-F -」從 stdin 讀 commit 訊息會失敗，git 直接報 could not read file '-'。
  防：merge commit 訊息用 -m 直接給。｜出處：rev3:CLAUDE.md§3-收尾
- **L-023**｜進度檔回填（里程碑表、todo 檔、active-feature 標記）若排在 merge 之前做，要寫入的 merge SHA 與最終 worktree pin 都還沒確定、必然回頭改。
  防：進度檔回填一律排在 merge 之後（這些檔屬 workspace 層、本就在主幹上）。｜出處：rev3:CLAUDE.md§3-收尾
- **L-024**｜收尾把 feature branch 清掉會失去 spec-kit feature 的 audit／追溯線索。
  防：merge --no-ff 回主幹後保留 feature branch 不清理。｜出處：rev3:CLAUDE.md§3-收尾
- **L-025**｜submodule pin bump 延到 feature 末刀才一次做（rev3-001 曾把十餘個 task 的 pin 全延到最後一個 task），中繼 outer commit 的 pin 全部過期，checkout 任一中繼 commit 都不可重現當時 tasks 勾選聲明。
  防：worktree commit 落地的當個 task／單元就同步 bump outer pin，讓每個 outer pin commit 對應一個可重現的單元邊界。｜出處：rev3:CLAUDE.md§4.1；另 rev3:CLAUDE.md§4.1／§5
- **L-026**｜本機 worktree 模式下 git submodule status 行首的減號是永遠出現的正常現象，誤跑 git submodule update --init --recursive 會與 worktree 的 .git gitlink 衝突。
  防：先判 base-web/rust-api 的 .git 是檔案（worktree 模式、勿 update）還是不存在（新 clone 機器、才跑 init update）再處置。｜出處：rev3:CLAUDE.md§4.3
- **L-027**｜outer pin 與本機 worktree HEAD 不同時跑 git submodule update，會把 worktree reset 掉、覆蓋尚未推出的本機改動。
  防：pin 與 worktree 分歧一律走「回外層更新 pin」方向，永不 submodule update。｜出處：rev3:CLAUDE.md§4.7
- **L-028**｜在 worktree 內裸跑 git push 不指定 remote/branch，預設推向 fork 源倉、可能誤推到非預期分支。
  防：worktree push 一律顯式 git push origin 加長名分支。｜出處：rev3:CLAUDE.md§5
- **L-029**｜用 git submodule add 註冊 base-web/rust-api 會嘗試 clone 進目錄、與既有 worktree 衝突。
  防：submodule 設定手寫 .gitmodules 加 git config 加 submodule init，外層只 git add 目錄記 SHA pin。｜出處：rev3:CLAUDE.md§4.4／§5
- **L-030**｜直接編輯 fork260509 系列源倉的檔案，改動不會落在整合分支的 worktree 上。
  防：base 與 rust 的改動一律透過 base-web/、rust-api/ worktree 進行；docs 源倉僅參考不改。｜出處：rev3:CLAUDE.md§5
- **L-031**｜跳過 spec-kit 標記為 mandatory 的 pre-hook（specify 前自動建 feature branch 那支），spec 文件與 pin 變動會直接落在 default branch 上。
  防：讓 pre-hook 跑、或手動先切出 feature branch；pre-hook 只在 local 建分支不 push，不違反 push 同意紀律。｜出處：rev3:CLAUDE.md§5
- **L-032**｜在外層 git add fork260509 系列源倉目錄會把它們變成 embedded git repo 污染外層。
  防：源倉維持 gitignored、只 add base-web/rust-api 兩個 gitlink；add gitlink 時 git 的 embedded repository 警告屬正常可忽略。｜出處：rev3:CLAUDE.md§5／§4.7
- **L-033**｜fork260509 系列源倉雖 gitignored，本機刪掉它會讓 worktree 的 .git 檔（指向源倉 worktrees 目錄）懸空、base-web/rust-api 全斷。
  防：源倉本機必留；真斷了走 worktree 重建流程，或新機器改用 recurse-submodules clone。｜出處：rev3:CLAUDE.md§2
- **L-034**｜源倉設了指向 soybeanjs 官方的 upstream remote 後，一個手滑 push 就會推到官方 repo。
  防：upstream 的 push URL 設成 no_push（fetch 留官方 URL），fetch 前 git remote -v 確認兩向 URL。｜出處：rev3:CLAUDE.md§4.6
- **L-035**｜base-web 對 upstream rebase 改寫 history 後若忘了回外層 bump pin，outer 記的 SHA 指向已被改寫掉的舊 history。
  防：rebase 加 force-with-lease push 後立即回外層 git add base-web 更新 pin。｜出處：rev3:CLAUDE.md§4.6

**〔流程與編排（spec-kit／superpowers／Workflow／subagent）〕**

- **L-036**｜把 SDD 規格起手指令排進 brainstorm 流程內自動觸發時，負責建 feature branch 的 mandatory pre-hook 不會執行，spec 文件會落在錯的 branch 上。
  防：規格指令一律在 brainstorm 收尾後手動執行，讓 pre-hook 正常從 default branch 衍生 feature branch。｜出處：rev3:CLAUDE.md§3-階段0
- **L-037**｜實作階段若改用 spec-kit 內建的 implement 指令起手，會繞過 TDD 編排（implementer→spec 對照審→品質審的 fix 迴圈）與主線單元邊界 checkpoint。
  防：實作一律以 superpowers 的 executing-plans 讀 tasks 起手並批判審查分執行單元，從不使用 spec-kit 的 implement 指令。｜出處：rev3:CLAUDE.md§3
- **L-038**｜把純工程「怎麼做」選擇（優化手法、模組拆法、DTO 映射、命名、測試策略）做成選項題丟給 user，或拍板題用內部術語抽象列，浪費拍板頻寬又害 user 選錯。
  防：工程選擇自己拍；只有動 schema／加 migration、feature scope 邊界、破紀律例外等真拍板級才問，問時大白話＋每選項串回 user 核心目標＋trade-off 主張先 grep 實證。｜出處：rev3:CLAUDE.md§3-階段0
- **L-039**｜spec 設計 wire DTO 時盲信 brainstorm 假設而非 facade 實際返回型——rust-api 是 facade-only 存取（無 service trait 層），不同 facade fn 可能返 raw Model、也可能返 sanitized 形（濾軟刪列、遮密碼欄），對不上就是契約錯。
  防：plan 的 research 階段先 grep facade fn 真實返回型並對照 entity Model 欄位，再定 wire DTO。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-040**｜wire endpoint 三端（rust handler 返回型、前端 service 與 typings 宣告型、component 內部 state 型）任一端沒對齊就是 runtime bug 或 type lie，且單看任一端都全綠。
  防：每條 wire endpoint 動工前同時 grep 三端型別並互相對齊。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-041**｜spec/data-model 裡 brainstorm 推測的 struct/function 命名與檔案行號引用常與實碼不符，implementer 盲信 spec 字面命名會改錯地方。
  防：文件內每個程式引用先 grep 驗真實命名，實作以 actual code 為準而非 spec 命名。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-042**｜subagent 把長時間 cargo 丟 background 或 timeout 設太短，會在編譯結束前結束回合、拿不到真結論。
  防：長 cargo 不准 background、timeout 拉長、agent 得出結論前不得結束回合——此紀律要烤進每個 agent prompt。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/subagent-foreground-blocking
- **L-043**｜review agent 把 findings 寫成 repo 內檔案（review 報告檔之類）會污染 git status、混進後續 commit。
  防：spec 審與品質審兩個 review agent 一律只讀，findings 只放回傳訊息。｜出處：rev3:CLAUDE.md§3-階段2
- **L-044**｜Workflow script 裡 agent() 遇 transient API error 或 user skip 會回 null，直接取回傳物件的欄位就 throw、整支 workflow crash。
  防：agent() 回傳一律 null-guard，null 視為 inconclusive、retry 或跳過該步。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/workflow-review-loop-null-and-scope
- **L-045**｜reviewer prompt 沒寫明本單元 in/out scope 時，reviewer 會把下游單元/波次的 deferred 產物誤判成 critical、同時漏抓真 bug。
  防：每個 reviewer prompt 明列「本單元範圍＝X、後續 deferred 工作＝Y、不得 flag」。｜出處：rev3:CLAUDE.md§3-階段2
- **L-046**｜Workflow 用 args 物件傳 per-unit prompt 時，args 常被序列化成字串、script 內取欄位變 undefined——silent 不 throw，agent 收到字面「undefined」當任務內容。
  防：per-unit prompt 一律內聯進 script body 的 const，不靠 args 傳。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/workflow-args-stringified-undefined
- **L-047**｜[流程] 手動逐-subagent 編排時，reviewer 完成通知常被折進 sibling/parent 的通知串、不會喚醒 main loop——純被動等通知就出現長 idle gap，甚至誤信沒派過的 review「已通過」。
  防：多單元 pipeline 改用 Workflow 工具驅動（script 內 deterministic 串 implementer→review→fix、主線只在單元邊界醒）；保留手動模式時 agent 理應完成就主動用 git/test 自驗 ground-truth、等待期做非重疊 prep，不純等 flaky 通知。｜出處：rev3:memory/orchestration-avoid-idle-on-folded-notifications
- **L-048**｜[流程] Workflow implementer 的結構化自報（filesChanged、gitStatusClean）不可信——曾自報「5 檔乾淨」實際 commit 7 檔：偷 commit 該留在 /tmp 的測試檔、還動了明令不動的 package.json，自報摘要把偏離全部抹平。
  防：每個單元邊界 bump submodule pin 前，主線親自 git show --stat HEAD＋git status 對照該單元授權範圍，專抓多出的禁改檔（測試檔、package.json、lockfile、generated typings）。｜出處：rev3:memory/workflow-implementer-gitstate-claims-unreliable；另 rev3:CLAUDE.md§3-階段2
- **L-049**｜[流程] 部署層交付物（compose/deploy 檔）的驗收 grep 對前代 workspace 代號字樣零豁免，連 review 修補註解時順手寫入前代代號都會撞紅——同一人踩過兩次。
  防：部署層檔案提及前一代一律寫「前代」「前代 workspace」；僅既定豁免（migration 檔名、GitHub 永久倉名）例外。｜出處：rev3:memory/deploy-layer-zero-rev2-wording
- **L-050**｜[流程] 依賴/設定漂移若功能上惰性（如 feature-gated、永不編譯的 optional dep 被解析到新版），強制改回舊 pin 只是 churn；但默默吞掉又違反漂移必 surface 的紀律。
  防：先判 real/inert（cargo tree -i 看是否真在編譯圖）；惰性者仍要 surface，把「接受漂移＋把 stale 註解校正成真正的不變式（不啟用拉該 crate 的 feature）」列首選、「強制原 pin」列次選並標明是 churn。｜出處：rev3:memory/inert-drift-accept-and-correct-doc
- **L-051**｜[流程] review「從前代拉來且有調整」的檔案時只看衍生檔本身，抓不到周邊文件內嵌的舊結構殘影——章節序、子節編號慣例的引用點全指舊版結構而不自知。
  防：三方比對：先讀原版全結構（grep 標題）、diff 出結構差異清單、再 grep 全 repo 引用該檔結構的下游逐一核對。｜出處：rev3:memory/read-source-before-derived-review
- **L-052**｜[流程] 往文件階層寫識別碼的兩個坑：brainstorm 拍板自鑄新警示碼當小節編號會污染全域決策 registry；用行號當交叉引用（某檔 line NNN）則文件一改行號全飄、引用立即 rot、讀者看不懂。
  防：拍板表用描述名、只引用既有 registry 碼，新碼只給真正跨 feature 的長壽決策且按實際編入先後給號、不預留 gap；交叉引用一律用穩定語意錨（章節號/附錄名/描述名），程式碼註解就地自解釋、不回指動態 todo 檔。｜出處：rev3:memory/brainstorm-doc-decision-table-not-warn-codes

**〔review／驗收方法論〕**

- **L-053**｜純靜態 review 對 runtime 漂移結構性失明——三輪純靜態審查給出全數 PASS、零真缺陷的結論，實際仍有設定列位置漂移、重置鈕行為、i18n raw key 洩漏等一批只有活體才看得到的問題，事後靠 live/CDP 輪才補抓。
  防：cumulative review 必配 live 讀端（curl/psql/redis）＋CDP 真瀏覽器補證輪；靜態輪對驗不到的項誠實標 needs-runtime，不得逕判 PASS。｜出處：rev3:REVIEW§1＋§7
- **L-054**｜一批 UI/runtime 真相只有 CDP 真瀏覽器抓得到：axios 空字串 query 的真實序列化形、搜尋重置鈕行為、匯出鈕收合後的可發現性、列表無排序時的位置漂移、i18n raw-key 洩漏、三態排序箭頭與持久化還原——curl、typecheck、grep 全綠都掩蓋。
  防：UI 行為類驗收一律排 CDP 軌；curl 只當補充、且刻意模擬前端請求形（帶空參數）而非乾淨 query。｜出處：rev3:REVIEW§7
- **L-055**｜review 輪受非破壞紀律約束（禁寫端操作、禁觸發鎖定、禁建 IP 規則），寫端需求實際只有「實碼閱讀＋當年收刀驗收全綠」等級的背書——review 報 PASS 容易被誤讀成寫端已被重新驗證。
  防：review 報告逐項明標證據等級（純靜態／live 讀端／CDP／收刀背書），寫端回歸靠自動化測試覆蓋，否則明示「未重演」。｜出處：rev3:REVIEW§7
- **L-056**｜cumulative 多刀審查若平行跑，後刀合法推翻前刀的行為會被 reviewer 誤判成漂移缺陷，或反向漏掉真正無依據的漂移。
  防：依刀序 serial 審查＋維護 supersession 映射表作為「所有偏離皆有拍板依據」的合法依據；前刀行為被後刀改變時，同步在前刀 spec 補 as-built 勘誤註記。｜出處：rev3:REVIEW§5＋§7
- **L-057**｜多個 reviewer 各自登入做 live 驗證會污染登入嘗試/存取日誌、甚至觸發帳號鎖定，把審計類斷言弄成偽紅。
  防：reviewer 共用同一 token（前提＝單一 session 政策關閉）；token 過期從瀏覽器 localStorage 唯讀恢復；CDP 分頁登出態用 token 注入 SOP 而非重走登入表單。｜出處：rev3:REVIEW§7
- **L-058**｜upstream 原樣繼承的頁面行為是審查盲區——搜尋重置鈕不重新查詢、帳號名欄改了顯示成功卻靜默不寫，兩個缺陷都不屬任何一把刀的 spec 範圍，拖到最終 cumulative 輪才浮出。
  防：把繼承自 upstream 的頁面行為也納入驗收/審查面，別假設 upstream＝正確；發現後把「修（產生 fork-delta）vs 維持原樣（零 delta）」做成 user 拍板題而非默改。｜出處：rev3:REVIEW§3.2-F-4/F-5
- **L-059**｜fan-out 出的大量疑似 findings 若直接全修會浪費工甚至誤修——對抗式查證後仍有一批「聽起來合理但未確認」的項。
  防：走對抗式 verifier 把 findings 分 CONFIRMED/PLAUSIBLE 兩級，只有 CONFIRMED 進修復清單；PLAUSIBLE 留完整 reasoning 於紀錄、不動碼。｜出處：rev3:REVIEW§1＋§6
- **L-060**｜多輪 review 的 findings 混雜不分流時，會重修已閉合項、漏掉需 user 拍板的行為變更、或把該登記遞延的項當場亂修。
  防：統一修復輪把 findings 分四類分流（直接修／需 user 拍板／登記不修碼／明確不修）並逐項標處置結果；另設「已閉合 findings」節防重修。｜出處：rev3:REVIEW§3＋§4
- **L-061**｜行為變更的拍板題用抽象語意句問 user，容易讓 user 選錯方向（實際發生過選項誤選）。
  防：問拍板題附具體渲染範例（mock／前後對照畫面）、正交維度拆開列選項、「隱藏/不顯示」類行為必明示其可見結果。｜出處：rev3:REVIEW§3.2 標頭（引 memory ui-behavior-options-need-concrete-examples）
- **L-062**｜驗收計畫把 CDP browser smoke 延後、只留 curl 直打時，「curl 直送不等於前端 modal 行為」的破口會靜默漏到下游。
  防：要 defer 就在 spec 內明示此風險，並在 follow-up backlog 登記補測。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律

**〔文件紀律〕**

- **L-063**｜文件勘誤只修被點名那一行、同檔另一行同語意殘留（檔頭仍寫三端點、下方已修成四端點、上方漏改），下一輪 review 再被抓一次。
  防：做勘誤時對同語意字串跑全檔／全 repo grep 掃描，一次改齊所有出現點。｜出處：rev3:REVIEW§3.1-F-1
- **L-064**｜指引文件的 schema 欄位清單只列部分欄（實十六欄只列五欄）又未標明是節選，連續兩輪 review 點名、且曾實際誤導加欄規劃、靠外部記憶補救。
  防：文件列欄位/schema 清單要嘛列全、要嘛明說 partial，並註記以資料庫實況（psql）對過。｜出處：rev3:REVIEW§3.1-F-3；另 rev3:memory/rev3-sys-user-profile-fields-exist
- **L-065**｜spec 寫死數量口徑（表數、設定列數、路由總數、service 數）必被後續刀推翻——每加一項都得補一條 supersession 或勘誤，口徑本身變成維護債。
  防：spec 口徑改指權威 registry/migration「以現況為準」或標 as-of 時點；由加項的那把刀負責同步勘誤前刀 spec。｜出處：rev3:REVIEW§5（表數/設定列數/路由總數多列）
- **L-066**｜歷次 review 報告逐輪堆積且互相引用，一旦清理刪檔、其他文件的引用點全部 dangling。
  防：定期把多份 review 報告整併為單一自包含留存版，詳版全文靠 git 史以 SHA 引用；cross-ref 紀律＝只引用留存文件與 git SHA、不引用已刪檔名路徑。｜出處：rev3:REVIEW檔頭＋§1
- **L-067**｜repo 內 git-tracked 文件引用本機 Claude memory（per-machine／per-user、不在 repo），換機、換維護者、別人 clone 都不存在，引用即 dangling、對他人無意義。
  防：重要記憶內容先提取進 repo 文件（設計/決策/指引檔），再引用該 repo 段落；memory 只供跨 session recall、非引用目標。｜出處：rev3:CLAUDE.md§7
- **L-068**｜其他文件跨檔深連結動態 todo 檔的揮發章節（波狀態、follow-up 節會滾動收縮歸檔），章節錨必 rot 成死連結。
  防：cross-ref 一律改指權威或永久檔（設計藍圖、決策帳、里程碑、spec）；只有 todo 檔內部互引與整檔指向屬結構性例外。｜出處：rev3:CLAUDE.md§7.3
- **L-069**｜todo 檔「最新進展」清單後緊貼的「下一步」blockquote marker 若前面不留空行，會被前一個 list item 的 lazy-continuation 吸收成子項、渲染錯亂。
  防：marker 前必留空行且 marker 勿刪、下一步勿併入最新進展，改完回讀渲染驗證。｜出處：rev3:CLAUDE.md§7.5
- **L-070**｜進度/帳本文件記「已push／未push」這類揮發 git 狀態，push 後立即 stale、誤導後續 session。
  防：只記 commit/merge SHA（可追溯、非揮發），推沒推看 git 本身。｜出處：rev3:CLAUDE.md§7.5

**〔後端／DB／redis〕**

- **L-071**｜workspace 的 sea-orm 刻意 default-features=false、無 date-time backend，新增帶 timestamptz 欄的 entity Model 會編譯失敗（DateTimeWithTimeZone 型別找不到）——每個帶 timestamp 欄的新 entity 刀都會再撞。
  防：在消費該型的 crate 對 sea-orm 加 with-chrono feature（絕不用 with-time、避免把 time crate 拉進編譯圖）；另注意複合主鍵 join 表兩個 PK 欄都要標 primary_key＋auto_increment=false。｜出處：rev3:memory/sea-orm-entity-datetime-feature-gate
- **L-072**｜jsonwebtoken 9 經 simple_asn1 把 time crate 拉進「真實」編譯圖（與 sea-orm 路徑那個永不編譯的惰性 time 性質相反），不 pin 時 cargo 解析到需 rustc 1.88 的 time 版本、在 pin 1.86 的 toolchain 上 build 硬失敗。
  防：遇 time 鏈 MSRV 衝突先 cargo tree -i time 判 real/inert：真在編譯圖就先 pin simple_asn1 0.6.3（放寬 time 需求下限）再 pin time 0.3.37，順序不可顛倒（反序 cargo update 直接失敗）；只經未啟用 feature 的惰性路徑則接受不 pin。｜出處：rev3:memory/jsonwebtoken9-msrv-time-real-graph
- **L-073**｜server crate 沒有 chrono 直接依賴，寫端 facade 要塞「現在時間」進 timestamptz 欄時 use chrono::Utc 不編譯——但也不必為此動 Cargo.toml。
  防：走 sea-orm 的 sqlx re-export：sea_orm::sqlx::types::chrono::Utc::now().into() 得 DateTimeWithTimeZone（prelude 只 re-export 型別別名、拿不到 Utc 建構子）；要 DB 端時間可用 Expr::current_timestamp() 但取不回更新後的 Model。｜出處：rev3:memory/seaorm-now-via-sqlx-chrono-reexport
- **L-074**｜初判「sea-orm DbErr 無乾淨路徑辨識 unique violation、只能 string-match 破壞封裝」是錯的——官方 DbErr::sql_err() 直接回 SqlErr::UniqueConstraintViolation（底層解析 SQLSTATE 23505），撞碼並發 race 守門「同業務拒、永不系統錯」就靠它。
  防：unique/FK 偵測一律用 sql_err() 在 handler remap 成業務錯誤碼；facade 保持回 DbErr 免層級倒置，txn rollback 傳回的原始 DbErr 在 handler 仍辨識得出。｜出處：rev3:memory/seaorm-sqlerr-unique-violation-23505
- **L-075**｜token rotation 這類狀態機寫端只靠冪等守門（UPDATE … WHERE status='active'）擋不住「撤銷穿插」race——pre-read 見 active 到上鎖之間鏈被撤，rows=0 被當良性照樣重鑄新 token、繞過撤銷。
  防：「讀狀態→決定→寫」的發放決策要在 FOR UPDATE 鎖住的列上重判（lock-then-redecide）、鎖住列已撤即拒；但非萬用——集合 toggle 且有 DB UNIQUE 兜底者（如 casbin policy 寫端）靠冪等＋unique violation rollback 已足、不需 FOR UPDATE。｜出處：rev3:memory/lock-then-redecide-toctou
- **L-076**｜casbin policy 寫端若走 enforcer MgmtApi（remove_filtered_policy/add_policies）＝改 in-memory＋adapter auto-save 旁路、審計非原子——這是前代被推翻並被 constitution 明禁的 anti-pattern；研究 agent 給的「MgmtApi 怎麼用」是 API 層知識、不等於專案 mandate。
  防：任何 policy 寫端一律 DB-first：facade 在同一 txn 直寫 casbin_rule 實體（含 protected 拒改、與操作日誌原子），寫後 enforcer load_policy 全量重載；設計前先讀 constitution 與設計權威的 casbin 寫入章。｜出處：rev3:memory/casbin-write-db-first-not-mgmtapi
- **L-077**｜研究與 spec 文件曾假設 casbin seed 沒有 button 維度、getUserInfo 的 buttons 回空陣列——實機驗證推翻：初始 seed 實有 16 筆 button 政策（超管角色佔 12 個 button code）與 83 筆 menu 政策，live 端點回真按鈕清單。
  防：推論按鈕/選單權限設計前先 psql 查 casbin_rule 實際維度分佈，別信文件「現空」的舊假設；code 對而文件錯時不必回頭改史料、但後續推論別再引用錯假設。｜出處：rev3:memory/casbin-seed-has-button-policies
- **L-078**｜host 無 rust toolchain，且 live smoke 測試共用 DB 資料表、多執行緒跑會互踩出偽失敗。
  防：rust build/test 一律在 rust-api dev 容器內 docker exec 跑，live smoke 帶 DATABASE_URL 並加 --test-threads=1 單緒。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/live-ignore-tests-need-serial
- **L-079**｜live 測試對共享 seed 實體（如 seed 管理員角色）的操作日誌下絕對計數斷言（等於 1），隱含「我是唯一寫者」假設——別的 feature 經真 server 提交的審計列會累積、READ COMMITTED 下計數大於 1 偽紅；連補表名述詞也擋不住同表同 id 的累積污染。
  防：斷言「本測試自身寫了一筆」唯一可靠隔離＝本測試專屬 trace_id 過濾、或計數前後 delta，絕不用絕對計數。｜出處：rev3:memory/oplog-count-assert-nonidempotent-shared-entity-id
- **L-080**｜per-request access-log 中介層對每個已認證請求（含審計查詢端點自身的 GET）都寫一列 access log——spec 寫「查詢絕不產生新稽核紀錄」就與現實矛盾。
  防：「唯讀」端點只能宣稱不寫操作日誌、不主動自審，不能宣稱零 DB 寫；驗收的唯讀證只查操作日誌零新增（access-log 每查加一列屬基建預期、非污染）。｜出處：rev3:memory/audit-read-endpoints-not-db-write-free
- **L-081**｜Redis 快取的讀端（查命中）與寫端（set）若由兩個獨立函式各自渲染 key 字串，IPv6 canonical/expanded、CIDR /32 與 /128、格式差異會讓讀端永遠 miss——快取靜默失效、無任何 error，單看讀端或寫端的測試都是綠。
  防：讀寫兩端 key 一律由同一個 helper 導出；純函式測試斷言 write_key(x)==read_key(x)，live 驗收必含「寫端觸發→讀端命中→證明短路」的交叉軌。｜出處：rev3:memory/redis-cache-key-shared-helper
- **L-082**｜redis-rs 的 MultiplexedConnection 在 redis 容器 stop→start 後不自動重連，之後每個操作回 broken pipe、全走 fail-open 降級值，要重啟 rust-api 拿新連線才恢復——含 redis 重啟軌的驗收裡，排在後面的「需 redis 寫成功」斷言會假失敗。
  防：驗收把需 redis 寫成功的斷言排在 redis stop/start 之前；必須排後面就先 restart rust-api＋探針確認 key 寫得進去再續；log 大量 broken pipe＝連線斷未重連、非偶發錯誤。｜出處：rev3:memory/redis-multiplexed-no-auto-reconnect
- **L-083**｜vendored ip2region xdb crate 的初始化對缺檔是 .expect() panic（非 best-effort），xdb 資料檔不在時 boot 或 request path 直接炸。
  防：boot 先 guard 檔案存在才 init 並設 ready flag，middleware 只在 ready 時查 IP 歸屬、否則 region 給 None；prod runtime image 必須 COPY xdb 資料檔（dev bind-mount 會遮住這個缺口）。｜出處：rev3:memory/xdb-searcher-panics-on-missing-file
- **L-084**｜新增 rust workspace crate 時 prod 多階段 Dockerfile 實際要補四處 COPY（Manifest 段、Source 段、builder 產物 cp 到輸出目錄、runtime stage COPY 進 /usr/local/bin）——檔頭註解只寫兩處會誤導；漏後兩處時 docker build 照綠，只在 runtime 執行該 binary 才 exec not found。
  防：加 crate 的刀在 prod build 驗收必加 runtime binary 斷言（docker run prod image 列出該 binary 或走 entrypoint dispatch smoke），不可只靠 compose build 綠。｜出處：rev3:memory/rev3-new-crate-dockerfile-four-copy；另 rev3:CLAUDE.md§3-Phase1紀律
- **L-085**｜把前代多支 migration 的 seed squash 成一次性 INSERT 後，用「排序後 md5」比對 pg_dump 會同時掩蓋兩層問題：sequence id 落值真漂移（INSERT 順序沒對齊前代按 id 排序的終態）與 COPY 物理列序假紅（heap ctid 序經 UPDATE 移位、不可能用 INSERT 順序重現）。
  防：對 pristine dump 跑未排序逐列（含 id 欄）diff；normalize 規則把 COPY 段整列 sort 消物理序假紅、id 漂移則修 migration 的 INSERT 順序；並跑 negative test 證明比對不遮實質差異。｜出處：rev3:memory/seed-squash-rowid-drift
- **L-086**｜Cloudflare Tunnel 第三 ingress（cloudflared 繞過 nginx 直連 rust-api 內部 port）下，若 tunnel 信任網段沒有包含於內網信任預設清單，還原真實 client IP 的 header fallback 根本不會觸發——IP 存取控制閘刀（rev3-022）的實測 footgun。
  防：trust-model 設定裡 tunnel 段必須是內網預設段的子集，且只含 cloudflared origin、不放整個內網（防內網偽造 header）。｜出處：rev3:CLAUDE.md§8.2-ingress註（rev3-022 IP 閘刀）
- **L-087**｜供 UI 列表消費的查全表 facade 沒加 ORDER BY 時走 heap 實體序，任一列被更新後在頁面上位置漂移——靜態讀碼與單次 curl 都看不出，只有「更新後再看列序」的實測才現形。
  防：任何供列表/設定頁消費的 find-all 一律加穩定排序鍵；review 時把「無 ORDER BY 的全表查詢」列為缺陷候選並實測更新後列序。｜出處：rev3:REVIEW§3.1-F-2
- **L-088**｜寫端 handler 把 facade 的 no-op 回傳（目標列已消失、回 None）直接映成成功回應——實際沒寫入卻報成功；僅併發硬刪自身列的極端邊角可達，平時測不到。
  防：handler 對 facade 的 Option 回 None 一律轉 notFound 類業務碼，不得靜默映成成功；同族「no-op 假成功」模式列為 review 檢查點。｜出處：rev3:REVIEW§3.2-F-6
- **L-089**｜base-web axios 把未填的搜尋欄序列化成空字串 query 參數、serde 端收到 Some("") 而非 None，handler 沒守門就把空字串當真值過濾、曾致列表整頁變空；curl 手打的乾淨 query 完全掩蓋此 bug。
  防：handler 一律把空字串當「未設」（Option 濾掉空字串、enum/數值轉換把空字串映成 None），驗收必跑瀏覽器/CDP 軌，curl 測試刻意帶空參數模擬前端。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律；另 rev3:REVIEW§2（012 列空字串守門 CDP 實證）＋rev3:CLAUDE.md§3
- **L-090**｜前端 axios 把未填的 search filter 送成空字串 query（如 ?entityId=），handler 的 Query DTO 數字欄若直接宣告 Option<i64>，axum 抽取層在進 handler 之前就整個請求 400（空字串 parse 不成整數）、頁面整掛——curl 乾淨 query 測不到，只有 browser/CDP 真送空參數才抓得到。
  防：query 來的數字/bool 欄一律 Option<String>＋parse 守門（空→None、合法→Some、畸形→業務錯誤碼），絕不直接 serde 成數字型；驗收刻意帶空參數、並跑 browser 軌。｜出處：rev3:memory/numeric-query-param-empty-string-400

**〔前端／UI〕**

- **L-091**｜flex-height 的 NDataTable 包進 NCard＋NTabs 後，NCard 內容區是 display:block、截斷 flex 高度鏈，table body 塌成 0px——分頁顯示「共 N 條」、列在 DOM 且文字齊全，但視覺整片空白；空表期潛伏、有資料才引爆，數 DOM 列數會誤判正常。
  防：診斷量 table body 元素的 getBoundingClientRect().height（0 即此 bug）、再沿祖先鏈找 flex 斷點；修法在頁面補回連續 flex-column 鏈（NCard content-style 改 flex＋各層 flex:1 與 min-height:0），子表元件不動。｜出處：rev3:memory/soybean-flex-height-table-in-ntabs-body-collapse
- **L-092**｜照抄 table 頁模板的頁 root class（min-h-500px flex-col-stretch overflow-hidden）用在卡片/表單類非-table 頁，內容一多就被裁在摺疊線下且無法下滾——table 頁靠 NDataTable 內部滾動所以正確，非-table 頁無內部滾動容器接手；內容少時潛伏無感、加項目後才引爆。
  防：非-table 頁 root 改 flex-col-stretch gap-16px（去掉 overflow-hidden 與最小高度），讓 layout main 接手滾動、別動既有 table 頁；診斷用 CDP 沿祖先鏈找 scrollHeight 大於 clientHeight 且 overflow hidden 的裁切層。｜出處：rev3:memory/soybean-page-root-overflow-hidden-clips-nontable
- **L-093**｜新增 base-web view 後，4 個 git-tracked route 檔（elegant-router 的 imports/routes/transform＋route 型宣告）要等 running dev server 掃描時才重生、不在建檔當下——implementer 建完立即 git status 看不到而誤報無變動；漏 commit 則 fresh checkout 該頁不可達、漏補 route i18n 鍵則兩語系字典 typecheck 紅。
  防：建 view 後 restart base-web 觸發重生，git status 見 route 檔變動就連同 view 一起 commit、同 commit 補兩語系 route 鍵、typecheck 綠才算完；i18n 改動要在 running app 驗收（CDP）前也必先 restart，否則 vite stale locale 分不清 source 缺漏還是快取。｜出處：rev3:memory/base-web-elegant-router-regen-on-new-view
- **L-094**｜只把後端業務錯誤碼譯文加進 locale 字典、沒同步擴 typings/app.d.ts 的 I18n Schema 型，locale 字典因 excess-property 直接 typecheck 紅——i18n 接線三範圍（攔截器/字典/Schema 型）最常漏第三個，每個加業務譯文鍵的切片都會遇。
  防：先擴 Schema 型再加 locale 譯文、兩者同 commit 且鍵集完全對齊（任一側單獨 commit 都 typecheck 紅）。｜出處：rev3:memory/base-web-i18n-schema-iii-gotcha
- **L-095**｜base-web 在 alpine（musl）dev 容器內 git commit 被 simple-git-hooks pre-commit 擋死——oxlint 缺 musl native binding 直接 crash、加上 upstream 既有 eslint error，失敗與本次改動無關。
  防：base-web commit 一律 --no-verify（環境缺陷、非偷懶），改為獨立自驗：容器內跑 pnpm typecheck 確認無新 type error；修 hook 工具鏈屬 scope creep 不做。｜出處：rev3:memory/base-web-precommit-hook-broken-in-alpine；另 rev3:CLAUDE.md§3-階段2
- **L-096**｜base-web view 首次使用某個 naive-ui 元件時，dev 容器的 unplugin-vue-components 會自動重生 git-tracked 的元件型別宣告檔，漏 commit 它會讓 fresh checkout（無 dev server）缺全域型別、typecheck 失敗。
  防：第一段 commit 前在 base-web 內 git status 檢查元件型別宣告檔有無變動，有就與引入元件的 commit 一起 add（只有全新元件才觸發）。｜出處：rev3:CLAUDE.md§4.1

**〔CDP／mock 驗收〕**

- **L-097**｜CDP 連線用截短的 page id（非完整 32 字元 hex）時，WebSocket 直接 reject、close 1006 且 error message 為空、無從診斷。
  防：從 targets 列表取完整 32 字元 id，篩 type=page 加目標 URL。｜出處：rev3:000-bootstrap§3.1
- **L-098**｜瀏覽器內部頁（edge:// 、chrome:// ）不可 CDP attach，對新開 tab 直接連會失敗。
  防：新 tab 先 navigate 到任一 http URL 再 attach，並注意 navigate 後 page id 會換。｜出處：rev3:000-bootstrap§3.1
- **L-099**｜CDP 的 targets 列表列出所有 targets，腳本操作的 tab 不一定是 user 親眼看的那個、雙方各看各的狀態。
  防：讓 user 開一個專用 tab 供自動化操作，選 target 時比對 URL。｜出處：rev3:000-bootstrap§3.1
- **L-100**｜CDP browser smoke 走 login-form 自動化很 flaky；且 localhost 與 127.0.0.1 是不同 origin、localStorage token 不共享，origin 混用時注入的 session 白做。
  防：curl 打登入端點取 token→CDP 把 JSON-stringify 的 token 寫進 localStorage 的 SOY_token（前綴來自 VITE_STORAGE_PREFIX）→navigate 到 front-nginx 整合路徑，全程鎖同一 origin；CDP 專驗 curl 抓不到的「頁面真的 render、i18n toast 在地化」。｜出處：rev3:memory/cdp-session-inject-soy-token；另 rev3:000-bootstrap§3.1
- **L-101**｜apifox 雲端 mock 有四坑：不帶 apifoxToken header 回 HTTP 500 內包 401；取用戶路由無 Bearer token 回「用户已失效」、refreshToken 給 dummy 值回錯誤；連打觸發頻率限制回 5xx；限流時 login 顯 timeout toast 但請求常在背景完成並跳轉
  防：打 mock 帶齊 header/token、限流時間隔重試、驗收以頁面實際跳轉為準而非 toast｜出處：rev3:superpowers/000（雲端 mock 段）

---

## 6. 交接程序

1. **攜檔**：本檔已在 rev4 目錄（`fork260509-rev4/docs/`）；新 workspace 開張即以本檔為唯一輸入，照 §4.2 B1 起跑。
2. **rev3 處置**：rev3 workspace 凍結為唯讀參考庫（不再開發）；本檔對它零依賴，回溯抽查用 K 清單出處欄的 `rev3:` 座標。
3. **本檔退役**：bootstrap DoD 全綠後，本檔轉存 `docs/brainstorms/000-doc-architecture.md`——內容屆時已由 CLAUDE.md（規則）、constitution（凍結原則）、tools/docs-sync（lint 實碼）、ops/LESSONS.md（K3 全量）、ops/BACKLOG.md（K2 全量轉入、見 B8）、ADR 群（K1 處置結果）承接；此後任何活文件不得引用本檔（避免第二權威），未及處置的 K1 條目以 BACKLOG 項續命。
