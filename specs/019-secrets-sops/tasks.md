# Tasks: 019-secrets-sops 機密管理——SOPS+age 全量導入＋三層掃描防線

**Input**: spec.md（US1~US5）＋plan.md＋research.md（R1~R19）＋data-model.md（7 模型）＋
contracts/scan-gates.md（S1~S6）＋contracts/secret-pipeline.md（P1~P8）＋quickstart.md（S1~S10）
**Tests**: TDD 必列（rev4 工作流紀律：先紅後綠）——python 工具自帶 unittest（沿 018 家族慣例）；
bash 腳本與 hook 走 fixture 演練機判（否定測試為主）；[P] 僅限異檔零依賴。
**排序註記**: Phase 2（U1 三實測閘）**只 block US2~US4、不 block US1**——US1 不依賴 SOPS，
建議實際執行序＝Setup→**US1（MVP）**→Foundational→US2→US3→US4→US5。全刀**零 submodule
改動、零 pin bump**（兩源倉僅設 per-machine `core.hooksPath`）；★不排入 push/merge
（CLAUDE.md 硬禁令；finishing 另行）；活書 ARCHITECTURE as-built 不入本清單（落收刀簿記＝L6(b) 閘）。

## Phase 1: Setup

- [x] T001 基線快照（供 SC-009 對照、數字記回本行備註）：`sh .githooks/pre-commit` 全鏈實跑
  `time` 基線（無 staged、無工具改動）×2 取中位；＋`python3 tools/docs-sync.py test`／
  `schema-gate.py test`／`wire-schema.py test` 三套件現況案數（預期 347／130／7）——沿 018
  T001 方法論（drvfs 牆鐘變異大、同機同日對照，L-155）
  ——**實測（2026-07-28）**：全鏈 51.3s／52.3s（中位 51.8s、rc=0×2）；三套件 347／130／7 全綠
- [x] T002 **三支外部工具釘版雙查與拍板呈報**（★需 user 拍板、不得自決；CLAUDE.md §6 釘版
  紀律；一次呈報三案、避免施工中途再中斷）：①**Betterleaks**（research R1 當日值 v1.7.1／
  2026-07-27）②**sops** 映像（R7 當日值 v3.13.3-alpine＋其 multi-arch index digest，需複查該
  digest 仍指向該 tag）③**age**（R9 當日值 v1.3.1）——三者皆屬浮動量必須現查上游最新穩定版，
  各以「維持研究當日值 vs 更新版」兩案呈報 user 選定 → 選定值記入 `docs/ops/RUNBOOK.md`
  工具版本欄，供 T003／**T040**／T018／T019 取用
  ——**拍板（2026-07-28）**：①Betterleaks v1.7.1 ②sops v3.13.3-alpine（index digest
  ae501277…140ea 本輪對 ghcr 逐字複核相符）③age v1.3.1——三者皆＝研究當日值＝現查最新穩定；
  已記 RUNBOOK §12 版本欄。**併問儀式拍板＝C 案**（拍板全文＝ADR
  `docs/arc42/decisions/0080-age-identity-bprime-secretsdir-solution2.md`「決策」節第 5 點；
  施工面見 T019）
- [x] T003 安裝掃描器並驗證：依 T002 拍板版本下載 `betterleaks_<VER>_linux_x64.tar.gz`
  （★版號無 `v` 前綴、架構寫 `x64`）＋`checksums.txt`（★檔名不含版號）→ `sha256sum -c`
  驗證 → 安裝至 PATH → `betterleaks version` 確認與拍板值一致（不符即中止、依 §6 紀律）
  ——**實做（2026-07-28）**：`sha256sum -c` OK→安裝 `~/.local/bin/betterleaks`→`version`
  回 `1.7.1` 與拍板一致

## Phase 2: Foundational（U1 三實測閘）

**Goal**: 結清三個 go/no-go 實測，決定 US2／US3 的方案形狀；結果全數記入 ADR draft。
**Blocking 範圍**: block US2／US3／US4；**不 block US1**。

- [x] T004 **閘 #2**（硬性前置、research R14）：於 `$HOME` ext4 路徑與 `/dev/shm` 各放測試檔，
  以該路徑 bind-mount 起一個容器，`docker inspect --format '{{json .Mounts}}'` 確認 Source
  正確且容器**讀得到**；併驗權限與 UID 行為。★**失敗＝方案形狀改「解法 1 環境變數注入」
  ＝立即停工升級 user 重拍**（腳本形狀全異、後續任務作廢重寫），不得自行改設計
  ——**實測（2026-07-29）閘 #2 全過**：ext4（`$HOME/.cache` 下測試目錄）與 `/dev/shm` 下
  0700 測試目錄各起 alpine:3.23.3（--rm），inspect Mounts Source 逐字正確、容器內 cat 讀到
  同值；UID/權限＝真 POSIX——uid:gid 1000:1000 原樣呈現、600 檔擋非 owner UID（472/59000
  Permission denied）、644 檔之**檔案級** bind-mount（＝compose secrets 實形）UID 472/59000
  皆讀取成功；另實測「掛整個 700 目錄」時非 root UID 無法穿越＝dir 700＋file 644＋逐檔掛載
  的既定設計正確自洽。實驗檔與容器已全清
- [x] T005 **閘 #11**（結論反轉條件、必須早於落點定案）：自 Windows 側 docker client 對
  WSL 內部 ext4／tmpfs 路徑起一個容器，**以 `docker inspect` 的 Mounts 判讀**（非只看容器
  有沒有起來）；併校準「解密後明文能否被 Windows 側讀取」。★**反轉→SECRETS_DIR 拍板回頭
  重做（2 vs 2′ 比較基礎改變）＝升級 user**
  ——★**實測（2026-07-29）閘 #11 反轉、升級 user**（雙側完整數據見本次 blocked 回報；
  環境＝distro Ubuntu-24.04、Docker Desktop 引擎 29.6.2、docker.exe 同引擎）：
  ①**Windows 側 docker.exe 以 UNC 形 `\\wsl.localhost\Ubuntu-24.04\dev\shm\...` 可定址
  WSL 內部 tmpfs 起容器且 Mounts 成立、容器內讀到明文**（600 權限被容器 root 無視）；
  ②**/dev/shm 明文可被 Windows 側輕易讀取**——`powershell.exe Get-Content` 與 `cmd.exe type`
  經 `\\wsl.localhost`（及舊別名 `\\wsl$`）讀 600 權限測試檔皆逐字成功；③對照組：docker.exe
  以**純 Linux 路徑字串**（`/dev/shm/...`／`/home/...`）掛載＝Mounts JSON 與 WSL 側完全同形
  但容器內是**別 namespace 的空目錄**（構不到 Ubuntu 內容；證「只看 inspect Mounts 不可判定
  定址成立、必須驗內容」）；④對稱性：ext4（`$HOME`）路徑經 UNC 讀取同樣成功＝live 通道對
  解法 2 與 2′ 暴露相同、2′ 差異化收益收窄至 at-rest（不落 vhdx）與關機即清。
  ——與 2′ 拍板前提相悖之兩個停工級判準例逐字命中→**status blocked、SECRETS_DIR 2 vs 2′
  比較基礎由 user 重裁**；T006/T040/T007/T008 未動工（B′×2′ 自洽耦合、待重拍後續跑）
  ——★**重拍定案（2026-07-29、user 三點）**：拍板全文與三點理由＝ADR
  `docs/arc42/decisions/0080-age-identity-bprime-secretsdir-solution2.md`「決策」節第 1~3 點
  與其下「user 重拍三點定案與理由」段（＝**唯一權威落點**）；**本任務範圍止於閘 #11 實測與
  升級 user 重裁**——重拍值之落地屬 T024（`.env` 定值）／T031（RUNBOOK 常駐語意）等下游任務。
  閘就此結清、續跑 T006 起
  （★2026-07-29 改正：本備註原就近複述三點全文，與 ADR 該節近乎逐字鏡像，且下游八處寫
  「詳 T005 備註與 ADR 0080」＝雙頭權威；現拍板收歸 ADR、tasks 側只留指路——同型坑與防法
  見 L-166，本輪才掃到之因見 L-167）
- [x] T006 [P] pinentry 前置（research R8）：建 `~/.gnupg/gpg-agent.conf` 寫入
  `pinentry-program /usr/bin/pinentry-curses`＋`GPG_TTY` 設定 → `gpgconf --reload gpg-agent`
  （本機該檔原不存在＝零衝突覆蓋風險；純終端 session 下預設 pinentry-gnome3 可能彈不出）
  ——**實測（2026-07-29）**：`/usr/bin/pinentry-curses` 存在（1.2.1）；conf 原不存在（與 R8
  一致、免備份）→ 寫入 pinentry-program 一行（mode 600）→ `gpgconf --reload gpg-agent` rc=0
  → 讀回逐字相符；`GPG_TTY` 屬 session 環境變數、非 gpg-agent.conf 合法選項＝以 session
  `export GPG_TTY=$(tty)` 落實、RUNBOOK 面落地歸 T031
