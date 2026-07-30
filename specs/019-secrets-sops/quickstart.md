# quickstart.md — 019-secrets-sops 驗證劇本（S1~S10 ↔ SC-001~010）

> 用法：每節為一個可獨立執行的機判單元，收刀前全數跑過並記錄實測輸出。**「不做驗收＝沒做」**
> ——本方案失敗模式幾乎全是「指令回報成功但做錯了」，故每節都含否定測試（必須紅的情境）。
> **唯一例外＝「S4 後半」**：其前提是 US3 接線完成，故實際執行序須排在 S6 之後（非節序位置）。
> 前置：`tools/bootstrap` 已跑過（掃描器與 hooksPath 就緒）；U1 三閘已結清並記入 ADR。

---

## S1 8 格 fixture＝四形 × 兩路徑（SC-001）

**做什麼**：以**當場產生的假值**建 4 個 fixture（`KEY=value` 形／DSN 形／裸值形＝取任一機密現值
原文／SOPS 密文形），各以 `git add`+`commit` 與 `git commit -a` 兩條路徑提交。

**期望**（契約＝contracts/scan-gates.md §S6）：

| fixture | 期望 | 攔截層 |
|---|---|---|
| `KEY=value` | 擋 | 樣式 |
| DSN | 擋 | 樣式（自訂 DSN 規則） |
| 裸值 | 擋 | **值比對**（樣式不中屬預期） |
| SOPS 密文 | 放行 | — |

**兩路徑結果必須一致**（`git commit -a` 路徑必測——容器形式的靜默漏報只在此現形）。
**另**：rust-api 與 base-web 各以樣式形 fixture 實擋至少一案。

**收尾**：fixture 假值當場產生、驗完即刪，不入版控。★裸值格必用機密現值原文——`git add`
當下即在外層 `.git/objects` 留下 unreachable loose blob（縱使 commit 被擋）：驗收後**必跑
`git prune --expire=now`**，機判＝`git hash-object` 逐支現值檔算 SHA 後 `git cat-file -e`
全數必須失敗（工作樹收乾淨≠物件庫收乾淨；L-158）。

---

## S2 誤報基線與簿記不誤擋（SC-002）

**做什麼**：①U0 現場重跑全歷史掃描重建誤報基線（**不沿用任何舊數字**，現況 commit 483）；
②寫 allowlist（`condition = AND`＋`paths`×`regexes`，**禁整檔放行**）；③以真實簿記 commit 驗證。

**期望**：`docs/ops/events.jsonl` append 40-hex（`merge`／`pins.web`／`pins.api` 三欄各 18 筆、
合計 54 筆樣態）的 commit **不被誤擋**；`deploy/secrets/*.txt.example` 與
`specs/017-audit-retention/quickstart.md` 的 `curl -u` 示例同樣不誤擋。

**否定測試**：把 allowlist 的 `condition = AND` 改成預設（拿掉該行）→ 應能觀察到放行範圍過寬
（真機密樣本被誤放）→ 復原。此為本 schema 最大靜默失效點的實證。

---

## S3 三 repo 覆蓋與 pre-push 第二層（SC-001 延伸／FR-005／FR-006）

**做什麼**：①`git config core.hooksPath` 逐 repo 讀值，確認外層與兩源倉皆已設定；
②以 `--no-verify` 繞過 pre-commit 造一個含假機密的 commit，然後 `git push --dry-run`
（或推到本地測試 remote）；③三種 push 情境各驗一次：一般更新／新分支首推（remote-oid 全零）／
刪除分支（local-oid 全零）。

**期望**：②被 pre-push 擋下；③新分支首推走 `--not --remotes=origin` 退階路徑、刪除分支被跳過
（不報錯）；base-web 側 commit 不觸發上游 husky／pnpm 鏈（毫秒級完成）。

**收尾**：測試 commit 全數丟棄（`git reset --hard`／刪測試分支），不推真 remote。

---

## S4 加解密往返與加密檔形制（SC-003 前半／#1／FR-014／FR-015）

**做什麼**：①最小加解密往返（#1）；②`git diff` 檢視加密檔；③key 數與名稱斷言；
④確認明文中間產物已刪除且未 staged。

**期望**：①還原值與原值一致；②**key 名明文可讀、每值以 `ENC[` 開頭**（非整檔單一密文塊）；
③恰 8 key（7 leaf＋`alert_webhook_url`）；④`git status` 無明文殘留。

