---
id: "0051"
title: 選單域狀態機總綱——序列化域＋同鍵重建零繼承＋治理域／顯示域分層（島 H 設計理據）
date: 2026-07-13
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-13 010-menu-admin brainstorm D1~D5（user 逐題親決）＋對抗式多鏡頭審查 23 confirmed 全折入＋plan Phase 0 research R1（序列化域）／R2（治理域分層）／R6（button 絕版一致性）；憲法 v1.8.0 島 H 之設計理據檔（Amendment 本身＝ADR 0052）"
tags: [menu, state-machine, concurrency, authz, governance]
---

## 背景

010-menu-admin 把 002 就預埋好的 menu 域 7 端點（getMenuList/v2、addMenu、updateMenu、deleteMenu、batchDeleteMenu、getDeletedMenus〔protected〕、restoreMenu〔protected〕）接成活的——選單生命週期＋選單回收桶，**零 seed 變更**（D2、demo 選單與其授權全留、B-060 不折入）、零 migration、零新錯誤碼。

選單與角色的關鍵差異＝**選單是多列樹關係**（parent↔child 活性、環、跨列 button code 共用），且 deleteMenu 要撤銷「跨全角色」的可見性授權——**無單一列可鎖**。009 島 G5 的「鎖標的角色列」範式在此結構上無法涵蓋：deleteMenu 鎖選單、updateRoleMenu 鎖角色，兩寫端鎖不相交→READ COMMITTED 下併發 grant 之 phantom INSERT 逃過刪除連動歸檔、殘留 live 授權列→同路由鍵重建靜默繼承。對抗式多鏡頭審查（2026-07-13、7 鏡頭×3 異質核驗、10 agents、34 raw findings）此破口三票全 CONFIRMED blocker（4 鍵同缺陷）；樹寫端彼此的無鎖 pre-read 亦互刺（活子項掛軟刪父、對向 re-parent 合併成環）。審查 confirmed 23／refuted 0／uncertain 1，全數折入 spec 與本設計。

## 決定

選單域為新行為島（島 H），五條不變式之設計理據如下（條文本身入憲＝ADR 0052／憲法 v1.8.0）：

- **H1 序列化域（R1）**：以 DB 交易級 advisory 鎖（`pg_advisory_xact_lock`、key 值＝常數留活書）把選單樹五寫端＋009 的選單維／按鈕維授權寫端（`set_role_dimension` menu/button、`restorePolicy`）納入單一序列化域，域內固定序＝取域鎖→標的列 `FOR UPDATE`→鎖內重驗全部守門→寫＋連動歸檔→op-log→commit→Applied 才 reload（沿 009 重建-swap）。端點維寫端不涉選單、不入域。理由：多列關係無單列可鎖，逐列精緻鎖易漏（審查已證），全序列化對 QPS≈0 的管理寫端零效能代價、可測可入憲；域內單線程使「樹 TOCTOU 競態群＋跨實體 grant 競態群＋button 獨有判定競態」全部結構性不可達。
- **H2 同鍵重建零繼承（R6）**：deleteMenu 同交易連動歸檔（menu 維跨全角色 reason=`menu_soft_delete`＋該選單「獨有」button code 之 button 維列）；updateMenu 移除 button code 致其全域絕版時亦歸檔（reason=`menu_button_removed`）。獨有判定＝jsonb containment 查「是否仍屬任一未刪選單」、域內執行故無競態、排除自身故共用 code 不誤傷。此三 reason 歸檔列不可手動復原（gate enforce 於 restorePolicy 權威判定、與 list 旗標單點共用防漂移）。零繼承雙封：現役無殘留（序列化域）＋歸檔不可回灌（reason gate）——與島 G3 撤銷必歸檔同源、選單實體側對偶。
- **H3 樹結構不變式**：改父層過防環檢查（上溯祖先鏈遇自身→拒、上溯上限常數）；parent 驗三處一致（新增／改父層／復原＝父存在且未刪、停用不擋、parentId=0 頂層豁免）；deleteMenu 守門固定序①受保護②存在未刪子項（不論啟停）；批刪 no-partial＋child-first 拓撲序（否則同批父子結構性必拒——審查折入）。域內單線程使「活子掛軟刪父」「對向 re-parent 成環」結構性不可達。對偶島 G4。
- **H4 不可變錨欄＋兩域分層（R2）**：`route_name`（casbin v1 錨／i18n 錨）與 `menu_type` 建後不可變（後端顯式拒、防繞 UI 靜默縫隙；審查折入 menu_type）。讀端分兩域——治理域（授權候選與映射、`list_governed`＝未刪含停用）／顯示域（使用者可見性、`list_active`＝啟用且未刪）；否則停用選單自治理候選消失→下次全量替換把「停用」靜默升級「永久撤銷」（審查 dropped 回收之最重非併發折入）。009 讀端換源四處（getMenuTree／getRoleMenu 反查／menu_ids_to_route_names／getAllButtons）。
- **H5 復原不回灌**：restoreMenu 域內鎖列＋重驗（同鍵活性衝突 23505 兜底收斂／父層未刪）→成對清空 deleted_at/by＋原 status 保留；不回灌授權——復原後零授權、經授權面板重勾（與新增選單兩步流一致、D5）。

## 後果

- **零 migration／零新表／零 seed 變更／零新錯誤碼／零新依賴**——`archive_reason varchar(32)` 僅取值集合加二值（欄型不變）；7 端點政策已 seed（seed 列 25/28/29/30/31/64/65）零政策遷移；010 為 admin 家族至今治理面最乾淨一刀。
- **兩步流的體驗代價**（新增／復原後須顯式勾選才可見）以文檔與 CDP 驗收場景明示；治理面授權授予路徑單一（009 全量替換）、不擴。
- **009 連動改動**：治理讀端換口徑（授權面板將列出停用選單、user 已核可）＋選單維／按鈕維寫端入序列化域（加強非改變、advisory 先於既有列鎖、鎖內重驗沿既有）——既有測試斷言連動改寫。
- **審查缺陷群溯源**（可回溯性）：跨實體 grant 競態→H1；樹 TOCTOU 群→H1＋H3；button 維語意群→H2；單點語意缺口（menuType／謂詞／parentId=0／reason gate 落點）→H3/H4；批刪父子互斥→H3；驗證面失準（pg_blocking_pids 標的、button 守門自證）→測試面（負向自證 5 支＋併發機器證 3 組）。uncertain 1（§III.2(d) 錨衝突）→ADR 0052 (d) 錨點擴充。
- **role_home 懸空**由 009 US6 讀端兜底承接（FR-039）、本刀零寫端 cascade；「首頁指向被刪選單」驗收案例錨定。
- casbin reload 沿用 009 rebuild-swap（絕不對 live enforcer 裸呼 load_policy）；序列化域為新範式首例，未來新選單域寫端 MUST 入域。
