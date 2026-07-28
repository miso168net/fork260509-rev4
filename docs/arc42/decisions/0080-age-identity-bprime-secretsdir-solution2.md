---
id: "0080"
title: 私鑰 B′（passphrase 加殼 identity）× SECRETS_DIR 解法 2（$HOME/.cache/rev4-secrets）——三實測閘定案與 #11 反轉後重拍
date: 2026-07-29
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 019-secrets-sops brainstorm §3（user 親決私鑰 B′ 傾向＋SECRETS_DIR 2′）／§9 ADR-B 綱要＋research R7／R8／R9／R14＋spec FR-009~FR-012＋tasks T004／T005／T007 三閘實測（2026-07-28~29）＋user 重拍三點定案（2026-07-29、#11 反轉後）＋T019 儀式拍板 C 案（2026-07-28、T002 併問）"
tags: [security, secrets, sops, age, deployment]
---

> **draft 狀態說明**：本檔於 `specs/019-secrets-sops/tasks.md` Phase 2（Foundational 三實測閘）
> 結清時立骨架與實測欄；正文完稿（自洽論證全文、SSH identity 禁令、passphrase 政策 diceware≥6
> 與離線備份義務、tmpfs／ext4 殘餘風險誠實登記之總表化）歸同檔 **T034（Phase 7 US5 治理）**，
> 收刀時轉 accepted。

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

**user 重拍三點定案與理由（2026-07-29、#11 反轉後）**：

- ①SECRETS_DIR＝解法 2：#11 實證 live 通道（Windows 側經 UNC 讀取）對 2 與 2′ 暴露相同，
  2′ 的差異化收益收窄至 at-rest（不落 vhdx）與關機即清，換不回每次開機重跑解密儀式的代價；
  解法 2 的 at-rest 代價＝明文長駐 `ext4.vhdx`——誠實登記、不偽稱有保護。
- ②私鑰維持 B′：#11 事實下（Windows 側可讀走 WSL 內任何檔案）B′ 是唯一不怕「檔案被讀走」
  的 at-rest 信物——讀走的是密文、根信物在腦中；且 identity 保護的是**跨 git 歷史與未來輪替
  的根信物**，與「現值明文暴露面」正交（現值另由落點與掃描防線承載）。
- ③退路連帶調整：SECRETS_DIR 既已定在 2，退路只剩私鑰維度＝僅退方式 A。

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
- **對設計的影響**：T019 依 B′ 形制產正式鑰；wrapper（T018）`-it` 條件化與 tty 守衛（T022）
  的技術根據獲實證；pinentry 前置（T006）已落 conf、`GPG_TTY` 屬 session 變數由 RUNBOOK
  （T031）承載。

## 儀式拍板引用（C 案、2026-07-28 T002 併問）

正式鑰產製走 **C 案**（tasks T019 註記為權威）：agent 以拋棄式 passphrase 產「暫代正式鑰」
（B′ 形制、機制全走、pty 驅動互動）全自動施工；收刀 finishing 時 user 親產真鑰走加人四步＋
對暫代鑰撤銷四步（含 7 支 leaf 值輪替；`alert_webhook_url` 不動、保 SC-007）；暫代鑰
passphrase 留於對話紀錄＝**視同已洩露**、於此誠實登記。

## 後果

- 明文長駐 `ext4.vhdx`（解法 2 的 at-rest 代價）＝有意識接受並誠實登記；補償面＝①私鑰 B′
  使根信物不隨檔案讀走②三層掃描防線擋入庫面③RUNBOOK §4 人工清單之 BitLocker 確認項。
- 免開機儀式：`wsl --shutdown` 後明文仍在、compose 直接可起；RUNBOOK 開機儀式段改寫為
  常駐語意（T031）。
- `/dev/shm` 相關的 swap 殘餘風險登記隨 2′ 作廢；改登記 ext4 at-rest 面（T034 完稿總表化）。
- （其餘後果隨 T034 完稿補齊。）
