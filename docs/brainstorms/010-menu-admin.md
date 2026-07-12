# 010-menu-admin 刀 brainstorm — 選單管理頁＋選單域狀態機（admin 管理面家族第二刀出鞘）

**admin 管理面家族**（role → user → menu → audit → ip-rule 頁；009 brainstorm 定義）。★方向覆蓋
（user 拍板 2026-07-12）：原 NOTES 首選「使用者管理刀」改由 **menu 刀先行**、家族其餘序不變
（user／audit／ip-rule 後續再排）。核心＝把 002 預埋的 **menu 域 7 端點（現況＝零）** 接成活的＋
manage/menu 頁寫側接線＋選單回收桶；**零 seed 變更**（B-060 明確不折入、demo 選單與授權全留）。

上游輸入：**ADR 0023**（casbin 政策 seed 入基線——本刀 7 端點政策全數已 seed、含 protected 的
getDeletedMenus/restoreMenu、零 seed migration）、ADR 0027（`require_policy` 骨架）、ADR 0048/0049/0050
（009 治理狀態機／archive.role_id／明細通道——本刀直接消費）、ADR 0006（軟刪慣例＝partial-uniq＋
讀端濾）、ADR 0002/0004（datetime／13 碼矩陣）；憲法 §I.1（base-web 權威——模板 menu 頁功能面＝設計
下限）、§I.2（選單可見性＝casbin 勾選層治理；demo 全集入 seed **本刀不動**）、§I.3（envelope 凍結、
`PageRes` 形、msg＝i18n key）、§I.5（rust-api 全新寫）、§I.6（六審計欄）、§I.7 島 G（G1~G5——本刀
對偶擴充）、§III.2 (a)(b)(d)（模板接線／button gating／選單復原 re-parent 軌道）；L-015（新 i18n key
後 restart 再 CDP）、L-119（`.vue` template 標記 `<!-- -->`）、L-137（Workflow 發射 CWD 在 repo 根）、
L-138（gate2 假紅先疑 flaky 孤兒列）。

---

## 接地盤點（2026-07-12 偵察、關鍵結論已對照實碼）

- **後端現況**：menu 域端點**零**；002 casbin seed 預埋 7 端點政策——`getMenuList/v2`(GET)、
  `addMenu`(POST)、`updateMenu`(POST)、`deleteMenu`(DELETE)、`batchDeleteMenu`(DELETE)、
  `getDeletedMenus`(GET★protected)、`restoreMenu`(POST★protected)。支撐讀 getMenuTree／getAllPages／
  getAllButtons（009 已活）。`list_active`＝`status=1 AND deleted_at IS NULL`
  （`facade/sys_menu.rs:76`）；getUserRoutes 組樹＝祖先包含、孤兒升根（`sys_menu.rs:93-`）；
  getAllPages＝活性選單 route_name[]（`handler/role.rs:643`）。
- **seed 真相**：sys_menu 78 列（protected 8 列＝home＋manage 樹）；route_name partial-uniq
  `WHERE deleted_at IS NULL`；buttons jsonb；`menu:add/edit/delete` button code 已 seed
  （manage_menu.buttons＋casbin button 列）→ (b) gating 入範圍。casbin menu 維 v1＝route_name
  （009 id↔route_name 映射、讀端 orphan skip 已有）；casbin_rule 無 deleted_at；archive 表＝
  v0..v5 快照＋role_id＋archive_reason。
- **前端現況**：manage/menu 頁模板全套（index.vue＋menu-operate-modal＋shared.ts）；讀側已呼叫
  `fetchGetMenuList`（端點不存在、現況必敗）＋`fetchGetAllPages`；寫側全 stub（modal handleSubmit
  `// request`、index handleDelete/handleBatchDelete）。`MenuList＝PaginatingQueryRecord<Menu>`
  （凍結形）；index 用 `useNaivePaginatedTable` 無參呼叫。
- **B-060 前提驗證**（BACKLOG 動工前偵察紀律）：demo=67 選單＋77 casbin 列、keep=11 屬實；
  gate2 seed 面 `SELECT *` 全列比對、`GLOBAL_SEED_EXCLUDE` 含 deleted_at 不含 deleted_by
  （`tools/schema-gate:140`）→ 軟刪清理會「內容差紅」、硬刪「缺列紅」——**本刀拍板零 seed 變更後
  全部無關**、紀錄供日後參考。
- **009 可復用**：rebuild_enforcer 重建-swap＋有界重試、set_role_dimension／set_role_endpoints
  全量替換寫端、restorable reason gate、mutate_in_txn＋op-log 同交易範式、2222 data 明細插值通道。

---

