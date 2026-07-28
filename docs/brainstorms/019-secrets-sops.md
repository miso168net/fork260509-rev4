# 019-secrets-sops 階段 0 brainstorm — 機密管理：SOPS+age 全量導入＋三層掃描防線

- 日期：2026-07-28
- 方法：前置評估 Workflow（20 支唯讀 agent：外部方案研究 10 章精讀＋repo 5 域偵察＋4 域差距
  比對＋完備性審查→115 落點、24 拍板題、12 處研究陳述與 repo 現況漂移）→ 主線親核關鍵行號
  證據（全數屬實）→ 拍板題逐題親決（14 問）→ 設計七節逐節核可 → 交 user 審。
- 存在理由：user 指示 2026-07-28——依外部機密管理方案研究（2026-07 完成之 SOPS+age 決策研究）
  把本 repo 機密管理自「gitignore 結構防線＋9p 明文」升級為「密文入版控＋明文離開 /mnt/d＋
  三層洩漏掃描」，**全量一刀**（掃描防線＋SOPS 本體＋治理落檔）。研究結論已全數內嵌本檔，
  **專案文件一律不引用其原始筆記檔**（user 明示）。
- 觸發拓樸前提：沿用本 repo 既有閘點（pre-commit／bootstrap／機判驗收單），不新增常駐服務
  （「零維運」為選型硬約束——先排除 Vault／Infisical 等 server 類方案；SOPS+age 勝出理由見 §3）。
- 下一步：本檔 commit 落 default（rev4-admin-root）→ user 審 → 手動起手 `/speckit-specify`
  （feature branch `019-secrets-sops` 由 specify 建）。

---

## §1 接地盤點（偵察實證精華、主線親核）

- **SOPS 產物全數不存在**：`.sops.yaml`、`deploy/sops.sh`、`deploy/decrypt-secrets.sh`、
  `deploy/secrets.dev.enc.yaml`、`.env`／`.env.example`、`.gitleaks.toml` 皆缺；host 未裝
  sops／age／gitleaks／betterleaks／cosign；`~/.config/sops/` 不存在——方案自紙上起步。
- **SECRETS_DIR 三處硬編碼**（研究判定「最嚴重的坑」、親核屬實）：`deploy/generate-secrets.sh:41`
  與 `deploy/preflight-secrets.sh:12` **無條件賦值** `SECRETS_DIR="$SCRIPT_DIR/secrets"`（外部
  export 被靜默吃掉）；`deploy/setup-reaper-role.sh:16` `PW_FILE=deploy/secrets/reaper_password.txt`
  硬編碼相對路徑。
- **compose 接線現況**：`docker-compose.yml:361-385` 頂層 `secrets:` 恰 10 條 `file:` 條目
  （`reaper_password` 不進 compose、由 setup-reaper-role 直讀）；零環境變數展開。
- **權限現況**：`deploy/generate-secrets.sh:160` `chmod 600`（9p 上 no-op、顯示恆 777）——
  研究裁定終值＝目錄 700／檔案 644（grafana UID 472、postgres-exporter 65534、redis-exporter
  59000 三個非 root service 要讀，600 會在開 obs／metrics 軌時才炸）。
- **機密清單口徑**（引用時必言明）：**11 檔**＝7 leaf＋3 composite＋1 user 自填（`deploy/secrets/
  *.txt`）；**10**＝進 compose 項；**8**＝加密檔 key 數（7 leaf＋alert_webhook_url）；13＝11＋
  2 支 dev TLS 私鑰。`alert_webhook_url.txt` 現值 39 bytes 真值（dev 收器已撤、NOTES 載明）＝
  8 key 中唯一不可亂數重建者。
- **hook／掃描現況**：`.githooks/pre-commit` 19 行、docs-sync check→lint 起手、**無任何機密
  掃描行**；無 pre-push；`tools/bootstrap:120-131` secrets 體檢僅檢缺檔（warn 級）、全檔零二進位
  存在性斷言；**submodule hooksPath 皆未設**——rust-api 生效 hooks 僅 .sample＝零防線、base-web
  有上游 simple-git-hooks 但本 repo 慣例 `--no-verify`（躲 husky 跑 pnpm install）＝一併繞過。
  近 90 天提交占比：外層 483／rust-api 160／base-web 75——**約 1/3 提交發生在兩源倉、現行外層
  hook 構不到**。
