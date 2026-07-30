# Implementation Plan: 019-secrets-sops 機密管理——SOPS+age 全量導入＋三層掃描防線

**Branch**: `019-secrets-sops` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/019-secrets-sops/spec.md`

## Summary

把本 repo 機密管理自「gitignore 結構防線＋9p 明文（權限恆 777）」升級為三件事：①**洩漏掃描三層
防線**（事件型樣式掃描器×既有狀態型窄樣式 L16×確定性值比對）覆蓋三個 repo 的 commit 與 push
邊界；②**機密以密文入版控**（單一加密檔 8 key、公鑰模型、加人零機密傳遞）＋fail-loud 解密管線；
③**明文落點遷出 9p**（tmpfs；★重拍 2026-07-29、#11 反轉後改**ext4 持久
`$HOME/.cache/rev4-secrets`**——見下方 Storage 節重拍註記）並以單一事實來源貫穿 compose 與
三支腳本。技術路線＝SOPS+age，
sops 走官方容器（host 零安裝、image digest 釘版），私鑰採 passphrase 加密 identity（施工首波
實測定案、退路預拍）。所有既有失敗模式皆「指令回報成功但做錯了」，故每項改動配一條否定測試。

## Technical Context

**Language/Version**: Bash（POSIX sh 相容 hook＋bash 腳本）、Python 3（既有 tools/ 家族慣例）；
零新增執行期語言。

**Primary Dependencies**: sops（官方容器映像、digest 釘版；host 零安裝）／age＋age-keygen
（一次性產鑰、官方 release 二進位＋checksum、用完即刪）／機密掃描器 Betterleaks（原生二進位、
釘版）；既有 docker compose、既有 tools/docs-sync.py 家族。

**Storage**: 加密檔 `deploy/secrets.dev.enc.yaml`（git tracked 密文）；解密明文＝tmpfs
（`/dev/shm/rev4-secrets`＝解法 2′ 拍板值，實測閘 #11 為反轉條件；**#3 失敗時之預拍退路值＝
`$HOME/.cache/rev4-secrets`**＝解法 2、ext4 持久）；私鑰＝host `~/.config/sops/age/`。
★重拍（2026-07-29、#11 反轉後）：解密明文落點改**解法 2＝`$HOME/.cache/rev4-secrets`**
（ext4 持久、免開機儀式）、私鑰維持 B′、#3 退路僅退方式 A（SECRETS_DIR 已在 2 不再降）——
拍板全文與理由＝ADR `docs/arc42/decisions/0080-age-identity-bprime-secretsdir-solution2.md`
「決策」節第 1~3 點與其下「user 重拍三點定案與理由」段（唯一權威落點）。

**Testing**: 新增 python 工具照 018 慣例（自帶 test 子命令＋紅綠 self-test＋pre-commit 條件觸發）；
bash 腳本與 hook 走 fixture 演練機判（8 格 fixture、刪 key、CR 注入、`.new` 觸發）；整體驗收
＝quickstart 機判劇本（比照 017／018）。

**Target Platform**: WSL2（Ubuntu）＋Docker Desktop WSL integration；repo 位於 drvfs（`/mnt/d`）、
明文落點與私鑰位於 ext4／tmpfs（★重拍 2026-07-29、#11 反轉後：明文落點與私鑰**皆位於 ext4**、
tmpfs 不再涉入）。

**Project Type**: 治理工具鏈＋部署資產（無應用程式碼改動；兩 submodule 樹零改動）。

**Performance Goals**: pre-commit 端到端維持秒級（SC-009，比較基準＝018 現況；掃描器為 Go 靜態
二進位、增量掃 staged 面）。

**Constraints**: 零維運（不新增常駐服務）；host 零安裝為原則、例外僅一次性產鑰工具（用完即刪）
與掃描器二進位（常駐、有存在性斷言）；兩 submodule 樹零改動（憲法 §III 軌道零波及）；
`--no-verify` 可繞過事件型檢查＝已知邊界，由 pre-push 第二層與 allowlist 先行降低誘因。

**Scale/Scope**: 8 個加密 key／11 支機密檔／10 條 compose 條目／3 個 repo 的 hook 面／
5 支 ADR／**新增 11 個檔案（另 5 支 ADR 新檔）＋改動 12 個結構性既有檔**，另加 research R18
的程序性引用檔逐檔判定（部分與上述清單重疊、實數以現場 `git grep` 為準）——逐檔清單＝下方
Project Structure＋research R18 表兩者聯集。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

逐題對照 §IV 九題（憲法 v1.14.0）：

1. **§I.1 base-web 為權威？** 不違反——本刀零 wire／endpoint 面改動，base-web 與 rust-api
   功能對應關係不變。
2. **動到 base-web inline？** **否**——hook 檔寄宿外層 repo，兩源倉僅由 bootstrap 設定
   `core.hooksPath`（per-machine git config，非樹內檔案）。base-web 與 rust-api 工作樹零改動、
   零 `rev4-inline` 標記需求、fork-delta-lint 面不變（pin 亦不動）。
3. **menu 顯示走 Casbin enforce？** N/A——本刀無 menu 面。
4. **wire 設計對齊 §I.3？** N/A——本刀零 wire 改動（無新端點、無 envelope／碼表變更）。
5. **自前代 source 拷貝 code？** 否——新增腳本與工具全新寫；上游工具（sops wrapper 樣板）
   為外部參考、依本專案慣例重寫。
6. **抵觸 §II 拍板？** 否——三項拍板（unknown header／auth route mode／prod 路徑前綴）皆不涉。
7. **觸及 §III ★ 軌道？** **否**（此為 hook 寄宿外層的設計動機）——原案「base-web 倉內新增
   hook 目錄」不在任何授權軌道內（預設軌道僅 `.env*`／`typings/api/` 新檔／`rev4-*.ts` 新檔），
   照做需 Amendment；改為外層寄宿後零軌道波及、零 Amendment。
8. **新建業務表？** 否——零 migration、零 schema 面。
9. **觸及 §I.7 行為島？** 否——十島（single-session／token rotation／denylist／閒置／登入節流／
   IP 閘／casbin／選單／使用者域／稽核域）皆為執行期行為，本刀止於部署資產與 commit 邊界治理，
   不改任一 invariant。**是否屬「該入憲而未入憲的新行為島」？** 否——機密管理無執行期狀態機
   （無並發、無鎖序、無 fail 方向切換）；其紀律屬營運操作規則，歸 ADR＋RUNBOOK 承載
   （brainstorm §4 拍板：SSH identity 禁令落 ADR 而非憲法）。

**結論：九題全過、零 Amendment 需求。** Complexity Tracking 無需填寫。

## Project Structure

### Documentation (this feature)

```text
specs/019-secrets-sops/
├── plan.md              # 本檔
├── research.md          # Phase 0：接地決策（R1~Rn）
├── data-model.md        # Phase 1：機密資產與掃描規則模型
├── quickstart.md        # Phase 1：驗證劇本（S1~Sn ↔ SC-001~010）
├── contracts/
│   ├── scan-gates.md    # 掃描三層防線的機器閘契約
│   └── secret-pipeline.md # 加密／解密管線與落點接線契約
├── checklists/
│   └── requirements.md  # /speckit-specify 產出
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本命令）
```

### Source Code (repository root)

```text
# 新增
.gitleaks.toml                    # 掃描器設定：誤報 allowlist＋DSN 自訂規則（三 repo 共用；
                                  #   僅用 gitleaks 子集欄位＝Betterleaks 亦原生 fallback 此檔名）