- [x] T040 **age 二進位取得**（★編號後補、**執行序在 T006 之後 T007 之前**、見 Dependencies；T007 的硬前置——T007 要實跑 `age-keygen` 與 `age -p`，而全清單
  原僅 T019 取得 age 且用完即刪、host 現況無此工具）：依 T002 拍板之 age 版本自官方 GitHub
  release 下載 `age-v<拍板版本>-linux-amd64.tar.gz`，**以該版本 release API 的 `digest` 欄位
  現查值比對 `sha256sum`**（★age **無 checksums 檔**、改配 Sigsum `.proof`；R9 所記 v1.3.1
  之 sha256 僅研究當日值、版本一變即作廢）→ 置於暫存路徑供 T007／T019／T033 共用、**全刀完成後刪除（清理承接＝T038 收刀終驗）**
  ——**實測（2026-07-29）**：release API digest 現查值＝`sha256:bdc69c09cbdd6cf8b1f333d372a1f5
  8247b3a33146406333e30c0f26e8f51377`、tarball `sha256sum` 逐字相符（比對基＝本輪 API 現查、
  非 research 舊記；本輪現查值恰與 R9 當日值相同）；解包路徑＝
  `$HOME/.cache/rev4-019-tmp/age/age/`、`age` 與 `age-keygen` 實跑皆回 v1.3.1
  ——★**勾選語意＝取得與 digest 驗訖已完成**（T007／T019 硬前置就此解除；**T019 直接沿用此
  二進位、勿重複下載**）；本任務文中「全刀完成後刪除」之暫存清理
  （`$HOME/.cache/rev4-019-tmp/`＝tarball＋release-api.json＋解包目錄）**未隨勾選完成、
  屬收刀時執行之餘留步驟**（勾選不代表暫存已清；★承接任務＝T038、其列明清理此暫存）
- [x] T007 **閘 #3**（B′ 定案點）：`age-keygen | age -p` 產一把 passphrase 加密 identity
  （★`age -p` 的 passphrase 讀取走 `/dev/tty`、與 stdout 重導向互不干擾，真 TTY 下可行）→
  `xxd` 驗 `keys.txt` 尾端無 CR → 以 `--age <剛產生的公鑰>` 直接指定做最小加解密往返
  （**此處不用 `.sops.yaml`**，避開循環依賴）→ 另開 shell 跑解密，確認**跳出 passphrase
  提示且解得開**、且無 keyring 自動填入假象；**先記單 recipient 情境的提示次數作基線**
  （★#13 的多 recipient 值在此時點結構性量不到、僅一把金鑰；由 T033 雙金鑰在場時實測、
  RUNBOOK 不寫死）。★成功→定案 B′；**失敗→預拍退路自動
  生效：方式 A（明文 identity＋`chmod 600`）＋SECRETS_DIR 降解法 2＝`$HOME/.cache/rev4-secrets`
  （ext4 持久、免開機儀式；compose 與腳本零改動、只換 `.env` 一個值）——記入 ADR、不停工**
  ——**實測（2026-07-29）閘 #3 全過→B′ 定案、退路未動用**（重拍後退路＝僅退方式 A、
  SECRETS_DIR 已在 2；詳 ADR 0080「決策」節第 3 點）：全程 pty 驅動（python pty、零人工）——
  ①`age-keygen | age -p` 產拋棄式 passphrase 加殼 identity（371 bytes、開頭
  `age-encryption.org/v1`＋binary scrypt 段、`xxd` 驗尾端無 CR〔末 byte 0x64〕）；
  ②sops 官方容器（digest 釘版）`--age` 公鑰加密最小檔（不用 `.sops.yaml`）＝key 名明文、
  值 `ENC[`；③另開新 pty session 帶 `SOPS_AGE_KEY_FILE`（唯讀掛載、容器 env 乾淨）解密：
  跳提示 `Enter passphrase for identity 'SOPS_AGE_KEY_FILE':`、輸入後逐字還原 rc=0；
  ④第二次解密仍跳提示＝無 keyring／agent 快取假象；⑤錯誤 passphrase 反證 rc=128、零明文
  （`Recovery failed because no master key…`）＝提示為真實守門。**單 recipient 提示次數基線＝
  每次 `sops -d` 恰 1 次**（多 recipient 值由 T033 量、RUNBOOK 不寫死）。閘用檔案全程限
  `$HOME/.cache/rev4-019-tmp/gate3/`（未碰 `~/.config/sops/age/`）、identity 與實驗檔驗畢
  全清、容器一律 --rm 零殘留
- [x] T008 三閘結果落 ADR draft `docs/arc42/decisions/0080-*.md`（私鑰與落點篇的實測欄）：
  逐閘記「怎麼跑／實測輸出／結論／對設計的影響」；#3 失敗時另記退路生效與 SECRETS_DIR 降階
  ——**實做（2026-07-29）**：落檔 `0080-age-identity-bprime-secretsdir-solution2.md`
  （status: draft、格式對齊 0077）：三閘逐閘四欄實測欄（#2 過引 T004 證據／#11 反轉雙側
  數據＋user 重拍三點定案與理由／#3 本輪全過 B′ 定案、退路未動用）＋C 案產鑰儀式拍板落
  「決策」節第 5 點（★2026-07-29 改正：原落成獨立「引用」節、與 T019 互指權威成循環錨且
  兩段近乎逐字鏡像；現 ADR 為唯一權威落點、tasks 側只留指路一行——坑與防法見 L-166）
  ＋解法 2 at-rest 代價誠實登記；正文完稿歸 T034（Phase 7 US5 治理）、
  收刀轉 accepted
  ——★**重拍連帶註記**：上方任務文「#3 失敗時另記退路生效與 SECRETS_DIR 降階」屬 2′ 基準原文；
  #11 反轉重拍後退路**僅退方式 A、不含 SECRETS_DIR 降階**（ADR 0080 決策 3），且本輪 #3 全過
  ＝退路未動用、無「降階」可記

## Phase 3: US1 — 機密洩漏三層掃描防線（P1；MVP）

**Goal**: Betterleaks 事件型廣譜 × 既有 docs-sync L16 狀態型窄樣式 × 值比對確定性三層互補，
覆蓋三 repo 的 commit 與 push 邊界。
**Independent Test**: spec US1——8 格 fixture（四形 × 兩路徑）全符預期、三 repo 各實擋一案、例行簿記
commit 零誤擋（不建任何 SOPS 資產即可完整驗證）。

- [x] T009 [US1] **誤報基線現場重建**（★必先於 T010；不得沿用任何舊數字）：以 T003 安裝之
  掃描器對全歷史實跑一次，逐筆分流「真機密／誤報」並記錄命中樣態與所屬檔案；重點確認
  `docs/ops/events.jsonl` 的 40-hex 三欄（merge／pins.web／pins.api）、
  `deploy/secrets/*.txt.example`、`specs/017-audit-retention/quickstart.md` 的 `curl -u` 示例
  ——**實測（2026-07-28、493 commits、--redact 全程）**：21 findings、逐筆分流全數誤報、
  零真機密——events.jsonl `pins.api` 欄 40-hex ×20（generic-api-key；merge／pins.web 欄
  不觸發該規則＝關鍵字不中）＋017 quickstart `curl -u` 命令替換示例 ×1（curl-auth-user）；
  `deploy/secrets/*.txt.example` 零命中（22-byte 佔位、低熵不中）