- **既有第三防線**：docs-sync L16 憑證內容掃描（018 落地）＝狀態型窄樣式四類（`tools/docs-sync.py`
  CRED_PATTERNS）、無 DSN 連線字串樣式——與本刀掃描器互補不重疊（定位入 ADR）。
- **allowlist 首要誤報源**（親測）：`docs/ops/events.jsonl` 現 30 行、merge／api／web 三欄位
  各 18 筆 40-hex SHA——不先圈定、第一個被擋的是例行收刀簿記。外層 `git grep -l 'deploy/secrets'`
  命中 27 檔＝指路文字與腳本引用全落點。
- **RUNBOOK §7 機密輪替表存在**（`docs/ops/RUNBOOK.md:128` 起、逐支機密有程序）——研究懸置的
  「輪替表存在與否」兩案並陳就地結清：**執行既有表＋增補 re-encrypt 步驟**，非建新表。
- **無任何 CI 設定**（外層與 rust-api；base-web 僅上游遺留 workflow）——CI 側金鑰保護（對應
  遞延驗收 #6）無落點、遞延。

## §2 名詞表（本檔自成一體所需之最小集）

| 詞 | 意思 |
|---|---|
| leaf | 亂數產生的原始機密（7 支）。進加密檔 |
| composite | 由 leaf 組出的連線字串（database_url／redis_url／reaper_database_url）。不進加密檔、由 generate-secrets.sh 重生 |
| recipient | 可解開某加密檔的 age 公鑰（及持有者）。公鑰非機密 |
| data key | 每個加密檔一把的對稱金鑰，再用各 recipient 公鑰各包一次——**權限粒度是檔案不是 secret** |
| identity | age 私鑰檔（預設 `~/.config/sops/age/keys.txt`） |
| 方式 A／B′ | 私鑰明文落地（chmod 600）／私鑰檔本身以 passphrase 加密落地（根信物＝腦中 passphrase） |
| 解法 2／2′ | 解密明文寫 `$HOME/.cache/rev4-secrets`（ext4 持久）／寫 `/dev/shm/rev4-secrets`（tmpfs、RAM-backed、永不進 vhdx） |
| 事件型／狀態型 | 掃描器＝事件型（`--no-verify` 繞過一次即真進 git、下次不再抓）；docs-sync＝狀態型（繞過只延後） |

## §3 拍板記錄（user 親決 13 題）

- **範圍**：**全量一刀**（第 0 步掃描防線＋SOPS 本體第 1~5 步＋治理落檔）。落選：只做掃描防線
  （研究執行序的保守建議）／掃描最小刀（防線只護外層＝有洞）。
- **選型前提**（研究結論、內嵌備查）：SOPS+age 四理由＝公鑰模型加人零機密傳遞／`.sops.yaml`
  path→recipients 進版控可 review／值層加密 key 名明文 diff 可讀／updatekeys·rotate 撤銷語意
  清楚；**誠實收窄**：對唯一真競爭者 dotenvx 實際只贏「多 recipient」＋「宣告式 per-path 對應」
  兩項，足以支撐（本專案核心需求＝dev/prod 分層）但論證只有一條腿。
- **掃描器＝Betterleaks**（v1.7.0 為研究查核當日值；安裝時依釘版紀律雙查最新穩定版＋驗
  checksum）。落選 gitleaks（已宣告 feature-complete；兩者 drop-in 同構、反悔可換）。
- **cosign＝不裝**：digest 釘版為實際防線；ADR 誠實登記「官方簽章存在但未啟用驗證」。
- **age-keygen＝GitHub release 官方二進位**＋checksum、產完金鑰即刪。落選：alpine 容器 apk
  （執行期未釘版）／apt（1.1.1 最舊）；第三方 age 映像＝紅線排除。
