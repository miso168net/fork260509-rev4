---
id: "0082"
title: 機密洩漏三層掃描防線定位——事件型廣譜 × 狀態型窄樣式 × 值比對確定性互補並存、三 repo 覆蓋
date: 2026-07-30
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 019-secrets-sops brainstorm §1（接地盤點：兩源倉零防線、近 90 天約 1/3 提交構不到掃描）與 §3（user 親決掃描器＝Betterleaks）與 §9 ADR-D 綱要／spec Clarifications 兩問（值比對與 pre-push 的 repo 覆蓋範圍）／research R1·R2·R5·R16·R17／spec FR-002~FR-008·FR-018／contracts scan-gates §S1~§S6／tasks T009~T017 實測"
tags: [security, secrets, pre-commit, pre-push, governance, submodule]
---

## 背景

018 已落地 docs-sync 的 L16 (Lint16) 憑證內容掃描（ADR 0077）——那是一道**窄樣式、高確信**的閘，
有意識接受漏報面。019 要導入 SOPS 之前，先要面對三個 018 未覆蓋的缺口：

1. **樣式射程**：L16 (Lint16) 只認四類（PEM 私鑰／AWS access key／GitHub token／GitHub PAT），
   資料庫連線字串（DSN）與泛 `KEY=value` 形完全不在射程內。
2. **repo 覆蓋**：L16 (Lint16) 掛在外層 pre-commit；兩個 submodule 源倉（base-web／rust-api）
   `core.hooksPath` **皆未設**＝生效 hooks 只有 `.sample`＝零防線。近 90 天提交占比
   外層 483／rust-api 160／base-web 75——**約 1/3 的提交構不到任何掃描**。
3. **本 repo 自己的機密現值**：`deploy/secrets/*.txt` 的實值是**高熵裸字串**，任何樣式規則
   都不該、也不可能認得它——把它貼進某份文件裡 commit，兩層樣式閘都會放行。

同時導入 SOPS 本身也帶來一個新的誤報面：加密檔的 `ENC[...]` 值是高熵字串，若掃描器把它當
機密就會讓整套流程無法運作。

## 決策

### 1. 三層互補並存，各自定位不同、不合併不取代

| 層 | 實作 | 類型 | 射程 | 已知盲區 |
|---|---|---|---|---|
| 樣式廣譜 | Betterleaks（`.gitleaks.toml`，含自訂 DSN 規則） | **事件型** | 已知形制的機密：token 前綴形、`KEY=value`、DSN 連線字串 | 裸高熵值（無形制可認）；未收錄的機密形 |
| 樣式窄集 | docs-sync L16 (Lint16)（018／ADR 0077） | **狀態型** | 四類高確信樣式；**外層 tracked 全量＋staged 面＋pin bump 增量掃 submodule** | 依 ADR 0077 決策 2 有意識接受的漏報面 |
| 值比對 | `tools/secret-value-guard.py` | **確定性** | 本 repo 機密**現值**逐字出現在 staged 內容 | 明文缺席時 skip（fail-open）；僅外層 |

**互補的判準是「哪一格只有它守得住」**（契約＝`contracts/scan-gates.md` §S6）：裸值形樣式
掃描結構性不中（預期行為），只有值比對能擋；DSN 形與 `KEY=value` 形值比對不涉及（那些是
外來機密、不是本 repo 現值），只有樣式層能擋。**兩層都不是另一層的超集**。

### 2. 事件型與狀態型的語意差異必須被寫進 hook 註解

- **事件型（掃描）**：`--no-verify` 繞過一次，內容就**真的進了 git**——下次 commit 不會再
  掃到它（掃描面是本次 staged 內容），洩漏已不可逆。
- **狀態型（docs-sync check／lint）**：繞過只是**延後**——狀態面下次照樣紅，帳面遲早要平。

這個差異決定了三件事：①掃描行必須置於 docs-sync 檢查**之前**（先擋不可逆的）；②繞過的
代價不對稱，故需要 pre-push 第二層；③`--no-verify` 不能是常態習慣（見決策 5）。

### 3. 三 repo 覆蓋：hook 檔寄宿外層，兩源倉以 `core.hooksPath` 指向

