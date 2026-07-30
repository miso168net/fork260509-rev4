---
id: "0080"
title: 私鑰 B′（passphrase 加殼 identity）× SECRETS_DIR 解法 2（$HOME/.cache/rev4-secrets）——三實測閘定案與 #11 反轉後重拍
date: 2026-07-29
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 019-secrets-sops brainstorm §3（user 親決私鑰 B′ 傾向＋SECRETS_DIR 2′）／§9 ADR-B 綱要＋research R7／R8／R9／R14＋spec FR-009~FR-012＋tasks T004／T005／T007 三閘實測（2026-07-28~29）＋user 重拍三點定案（2026-07-29、#11 反轉後）＋user 產鑰儀式拍板 C 案（2026-07-28、T002 釘版呈報時併決）"
tags: [security, secrets, sops, age, deployment]
---

## 背景

019 把機密自「gitignore 結構防線＋9p 明文（權限恆 777）」升級為 SOPS+age 密文入版控＋
明文落點遷出 9p。兩個耦合拍板——**私鑰存放方式**（A 明文 chmod 600 vs B′ passphrase 加殼
identity）與 **SECRETS_DIR 解密明文落點**（解法 2 ext4 持久 vs 2′ tmpfs）——brainstorm 階段
拍 B′×2′（唯一自洽組合），同時預留三個 go/no-go 實測閘：#2（容器 bind-mount ext4／tmpfs
可見性）為硬性前置、#11（Windows 側 docker client 定址 WSL 內部路徑）為結論反轉條件、
#3（B′ passphrase identity 可用性）為 B′ 定案點。三閘於 tasks.md Phase 2 實測結清，其中 #11 反轉、
經 user 重拍後定案為 **B′ × 解法 2（`$HOME/.cache/rev4-secrets`）**。

## 決策

1. **私鑰＝方式 B′**：age identity 以 passphrase 加殼落地 `~/.config/sops/age/keys.txt`
   （開頭 `age-encryption.org/v1`＋scrypt 段；根信物＝腦中 passphrase）。
2. **SECRETS_DIR＝解法 2＝`$HOME/.cache/rev4-secrets`**（ext4 持久、免開機儀式）；
   原 2′（`/dev/shm/rev4-secrets`）拍板值因 #11 反轉作廢。
3. **閘 #3 失敗之預拍退路連帶調整＝僅退方式 A（明文 identity＋chmod 600）**、SECRETS_DIR
   已在解法 2 不再降（本輪 #3 實測全過、退路未動用，條款保留供金鑰輪替等再驗情境）。
4. 解密腳本**自建 0700 子目錄**要求維持（縱深防禦、與落點無關；contracts §P4）。
5. **正式鑰產製儀式＝C 案**（2026-07-28、T002 釘版呈報時併問、user 選定；**本決策 5 即此
   拍板的唯一權威落點**，tasks／RUNBOOK 等執行面文件只留指路、不複述）：
   - **施工期**：agent 以拋棄式 passphrase 產一把「暫代正式鑰」（B′ 形制、機制全走、pty 驅動
     互動），019 全刀施工與演練（含 T033 撤銷演練）因而全自動、零人工中斷。
   - **收刀期**：finishing 階段由 user 親產真鑰，走 RUNBOOK 加人四步（零機密傳遞）＋對暫代鑰
     的撤銷四步；撤銷連帶輪替 7 支 leaf 實值，`alert_webhook_url` 不輪替（該值為 user 已填
     真值、保 SC-007）。
   - **誠實登記**：暫代鑰 passphrase 存在於對話紀錄＝**視同已洩露**；故上列收刀期兩組步驟是
     硬性義務、非可選收尾——019 未完成該義務前，版控內密文的實質保護等同無。

**user 重拍三點定案與理由（2026-07-29、#11 反轉後）**——內容＝上列決策 1~3、不涉決策 4／5；
**本段連同決策 1~3 即此拍板的唯一權威落點**，`tasks.md`／`spec.md`／`plan.md`／`data-model.md`
等執行面文件只留指路（檔名＋節號）、不複述：