- **私鑰＝B′ 傾向＋#3 實測定案**：施工首波實測原生 passphrase identity（產鑰→`--age` 直指
  最小往返→另 shell `sops -d` 須跳提示且解得開；確認 pinentry 無 keyring 自動填入假象）。
  成功→定案 B′；**退路預拍＝退方式 A**（同時 SECRETS_DIR 降解法 2、ADR 記錄）——不採
  SOPS_AGE_KEY_CMD 備案（容器邊界複雜化）；`-e SOPS_AGE_KEY=私鑰值` 注入＝紅線不可採。
- **SECRETS_DIR＝2′ `/dev/shm/rev4-secrets`**：與 B′ 唯一自洽組合（免「已知不自洽」登記）。
  代價＝`wsl --shutdown` 後清空、每次開機重跑 decrypt＋輸一次 passphrase。**#11 為結論反轉
  條件**（Windows 側 docker client 定址 WSL 內部路徑）、U1 首波實測、反轉則本題回頭重拍。
- **prod 加密檔＝不建**：dev 單檔單規則；prod 目標形狀入 ADR 備忘（`deploy/secrets.prod.enc.yaml`
  ／recipients≥2／不含 company_pc／託管 DB 時 database_url 升格 primary secret 入 SOPS）。
- **切檔粒度＝dev 一檔 8 key**、多人或需層內分權時重評（ADR 記條件）。
- **ca.key＝不進 SOPS**：維持可重生；ADR 備註重評條件（多人協作或 CDP 信任鏈重建成痛點）。
- **A-4 團隊組成＝「將來可能有非工程師」**→依研究規則升級：ADR 記「必須分兩層」為**待觸發
  架構決定**（非工程師 GUI 層屬問題 B、觸發即重啟選型），現況單人不影響本刀施工。
- **問題 B（個人密碼管理器）＝維持延後＋四反轉條件登記**（①#3 失敗且方式 A 殘餘風險不可
  接受②出現非工程師成員③prod 上線且人數>1④決定以 SSH 金鑰充當 identity——④已被本刀禁令
  封死）。
- **驗收升格＝a／b／c／d／f／h＋preflight 一致性檢查全升**；g（無 docker 離線還原）不升、
  改 RUNBOOK 災復備註。

## §4 工程拍板（自拍回報）

- root 產物對策＝**B：host shell stdout 重導向＋umask 077**（沿 generate-secrets 慣例；容器
  `--user` 對策會弄壞私鑰掛載點）。
- 檔名紅線：`deploy/secrets.dev.enc.yaml`（格式副檔名放最後；寫成 `.env.enc` 會退化整檔加密）。
- **不設 `encrypted_regex`**（白名單語意、新欄位靜默不加密）；`_unencrypted` 後綴命名禁令。
- git merge driver 不裝（單人單檔現況 YAGNI；衝突處置程序入 RUNBOOK）。
- **SSH 金鑰充當 identity 禁令**落 ADR＋RUNBOOK 規則段、不動憲法（屬營運操作規則非治理原則）。
- 候選 i（.wslconfig swap／BitLocker 確認）→ RUNBOOK §4 人工必填清單、不入驗收。
- hook 佈署形狀：rust-api＝倉內新增 `.githooks/pre-commit`＋bootstrap 設 `core.hooksPath`；
  base-web＝fork-delta **純新增型**目錄（如 `.githooks-rev4/`、零上游行改動）＋bootstrap 設
  hooksPath——lint 照跑、無「原行」需求。
- `.env` 斷鏈閉合：compose 原生讀 `.env`；decrypt／generate／preflight 三腳本各自
  `source .env`（存在時）——SECRETS_DIR 單一事實來源、殺「compose 讀 ext4、腳本查 9p」分裂。
- 值比對腳本（暫名 `tools/secret-value-guard.py`，spec 階段定名）：讀 SECRETS_DIR（回退
  deploy/secrets）現值→比對 staged diff→命中即擋、**絕不輸出值本身**；自帶紅綠 self-test
  防恆綠（比照 L16 慣例）；值缺席（開機未解密）→skip＋提示、不 fail-closed（樣式掃描為主防線）。