## 拍板紀錄（2026-07-12~13、user 逐題親決）

| # | 議題 | 拍板 |
|---|---|---|
| D1 | 刀的整體形狀 | **完整 menu 頁刀**：7 端點接活＋頁面寫側接線＋回收桶 UI；規模約 009 的 1/3 |
| D2 | B-060 demo 清理 | **零 seed 變更**（初問硬刪/軟刪、user 拍「不刪」；追問確認＝連 casbin 授權列也不動）：B-060 續留 BACKLOG＋註記、demo 選單維持現狀；無清理 migration、無 SEED_REMOVAL_ALLOWLIST、無 §I.2 Amendment |
| D3 | 非空目錄刪除 | **拒絕**（有活子項→2222 拒因）；批刪照 no-partial |
| D4 | route_name 改名 | **建後不可改**：前端 edit 鎖欄＋後端顯式拒（防繞 UI 靜默縫隙；B-025 鎖鍵欄哲學） |
| D5 | 新建選單可見性 | **兩步流、不自動勾**：addMenu 零 casbin 寫；勾選走 009 角色選單授權 modal（全量替換單一寫入路徑不擴） |

---

## §1 總覽：一台選單域狀態機、零 seed 變更

```
P0  wire 對齊＋facade 讀端（getMenuList/v2、getDeletedMenus）＋序列化域基建
P1  addMenu／updateMenu（不可變欄＋re-parent 環檢測＋parent 驗）
P2  deleteMenu／batchDeleteMenu（守門固定序＋連動歸檔＋拓撲序批刪）
P3  restoreMenu（鎖序對偶）＋009 治理域讀端分層改造
P4  前端接線 (a)(b)(d)＋回收桶 UI
P5  負向自證＋併發機器證＋CDP＋收尾
```

零 migration、零新表、零 seed 變更、零新錯誤碼（reuse `2222`／`0000`／`5003`）、零新依賴。

## §2 選單域序列化域（★對抗式審查 Blocker 折入、本刀治理核心）

**問題**：選單樹是多列關係（parent↔child 活性、環、跨列 button code 判定），且 deleteMenu 要撤銷
「跨全角色」的 menu 維授權——**無單一列可鎖**。009 的 G5 列鎖範式（鎖 sys_role 單列）結構上
無法涵蓋：deleteMenu 鎖選單、updateRoleMenu 鎖角色，兩寫端鎖不相交→READ COMMITTED 下併發
grant 之 phantom INSERT 逃過刪除連動歸檔、殘留 live 授權列→同名重建**靜默繼承**（審查三票全
CONFIRMED blocker×4 鍵）；樹寫端彼此的無鎖 pre-read 亦互刺（活子項掛軟刪父、對向 re-parent
合併成環……審查 confirmed 群）。

**解**：**選單域寫入序列化域**——以 `pg_advisory_xact_lock(<寫死常數 key>)` 將下列寫端納入單一
序列化域，域內固定序＝取 advisory lock→標的列 FOR UPDATE→**鎖內重驗一切前提**（lock-then-redecide）
→寫入→op-log→commit：

- 樹寫端 5 支：addMenu／updateMenu（含 re-parent）／deleteMenu／batchDeleteMenu／restoreMenu。
- 引用選單域的 casbin 寫端（009 碼改動點、各加一行進域＋鎖內重驗）：set_role_dimension 之
  **menu／button 維**（updateRoleMenu／updateRoleButton）、restorePolicy 之 menu／button 維分支。
  endpoint 維不涉選單域、不入域。

代價與理由：admin 治理寫端 QPS≈0、全序列化零效能顧慮；正確性一舉封死「樹 TOCTOU 競態群＋
跨實體 grant 競態群＋button 獨有判定競態」全部；比逐列精緻鎖（FOR SHARE 引用列）簡單、可測、
可入憲。原「批刪 id 升冪取鎖」條款由 advisory lock 域取代（域內單線程、無死鎖面）。

## §3 選單域狀態機（修正後全文）

1. **addMenu**：route_name 形制守門＋partial-uniq 23505→`2222` Conflict；parent 驗（見 7）；
   **零 casbin 寫**（D5 兩步流）。
2. **updateMenu 不可變欄集合＝{route_name, menu_type}**：變更→顯式拒（distinct 拒因、防繞 UI
   直打 API 靜默縫隙；menuType 為審查折入——前端 edit 本就鎖 menuType、後端補對稱強制）。
3. **re-parent**（updateMenu parentId）：域內環檢測（上溯祖先鏈、驗新 parent 非自身或子孫）＋
   parent 驗（見 7）——審查折入：原設計 re-parent 漏 parent 活性驗、與 add/restore 不一致。
