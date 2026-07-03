# Feature Specification: 001-compose-stack 一鍵開發環境

**Feature Branch**: `001-compose-stack`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "@docs/brainstorms/001-compose-stack.md"（波 0 第一刀；上游＝
docs/brainstorms/wave-0-plan.md §2.1＋docs/brainstorms/001-compose-stack.md 拍板 13 題、
ADR 0019 port 配號、ADR 0020 波 0 組成）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 一鍵起整套開發環境 (Priority: P1)

開發者在接妥 worktree 的機器上，跑「生成機密 → 生成開發憑證 → 啟動」三步，得到一套完整可用
的本機開發環境：前端頁面、後端 API、資料庫、快取、反向代理全部健康就緒，且各服務入口
（含 TLS 入口）都能連通。

**Why this priority**: 這是本刀存在的目的——沒有它，波 0 後續兩刀（schema 基線、wire 地基）
與波 1 功能刀都沒有承載環境。

**Independent Test**: 從乾淨狀態（無容器、無卷）執行啟動三步，檢查啟動命令退出碼與全部
連通點，即可獨立驗證、不依賴其他 story。

**Acceptance Scenarios**:

1. **Given** 乾淨狀態（無容器、無卷、機密未生成），**When** 依序跑機密生成、憑證生成、
   預檢、一鍵啟動，**Then** 啟動命令退出碼 0，五個常駐服務全部 healthy、一次性 migration
   服務成功結束（退出碼 0）。
2. **Given** 環境已啟動，**When** 逐一測七個連通點（代理入口 HTTP／TLS、經代理的 API 健康
   端點、API 直連、前端頁面、資料庫直連、快取直連），**Then** 全部通過；且經代理探測
   metrics 路徑對外回 404（不外洩）。
3. **Given** 環境已啟動，**When** 停止後再啟動（保留資料卷），**Then** 第二次啟動更快且
   全綠；**When** 連資料卷一併清除後重來，**Then** 仍全綠（冪等）。

---

### User Story 2 - migration 閘門：schema 就緒先於 API (Priority: P2)

開發者啟動環境時，資料庫 schema 由一次性 migration 服務先行套用；API 服務必須等 migration
成功結束才啟動。migration 失敗時 API 不得啟動、整體啟動命令顯式失敗——開發者永遠不會拿到
「服務起了但 schema 半套」的環境。

**Why this priority**: 002 刀（schema 基線）的 migration 將直接掛進這個閘門；閘門語意錯了，
後續所有含 schema 變更的刀都會踩到半初始化狀態。

**Independent Test**: 觀察啟動時序證據（資料庫健康 → migration 執行且成功結束 → API 才啟動）
＋故意讓 migration 失敗驗證 API 不起。

**Acceptance Scenarios**:

1. **Given** 乾淨啟動，**When** 檢視容器啟動時序，**Then** 順序為：資料庫 healthy →
   migration 服務啟動並以退出碼 0 結束 → API 服務才啟動；且資料庫內出現 migration 框架的
   版本記錄表。
2. **Given** migration 被安排為必然失敗（驗證用暫時手段），**When** 一鍵啟動，**Then** API
   服務不啟動、啟動命令以非零退出碼失敗，錯誤指向 migration 服務。

---

### User Story 3 - 改檔即生效的開發迴圈 (Priority: P3)

開發者改後端原始碼存檔後，服務在容器內自動重新編譯並重啟，數十秒內能觀察到新行為；改前端
原始碼由前端開發伺服器即時反映。全程不需手動重啟任何容器。

**Why this priority**: 這是 dev 環境相對於「跑起來就好」的核心價值；波 0 後續刀與功能刀的
TDD 迴圈都靠它。

**Independent Test**: 暫時修改後端健康端點回應字串，觀察自動重編重啟與新回應，再改回。

**Acceptance Scenarios**:

1. **Given** 環境已啟動，**When** 修改後端原始碼並存檔，**Then** 不需任何手動操作，容器內
   自動重編重啟，隨後對健康端點的請求回傳新行為（在 WSL2 掛載上同樣有效——檔案變更以輪詢
   偵測、不依賴檔案系統事件）。
2. **Given** 環境已啟動，**When** 修改前端原始碼，**Then** 前端開發伺服器即時反映變更。

---

### User Story 4 - 機密配置防呆 (Priority: P4)

開發者的機密（資料庫密碼、快取密碼、簽章私鑰材料、連線字串）由腳本一鍵生成、實值永不入
版控；缺檔在啟動前被預檢指名攔截；誤把範本佔位值當真值使用時，後端在啟動階段立即失敗並
指名是哪個機密——而不是拿佔位值繼續跑、之後在難以歸因的地方壞掉。