- **hook 檔一律住外層 repo**（`.githooks/`＋源倉專用的 `.githooks-submodule/`），
  由 `tools/bootstrap` **冪等**設定兩源倉的 `core.hooksPath` 指向外層絕對路徑。
- **為何不放進源倉樹**：base-web 倉內新增 hook 目錄不在憲法 §III 任何授權軌道內
  （預設軌道僅 `.env*`／typings／`rev4-*.ts` 新檔）。寄宿外層的覆蓋面相同、**兩源倉樹零
  改動、零 fork-delta 面、零憲法 Amendment 需求**；rust-api 採同形（對稱、單一事實來源）。
- **源倉 hook 只跑毫秒級樣式掃描、零 python 依賴**：不 source 任何 lib（`scan-range.sh`
  只承載 pre-push 的 stdin 解析），且不觸發上游 husky／pnpm 鏈。
- **源倉樹無 `.gitleaks.toml`**＝掃描器自動探索構不到，故兩支源倉 hook 以 `dirname "$0"`
  自我定位後顯式帶 `--config` 指外層設定檔（外層 hooksPath 為絕對路徑，保證 `$0` 絕對）。
- **已知邊界**：`core.hooksPath` 是 **per-machine 設定**——他機 clone 未跑 `bootstrap` 即無
  防線。補償＝bootstrap 體檢對 hooksPath 做**斷言**（不符即 die＋自癒指令）；此邊界誠實
  登記、不假裝已消滅。

### 4. 覆蓋範圍的兩個 clarify 拍板

- **值比對層＝僅外層 repo**：源倉靠樣式層（含 DSN 自訂規則）；理由＝源倉 hook 的「零 python
  依賴、毫秒級」承諾與值比對層互斥，且裸值格驗收只在外層有意義（機密現值屬外層資產）。
- **pre-push 第二層＝三 repo 同套**：hooks 目錄共用、一檔生效三處；掃描範圍＝本次 push 的
  commit 範圍（新分支首推 remote-oid 全零時退階 `--not --remotes=origin`，該退階無效時掃
  整條分支；刪除分支跳過）。第二層價值最高處是 base-web——**`--no-verify` 慣性風險集中處，
  且 push 目標是 GitHub 公開遠端**。

### 5. base-web `--no-verify` 慣例**廢止**

舊慣例＝base-web worktree commit 一律 `--no-verify`（躲上游 husky 觸發 `pnpm install`）。
hook 寄宿外層＋`core.hooksPath` 指向後，**husky 已被結構性旁路**（hooksPath 一設，上游
`.husky/` 就不再生效）——`--no-verify` 的原始理由消失，而它同時會繞過本刀新掛的掃描層。

- 廢止的必要性來自事件型語意（決策 2）：**繞過一次就是真的進 git**。
- 同步落點＝`docs/ops/NOTES.md` 的對應慣例行（repo 文件不引用 per-machine memory 路徑）。
- 回退成本＝零：慣例本身無技術依賴，且 pre-push 第二層仍在。

### 6. 掃描器選型＝Betterleaks，設定檔命名 `.gitleaks.toml`（雙向可攜）

- Betterleaks 由 gitleaks 原作者主導、MIT 授權，定位為 gitleaks 官方後繼；gitleaks 上游已
  逐字宣告 feature complete、只收安全補丁。
- **設定檔命名紀律**：Betterleaks 依序找 `.betterleaks.toml` → **fallback `.gitleaks.toml`**。
  只要設定檔堅持 **gitleaks 子集欄位**（`[[rules]]`／`[[allowlists]]`／`[[rules.allowlists]]`），
  兩支 scanner 可互換；一旦用 Betterleaks 專屬 CEL 欄位即**單向鎖死**。故檔頭註記「僅用
  gitleaks 子集欄位」，反悔可換。
- **原生二進位、禁容器**：容器形式的掃描拿不到 `GIT_INDEX_FILE`，`git commit -a` 路徑會掃到
  0 bytes ＝**靜默漏報**（8 格 fixture 之所以必含 `commit -a` 路徑即為此）。
- **`--redact` 不可省**（預設 0＝命中值明文噴上終端）；**`--exit-code 2`** 使「掃到洩漏」與
  「掃描器自身壞掉」可分流（上游預設兩者同為 1）。
- 禁用 `protect`／`detect` 子命令（已廢棄語意）。