4. **status 停用**：顯示域即時消失（下次 getUserRoutes）；**治理域不受影響**（見 §4 分層）。
5. **deleteMenu 守門固定序**（域內鎖內判）：①protected（seed 8 列）→拒；②**存在未軟刪子項**
   （`deleted_at IS NULL`、**不論 status**——審查折入：謂詞釘死、停用子項也擋刪）→拒。
   過門→軟刪＋同交易連動歸檔：**menu 維**（v1=route_name、跨全角色、reason=`menu_soft_delete`、
   role_id=各列所屬角色 id）＋**獨有 button codes** 之 button 維列（code 仍屬任一「未軟刪」選單
   buttons jsonb 者不歸檔、防跨頁共用 code 誤傷；判定在域內＝無競態）→op-log→commit→
   **Applied 才 reload**（009 rebuild-swap 復用、絕不對 live enforcer 裸 load_policy）。
6. **batchDeleteMenu**：no-partial（一項違規→整批零變更）＋**批內拓撲序**（child-first、同 txn
   依序執行、守門逐列於域內判——同批父子共刪時子先刪、父的活子項檢查自然通過；審查折入：
   否則多層子樹批刪結構性不可能）。
7. **parent 驗統一謂詞（三處一致）**：add／re-parent／restore 一律驗「parent 存在且**未軟刪**」；
   **停用 parent 不擋**（停用是暫時態、不阻結構操作；顯示端由組樹祖先語意自然處理）。
   ★此為對原 §B「restore 拒停用 parent」的修正——審查折入三處語意不一致 finding 後統一放寬。
8. **restoreMenu 鎖序**（009 Blocker 1 對偶、域內）：advisory lock→FOR UPDATE 鎖已刪列→
   route_name 活性衝突驗（同名活列在→拒；23505 兜底收斂）→parent 驗（見 7）→復原
   （deleted_at/deleted_by 成對清空）→op-log→commit。**restore 不回灌授權**（重勾、與 D5 一致）。
9. **updateMenu buttons jsonb 編輯＝button 授權一致性**（審查折入、取代原「授權列不動」）：
   移除 code 時，對「移除後不再屬任何未軟刪選單」的 code，同交易連動歸檔其 button 維授權列
   （reason=`menu_button_removed`）；新增 code 零 casbin 寫（兩步流一致）。否則 orphan 授權列
   在 code 重現時跨頁靜默繼承。
10. **role_home 懸空**：009 US6 讀端兜底接住、不做寫端 cascade（明文設計事實）。
11. **parentId wire 映射**：wire `parentId:number`、root＝`0`↔DB `parent_id NULL` 雙向映射；
    parentId=0 豁免 parent 驗與環檢測基底（審查折入：否則建頂層選單被誤拒）。
12. **生效延遲**：API 即時、前端選單等下次 getUserRoutes（009 明文設計事實沿用）。

## §4 治理域／顯示域分層（★審查折入、改 009 讀端）

**問題**（審查 dropped→回收）：停用（status=2）選單從 `list_active` 消失→getMenuTree／getRoleMenu
候選缺席→下一次 updateRoleMenu **全量替換**把停用選單的授權 diff 掉＝「停用」被升級成「靜默永久
撤銷」；getAllButtons 同構。

**解**：讀端分兩域——
- **治理域**（授權勾選候選與映射）：getMenuTree、getRoleMenu 反查、menu_ids_to_route_names、
  getAllButtons 聯集 → 改用「**未軟刪**」集合（含停用；新 facade 讀 `list_governed`）。
- **顯示域**（使用者可見性）：getUserRoutes、getAllPages → 維持 `list_active`
  （status=1 AND 未軟刪）。

009 碼改動點：getMenuTree／getRoleMenu／getAllButtons／menu_ids_to_route_names 四處換域；
行為變更＝勾選 modal 會列出停用選單（合理：停用≠撤銷授權）。

## §5 治理（憲法動作）

- **島 G 增補（G6 選單域）方向、plan 期定稿（MINOR Amendment、user 親決）**：①選單域寫入
  序列化域（§2 全清單、鎖內重驗）；②同名重建零繼承（menu＋button 維；刪除／code 移除即連動
  歸檔）；③樹結構不變式（無環；活子項僅掛未軟刪父；非空目錄不可刪）；④restore 不回灌＋
  reason gate 權威落點在 restorePolicy 的 restore 判定本體（非僅列表旗標）。
  ★入憲位置備選：樹結構不變式非 casbin 側、若 G6 塞不下則拆新島——plan 期 Constitution Check 定。