- ①SECRETS_DIR＝解法 2：#11 實證 live 通道（Windows 側經 UNC 讀取）對 2 與 2′ 暴露相同，
  2′ 的差異化收益收窄至 at-rest（不落 vhdx）與關機即清，換不回每次開機重跑解密儀式的代價；
  解法 2 的 at-rest 代價＝明文長駐 `ext4.vhdx`——誠實登記、不偽稱有保護。
- ②私鑰維持 B′：#11 事實下（Windows 側可讀走 WSL 內任何檔案）B′ 是唯一不怕「檔案被讀走」
  的 at-rest 信物——讀走的是密文、根信物在腦中；且 identity 保護的是**跨 git 歷史與未來輪替
  的根信物**，與「現值明文暴露面」正交（現值另由落點與掃描防線承載）。
- ③退路連帶調整：SECRETS_DIR 既已定在 2，退路只剩私鑰維度＝僅退方式 A。

## 自洽論證（私鑰方式 × 落點的四格矩陣）

**判準**：一個組合自洽，當且僅當**根信物（identity）的保護強度 ≥ 現值明文的保護強度**。
否則為現值付出的代價（開機儀式、每次解密的摩擦）買不到等值的保護——防護強度由最弱環節決定，
而根信物是最弱環節時，換掉現值落點只是換一個地方放同樣讀得到的東西。

| 組合 | 自洽性 | 說明 |
|---|---|---|
| A × 2（私鑰明文 × ext4 持久） | **不自洽** | #11 事實下 Windows 側可經 UNC 讀走 `keys.txt` 明文＝一次讀取即取得**全部 git 歷史與未來輪替**的解密能力；現值明文只是同一次讀取的附帶品 |
| A × 2′（私鑰明文 × tmpfs） | **不自洽（且代價最高）** | 現值每次開機重解密（儀式代價全付），根信物卻明文長駐——付了儀式的錢，保護等級仍由私鑰決定 |
| B′ × 2′ | 自洽（brainstorm 原拍） | 在「tmpfs 使 Windows 側構不到明文」的**假設**下成立；#11 實測推翻該假設 |
| **B′ × 2（本決策）** | **自洽** | 讀走 identity 檔得到的是密文、根信物在腦中；現值明文的暴露面另由落點（離開 9p 777）＋三層掃描防線（擋入庫面）承載 |

**B′ 的正面論證**：identity 保護的是**跨 git 歷史與未來輪替的根信物**，與「現值明文暴露面」
正交——現值可以輪替（RUNBOOK §7＋§15.4），根信物一旦洩漏則版控內所有歷史版本的密文永久
可解。兩者不可互相代償，故必須各自有防線。

**退路預拍（#3 失敗時）＝僅退方式 A**（明文 identity＋`chmod 600`），SECRETS_DIR 不降階
（決策 3）。本輪 #3 實測全過、**退路未動用**。條款保留供金鑰輪替等再驗情境；**若日後真的
動用退路，必須同刀補記兩件事**：①根信物降為「檔案本身」＝上表 A×2 的不自洽格當場成立、
須明文登記接受；②重評 ADR 0083 之問題 B 反轉條件①（#3 失敗且方式 A 殘餘風險不可接受）。

**#11 反轉條件的定義與其再反轉**：brainstorm 拍 2′ 時預留的反轉條件為「**若** Windows 側
docker client 能定址 WSL 內部路徑，**則** 2 vs 2′ 的比較基礎改變、本題回頭重拍，且必須
**升級 user 重裁、非 agent 自決**」。該條件已實測命中（見下方閘 #11 欄）並依約升級、重拍
定案。**再反轉的觸發條件**（記於此供日後重評）：若 Docker Desktop 或 WSL 側關閉 UNC 通道
（例如改用純 WSL 引擎、或 `\\wsl.localhost` 與 `\\wsl$` 別名被停用），2′ 的差異化收益
（at-rest 不落 vhdx＋關機即清）回復，決策 2 應重評——屆時的比較基礎是「重跑解密儀式的
日常代價 vs 恢復的 at-rest 收益」。

## 附屬規則：SSH identity 禁令與尋鑰來源