- [x] T010 [US1] 新增 `.gitleaks.toml`（★必先於 T015 啟用 hook）：①DSN 自訂 `[[rules]]`
  （`id`＋`regex` 必填，涵蓋 postgres(ql)／redis／mysql 帳密 URL 樣式，補 `description`＋
  `keywords`）②依 T009 基線寫 per-rule allowlist——**每條必含 `condition = "AND"`**＋
  `paths`×`regexes`＋顯式 `regexTarget`，**嚴禁整檔放行**（漏 AND 退化為過寬放行且不報錯
  ＝本 schema 最大靜默失效點）③檔頭註記「僅用 gitleaks 子集欄位」（保雙向可攜）
  ——**實測（2026-07-28）**：`extend.useDefault=true` 落檔後五探針全過——①KEY=value 執行期
  假值 fixture exit 2（內建規則仍生效＝未被自訂 config 取代）②DSN fixture exit 2（命中
  `rev4-dsn-credential-url`）③SOPS 密文形 exit 0 ④玩具示例限 specs/*.md 放行、同形在根目錄
  檔 exit 2（allowlist AND 圈定生效）⑤帶 config 全歷史重掃 21→0 findings（基線全數圈定）
- [x] T011 [P] [US1] **TDD 紅**：`tools/secret-value-guard.py` 測試先行——內嵌
  `unittest.TestCase`（沿 018 慣例、無 pytest）：命中即擋／絕不輸出值本身／值缺席時 skip 不
  fail-closed／紅綠 self-test 防恆綠（紅樣本執行期字串串接構造、綠樣本含近似不命中與**邊界
  樣本**）／`purge_git_env` 隔離 git fixture。此時實作未寫、測試必紅
  ——**紅證據（2026-07-28）**：測試全寫、實作全 `raise NotImplementedError` 時實跑
  `test` 子命令＝`Ran 25 tests … FAILED (errors=21)`（其餘 4 案＝純 CLI usage 面、不依賴實作）
- [x] T012 [US1] **TDD 綠**：實作 `tools/secret-value-guard.py`——`main(argv)` 手寫
  `if cmd == "…"` 字面鏈＋`test` 子命令＋usage `exit 64`（★掃源正則只認此形）；讀
  `$SECRETS_DIR`（回退 `deploy/secrets`）現值比對 `git diff --cached`；**★同步登記進
  `tools/docs-sync.py` 的 `TOOLS_PY` 常數**（否則不入 tools-cli 真表、L19／L20 涵蓋不到）→
  `python3 tools/docs-sync.py generate` 重算真表
  ——**綠證據（2026-07-28）**：實作補齊後 `Ran 25 tests … OK`；staged 真實機密值活探針
  rc=1、訊息只有「檔案:行號＋機密名稱」、輸出經比對確認不含值原文；★TOOLS_PY 登記牽動
  docs-sync 同檔釘死斷言（名冊字面／真表 7 節／dry-run BASE 與分支 a）連動改、347 案仍全綠
  （名冊釘死＝設計上強迫登記時同步過賬，非 scope 外擅改）；generate 重算 tools-cli 真表新增
  secret-value-guard 節
  ——**quality 第 1 輪修正（2026-07-29）**：上列「真表新增節」當時未察抬頭已失真——名冊
  進第 5 支後，`gen_tools_cli` 寫死的敘述字面仍稱「六支（python 四支）」，生成檔遂抬頭說
  六支、實列七節而 347 案全綠（無斷言碰得到該字串）。修＝抬頭支數改由 rows 現算＋同案補
  字面斷言（實證：把抬頭改回寫死字面＝該案當場 FAIL）；同語意殘漏一併全掃 5 處
  （`compute_tools_cli`／`gen_tools_cli`／真表案名與 docstring／舊名禁令 docstring／bootstrap
  與 hook 兩案 docstring 的支數）。另修 `secret-value-guard.py` 兩缺陷：①self-test 邊界樣本
  原以 `MIN_SECRET_LEN` 自身構造＝套套邏輯（實測 MIN 改 2／21 皆全綠、生產面 check 零守門）
  → 樣本改字面 `EDGE_HIT`／`EDGE_SKIP` 雙記帳，MIN=2／4／16／21 逐一實跑 check 皆 exit 1；
  ②`find_hits` 把內容以「兩個加號」起頭的新增行誤判 diff 檔頭（報錯檔錯行）或整行漏掃
  （行號少算）→ 改以 hunk 邊界切開檔頭區與內容區。測試 25→29 案 OK、docs-sync 347 案零轉紅
  ——**quality 第 2 輪補掃（2026-07-29）**：同語意殘漏第 6 處＝`docs/ops/RUNBOOK.md` §12 的
  L19 條款速覽仍寫「四支 python 工具的舊名」（該節另三處支數已由 f88e579 修、獨漏此句）。
  修法不填新數字、改敘述為「python 工具名冊各支（＝真表 python 節逐支）」——支數寫死即
  下次名冊增減再度失真，改指向現算的真表才是 L-156 要的止血。機判：改後 lint 0 錯誤、
  `errata 四支` 於三件活手冊僅剩兩處、逐一核對為真——CLAUDE.md 該句述 018 之 B-111 確為四支
  改名、RUNBOOK 該句述 bootstrap 確跑四支 `test` 子命令（fork-delta-lint 無 test 子命令、
  self-test 隨每次實跑內建，故不計入該四支）；其餘命中全屬 018 過去式產物／事件源／機器生成
- [x] T013 [P] [US1] 新增 `.githooks/lib/scan-range.sh`＋`.githooks/pre-push`（contracts
  scan-gates §S3）：解析 pre-push stdin 四欄位；範圍推導＝一般更新用 `remote-oid..local-oid`／
  **新分支首推（remote-oid 全零）退階 `local-oid --not --remotes=origin`**／該退階無效時掃整條
  分支／刪除分支（local-oid 全零）跳過；命中即 exit 1
  ——**實測（2026-07-28）**：`sh -n` 語法綠；合成 stdin 冒煙——一般更新（HEAD~1..HEAD）exit 0、
  刪除分支行（local-oid 全零）靜默跳過 exit 0；scanner exit 2／其他非零分流訊息各自可辨識；
  三情境 bare-repo 全驗＝T017 ④
- [x] T014 [P] [US1] 新增 `.githooks-submodule/pre-commit` 與 `.githooks-submodule/pre-push`
  （兩源倉專用、**僅樣式掃描、零 python 依賴**）：**pre-commit 直接跑樣式掃描、不 source 任何
  lib**（`scan-range.sh` 只承載 pre-push 的 stdin 解析與範圍推導）；**pre-push 才**以
  `dirname "$0"` 自我定位後 source `../.githooks/lib/scan-range.sh`（**不硬編碼外層絕對路徑**）
  ——**實測（2026-07-28）**：`sh -n` 語法綠；★源倉樹無 `.gitleaks.toml`＝scanner 自動探索
  構不到，兩 hook 以 `dirname "$0"` 取外層檔顯式帶 `--config`（外層 hooksPath 絕對路徑保證
  `$0` 絕對）；實擋演練＝T017 ②④
- [x] T015 [US1] 改 `.githooks/pre-commit`：①掃描行置於 `docs-sync check` **之前**，指令＝
  `betterleaks git --pre-commit --staged --redact --verbose --exit-code 2`（★`--redact` 不可省
  ——預設 0＝明文噴進終端；★禁用 `protect`／`detect`；★原生二進位、禁容器）②exit code 分流
  （2＝命中／1＝掃描器自身異常、訊息可辨識並指向 bootstrap）③加值比對呼叫 ④註解**明確區分
  事件型（掃描：`--no-verify` 繞過即真進 git）與狀態型（docs-sync：只延後）** ⑤新工具加入條件
  觸發自測 `for` 清單
  ——**實測（2026-07-28）**：五要件全落；T009→T010→T015 硬序守住（allowlist 先行）；
  本 commit 起每筆 commit 實跑新 hook＝活自證（本次 commit 即首例、全鏈綠）
- [x] T016 [US1] 改 `tools/bootstrap`（沿既有編號段與 ok/warn/die 慣例）：①掃描器存在性與版本
  斷言（**die 級**、附安裝指引；防新機 commit 時 exit 127 猝死）②兩源倉 `core.hooksPath` 冪等
  佈署（絕對路徑指向外層 `.githooks-submodule`）＋讀值斷言（不符 die＋自癒指令）③段 5 自測
  清單加入新工具
  ——**實測（2026-07-28）**：全綠實跑（斷言過＋兩源倉 hooksPath 佈署讀值符＋四支自測綠＋
  重跑冪等）；否定測試——PATH 遮蔽（缺席）與 9.9.9 假版 shim 兩情境皆 die exit 2、附下載
  URL 樣式與 sha256sum -c 指引
- [x] T017 [US1] **S1／S2／S3 驗收**（quickstart 逐步）：8 格 fixture（四形 × `git add`+commit
  與 `git commit -a` 兩路徑、假值當場產生驗畢即刪）＋兩源倉各實擋一案＋例行簿記 commit 零誤擋
  ＋pre-push 三情境（一般／新分支全零 oid／刪除分支）＋**否定測試**：暫時拿掉 allowlist 的
  `condition = "AND"` 觀察放行過寬後復原
  ——**實測（2026-07-28）**：①8 格全符預期且兩路徑一致——KEY=value 擋（generic-api-key）／
  DSN 擋（rev4-dsn-credential-url）／裸值（jwt_secret 現值原文）擋（值比對層、輸出經機器
  比對不含值原文）／SOPS 密文形兩路徑均放行（拋棄 commit 驗畢 reset 丟棄）；②rust-api
  0.76s、base-web 1.76s 各實擋一案（generic-api-key）、husky/pnpm 零觸發、fixture 刪淨、
  兩 worktree status 零行、外層 pin 零動；③真實簿記 commit 零誤擋樣本＝**2 筆**（457482b、
  0c59450）——★原記「本單元 4 筆」為灌水：樣式與值比對兩層係於 457482b 才進
  `.githooks/pre-commit`（逐筆 `git show <c>:.githooks/pre-commit | grep -c` ＝0／0／1／1），
  其前兩筆（3220c1d、1111ac2）結構上不可能經過新閘、不得計入；SC-002 其餘樣本待全刀後續
  簿記 commit 累積（實質面已另證：帶 config 全歷史重掃 no leaks found）
  ＋合成 events.jsonl 三欄 40-hex append 探針兩層 exit 0；④pre-push 對 /tmp bare：新分支首推乾淨
  放行、一般更新乾淨放行、一般更新含 --no-verify 假機密 commit 擋（rc=1）、新分支首推含假
  機密走退階實掃亦擋、刪除分支跳過放行；sh -x 證退階 opts＝`--not --remotes=origin`、
  origin 零 ref 之再退階＝掃整條分支；⑤拿掉 DSN allowlist 之 condition 行→specs/*.md 內
  真值形 DSN 被誤放（exit 2→0）、復原後回擋（exit 2）＝OR 退化實證。測試 remote／分支／
  fixture 全數清除、**工作樹**收乾淨
  ——★**殘項（2026-07-29 spec review 抓出、待主線結清；原記「收乾淨」只涵蓋工作樹、不涵蓋
  物件庫）**：①裸值格 fixture 結構上必須用機密**現值原文**，該內容在 `git add` 當下即寫成外層
  `.git/objects` 的 unreachable loose blob——`8a183df0`（64 bytes＝`deploy/secrets/jwt_secret.txt`
  byte 級同值、mtime 2026-07-28 23:21:35 落在 T017 執行窗；同窗另有 7 筆 fixture blob）；
  `git rev-list --all --objects` 命中 0＝**未進版控歷史**（閘門有效），故只需 prune、不需改寫歷史。
  結清＝外層跑 `git prune --expire=now`（或 `git gc --prune=now`），機判＝其後
  `git cat-file -e 8a183df0` 必須 rc≠0；稽核法＝`git hash-object deploy/secrets/*` 與
  `git fsck --unreachable` 之 blob 集合取交集須為空。②quickstart S1 **收尾**須補「裸值格驗收後
  必 prune 外層物件庫並以 `cat-file -e` 反證」一步（屬裸值格驗收設計的固有副作用、非一次性
  疏忽；踩坑與防法已收錄 L-158）
  ——**主線結清（2026-07-29）**：①`git prune --expire=now` 實跑後 `git cat-file -e 8a183df0`
  rc=1、且 11 支現值檔 `git hash-object` 逐支 `cat-file -e` 全數失敗、`jwt_secret.txt` 完好
  64 bytes、工作樹零行；②quickstart S1 收尾補句已落。兩項機判全綠、殘項就此結清

## Phase 4: US2 — 機密以密文入版控＋可斷言的解密管線（P2）

**Goal**: 8 key 加密入版控（公鑰模型、加人零機密傳遞）＋fail-loud 解密管線。
**Independent Test**: spec US2——在現行落點不變的前提下即可完整驗證加密往返、斷言行為與守衛。
**依賴**: Phase 2（T007 定私鑰方式）。

- [x] T018 [US2] 新增 `deploy/sops.sh`（contracts secret-pipeline §P1 七要件）：digest 釘版常數
  ＝`ghcr.io/getsops/sops@sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`
  （★值依 T002 拍板之 sops 映像 tag〔research R7 當日值 v3.13.3-alpine〕；施工時複查該 digest
  仍指向拍板 tag；★registry 與 digest 必須成對）＋`-it` 條件化
  ＋**不轉發 `EDITOR`**＋顯式 `-e SOPS_AGE_KEY -e SOPS_AGE_KEY_FILE -e SOPS_AGE_KEY_CMD`＋
  掛載 `$PWD:/work -w /work` 與私鑰目錄唯讀；`chmod +x` 後 **`git update-index --chmod=+x`**
  （drvfs exec bit 不落 index）
  ——**實做（2026-07-29）**：七要件全落（digest 複查＝本機映像 `v3.13.3-alpine` 之 index digest
  逐字相符）；`-i -t` 條件＝stdin 是 tty（實測 stdout 重導向時 sops 提示與輸出同流＋CRLF、
  詳 T022 parser 註）；非互動 `--version` rc=0、非互動解密 rc=128 吵鬧失敗不 hang；
  `git ls-files -s` 驗 100755
- [x] T019 [US2] 產正式金鑰（age 二進位已由 T040 取得、此處沿用；★版本＝T002 拍板值）：
  ★**完整性比對值須取該版本 release API 的 `digest` 欄位現查**——research R9 所記 v1.3.1 之
  sha256 僅為研究當日值、**版本一變即作廢**。原取得步驟保留備查：自官方 GitHub release 下載
  `age-v<VER>-linux-amd64.tar.gz`（★**無 checksums 檔**——完整性以 release API 的 `digest`
  欄位比對 `sha256sum`）→ 依 T007 定案產鑰（B′：`age-keygen | age -p`／退路 A：明文＋
  `chmod 600`）→ `xxd` 驗尾端無 CR →（★時點勘誤 2026-07-29：二進位**不於本任務刪除**——
  T033 產演練金鑰仍需 `age-keygen`、清理統一由 T038 收刀終驗承接）；以 `age-keygen -y` 取
  recipient 公鑰
  ——★**儀式拍板＝C 案**（拍板全文、誠實登記與收刀義務見 ADR
  `docs/arc42/decisions/0080-age-identity-bprime-secretsdir-solution2.md`「決策」節第 5 點
  ＝唯一權威落點）：**本任務只產「暫代正式鑰」**（agent 拋棄式 passphrase、B′ 形制、pty
  驅動全自動）；真鑰產製與暫代鑰撤銷／輪替屬**收刀 finishing 義務**、不在本任務範圍
  ——**實做（2026-07-29）**：C 案暫代正式鑰產訖——pty 驅動 `age-keygen | age -p`（沿用 T040
  二進位）、拋棄式 passphrase 執行期構造（已依 C 案誠實登記於單元回報、視同已洩露）；
  `~/.config/sops/age/keys.txt` 371 bytes、開頭 `age-encryption.org/v1`、`xxd` 尾 byte 0xb4
  無 CR、目錄 700 檔 600；公鑰取產出時 public key 行（回報 interim_pubkey 欄）；echo 回顯
  檢查＝pty 流不含 passphrase 原文
- [x] T020 [US2] 新增 `.sops.yaml`（contracts §P2 五條）：單一 `creation_rules`、
  `path_regex` **錨定式**（★比對用 `MatchString`＝非錨定子字串命中）、`age:` 用 YAML 清單形、
  **不設六個範圍選項任一**（預設 `unencrypted_suffix="_unencrypted"`＝全加密）；寫完**驗證
  規則確實命中**目標檔
  ——**實測（2026-07-29）**：命中驗證＝`--filename-override deploy/secrets.dev.enc.yaml`
  不帶 `--age` 加密成功且 metadata recipient 逐字＝T019 公鑰（規則供鑰自證）；錨定否定
  探針三案（前綴 x、後綴 .bak、點未跳脫形 secretsXdev）全數 rc=1
  `no matching creation rules found`
- [x] T021 [US2] 建 `deploy/secrets.dev.enc.yaml`（恰 8 key＝7 leaf＋`alert_webhook_url`）：
  自現值組明文 YAML（**中間產物限 repo 內 gitignored 目錄、用完即刪、不得 staged**；wrapper
  只掛載 `$PWD`）→ 經 wrapper 加密 → 驗 `git diff` 呈現 **key 名明文＋值全 `ENC[`**、key 數＝8。
  ★`alert_webhook_url` **如實搬移現值**（現值 39 bytes 為 user 已填真值；`--force` 不重置、
  **絕不以刪檔為手段**）；composite 不進（由既有腳本重生）
  ——**實測（2026-07-29）**：名單現場核對＝README 對照表與 generate-secrets.sh 之 11 支
  去除 3 composite（database_url／redis_url／reaper_database_url）＝8；明文組檔於
  `tmp/019-us2-plain/`（gitignored、`git check-ignore` 證）、pyyaml round-trip byte 級斷言
  全過且 8 值皆無引號純量形、驗畢即刪＋`git status` 零 staged；`grep -cE 'key: ENC\[' `＝8、
  key 名明文 8 支逐字符合；`_unencrypted` 唯一命中＝sops metadata 之 `unencrypted_suffix`
  記錄行、非 key 名；alert_webhook_url 依現值 sha256 基準（9848…dd3e）如實搬移、
  byte 級一致證據收 T023 往返驗
- [x] T022 [US2] 新增 `deploy/decrypt-secrets.sh`（contracts §P4 五要求）：tty 守衛（非互動
  **吵鬧失敗**、不得 hang）→ **`source .env`（存在時）、`SECRETS_DIR` 未設時回退
  `deploy/secrets`**（與 T012 值比對工具同一回退口徑；★`.env` 於 T024 才建立，此回退是 US2
  能在 US3 之前獨立驗證的前提）→ `mkdir -p`＋`chmod 700`**自建 0700 子目錄**
  （`/dev/shm` 為 world-writable；★重拍 2026-07-29、#11 反轉後：落點改 ext4
  `$HOME/.cache`〔`drwx------`、非 world-writable〕，**自建 0700 子目錄之要求不變**——理由改為
  **縱深防禦、與落點無關**，見 ADR 0080 決策 4）→ wrapper 收 stdout（`umask 077`、**不用 `--output`／`-i`**
  避免 root 產物）→ **key 數與名稱斷言、不符零寫入＋非零退出＋指名缺哪個 key** → 逐檔
  `printf '%s'`（無尾端換行）＋`chmod 644` → **現值 ≠ 解密值則另存 `.txt.new` 不覆寫**
  ——**實做（2026-07-29）**：契約全落＋兩個實測接地——①單次 `sops -d`（B′ 單 recipient
  恰 1 次提示、pty 實測 fed=1）收全 YAML 至 0700 暫存目錄（trap 即刪；★落點於 quality
  第 2 輪自 repo 內 `tmp/` 改至 `$XDG_CACHE_HOME`〔回退 `$HOME/.cache`〕，見下方第 2 輪修復記）；
  ②★容器 pty 單流雜訊實測＝提示行＋ANSI 清行序列（ESC[F ESC[K）黏在首資料行
  ＋全輸出 CRLF——拆 key 前先 `tr '\r' '\n'`＋剝 CSI 序列、只認 `key: value` 行（提示行天然
  被濾）；權限自證 drvfs（v9fs）分支＝WARN 不中止（chmod 結構性 no-op、US3 遷移消滅）、
  其他 fs 不為 700＝FAIL。正向全跑 rc=0、8 支 WRITTEN、11 支 sha256 前後全 OK（含 3 composite
  未動）；非互動 rc=1 即紅不 hang；exec bit `git ls-files -s`＝100755
  ——**quality 第 1 輪 blocker 修復（2026-07-29）**：①補**非裸量純量斷言**（值首字元落 `" ' | >` 即 FAIL 指名、零寫入）——原逐行拆 key 只對裸量正確，sops 對空值吐 `""`、對含「冒號空白」吐單引號包裹，兩者都被逐字寫進機密檔且「值為空」斷言被架空（真容器對照組實測：修正前 rc=0 且 jwt_secret.txt=2 byte／alert_webhook_url.txt 多 2 byte 引號；修正後 rc=1 零寫入指名）；②失敗分支**濾除資料行後才倒 sops 輸出**——容器 pty 單流使捕捉檔同時承載 stdout 與 stderr，「已 Emit 後才失敗」即整份明文上終端（stub 實測：修正前 8 值全印、修正後 0 明文＋濾除行數計數，sops 正常錯誤診斷完整保留）。回歸：全裸量案 8 支 byte 數與 sha256 前 8 碼前後一致；現行 8 值經性質檢查全屬裸量、不受新斷言影響。詳 L-170
  ——**quality 第 2 輪 blocker 修復（2026-07-29）**：**明文暫存落點遷出 repo 內 `tmp/`**——
  原以 `mktemp -d tmp/decrypt-secrets.XXXXXX` 把「8 支完整明文」落在 /mnt/d（v9fs：`umask 077`
  與 `chmod` 皆結構性 no-op，實跑 `ls -ld tmp`＝`drwxrwxrwx`、Windows 側可見），與同檔上方
  為 `SECRETS_DIR` 承認並 WARN 的性質同因，且**不隨 US3 落點遷移消失**（T024~T030 無一涵蓋此
  落點）＝FR-021／SC-005 要消滅的暴露面。改落 `${XDG_CACHE_HOME:-$HOME/.cache}` 下之
  `rev4-decrypt.XXXXXX`（0700），並補**落點性質斷言**（fs 為 `v9fs` 或 mode≠700 即 FAIL＋處置
  指引；斷言**早於** `sops` 呼叫＝不合格時零明文產生）。可行性依據＝此檔由 host shell 重導向
  產生、不進容器，contracts §P4「合併衝突」列之「暫存明文必須落 repo 內（wrapper 只掛載
  `$PWD`）」只約束**要餵回 sops 加密**的輸入檔，不約束 host 收的輸出。隔離沙箱機判（ext4、
  stub `sops.sh` 餵 8 支假值＋pty，全程未觸真機密與 repo 工作樹；落點以 stub 內
  `exec 9>&1`＋`readlink -f /proc/self/fd/9` 探得）：對照組（`git show HEAD:` 版）RAW＝
  `<repo>/tmp/decrypt-secrets.*/raw.out`；修正後 RAW＝`$HOME/.cache/rev4-decrypt.*/raw.out`、
  沙箱 repo 內**未生成 `tmp/`**、離場零殘留；否定案（`XDG_CACHE_HOME` 指 /mnt/d 路徑）rc=1、
  stub `sops` **未被呼叫**、零檔寫出；SIGKILL 硬砍殘留案＝殘留目錄落 `$HOME/.cache`、
  `stat -c %a`＝700（原版則為 /mnt/d 之 777）。回歸：修正前後 8 支寫出檔 sha256 前 8 碼、
  byte 數、mode 644 全等；`bash -n`＋`shellcheck -S warning` 全綠；repo 內
  `deploy/secrets/alert_webhook_url.txt` sha256 仍 9848…（39 bytes、未動）。詳 L-171
- [x] T023 [US2] **S4／S5 驗收**：加解密最小往返（#1）＋加密檔形制三條＋五要求逐條否定測試
  （刪 key→零寫入報錯｜構造 `alert_webhook_url` 差異→產 `.new` 原檔不變｜`xxd` 驗無 `0a`
  無 `0d`｜leaf 與 composite 內嵌值 byte 數一致｜owner 非 `root:root`｜非互動呼叫吵鬧失敗）；
  **否定測試**：故意以錯誤副檔名順序加密一次觀察退化為整檔加密後刪除實驗檔；
  ★**重拍連帶**（2026-07-29、#11 反轉後；contracts §P4.6）：另**構造權限非 0700 的父目錄**
  （如 `chmod 755` 的暫存父目錄）、把 `SECRETS_DIR` 指入其下跑解密，`stat -c %a` 子目錄
  **仍必為 `700`**（＝「0700 子目錄要求＝縱深防禦、與落點無關」的機判證據；此項**不可**落在
  `quickstart.md` §S6／T030——解法 2 之下 `$HOME/.cache` 本身即 `drwx------`，權限非 0700 的
  父目錄只能在解密管線驗收面刻意構造）；驗完刪除暫存父目錄。
  ★**施工時同步補列**：`quickstart.md` §S5 表現為六列、**尚未含本項**（contracts §P4.6 已註明
  以本行為唯一權威落點）——本任務施工時把本項補成 §S5 第七列，使劇本與 T023 一致；未補列前
  照 §S5 逐列核對者必漏跑本項
  ——**實測（2026-07-29、全數過；解密互動一律 pty 盲餵暫代 passphrase）**：
  ①往返：管線 rc=0、8 支 WRITTEN、11 支 sha256 前後全 OK（#1 還原一致＋SC-007）；
  ②形制：`git diff`（加入 enc 之 commit）新增行 `key: ENC[AES256_GCM` 恰 8、key 名明文 8 支；
  ③明文中間產物已刪＋`git status`／`git diff --cached` 零殘留；④否定逐條——刪 key（解密→
  濾掉 jwt_secret→重加密置換）→rc=1 指名 `jwt_secret`＋11 支 sha256 全未動（零寫入）＋
  `git checkout --` 復原；alert_webhook_url 差異（暫改 enc 內值）→7 支 WRITTEN＋
  `alert_webhook_url.txt.new`（內容 sha256＝構造值）＋原檔 sha256 前中後三查皆 9848…dd3e
  39 bytes（SC-007）、驗完 rm .new＋checkout 復原；`xxd` 8 支末 byte 皆非 0a/0d；
  leaf↔composite 內嵌值 byte 級比對 3 對全 OK；owner 全 1000:1000＝id -u/-g 非 root；
  非互動 rc=1 即紅不 hang；★P4.6 新否定＝755 父目錄（ext4）下 SECRETS_DIR 指入→子目錄
  `stat -c %a`＝700、8 支 644 全寫出、驗完刪暫存父目錄；⑤錯誤副檔名 `secrets.env.enc`
  →binary store 退化＝單一 `data: ENC[` 密文塊、key 名不可見（帶 `--config` 臨時 catch-all
  規則檔實驗、實驗檔已刪；★`--age` 不能繞過 config 規則比對＝L-168）；⑥§S5 第七列（P4.6）
  已補列。全程 fed=1（單 recipient 恰 1 次提示、與閘 #3 基線一致）
  ——**補測（2026-07-29、spec review 第 1 輪修後）**：原 `.new` 為 `chmod 600`，而腳本 WARN
  自陳的補救＝`mv .new` 蓋回（同 fs＝rename、mode 原樣保留）→ 落點檔終值變 600、違反
  P4.7／FR-022 且只在開 obs／metrics 軌時才炸。已改 `.new` 一併 644；隔離 ext4 沙箱
  （`$HOME/.cache/rev4-019-tmp/verify-p47`、stub `sops.sh` 餵 8 key＋pty，全程未觸 repo 工作樹
  與 `deploy/secrets/`）機判：修前 `.new`＝600、mv 後落點 600（複現）；修後 8 支＋`.new` 皆 644、
  mv 後落點 644、`xxd` 末 byte 仍非 0a／0d、原檔於 mv 前未被覆寫（P4.5 不變）；
  `bash -n`＋`shellcheck -S warning` 全綠。repo 內 `deploy/secrets/alert_webhook_url.txt`
  sha256 仍 9848…dd3e（未動）
  ——**補測（2026-07-29、quality 第 2 輪修後）**：新增第八列驗收＝**明文暫存落點**
  （FR-021／SC-005）——正向 RAW 落 `$XDG_CACHE_HOME`／`$HOME/.cache` 之 0700 目錄且離場清除；
  否定＝`XDG_CACHE_HOME` 指 /mnt/d 路徑 → rc=1、`sops` 未被呼叫、零檔寫出。實測結果詳 T022
  第 2 輪修復記；`quickstart.md` §S5 表已同步補為八列

## Phase 5: US3 — 明文離開 /mnt/d（SECRETS_DIR 遷移）（P3）

**Goal**: 明文自 9p（權限恆 777）遷至 tmpfs；compose 與三腳本經單一事實來源取得落點。
★重拍（2026-07-29、#11 反轉後）：遷入落點改**解法 2＝`$HOME/.cache/rev4-secrets`（ext4 持久）**、
非 tmpfs（落點拍板值＝ADR 0080「決策」節第 2 點；`.env` 落地見 T024）；接線與五步遷移程序不變。
**Independent Test**: spec US3——遷移五步＋落點驗證＋觀測軌全開讀取，全程機判。
**依賴**: Phase 2（T004／T005）＋US2（T022 解密管線）。

- [x] T024 [US3] 新增 `.env.example`（tracked）＋`tools/bootstrap` 代勞產生 `.env`
  （gitignored）：`SECRETS_DIR` 依 T005 結果定值（拍板值 `/dev/shm/rev4-secrets`
  ★重拍（2026-07-29、#11 反轉後）：**重拍值＝`$HOME/.cache/rev4-secrets`、原 2′ 拍板值作廢**、
  詳 ADR 0080「決策」節第 2 點）；
  ★**退路分支（機械化 #3 之「自動生效」）**：若 T007 判 #3 失敗，`SECRETS_DIR` 改寫
  **`$HOME/.cache/rev4-secrets`**（＝解法 2、ext4 持久；**寫入形式與 2′ 完全相同、只換值**、
  compose 與腳本零改動）；`.gitignore` 既有規則已覆蓋、無須加行
  ——★**重拍後本分支已成無作用**：主值即為 `$HOME/.cache/rev4-secrets`，退路只剩私鑰維度
  （方式 A）、SECRETS_DIR 不再有降階動作（ADR 0080 決策 3）；條款留存供金鑰輪替等再驗情境
  ——**實測（2026-07-29）**：`.env.example` 落檔（產檔約束三條：單行 KEY=VALUE／絕對路徑
  字面〔compose 讀 .env 不做 shell 展開〕／值不含空白與 shell 元字元）；`git check-ignore -v
  .env`＝`.gitignore:60` 命中（既有規則覆蓋、零加行）；bootstrap 實跑＝缺失時代勞產生
  `SECRETS_DIR=/home/anew/.cache/rev4-secrets`（shell 側展開後寫入）、已存在時不覆寫只讀值
  斷言（T039 重跑實證）
- [x] T025 [US3] 三腳本 SECRETS_DIR 同步改（★**三處必須同刀齊改**，任一未改即該處無條件賦值
  靜默吃掉外部值）：`deploy/generate-secrets.sh`（`SECRETS_DIR` 賦值行）／
  `deploy/preflight-secrets.sh`（同）／`deploy/setup-reaper-role.sh`（`PW_FILE` 賦值行）
  ——改帶預設展開＋各自 `source .env`（存在時）
  ——**實測（2026-07-29、與 T026 同一 commit 落地）**：三處改帶預設展開（未設回退
  deploy/secrets）；★.env 讀取**不整檔 source**、改四腳本（含 decrypt）同口徑只嚴格解析
  `SECRETS_DIR=` 一行（U3 遺留 advisory 四：白名單字元類拒空白／shell 元字元、絕對路徑字面
  斷言、環境變數優先＝compose 口徑）；機判＝元字元值與相對路徑值皆 rc=1 拒用（含 `$()`
  探針值未被執行）、env var 蓋過 .env、`bash -n`＋`shellcheck -S warning` 全綠
- [x] T026 [US3] `deploy/generate-secrets.sh` 功能改：加 `--compose-only` 旗標（缺 leaf
  **報錯退出、不生成**——防靜默造新亂數）＋權限終值改 **644**（原 600 會使三個非 root service
  在開 obs／metrics 軌時 Permission denied）；★`printf '%s'` 寫檔形**不得改為 echo**
  ——**實測（2026-07-29、ext4 沙箱假值 fixture）**：`--compose-only` 斷言 8 支來源檔
  （7 leaf＋alert_webhook_url）在位非空——全在位 rc=0 只重組 3 composite（leaf 記 PRESENT
  不動）、刪 jwt_secret 後 rc=1 指名且**未代生成**（刪檔仍缺＝零生成實證）；權限終值
  目錄 700＋檔 644（stat 實測）；printf 寫檔形未動；未知旗標 exit 64
- [x] T027 [US3] `deploy/preflight-secrets.sh` 增強：①CR 偵測護欄（命中即 FAIL）②composite↔
  leaf 一致性檢查（複用既有期望值組合式；防「塞入密碼已過期的 `database_url` 也回 OK」）
  ③成功句改**陣列長度插值**（現硬編碼「十一個」、免每刀追改）
  ——**實測（2026-07-29、同沙箱）**：①注入 CR → rc=1 指名 captcha_secret.txt；②尾附
  drift 於 database_url → rc=1 指名＋指路 `--compose-only` 重組、重組後復綠；③成功句
  `${#REQUIRED[@]}` 插值實印「11 個…（落點路徑；CR 零命中、composite 一致）」；
  訊息全程只指名檔案、零值輸出
- [x] T028 [P] [US3] `docker-compose.yml` 頂層 `secrets:` 10 條目改帶預設值變數展開（未設變數
  時回退專案相對路徑）；★`reaper_password` 不進 compose 是設計（僅 setup-reaper-role 直讀）、
  **勿誤補**；dev 與 example 兩 compose 檔零改動
  ——**實測（2026-07-29）**：10 條全改 `${SECRETS_DIR:-./deploy/secrets}/…`；無 .env 時
  `config` 解析回 repo 內 deploy/secrets（#4）、.env 在位時三 profile 全開 config 之 10 條
  file 全解析至 `/home/anew/.cache/rev4-secrets`；reaper_password 未誤補、dev／example
  兩檔 git diff 零行
- [x] T029 [P] [US3] `tools/bootstrap` secrets 體檢 glob 隨 SECRETS_DIR；**三級口徑明確落地**
  （contracts §P5.4、scan-gates §S4）：`.env` 缺失→**代勞產生（自癒、不中止）**／掃描器與
  hooksPath 斷言→**die 級**／機密實值缺檔→**維持 warn 級**（既有慣例、實值人對人交接、
  bootstrap 不生成）；★上機前的 fail-loud 由 preflight 承載（T027），bootstrap 不重複把關
  ——**實測（2026-07-29）**：.env 缺失實跑＝代勞產生＋繼續跑（非 die）；體檢名冊仍取 repo 內
  `deploy/secrets/*.example`、實值在位檢查隨 SECRETS_DIR；T039 清空落點實跑＝warn 級列 11 缺檔
  ＋rc=0（重建指引改指 decrypt＋--compose-only）；掃描器／hooksPath 斷言維持 die 級未動
- [x] T030 [US3] **遷移執行＋S6／S7 驗收**：依 contracts §P6 五步（`down`→decrypt→設值
  `up -d`→**逐容器 `docker inspect` 驗來源皆非 `/mnt/d`**→**確認後才**刪舊落點）；＋未設變數時
  `docker compose config` 回退驗證（#4）＋`--profile obs --profile metrics` 全開驗三個非 root
  service（472／65534／59000）讀得到且健康＋**否定測試**：跳過 `down` 觀察 `Starting` 而非
  `Recreated`（假性完成信號）後復原重做；完成判準＝`/mnt/d` 全樹零明文機密檔
  ——**實測（2026-07-29、全過；步驟 0 先記 11 支 sha256 前 8 碼＋byte 數基準）**：
  ①三 profile 旗標 down（僅 rev4；rev3 12 支容器 ID 集合前後 diff 零行）；②pty 驅動 decrypt
  8 支 WRITTEN＋`--compose-only` 重組 3＋preflight 綠（fed=1、echo_leak=0）；③up -d --wait
  6 業務件全 Created→Healthy；④**逐容器逐 mount 列證**：14 容器（含 obs／metrics）之 12 筆
  `/run/secrets/*` 掛載 Source 經 `readlink -f` **物理化**後全落 `/home/anew/.cache/
  rev4-secrets`、零 `/mnt/d`（★字面 grep 會假綠——遷移前 Source 即顯示 symlink 邏輯路徑
  `/home/anew/x_Project/...`、物理實為 /mnt/d，物理化斷言之因＝L-172）；⑤刪前終核新落點
  11/11 sha256 與基準全符**後才** `rm deploy/secrets/*.txt`（.example＋README 保留、
  git status 零行）。#4 回退：無 .env 與 .env 暫移兩情境 config 均解析回 deploy/secrets、
  驗畢復原。S7：obs＋metrics 全開，grafana(472)／postgres-exporter(65534)／redis-exporter
  (59000) 容器內 id -u 實證＋讀 `/run/secrets/*` 之 sha256 前 8 碼與基準全符（a665975d／
  98483895／e68962c7／dcd27828）、grafana /api/health database ok、prometheus 查
  pg_up=1／redis_up=1（兩 exporter 以 644 檔真連線成功＝644 終值真驗收）。否定測試：跳過
  down 直接改值 up -d → 全程零 `Recreated`、rust-api 掛載仍指舊路徑（假性完成實證）→
  復原後照 ①~⑤ 正確順序重做。完成判準：`/mnt/d/AnewSpaces/x_Project` 全樹（含 .git 物件庫、
  fork 源倉、rev3 目錄）以 7 種基準 byte 數預篩 7890 檔、sha256 與 11 支基準交集**零命中**
  （全碟其餘目錄與本 repo 機密值無接觸面、範圍判定記於單元回報）。★U3 遺留 advisory 一：
  新落點版控面外機判＝`git check-ignore` 與 `git ls-files --error-unmatch` 對新落點路徑皆
  rc=128 fatal outside repository＋物理路徑非 toplevel 前綴＋`git status --porcelain` 零行
- [x] T039 [US3] **SC-003 後半：乾淨重建全鏈驗收**（quickstart S4 後半；★編號為後補、執行序
  緊接 T030 之後、見 Dependencies）：清空 `$SECRETS_DIR`
  模擬全新環境 → `tools/bootstrap` → `deploy/decrypt-secrets.sh` → `generate-secrets.sh
  --compose-only`（重組 3 composite）→ `preflight-secrets.sh` → `docker compose up -d` →
  **驗 11 支機密檔全數重建、preflight 全綠、服務全健康、全程零人工傳遞任何機密值**；
  ＋**US3 情境 5 否定測試**：清空落點後**不跑解密**直接 preflight → 必須明確紅並指名缺檔
  （而非服務靜默啟動失敗）
  ——**實測（2026-07-29、全過）**：`rm -rf $SECRETS_DIR` → bootstrap（.env 不覆寫、讀值斷言
  綠；缺 11 實值＝warn 級 rc=0）→ **情境 5 否定**：不解密直接 preflight＝rc=1 明確紅列名
  11 缺檔＋重建指引 → pty decrypt 8 支＋--compose-only 重組 3＋preflight 綠 → up：11/11
  sha256＋byte 數與基準全符（**alert_webhook_url 98483895/39 bytes＝SC-007**）、全程僅憑
  repo 內密文＋暫代私鑰、零人工傳遞機密值。★踩坑：清空前已存在的容器 bind 舊 inode——
  running 件無感、**Exited 的 migrate 下次 up 重 start 即 mount error**（Docker Desktop
  bind 快照隨舊 inode 消失；`up -d` 對 config 未變者只 Start 不自癒）＝§P6 否定契約實證形；
  處置＝6 業務件＋8 觀測件 `up -d --force-recreate` 重掛新 inode 後全綠（migrate Exited 0、
  5 業務件 healthy、grafana ok／pg_up=1／redis_up=1），坑與防法＝L-173。收尾：8 觀測件
  指名 stop 收回 opt-in（絕不 down）、rev3 全程零波及

## Phase 6: US4 — 營運程序落地（P4）

**Goal**: 加人／撤銷／輪替／遺失／開機儀式可依 RUNBOOK 執行；§7 輪替表增補 re-encrypt 步驟。
**Independent Test**: spec US4——以演練用第二把金鑰跑完整撤銷演練＋輪替一支機密驗證加密檔同步。
**依賴**: US2（資產存在）。

- [ ] T031 [US4] `docs/ops/RUNBOOK.md` 新增 SOPS 營運段群：編輯機密（`sops edit`→decrypt→
  `up -d --force-recreate`、**不用 `restart`**）／加人與換機四步（零機密傳遞；★「換機
  `git pull` 即可用」是錯的）／撤銷四步（★`rotate -i --rm-age` **逐檔一行**——`rotate` 只吃
  第一個位置參數、其餘靜默略過且 exit code 不變）／金鑰與 passphrase 遺失（★備份含 passphrase
  本身）／開機儀式（2′ 下每次開機重跑解密；★重拍（2026-07-29）：此段改寫為**解法 2 常駐語意
  ——毋需每開機重解密**、內容改述為「**落點缺檔時的補救步驟**」〔快取被清／新機／手動刪落點
  時＝跑解密儀式〕、詳 ADR 0080「決策」節第 2 點）／★**GPG_TTY 前置**（T006 移交：`GPG_TTY`
  屬 session 環境變數、非 `gpg-agent.conf` 合法選項——B′ 互動解密前置＝session
  `export GPG_TTY=$(tty)`、寫進 SOPS 營運段）／合併衝突（暫存必落 repo 內、重加密後核對
  `sops.age` 清單）／災復備註（g 不升格之代償）／工具版本記錄欄（T002 三支拍板值）／
  ★**SSH identity 禁令與尋鑰來源注意事項**（FR-012 的 RUNBOOK 面落點：sops 尋鑰為**聯集載入**
  且會零設定自動探測 `~/.ssh/id_ed25519` 與 `id_rsa`——禁以 SSH 金鑰充當 identity；切換取鑰
  來源後必跑 #10 反向驗證）／★**#13 passphrase 提示次數**：只記 T033 實測值與量測條件、
  **不寫死次數**
- [ ] T032 [P] [US4] `docs/ops/RUNBOOK.md` 既有節連帶：**§7 輪替表增補「輪替後 re-encrypt 回
  加密檔」步驟**（漏此步→輪替值與加密檔脫鉤、下次 decrypt 觸發 `.new` 守衛）＋§4 人工必填
  清單增 `.wslconfig`／BitLocker 確認項＋§12 工具鏈速查增 `deploy/sops.sh` 與
  `deploy/decrypt-secrets.sh`
- [ ] T033 [US4] **S8 撤銷演練＋反向驗證**：產演練用第二把金鑰（★age 沿用 T040 暫存二進位、
  勿重複下載）→加入→`updatekeys -y`→確認可解
  →撤銷四步→**#7 五準則逐條驗**（核心＝否定測試：舊 `enc:` stanza 貼回新檔跑原廠解密**必須
  失敗於 MAC 驗證**；rotate 前後值密文必變；recipient 清單前後不含被撤銷者；人工確認 dev 檔
  無 prod 級機密）→**#10 反向驗證**（identity 移走＋`unset` 相關變數後解密**必須失敗**）→
  ★順序陷阱驗證（故意先 rotate 後 updatekeys 觀察中間狀態）→★**#13 實測**：趁雙 recipient 在場
  量測 passphrase 提示次數並記錄（FR-024 後半；RUNBOOK 只記實測值與量測條件、**不寫死次數**）
  →演練金鑰移除、痕跡不入版控（C 案下本演練全自動——暫代鑰＝當前正式鑰、agent 知其
  passphrase；#13 以 pty 驅動量測）

## Phase 7: US5 — 治理落檔（P5）

**Goal**: 拍板全數落 ADR；遞延項登記 BACKLOG；指路文字連帶更新。
**Independent Test**: spec US5——對照綱要逐支核 ADR 欄位；BACKLOG／NOTES／指路文字逐處核。
**依賴**: 前四者結果（實測欄位、驗收證據）。

- [ ] T034 [US5] ADR 5 支落 `docs/arc42/decisions/`（0079 起、一決策一檔、綱要＝brainstorm §9）：
  **A** 選型 SOPS+age（四理由＋誠實收窄＋零維運硬約束＋digest 釘版＋**cosign 不啟用之誠實
  登記**＋age 取得路徑）／**B** 私鑰 B′×SECRETS_DIR **解法 2**（★重拍 2026-07-29、#11 反轉後：
  原綱要之「SECRETS_DIR 2′」與「**tmpfs swap 殘餘風險誠實登記**」兩項**隨 2′ 作廢、不得寫回
  正式 ADR**；改為 **ext4 at-rest 殘餘風險誠實登記**〔明文長駐 `ext4.vhdx`＋補償三面〕之總表化。
  施工標的＝**既存 draft `docs/arc42/decisions/0080-age-identity-bprime-secretsdir-solution2.md`
  完稿並轉 accepted**、非另立新檔）（自洽論證＋退路預拍〔重拍後僅退方式 A〕＋#11 反轉條件與
  反轉實測＋**SSH identity 禁令**＋passphrase 政策〔diceware≥6＋離線備份義務〕
  ＋**產鑰儀式 C 案拍板**〔已落「決策」節第 5 點、本 ADR 為其唯一權威落點：暫代鑰 passphrase
  視同已洩露之登記，與收刀期真鑰產製／撤銷四步／7 支 leaf 輪替之硬性義務〕；T008 實測欄
  已於 Phase 2〔Foundational〕併入）／
  **C** 加密資產形狀（dev 單檔 8 key／prod 不建含目標形狀備忘／`ca.key` 不進含重評條件／
  命名紅線／不設範圍選項）／**D** 掃描三層防線定位（事件型×狀態型×確定性互補；三 repo 覆蓋；
  base-web `--no-verify` 慣例廢止；**compose 向後相容取捨之誠實登記**）／**E** 團隊組成前提
  （將來可能有非工程師→兩層架構待觸發決定）＋問題 B 四條件延後登記
- [ ] T035 [P] [US5] `docs/ops/BACKLOG.md` 登記 B-115 prod 機密分層遞延包（prod 加密檔＋
  #5／#6 結構性不可測驗收＋CI 側保護；掛 prod 部署刀群）＋`docs/ops/NOTES.md` 同步 base-web
  `--no-verify` 慣例廢止（repo 文件不引用 per-machine memory 路徑）
- [ ] T036 [US5] `deploy/secrets` 命中逐檔判定（**以現場 `git grep` 為準、不以靜態數字為驗收
  基準**）：程序性引用逐檔改（清單＝research R18 表；★**排除 `docs/arc42/ARCHITECTURE.md`**
  ——該檔屬活書 as-built、**歸收刀簿記 commit、不在本 feature branch 內改**〔檔頭宣告＋
  docs-sync L6(b) 閘〕）／歷史文件不改／生成物由
  `python3 tools/docs-sync.py generate` 重算；★`deploy/secrets/README.md` 四處描述對齊實際行為
  （預檢語意／`--force` 語意／chmod 注記／機密對照表）——該檔是唯一向 user 說明 secrets 程序的
  人寫文件、失真即誤導；順帶勘誤 `.gitignore` 的 `.json` 規則註解（與現行 compose 形不符）

## Phase 8: Polish & Cross-Cutting

- [ ] T037 [P] **S9 秒級量測**（SC-009）：★**量法依 L-155 硬性規定**——**以 `perf_counter`
  直接包兩段（掃描器呼叫／值比對工具）各自連跑數次取中位數**，**絕不可用整鏈 `time` 前後差量**
  （drvfs 牆鐘變異 ±1.5s 大於被測成本、018 U2 曾量出負值）；T001 整鏈基線僅供數量級粗判。
  ★**機判門檻（出處 SC-009）：兩段合計中位數 ≤5s；值比對工具自測增量 ≤3s**。記「純碼 commit」
  與「治理檔 commit」兩情境；超標則記錄成本結構並掛 BACKLOG（比照 018 SC-008 處置）
- [ ] T038 **S10 治理完備＋收刀前終驗**：quickstart S1~S10 全機判單通＋SC-001~010 逐條勾稽；
  `python3 tools/docs-sync.py generate`＋`check`＋`lint` 全綠、工作樹收斂；ADR 5 支轉 accepted
  （含三閘實測欄）；踩坑逐筆 append `docs/ops/LESSONS.md`；★清理 019 暫存
  `$HOME/.cache/rev4-019-tmp/`（age 二進位＋tarball＋release-api.json——T040 產出、
  T007／T019／T033 共用之**唯一清理點**；清後 `ls` 反證不存在）

## Dependencies

```
T001 → T002 → T003
     ├─→ [US1（MVP、不依賴 Phase 2）: T009 → T010 → T011 → T012 → T013(P)/T014(P) → T015 → T016 → T017]
     └─→ [Foundational: T004 → T005 → T006(P) → T040 → T007 → T008]
                                                    ↓
                        [US2: T018 → T019 → T020 → T021 → T022 → T023]
                                                    ↓
                        [US3: T024 → T025 → T026 → T027 → T028(P)/T029(P) → T030 → T039]
                                                    ↓
                        [US4: T031 → T032(P) → T033]
                                                    ↓
                        [US5: T034 → T035(P) → T036]  →  [Polish: T037(P) → T038]
                                                    ↑
   US1 支線 T017 ───────────────────────────────────┘（US5 之 ADR D 需 US1 掃描防線實證；
                                                       T038 收刀終驗需 S1~S3 已通過）
```

- **US1＝MVP 且與 Foundational 正交**：掃描防線零 SOPS 依賴，可先行或與 Phase 2 並行。
- **T009 → T010 → T015 為硬序**：基線重建 → allowlist 落檔 → **才**啟用 hook。次序顛倒＝
  第一個被擋的是自己人的簿記 commit，且會養成 `--no-verify` 慣性使事件型檢查**永久失效**。
- **T004（#2）為停工級閘**：失敗＝方案形狀改變＝升級 user 重拍，US2／US3 全部任務作廢重寫。
- **T005（#11）→ T024 落點定值**；**T007（#3）→ T019 產鑰形式 ＋ T024 落點值分支**
  （失敗走預拍退路：方式 A＋`$HOME/.cache/rev4-secrets`、不停工；★重拍後〔#11 反轉〕退路
  **僅退方式 A**，SECRETS_DIR 主值即為此值＝無降階動作，詳 ADR 0080 決策 3）。
- **T040（age 二進位）為 T007 硬前置**（T007 要實跑 `age-keygen`／`age -p`；二進位由 T007
  ／T019／T033 共用、清理承接＝T038 收刀終驗）。
- **T025 三處同刀齊改**：任一未改則該處無條件賦值靜默吃掉外部值（preflight 回 OK、compose 掛掉）。
- **T030 遷移五步順序即契約**：刪舊落點必為最後一步（提前刪＝容器 bind 舊 inode、下次重啟才炸）。
- **T039（編號後補、執行序在 T030 之後）**＝SC-003 後半乾淨重建全鏈；需 US3 全部接線完成才有意義。
- **Phase 2 三閘的 blocking 範圍**＝US2／US3／US4；US5 經 US2~US4 鏈遞移依賴、US1 則完全不受
  Phase 2 影響（可先行或並行）。
- [P] 標記＝與同 phase 前一任務異檔零依賴（T006 gnupg 設定／T013、T014 hook 新檔／T028 compose／
  T029 bootstrap／T032 RUNBOOK 既有節／T035 BACKLOG＋NOTES／T037 量測）；其餘序列。
- **零 submodule 改動、零 pin bump**：兩源倉僅設 per-machine `core.hooksPath`（T016）、工作樹不動。

## Implementation Strategy

- **MVP first**: T001~T003＋T009~T017（US1）＝可交付最小閉環——三層防線立即生效，機密進 git
  的不可逆風險當場下降，且**完全不依賴 SOPS 是否導入成功**。
- **風險前置**: Phase 2 三閘先於一切 SOPS 施工——#2 失敗的代價是「腳本形狀全異」，先寫再驗
  有一半機率要重寫（research 明列）；#3 有預拍退路故不停工、#2／#11 失敗一律升級 user。
- **Incremental**: US2（密文入版控）→US3（明文遷移）→US4（營運程序）→US5（治理）逐單元收斂；
  每單元 TDD 先紅後綠（python 面）或 fixture 否定測試（bash／hook 面）＋雙審查編排
  （executing-plans、CLAUDE.md §2 六件套）＋單元邊界復核。
- **否定測試為第一公民**: 本方案失敗模式幾乎全是「指令回報成功但做錯了」——T017／T023／T030／T039／
  T033 各含刻意構造的必紅情境，**不做否定測試＝該項未驗收**。