**Why this priority**: rev3 實證教訓——compose 對缺失機密不報錯、容器拿到空值後的錯誤訊息
嚴重誤導排錯方向。防呆缺席時，環境問題的排查成本最高。

**Independent Test**: 刪除單一機密檔跑預檢（應指名缺檔）；將範本佔位值放入機密檔啟動
（後端應啟動失敗並指名該機密）。

**Acceptance Scenarios**:

1. **Given** 機密已生成，**When** 重跑生成腳本，**Then** 已存在的不被覆寫（冪等）、缺的補
   齊；**When** 單獨重生某一底層機密，**Then** 由它組合出的連線字串機密同步重生（不產生
   兩處不一致）。
2. **Given** 缺一個機密檔，**When** 跑啟動預檢，**Then** 預檢失敗並指名缺哪個檔、提示生成
   方式。
3. **Given** 機密檔內容是範本佔位值，**When** 啟動後端，**Then** 後端啟動失敗、錯誤訊息
   指名該機密；佔位值不會被當真值使用。

---

### User Story 5 - port 對照文件自動生成與對賬 (Priority: P5)

開發者查「哪個服務用哪個 port」時，有一份由機器從 compose 設定直接生成的全量對照表；任何
人改了 compose 的 port 而忘了重新生成，提交會被攔下——文件與現實永不漂移。

**Why this priority**: 這是文件系統既有義務（B-002）搭本刀的順風車落地；價值真實但不阻塞
其他 story。

**Independent Test**: 跑生成命令檢查對照表內容與 compose 一致；手改 compose port 不重生成，
驗證檢查命令攔截。

**Acceptance Scenarios**:

1. **Given** compose 檔就位，**When** 跑文件生成命令，**Then** 產出 port 全量對照表（服務、
   對外 port、容器內 port、綁定位址、來源檔），內容與 compose 實際設定一致。
2. **Given** 有人改了 compose 的 port 映射但未重新生成，**When** 跑一致性檢查，**Then**
   檢查失敗並指出漂移處。

---

### Edge Cases

- 機密檔存在但為空、或內容是範本佔位值 → 預檢／後端啟動階段攔截並指名（story 4）。
- migration 失敗 → API 不起、啟動命令顯式失敗（story 2）；不存在「半初始化可用」狀態。
- 資料卷清除後重啟 → 全部重建、結果與首次啟動一致；快取資料落在持久卷（服務重啟不丟）。
- host port 被其他程序占用 → 啟動失敗且錯誤訊息指向該 port；與 rev3 同機並行保證零撞號
  （port 空間、專案名、卷名前綴、網路名全部隔離）。
- WSL2 掛載上檔案變更事件不可靠 → 熱重載以輪詢偵測，不依賴檔案系統事件。
- 前端首次啟動需安裝依賴、後端首次啟動需完整編譯 → 健康檢查給足啟動寬限期，`--wait` 不因
  冷啟動慢而假陰性。
- 對外訪問 metrics 路徑 → 一律 404（即使日後觀測功能進場，此擋門先行存在）。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 提供一鍵啟動：單一啟動命令（配合等待旗標）完成後，五個常駐服務
  （反向代理、前端、後端 API、資料庫、快取）全部 healthy、一次性 migration 服務以成功狀態
  結束；命令退出碼 0。
- **FR-002**: 環境組成 MUST 分為共通定義層與開發覆蓋層兩份設定檔；共通層不含對外 port 與
  開發專屬掛載；對外 port 僅存在於開發覆蓋層。
- **FR-003**: 對外 port 配置 MUST 照 ADR 0019：42079（API 直連）、42080（代理 HTTP）、
  42081（前端直連）、42443（代理 TLS）、45432（資料庫）、46379（快取），全部只綁
  127.0.0.1；容器內一律使用各服務的官方預設號（HTTP 類 80、TLS 443、自寫 API 8080、
  資料庫 5432、快取 6379）。
- **FR-004**: migration 閘門 MUST 成立：資料庫 healthy 後 migration 服務才執行；migration
  成功結束後 API 服務才啟動；migration 失敗時 API 不啟動且啟動命令顯式失敗。
- **FR-005**: 反向代理 MUST 落實路由契約：`/` 轉前端；`/api/` 前綴剝除後轉後端；`/health`
  由代理自答 200 ok；`/api/metrics` 對外一律 404。
- **FR-006**: TLS 入口 MUST 可用：自簽開發憑證由腳本生成（支援外部 CA 簽發模式與自簽
  fallback）、私鑰與憑證產物不入版控。
