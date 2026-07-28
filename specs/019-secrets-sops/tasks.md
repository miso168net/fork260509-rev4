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

- [ ] T001 基線快照（供 SC-009 對照、數字記回本行備註）：`sh .githooks/pre-commit` 全鏈實跑
  `time` 基線（無 staged、無工具改動）×2 取中位；＋`python3 tools/docs-sync.py test`／
  `schema-gate.py test`／`wire-schema.py test` 三套件現況案數（預期 347／130／7）——沿 018
  T001 方法論（drvfs 牆鐘變異大、同機同日對照，L-155）
- [ ] T002 掃描器釘版雙查與**拍板呈報**（★需 user 拍板、不得自決；CLAUDE.md §6 釘版紀律）：
  查 Betterleaks 上游最新穩定 release 版本與發布日（research R1 當日值＝v1.7.1／2026-07-27，
  屬浮動量必須現查）→ 連同「維持該版 vs 更新版」兩案呈報 user 選定 → 選定值記入
  `docs/ops/RUNBOOK.md` 工具版本欄
- [ ] T003 安裝掃描器並驗證：依 T002 拍板版本下載 `betterleaks_<VER>_linux_x64.tar.gz`
  （★版號無 `v` 前綴、架構寫 `x64`）＋`checksums.txt`（★檔名不含版號）→ `sha256sum -c`
  驗證 → 安裝至 PATH → `betterleaks version` 確認與拍板值一致（不符即中止、依 §6 紀律）

## Phase 2: Foundational（U1 三實測閘）

**Goal**: 結清三個 go/no-go 實測，決定 US2／US3 的方案形狀；結果全數記入 ADR draft。
**Blocking 範圍**: block US2／US3／US4；**不 block US1**。

- [ ] T004 **閘 #2**（硬性前置、research R14）：於 `$HOME` ext4 路徑與 `/dev/shm` 各放測試檔，
  以該路徑 bind-mount 起一個容器，`docker inspect --format '{{json .Mounts}}'` 確認 Source
  正確且容器**讀得到**；併驗權限與 UID 行為。★**失敗＝方案形狀改「解法 1 環境變數注入」
  ＝立即停工升級 user 重拍**（腳本形狀全異、後續任務作廢重寫），不得自行改設計
- [ ] T005 **閘 #11**（結論反轉條件、必須早於落點定案）：自 Windows 側 docker client 對
  WSL 內部 ext4／tmpfs 路徑起一個容器，**以 `docker inspect` 的 Mounts 判讀**（非只看容器
  有沒有起來）；併校準「解密後明文能否被 Windows 側讀取」。★**反轉→SECRETS_DIR 拍板回頭
  重做（2 vs 2′ 比較基礎改變）＝升級 user**
- [ ] T006 [P] pinentry 前置（research R8）：建 `~/.gnupg/gpg-agent.conf` 寫入
  `pinentry-program /usr/bin/pinentry-curses`＋`GPG_TTY` 設定 → `gpgconf --reload gpg-agent`
  （本機該檔原不存在＝零衝突覆蓋風險；純終端 session 下預設 pinentry-gnome3 可能彈不出）
- [ ] T007 **閘 #3**（B′ 定案點）：`age-keygen | age -p` 產一把 passphrase 加密 identity
  （★`age -p` 的 passphrase 讀取走 `/dev/tty`、與 stdout 重導向互不干擾，真 TTY 下可行）→
  `xxd` 驗 `keys.txt` 尾端無 CR → 以 `--age <剛產生的公鑰>` 直接指定做最小加解密往返
  （**此處不用 `.sops.yaml`**，避開循環依賴）→ 另開 shell 跑解密，確認**跳出 passphrase
  提示且解得開**、且無 keyring 自動填入假象。★成功→定案 B′；**失敗→預拍退路自動生效
  （方式 A＋SECRETS_DIR 降解法 2），記入 ADR、不停工**
