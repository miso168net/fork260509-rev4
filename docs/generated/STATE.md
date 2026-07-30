<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=694741f

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：83（accepted 77、superseded 6）
- BACKLOG 待辦：39（next：B-122）｜滯後：2
- LESSONS：195 筆（next：L-196）
- events：30 筆（feature_close 18、misc 9、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-28｜feature_close｜018-governance-hardening｜018-governance-hardening 收刀——治理工具鏈與編排紀律硬化（paulsha-conventions 評估九項＋B-111 併刀；六執行單元 TDD 雙審編排、U6 起 Fable 實作×Opus 審查異質配置＋final review Opus×Fable 異質雙審首航）。核心＝①B-111 四支 python 工具補 .py（直接改名＋活引用原子 commit、連字號保留；spec 未列四落點接地補齊〔bootstrap／ARCHITECTURE／setup-reaper-role.sh／archetype-map.json〕）＋CLAUDE.md 編排範本三件（六件套⑥空間邊界／review 次輪前饋／遷移三欄表慣例句；U2 起五支 workflow script 自食機器證＝SC-007）；②docs-sync 五新條款——L16 憑證內容掃描（外層 tracked 全量＋staged 面＋pin bump 增量掃 submodule、CRED_PATTERNS 四類窄樣式、退化全樹掃 WARN／執行失敗 ERROR、每跑紅綠 self-test 防恆綠、無 inline 豁免＝ADR 0077）／L17 pin 互證（平時 WARN、收刀 ERROR、缺席與 index 衝突 skip）／L18 events SHA 逐列實證（三物件庫 cat-file 批次併發中位 135ms 達 200ms 契約、pins 鍵集斷言恰 web+api、merge ERROR／pins WARN＝rebase 卷史合法）／L19 命令形 lint（語料寫死三件活手冊、子命令基準＝掃源分派表〔真表為生成物〕、舊名禁令＝B-111 長期機器化、bash 存在檢）／L20 空集合守衛七組 fail-closed（守衛#5 依實證收斂＝名冊非空＋有分派表者子命令集非空；fork-delta-lint 零分派表屬正確事實）；③G6 摘要三段式（X 錯誤／Y 警告／Z 條款跳過＋明細、退出碼僅 X 大於 0；8 類 silent-skip 入累積器、L16~L18 skip 以 submodule_head 共用探針歸一）；④events 帳本 4 筆短 SHA 一次性正規化（獨立勘誤 commit 逐筆 rev-parse 同物件證據＝ADR 0078 首例）＋RE_SHA 全域收 40；⑤tools-cli 真表（六支掃源）＋pre-commit 條件觸發（staged 含工具本體才跑該支 test、fork-delta-lint 兩條件聯集去重單跑）＋bootstrap 體檢三支 test fail-closed＋RUNBOOK §12 速覽連帶（L16~L20 逐條退出碼與跳過語意）。品質＝測試 212→347 案（新增 135、既有零轉紅；schema-gate 130／wire-schema 7 不變）；quality 審查累計約 170 突變體實證（U5 單輪 74 個 71 殺）；抓到真洞含 git commit -a 之 GIT_INDEX_FILE 絕對路徑洩漏（測試 fixture 寫真 repo index、44 failures 誤擋 commit——修＝purge_git_env 只掛 test 分支）與 L19 續值誤收完整命令形（誤紅 RUNBOOK 跨工具並列句型）。SC-001~009 全 PASS；SC-008 依 T001/T018 校正基準通過（平時增量約 0＝硬性達標；兩個絕對秒數已被本刀自身測試增長與 drvfs I/O 稅超越、成本結構與提速追蹤＝B-113）。final holistic review 雙 mergeable 零 merge-blocker。FR-017 機器證＝零 submodule 改動零 pin bump；憲法 v1.14.0 零 Amendment。
- 2026-07-22｜feature_close｜017-audit-retention｜017-audit-retention 收刀——B-016 稽核 log retention 自動清理本體（016 reaper 底座上第二個排程 job）。核心＝--job audit-retention 分派表化（未知值 exit 1 沿用）：env 四鍵 AUDIT_RETENTION_{OPERATION_LOG,ACCESS_LOG,LOGIN_ATTEMPT,SESSION_EVENT}_DAYS 三分語意（缺席 90／畸形〔含負數〕warn+90 照跑／解析成功且低於 30 含 0→開跑前全拒：結構化 error 指名鍵值＋exit 1＋四表零刪除＋不推心跳；四鍵一次全驗先於 Database::connect、以不可達 URL 反證零 DB 動作）；execute＝固定表序 operationLog→accessLog→loginAttempt→sessionEvent 逐表 mutate_in_txn{purge_before＋PURGE 自記}同交易（島 J3 複用繼承：operator None→created_by NULL、payload_after={table,before_days,deleted_count,job:audit-retention}、0 列照落、op-log 恆豁免 operation 不等 PURGE）＋逐表事件＋deleted_total 摘要（心跳 gauge 同值）；dry-run＝count_before（謂詞與 purge_before 逐字同形＝候刪即將刪）零變動零自記；bin 自帶 RetentionTable wire×entity_table 鏡像映射（不 import handler 私有 PurgeTable、R8）＋RETENTION_MIN_DAYS=30 與 PURGE_MIN_DAYS 雙側字面斷言互指（R3）。權限＝m013 純 GRANT 恰好集（四稽核表 SELECT,DELETE＋sys_operation_log INSERT＋sys_operation_log_id_seq USAGE；down 對稱不動 m012 射程；重掛錨比照 m012）。觀測＝心跳 PUT 按 reaper_job 分組（token-reap URL 同步遷移、R1）＋rules.yml 11→13 一筆原子交付（⑤/⑤b 補 reaper_job=token-reap matcher 射程收斂〔R1 honor_labels 接地新發現〕＋⑥/⑥b 鏡像新增、172800 互錨三檔擴涵蓋⑥）＋一次性清舊組遷移（RUNBOOK §9 承載、FR-010）。排程＝dev loop 兩 job 先後分號分隔互不阻斷（FR-009 構造承載）。測試＝四 facade count_before TDD（lib 726→730）＋handler 鏡像斷言（→731）＋bin 單測 8（三分六案＋未知 job 分派表＋鏡像斷言）＋整合 audit_retention 7 案（execute 快樂路徑含四組鏡像等值鎖／0 列照落／PURGE 豁免複證／同交易負向 rollback〔entity_table 溢位注入〕／跨表部分完成＋冪等〔session_event trigger 注入、FR-008 兩子句〕／dry-run 零變動／前置全拒）；quickstart S1~S7 全機判單通＋SC-001~008 勾稽全 PASS（U6 專單元：越權雙打 permission denied＋告警四條正反向轉紅復歸＋互斥雙向機器證＋清舊組衛生、pushgateway 末態恰兩分組）。品質＝U1~U7 七單元 implementer＋spec/quality 雙審（quality 累計抓 5 真 blocker：U5 dispatcher 姿態註解漂移、U7 RUNBOOK §5 毀後重建仍雙分組前語意、U6 三筆環境殘留證據不自洽——全修畢複審零）＋final review 雙 Opus 零 merge-blocker（4 advisories：1 修〔測試檔首註解涵蓋 U3〕、1 收刀兌現〔0076 轉 accepted〕、2 備查〔push_heartbeat 失敗分支無自動測屬契約明訂 best-effort、dry-run×低於下限與 execute 同一前置路徑已覆蓋〕）。治理＝ADR 0076 accepted（supersede 0075——「不新增任何自動刪除」「reaper 範圍不含 session_event」就此翻案、其預留條款兌現）＋RUNBOOK §4/§5/§8/§9/§10 連帶＋活書 §6/§7 同步（稽核域自動 retention、reaper 雙 job、告警 13 條）。
- 2026-07-21｜misc｜B-108 收單（RUNBOOK 驗證 WSL2 環境輪執行完畢、詳同日 review 事件與 docs/reviews/20260719-RUNBOOK-verify-wsl.md）——review 事件 schema 無 backlog_done 欄、依 2026-07-17 調規以 misc 輕量軌唯一證據通道記機器證據

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
