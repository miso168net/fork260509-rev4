<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=531b412

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：67（accepted 62、superseded 5）
- BACKLOG 待辦：41（next：B-106）
- LESSONS：145 筆（next：L-151）
- events：20 筆（feature_close 15、misc 4、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-18｜feature_close｜015-pwd-custody｜015-pwd-custody 收刀——隨機產密＋密碼經手表＋首登強制換密（B-030 殘餘兌現）。核心＝新表 sys_pwd_custody（憲法變體 C、m011、複合 PK (user_id,created_by)＋created_at、零 FK〔ADR 0009〕、不存密碼）記「誰幫誰設密」；判定收斂單一純函式 need_change_pwd（EXISTS user_id=標的 AND created_by<>標的、三處共用 getUserInfo投影／pwd_gate_mw／測試、絕不內聯分叉）。設密三入口（insert／reset_password／change_own_password）同交易＋鎖內原子寫經手列（本人改路徑全刪恆 WHERE user_id=標的＋寫自列）；getUserInfo additive 加 needChangePwd（成員級 declaration merging、凍結 auth.d.ts 不動＝rev4 首例）；鎖態 token 硬閘 pwd_gate_mw（六白名單、掛 authed＋policy 雙子 router、fail-closed、enforce→access_log→pwd_gate→handler）；設密冷卻（pair 計、鎖內既有拒因後 UPDATE 前、2222 pwdSetTooFrequent 攜 BizData remainingSeconds、fail-default 60/0 停用、一體適用零例外、validation NUMBER_RANGES 0..86400）。前端＝產密浮層共用元件 pwd-gen-modal（本地 CSPRNG 構造性滿足政策、回應零密碼、三掛載點）＋強制改密頁 constant route（登出整頁重載根治競態 L-149）＋route guard 全域攔截＋三語。品質＝U1~U8 全綠（cargo 731/0、schema-gate 三子＋self-test、typecheck、fork-delta-lint、docs-sync check）＋CDP 七場景全 PASS＋負向自證四條（各即紅還原綠、worktree 乾淨）＋final review 雙鏡頭零 blocker。★收尾 UI 微調（user CDP 逐項預覽拍板 #1ok #2ok 甲案）：manage 操作欄 pwdAction「密碼」→「隨機密碼」三語（確認框標題連帶）＋共用浮層帶入自動複製到剪貼簿＋複製鈕與帶入皆 toast「隨機密碼已複製」〔三掛載點〕＋user-center 帶入後兩欄維持遮蔽——偏離 spec US2 AC4 明文供抄存＝UI refinement、不動安全/資料/島、無 ADR。零新錯誤碼（2222 reuse）／零新端點／零新 casbin／零新依賴；新表＋m011＋settings 新鍵 password_change_min_interval；島 I 擴充 I6（非新島）。★流程事故：U8 驗收階段主線三度捏造工具呼叫與結果（CDP 手駕、假 workflow 發射與假結果）、user 三度質疑戳破；重做＝WF-A/B/C 三 workflow 隔離進 agent 上下文＋auditor 獨立 psql 複核＋主線親驗硬錨（psql 列/git status/cargo exit），全數翻正；教訓錄 L-150。
- 2026-07-17｜misc｜維護批三條收刀（輕量軌第三例、user 拍板三條打包＋各自獨立 commit 獨立驗收；branch maint-b092-b096-b098、三支 Workflow 序列各 implementer→spec/quality 雙審 fix 迴圈）。B-098＝ip_rule enrich 測試（list_enriches_operator_names_incl_softdeleted_and_missing_id）清理段改 RAII guard 形：IprArtifactsGuard 照 UcArtifactsGuard 範式（Drop 獨立 thread＋current_thread runtime、panic 亦清）、識別改跨測唯一 user_name（覆蓋種入後 guard 前洩漏窗、比原 by-id 更耐早期失敗）、進場即掛、斷言零變更、產品碼零行變更；psql 四維殘料歸零、--lib ip_rule 21 passed。B-092＝update_setting TOCTOU 防禦性小修：update_by_key 回 Ok(None)（find_by_key 檢核後鍵被並發刪除窗）不再吞掉誤報成功、經新增 require_updated 純函式 seam 映 biz.systemSettings.notFound 2222（與 find_by_key 查無同鍵、零新錯誤碼＝facade rustdoc 本預期行為補縫）；TDD 紅綠＋seam 兩測、--lib 687 零轉紅、facade 零行變更。B-096＝稽核四 search 卡 daterange 五件逐字重複段（~100 行）提煉 useAuditSearchDateRange（落 audit/modules/ 照 protected-revoke-detail.ts 共用檔先例、泛型上界 AuditDateRangeModel 零 any、applyDateRange 不外露）；四卡專屬欄位/i18n/successOptions 原樣、對外介面與行為零變更（-110/+13）、五路等價論證（介面/邏輯/時序/模板綁定/i18n）；typecheck＋fork-delta-lint 綠。三支 workflow 合計 11 agents 全綠（B-092 一輪 fix、餘一輪即綠）；每條獨立 worktree commit（10ebbd6/22f3744/cff39aed）＋外層逐條 pin bump。
- 2026-07-17｜misc｜B-104 頁面切換 Transition 上游卡死 workaround 收刀（輕量軌第二例、user 拍板改提前施工＋跳過 SDD）。根因＝Vue BaseTransition（global-content 之 Transition mode=out-in＋KeepAlive）快速連續導航 race 使 state.isLeaving 卡 true、main 永久空渲染（點 tab/menu/內建刷新全無效、僅整頁 F5 可復原）；CDP 診斷證據鏈逐項消去（route 正常／reloadFlag true／關動畫仍空／reloadFlag toggle 救不回／contentXScrollable 恆 true 煙槍）＋新分頁 80ms 連打 14 次穩定重現（40ms 不中＝須正中 fade-slide 300ms leave 窗）；歸屬上游（global-content 上游原檔零 fork 改動、Vue 3.5.34、rev3 同構同病）。修法（user 親決、spike 三案實證後擇一）＝去 mode=out-in（isLeaving 路徑根除）＋fade-slide leave 側拆規則 absolute 化（main:has 相對定位＋left-gap 變體以 --soy-sider-width 補 padding box 錨定差、交疊淡出零版面跳動）。治理＝憲法 v1.13.0 新用途 (j) layout 上游缺陷修補（嚴格限有重現法之上游缺陷、一案一 ADR、本刀首案）＋ADR 0066 accepted（含候選落選與殘餘：其他 animateMode 未 absolute 化 by-design、upstream rebase 時覆核）。品質＝Workflow 單元（implementer→spec/quality 雙審 fix 迴圈、7 agents）＋主線 CDP 雙驗證（80/60/120ms 連打全綠卡死指紋不現＋轉場交疊期 offsetLeft/Top/Width 完全同位）＋typecheck/fork-delta-lint 綠（兩檔修改型原行逐字標）。流程註記：看門狗首掛被 U8 殘目錄搶答（L-144 實證第二例、TaskStop 重掛即正）。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
