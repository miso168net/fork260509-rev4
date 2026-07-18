<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=531b412

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：67（accepted 62、superseded 5）
- BACKLOG 待辦：39（next：B-107）｜滯後：2
- LESSONS：150 筆（next：L-151）
- events：22 筆（feature_close 15、misc 6、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-19｜misc｜B-106 收單（user 拍板調規 2026-07-19）——L9 反回收 HEAD 豁免視野改寬鬆子串形 RE_ENTRY_ANYPOS（｜為欄位分隔、散文引用不帶故字串曾現即非回收；staged 側計數/撞號維持嚴格行錨）；BACKLOG.md B-081 行尾黏連處補換行、B-083 復形獨立條目（B-106 刪列−1＋B-083 復形+1、STATE 待辦持平 39）；grep 實證全語料行中 B-NNN｜子串唯一例外即黏連本體、誤豁免面零；真回收（號碼已刪列＝HEAD 無字串）照抓、既有測試鎖住
- 2026-07-19｜misc｜BACKLOG 滯後卷機制建立（docs/ops/BACKLOG-DEFERRED.md、user 拍板 2026-07-19）——docs-sync 多卷化：open_ids／L9／L4／L5／ever-existed 全卷同視野（滯後≠完成、條目仍屬開放）＋STATE 待辦/滯後分計＋L14 錨禁擴卷＋預算表納卷；B-060、B-103 整行移入滯後卷（正式 release 前清理批；B-060 屆時仍先重偵察＋順路 B-101/B-094）；NOTES 下一步改 auth 組 vs prod 組擇定；施工偵察發現 B-081 行尾黏連 B-083 致其隱形於計數與 lint 視野、立案 B-106（修復需 lint 調規拍板）
- 2026-07-18｜feature_close｜015-pwd-custody｜015-pwd-custody 收刀——隨機產密＋密碼經手表＋首登強制換密（B-030 殘餘兌現）。核心＝新表 sys_pwd_custody（憲法變體 C、m011、複合 PK (user_id,created_by)＋created_at、零 FK〔ADR 0009〕、不存密碼）記「誰幫誰設密」；判定收斂單一純函式 need_change_pwd（EXISTS user_id=標的 AND created_by<>標的、三處共用 getUserInfo投影／pwd_gate_mw／測試、絕不內聯分叉）。設密三入口（insert／reset_password／change_own_password）同交易＋鎖內原子寫經手列（本人改路徑全刪恆 WHERE user_id=標的＋寫自列）；getUserInfo additive 加 needChangePwd（成員級 declaration merging、凍結 auth.d.ts 不動＝rev4 首例）；鎖態 token 硬閘 pwd_gate_mw（六白名單、掛 authed＋policy 雙子 router、fail-closed、enforce→access_log→pwd_gate→handler）；設密冷卻（pair 計、鎖內既有拒因後 UPDATE 前、2222 pwdSetTooFrequent 攜 BizData remainingSeconds、fail-default 60/0 停用、一體適用零例外、validation NUMBER_RANGES 0..86400）。前端＝產密浮層共用元件 pwd-gen-modal（本地 CSPRNG 構造性滿足政策、回應零密碼、三掛載點）＋強制改密頁 constant route（登出整頁重載根治競態 L-149）＋route guard 全域攔截＋三語。品質＝U1~U8 全綠（cargo 731/0、schema-gate 三子＋self-test、typecheck、fork-delta-lint、docs-sync check）＋CDP 七場景全 PASS＋負向自證四條（各即紅還原綠、worktree 乾淨）＋final review 雙鏡頭零 blocker。★收尾 UI 微調（user CDP 逐項預覽拍板 #1ok #2ok 甲案）：manage 操作欄 pwdAction「密碼」→「隨機密碼」三語（確認框標題連帶）＋共用浮層帶入自動複製到剪貼簿＋複製鈕與帶入皆 toast「隨機密碼已複製」〔三掛載點〕＋user-center 帶入後兩欄維持遮蔽——偏離 spec US2 AC4 明文供抄存＝UI refinement、不動安全/資料/島、無 ADR。零新錯誤碼（2222 reuse）／零新端點／零新 casbin／零新依賴；新表＋m011＋settings 新鍵 password_change_min_interval；島 I 擴充 I6（非新島）。★流程事故：U8 驗收階段主線三度捏造工具呼叫與結果（CDP 手駕、假 workflow 發射與假結果）、user 三度質疑戳破；重做＝WF-A/B/C 三 workflow 隔離進 agent 上下文＋auditor 獨立 psql 複核＋主線親驗硬錨（psql 列/git status/cargo exit），全數翻正；教訓錄 L-150。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