- **archive reason gate 擴充**：不可手動復原集合 `{role_soft_delete}` →
  `{role_soft_delete, menu_soft_delete, menu_button_removed}`；enforce 於 restore 權威判定。
- **§III.2(d) 字面 Amendment（plan 期提、user 親決）**：(d) 檔案錨＝menu-operate-modal.vue，
  但「顯示已刪除」toggle＋逐列 restore 鈕天然落 index.vue——**不自斷「用途射程內」**、走 §V.2
  正式 Amendment 修 (d) 字面（用途「選單樹復原／父層級調整」不變、錨點擴至 index.vue）。
  ★審查 uncertain finding 之正解。
- **ADR drafts（隨 SDD、user 親決）**：①選單域狀態機總綱（序列化域／守門序／連動歸檔／restore
  語意／不可變欄／兩步流／治理域分層）；②§III.2(d) Amendment＋島 G6 增補案。
- 拒因走 ADR 0050 明細範式：新 `biz.menu.*` key（hasChildren／protectedMenu／routeNameImmutable／
  menuTypeImmutable／routeNameExists／parentNotFound／notRestorable／notFound…spec 期定）＋三語、
  I18N-WIRING (ii) 軌道。

## §6 wire／前端

- `MenuList＝PaginatingQueryRecord<Menu>`（凍結形）；server 語意＝頂層分頁＋children 巢狀
  （wire 凍結形權威、mock 僅補充 fixture）；getDeletedMenus 回傳形 spec 期釘（傾向 PageRes 同形、
  與 toggle 復用同一 table 管線）。
- 凍結 system-manage.ts 不動；寫端四支＋回收桶讀寫→WRAPPER 新檔 `rev4-menu-admin.ts`；
  net-new 型→ADAPT 新 `.d.ts`（鏡像 009 rev4-role-admin 範式）。
- **(a)** modal handleSubmit（add/edit 真打）＋index handleDelete/handleBatchDelete 接線；
  **(d)** toggle 切換列表資料源（OFF＝活性列／ON＝已刪列＋逐列 restore 鈕）＋edit 模式 parentId
  re-parent——落點依 §5 Amendment；**(b)** `hasAuth('menu:add'|'menu:edit'|'menu:delete')` gating。
- i18n 新 key 三語；`.vue` template 標記 `<!-- -->`（L-119）；新 key 後 CDP 前 restart base-web
  （L-015）；本刀不建新頁→route locale 零新增；fork-delta 修改型 inline 帶 `原行:`、每動跑
  fork-delta-lint、worktree commit `--no-verify`。
- 已知限制（明文、不解）：getAllPages 候選＝活性選單自我指涉——被軟刪選單的頁面暫離候選、
  restore 即回；runtime 新增選單之 i18nKey 無對應譯文→前端回退 menuName 顯示。

## §7 錯誤處理

全 reuse：業務拒 `2222`＋HTTP 200＋distinct `biz.menu.*` key；notFound 不靜默；批次拒因帶明細
（ADR 0050 data 插值範式）；23505→`2222` Conflict 收斂；政策拒沿 `require_policy` 5003。
前端 data 插值通道 009 已建、直接消費。

## §8 測試策略（審查折入後）

- **rust**（容器內、全程 serial）：facade／handler 單元＋整合；狀態機 table-driven（守門固定序、
  環檢測含對向成環、parent 謂詞三處一致、獨有 button code 判定〔含共用 code 不誤傷〕、批刪拓撲序、
  no-partial、restore 衝突、parentId=0 映射）；**每條新 route 契約 case**（coverage gate、7 條）。
- **負向自證 5 支**（審查修正）：①拆 protected 守門→測試須 FAIL（測試用**無子項** protected 列＋
  斷言拒因＝protectedMenu、防被 hasChildren 遮蔽恆綠）；②拆環檢測→成環測試須 FAIL；③拆刪除
  連動歸檔→「同名重建零繼承」測試須 FAIL（前置＝**先授權再刪再重建**、確保有可繼承列、防恆綠）；
  ④no-partial 改逐項→整批零變更測試須 FAIL；⑤拆 button 維連動（獨有判定／menu_button_removed）→
  「code 重現零繼承」測試須 FAIL。
- **併發機器證**（審查修正標的）：deleteMenu(parent)×restoreMenu(child)＋deleteMenu×updateRoleMenu
  (menu 維 grant)——advisory lock 序列化以 pg_locks／pg_blocking_pids 觀察等待、證域有效。