- **FR-007**: 機密管理 MUST 具備：六個機密（資料庫密碼、快取密碼、兩個簽章機密、兩個連線
  字串）由腳本一鍵生成且冪等；底層機密重生時其組合機密同步重生；預檢命令在啟動前指名缺檔；
  機密以檔案掛載方式注入容器、環境變數僅承載檔案路徑；實值路徑列入版控忽略清單、僅範本
  （佔位值）入版控。
- **FR-008**: 後端最小服務 MUST 提供：純文字健康端點（憲法信封例外）；設定載入支援
  「檔案路徑型環境變數優先於直值型」；啟動時驗證六機密中後端消費的四支在場、非空、非範本
  佔位值，違反即啟動失敗並指名；收到終止訊號時平滑關閉。
- **FR-009**: migration 空殼 MUST 可跑：零支 migration 情況下執行「套用」動作能成功連庫、
  建立框架版本記錄表、以退出碼 0 結束——作為閘門載體與 002 刀的掛載點。
- **FR-010**: 熱重載 MUST 成立：後端原始碼變更後容器內自動重編重啟（以輪詢偵測、WSL2 掛載
  可用）；前端由開發伺服器原生熱更新；兩者皆不需手動重啟容器。
- **FR-011**: 啟停 MUST 冪等：停止後重啟（保留卷）更快且全綠；連卷清除後重來仍全綠。
- **FR-012**: port 對照文件 MUST 機器生成：文件生成命令從 compose 設定產出全量對照表；
  一致性檢查命令能攔截 compose 與文件的漂移（B-002 落地、stub 轉真）。
- **FR-013**: 版本 MUST 全數釘完整數字版（映像 tag、工具鏈、工具安裝），不留浮動版本；
  定值與查證紀錄凍結於 docs/brainstorms/001-compose-stack.md §0／§1，實作以該定案為準。
- **FR-014**: 本刀全程 MUST 保持 base-web 零 fork 改動（可 git 稽核：其工作樹乾淨、指針
  停在既有提交零新增）。
- **FR-015**: 與 rev3 同機並行 MUST 零衝突：專案名、網路名、卷名前綴、對外 port 空間全部
  與 rev3 隔離，兩套環境可同時運行互不干擾。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 從乾淨狀態（不含映像下載與首次編譯快取）到整套環境可用，操作者需要的命令
  不超過 4 條（機密生成、憑證生成、預檢、啟動）；後續日常啟動 1 條命令完成。
- **SC-002**: 七個連通點（代理 HTTP、代理 TLS、經代理 API、API 直連、前端、資料庫、快取）
  通過率 100%；metrics 路徑對外一律 404。
- **SC-003**: 後端小幅原始碼變更從存檔到新行為可觀察 ≤ 60 秒（不含首次冷編譯）；期間零次
  手動容器操作。
- **SC-004**: 任一機密缺失或為佔位值時，問題在啟動階段被指名攔截的比率 100%——不存在
  「環境啟動成功但配置實為壞值」的狀態。
- **SC-005**: port 對照文件與環境實際設定一致率 100%（由提交前檢查機制保證，漂移即攔截）。
- **SC-006**: 波 0 不變式成立：本刀收刀時 base-web 零新提交、工作樹乾淨（版本控制可稽核）。
- **SC-007**: 日常啟停迴圈（保留卷的停止→啟動→全 healthy）在 5 分鐘內完成。

## Assumptions

- 執行環境：WSL2 上的 Docker Engine＋Compose v2 已可用；host 不需要任何語言工具鏈（rust／
  node 全在容器內）。
- 雙 worktree（base-web、rust-api）已接妥（pins 見 docs/generated/STATE.md）；本刀的程式
  改動只落 rust-api，base-web 完全不動。
- rev3 環境可能在同機並行運行，本刀以隔離設計（port 空間 4xxxx、獨立專案名／卷／網路）
  共存，不要求 rev3 停機。
- 範圍邊界（明確不含、歸屬已定）：prod 部署形（含 prod 覆蓋層、正式憑證自動化、前端正式
  build）歸部署刀；觀測（logs／metrics 四件套與 exporter）歸觀測刀；清理排程服務歸
  cleanup-job 功能刀；單服務 standalone compose 檔不帶入（brainstorm 拍板 #13）。
- 上游輸入凍結：wave-0-plan §2.1（交付物九項）、brainstorm 001（拍板 13 題＋五節設計）、
  ADR 0019（port）、ADR 0020（波 0 組成）；本 spec 與上游不一致時以上游拍板為準並回報。
- 資料庫使用者／庫名沿 rev3 慣例（brainstorm §0 節 2 核可紀錄），非本刀新決策。
