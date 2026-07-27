---
id: "0077"
title: 憑證內容掃描閘——外層 tracked 全量＋pin bump 增量掃 submodule、窄樣式集高確信、無 inline 豁免
date: 2026-07-28
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 018-governance-hardening brainstorm §4 ADR draft 候選（user 親決「憑證掃描範圍＝外層 tracked 全量＋pin bump 時增量掃 submodule」）＋research R1（樣式集定稿與樣本構造紀律）／R2（文字二進位判定）／R3（增量掃實作與退化）；spec FR-007／FR-008、contracts G1"
tags: [security, lint, pre-commit, governance, submodule]
---

## 背景

rev4 對機密入庫只有**結構面**防線——gitignore 擋 `.env`／憑證目錄、schema-gate 擋 seed 密碼
字面詞典——沒有任何**內容面**掃描：任何檔案裡的私鑰本文、雲端 access key、平台 token 都能
一路 commit 進版控。001 那刀的 CA 私鑰是靠人工 review sweep 才在入庫前攔下，屬於運氣而非
機制。同時兩個 submodule（base-web／rust-api）各自推 github 遠端，其新進內容在外層完全
不被任何機器閘看過——外層只記 gitlink SHA，pin bump 時等於把一整段未經掃描的歷史接進來。

守門工具鏈「從來不掃自己」的葫蘆是本刀（018）的共同動機；憑證面是其中唯一的安全缺口、
且有真實前例，故單獨立 ADR 定範圍與哲學。

## 決策

lint 新增條款 **L16 憑證內容掃描**（contracts G1），命中即 ERROR 擋 commit。五項決策：

1. **掃描範圍＝外層 tracked 全量＋pin bump 時 submodule 增量，不回掃歷史**。
   外層面：每次 lint 對 `git ls-files` 全部 tracked 檔（扣除 gitlink 條目）逐檔讀，前 8KB
   含 NUL byte 判二進位跳過，其餘以 UTF-8（`errors="replace"`）全文過樣式集。
   ★外層面的判定基準同時取 index、不只取工作樹快照：`git diff --cached` 的新增行亦過同一
   樣式集，涵蓋「`git add` 後把工作樹檔刪掉」與「`git add` 後把工作樹版本洗白」兩態——閘
   要護的是這次要進版控的內容，工作樹乾淨不等於 index blob 乾淨；且工作樹讀不到（檔缺席、
   權限、目錄）一律落 WARN 留信號，不得靜默視同乾淨（「沒掃到」與「掃過沒命中」必須分得開）。
   submodule 面：staged 含 `base-web`／`rust-api` gitlink 變動時才啟動，掃「舊 pin→新 pin」
   diff 的新增行——成本正比於本次帶進來的變更量，不是每次 commit 掃兩個大庫全樹。
   舊 pin 不可解（base-web upstream rebase 後首次 bump 是常態）或 diff 失敗→**退化為掃新
   pin 全樹並附 WARN 註記**（fail-closed 方向：寧可多掃、不可漏窗）；submodule worktree
   缺席（唯讀快速看碼模式）→跳過並落跳過明細。
   ★退化掃**本身跑不成**（例如新 pin 物件不在該庫、切分支後尚未 fetch）→**ERROR**，不得
   當成零命中放行：那會在 WARN 已宣稱「已退化為全樹掃」的同時做出假保證，比不掃更危險。
   「無命中」與「沒跑成」必須在實作上分得開——退化面唯一走 git 自己的 regex 引擎（其餘面
   走 python），該路徑的紅綠射程靠自帶測試逐 label 實跑保證，不靠單一樣本抽驗。
   **明文不做**：不回掃 submodule 既有歷史——已推遠端的內容撤不回來，掃出來只能製造無法
   處置的紅；歷史面的處置歸憑證輪替，不歸 commit 閘。
   落選：只掃外層（submodule 新進內容永遠是盲區）；每次 commit 掃 submodule 全樹（重複掃
   同一份歷史、成本與訊噪比都差）。

