# Feature Specification: 019-secrets-sops 機密管理——SOPS+age 全量導入＋三層掃描防線

**Feature Branch**: `019-secrets-sops`

**Created**: 2026-07-28

**Status**: Draft

**Input**: User description: "@docs/brainstorms/019-secrets-sops.md"（階段 0 brainstorm 全文＝本 spec 唯一輸入；
外部方案研究結論已全數內嵌該檔、專案文件不引用其原始筆記）

## Clarifications

### Session 2026-07-28（brainstorm 階段逐題親決 14 問，摘錄影響 scope 者）

- 範圍＝**全量一刀**：掃描防線（第 0 步）＋SOPS 本體（第 1~5 步）＋治理落檔。
- 掃描器＝**Betterleaks**（安裝時依釘版紀律雙查最新穩定版＋驗 checksum；與 gitleaks drop-in 同構、反悔可換）。
- cosign＝**不裝**：容器 image digest 釘版為實際防線；ADR 誠實登記「官方簽章存在但未啟用驗證」。
- age-keygen＝**GitHub release 官方二進位**＋checksum、產完金鑰即刪。
- 私鑰＝**方式 B′ 傾向＋#3 實測定案**（passphrase 加密 identity）；退路預拍＝**退方式 A**（同時
  SECRETS_DIR 降解法 2）；`SOPS_AGE_KEY` 環境變數注入私鑰值＝紅線不可採。
- SECRETS_DIR＝**解法 2′ `/dev/shm/rev4-secrets`**（tmpfs；與 B′ 唯一自洽組合）；**#11 為結論
  反轉條件**（U1 首波實測；反轉→**升級 user 重拍、非 agent 自決**）。
  ★重拍（2026-07-29、#11 反轉後）：SECRETS_DIR 改**解法 2＝`$HOME/.cache/rev4-secrets`**、
  私鑰維持 B′、#3 退路僅退方式 A——詳 tasks T005 備註與 ADR 0080。
- prod 加密檔＝**不建**（dev 單檔單規則；prod 目標形狀入 ADR 備忘）；切檔粒度＝**dev 一檔 8 key**；
  ca.key＝**不進 SOPS**（維持可重生、ADR 記重評條件）。
- 團隊組成（A-4）＝「**將來可能有非工程師**」→ ADR 記「必須分兩層」為待觸發架構決定；
  問題 B（個人密碼管理器）＝延後＋四反轉條件登記。
- 驗收升格＝**a／b／c／d／f／h＋preflight 一致性檢查全升**；g（無 docker 離線還原）不升、
  改 RUNBOOK 災復備註。**升格字母對照表**（此組字母＝brainstorm 候選驗收編號，與
  `contracts/secret-pipeline.md` §P4 的 (a)~(e)＝FR-016 五要求本地編號**屬不同命名空間**，
  引用時必言明出處）：

  | 字母 | 驗收項 |
  |---|---|
  | a | 解密產物 byte 級健康（尾端無 CR／LF、leaf 與 composite 內嵌值 byte 數一致）＋preflight CR 護欄 |
  | b | 產物 owner 與 mode（非 `root:root`、目錄 700／檔 644） |
  | c | obs＋metrics 全開、三個非 root service 讀取成功 |
  | d | `docker inspect` 驗機密掛載來源已離開 `/mnt/d` |
  | f | 刪 enc 檔一 key → 管線 fail-loud（零寫入、非零退出） |
  | g | 無 docker 離線還原演練（**不升格**、改 RUNBOOK 災復備註） |
  | h | 掃描三延伸（誤報基線對照／三 repo 覆蓋實擋／連線字串規則命中） |

### Session 2026-07-28（/speckit-clarify）

- Q: 值比對防線的 repo 覆蓋範圍？ → A: 僅外層 repo 掛值比對；兩源倉靠 Betterleaks 樣式層
  （含 DSN 自訂規則）——源倉 hook 保持零 python 依賴、毫秒級承諾可守；裸值格驗收只在外層跑。
- Q: pre-push 第二層的 repo 覆蓋範圍？ → A: 三 repo 同套 pre-push——hooks 目錄共用、一檔生效
  三處；掃描範圍＝本次 push 的 commit 範圍；第二層價值最高處＝`--no-verify` 慣性風險集中的
  base-web（push 目標為 GitHub 遠端）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 機密洩漏三層掃描防線（三 repo） (Priority: P1)