**否定測試**：故意把檔名寫成 `secrets.env.enc` 形加密一次 → 觀察退化為整檔加密（diff 變單行
巨大密文）→ 刪除該實驗檔。

### S4 後半：乾淨重建全鏈（SC-003 後半；驅動 task＝T039）

**做什麼**（需 US3 接線完成後才有意義）：清空 `$SECRETS_DIR` 模擬全新環境 → `tools/bootstrap`
→ `deploy/decrypt-secrets.sh` → `deploy/generate-secrets.sh --compose-only`（重組 3 composite）
→ `deploy/preflight-secrets.sh` → `docker compose up -d`。

**期望**：11 支機密檔全數重建、preflight 全綠、服務全健康；**全程零人工傳遞任何機密值**
（僅憑 repo 內密文＋一把已授權私鑰）。

**否定測試（US3 驗收情境 5）**：清空落點後**不跑解密**直接 preflight → **必須明確紅並指名
缺檔**，而非讓服務靜默啟動失敗。

---

## S5 解密管線五要求與否定測試（SC-004／SC-007／SC-008）

**做什麼**（逐條，每條含否定情境）：

> **命名空間**：下表「驗收項」欄用可讀名稱；括號內為契約編號（`contracts/secret-pipeline.md`
> §P4 的 FR-016 本地代號），**與 spec 的驗收升格字母 a／b／c／d／f／h 屬不同命名空間**
> （對照表見 spec Clarifications）。

| 驗收項 | 正向 | 否定測試（必須紅） |
|---|---|---|
| key 數與名稱斷言（P4.3） | 完整 enc 檔 → 全部寫出 | **刪 enc 檔一個 key** → 零寫入＋非零退出＋指名缺哪個 key（**絕不落到造亂數路徑**） |
| 自填值 `.new` 守衛（P4.5） | 現值＝解密值 → 直接寫入 | 構造 `alert_webhook_url` 差異 → 產生 `.txt.new`＋警示、**原檔不變** |
| 寫檔無尾端換行（P4.1） | `xxd \| tail -1` 尾端**無 `0a` 無 `0d`** | 注入 CR 的檔 → preflight CR 護欄轉紅、修正後復歸 |
| byte-identical 不變式（P4.1） | leaf byte 數與 composite 內嵌值一致 | 手改 leaf 不重跑 → 一致性檢查紅 |
| 產物 owner 與 mode（P4.7＋P1.6） | 目錄 700／檔 644／owner＝本人 uid:gid | 觀察是否出現 `root:root`（P1.6 對策失效的信號） |
| tty 守衛（P4.2） | 互動情境正常 | 非互動呼叫 → **吵鬧失敗**（不得 hang、不得寫出帶 CR 的檔） |
| 落點自建 0700 子目錄（P4.6） | `mkdir -p`＋`chmod 700`＋權限自證（縱深防禦、與落點無關；ADR 0080 決策 4） | 將 `SECRETS_DIR` 指入**權限非 0700 的父目錄**（如 `chmod 755` 暫存父目錄）下跑解密 → `stat -c %a` 子目錄**仍必為 `700`**；驗完刪除暫存父目錄（T023 施工時補列＝契約 §P4.6 所命） |
| 明文暫存落點（FR-021／SC-005；★非 P4 編號＝spec 需求代號） | RAW／CLEAN 落 `${XDG_CACHE_HOME:-$HOME/.cache}` 之 `rev4-decrypt.XXXXXX`（0700）、**不落 repo 內 `tmp/`**（/mnt/d＝9p、`chmod` no-op＝實效 777、Windows 側可見），離場 trap 清除 | 把 `XDG_CACHE_HOME` 指到 `/mnt/*` 路徑下跑解密 → **rc=1＋指名 fs／mode**，且斷言早於 `sops` 呼叫＝**零明文產生、零檔寫出**；驗完刪除該暫存路徑 |

**★ 紀律**：`alert_webhook_url` 現值為 user 已填真值（39 bytes）——**測試絕不以刪該檔為手段**；
差異情境以複本或暫時改 enc 檔內值構造，驗完復原並 byte 級比對現值未變（SC-007）。

---

## S6 落點遷移五步與向後相容（SC-005／#4／d 驗收〔brainstorm 升格字母，對照表見 spec Clarifications〕）