2. **窄樣式集高確信，有意識接受漏報面**。樣式集＝四個 label（regex 常數住
   `tools/docs-sync.py` 的 `CRED_PATTERNS`、逐字定稿見 018 spec 的 data-model 第 1 節）：
   `pem-private-key`（PEM／OPENSSH／PGP 私鑰家族的 BEGIN 頭形）、`aws-akia`（AWS access
   key id 前綴＋16 位大寫英數）、`github-token`（GitHub classic／app token 的五種二字母
   前綴形）、`github-pat`（GitHub fine-grained PAT 前綴形）。
   **明文排除**：泛熵值偵測（高熵字串到處都是——雜湊、base64 資產、測試 fixture，誤報成本
   遠高於殘餘風險）；`password=` 等號類（同樣誤報面大，且 seed 密碼字面已由 schema-gate
   的詞典條款承載）。
   代價＝**漏報面**：不在樣式集內的機密形（自建 API key、資料庫連線字串裡的密碼、雲端
   服務商的其他 key 形）掃不到。這是有意識的取捨——一個會被關掉的高誤報閘價值為零；樣式集
   擴充屬後續小改（動一個工具常數即可），擴充時憑實際命中案例決定、不憑想像。

3. **無 inline 豁免 marker；豁免唯一路徑＝工具常數白名單＋ADR，現白名單為空集**。
   刻意不提供「在該行加註記就放行」的機制：inline marker 等於把繞過閘的權力交給任何一次
   commit，而洩漏的代價不可逆。確有教學或測試需要留下形似真鑰的字面時，走
   `tools/docs-sync.py` 的 `CRED_WHITELIST` 常數（現為空集）並同時立 ADR 說明理由——白名單
   進出都留在 git 史與決策紀錄裡，而不是散落在被豁免的檔案內。
   前提條件是現庫必須乾淨：2026-07-28 對全庫 tracked 檔預掃實測 415 檔（扣 2 個 gitlink
   後 413 個文字檔）**零命中**，故白名單得以從空集起步。

4. **self-test 防恆綠＋樣本執行期構造紀律**。每次 lint 執行連帶跑紅綠樣本驗證：四個 label
   的紅樣本必須各自被自己的 label 攔下、綠樣本（普通文字與形似但不合規的字串）必須全數
   放行，任一不符即 ERROR。這道防的是「條款還在、但已經永遠不會紅」——沿用
   fork-delta-lint 每跑必 self-test 的既有範式。
   ★配套紀律：**所有紅樣本一律以執行期字串串接構造，任何 tracked 檔內不得出現任何一個
   樣式的完整命中字面**（工具本體、自帶測試、本 ADR、commit message 皆同）。理由是外層
   全量掃會掃到工具自己與文件自己——落了完整字面就自命中自紅，掃描器變成自我毀滅裝置。
   樣式的 regex 字面本身不自匹配（regex 中的字元類與量詞語法不構成合法命中），故文件與
   常數表得以記載完整 regex。

5. **命中訊息形制**：外層面指名「檔案路徑：行號」與 label；submodule 面另含庫名與該庫內
   檔案路徑，並指引「回該庫移除並輪替後重 bump pin」。輪替是必要動作——內容一旦寫進任何
   一次 commit 就當作已洩漏，移除只是止血。

## 後果

- pre-commit 每次都多一趟外層全量檔案讀取：本機（WSL2 drvfs、413 個文字檔）實測約 1.5 秒，
  相對既有 lint 全鏈約 46 秒屬可忽略增量；未來 tracked 檔數量級成長時（如引入大量資產檔）
  需重估，屆時可改走 `git grep` 一發或只掃 staged 面。
- 樣式集擴充與白名單新增都必須動工具常數＝必然經過 code review 與 ADR，不會靜默漂移。
- 漏報面殘留（第 2 項取捨）：內容面掃描是**縱深防禦的一層**，不取代 gitignore 結構面、
  不取代審查輪、也不取代「憑證本來就不該進 repo」的紀律。
- submodule 面只在 pin bump 時觸發，與 fork-delta-lint 的觸發條件同型（同樣掛 staged 含
  gitlink 變動）、彼此無順序相依、各自獨立紅綠。
- 掃描面的 tracked 檔清單「理論上不可能為空」——空即代表掃描器或環境壞了，該情境的
  fail-closed 守衛歸 018 後續單元的空集合守衛條款統一處置。
