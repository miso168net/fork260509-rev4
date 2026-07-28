# research.md — 019-secrets-sops Phase 0 接地決策（R1~R19）

> 產出方法：5 支唯讀偵察 agent 並行（掃描器上游／SOPS-age 上游／deploy 腳本面／治理慣例／
> 環境面），全部事實附來源與查核日 2026-07-28。**★ 標記＝推翻或修正 brainstorm 既有假設者**，
> 必須以本檔為準。網路查得之版本號屬浮動量，安裝時仍依釘版紀律雙查並由 user 拍板。

---

## R1 ★ 掃描器選型事實校正（FR-001）

**Decision**: 採 Betterleaks，釘完整版號；設定檔命名 `.gitleaks.toml`。

**Rationale**:
- Betterleaks **不是第三方 fork**——由 gitleaks 原作者 Zach Rice 主導、Aikido 贊助、MIT 授權，
  定位為 gitleaks 官方後繼（brainstorm 記為「社群接棒 fork」，語意修正）。當下最新穩定
  **v1.7.1（2026-07-27）**；發版節奏約兩週一版、1.x 仍快速演進。
- gitleaks 最新穩定 v8.30.1（2026-03-21），README 逐字宣告 feature complete、只收安全補丁。
- **設定檔解析順序使 `.gitleaks.toml` 成為雙向可攜檔名**：Betterleaks 依序找
  `.betterleaks.toml` → **fallback `.gitleaks.toml`**。只要設定檔堅持 gitleaks 子集欄位
  （`[[rules]]`／`[[allowlists]]`／`[[rules.allowlists]]`），兩支 scanner 可互換；一旦用
  Betterleaks 專屬 CEL 欄位（`validate`／`filter`／`tokenEfficiency`）即單向鎖死。
  → **紀律：設定檔頭註記「僅用 gitleaks 子集欄位」**。

**Alternatives considered**: 維護雙檔（`.betterleaks.toml`＋`.gitleaks.toml`）——無必要，fallback
已保證相容且雙檔會漂移。

**★ 資產命名校正**：Linux 資產＝`betterleaks_1.7.1_linux_x64.tar.gz`（**版號無 `v` 前綴、架構
寫 `x64` 非 `amd64`**）；checksums 檔名固定 `checksums.txt`（**不含版號**，與 gitleaks 的
`gitleaks_8.30.1_checksums.txt` 命名不同）。多版本快取須以目錄隔離避免互蓋。

---

## R2 ★ 掃描器 exit code 分流（FR-001／FR-004）

**Decision**: hook 呼叫顯式帶 `--exit-code 2`，hook 內對 2（掃到洩漏）與 1（scanner 自身失敗）
分流輸出不同訊息。

**Rationale**: 上游約定＝**0 無洩漏／有洩漏回 `--exit-code` 值（預設 1）／執行錯誤無條件 1**。
預設值下「掃到機密」與「binary 壞掉、config 語法錯」同碼，被擋者無從判斷該修 commit 還是修
環境。設 2 後兩者可分。

**Alternatives considered**: 沿用預設 1＋以 stderr 內容判別——脆（訊息格式非契約）。

---

## R3 掃描指令列定稿（FR-004）

**Decision**: pre-commit 指令＝`betterleaks git --pre-commit --staged --redact --verbose --exit-code 2`。

**Rationale**（逐旗標，皆自原始碼與官方 hook 範本核實）:
- `--pre-commit`＋`--staged`＝官方 `.pre-commit-hooks.yaml` 同形；兩者任一為真即切 `git diff`
  模式，`--staged` 決定只掃索引（不掃工作樹未暫存雜訊）。
- **`--redact` 預設 0＝完全不遮蔽**，裸寫等於 100（全遮）。不帶則掃到真機密時明文噴進終端與
  scrollback＝二次外洩。**硬紀律，寫進 hook 註解。**