- [ ] T008 三閘結果落 ADR draft `docs/arc42/decisions/0080-*.md`（私鑰與落點篇的實測欄）：
  逐閘記「怎麼跑／實測輸出／結論／對設計的影響」；#3 失敗時另記退路生效與 SECRETS_DIR 降階

## Phase 3: US1 — 機密洩漏三層掃描防線（P1；MVP）

**Goal**: Betterleaks 事件型廣譜 × 既有 docs-sync L16 狀態型窄樣式 × 值比對確定性三層互補，
覆蓋三 repo 的 commit 與 push 邊界。
**Independent Test**: spec US1——8 格 fixture × 兩路徑全符預期、三 repo 各實擋一案、例行簿記
commit 零誤擋（不建任何 SOPS 資產即可完整驗證）。

- [ ] T009 [US1] **誤報基線現場重建**（★必先於 T010；不得沿用任何舊數字）：以 T003 安裝之
  掃描器對全歷史實跑一次，逐筆分流「真機密／誤報」並記錄命中樣態與所屬檔案；重點確認
  `docs/ops/events.jsonl` 的 40-hex 三欄（merge／pins.web／pins.api）、
  `deploy/secrets/*.txt.example`、`specs/017-audit-retention/quickstart.md` 的 `curl -u` 示例
- [ ] T010 [US1] 新增 `.gitleaks.toml`（★必先於 T015 啟用 hook）：①DSN 自訂 `[[rules]]`
  （`id`＋`regex` 必填，涵蓋 postgres(ql)／redis／mysql 帳密 URL 樣式，補 `description`＋
  `keywords`）②依 T009 基線寫 per-rule allowlist——**每條必含 `condition = "AND"`**＋
  `paths`×`regexes`＋顯式 `regexTarget`，**嚴禁整檔放行**（漏 AND 退化為過寬放行且不報錯
  ＝本 schema 最大靜默失效點）③檔頭註記「僅用 gitleaks 子集欄位」（保雙向可攜）
- [ ] T011 [P] [US1] **TDD 紅**：`tools/secret-value-guard.py` 測試先行——內嵌
  `unittest.TestCase`（沿 018 慣例、無 pytest）：命中即擋／絕不輸出值本身／值缺席時 skip 不
  fail-closed／紅綠 self-test 防恆綠（紅樣本執行期字串串接構造、綠樣本含近似不命中與**邊界
  樣本**）／`purge_git_env` 隔離 git fixture。此時實作未寫、測試必紅
- [ ] T012 [US1] **TDD 綠**：實作 `tools/secret-value-guard.py`——`main(argv)` 手寫
  `if cmd == "…"` 字面鏈＋`test` 子命令＋usage `exit 64`（★掃源正則只認此形）；讀
  `$SECRETS_DIR`（回退 `deploy/secrets`）現值比對 `git diff --cached`；**★同步登記進
  `tools/docs-sync.py` 的 `TOOLS_PY` 常數**（否則不入 tools-cli 真表、L19／L20 涵蓋不到）→
  `python3 tools/docs-sync.py generate` 重算真表
- [ ] T013 [P] [US1] 新增 `.githooks/lib/scan-range.sh`＋`.githooks/pre-push`（contracts
  scan-gates §S3）：解析 pre-push stdin 四欄位；範圍推導＝一般更新用 `remote-oid..local-oid`／
  **新分支首推（remote-oid 全零）退階 `local-oid --not --remotes=origin`**／該退階無效時掃整條
  分支／刪除分支（local-oid 全零）跳過；命中即 exit 1
- [ ] T014 [P] [US1] 新增 `.githooks-submodule/pre-commit` 與 `.githooks-submodule/pre-push`
  （兩源倉專用、**僅樣式掃描、零 python 依賴**）：以 `dirname "$0"` 自我定位後 source
  `../.githooks/lib/scan-range.sh`（**不硬編碼外層絕對路徑**）
