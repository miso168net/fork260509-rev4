---
id: "0079"
title: 機密管理選型＝SOPS＋age——零維運硬約束下的公鑰信封模型，官方容器 digest 釘版、cosign 不啟用
date: 2026-07-30
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 019-secrets-sops brainstorm §3（user 親決全量一刀＋選型前提）與 §9 ADR-A 綱要／research R1（掃描器資產命名）R7（sops 版本與 digest）R9（age 取得與完整性驗證校正）R11（wrapper 形制）／spec FR-001·FR-010·FR-011／tasks T002（三支外部工具釘版雙查、user 親決）T018（wrapper）T040（age 取得與 digest 驗訖）"
tags: [security, secrets, sops, age, supply-chain, deployment]
---

## 背景

019 之前，rev4 的機密管理只有**結構面**防線：11 支明文 `.txt` 落在 repo 內 `deploy/secrets/`
（/mnt/d＝9p，`chmod` 結構性 no-op、權限顯示恆 777），靠 `.gitignore` 擋入庫。三個後果：
①機密值完全不可版控，加人／換機只能人對人傳明文；②任何一次 `git add -A` 的失手就是不可逆
洩漏（gitignore 是唯一那道門）；③備份、輪替、撤銷都沒有可依循的機器程序。

選型的**硬約束是「零維運」**——本 repo 是單人 dev workspace、既有閘點只有 pre-commit 與
`tools/bootstrap`，不接受為了管機密而多養一個常駐服務（部署、升級、備份、憑證、故障處置的
成本會超過被保護資產的價值）。這條約束先把 Vault／Infisical／OpenBao 等 server 類方案整批
排除，剩下的真競爭者只有兩個：SOPS+age 與 dotenvx。

## 決策

### 1. 採 SOPS + age 作為機密加密與版控機制

四個理由（依對本專案的權重排序）：

- **公鑰模型使「加人」零機密傳遞**：新成員只交出 age 公鑰（非機密、可貼在任何地方），既有
  持鑰者跑一次 `updatekeys` 即可；全程沒有任何一刻需要把明文機密或私鑰交給對方。這是本刀
  最核心的收益——舊模型下「加一個人」等同「把 11 支明文複製一份給他」。
- **`.sops.yaml` 的 path→recipients 對應進版控、可 review**：誰能解開哪個檔案是一份 diff
  看得見的宣告，而不是散落在某台機器上的設定或某人腦中的默契。
- **值層加密使 `git diff` 仍可讀**：key 名保持明文、只有值成 `ENC[...]`，於是「這次改了哪支
  機密」在 review 面是可見的；整檔加密方案（含 `.env.enc` 形）會讓每次改動都退化成一坨
  無意義的二進位 diff。
- **`updatekeys`／`rotate` 給出清楚的撤銷語意**：撤銷＝移除 recipient ＋ `rotate -i --rm-age`
  換 data key，兩者的語意差異與陷阱可被寫成可實測的程序（RUNBOOK §15.3、實測見 tasks T033）。

### 2. 誠實收窄：對唯一真競爭者 dotenvx，實際只贏兩項

上列四理由中，**「值層加密／diff 可讀」與「撤銷語意」dotenvx 同樣具備**。逐項比對後
SOPS+age 真正的差異化優勢只有兩條：**多 recipient**（dotenvx 每檔單一公鑰）與**宣告式
per-path 對應**（`.sops.yaml` 一份設定管住多個路徑的 recipients 清單）。

這兩條足以支撐本專案的選擇，因為本專案的核心需求正是 **dev／prod 分層**（將來 prod 檔要有
≥2 個 recipient 且不含開發機）。但必須誠實記載：**論證只有一條腿**——若日後 prod 分層需求
消失、或退回單人單機，這個選型的差異化理由會同時消失，屆時 dotenvx 是合法的重評對象。
不假裝有四條腿。

### 3. 零維運＝硬約束，落選方案與理由

- **Vault／Infisical／OpenBao（server 類）**：功能完備但需常駐服務＋自身的高可用、備份、
  unseal／根憑證管理。對單人 dev workspace 而言，維運機密管理系統的風險高於它消滅的風險。
- **雲端 KMS（AWS KMS／GCP KMS／Azure Key Vault）**：sops 原生支援，但引入雲端帳號依賴與
  離線不可用面；且本專案目前無雲端 footprint，為機密而開帳號是反向的複雜度輸入。
- **git-crypt**：整檔加密（diff 不可讀）、金鑰輪替與撤銷語意薄弱。
- **手動 GPG**：撤銷與加人皆為人工程序、無宣告式對應、pinentry 面的坑更多。

### 4. sops 以官方容器 digest 釘版、經 wrapper 提供；host 不裝 sops 二進位

`deploy/sops.sh` 釘死
`ghcr.io/getsops/sops@sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`
（＝v3.13.3-alpine 的 multi-arch index digest；版本與 digest 由 user 於 tasks T002 親決、
施工時對 ghcr 逐字複核相符）。三點紀律：