- `--verbose` 讓被擋者看到命中的 rule id 與檔案行（配合 redact 不外洩值）；不帶只有退出碼。
- **`protect`／`detect` 子命令兩專案皆已隱藏**（gitleaks v8.19.0 起 deprecated；Betterleaks 設
  `Hidden: true` 屬相容遺留、無文件保證）→ 一律用 `git` 子命令。

---

## R4 ★ pre-push 範圍掃描與全零 oid 退階（FR-005）

**Decision**: 自行組裝——hook 讀 stdin 逐行解析 `<local-ref> <local-oid> <remote-ref> <remote-oid>`，
跳過刪除行（local-oid 全零），對每行執行 `betterleaks git --log-opts=<remote-oid>..<local-oid>`；
**remote-oid 全零（新分支首推）退階為 `--log-opts=<local-oid> --not --remotes=origin`**；
`--remotes=origin` 為空（全新 remote）時退為掃整條分支。

**Rationale**: 上游**無 pre-push 專用模式或官方範本**（僅文件化 `--log-opts` 自訂 git log 範圍）；
stdin 契約來自 git 本身。退階選 `--not --remotes=origin` 而非「掃整條分支」＝只掃尚未存在於任何
origin 分支的 commit，避免首推大分支時重掃全史（秒級紅線）。

**Alternatives considered**: 新分支一律掃整條分支——正確但可能極慢；作為第二層退階保留。

---

## R5 ★ allowlist 精確圈定寫法與最大靜默失效點（FR-002）

**Decision**: 誤報圈定一律用 per-rule allowlist＋**`condition = AND`**＋`paths` 與 `regexes`
並用＋顯式 `regexTarget`；**嚴禁只寫 `paths` 整檔放行**。

**Rationale**: `condition` **預設 OR**——漏寫 `AND` 會退化成「檔案符或值符任一即放行」的過寬放行，
且不報錯（本 schema 最大靜默失效點）。`regexTarget` 合法值＝`secret`（預設）／`match`／`line`，
非法值會 fail-loud。allowlist 至少需 `commits`／`paths`／`regexes`／`stopwords` 其一，全空即
config 載入失敗。

**本專案首要誤報源（實測）**：`docs/ops/events.jsonl` 30 列中 **40-hex 共 54 筆**——`merge` 18 筆、
`pins.web` 18 筆、`pins.api` 18 筆（★ brainstorm 記「三欄各 18」正確，但總數應為 54；spec 沿用
「三欄各 18 筆」語意不變）。圈定方式＝`paths` 限該檔 × `regexes` 限 40-hex 樣式 × `condition = AND`。
次要誤報源＝`deploy/secrets/*.txt.example`（tracked 假值檔，11 支各 22 bytes）與
`specs/017-audit-retention/quickstart.md` 的 `curl -u admin:...` 示例。

**基線重建**：全歷史掃描於 U0 現場重跑（現況 commit 483、與研究舊值 417 已漂移），舊 findings
數字一律不沿用。

---

## R6 自訂 DSN 規則最小合法形（FR-003）

**Decision**: 新增一條 `[[rules]]`，`id`＋`regex` 必填、補 `description` 與 `keywords`；
regex 至少涵蓋 `(postgres(ql)?|redis|mysql)://<user>:<pw>@`。

**Rationale**: 機器驗證的必填只有 `id` 非空、且 `regex` 與 `path` 至少一個非空；`keywords` 屬
效能預過濾（同時降誤報），`entropy` 屬調參可後補。本專案 3 支 composite（`database_url`／
`redis_url`／`reaper_database_url`）正是此形，落在預設規則庫盲區。

---

## R7 ★ sops 版本、映像與 digest（FR-010）

**Decision**: wrapper 釘 `ghcr.io/getsops/sops@sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`
（＝v3.13.3-alpine 的 multi-arch index digest，本輪獨立核實）。