- bash 腳本測試策略＝fixture 演練機判（刪 key／CR 注入／`.new` 觸發），不硬套單元測試框架；
  python 工具照 018 慣例 pytest 式＋pre-commit 條件觸發。

## §5 波次結構（閘門式單刀五波）

- **U0 掃描防線**（不依賴 SOPS）：Betterleaks 釘版安裝→**全歷史掃描現場重建誤報基線**（不得
  沿用研究舊數字）→`.gitleaks.toml`（allowlist 先寫再啟用＋DSN 自訂規則至少涵蓋
  `(postgres(ql)?|redis|mysql)://user:pw@` 樣式）→值比對腳本→pre-commit（掃描行在 docs-sync
  之前、`--redact`、事件型註解）＋pre-push→三 repo hook 佈署→bootstrap 斷言→8 格 fixture 驗收。
- **U1 實測閘**（三 go/no-go、結果入 ADR）：**#2** Docker Desktop bind-mount ext4/tmpfs 路徑
  （失敗→方案形狀改「解法 1 環境變數注入」＝**升級 user 重拍**）；**#11** Windows 側 docker
  定址（反轉→SECRETS_DIR 重拍）；**#3** B′ 可用性（失敗→預拍退路自動生效、不卡關）。
- **U2 SOPS 工具鏈**：`deploy/sops.sh`（digest 釘版、`-it` 條件化、不轉發 EDITOR、顯式
  `-e SOPS_AGE_*`；chmod +x＋`git update-index --chmod=+x` 防 9p exec bit 掉失）→age-keygen
  →產金鑰（B′：`age-keygen | age -p`、落地後 `xxd` 驗尾端無 0d）→`.sops.yaml`（四自檢：單檔式
  path_regex／僅一條 creation_rules／驗命中／不設 encrypted_regex）→enc 檔首建（明文中間產物
  落 repo 內 gitignored 目錄、用完即刪；alert_webhook_url **如實搬移**；驗收：diff 見明文 key
  名＋`ENC[...]` 值、key 數＝8、staged 無明文）。
- **U3 解密管線＋接線**：`deploy/decrypt-secrets.sh`（五要求：寫檔無尾端換行／key 數名稱斷言
  不符**零寫入退出**／目錄 700 早於任何 up／alert_webhook_url 差異**另存 `.new` 不覆寫**／
  B′ tty 守衛）→`.env`＋`.env.example`＋bootstrap 代勞→compose 10 條目改
  `${SECRETS_DIR:-./deploy/secrets}/…`（向後相容取捨誠實入 ADR：忘設變數＝保護失效、由
  preflight＋bootstrap 斷言補）→generate/preflight 改帶預設展開＋`--compose-only`＋CR 護欄＋
  composite↔leaf 一致性→setup-reaper-role PW_FILE→bootstrap 體檢 glob。
- **U4 遷移＋總驗收**：遷移五步（**先 `docker compose down`**→decrypt→設變數 up -d→
  `docker inspect .Mounts` 逐容器驗來源已非 /mnt/d→確認無誤**才**刪 9p 明文）→升格驗收全集
  （§7）→**#7 撤銷演練**→**#10 反向驗證**。
- **U5 治理收攏**：ADR 群 accepted＋RUNBOOK＋BACKLOG＋收刀簿記（隨做隨記、此波收攏）。

## §6 驗收全集（機判單、比照 017 quickstart 慣例）