維護者在外層、rust-api、base-web 任一 repo 提交含機密（樣式命中或 `deploy/secrets` 現值）的
變更時，commit 當場被擋、終端輸出遮蔽不含明文；例行收刀簿記（events.jsonl 40-hex SHA）不被
誤擋。防線＝Betterleaks（事件型廣譜）×既有 docs-sync L16（狀態型窄樣式）×值比對（確定性）
三層互補。

**Why this priority**: 不依賴 SOPS、獨立可交付；機密進 git 是本刀所有失敗模式中不可逆性最高
的一種（事件型：進了就永在歷史）；且兩源倉現況零防線、近 90 天約 1/3 提交構不到掃描。

**Independent Test**: 不建任何 SOPS 資產即可完整驗證——8 格 fixture＋三 repo 實擋＋簿記不誤擋。

**Acceptance Scenarios**:

1. **Given** 防線佈署完成且 allowlist 就緒，**When** 於外層以 `git add`＋`commit` 提交含
   KEY=value 形假機密的 fixture，**Then** commit 被擋且輸出遮蔽（不含明文值）。
2. **Given** 同上，**When** 以 `git commit -a` 路徑提交 DSN 形（`postgres://user:pw@host`）
   fixture，**Then** 同樣被擋（自訂連線字串規則命中；證 index 面無盲區）。
3. **Given** rust-api 與 base-web 各自 worktree，**When** 各提交假機密 fixture，**Then** 兩源倉
   皆被擋（三 repo 覆蓋實證）。
4. **Given** `deploy/secrets/*.txt` 現值存在，**When** 將某現值貼進 tracked 文件並 commit，
   **Then** 值比對層擋下且絕不印出該值（裸值形樣式掃描不中屬預期、由此層接）。
5. **Given** SOPS 密文形 fixture，**When** commit，**Then** 不誤報（放行）。
6. **Given** allowlist 就緒，**When** 例行簿記 commit（events.jsonl append 40-hex SHA），
   **Then** 不誤擋（誤報基線現場重建後實證）。
7. **Given** 掃描器二進位缺席的新機，**When** 跑 `tools/bootstrap`，**Then** 體檢以 die 級擋下
   並附安裝指引（而非 commit 時 exit 127 猝死）。
8. **Given** 開發者以 `--no-verify` 繞過 pre-commit，**When** push，**Then** pre-push 同套規則
   第二層攔下。

---

### User Story 2 - 機密以密文入版控＋可斷言的解密管線 (Priority: P2)

維護者把 8 支機密（7 leaf＋alert_webhook_url）加密進單一 tracked 檔案；解密管線以 fail-loud
斷言重建明文：缺 key 零寫入、user 自填值不被靜默覆寫、私鑰來源切換可反向驗證。

**Why this priority**: 本刀核心價值（機密可版控、加人零機密傳遞）；依賴 U1 實測閘結果
（#3 定私鑰方式），但不依賴明文落點遷移（US3）。

**Independent Test**: 在現行 `deploy/secrets/` 落點不變的前提下即可完整驗證加密往返、斷言
行為與守衛。

**Acceptance Scenarios**:

1. **Given** `.sops.yaml` 與加密檔就緒，**When** 做一次加解密最小往返，**Then** 還原值與原值
   一致（#1）。
2. **Given** 加密檔入版控，**When** 檢視 `git diff`，**Then** key 名明文可讀、每個值皆為密文
   （非整檔單一密文塊）。
3. **Given** 加密檔被刻意刪去一個 key，**When** 跑解密管線，**Then** 零寫入＋非零退出＋指名
   缺哪個 key（絕不靜默造亂數）。
4. **Given** 落點現值與加密檔內值不同（alert_webhook_url 情境），**When** 解密，**Then** 現值
   不被覆寫、差異另存 `.new` 並警示人工比對。
5. **Given** identity 檔移走＋相關環境變數清空，**When** 解密，**Then** 必須失敗（#10 反向
   驗證——防取鑰途徑靜默回退）。
6. **Given** B′ passphrase 加密 identity（#3 實測成立時），**When** 另開 shell 解密，**Then**
   跳出 passphrase 提示且解得開；提示次數被記錄（#13、不寫死）。

---

### User Story 3 - 明文離開 /mnt/d（SECRETS_DIR 遷移） (Priority: P3)