**禁令**：①**禁止以 SSH 金鑰充當 SOPS identity**；②**切換取鑰來源後必須緊接 #10 反向驗證**
（把預期不生效的來源移走／`unset` 後解密**必須失敗**；仍解得開＝切換未生效）。

技術根據（sops 原始碼核實，research R10）：`loadIdentities` 是**聯集載入、非 first-match**，
依序收集五類來源——SSH（`SOPS_AGE_SSH_PRIVATE_KEY_FILE`／`_CMD`／**零設定自動探測
`~/.ssh/id_ed25519` 與 `~/.ssh/id_rsa`**）→ `SOPS_AGE_KEY` → `SOPS_AGE_KEY_FILE` →
`SOPS_AGE_KEY_CMD` → 預設 `~/.config/sops/age/keys.txt`。兩個後果：**聯集語意**使「切換來源」
後舊來源仍可能默默生效（故 #10 不可省）；**SSH 預設探測**使爆炸半徑意外綁上 SSH 私鑰。

**禁令的必要性不因現況而降低**：現場旁證顯示本機 `~/.ssh` 無那兩個預設探測檔名、且 wrapper
不掛載 `~/.ssh`＝容器內結構性構不到 SSH 來源（tasks T033 ⑤）。但禁令護的是**日後為了省事把
SSH 金鑰接上去**的那個動作——一旦接上，同一把私鑰同時是 git 遠端存取憑證與機密解密的根信物，
任一面洩漏即兩面同時失守。此禁令同時封死 ADR 0083 所列問題 B 反轉條件④。

## 附屬規則：passphrase 政策與離線備份義務

- **強度**：diceware **≥6 詞**（或等強度）。理由＝#11 事實下 identity 檔可能被讀走，此時唯一
  防線是 passphrase 的**離線**暴力破解成本；age 的 scrypt 加殼提供 work factor，但 work
  factor 不能替代熵。
- **離線備份義務含 passphrase 本身**：B′ 的根信物是腦中的 passphrase——遺失即該 identity
  永久失效（走加人流程重加入）；若它是**唯一** recipient，版控內密文即永久不可解
  （RUNBOOK §15.5）。故備份對象＝**identity 檔 ＋ passphrase 本身**，且兩者不得存放於同一處
  （放同一處＝把加殼的意義歸零）。
- **紅線**：**不得以 `SOPS_AGE_KEY` 環境變數注入私鑰值**（brainstorm 拍板）——環境變數會
  出現在 process 環境、容器 inspect、shell 歷史與 CI log，等同把根信物散佈到不可控面。
- **產鑰是一次性人工儀式**：`age -p` 的 passphrase 一律經 `/dev/tty` 讀取、官方無
  passphrase-from-file 旗標＝**結構上不可無頭自動化**。施工期以拋棄式 passphrase 的暫代鑰
  代行（決策 5 之 C 案）、收刀期由 user 親產真鑰。

## 三閘實測欄

### 閘 #2 容器 bind-mount ext4／tmpfs（2026-07-29、T004）——全過

- **怎麼跑**：於 `$HOME/.cache` 下 ext4 測試目錄與 `/dev/shm` 下 0700 測試目錄各放測試檔，
  以 alpine:3.23.3（--rm）bind-mount 起容器，`docker inspect --format '{{json .Mounts}}'`
  判讀 Source＋容器內 cat 驗內容；併驗 UID／權限矩陣（600／644、檔案級與目錄級掛載、
  UID 472／59000）。
- **實測輸出重點**：兩落點 inspect Mounts Source 逐字正確、容器內讀到同值；uid:gid 1000:1000
  原樣呈現＝真 POSIX；600 檔擋非 owner UID（472／59000 Permission denied）；644 檔之檔案級
  bind-mount（＝compose secrets 實形）UID 472／59000 皆讀取成功；掛整個 700 目錄時非 root
  UID 無法穿越。
- **結論**：過——bind-mount 方案形狀成立。
- **對設計的影響**：「dir 700＋file 644＋逐檔掛載」既定設計正確自洽；解法 1（環境變數注入）
  重拍路徑無需啟動。

### 閘 #11 Windows 側 docker client 定址 WSL 內部路徑（2026-07-29、T005）——反轉→重拍