8 格 fixture（KEY=value／DSN／裸值／SOPS 密文 × `git add`+commit 與 `git commit -a` 兩路徑；
裸值形樣式掃描不中屬預期、由值比對層接）｜h 三延伸（誤報基線對照：例行簿記 commit 不誤擋／
三 repo 實擋：兩源倉各建假機密 fixture／DSN 命中）｜a：`xxd` 驗解密產物尾端無 0d 無 0a＋leaf
與 composite 內嵌值 byte 數一致＋preflight CR 護欄轉紅復歸｜b：產物 owner＝本人 uid:gid、
目錄 700 檔 644｜c：`--profile obs --profile metrics` 全開、UID 472/65534/59000 讀得到
`/run/secrets/*` 且健康｜d：逐容器 inspect Mounts 離開 /mnt/d｜f：刻意刪 enc 檔一 key→管線
零寫入報錯退出、絕不靜默造亂數｜preflight composite↔leaf 一致性（過期 database_url 必紅）｜
#7 撤銷演練五準則（核心＝否定測試：舊 `enc:` stanza 貼回新檔跑原廠 decrypt 必失敗於 MAC 驗證；
另：recipient 清單前後、rotate 前後值密文必變、dev 檔無 prod 級機密人工確認、前置 age-keygen）
｜#10：identity 移走＋unset 後 `sops -d` 仍解得開＝切換未生效、必須失敗才對｜#1 加解密最小
往返｜#4 未設變數時 `docker compose config` 解析回 `./deploy/secrets` 相對路徑｜#13 多
recipient passphrase 提示次數（實測記錄、RUNBOOK 不寫死）｜#9 落點×私鑰方案自洽終驗。
**#5／#6（company_pc 解不開 prod／CI 取不到金鑰）＝結構性不可測、遞延登記 B-115。**

## §7 靜默坑→防線對映（16 列、設計不變式）

| 靜默失效模式（全綠假象） | 本刀防線落點 |
|---|---|
| encrypted_regex 白名單漏加密新欄位 | 不設 encrypted_regex＋`_unencrypted` 命名禁令 |
| path_regex 目錄式比對不到／第二條 rules 被忽略 | 單檔式＋單規則＋寫完驗命中（.sops.yaml 四自檢） |
| prod 機密放進 dev 檔＝dev 圈全員立得 | 流程不變式＋prod 不建檔＋#7 準則④人工確認 |
| 取鑰失敗靜默退回磁碟明文私鑰 | #10 反向驗證（必做、緊接切換後） |
| `~/.ssh/id_*` 被零設定自動採用為 identity | SSH 禁令（ADR＋RUNBOOK）＋#10 |
| 先 rotate 後 updatekeys／多檔 rotate 只吃第一個 | RUNBOOK 收 `rotate -i --rm-age` 原子指令、逐檔一行 |
| 撤銷演練只驗「解不開 HEAD」＝假通過 | #7 五準則含否定測試 |
| alert_webhook_url 被 decrypt 靜默覆蓋 | `.new` 守衛（差異必人工比對） |
| `-it` 寫死＋重導向→CRLF 汙染密碼尾端 | wrapper `-it` 條件化＋a 驗收＋preflight CR 護欄 |
| 檔 600→觀測軌開才炸 Permission denied | 目錄 700 檔 644＋c 全開驗收 |
| export SECRETS_DIR 被無條件賦值靜默吃掉 | 三腳本帶預設展開＋`.env` source 閉環＋#4 |
| 改值不觸發重建、容器 bind 舊 inode | 遷移先 down＋d inspect Mounts |
| 變數未設時解法 2 靜默失敗（容器照 Started） | `.env` bootstrap 代勞＋preflight 斷言 |
| preflight 只檢「檔在非空」：缺 key 造亂數／過期 composite 照 OK | decrypt 斷言零寫入＋f 刪 key 演練＋一致性檢查 |
| 容器掃描不帶 GIT_INDEX_FILE：`commit -a` 掃 0 bytes | 原生二進位鐵律＋8 格含 commit -a 路徑 |
| DSN 連線字串落預設規則盲區／hooksPath per-repo 邊界 | 自訂 DSN 規則＋h 命中驗收；三 repo 佈署＋h 實擋驗收 |

## §8 Risk／Guard／Rollback 三欄表（遷移類變更）