解密後明文自 9p（權限恆 777）遷至 tmpfs；compose 與全部腳本經單一事實來源（`.env`）取得落點；
遷移不產生假性完成；觀測軌全開仍讀得到機密。

**Why this priority**: 消除 9p 777 缺口＝本刀威脅模型主收益之一；依賴 US2 的解密管線與 U1
實測閘（#2／#11）。

**Independent Test**: 遷移五步＋落點驗證＋全開讀取，全程機判。

**Acceptance Scenarios**:

1. **Given** 遷移執行至驗證步，**When** 逐容器 `docker inspect` 檢查掛載，**Then** 機密來源
   路徑皆非 `/mnt/d`；**之後才**刪除 9p 明文。
2. **Given** 未設 SECRETS_DIR 變數，**When** `docker compose config`，**Then** 回退解析至
   `./deploy/secrets` 專案相對路徑（#4 向後相容）。
3. **Given** `--profile obs --profile metrics` 全開，**When** 檢查 grafana（UID 472）、
   postgres-exporter（65534）、redis-exporter（59000），**Then** 三者讀得到 `/run/secrets/*`
   且服務健康。
4. **Given** 解密產物，**When** byte 級與屬性檢查，**Then** 尾端無 CR 無 LF、leaf 與 composite
   內嵌值 byte 數一致、owner＝本人 uid:gid、目錄 700 檔案 644。
5. **Given** `wsl --shutdown` 重開機且未跑解密儀式，**When** 跑 preflight，**Then** 明確紅
   （指名缺檔）而非服務靜默啟動失敗。

---

### User Story 4 - 營運程序落地（加人／撤銷／輪替／遺失／開機儀式） (Priority: P4)

維護者依 RUNBOOK 完成日常與異常操作：編輯機密、加人／換機四步、撤銷四步（原子 rotate）、
金鑰／passphrase 遺失處置、開機儀式；既有 §7 輪替表增補「輪替後 re-encrypt 回加密檔」步驟。

**Why this priority**: 營運程序是防線的長期承載；依賴 US2 資產存在。

**Independent Test**: 以演練用第二把金鑰跑完整撤銷演練＋輪替一支機密驗證 enc 檔同步。

**Acceptance Scenarios**:

1. **Given** 演練用第二把金鑰已加入後撤銷，**When** 執行撤銷四步＋否定測試，**Then** #7 五
   準則全過（核心：舊 `enc:` stanza 貼回新檔跑解密必失敗於 MAC 驗證；rotate 前後值密文必變）。
2. **Given** 輪替某支機密，**When** 依 §7 增補後程序執行，**Then** 加密檔同步更新、下次解密
   不觸發 `.new` 守衛。
3. **Given** RUNBOOK 各段落地，**When** 對照機判單逐段核，**Then** 編輯／加人／撤銷／遺失／
   開機儀式／災復備註／版本記錄欄齊備且與實測結果一致。

---

### User Story 5 - 治理落檔 (Priority: P5)

拍板全數落 ADR（5 支）；遞延項登記 BACKLOG（B-115 prod 分層包）；指路文字連帶更新；
`--no-verify` 慣例廢止同步 NOTES。

**Why this priority**: 收刀完備性；依賴前四者結果（實測欄位、驗收證據）。

**Independent Test**: 對照綱要逐支核 ADR 欄位；BACKLOG／NOTES／指路文字逐處核。

**Acceptance Scenarios**:

1. **Given** 收刀前，**When** 檢視 `docs/arc42/decisions/`，**Then** 5 支 ADR（0079 起）
   accepted 且涵蓋既定綱要（含 U1 三閘實測結果欄）。
2. **Given** 外層 `deploy/secrets` 現場 `git grep` 命中清單，**When** 逐檔判定，**Then** 程序性
   引用已更新、歷史文件不改、判定結果可查。

---

### Edge Cases

- 開機未解密即 `docker compose up`：preflight 指名缺檔擋下；compose 端「secret file does not
  exist」警告不可作為唯一防線。
- 加密檔 git merge 衝突：依 RUNBOOK 程序（雙方解密→明文三方合併→重加密→核對 recipient 清單
  一致），暫存明文限 repo 內 gitignored 目錄。
- passphrase 遺失（B′）：該 identity 永久失效＝走加人流程重加入；離線備份義務含 passphrase 本身。
- U1 閘反轉：#2 失敗→方案形狀改環境變數注入＝**升級 user 重拍**；#11 反轉→**升級 user 重拍**
  SECRETS_DIR（2 vs 2′ 比較基礎改變）；#3 失敗→預拍退路（方式 A＋解法 2＝
  `$HOME/.cache/rev4-secrets`）自動生效、不停工、ADR 記錄。