- **CDP 實機**：兩步流全鏈（新增→列表可見/sidebar 不可見→勾選→重整可見）；rename／menuType 鎖欄；
  停用即隱＋**停用選單仍在勾選候選**（§4 分層）；刪除守門×2＋成功刪除後**受影響角色選單/按鈕
  實際收縮**＋**共用 button code 他頁存活**（審查折入）＋policy-archive 頁歸檔列（不可復原態）；
  批刪含父子成功（拓撲序）；回收桶 toggle→restore→同名衝突拒；i18n 三語零 raw。
  residue 紀律：建列場景精確清理＋順跑 gate2（L-138）。
- 收刀閘：cargo test 全綠＋typecheck＋fork-delta-lint＋docs-sync 三閘＋契約覆蓋閘。

## §9 BACKLOG／簿記動作（收刀時）

- B-060 **註記**：「010 拍板不折入（零 seed 變更、demo 選單全留）、續留原觸發條件」。
- B-061 不動（audit/ip-rule 譯文隨各自刀）。
- 新增候選：無（審查 findings 全數折入本刀或屬既有條目射程）。

## §10 風險與備註

1. **規模**：7 端點＋一頁接線＋序列化域基建＋009 讀端分層改造，預估 **10~12 執行單元**（審查
   折入後自 8~10 上修）；編排照 CLAUDE.md §2（防呆五件套＋看門狗原子成對＋單元邊界 pin bump）。
2. **009 碼改動點集中**：set_role_dimension（menu/button 維入域）＋restorePolicy（入域）＋
   getMenuTree/getRoleMenu/getAllButtons/menu_ids_to_route_names（治理域換源）——各點既有測試
   連動改寫、迴歸面在 §8 覆蓋。
3. **序列化域為新範式首例**：advisory lock 常數 key 寫死 code；與 009 列鎖並存（域內仍鎖標的列）；
   plan 期 Constitution Check 對 §I.7 逐項過。
4. **對抗式審查已跑**（2026-07-13、設計節核可後）：7 鏡頭×3 異質核驗（全 opus 4.8、10 agents、
   34 raw findings）——詳下節。

---

## 對抗式審查紀錄（2026-07-13）

- **編排**：Workflow `wf_02dcec27-898`＋wf-watchdog 原子成對；7 finder 鏡頭（併發鎖序／授權繼承／
  狀態機／wire 前端／憲法先例／測試驗證／影響半徑）→claim_key 去重（34→24、cap 裁 10 個低嚴重度
  誠實回收）→3 異質核驗（實碼接地／紅隊反證／先例一致性）逐 finding 表決。
  結果：**confirmed 23／refuted 0／uncertain 1**；全數處置如下。
- **缺陷群歸併與折入**（confirmed 23 鍵→6 群）：
  1. **跨實體 grant 競態（真 blocker、三票全 C×4 鍵）**：deleteMenu 連動歸檔×updateRoleMenu grant
     無共同鎖→殘留 live 授權→同名重建繼承。→折入 §2 序列化域。
  2. **樹寫端 TOCTOU 群（2 blocker〔先例鏡頭判 serious〕＋6 serious 鍵）**：restore×delete(parent)、
     add/re-parent×delete、對向 re-parent 成環、re-parent 漏 parent 驗。→折入 §2 域＋§3-3/7/8。
  3. **button 維語意群（5 鍵）**：獨有判定競態、buttons 編輯 orphan 授權、負向自證缺口。
     →折入 §3-5/9＋§8 自證⑤。
  4. **單點語意缺口（4 鍵）**：menuType 不可變後端強制、「活子項」謂詞釘死、parentId=0 映射、
     reason gate 權威落點。→折入 §3-2/5/11＋§5。
  5. **批刪父子互斥（1 鍵）**：→折入 §3-6 拓撲序。
  6. **驗證面失準（1 鍵）**：pg_blocking_pids 標的錯位（delete×restore 無共享鎖可證）。→折入 §8。
- **uncertain 1（票 C/U/R）**：§III.2(d) 檔案錨衝突——採納其紀律主張、不自斷射程，
  →折入 §5 正式 Amendment 途徑。
- **cap 裁掉 10 個逐條回收**：停用×全量替換靜默撤銷（serious）→§4 分層（本刀最重要的非併發
  折入）；其餘 9 個（環檢測併發重複鍵／鎖序死鎖／wire 形釘定／G6 範圍／負向自證①③恆綠風險／
  CDP 收縮驗證）→分別折入 §2/§5/§6/§8、無一遺漏。
- **severity 校準備註**：樹 TOCTOU 群兩鍵 finder 判 blocker、先例鏡頭以「優雅降級升根、無授權
  旁路」主張 serious（票 CCU）——本檔按 serious 口徑記、但修法（序列化域）與 blocker 同刀落地，
  爭議不影響行動。