**Rationale**:
- sops 最新穩定 **v3.13.3（2026-07-23）**；官方雙 registry（ghcr／quay），tag 形 `vX.Y.Z` 與
  `vX.Y.Z-alpine`。**alpine 變體不含雲端 CLI 相依、攻擊面小**，本專案純 age 流程不需 KMS。
- digest 取得法：`GET ghcr.io/token?scope=repository:getsops/sops:pull` 取匿名 token → 對
  `/v2/getsops/sops/manifests/v3.13.3-alpine` 發 HEAD 帶 manifest-list Accept → 讀
  `docker-content-digest`（等價：`crane digest`／`docker buildx imagetools inspect`）。
- **★ registry 與 digest 必須成對**：quay 為獨立推送，同 tag digest 與 ghcr 不必然相同。

**★ 官方映像內容物（alpine v3.13.3）**：基底 alpine:3.24，僅裝 ca-certificates 與 vim，
`ENV EDITOR vim`，ENTRYPOINT＝sops；**不含 age／age-keygen／curl／gnupg**；**無 USER 指令
＝以 root（UID 0）執行**。三個直接後果：①產鑰不能指望此映像（R9）；②掛載卷內產物屬 root
→ 採 root 產物對策 B（R11）；③`sops edit` 開箱可用、**wrapper 不得轉發 host `EDITOR`**。

---

## R8 ★ passphrase identity 機制與容器邊界（FR-011／實測閘 #3）

**Decision**: B′ 路線技術上成立（sops ≥ v3.10.0 原生支援，本刀釘 v3.13.3 遠高於門檻）；
**wrapper 必須條件化配置互動終端**，因容器內無 gpg-agent → 必回退終端互動。

**Rationale**（原始碼級核實）:
- 解包函式＝`unwrapIdentities`（`age/encrypted_keys.go`，v3.10.0 起存在；v3.9.4 為 404）。
  以 `bufio.Peek(14)` 偵測開頭 `age-encryption`（binary）或 `-----BEGIN AGE`（armor）即視為
  passphrase 加密 identity，走 `LazyScryptIdentity` 延遲解密。
- **passphrase 取得順序：先試 gpg-agent（快取鍵 `SopsAge` 前綴），連不上才回退終端互動。**
  官方容器內無 gpg-agent → 必然回退互動 → **需 `-it`**。這正是 wrapper「互動旗標條件化」
  的技術根據：有 tty 就配 `-it`，無 tty 則失敗要吵（而非 hang）。
- `loadIdentities` 對三個環境變數與預設 `keys.txt` **每一個來源都套 `unwrapIdentities`**
  → 加殼 identity 放任一來源皆可。

**★ `age -p` 加殼可行性澄清**（brainstorm 標為未解）：`age -p` 的 **passphrase 讀取一律經
`term.WithTerminal`（優先開 `/dev/tty`）**，與 stdout 重導向互不干擾——故
`age-keygen | age -p > ~/.config/sops/age/keys.txt` **在真 TTY 下可行**；官方無
passphrase-from-file 旗標＝加殼是**一次性人工儀式**，不可無頭自動化。

**pinentry 前置（本機實測）**：`~/.gnupg/` 存在但 `gpg-agent.conf` 等 conf 檔**全不存在**、
`/etc/gnupg` 不存在 → 可直接建檔、零衝突。預設 pinentry＝`pinentry-gnome3`，`pinentry-curses`
亦在。**#3 實測前先寫 `gpg-agent.conf` 指定 `pinentry-program /usr/bin/pinentry-curses`**
（純終端 session 下 gnome3 版可能彈不出來；WSLg 在但未實測）。

---

## R9 ★ age 取得與完整性驗證方式校正（FR-011）

**Decision**: 自官方 GitHub release 取 `age-v1.3.1-linux-amd64.tar.gz`，**以 GitHub release API
的 `digest` 欄位比對 `sha256sum`**，產鑰完畢即刪二進位。

