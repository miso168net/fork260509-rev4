---
id: "0081"
title: 加密資產形狀——dev 單檔 8 key、prod 不建（目標形狀備忘）、ca.key 不進 SOPS、命名紅線與不設範圍選項
date: 2026-07-30
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 019-secrets-sops brainstorm §3（user 親決 prod 不建／切檔粒度／ca.key 不進）與 §4（檔名紅線、不設 encrypted_regex）與 §9 ADR-C 綱要／research R12（.sops.yaml 語法與六個範圍選項互斥）／spec FR-013·FR-014·FR-015／contracts secret-pipeline §P2·§P3／tasks T020（.sops.yaml 四自檢實測）T021（加密檔首建）"
tags: [security, secrets, sops, age, naming]
---

## 背景

決定「用 SOPS+age」（ADR 0079）之後，仍有一組彼此獨立的形狀問題必須各自拍板：**加密幾個檔、
每檔裝什麼、檔名怎麼取、加密範圍怎麼圈**。這些選擇的共同性質是——**選錯的後果都不是報錯，
而是靜默地少加密了東西**：檔名副檔名順序寫錯會退化成整檔加密、範圍選項設成白名單會讓新增
欄位靜默留明文、key 名撞上保留後綴會讓該值明文躺在版控裡。故單獨立 ADR 把紅線寫死。

## 決策

### 1. dev 一檔 8 key：`deploy/secrets.dev.enc.yaml`

- **口徑＝7 leaf ＋ `alert_webhook_url`**（機密清單的四口徑：11 檔／10 進 compose／**8 入
  加密檔**／13 含 dev TLS 私鑰——引用時必言明是哪一個）。
- **3 支 composite 不進加密檔**（`database_url`／`redis_url`／`reaper_database_url`）：它們是
  由 leaf 組出的連線字串，由 `deploy/generate-secrets.sh --compose-only` 重生。理由＝進了
  加密檔就變成同一份密碼的第二個真相來源，輪替時必然漂移；不進則 byte-identical 不變式由
  單一腳本保證（`contracts/secret-pipeline.md` §P5.7）。
- **`alert_webhook_url` 如實搬移現值、不可重生**：該值是 user 已填的真值（39 bytes），
  亂數重生會直接毀掉它。守衛＝解密時現值與解密值不同即另存 `.txt.new` **不覆寫**（§P4.5）；
  `--force` 亦不重置此檔。**測試絕不以刪該檔為手段**。
- **切檔粒度＝dev 一檔**。**重評條件**：①成員數 >1 且需要「層內分權」（例如某人只該解得開
  一部分機密）②出現與 dev 生命週期不同的機密群（如第三方 API 憑證需獨立輪替節奏）。
  **粒度的本質是權限粒度**——SOPS 的 data key 是**每檔一把**，同檔內所有 key 對所有 recipient
  一視同仁；要分權只能切檔，不能在檔內分。

### 2. prod 加密檔**不建**——但目標形狀立即備忘

本刀**不建** `deploy/secrets.prod.enc.yaml`：目前無 prod 環境、無 prod 機密實值，建了就是
一個裝著假值的檔案，而假值檔會製造「prod 機密已納管」的錯覺。

**目標形狀備忘**（B-115 兌現時照此起手，不重新設計）：

- 檔名 `deploy/secrets.prod.enc.yaml`，`.sops.yaml` 增第二條 `creation_rules`（**錨定式
  `path_regex`**，與 dev 條互斥）。
- **recipients ≥ 2**（避免單點金鑰遺失＝prod 密文永久不可解），且**不含開發機（company_pc）
  的公鑰**——這正是遞延驗收 #5「company_pc 解不開 prod」的結構前提。
- **託管 DB 情境下 `database_url` 升格為 primary secret 入 SOPS**：託管 DB 的連線字串不再由
  本地 leaf 組出（帳密由供應商給），composite 重生模型不適用。
- CI 側金鑰保護（GitHub Environments／OIDC）＝遞延驗收 #6 的落點。
- 以上全數掛 **BACKLOG B-115**（prod 機密分層遞延包），與 prod 部署刀群同期。

### 3. `ca.key`（dev TLS 私鑰）**不進 SOPS**

- 理由＝**可重生**：dev TLS 憑證由 `deploy/dev-certs/` 的生成流程重建，無不可重生的價值；
  進 SOPS 只是把「可丟棄的東西」升格成「要管理的東西」。