- **怎麼跑**：環境＝distro Ubuntu-24.04、Docker Desktop 引擎 29.6.2、docker.exe 同引擎。
  自 Windows 側以 docker.exe 分別用 UNC 形（`\\wsl.localhost\Ubuntu-24.04\...`）與純 Linux
  路徑字串（`/dev/shm/...`／`/home/...`）掛載 WSL 內部 tmpfs／ext4 路徑起容器，
  `docker inspect` Mounts 判讀＋容器內驗內容；併以 `powershell.exe Get-Content` 與
  `cmd.exe type` 經 `\\wsl.localhost`（及舊別名 `\\wsl$`）直讀 WSL 內 600 權限明文測試檔。
- **實測輸出重點**：①docker.exe UNC 形可定址 WSL 內部 tmpfs 起容器且 Mounts 成立、容器內
  讀到明文（600 被容器 root 無視）；②`/dev/shm` 之 600 明文被 powershell／cmd 經 UNC 逐字
  讀成功；③對照組：純 Linux 路徑字串掛載＝Mounts JSON 與 WSL 側完全同形但容器內是別
  namespace 的空目錄（證「只看 inspect Mounts 不可判定定址成立、必須驗內容」）；
  ④對稱性：ext4（`$HOME`）路徑經 UNC 讀取同樣成功＝live 通道對 2 與 2′ 暴露相同。
- **結論**：反轉——「tmpfs 使 Windows 側構不到明文」前提不成立，2 vs 2′ 比較基礎改變，
  依預拍升級 user 重裁。
- **對設計的影響**：user 重拍三點定案（見「決策」節）——SECRETS_DIR 改解法 2、私鑰維持 B′、
  退路僅退方式 A；T024 `.env` 定值與 T031 開機儀式段（改常駐語意）連帶改。

### 閘 #3 B′ passphrase identity 可用性（2026-07-29、T007）——全過→B′ 定案

- **怎麼跑**：全程 pty 驅動（python pty、零人工）、閘用檔案限 `$HOME/.cache/rev4-019-tmp/
  gate3/`（identity 拋棄式、驗畢即刪、未碰 `~/.config/sops/age/`）。
  `age-keygen | age -p`（age v1.3.1、T040 依 release API digest 現查值驗訖）產 passphrase
  加殼 identity → `xxd` 驗形制 → sops 官方容器（digest 釘版 `ghcr.io/getsops/sops@sha256:
  ae501277…140ea`、ad-hoc docker run、不建 wrapper）以 `--age` 公鑰加密最小測試檔（不用
  `.sops.yaml`、避循環依賴）→ 另開新 pty session（容器 env 乾淨）帶 `SOPS_AGE_KEY_FILE`
  （唯讀掛載）解密兩次＋錯誤 passphrase 反證一次。
- **實測輸出重點**：identity 371 bytes、開頭 `age-encryption.org/v1`＋binary scrypt 段、
  尾端無 CR（末 byte 0x64）；加密產物 key 名明文、值 `ENC[`；第一次解密跳提示
  `Enter passphrase for identity 'SOPS_AGE_KEY_FILE':`、輸入後逐字還原 rc=0；第二次解密
  仍跳提示＝無 keyring／gpg-agent 快取假象（容器內無 gpg-agent、必回退終端互動＝R8 預期）；
  錯誤 passphrase 反證 rc=128、零明文、報 `Recovery failed because no master key…`＝提示為
  真實守門非裝飾。**單 recipient 提示次數基線＝每次 `sops -d` 恰 1 次**（多 recipient 值由
  T033 雙金鑰在場時實測、RUNBOOK 不寫死）。
- **結論**：過——B′ 定案、預拍退路未動用。
- **對設計的影響**：T019 依 B′ 形制產暫代正式鑰（儀式走決策 5 之 C 案）；wrapper（T018）
  `-it` 條件化與 tty 守衛（T022）的技術根據獲實證；pinentry 前置（T006）已落 conf、
  `GPG_TTY` 屬 session 變數由 RUNBOOK（T031）承載。

## 後果

### 殘餘風險總表（誠實登記——記載的是「還沒被消滅的」，不是「已經解決的」）