**Rationale**: ★ **age 無 `checksums.txt` 類檔案**（brainstorm 假設「驗 checksum」的方法需校正）
——每資產改配 `.proof` 檔（Sigsum 透明日誌證明，需 sigsum 工具鏈、成本高）；實務上完整性驗證取
API `digest` 欄位（v1.3.1 linux-amd64＝`sha256:bdc69c09cbdd6cf8b1f333d372a1f58247b3a33146406333e30c0f26e8f51377`）。
age 最新穩定 **v1.3.1（2025-12-28）**；**官方不發布容器映像**（README 無、release 無映像推送）。

**`age-keygen` 輸出形制**：無參數輸出三行至 stdout（`# created:` RFC3339／`# public key: age1…`／
`AGE-SECRET-KEY-1…`）；stdout 非終端時公鑰另印 stderr。**取 recipient 的權威路徑＝`age-keygen -y`**
（亦可 grep `# public key:` 註解行）。解析時須同時容忍 `AGE-SECRET-KEY-1` 與 v1.3 新增的
`AGE-SECRET-KEY-PQ-1` 前綴（sops v3.13.3 兩者皆吃）。

---

## R10 ★ 尋鑰順序與 SSH 禁令技術根據（FR-012）

**Decision**: SSH identity 禁令落 ADR＋RUNBOOK；`#10` 反向驗證為必做測項。

**Rationale**（原始碼核實）：`loadIdentities` 是**聯集載入非 first-match**，依序收集
①SSH：`SOPS_AGE_SSH_PRIVATE_KEY_FILE`／`_CMD`／**預設 `~/.ssh/id_ed25519` 與 `~/.ssh/id_rsa`
（零設定自動探測）** ②`SOPS_AGE_KEY`（內容本身，唯一允許同行多鑰）③`SOPS_AGE_KEY_FILE`（路徑）
④`SOPS_AGE_KEY_CMD`（stdout 為 identity，執行時注入 `SOPS_AGE_RECIPIENT`）⑤預設
`$XDG_CONFIG_HOME/sops/age/keys.txt`（Linux 回退 `~/.config/sops/age/keys.txt`）。
→ 聯集語意使「切換取鑰來源」後舊來源仍可能默默生效＝**#10 反向驗證不可省**；
SSH 預設探測使爆炸半徑意外綁上 SSH 私鑰＝禁令的技術根據。

---

## R11 ★ wrapper 形制定稿（FR-010）

**Decision**: `deploy/sops.sh` 要件——①digest 釘版常數（R7）②`-it` 條件化（有 tty 才配）
③**不轉發 `EDITOR`**（映像已內建；必要時用 `SOPS_EDITOR`）④顯式 `-e SOPS_AGE_KEY -e
SOPS_AGE_KEY_FILE -e SOPS_AGE_KEY_CMD`⑤掛載 `$PWD:/work -w /work` 與私鑰目錄唯讀
⑥**root 產物對策 B**：解密一律由 host shell 收 stdout＋`umask 077` 寫檔，不用 `--output`／`-i`
產出明文⑦`chmod +x` 後 `git update-index --chmod=+x`（drvfs exec bit 不落 index）。

**Rationale**: ①~④見 R7／R8；⑥因映像以 root 執行、host umask 不跨容器邊界，若讓容器直接產出
明文檔會得到 `root:root` 產物，使既有 `generate-secrets.sh` 的 `chmod` 在 `set -euo pipefail`
下直接中止。對策 A（`--user` 對映）會讓容器內 `HOME` 不再是 `/root`、私鑰掛載點失效，須改用
`SOPS_AGE_KEY_FILE` 指容器內路徑——複雜度更高。

**沿用既有慣例**：`generate-secrets.sh` 已以 `docker run --rm alpine/openssl` 產亂數（host 零
openssl 依賴），wrapper 走容器與該慣例同構。

---

## R12 ★ `.sops.yaml` 語法要點（FR-013）

**Decision**: 單一 `creation_rules`、`path_regex` 寫**錨定式** `^deploy/secrets\.dev\.enc\.yaml$`、
recipient 用 `age:` YAML 清單形、**不設任何範圍選項**。