### 7. allowlist 紀律：先寫再啟用、圈定到欄位層級、禁整檔放行

- **硬序 ＝ 誤報基線現場重建 → allowlist 落檔 → 才啟用 hook**。次序顛倒的話，第一個被擋的
  就是自己人的例行簿記 commit（`docs/ops/events.jsonl` 的 40-hex SHA），而那會直接**養成
  `--no-verify` 慣性**、使事件型檢查永久失效。
- **每條 allowlist 必含 `condition = "AND"`**：漏寫即退化為 OR＝過寬放行**且不報錯**——這是
  本 schema 最大的靜默失效點。實證＝拿掉該行後，`specs/*.md` 裡的真值形 DSN 由 `exit 2`
  變成 `exit 0`，復原即回擋。
- **禁整檔放行**：圈定必須是 `paths` × `regexes` 交集＋顯式 `regexTarget`。
- **基線不得沿用舊數字**：誤報基線一律以當時的全歷史掃描現場重建（研究期數字全部過時）。

### 8. 值比對層 **fail-open**（明文缺席時 skip）＝有意識取捨

明文缺席（尚未解密）時該層 skip＋提示、**不 fail-closed**——否則新機／未解密狀態下無法
commit 任何東西。代價＝該層有一條合法的「什麼都沒守」路徑。

**補償紀律**：fail-open 的層級必須有「我這次真的在守」的**正向證據**——收單前以端到端反證
（構造裸值 staged 探針 → 必須 `rc≠0` 且指名檔案:行號＋機密名稱）證明它沒有在恆 skip。
實證與踩坑＝L-174（落點遷移後該層曾結構性恆 skip 卻全綠）。

### 9. compose 向後相容取捨之誠實登記

compose 頂層 10 條 `secrets:` 改帶預設值變數展開（`${SECRETS_DIR:-./deploy/secrets}/…`）
＝未設變數時**回退專案相對路徑**，保住「clone 下來直接 up」的向後相容（驗收 #4）。

**代價＝忘設變數時保護靜默失效**：compose 會掛回 repo 內舊落點（遷移後那裡零 `.txt`，
`up` 甚至會自動建空目錄當 secret 掛入）。

- **「結構性不可能誤設」與「向後相容」不可兼得，本刀取後者**——因為前者的代價是每個新環境
  都必須先讀文件才能起服務。
- **補償控制**：`preflight-secrets.sh` 上機前 fail-loud（指名缺檔／CR／LF／composite 漂移）
  ＋`tools/bootstrap` 代勞產生 `.env` 並讀值斷言。**兩者都不是結構保證、只是可靠的提醒**——
  誠實登記，不宣稱這條路已經封死。
- 落點值本身的三級解析口徑（環境變數→`.env` 嚴格解析單行→回退）與其消費者聯集（七處）
  屬 ADR 0080 射程，唯一權威清單＝`contracts/secret-pipeline.md` §P5.1。

## 後果

- **pre-commit 多兩段成本**：樣式掃描＋值比對；秒級紅線由 SC-009 以 `perf_counter` 分段
  量測把關（**不可用整鏈 `time` 差量**——drvfs 牆鐘變異大於被測成本，L-155）。
- **三層各自的紅綠必須各自可驗**：8 格 fixture（四形 × 兩路徑）＋兩源倉各一實擋＋例行簿記
  零誤擋，缺一即該格未驗收。
- **漏報面仍在**：三層聯集仍不覆蓋「未收錄形制的外來機密且非本 repo 現值」——這是有意識
  接受的殘餘，掃描是**縱深防禦的一層**，不取代 gitignore 結構面、不取代「機密本來就不該進
  repo」的紀律。
- **物件庫殘留是掃描防線看不到的面**：`git add` 過即在 `.git/objects` 留 unreachable blob，
  三層全部看不到（樣式與值比對只看 staged 內容、pre-push 只看 commit 範圍）。以真實機密值
  當 fixture 的驗收，收尾必含 `git prune --expire=now`＋`cat-file -e` 反證（L-158）。
- **兩源倉的防線是 per-machine 的**（決策 3 末）：這是 hook 寄宿外層方案的固有邊界，
  由 bootstrap 斷言暴露，不由 repo 內容保證。