| 變更 | Risk | Guard | Rollback |
|---|---|---|---|
| 明文落點 9p→tmpfs（2′） | 假性完成（容器 bind 舊 inode）；開機後忘解密服務起不來 | 遷移五步先 down；d 驗收；bootstrap 體檢＋preflight 斷言；RUNBOOK 開機儀式 | `.env` 改回 default 值→up -d --force-recreate（compose 寫法不變、改一值即回） |
| enc 檔首建＋明文中間產物 | 明文暫存誤入版控；awu 真值走失 | 暫存限 gitignored 目錄＋用完即刪＋staged 驗收；awu 如實搬移＋`.new` 守衛 | enc 檔 git rm＋`deploy/secrets/*.txt` 原樣在（U4 前不刪 9p 明文） |
| 兩源倉 hooksPath 佈署 | base-web 旁路 husky 改變 commit 行為；他機 clone 未設 hooksPath＝無防線 | hook 只跑毫秒級掃描（不碰 pnpm）；bootstrap 幂等佈署＋體檢斷言；h 三 repo 實擋驗收 | `git config --unset core.hooksPath`（單指令、即回原狀） |
| base-web `--no-verify` 慣例廢止 | 舊習慣殘留＝掃描被繞過（事件型、繞過即漏） | memory／NOTES 同步更新；pre-push 第二層攔截 | 慣例可回退（hook 已旁路 husky、--no-verify 不再必要、無回退動機） |

## §9 治理落檔

- **ADR 5 支（0079 起、一決策一檔）**：**A** 選型 SOPS+age（四理由＋誠實收窄＋零維運硬約束＋
  官方容器 digest 釘版＋cosign 不啟用登記＋age-keygen 取得路徑）；**B** 私鑰 B′×SECRETS_DIR 2′
  （自洽論證＋退路預拍方式 A＋#11 反轉條件＋SSH identity 禁令＋passphrase 政策：diceware≥6、
  離線備份含 passphrase 本身）；**C** 加密資產形狀（dev 單檔 8 key／prod 不建含目標形狀備忘／
  ca.key 不進含重評條件／命名紅線／encrypted_regex 不設）；**D** 洩漏掃描三層防線定位
  （Betterleaks 事件型廣譜 × docs-sync L16 狀態型窄樣式 × 值比對確定性——互補並存；三 repo
  覆蓋；base-web `--no-verify` 慣例廢止）；**E** 團隊組成前提（將來可能有非工程師→兩層架構
  待觸發決定）＋問題 B 四條件延後登記。
- **RUNBOOK**：新增 SOPS 營運段（編輯機密＝sops edit→decrypt→`up -d --force-recreate` 不用
  restart；加人／換機四步零機密傳遞；撤銷四步＋原子 rotate；金鑰／passphrase 遺失；開機儀式；
  災復備註〔g 不升格之代償〕；apk／工具版本記錄欄）；**§7 輪替表增補「輪替後 re-encrypt 回
  enc 檔」步驟**（否則輪替值與 enc 檔脫鉤、下次 decrypt 觸發 `.new` 守衛）；§4 人工清單增
  .wslconfig／BitLocker 確認；§12 工具鏈速查增 sops.sh／decrypt-secrets.sh。
- **BACKLOG**：B-115 prod 機密分層遞延包（prod enc 檔＋#5/#6 驗收＋CI 側 GitHub Environments
  保護；掛 prod 部署刀群 B-037/B-042/B-081 同期）。
- **repo 外提醒（不入 019 範圍、不入 repo 文件）**：①無 passphrase 之 ssh 私鑰加固
  （`ssh-keygen -p`、僅 user 本人執行）②家目錄一支疑似自動供 passphrase 之 `.sh` 檔用途檢視。
- **指路文字**：README／CLAUDE.md §3 故障排除指向、`deploy/secrets/README.md`——隨 U3/U5
  連帶更新（27 檔命中逐檔判定：程序引用改、歷史文件不改）。

## §10 未定案殘餘（U1 實測閘結清、非本檔懸案）

- #2／#3／#11 三閘結果（含 pinentry keyring 假象排除）→ 寫入 ADR-B 實測欄。
- #13 passphrase 提示次數 → 實測後記 RUNBOOK（不寫死）。
- 全歷史誤報基線數字 → U0 現場重建（研究舊數字全部過時：commit 數已 483、三欄各 18 筆）。
- Betterleaks 實際釘定版本 → 安裝時雙查最新穩定版（研究當日值 v1.7.0 僅供參考）。