**Rationale**（原始碼核實）:
- **`path_regex` 比對的是「相對於 `.sops.yaml` 所在目錄」的相對路徑**（`TrimPrefix(filePath,
  configDir+separator)`），且用 `MatchString`＝**非錨定、子字串命中即算中** → 不寫 `^…$` 則
  路徑任何位置含該片段都會誤中。`.sops.yaml` 置 repo 根。
- 規則依 YAML 順序 **first-match-wins**；`path_regex` 空字串＝無條件命中的萬用 fallback
  （本刀只有一條規則，不設 fallback）。
- recipient 兩種寫法：`age:`（字串逗號分隔或 YAML 清單）與 `key_groups[].age[]`（Shamir 用）。
  **採清單形**免引號與空白陷阱；單一信任域不需 key_groups。
- **六個範圍選項互斥**（`encrypted_suffix`／`unencrypted_suffix`／`encrypted_regex`／
  `unencrypted_regex`／`encrypted_comment_regex`／`unencrypted_comment_regex`），同時設兩個以上
  即報錯。**全不設時預設套用 `unencrypted_suffix = "_unencrypted"`**（＝全加密、僅該後綴鍵留
  明文）——這正是「不設 `encrypted_regex`＋禁 `_unencrypted` 後綴命名」兩條紀律的根據。

---

## R13 ★ updatekeys／rotate 語意與多檔陷阱（FR-023／FR-024）

**Decision**: RUNBOOK 收錄——加減 recipient＝`updatekeys -y`（可一次多檔）；撤銷＝
`rotate -i --rm-age <公鑰>` **逐檔一行**。

**Rationale**:
- `updatekeys` 以既有 master key 取回**同一把** data key 再換 recipient 重包——**不換 data key**；
  `-y` 為非互動；**可一次多檔**（for 迴圈逐檔、統計失敗數）。
- `rotate` **產生新 data key** 重加密全部值；`--rm-age`／`--add-age` 接逗號分隔清單，可在旋轉
  同時增刪 recipient（一步完成＝消除「先 rotate 後 updatekeys」的順序陷阱）。
- **★ 陷阱確認：`rotate` 只處理第一個位置參數**——多給檔案僅印警告 `More than one positional
  argument provided. Only the first one will be used!`，其餘**靜默略過且 exit code 不變**。
  → 批次必須 shell 層逐檔迴圈＋逐檔檢查退出碼。

---

## R14 ★ SECRETS_DIR 落點的環境接地（FR-017／FR-021／實測閘 #2 #11）

**Decision**: 落點 `/dev/shm/rev4-secrets`（＝解法 2′、拍板值不變），**解密腳本必須自建 0700
子目錄**；swap 殘餘風險誠實入 ADR，`noswap` 私有 tmpfs 列為 RUNBOOK 可選強化步驟（非必要、需 sudo）。

**★ 退路落點具體值（供 #3 失敗時自動生效、免回讀 brainstorm）**：解法 2＝
**`$HOME/.cache/rev4-secrets`**（ext4 持久、跨重開機存活、免開機儀式）；採此值時 SECRETS_DIR
寫入 `.env` 的形式與 2′ 完全相同（**compose 與腳本零改動、只換一個值**），代價＝明文長駐
`ext4.vhdx` 內（與方式 A 的威脅面一致、自洽）。

**Rationale**（本機實測）:
- `/dev/shm` 存在、tmpfs、16G 可用、選項 `rw,nosuid,nodev,noatime`——**未帶 `noswap`**；
  且系統**有 8 GiB swap 分割啟用中**（WSL2 swap＝Windows 側 VHD 檔）→ 記憶體壓力下 tmpfs 內容
  理論上可能落入 Windows 磁碟。**這是 2′ 相對 2 的保護有上限的誠實登記。**