**做什麼**：依 contracts/secret-pipeline.md §P6 順序執行五步；②與③之間補跑
`./deploy/generate-secrets.sh --compose-only`＋`./deploy/preflight-secrets.sh`
（composite 三支不進加密檔、由 leaf 重組；preflight＝上機前 fail-loud；T030 施工時補列）。

**期望**：①`down` 先行；④逐容器
`docker inspect <c> --format '{{range .Mounts}}{{.Source}}{{end}}'` 顯示來源**皆非 `/mnt/d`**
——★每筆 Source 必先以 host 側 `readlink -f` **物理化**再比對前綴：Mounts.Source 是 compose
專案 working_dir 的邏輯路徑，symlink 環境下字面 grep 在遷移前就全綠＝假陰性（L-172；
T030 施工時補列）；
⑤確認後才刪舊落點；另**未設 `SECRETS_DIR` 時** `docker compose config` 解析回
`./deploy/secrets` 相對路徑（#4 向後相容）。

**否定測試**：跳過 `down` 直接改值 `up -d` → 觀察輸出為 `Starting` 而非 `Recreated`（config-hash
相同、不觸發重建）＝假性完成的信號 → 復原後照正確順序重做。
＋★**`.env` 行形三方矩陣**（019 U4 quality 補；契約 §P5.1 行形寬進窄出）：同一份 `.env` 逐案改寫成
`export ` 前綴／行首縮排／等號兩側空白／UTF-8 BOM／CRLF 行尾五形，每案跑
`docker compose config | grep 'file:'`、`./deploy/preflight-secrets.sh`、
`python3 tools/secret-value-guard.py check` → **三方必須解析出同一個落點**；任一案分裂
（典型＝腳本／guard 回退 `deploy/secrets` 而 compose 用新落點、且雙方 `rc=0` 零訊息）
即為 blocker——那正是「compose 掛得到、容器跑得動、唯獨 pre-commit 不再守」的假綠。
＋★**`SECRETS_DIR` 空字串邊界**（019 U4 quality 第 3 輪補；契約 §P5.1）：以 `SECRETS_DIR=`（匯出為
空字串）同時跑 `docker compose config | grep 'file:'`、四支 deploy 腳本、
`python3 tools/secret-value-guard.py check` → compose 因 `${SECRETS_DIR:-…}` 對空字串吃預設值而
回退 `./deploy/secrets`（遷移後零 `.txt`），故四腳本＋guard **必須全數 `rc=1` 並指名空字串**；
若其中任一改讀 `.env` 落點回 `rc=0`（＝「preflight 說可 up、compose 掛空目錄」）即為 blocker。
對照組 `unset SECRETS_DIR` → 三方同解新落點；`SECRETS_DIR=/tmp/rev4-nonexistent` → 環境變數仍
勝出 `.env`（preflight 指名該路徑缺檔）。
＋★**`SECRETS_DIR` 相對路徑之錨定基準**（019 U4 quality 第 4 輪補；契約 §P5.1）：**自 repo
子目錄**執行（例 `cd deploy`）並帶 `SECRETS_DIR=rel/dir`，同跑 `preflight-secrets.sh`、
`python3 ../tools/secret-value-guard.py check`、（於 repo 根）`docker compose config` →
**三方必須同解為 repo 根之 `rel/dir`**（非 CWD 相對），且 preflight **必須 `rc=1` 指名缺檔**。
若 preflight 印「齊備且健康、可 up」而 compose 指向別處＝**假綠 blocker**（該目錄零檔、`up`
會自動建空目錄當 secret 掛入；generate 更會把明文寫進 repo 樹內而值比對層掃不到＝L-178）。

**完成判準**：`/mnt/d` 全樹零明文機密檔；＋新落點在**版控面外**之機判（019 U3 遺留
advisory 一、T030 施工時補列）——`git check-ignore` 與 `git ls-files --error-unmatch` 對
新落點路徑皆 rc=128 fatal outside repository、物理路徑非 `git rev-parse --show-toplevel`
前綴、`git status --porcelain` 零行。

---

## S7 觀測軌全開讀取（SC-005 後半／c 驗收〔brainstorm 升格字母，對照表見 spec Clarifications〕）

**做什麼**：`docker compose --profile obs --profile metrics up -d` 全開一次。