- [ ] T015 [US1] 改 `.githooks/pre-commit`：①掃描行置於 `docs-sync check` **之前**，指令＝
  `betterleaks git --pre-commit --staged --redact --verbose --exit-code 2`（★`--redact` 不可省
  ——預設 0＝明文噴進終端；★禁用 `protect`／`detect`；★原生二進位、禁容器）②exit code 分流
  （2＝命中／1＝掃描器自身異常、訊息可辨識並指向 bootstrap）③加值比對呼叫 ④註解**明確區分
  事件型（掃描：`--no-verify` 繞過即真進 git）與狀態型（docs-sync：只延後）** ⑤新工具加入條件
  觸發自測 `for` 清單
- [ ] T016 [US1] 改 `tools/bootstrap`（沿既有編號段與 ok/warn/die 慣例）：①掃描器存在性與版本
  斷言（**die 級**、附安裝指引；防新機 commit 時 exit 127 猝死）②兩源倉 `core.hooksPath` 冪等
  佈署（絕對路徑指向外層 `.githooks-submodule`）＋讀值斷言（不符 die＋自癒指令）③段 5 自測
  清單加入新工具
- [ ] T017 [US1] **S1／S2／S3 驗收**（quickstart 逐步）：8 格 fixture（四形 × `git add`+commit
  與 `git commit -a` 兩路徑、假值當場產生驗畢即刪）＋兩源倉各實擋一案＋例行簿記 commit 零誤擋
  ＋pre-push 三情境（一般／新分支全零 oid／刪除分支）＋**否定測試**：暫時拿掉 allowlist 的
  `condition = "AND"` 觀察放行過寬後復原

## Phase 4: US2 — 機密以密文入版控＋可斷言的解密管線（P2）

**Goal**: 8 key 加密入版控（公鑰模型、加人零機密傳遞）＋fail-loud 解密管線。
**Independent Test**: spec US2——在現行落點不變的前提下即可完整驗證加密往返、斷言行為與守衛。
**依賴**: Phase 2（T007 定私鑰方式）。

- [ ] T018 [US2] 新增 `deploy/sops.sh`（contracts secret-pipeline §P1 七要件）：digest 釘版常數
  ＝`ghcr.io/getsops/sops@sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`
  （★施工時複查 digest 仍指向 v3.13.3-alpine；★registry 與 digest 必須成對）＋`-it` 條件化
  ＋**不轉發 `EDITOR`**＋顯式 `-e SOPS_AGE_KEY -e SOPS_AGE_KEY_FILE -e SOPS_AGE_KEY_CMD`＋
  掛載 `$PWD:/work -w /work` 與私鑰目錄唯讀；`chmod +x` 後 **`git update-index --chmod=+x`**
  （drvfs exec bit 不落 index）
- [ ] T019 [US2] 取得 `age-keygen` 並產正式金鑰：自官方 GitHub release 下載
  `age-v<VER>-linux-amd64.tar.gz`（★**無 checksums 檔**——完整性以 release API 的 `digest`
  欄位比對 `sha256sum`）→ 依 T007 定案產鑰（B′：`age-keygen | age -p`／退路 A：明文＋
  `chmod 600`）→ `xxd` 驗尾端無 CR → **二進位用完即刪**；以 `age-keygen -y` 取 recipient 公鑰
- [ ] T020 [US2] 新增 `.sops.yaml`（contracts §P2 五條）：單一 `creation_rules`、
  `path_regex` **錨定式**（★比對用 `MatchString`＝非錨定子字串命中）、`age:` 用 YAML 清單形、
  **不設六個範圍選項任一**（預設 `unencrypted_suffix="_unencrypted"`＝全加密）；寫完**驗證
  規則確實命中**目標檔
- [ ] T021 [US2] 建 `deploy/secrets.dev.enc.yaml`（恰 8 key＝7 leaf＋`alert_webhook_url`）：
  自現值組明文 YAML（**中間產物限 repo 內 gitignored 目錄、用完即刪、不得 staged**；wrapper
  只掛載 `$PWD`）→ 經 wrapper 加密 → 驗 `git diff` 呈現 **key 名明文＋值全 `ENC[`**、key 數＝8。
  ★`alert_webhook_url` **如實搬移現值**（現值 39 bytes 為 user 已填真值；`--force` 不重置、
  **絕不以刪檔為手段**）；composite 不進（由既有腳本重生）