.githooks/pre-push                # 外層第二層掃描（範圍推導含全零 oid 退階）
.githooks/lib/scan-range.sh       # 共用：pre-push stdin 解析＋範圍推導
.githooks-submodule/pre-commit    # 兩源倉專用（僅樣式掃描、零 python 依賴）
.githooks-submodule/pre-push      # 同上；以 dirname "$0" 自我定位後 source ../.githooks/lib/
.env.example                      # SECRETS_DIR 落點宣告範本（tracked）
deploy/sops.sh                    # sops 官方容器 wrapper（digest 釘版、七要件見 contracts P1）
deploy/decrypt-secrets.sh         # 解密管線（五要求：斷言／權限／.new 守衛／無尾端換行／tty）
deploy/secrets.dev.enc.yaml       # 加密檔（tracked 密文、8 key）
.sops.yaml                        # creation_rules（錨定式 path_regex、單規則、不設範圍選項）
tools/secret-value-guard.py       # 值比對防線（僅外層；自帶 test 子命令＋紅綠 self-test）

# 改動
.githooks/pre-commit              # 掃描行置於 docs-sync 之前＋值比對＋事件型註解＋條件觸發自測
tools/bootstrap                   # 掃描器存在性斷言（die 級）／兩源倉 hooksPath 佈署與斷言／
                                  #   .env 代勞產生／secrets 體檢 glob 隨 SECRETS_DIR／段 5 加新工具自測
tools/docs-sync.py                # ★TOOLS_PY 常數登記新工具（否則不入 tools-cli 真表、
                                  #   L19 命令形 lint 與 L20 空集合守衛涵蓋不到）