- **registry 與 digest 必須成對**：quay 為獨立推送，同 tag 的 digest 不必然與 ghcr 相同；
  換 registry 就必須重取 digest。
- **選 alpine 變體**：不含雲端 CLI 相依、攻擊面較小；本專案純 age 流程不需 KMS。
- **wrapper 形制**（要件全文＝`contracts/secret-pipeline.md` §P1）：互動旗標條件化（有 tty
  才配 `-i -t`，無 tty 時吵鬧失敗而非 hang）／不轉發 host `EDITOR`（映像內建 vim）／顯式
  轉發 `SOPS_AGE_KEY`、`SOPS_AGE_KEY_FILE`、`SOPS_AGE_KEY_CMD` 三個變數（未列出者被 docker
  靜默丟棄）／掛載 `$PWD:/work -w /work` 與私鑰目錄唯讀。

**為何走容器而非 host 二進位**：與既有慣例同構（`generate-secrets.sh` 早已以
`docker run --rm alpine/openssl` 產亂數、host 零 openssl 依賴），且 digest 釘版比「host 上
某次 apt／brew 裝了什麼版本」可稽核得多。**代價＝解密唯一依賴 docker**——離線／無 docker
的災難還原路徑僅止於 RUNBOOK §15.10 的備註，未經實測（見決策 6 與「後果」）。

**root 產物對策＝B（host shell 收 stdout ＋ `umask 077`）**：官方映像無 `USER` 指令、以 root
執行，若讓容器直接產出明文檔會得到 `root:root` 產物，使既有腳本的 `chmod` 在
`set -euo pipefail` 下中止。落選對策 A（`--user` 對映）＝會讓容器內 `HOME` 不再是 `/root`、
私鑰預設掛載點失效，複雜度更高。

### 5. cosign **不啟用**——誠實登記，不假裝有驗簽

sops 與 Betterleaks 的官方 release **確實有 cosign 簽章**，但本刀**不裝 cosign、不做驗簽**：

- 供應鏈防線實際止於**映像 digest 釘版**（容器面）與 **`sha256sum` 逐檔比對**（二進位面）。
- 不啟用之因：Betterleaks release 的 `cosign verify-blob` 所需 `certificate-identity` 值官方
  未公布，需下載 bundle 實測才能寫死；為一次性驗簽引入額外工具鏈與未定參數，成本高於收益。
- **誠實登記**：本專案的供應鏈保證是「取得當下的內容完整性」，**不是「來源身分經簽章驗證」**。
  digest／sha256 能保證「我拿到的與我當初核對過的是同一份」，不能保證「這份是官方發的」——
  首次取得那一刻的信任仍押在 HTTPS 與官方 URL 上。啟用 cosign 屬後續可選硬化，不列本刀範圍。

### 6. age 取得路徑：官方 GitHub release 二進位 ＋ release API `digest` 欄位現查比對

- **age 沒有 `checksums.txt` 類檔案**（每資產改配 Sigsum `.proof`，需 sigsum 工具鏈）——
  故完整性驗證改取該版本 **GitHub release API 的 `digest` 欄位現查值**比對 `sha256sum`。
  ★**比對基準必須現查、不得沿用研究當日記載值**：版本一變即作廢（實際執行時 T040 現查值恰
  與 research R9 當日值相同，屬巧合非依據）。
- **落選**：alpine 容器 `apk add age`（執行期解析版本＝未釘版）／`apt`（發行版版本最舊）／
  第三方 age 映像（**紅線排除**——私鑰生成工具不採無官方背書的映像）。
- **用完即刪**：age 二進位僅為施工期產鑰／演練所需，**不常駐**；清理時點統一為收刀終驗
  （tasks T038），施工期間由 T007／T019／T033 共用同一份暫存（時點勘誤原委見 tasks T040）。

## 後果

- **解密鏈依賴 docker**：`deploy/sops.sh` 是唯一的 sops 取用路徑，docker 不可用即解不開。
  代償＝RUNBOOK §15.10 災復備註（明載該路徑未經實測＝brainstorm 驗收字母 g 不升格的登記形）。
- **升級 sops／age 是一次拍板動作**：digest 與版本皆為 tracked 常數，升級必然產生 diff、
  必然經過 review，不會靜默漂移；代價是升級需人工複查 digest 與 registry 成對性。
- **供應鏈殘餘風險**：無簽章驗證（決策 5）；首次取得的信任錨＝官方 URL＋HTTPS。
- **選型論證的脆弱面**（決策 2）：差異化優勢押在 prod 分層需求上；prod 分層本刀不做、
  遞延 BACKLOG B-115——即在 B-115 兌現之前，本選型的兩條差異化優勢都尚未被實際使用。
  這是有意識接受的順序（先把可版控與掃描防線做出來），不是被忽略的矛盾。
- 加密資產的形狀（單檔 8 key／prod 不建／命名紅線／不設範圍選項）＝ADR 0081；私鑰存放與
  明文落點＝ADR 0080；掃描防線三層定位＝ADR 0082。