- B′ 下命令替換（無 tty）情境呼叫解密：tty 守衛擋下並給指引，不得 hang 死或靜默寫壞檔。
- 他機 clone 未跑 bootstrap：兩源倉 hooksPath 未設＝無防線——bootstrap 體檢斷言暴露；此為
  已知邊界（per-machine 設定）。
- 值比對層在明文缺席（開機未解密）時：skip＋提示、不 fail-closed（樣式掃描仍在）。
- 歷史中既存的 40-hex SHA 誤報源：allowlist 圈定至欄位層級、禁整檔放行；全歷史基線現場重建、
  不沿用研究舊數字。

## Requirements *(mandatory)*

### Functional Requirements

**掃描防線（U0）**

- **FR-001**: 掃描器（Betterleaks）MUST 以原生二進位安裝並釘版（安裝時雙查最新穩定版＋驗
  checksum、版本記入 RUNBOOK）；`tools/bootstrap` MUST 具存在性斷言——缺席即 die 並附安裝指引。
- **FR-002**: allowlist（`.gitleaks.toml`）MUST 先寫再啟用：以全歷史掃描現場重建誤報基線、
  圈定精確至欄位層級、禁整檔放行；啟用後例行收刀簿記 commit MUST 不被誤擋。
- **FR-003**: MUST 含自訂連線字串規則，至少涵蓋 postgres(ql)／redis／mysql 帳密 URL 樣式；
  DSN 形 fixture MUST 被擋。
- **FR-004**: 外層 pre-commit 掃描行 MUST 位於既有 docs-sync 檢查之前、輸出遮蔽；hook 註解
  MUST 明確區分事件型（掃描）與狀態型（docs-sync）語意差異。
- **FR-005**: 同套掃描規則 MUST 掛 pre-push 作第二層（攔截 `--no-verify` 放行後尚未離開本機
  的 commit）；**覆蓋範圍＝三 repo 同套**（clarify 拍板：hooks 目錄共用、一檔生效三處；掃描
  範圍＝本次 push 的 commit 範圍）。
- **FR-006**: 三 repo 覆蓋：外層＋rust-api＋base-web 的 commit MUST 皆經機密掃描。hook 檔
  MUST 寄宿外層 repo（單一事實來源）、由 bootstrap 冪等設定兩源倉 `core.hooksPath` 指向之
  ——兩源倉樹零改動（零 fork-delta 面、零憲法軌道波及）；bootstrap 體檢 MUST 斷言 hooksPath
  已設。源倉 hook MUST 只跑毫秒級樣式掃描（僅 Betterleaks、零 python 依賴、不觸發上游
  husky／pnpm 鏈）。
- **FR-007**: 值比對防線（tools/ 新增 python 工具、定名於 plan）MUST 讀取機密現值比對 staged
  內容、命中即擋且絕不輸出值本身；值缺席時 skip＋提示（不 fail-closed）；MUST 自帶紅綠
  self-test 防恆綠、掛 pre-commit 條件觸發自測（比照 018 慣例）。**覆蓋範圍＝僅外層 repo**
  （clarify 拍板：源倉靠樣式層、零 python 依賴）。
- **FR-008**: 8 格 fixture 驗收 MUST 全跑（於外層）：KEY=value／DSN／裸值／SOPS 密文四形 ×
  `git add`+`commit` 與 `git commit -a` 兩路徑；裸值形樣式掃描不中屬預期結果、MUST 由值比對
  層攔截驗證（僅外層有此層）；兩源倉另各以樣式形 fixture 實擋至少一案（SC-001）。

**實測閘（U1）**

- **FR-009**: 三實測閘 MUST 先於對應施工並記錄於 ADR：#2 容器 bind-mount ext4／tmpfs 路徑
  （失敗→**升級 user 重拍**方案形狀、非 agent 自決）；#11 Windows 側 docker client 定址 WSL
  內部路徑（反轉→**升級 user 重拍** SECRETS_DIR、非 agent 自決）；#3 B′ passphrase identity
  可用性含 pinentry keyring 假象排除（失敗→預拍退路自動生效：方式 A＋解法 2＝
  `$HOME/.cache/rev4-secrets`、ext4 持久，不停工、ADR 記錄）。