docker-compose.yml                # 頂層 secrets 10 條目改帶預設值變數展開
deploy/generate-secrets.sh        # SECRETS_DIR 帶預設展開＋--compose-only＋權限終值 644
deploy/preflight-secrets.sh       # 同上＋CR 護欄＋composite↔leaf 一致性＋成功句改陣列長度插值
deploy/setup-reaper-role.sh       # PW_FILE 隨 SECRETS_DIR（第三同步點）
deploy/secrets/README.md          # 四處程序性描述對齊（預檢語意／force 語意／chmod 注記／對照表）
docs/ops/RUNBOOK.md               # SOPS 營運段群＋§7 增補 re-encrypt＋§4／§12 連帶
docs/ops/BACKLOG.md               # B-115 prod 分層遞延包
docs/ops/NOTES.md                 # base-web --no-verify 慣例廢止
docs/arc42/decisions/0079~0083    # ADR 五支
（另：`deploy/secrets` 命中之**程序性引用檔逐檔判定，清單見 research R18**〔13 檔穩定值，
  其中 `.dockerignore`／`.gitignore`／`deploy/dev-webhook-sink.sh`／
  `deploy/grafana-provisioning/alerting/contact-points.yml` 四檔不在上方清單、由 T036 收；
  `docs/arc42/ARCHITECTURE.md` 屬活書 as-built、**歸收刀簿記 commit 不在本 branch 改**〕；
  歷史文件不改、檔數隨本刀產物增長；生成物由 docs-sync generate 重算）

# 零改動（設計保證）
base-web/**、rust-api/**          # 兩源倉工作樹不動、pin 不動（FR-006 之設計動機）
```

**Structure Decision**: 治理資產分三處落地——**倉根**（掃描器設定、`.env.example`、`.sops.yaml`：
需被 git 與工具在 repo 根定位者）、**`.githooks/`**（三 repo 共用的 hook 面，單一事實來源）、
**`deploy/`**（部署期資產：wrapper、解密腳本、加密檔，與既有 generate／preflight 同層）。
新增 python 工具入 `tools/`、沿 018 家族慣例（`.py` 副檔名＋自帶 test 子命令＋條件觸發）。

## Post-Design Constitution Check（Phase 1 後複評）

設計產出（research R1~R19、data-model 七模型、contracts 兩契約、quickstart S1~S10）後重跑 §IV：

- **第 2／7 題（base-web inline／★ 軌道）維持「否」且獲設計強化**：R17 定稿兩 hook 目錄拓樸
  ——`.githooks-submodule/` 寄宿**外層** repo，兩源倉僅由 bootstrap 設定 `core.hooksPath`
  （per-machine git config、非樹內檔案）。**兩源倉工作樹零改動、pin 不動、fork-delta 面不變。**
- **第 8／9 題維持「否」**：零 migration；設計全程無執行期狀態機（無並發、無鎖序、無 fail 方向
  切換）——機密管理紀律歸 ADR＋RUNBOOK，非行為島。
- **第 1／3／4／5／6 題維持 N/A 或「否」**：零 wire／menu／schema／前代 source 面。
- **新增確認（設計階段浮現）**：`tools/docs-sync.py` 的 `TOOLS_PY` 常數登記屬治理工具鏈**既有
  擴充點**（018 建立），非憲法面改動；`.githooks/` 續寫同理。

**結論：九題全過、零 Amendment；設計未引入新違規。**

## Complexity Tracking

> Constitution Check（前後兩次）九題全過、零違規——本節不適用。

## Phase 2 交棒說明

`/speckit-tasks` 依 spec 五個 user story 與 brainstorm 五波閘門結構拆解，注意三項排序硬約束：

1. **U1 實測閘先於 U2／U3**：#2 失敗→方案形狀改「解法 1 環境變數注入」＝**升級 user 重拍**
   （非 agent 自決）；#11 反轉→**升級 user 重拍** SECRETS_DIR（**同為非 agent 自決**）；
   #3 失敗→預拍退路自動生效（方式 A＋解法 2＝`$HOME/.cache/rev4-secrets`、不停工）。
   ★重拍（2026-07-29、#11 已實測反轉）：上句「方式 A＋解法 2」屬 2′ 基準原文；SECRETS_DIR 既已
   定在解法 2，**#3 退路僅退方式 A、不含 SECRETS_DIR 降階**——詳 ADR 0080 決策 3。
2. **U0 內部**：誤報基線重建 → allowlist 落檔 → **才**啟用 hook（次序顛倒＝第一個被擋的是
   自己人的簿記 commit，且會養成 `--no-verify` 慣性使事件型檢查永久失效）。
3. **U4 遷移五步順序即契約**（contracts/secret-pipeline.md §P6），刪舊落點必為最後一步。

tasks 不得排入 push／merge（憲法 §I.4）；ADR 隨拍板落 draft、收刀轉 accepted；
活書 as-built 歸收刀簿記 commit（不排進 feature branch 內）。
