# contracts/scan-gates.md — 019 洩漏掃描三層防線的機器閘契約

> 契約＝可機器驗證的閘門行為（觸發條件／通過與否／退出碼／跳過語意）。實作細節見 plan／tasks；
> 本檔只定「什麼情況必須紅、什麼情況必須綠、紅時退出碼是什麼」。

---

## S1 樣式掃描閘（pre-commit；FR-003／FR-004）

- **落點**：外層 `.githooks/pre-commit` 第一段（**先於** `docs-sync check`）；
  兩源倉 `.githooks-submodule/pre-commit` 唯一段。
- **指令**：`betterleaks git --pre-commit --staged --redact --verbose --exit-code 2`
- **通過**：無命中 → exit 0，靜默（不印摘要以免淹沒既有輸出）。
- **不通過**：命中 → scanner exit 2 → hook **exit 1** 擋 commit；輸出含 rule id 與檔案行、
  **值一律遮蔽**（`--redact` 裸寫＝100%）。
- **執行錯誤**：scanner exit 1（binary 缺失／config 語法錯）→ hook 以**可辨識訊息**擋下並指名
  「掃描器本身異常，非機密命中」＋指向 `tools/bootstrap`。
- **硬紀律**：①`--redact` 不可省（省略＝預設 0＝明文噴進終端與 scrollback）；②一律用 `git`
  子命令，**禁用 `protect`／`detect`**（兩專案皆已隱藏、無文件保證）；③**原生二進位**執行，
  禁容器形式（容器不帶 `GIT_INDEX_FILE` → `git commit -a` 掃 0 bytes 靜默漏報）。

---

## S2 值比對閘（pre-commit、**僅外層**；FR-007）

- **落點**：外層 `.githooks/pre-commit`（樣式掃描之後、`docs-sync` 之前或之後皆可，順序不構成
  契約）；**兩源倉不掛**（clarify 拍板：源倉零 python 依賴）。
- **輸入**：`$SECRETS_DIR`（回退 `deploy/secrets`）下的機密現值 × `git diff --cached` 內容。
- **通過**：staged 內容不含任何機密現值原文 → exit 0。
- **不通過**：命中 → **exit 非 0** 擋 commit；訊息指名「檔案:行號＋命中的機密名稱」，
  **絕不輸出值本身**（連遮蔽形式也不印）。
- **跳過（不算失敗）**：機密現值目錄缺席或為空（開機未解密）→ 印可辨識 skip 提示、exit 0
  （fail-open；樣式掃描為主防線）。
- **self-test**：每次執行連帶跑紅綠樣本；紅樣本未攔或綠樣本誤報 → **ERROR 級擋 commit**
  （防恆綠）。紅樣本以執行期字串串接構造（避免本檔自命中）。

---

## S3 pre-push 範圍掃描閘（三 repo；FR-005）

- **落點**：`.githooks/pre-push` 與 `.githooks-submodule/pre-push`（共用
  `.githooks/lib/scan-range.sh`，源倉側以 `dirname "$0"` 自我定位 source）。
- **輸入**：git 的 pre-push stdin 契約，每行
  `<local-ref> <local-oid> <remote-ref> <remote-oid>`。
- **範圍推導**：
  | 情境 | 判定 | 掃描範圍 |
  |---|---|---|
  | 一般更新 | 兩 oid 皆非全零 | `--log-opts=<remote-oid>..<local-oid>` |
  | 新分支首推 | remote-oid 全零 | `--log-opts=<local-oid> --not --remotes=origin` |
  | 上述退階 | `--remotes=origin` 為空 | 掃整條分支 |
  | 刪除分支 | local-oid 全零 | **跳過該行**（無內容可掃） |
- **通過**：所有行皆無命中 → exit 0。**不通過**：任一行命中 → exit 1 擋 push。
- **契約邊界**：本閘攔的是「`--no-verify` 放行後尚未離開本機」的 commit；`git push --no-verify`
  仍可繞過＝已知邊界（事件型檢查的本質），由 allowlist 先行降低繞過誘因。

---

## S4 掃描器存在性斷言（bootstrap；FR-001）

- **落點**：`tools/bootstrap` 新段（沿既有編號段慣例）。
- **通過**：`command -v betterleaks` 成功且版本符合釘定值 → `ok`。
- **不通過**：缺席或版本不符 → **`die`（exit 2）**＋安裝指引（下載 URL 樣式
  `betterleaks_<VER>_linux_x64.tar.gz`＋`sha256sum -c checksums.txt` 驗證步驟）。
- **理由**：缺 binary 時 hook 會以 exit 127 擋掉每一次 commit 且訊息難解——體檢須在此之前
  fail-loud。**注意三級差異（刻意、非疏漏；完整口徑見 secret-pipeline.md §P5.4）**：本斷言與
  hooksPath 斷言＝`die` 級（工具鏈完整性）／`.env` 缺失＝bootstrap 代勞產生（自癒、不中止）／
  secrets 實值缺檔＝維持既有 `warn` 級（人對人交接、bootstrap 不生成）；**上機前的 fail-loud
  由 preflight 承載**。

---

## S5 hooksPath 佈署與斷言（bootstrap；FR-006）

- **佈署**：`git -C <base-web worktree> config core.hooksPath <ROOT>/.githooks-submodule`；
  rust-api 同形。冪等（重跑＝再設同值）。
- **斷言**：兩源倉 `core.hooksPath` 讀值符合預期 → `ok`；不符或未設 → `die`＋自癒指令。
- **不變式**：**兩源倉工作樹零改動**（hooksPath 屬 per-machine git config、非樹內檔案）
  → fork-delta 面不變、pin 不變、憲法 §III 軌道零波及。
- **邊界**：他機 clone 未跑 bootstrap ＝ 兩源倉無防線（per-machine 設定的本質）——由本斷言
  在 bootstrap 時暴露。

---

## S6 三層互補不變式（FR-008 驗收語意）

| fixture 形 | 樣式掃描 | 值比對 | 期望總結果 |
|---|---|---|---|
| `KEY=value` 形（假 token） | 命中 | — | **擋** |
| DSN 形（`postgres://u:p@h`） | 命中（自訂規則） | — | **擋** |
| 裸值形（機密現值原文） | **不中＝預期** | 命中 | **擋**（僅外層） |
| SOPS 密文形（`ENC[…]`） | 不中 | 不中 | **放行** |

- 四形 ×（`git add`+`commit`／`git commit -a`）兩路徑＝8 格，**兩路徑結果必須一致**
  （`git commit -a` 路徑必測——容器形式的靜默漏報只在此路徑現形）。
- 兩源倉另各以樣式形 fixture 實擋至少一案（裸值形在源倉屬預期不擋、不列入源倉驗收）。
- 例行簿記 commit（events.jsonl append 40-hex）**必須不被誤擋**（allowlist 生效證明）。