**SOPS 資產（U2）**

- **FR-010**: sops MUST 經官方容器 wrapper（`deploy/sops.sh`）提供、image 以 digest 釘版；
  wrapper MUST：互動旗標條件化（非互動不配 tty）、不轉發 host 編輯器變數、顯式轉發
  `SOPS_AGE_*` 三變數；exec bit MUST 以 `git update-index --chmod=+x` 落 index。
- **FR-011**: age-keygen MUST 自官方 GitHub release 取得＋checksum 驗證、用完即刪；私鑰 MUST
  落地 host（B′＝passphrase 加密內容）、落地後 MUST 驗尾端無 CR。
- **FR-012**: MUST 禁止以 SSH 金鑰充當 SOPS identity（規則落 ADR＋RUNBOOK）；identity 來源
  切換後 MUST 緊接 #10 反向驗證。
- **FR-013**: `.sops.yaml` MUST 過四自檢：單檔式 path_regex、僅一條 creation_rules、寫完驗證
  規則確實命中、不設 encrypted_regex；機密 key 命名 MUST 禁 `_unencrypted` 後綴。
- **FR-014**: 加密檔 MUST 為 `deploy/secrets.dev.enc.yaml` 恰 8 key（口徑：7 leaf＋
  alert_webhook_url；composite 不進、由既有腳本重生）；alert_webhook_url MUST 如實搬移現值
  （不可重生）；明文中間產物 MUST 限 repo 內 gitignored 目錄、用完即刪、不得出現於 staged。
- **FR-015**: 版控後 `git diff` MUST 呈現 key 名明文、值全密文（非整檔加密退化形）。

**解密管線與接線（U3）**

- **FR-016**: `deploy/decrypt-secrets.sh` MUST 滿足五要求：寫檔無尾端換行；key 數與名稱斷言、
  不符零寫入退出；輸出目錄以 700 建立且早於任何 `up`；alert_webhook_url 現值差異另存 `.new`
  不覆寫；B′ 情境 tty 守衛。
- **FR-017**: SECRETS_DIR MUST 以 repo 根 `.env`（gitignored、bootstrap 代勞產生、
  `.env.example` tracked）為單一事實來源；compose 與 decrypt／generate／preflight MUST 讀值
  一致（腳本 source `.env`，殺「compose 讀新落點、腳本查舊落點」分裂）。
- **FR-018**: compose 頂層 10 條 secrets 條目 MUST 改帶預設值變數展開（未設變數回退
  `./deploy/secrets`＝#4 驗收）；「忘設變數＝保護失效」取捨 MUST 由 preflight＋bootstrap 斷言
  補償並於 ADR 誠實登記。
- **FR-019**: generate／preflight／setup-reaper-role 三腳本 MUST 改帶預設展開（含 PW_FILE）；
  generate MUST 增 `--compose-only`（缺 leaf 報錯退出、不生成）；preflight MUST 增 CR 護欄與
  composite↔leaf 一致性檢查（過期 database_url 必紅）。
- **FR-020**: `tools/bootstrap` secrets 體檢 glob MUST 隨 SECRETS_DIR。
- **FR-021**: 遷移 MUST 依五步順序（`down`→decrypt→設值 `up -d`→逐容器 inspect 驗來源→才刪
  9p 明文）；完成後 `/mnt/d` 全樹 MUST 零明文機密檔。
- **FR-022**: 解密產物權限終值 MUST 目錄 700／檔案 644；obs＋metrics 全開時三個非 root
  service MUST 讀取成功且健康。

**營運與治理（U4／U5）**

- **FR-023**: RUNBOOK MUST 落地：SOPS 營運段（編輯＝edit→decrypt→`up -d --force-recreate`
  不用 restart；加人／換機四步；撤銷四步含原子 `rotate -i --rm-age` 逐檔一行；金鑰／
  passphrase 遺失；開機儀式；災復備註；工具版本記錄欄）；§7 輪替表增補「輪替後 re-encrypt 回
  加密檔」步驟；§4 人工清單增 .wslconfig／BitLocker 確認項；§12 增工具速查。
- **FR-024**: 撤銷演練 MUST 過 #7 五準則（否定測試核心）；#13 提示次數 MUST 實測記錄且
  RUNBOOK 不寫死。
- **FR-025**: ADR 5 支（0079 起、一決策一檔、綱要＝brainstorm §9）MUST accepted；U1 三閘
  實測結果 MUST 記入對應 ADR。