**期望**：grafana（UID 472）、postgres-exporter（65534）、redis-exporter（59000）**三者皆讀得到
`/run/secrets/*` 且服務健康**。

**為何必跑**：三者平時不啟動——檔案設 600 或產物 `root:root` 時「導入當下全綠、開觀測軌才炸」；
今天全綠只是因為 9p 給了假的 777。

**收尾**：驗畢可 `--profile` 收回（jobs sidecar 維持 opt-in 未常駐）。

---

## S8 撤銷演練五準則與反向驗證（SC-006／#7／#10）

**做什麼**：①產演練用第二把金鑰→加入 recipient→`updatekeys -y`→確認新鑰可解；
②撤銷四步（移除 recipient →`rotate -i --rm-age` **逐檔一行**→輪替實際機密值）；
③五準則逐條驗（contracts/secret-pipeline.md §P8）；④#10 反向驗證。

**期望**：
- **否定測試（核心）**：舊 `enc:` stanza 貼回新檔跑原廠 `sops decrypt` → **必須失敗於 MAC 驗證**。
- rotate 前後**值密文必變**；recipient 清單前後不含被撤銷者。
- **#10**：把 `~/.config/sops/age/keys.txt` 改名移走＋`unset SOPS_AGE_KEY SOPS_AGE_KEY_FILE`
  → `sops -d` **必須失敗**（仍能解＝切換未生效，須逐條排除五類尋鑰來源）。

**★ 順序陷阱驗證**：故意先 `rotate` 後 `updatekeys` 一次 → 觀察新 data key 連同尚未移除的舊
recipient 一起加密（該中間狀態只要被 commit 一次，撤銷即為假）→ 復原並以原子指令重做。

**★ #13 提示次數實測**（FR-024 後半；趁演練期雙 recipient 在場）：以排序第二的 identity 跑
一次解密、**數 passphrase 提示次數**並記錄實測值與量測條件（recipient 數、排序位置）。
**RUNBOOK 只記實測值與條件、不寫死次數**（上游行為未有官方保證、兩來源曾未收斂）。

**收尾（★機判、019 U5 補列——原僅一句文字要求，逐列核對者會漏掉「資產是否真的復原」）**：
演練用金鑰移除、演練痕跡不入版控；**`.sops.yaml` 與 `deploy/secrets.dev.enc.yaml` 必須復原至
單 recipient**——`grep -c 'recipient:' deploy/secrets.dev.enc.yaml`＝**1**、`.sops.yaml` 與演練
前逐 byte 相同（`cmp -s`）、`sops -d` **rc=0 且 key 數＝8**；落點 11 支 sha256 與演練前基準
相符（★演練中被輪替的那一支例外——須記其新舊 sha256 前 8 碼與 byte 數，並跑
`deploy/preflight-secrets.sh` 確認 composite 一致）。

**★ 承接註記**：撤銷演練必然使加密檔換掉 data key（8 值密文全變）＝該檔的 `git diff`
**是預期產物、要 commit**；「復原」指的是 recipient 清單與可解性，不是 byte 級還原。

---

## S9 秒級紅線量測（SC-009）

**做什麼**：量測本刀新增兩段（樣式掃描、值比對）各自的成本，判斷是否維持秒級。

**方法（L-155 硬性規定）**：**以 `perf_counter` 直接包該段連跑數次取中位數**——
★**絕不可用整鏈 `time` 前後差量**：drvfs 上全鏈牆鐘變異達 ±1.5s 量級、大於被測成本
（018 U2 以整跑差量甚至量出負值）。T001 的整鏈 `time` 基線**僅供「有無數量級劣化」粗判**。
記錄「純碼 commit」與「治理檔 commit（工具本體 staged、自測觸發）」兩情境。

**怎麼造出被量的 staged 狀態（★不得用 `git add`）**：兩段成本皆正比於 staged 內容，故必須有真的
staged 狀態；但 `git add` 會把內容寫成新 blob 留在物件庫（＝L-158／L-191 的殘留源、還要收尾 prune）。
作法＝`cp .git/index` 到暫存後全程帶 `GIT_INDEX_FILE`，以
`git update-index --add --cacheinfo <mode>,<既有 blob SHA>,<新路徑>` 把**已在庫的 blob 掛到新路徑**
（零新物件、真索引與工作樹零改動）；**harness 保真機判**＝掃描器 `--verbose` 自報的
`scanned ~N bytes` 須等於掛入檔案 byte 數總和（不相符＝量到空索引，同型假象見
`.githooks/pre-commit` 註解「容器不帶 `GIT_INDEX_FILE` 掃 0 bytes 靜默漏報」）。量完以
`git status --porcelain` 零行反證未污染。詳 L-192。