- `/dev/shm` 目錄權限 `drwxrwxrwt`（world-writable＋sticky）→ **落檔必須自建 0700 子目錄**
  （brainstorm 未言明、此為新增要求）。
- 核心 6.18.33.2 ≫ `noswap` 需求（Linux 6.4），`man tmpfs` 本機明載該選項；util-linux 2.39.3
  → 強化選項技術可行、未實測掛載。
- `$HOME` 為原生 ext4（`/dev/sdd`），POSIX 權限可靠；repo 根為 9p（`aname=drvfs`），權限為掛載
  參數假象——**機密實值與解密暫存絕不落 repo 目錄**（既有設計已符合，遷移後更徹底）。
- docker 29.6.2＋compose v5.3.1、Docker Desktop WSL integration 確認；**bind-mount 對 `/dev/shm`
  的可見性與權限行為未實測＝#2 閘的實測對象**。

---

## R15 既有腳本改點定稿（FR-016～FR-020）

**Decision**（逐檔、行號為 2026-07-28 實測基準，施工時以符號重新定位）:

| 檔案 | 現況 | 改法 |
|---|---|---|
| `deploy/generate-secrets.sh:41` | `SECRETS_DIR="$SCRIPT_DIR/secrets"` 無條件 | 改帶預設展開、先 source `.env` |
| 同上 `:37-38` | 唯一旗標 `--force` | 加 `--compose-only` case（缺 leaf 報錯退出、不生成） |
| 同上 `:82`／`:120` | `printf '%s'` 寫檔（無尾端換行） | **不得改為 echo**——byte-identical 不變式前提 |
| 同上 `:160` | `chmod 600` | 改 644（三非 root service 要讀）＋目錄 700 |
| 同上 `:129-131` | composite 期望值字串 | 不動；preflight 一致性檢查複用此組合式 |
| `deploy/preflight-secrets.sh:12` | 同無條件賦值 | 同上 |
| 同上 `:17` | `REQUIRED` 11 名硬編碼陣列 | 保留（與 generate 人工雙維護屬既有現況） |
| 同上 `:23` 後 | 僅 `-f`＋`-s` | 補 CR 偵測分支＋composite↔leaf 一致性 |
| 同上 `:36` | 成功句硬編碼「十一個」 | 改陣列長度插值（免每刀追改） |
| `deploy/setup-reaper-role.sh:16` | `PW_FILE` 硬編碼相對路徑 | 第三同步點、同步改 |
| `docker-compose.yml:363-385` | 10 條 `file: ./deploy/secrets/*.txt` | 全數改帶預設值變數展開 |
| `tools/bootstrap:120-131` | secrets 體檢 glob 綁 `deploy/secrets` | 隨 SECRETS_DIR；缺實值維持 **warn 級**（既有慣例、不升 die） |
| `tools/bootstrap:35` | 僅設外層 hooksPath | 增兩源倉 hooksPath 佈署＋掃描器存在性斷言（**die 級**）＋`.env` 代勞 |

**★ alert_webhook_url 現值確認**：該檔 39 bytes、佔位字串長 51 字元 → **user 已填真值**
（依紀律未讀內容、由長度推斷）。`gen_placeholder` 對既有檔一律不動、`--force` 亦不重置，
重置唯一法＝刪檔重跑 → **任何測試絕不以刪該檔為手段**。

**★ 既有 SKIPPED 三語意不同**（README 對照表若加註須分開描述）：leaf＝檔在即 skip（不驗內容）；
composite＝檔在且**內容等於期望值**才 skip；placeholder＝檔在即 skip、`--force` 無效。

---

## R16 ★ 新工具與 hook 的既有慣例接線（FR-007／FR-004）

**Decision**: 值比對工具定名 **`tools/secret-value-guard.py`**，全面沿用 018 家族慣例：

- **CLI 形制**：`main(argv)` 手寫 `if cmd == "…"` 字面鏈（**非 argparse／dispatch dict**）
  ——`tools-cli` 真表的掃源正則 `RE_DISPATCH_EQ`／`RE_DISPATCH_IN` 只認這兩種形；usage 走
  stderr `exit 64`。