- **FR-026**: BACKLOG MUST 登記 B-115 prod 機密分層遞延包（prod 加密檔＋#5/#6 驗收＋CI 側
  保護；掛 prod 部署刀群）。
- **FR-027**: `deploy/secrets` 全 repo 命中 MUST 逐檔判定連帶更新（程序引用改、歷史文件不改、
  生成物由 docs-sync generate 重算；判定可查）。**以施工時現場 `git grep` 為準、不以任何靜態
  數字為驗收基準**（拆分口徑以 research R18 為準：**程序性 13 檔＝穩定值**、歷史檔隨本刀 SDD
  產物增長、生成物零命中；歷次計數 brainstorm 27 檔→plan 29 檔→analyze 36 檔皆為當時快照，
  差額全為本刀自身產物自指命中）。
- **FR-028**: base-web `--no-verify` 慣例廢止 MUST 同步 NOTES 對應慣例行（repo 文件不引用
  per-machine memory 路徑）。

### Key Entities

- **機密清單（四口徑）**: 11 檔（7 leaf＋3 composite＋1 user 自填）／10 進 compose／8 入加密
  檔／13 含 dev TLS 私鑰——引用時必言明口徑。
- **加密檔**: `deploy/secrets.dev.enc.yaml`，tracked，8 key，單一 data key、多 recipient 信封。
- **identity**: age 私鑰檔（B′＝passphrase 加密內容）；根信物＝腦中 passphrase（B′）或檔案
  本身（退路 A）。
- **SECRETS_DIR**: 解密明文落點，單一事實來源＝`.env`；拍板值 `/dev/shm/rev4-secrets`。
  ★重拍（2026-07-29、#11 反轉後）：改 `$HOME/.cache/rev4-secrets`、詳 tasks T005 備註與 ADR 0080。
- **allowlist／規則集**: `.gitleaks.toml`＝誤報圈定＋DSN 自訂規則；三 repo 共用。
- **hook 面**: 外層 `.githooks/`（含源倉用 hook 目錄）＋兩源倉 `core.hooksPath` 指向設定
  （per-machine、bootstrap 冪等）。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 四形 fixture × 兩路徑共 **8 案（＝「8 格」）** 結果全符預期（該擋的擋、密文不誤報、
  兩路徑一致），且三 repo 各至少一案實擋。
- **SC-002**: 誤報基線重建後，連續例行簿記 commit 零誤擋（以本刀期間全部真實簿記 commit 為樣本）。
- **SC-003**: 全新環境僅憑 clone＋一把已授權私鑰＋bootstrap＋解密儀式即重建全部 11 支機密檔，
  preflight 全綠、`docker compose up` 服務全健康——零人工傳遞任何機密值。
- **SC-004**: 加密檔缺任一 key 時解密管線零寫入、非零退出；注入過期 composite 時 preflight 必紅。
- **SC-005**: 遷移完成後 `/mnt/d` 全樹零明文機密檔、逐容器機密掛載來源皆非 `/mnt/d`；obs＋
  metrics 全開三非 root service 讀取成功。
- **SC-006**: 撤銷演練 #7 五準則全過（含否定測試 MAC 失敗）；#10 反向驗證通過（移走 identity
  必失敗）。
- **SC-007**: alert_webhook_url 現值全程 byte 級不變（如實搬移證明）；構造差異情境時觸發
  `.new` 而非覆寫。
- **SC-008**: 解密產物 byte 級健康全過：尾端無 CR／LF、leaf 與 composite 內嵌值 byte 數一致、
  owner 本人、目錄 700 檔 644。
- **SC-009**: pre-commit 端到端延遲維持秒級紅線——**機判門檻**：本刀新增兩段（樣式掃描＋值比對）
  合計中位數 **≤5s**；值比對工具本體 staged 時其自測增量 **≤3s**。★**量法依 L-155 硬性規定**：
  兩段成本**各自以 `perf_counter` 直接包該段（掃描器呼叫／值比對工具）連跑數次取中位數**——
  **絕不可用整鏈 `time` 前後差量**（drvfs 牆鐘變異 ±1.5s 大於被測成本，018 U2 曾量出負值）；
  T001 的整鏈基線僅供「有無數量級劣化」粗判。超標→記錄成本結構並掛 BACKLOG（比照 018 SC-008）。