**期望（機判門檻，SC-009）**：本刀**新增兩段（樣式掃描＋值比對）合計中位數 ≤5s**；值比對工具
本體 staged 時其**自測增量 ≤3s**。★判準用**增量**不用絕對總時——基線本身受 drvfs I/O 稅主導
（018 實測全鏈約 46~47s），絕對秒數不具比較意義。超標→記錄成本結構並掛 BACKLOG（比照 018
SC-008 處置慣例）。

---

## S10 治理完備（SC-010）

**做什麼**：逐項核對——①ADR 5 支（0079 起）accepted，**含 U1 三閘實測結果欄**；
②RUNBOOK 各段落地（SOPS 營運段群／§7 增補 re-encrypt 步驟／§4 增 `.wslconfig`＋BitLocker 確認／
§12 工具速查）；③BACKLOG 登記 B-115；④NOTES 同步 base-web `--no-verify` 慣例廢止；
⑤`deploy/secrets` 命中逐檔判定完成（**以現場 `git grep` 為準、不以靜態數字為驗收基準**；
程序性引用改、歷史文件不改、生成物由 generate 重算）；⑥`deploy/secrets/README.md` 四處
（預檢語意／force 語意／chmod 注記／對照表）已對齊實際行為；⑦清理 019 暫存
`$HOME/.cache/rev4-019-tmp/`（T038 唯一清理點）——清後 `ls` 反證不存在；
⑧**物件庫終驗（L-191；★不可只做 S1 收尾那一次）**——本刀期間**任何**被事件型防線擋下的 commit
都已把 staged 內容寫成 unreachable blob（擋的是 commit、不是 `git add`），且 S1 收尾的 L-158 稽核法
（`git hash-object <機密檔>` × `git fsck --unreachable` 取 **SHA 交集**）對「**文件內含**機密值」
結構性失明、會回報假綠。判準升級為**內容子字串比對**：`git fsck --unreachable` 逐筆
`git cat-file blob` 讀出、判是否含任一落點現值為子字串（只印 SHA 前 8 碼與 size、**不印內容**）
→ 非零即 `git prune --expire=now` → 反證「含機密之 unreachable blob 數＝0」。
★**三面同一判準**（L-196；漏一面即假綠）——①**unreachable**（`git fsck --unreachable`）
②**HEAD tree**（`git ls-tree -r HEAD` × `git cat-file --batch`）③**可觸及面**
（`git rev-list --all --objects` 全物件 × `git cat-file --batch`，命中者以 `rev-list --objects`
反查路徑，另限縮 `<merge-base>..HEAD` 得「本刀新引入」子集）——**三面一律跑子字串掃**。
★**可觸及面絕不可用 SHA 交集／`cat-file -e` 判否**：那是 L-191 已點名失明的 SHA 相等判準，
對「檔案**內含**機密」永遠回 0；本刀第一次寫這步就踩了（unreachable 面已升級、可觸及面用回舊
判準＝假的「未進歷史」）。
★**命中≠0 後的分流表**（此步是「只需 prune」vs「已進歷史」的**唯一**判準、不可含糊）：
（a）**真機密**（憑證／金鑰／可用於認證之值）→ **輪替該值＋改寫歷史**（`filter-repo`／
BFG）＋所有持有方同步，二者缺一即未結清；（b）**dev 佔位／不可外部解析之內部位址**且經評估
無憑證材料 → 可判**已接受殘餘**，但必須**誠實登記**（ADR 殘餘風險欄或 commit 訊息寫明「值已在
歷史、不改寫、理由與失效條件」），不得寫成「未進歷史」或「暴露面已關閉」。
⑨**收刀 finishing 硬性義務的可行動歸屬**（U6 quality 補列）：ADR 0080 決策 5 之收刀期兩組步驟
（user 親產真鑰＋暫代鑰撤銷四步＋7 支 leaf 輪替）在 tasks.md 明載「不在本任務範圍」、而 40 項
全勾＝無未勾項可承接——核 **BACKLOG 登記 B-120**（`grep -c 'B-120' docs/ops/BACKLOG.md` ≥1）
＋NOTES 同步一句。缺此登記＝該義務只活在 ADR 正文與**已勾選**的備註裡（L-165 型缺口），
而 ADR 0080 殘餘風險 #4 自陳「未完成前版控內密文的實質保護等同無」。
⑩**活書 as-built 修正的可行動歸屬**（U6 quality 第 2 輪補列）：`docs/arc42/ARCHITECTURE.md` 屬活書、
依紀律**不在 feature branch 改**而歸收刀簿記 commit——故 feature branch 上唯一可驗的是**歸屬存在**：
核 **BACKLOG 登記 B-122**（`grep -c 'B-122' docs/ops/BACKLOG.md` ≥1）＋NOTES 同步一句，且該列須逐條
指名活書失真處（本刀＝§7「機密」段之落點敘述與 `CHANGE-ME` 黑名單射程兩處，**＋第 3 輪補入的
`§8 橫切概念`「機密內容」列**——慣例欄與守門欄仍是 018 單層狀態〔窄樣式不含泛熵值、守門只列 L16〕，
與 ADR 0082 三層並存＋pre-push 三 repo 之 as-built 相反）；★**收刀事件 `arch_impact` 須含 `§7`
與 `§8`**，只列 §7 即把 §8 排除在義務外（而 L6(b) 不擋遺漏、見下）。
★**不可援引 lint L6(b) 當補償閘**：L6(b) 只對「宣稱 `arch_impact` 節集」與「簿記活書實際變動節集」
兩個**差集**發 ERROR——收刀若宣稱空集合又不動活書，兩者同為空、零 findings 全綠（它擋帳面不符、
不擋遺漏）。★併跑**勘誤枚舉**確認沒有「只修被點名那一處」：對每個被改述的泛稱句跑
`python3 tools/docs-sync.py errata '<句中關鍵詞>'`，逐處標明已修／歷史文件不改／歸收刀，
且關鍵詞須取**最短共同片段**（窄化即漏枚舉——本刀實證：以較長片段查會漏掉活書那一處）；
判讀時排除治理檔（BACKLOG／tasks／本檔）內談論該句的**後設引用**＝自指噪音、非待處置落點。