- **★ 必須登記進 `tools/docs-sync.py` 的 `TOOLS_PY` 常數（:1855）**，否則不入
  `docs/generated/reference/tools-cli.md` 真表、L19 命令形 lint 與 L20 空集合守衛涵蓋不到。
- **測試**：單檔內嵌 `unittest.TestCase`（無 pytest、無第三方依賴）＋`test` 子命令
  （`purge_git_env()` 先行→`unittest.main(exit=False, verbosity=1)`→回 0/1）；涉 git fixture
  沿用 `purge_git_env` 隔離（防 `GIT_INDEX_FILE` 寫進真 repo index）。
- **樣式／allowlist 常數化**：沿 L16 慣例——模組層 tuple 常數、`re.compile` 預編譯、
  **無 inline 豁免 marker**、擴充白名單須立 ADR、allowlist 另備專屬測試防零覆蓋。
- **self-test 防恆綠**：執行期字串串接構造紅樣本（避免本檔自命中）＋近似不命中的綠樣本＋
  **邊界樣本**（防「放寬下界」型突變全綠）；每次執行連帶跑、紅未攔或綠誤報即 ERROR。
- **pre-commit 條件觸發**：加入 `.githooks/pre-commit:8` 的 `for t in …` 清單（`grep -qxF`
  整行字面比對）；`tools/bootstrap:105-118` 段 5 無條件全跑清單亦加入。

---

## R17 ★ 三 repo hook 佈署形狀（FR-006／FR-005）

**Decision**: **兩個 hook 目錄**——`.githooks/`（外層，現況 pre-commit 續寫＋新 pre-push）與
`.githooks-submodule/`（兩源倉專用：pre-commit＋pre-push，**僅樣式掃描、零 python 依賴**）；
bootstrap 對兩源倉 worktree `git config core.hooksPath <外層絕對路徑>/.githooks-submodule`。
共用掃描邏輯抽 `.githooks/lib/scan-range.sh`，源倉 hook 以 `dirname "$0"` 自我定位後 source
（**不硬編碼外層路徑**）。

**Rationale**: 三 repo 共指同一目錄會讓源倉 commit 也跑 `python3 tools/docs-sync.py check`
——源倉沒有該檔＝每次 commit 必炸。分目錄比「單目錄＋hook 內自我判別 repo」失效面更小、
零判別邏輯。hooksPath 對源倉必須是**絕對路徑**（相對路徑會相對於源倉根），故由 bootstrap
代勞（per-machine 設定、不入版控）。

**兩源倉樹零改動**＝憲法 §III 軌道零波及的設計動機（plan Constitution Check 第 2／7 題）。

---

## R18 ★ `deploy/secrets` 命中三分流（FR-027 口徑校正）

**Decision**: **程序性引用 13 檔**（逐檔改；此為穩定值＝repo 運作檔）＋歷史文件（不改、**檔數隨
本刀 SDD 進度增長**）＋生成物由 `generate` 重算（不手改、現況零命中）。

**★ 口徑校正（本刀自身多次改寫，故數字必須以現場為準）**：brainstorm 評估當日 27 檔 → plan
Phase 0 偵察 84 命中／29 檔 → **analyze 階段複核實測 113 命中／36 檔＝程序性 13＋歷史 23＋
生成物 0**。差額全部來自本刀自身產物（brainstorm／spec／plan／tasks／research／contracts／
quickstart 皆提及該路徑）自指命中。**程序性 13 檔經現場 `git grep` 逐檔複核、與下表完全一致**
（先前正文誤植「14 檔」，表格本身無漏）。**施工時一律以現場 `git grep` 為準、不以任何靜態數字
為驗收基準。**

**程序性引用 13 檔（逐檔改；以檔名＋落點描述定位，施工時現場 grep 取實際位置）**：