- **重評條件**：①多人協作且每人重建 CA 導致信任鏈反覆失效②CDP／瀏覽器信任鏈重建成為實際
  痛點（每次重建都要重新匯入信任）。任一成立即重評——屆時的問題不是「能不能加密」，
  而是「值不值得為它多一個要輪替的資產」。

### 4. 命名紅線（兩條，違反皆為靜默失效）

- **檔名紅線：格式副檔名必須放最後**——`secrets.dev.enc.yaml`（✓）而非 `secrets.env.enc`（✗）。
  sops 以副檔名判 store：認不出即退化為 **binary store ＝整檔單一密文塊**，key 名不可見、
  `git diff` 完全不可讀，而**加密本身仍會成功**（不報錯）。已實測：以 `secrets.env.enc` 加密
  得到單一 `data: ENC[` 塊（tasks T023 ⑤）。
- **key 命名紅線：禁 `_unencrypted` 後綴**——見決策 5，該後綴是 sops 預設的**明文豁免**後綴，
  命名撞上即該值明文躺在版控裡。

### 5. **不設**六個範圍選項任一

sops 的六個範圍選項（`encrypted_suffix`／`unencrypted_suffix`／`encrypted_regex`／
`unencrypted_regex`／`encrypted_comment_regex`／`unencrypted_comment_regex`）**互斥**，同時設
兩個以上即報錯；**全不設時預設套用 `unencrypted_suffix = "_unencrypted"`**＝**全加密**、
僅該後綴的 key 留明文。

- **不設 `encrypted_regex` 的理由**：它是**白名單**語意——只有匹配的 key 被加密，日後新增
  的欄位**靜默留明文**。加密範圍的預設方向必須是「全加密＋列舉例外」，不能是「列舉要加密的」。
- **代價**：全加密使 sops metadata 以外的一切皆為密文，包含本來不敏感的欄位；本專案 8 key
  全為機密，此代價為零。
- 連帶紀律＝決策 4 的 `_unencrypted` 命名禁令（預設豁免後綴必須被禁用，否則白名單語意從
  後門回來）。

### 6. `.sops.yaml` 四自檢（寫完即驗，不靠事後發現）

| # | 自檢 | 失效樣態 |
|---|---|---|
| 1 | `path_regex` **錨定式**（`^…$`） | sops 用 `MatchString`＝**非錨定子字串**比對，未錨定則 `xsecrets.dev.enc.yaml.bak` 之類也命中 |
| 2 | **僅一條** `creation_rules` | 多條時只有**第一條匹配者**生效，第二條被靜默忽略 |
| 3 | **寫完立刻驗規則確實命中**目標檔 | 規則寫錯不會報錯、只會在加密時說「no matching creation rules」或落到別條規則 |
| 4 | **不設** `encrypted_regex`（＝決策 5） | 白名單語意、新欄位靜默不加密 |

實測落地＝tasks T020：命中驗證以 `--filename-override` 不帶 `--age` 加密成功且 metadata
recipient 逐字等於正式公鑰（**規則供鑰自證**）；錨定否定探針三案（前綴 `x`／後綴 `.bak`／
點未跳脫形）全數 `rc=1 no matching creation rules found`。

## 後果

- **加密檔的 `git diff` 是可 review 的**：key 名明文 8 支、值全 `ENC[AES256_GCM…`（實測
  `grep -cE '^[a-z_]+: ENC\['`＝8）。這使「這次動了哪支機密」在 review 面可見。
- **撤銷演練必然產生加密檔 diff**：`rotate` 換 data key ＝ 8 值密文全變，**該 diff 是預期
  產物、要 commit**；「復原」指的是 recipient 清單與可解性，不是 byte 級還原。
- **權限粒度＝檔案，不是 secret**：同檔 8 key 對所有 recipient 一視同仁；這是決策 1 重評
  條件的技術根據，也是 prod 必須另立檔（決策 2）而非「在 dev 檔裡多加幾個 key」的原因。
- **prod 機密的實質保護目前為零**（決策 2 的直接後果）——本刀交付的是 dev 面納管與可重複的
  程序骨架；prod 面在 B-115 兌現前**不得宣稱已納管**。
- **遞延驗收 #5／#6 結構性不可測**：`company_pc 解不開 prod` 與 `CI 取不到金鑰` 都需要 prod
  資產與 CI 存在才有驗收母體，本刀無此母體——登記 B-115，不做「假裝驗過」的替代測試。