**期望**：全數齊備且與實測結果一致；`docs-sync.py lint` **0 錯誤**、`generate` 後無 diff。
★**判準寫成語意式、不寫死警告筆數**（U6 quality 第 3 輪釐清、收單確認重寫）：收刀放行條件＝
**0 錯誤，且警告集合逐筆具名並各有可行動歸屬——空集合亦合格**；出現**無可行動歸屬之警告、
或任何錯誤**即不放行。★**警告筆數與 token 數皆為量測時點值**：第 3 輪當時為「0 錯誤／1 警告」
（該筆＝`L7｜docs/ops/LESSONS.md｜24783 tokens`、ERROR 餘裕 217、可行動歸屬＝BACKLOG B-121），
第 4 輪（`07f1df7`）已依主檔規則切出封存卷 `LESSONS-151-175.md`、主卷回落 14007 tokens、
`lint` 回到 **0 警告**，B-121 亦隨之收單刪列（`a4b6bff`）。判讀一律以現場
`python3 tools/docs-sync.py lint | tail -3` 為準、不以本行任何數字為基準——★U6 反覆實證＝
**L-197 失效模式多向復發**（★**復發次數本身也是量測時點值、不寫死**）：先是 T038 把 `3415dc9`
當時的 21598／0 警告寫成終驗恆值、被同單元後續兩輪自己的 append 推翻；接著本段又把「恰只允許
1 筆警告」寫成收刀恆值、被第 4 輪自己的分卷推翻（**警告被消滅也是一種推翻**——故筆數不入判準、
詳 L-197 防法②）；再者 T038 把分卷的「逐筆 byte 級零漂移」寫成不標基準的布林恆值，被 L-197
自身的就地勘誤推翻（→該段已補兩端基準 SHA 與排除清單、詳 L-197 防法①）。
★**機密值輸出禁令貫穿全節**（L-193）：byte 級健檢一律寫成**布林斷言**並只印 True／False 與 byte 數
（`b[-1] not in (0x0a, 0x0d)`、`b'\r' not in b`）——`tail -c1 | xxd` 之類會把機密值的 byte 印上終端；
需要指紋時用 sha256 前 8 碼（雜湊、非值切片）。