| 檔案 | 落點描述 |
|---|---|
| `.dockerignore` | 機密目錄排除行 |
| `.gitignore` | secrets 實值與 example 的 ignore／反 ignore 規則段 |
| `deploy/dev-webhook-sink.sh` | webhook 收器讀取機密檔的路徑 |
| `deploy/generate-secrets.sh` | 檔頭用法註解與結尾摘要指路句 |
| `deploy/grafana-provisioning/alerting/contact-points.yml` | webhook URL 的機密檔引用 |
| `deploy/preflight-secrets.sh` | 檔頭註解、FAIL 訊息與 OK 訊息中的目錄字樣 |
| `deploy/secrets/README.md` | 標題與全篇程序描述 |
| `deploy/setup-reaper-role.sh` | 檔頭註解與 `PW_FILE` 賦值 |
| `docker-compose.yml` | 頂層 `secrets:` 的 10 條 `file:` 路徑 |
| `docs/arc42/ARCHITECTURE.md` | 機密管理現況敘事（活書現在式、隨收刀更新） |
| `docs/ops/NOTES.md` | alert_webhook_url 維運待辦句 |
| `docs/ops/RUNBOOK.md` | 檔頭指路、§4 人工必填、§7 輪替表、§11 觀測維運各處 |
| `tools/bootstrap` | 檔頭說明與 secrets 體檢段 |

歷史文件（**不改**；analyze 階段實測 23 檔、**隨本刀產物增加而增長**）：歷刀與本刀的
brainstorm／spec／plan／tasks／research／contracts／quickstart／ADR／review 等過去式或設計紀錄。
生成物：由 `docs-sync.py generate` 重算、不手改（現況零命中）。

**`deploy/secrets/README.md` 為唯一向 user 說明 secrets 程序的人寫文件**——本刀改 preflight／
generate 任一行為時，其四處描述（預檢只查檔在且非空／`--force` 全重生語意／chmod 600 注記／
機密對照表的 env 注入欄）列入同刀收尾清單，失真即誤導。

**順帶勘誤候選**：`.gitignore` 中 `.json` 機密規則的註解稱其為「redis_exporter 需 JSON password
file」，與現行 compose 的 sh-wrapper `cat` 形（用 plain txt）不符——疑早期方案殘句；規則本身
無害可留、註解可趁刀勘誤。

---

## R19 agent context script

**Decision**: **不執行** spec-kit 的 update-agent-context 腳本（沿 018 R14 結論）。

**Rationale**: 該腳本在本 repo **不存在**（`.specify/scripts/bash/` 僅
check-prerequisites／common／create-new-feature／setup-plan／setup-tasks）；且 CLAUDE.md 受
250 行 lint 預算治理（現 139 行）、無 spec-kit managed 區段，001~018 歷刀皆未使用。技術脈絡由
plan.md 承載。

---

## 未解事項（移交 U1 實測閘或施工時現場定）

- **#2**（Docker Desktop bind-mount `/dev/shm` 與 tmpfs 的可見性、權限、UID 行為）、**#11**
  （Windows 側 docker client 定址 WSL 內部路徑）、**#3**（B′ 端到端含 pinentry 行為）——U1 閘。
- Betterleaks release 的 `cosign verify-blob` 所需 `certificate-identity` 值官方未公布，需下載一次
  bundle 實測才可寫死 → **本刀只做 `sha256sum -c checksums.txt`**，cosign 驗簽不入範圍（與
  「cosign 不裝」拍板一致）。
- Betterleaks 未知旗標的 exit code 是否同 gitleaks 的 126（兩者同用 cobra，推測相同、未實測）。
- 含 Betterleaks 專屬欄位的 toml 餵給 gitleaks 的確切行為（本刀堅持子集故不觸發）。
- `grafana`／`postgres` 官方映像實際運行 UID 未逐一 `docker image inspect` 實查（沿用
  compose 既有註解慣例；c 驗收會實地證明可讀性，不需預先釘 `user:`）。