- [ ] T022 [US2] 新增 `deploy/decrypt-secrets.sh`（contracts §P4 五要求）：tty 守衛（非互動
  **吵鬧失敗**、不得 hang）→ source `.env` → `mkdir -p`＋`chmod 700`**自建 0700 子目錄**
  （`/dev/shm` 為 world-writable）→ wrapper 收 stdout（`umask 077`、**不用 `--output`／`-i`**
  避免 root 產物）→ **key 數與名稱斷言、不符零寫入＋非零退出＋指名缺哪個 key** → 逐檔
  `printf '%s'`（無尾端換行）＋`chmod 644` → **現值 ≠ 解密值則另存 `.txt.new` 不覆寫**
- [ ] T023 [US2] **S4／S5 驗收**：加解密最小往返（#1）＋加密檔形制三條＋五要求逐條否定測試
  （刪 key→零寫入報錯｜構造 `alert_webhook_url` 差異→產 `.new` 原檔不變｜`xxd` 驗無 `0a`
  無 `0d`｜leaf 與 composite 內嵌值 byte 數一致｜owner 非 `root:root`｜非互動呼叫吵鬧失敗）；
  **否定測試**：故意以錯誤副檔名順序加密一次觀察退化為整檔加密後刪除實驗檔

## Phase 5: US3 — 明文離開 /mnt/d（SECRETS_DIR 遷移）（P3）

**Goal**: 明文自 9p（權限恆 777）遷至 tmpfs；compose 與三腳本經單一事實來源取得落點。
**Independent Test**: spec US3——遷移五步＋落點驗證＋觀測軌全開讀取，全程機判。
**依賴**: Phase 2（T004／T005）＋US2（T022 解密管線）。

- [ ] T024 [US3] 新增 `.env.example`（tracked）＋`tools/bootstrap` 代勞產生 `.env`
  （gitignored）：`SECRETS_DIR` 依 T005 結果定值（拍板值 `/dev/shm/rev4-secrets`）；
  `.gitignore` 既有規則已覆蓋、無須加行
- [ ] T025 [US3] 三腳本 SECRETS_DIR 同步改（★**三處必須同刀齊改**，任一未改即該處無條件賦值
  靜默吃掉外部值）：`deploy/generate-secrets.sh`（`SECRETS_DIR` 賦值行）／
  `deploy/preflight-secrets.sh`（同）／`deploy/setup-reaper-role.sh`（`PW_FILE` 賦值行）
  ——改帶預設展開＋各自 `source .env`（存在時）
- [ ] T026 [US3] `deploy/generate-secrets.sh` 功能改：加 `--compose-only` 旗標（缺 leaf
  **報錯退出、不生成**——防靜默造新亂數）＋權限終值改 **644**（原 600 會使三個非 root service
  在開 obs／metrics 軌時 Permission denied）；★`printf '%s'` 寫檔形**不得改為 echo**
- [ ] T027 [US3] `deploy/preflight-secrets.sh` 增強：①CR 偵測護欄（命中即 FAIL）②composite↔
  leaf 一致性檢查（複用既有期望值組合式；防「塞入密碼已過期的 `database_url` 也回 OK」）
  ③成功句改**陣列長度插值**（現硬編碼「十一個」、免每刀追改）
- [ ] T028 [P] [US3] `docker-compose.yml` 頂層 `secrets:` 10 條目改帶預設值變數展開（未設變數
  時回退專案相對路徑）；★`reaper_password` 不進 compose 是設計（僅 setup-reaper-role 直讀）、
  **勿誤補**；dev 與 example 兩 compose 檔零改動
- [ ] T029 [P] [US3] `tools/bootstrap` secrets 體檢 glob 隨 SECRETS_DIR；缺實值維持 **warn 級**
  （既有慣例——實值人對人交接、bootstrap 不生成）