- **SC-010**: 治理完備：ADR 5 支 accepted（含三閘實測欄）、RUNBOOK 各段落地、B-115 登記、
  `deploy/secrets` 命中逐檔判定完成（現場 grep 為準）。

## Assumptions

### 既有資產（已核實、2026-07-28 接地偵察）

- SOPS 產物零存在；掃描工具零安裝——全部自紙上起步。
- `generate-secrets.sh:41`／`preflight-secrets.sh:12` 無條件賦值 SECRETS_DIR、
  `setup-reaper-role.sh:16` PW_FILE 硬編碼；compose 頂層 `secrets:` 區塊起 :361、10 條 `file:`
  條目位於 :363-385（兩個行號指涉不同、非矛盾）、零變數展開；
  `generate-secrets.sh:160` chmod 600（9p 上 no-op）。
- `.githooks/pre-commit` 19 行無掃描行；無 pre-push；兩源倉 hooksPath 未設；`tools/bootstrap`
  :120-131 體檢僅缺檔 warn、零二進位斷言。
- docs-sync L16（018）＝既有狀態型窄樣式防線、無 DSN 樣式——與本刀互補。
- events.jsonl 三欄（merge／pins.web／pins.api）各 18 筆、合計 54 筆 40-hex＝allowlist 首要
  誤報源；`deploy/secrets` 外層命中＝**程序性 13 檔（穩定值、清單見 research R18）**＋歷史檔
  （隨本刀產物增長；analyze 階段快照 36 檔／113 命中）＋生成物零命中。
- RUNBOOK §7 輪替表存在（:128 起）——本刀增補而非新建。
- 無任何 CI 設定——CI 側掃描與金鑰保護遞延（B-115）。
- alert_webhook_url 現值＝已撤 dev 收器 URL（39 bytes）；「如實搬移」規則不因收器已撤而改變。

### 設計取捨（有意識接受）

- compose 帶預設值向後相容 ⇒ 忘設變數時保護靜默失效——以 preflight＋bootstrap 斷言補償、
  ADR 誠實登記（「結構性不可能誤 commit」與「向後相容」不可兼得，取後者）。
- 值比對層 fail-open（明文缺席時 skip）——樣式掃描為主防線、值比對為增援。
- B′ 日常摩擦（每次解密輸 passphrase）與 2′ 開機儀式（重開機後重跑解密）＝已拍代價。
- cosign 不裝＝供應鏈防線止於 digest 釘版（誠實登記、非假裝有驗簽）。
- 單人現況：撤銷演練以演練用第二把金鑰完成；#5（company_pc 解不開 prod）／#6（CI 取不到
  金鑰）結構性不可測、遞延 B-115。
- **hook 寄宿外層修正**（對 brainstorm §4 自拍項的接地修正）：base-web 倉內新增 hook 目錄
  不在憲法 §III 任何授權軌道內（預設軌道僅 `.env*`／typings／`rev4-*.ts` 新檔）——改為 hook
  檔寄宿外層 repo＋bootstrap 設 `core.hooksPath` 指向：覆蓋面相同、兩源倉樹零改動、零憲法
  Amendment 需求；rust-api 同形（對稱、單一事實來源）。
- g（無 docker 離線還原演練）不升格＝災難恢復路徑僅 RUNBOOK 備註。

### 範圍外（明確排除）

- prod 機密分層（prod 加密檔、path_regex 分層、#5/#6 驗收）→ B-115、掛 prod 部署刀群。
- CI 建置與 CI 側掃描／金鑰保護。
- 問題 B（個人密碼管理器選型）→ 延後＋四反轉條件（ADR-E 登記）。
- user 個人側動作：ssh 私鑰加 passphrase、家目錄疑似 passphrase 供應 `.sh` 檔檢視（repo 外
  提醒、不入 repo 文件）。
- 憲法 Amendment：本刀預期零 Amendment（hook 寄宿外層即為此設計）。

### 治理（隨刀落地）

- 隨做隨記：拍板→ADR draft→收刀 accepted；踩坑→LESSONS；衍生→BACKLOG；per-unit pin bump
  即時（本刀預期兩源倉零 commit——hook 寄宿外層後兩源倉樹不動、pin 不動）。
- 活書 as-built 歸收刀簿記 commit（docs-sync L6(b) 閘）；tasks 不排 push／merge。
- 本 spec 不引用外部研究筆記檔（結論已內嵌 brainstorm＋本檔）。
