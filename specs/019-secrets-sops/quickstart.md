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

**★ 紀律**：`alert_webhook_url` 現值為 user 已填真值（39 bytes）——**測試絕不以刪該檔為手段**；
差異情境以複本或暫時改 enc 檔內值構造，驗完復原並 byte 級比對現值未變（SC-007）。

---

## S6 落點遷移五步與向後相容（SC-005／#4／d 驗收〔brainstorm 升格字母，對照表見 spec Clarifications〕）

**做什麼**：依 contracts/secret-pipeline.md §P6 順序執行五步。

**期望**：①`down` 先行；④逐容器
`docker inspect <c> --format '{{range .Mounts}}{{.Source}}{{end}}'` 顯示來源**皆非 `/mnt/d`**；
⑤確認後才刪舊落點；另**未設 `SECRETS_DIR` 時** `docker compose config` 解析回
`./deploy/secrets` 相對路徑（#4 向後相容）。

**否定測試**：跳過 `down` 直接改值 `up -d` → 觀察輸出為 `Starting` 而非 `Recreated`（config-hash
相同、不觸發重建）＝假性完成的信號 → 復原後照正確順序重做。

**完成判準**：`/mnt/d` 全樹零明文機密檔。

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

**收尾**：演練用金鑰移除、演練痕跡不入版控。

---

## S9 秒級紅線量測（SC-009）

**做什麼**：量測本刀新增兩段（樣式掃描、值比對）各自的成本，判斷是否維持秒級。

**方法（L-155 硬性規定）**：**以 `perf_counter` 直接包該段連跑數次取中位數**——
★**絕不可用整鏈 `time` 前後差量**：drvfs 上全鏈牆鐘變異達 ±1.5s 量級、大於被測成本
（018 U2 以整跑差量甚至量出負值）。T001 的整鏈 `time` 基線**僅供「有無數量級劣化」粗判**。
記錄「純碼 commit」與「治理檔 commit（工具本體 staged、自測觸發）」兩情境。

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
（預檢語意／force 語意／chmod 注記／對照表）已對齊實際行為。

**期望**：全數齊備且與實測結果一致；`docs-sync.py lint` 全綠、`generate` 後無 diff。