- [ ] T030 [US3] **遷移執行＋S6／S7 驗收**：依 contracts §P6 五步（`down`→decrypt→設值
  `up -d`→**逐容器 `docker inspect` 驗來源皆非 `/mnt/d`**→**確認後才**刪舊落點）；＋未設變數時
  `docker compose config` 回退驗證（#4）＋`--profile obs --profile metrics` 全開驗三個非 root
  service（472／65534／59000）讀得到且健康＋**否定測試**：跳過 `down` 觀察 `Starting` 而非
  `Recreated`（假性完成信號）後復原重做；完成判準＝`/mnt/d` 全樹零明文機密檔

## Phase 6: US4 — 營運程序落地（P4）

**Goal**: 加人／撤銷／輪替／遺失／開機儀式可依 RUNBOOK 執行；§7 輪替表增補 re-encrypt 步驟。
**Independent Test**: spec US4——以演練用第二把金鑰跑完整撤銷演練＋輪替一支機密驗證加密檔同步。
**依賴**: US2（資產存在）。

- [ ] T031 [US4] `docs/ops/RUNBOOK.md` 新增 SOPS 營運段群：編輯機密（`sops edit`→decrypt→
  `up -d --force-recreate`、**不用 `restart`**）／加人與換機四步（零機密傳遞；★「換機
  `git pull` 即可用」是錯的）／撤銷四步（★`rotate -i --rm-age` **逐檔一行**——`rotate` 只吃
  第一個位置參數、其餘靜默略過且 exit code 不變）／金鑰與 passphrase 遺失（★備份含 passphrase
  本身）／開機儀式（2′ 下每次開機重跑解密）／合併衝突（暫存必落 repo 內、重加密後核對
  `sops.age` 清單）／災復備註（g 不升格之代償）／工具版本記錄欄
- [ ] T032 [P] [US4] `docs/ops/RUNBOOK.md` 既有節連帶：**§7 輪替表增補「輪替後 re-encrypt 回
  加密檔」步驟**（漏此步→輪替值與加密檔脫鉤、下次 decrypt 觸發 `.new` 守衛）＋§4 人工必填
  清單增 `.wslconfig`／BitLocker 確認項＋§12 工具鏈速查增 `deploy/sops.sh` 與
  `deploy/decrypt-secrets.sh`
- [ ] T033 [US4] **S8 撤銷演練＋反向驗證**：產演練用第二把金鑰→加入→`updatekeys -y`→確認可解
  →撤銷四步→**#7 五準則逐條驗**（核心＝否定測試：舊 `enc:` stanza 貼回新檔跑原廠解密**必須
  失敗於 MAC 驗證**；rotate 前後值密文必變；recipient 清單前後不含被撤銷者；人工確認 dev 檔
  無 prod 級機密）→**#10 反向驗證**（identity 移走＋`unset` 相關變數後解密**必須失敗**）→
  ★順序陷阱驗證（故意先 rotate 後 updatekeys 觀察中間狀態）→演練金鑰移除、痕跡不入版控

## Phase 7: US5 — 治理落檔（P5）

**Goal**: 拍板全數落 ADR；遞延項登記 BACKLOG；指路文字連帶更新。
**Independent Test**: spec US5——對照綱要逐支核 ADR 欄位；BACKLOG／NOTES／指路文字逐處核。
**依賴**: 前四者結果（實測欄位、驗收證據）。

- [ ] T034 [US5] ADR 5 支落 `docs/arc42/decisions/`（0079 起、一決策一檔、綱要＝brainstorm §9）：
  **A** 選型 SOPS+age（四理由＋誠實收窄＋零維運硬約束＋digest 釘版＋**cosign 不啟用之誠實
  登記**＋age 取得路徑）／**B** 私鑰 B′×SECRETS_DIR 2′（自洽論證＋退路預拍＋#11 反轉條件＋
  **SSH identity 禁令**＋passphrase 政策＋**tmpfs swap 殘餘風險誠實登記**；T008 實測欄併入）／
  **C** 加密資產形狀（dev 單檔 8 key／prod 不建含目標形狀備忘／`ca.key` 不進含重評條件／
  命名紅線／不設範圍選項）／**D** 掃描三層防線定位（事件型×狀態型×確定性互補；三 repo 覆蓋；
  base-web `--no-verify` 慣例廢止；**compose 向後相容取捨之誠實登記**）／**E** 團隊組成前提
  （將來可能有非工程師→兩層架構待觸發決定）＋問題 B 四條件延後登記