| # | 殘餘風險 | 為何仍在 | 補償控制 | 判定 |
|---|---|---|---|---|
| 1 | **明文長駐 `ext4.vhdx`（at-rest）** | 解法 2 的定義性代價：明文寫在持久檔系統上，關機不清 | ①私鑰 B′＝根信物不隨檔案被讀走②三層掃描防線擋入庫面（ADR 0082）③RUNBOOK §4 人工清單之 BitLocker／`.wslconfig` swap 確認項 | 有意識接受（user 重拍理由①） |
| 2 | **Windows 側經 UNC 可讀 WSL 內任何檔案（live 通道）** | Docker Desktop／WSL 的既有互通設計；`\\wsl.localhost` 與舊別名 `\\wsl$` 皆可達，600 權限對 Windows 側無效 | 同 #1 之①②；此通道對解法 2 與 2′ **暴露相同**（閘 #11 實測④）——換落點消不掉它 | 有意識接受；再反轉條件見「自洽論證」節 |
| 3 | **明文暫存與捕捉檔的落點** | 解密管線與合併衝突程序都會產生完整明文的中間檔 | 落點強制 `${XDG_CACHE_HOME:-$HOME/.cache}` 之 0700 目錄＋**fs／mode 斷言早於 `sops` 呼叫**（不合格＝零明文產生）；contracts §P4、RUNBOOK §15.7 | 已消滅 repo 內落點；殘餘＝同 #1（仍在 ext4） |
| 4 | **暫代正式鑰的 passphrase 視同已洩露** | 施工期由 agent 以拋棄式 passphrase 產鑰（決策 5 之 C 案），該值存在於對話紀錄 | 無技術補償——**唯一出路是收刀期的真鑰產製＋撤銷四步＋7 支 leaf 輪替**（決策 5 之硬性義務） | **019 未完成該義務前，版控內密文的實質保護等同無** |
| 5 | **磁碟加密與 swap 面無機器驗收** | BitLocker 狀態與 `.wslconfig` 的 `swap` 設定屬 Windows 側人工確認、無 repo 內可跑的判準 | RUNBOOK §4 人工必填清單第 6 項（`manage-bde -status`／`.wslconfig`） | 誠實登記為人工項、不偽裝成驗收 |
| 6 | **日常摩擦：每次解密輸一次 passphrase** | B′ 的定義性代價（單 recipient 基線＝每次 `sops -d` 恰 1 次；多 recipient 時次數＝該 identity 之 stanza 順位） | 落點持久＝解密頻率低（只在落點缺檔時跑，非每次開機）；提示次數實測表＝RUNBOOK §15.9 | 已拍代價 |

**★ 隨 2′ 作廢而不得寫回的登記**：`/dev/shm` 的 tmpfs swap 殘餘風險、以及「重開機即清空」
所蘊含的一切保護主張——2′ 未被採用，把它的風險或收益寫進本 ADR 都是失真。

### 其他後果

- **免開機儀式**：`wsl --shutdown` 後明文仍在、compose 直接可起。RUNBOOK 的「開機儀式」段
  已改寫為**常駐語意**＋「落點缺檔時的補救步驟」（§15.6）；US3 驗收情境 5 的觸發條件亦
  隨之由「重開機」改為「落點缺檔」——**反轉後照原文驗收只會得到假綠**（原委見 L-162）。
- **這個反向性質不升格為驗收項**：驗證它需要真的 `wsl --shutdown`（破壞性、屬人工一次性
  確認），升格只會製造無對應 task 的孤兒驗收。
- **落點成為跨消費者的單一事實來源**：`SECRETS_DIR` 由 repo 根 `.env` 承載，消費者聯集
  七處（唯一權威清單＝`contracts/secret-pipeline.md` §P5.1）——**漏列任一支即該處靜默失效
  且全綠**（實證與防法＝L-174／L-175／L-177／L-178）。
- **私鑰目錄不隨 repo 移動**：identity 落 `~/.config/sops/age/keys.txt`（目錄 700、檔 600），
  與 repo 生命週期解耦；換機＝走加人四步（RUNBOOK §15.2），不搬私鑰檔。