- [ ] T035 [P] [US5] `docs/ops/BACKLOG.md` 登記 B-115 prod 機密分層遞延包（prod 加密檔＋
  #5／#6 結構性不可測驗收＋CI 側保護；掛 prod 部署刀群）＋`docs/ops/NOTES.md` 同步 base-web
  `--no-verify` 慣例廢止（repo 文件不引用 per-machine memory 路徑）
- [ ] T036 [US5] `deploy/secrets` 命中逐檔判定（**以現場 `git grep` 為準、不以靜態數字為驗收
  基準**）：程序性引用逐檔改（清單＝research R18 表）／歷史文件不改／生成物由
  `python3 tools/docs-sync.py generate` 重算；★`deploy/secrets/README.md` 四處描述對齊實際行為
  （預檢語意／`--force` 語意／chmod 注記／機密對照表）——該檔是唯一向 user 說明 secrets 程序的
  人寫文件、失真即誤導；順帶勘誤 `.gitignore` 的 `.json` 規則註解（與現行 compose 形不符）

## Phase 8: Polish & Cross-Cutting

- [ ] T037 [P] **S9 秒級量測**（SC-009）：pre-commit 端到端延遲（外框＋掃描器＋值比對）對
  T001 基線；沿 L-155 方法論取多次中位、記「純碼 commit」與「治理檔 commit」兩情境；超標則
  記錄成本結構並掛 BACKLOG（比照 018 SC-008 處置）
- [ ] T038 **S10 治理完備＋收刀前終驗**：quickstart S1~S10 全機判單通＋SC-001~010 逐條勾稽；
  `python3 tools/docs-sync.py generate`＋`check`＋`lint` 全綠、工作樹收斂；ADR 5 支轉 accepted
  （含三閘實測欄）；踩坑逐筆 append `docs/ops/LESSONS.md`

## Dependencies

```
T001 → T002 → T003
     ├─→ [US1（MVP、不依賴 Phase 2）: T009 → T010 → T011 → T012 → T013(P)/T014(P) → T015 → T016 → T017]
     └─→ [Foundational: T004 → T005 → T006(P) → T007 → T008]
                                                    ↓
                        [US2: T018 → T019 → T020 → T021 → T022 → T023]
                                                    ↓
                        [US3: T024 → T025 → T026 → T027 → T028(P)/T029(P) → T030]
                                                    ↓
                        [US4: T031 → T032(P) → T033]
                                                    ↓
                        [US5: T034 → T035(P) → T036]  →  [Polish: T037(P) → T038]
```

- **US1＝MVP 且與 Foundational 正交**：掃描防線零 SOPS 依賴，可先行或與 Phase 2 並行。
- **T009 → T010 → T015 為硬序**：基線重建 → allowlist 落檔 → **才**啟用 hook。次序顛倒＝
  第一個被擋的是自己人的簿記 commit，且會養成 `--no-verify` 慣性使事件型檢查**永久失效**。
- **T004（#2）為停工級閘**：失敗＝方案形狀改變＝升級 user 重拍，US2／US3 全部任務作廢重寫。
- **T005（#11）→ T024 落點定值**；**T007（#3）→ T019 產鑰形式**（失敗走預拍退路、不停工）。
- **T025 三處同刀齊改**：任一未改則該處無條件賦值靜默吃掉外部值（preflight 回 OK、compose 掛掉）。
- **T030 遷移五步順序即契約**：刪舊落點必為最後一步（提前刪＝容器 bind 舊 inode、下次重啟才炸）。
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
- **否定測試為第一公民**: 本方案失敗模式幾乎全是「指令回報成功但做錯了」——T017／T023／T030／
  T033 各含刻意構造的必紅情境，**不做否定測試＝該項未驗收**。
