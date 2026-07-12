---
id: "0052"
title: 憲法 §I.7 行為島進場——島 H（選單域生命週期與授權連動）＋§III.2(d) 錨點擴充＋1.7.0 log 補記（v1.8.0）
date: 2026-07-13
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-13 010-menu-admin plan Constitution Check Q9（新島 H 進場＝MINOR）＋Q2/Q7（§III.2(d) 錨點擴充＝MINOR）；三處 user 逐題親決 2026-07-13〔新島 H 案／(d) 錨點核可修訂案／1.7.0 log 隨 v1.8.0 補記〕；島 H 設計理據＝ADR 0051"
tags: [constitution-amendment, menu, state-machine, governance, errata]
---

## 背景

010-menu-admin plan 期 Constitution Check 觸發三處憲法動作，皆 user 於 2026-07-13 逐題親決：

1. **島 H 進場（Q9、MINOR）**：選單域為新狀態機。其一半為純樹結構不變式（無環、父子活性、非空目錄不可刪），**不屬島 G「casbin 授權治理」標題射程**（對抗式審查亦指出此錯位）；另一半（連動歸檔／零繼承／不回灌）為島 G3/G5 之選單實體側對偶、可用條文交叉引用承載。spec Assumptions 原留「島 G 增補 G6 vs 拆新島、plan 期定」——user 親決**新島 H 案**（照 §I.7 進場規則「一台狀態機一島」慣例；A~G 各一台）。
2. **§III.2(d) 錨點擴充（Q2/Q7、MINOR）**：(d) 現行檔案錨僅 `menu-operate-modal.vue`，但「顯示已刪除」toggle（切換列表資料源）與逐列 restore 鈕天然落列表頁 `index.vue`、塞進編輯 modal 做不出合理 UI。對抗式審查此為 uncertain finding（票 C/U/R）、主張不可自斷「用途射程內」須走正式 Amendment——user 親決**核可修訂案**（用途字串「選單樹復原／父層級調整」一字不動、僅錨點列舉擴充）。
3. **1.7.0 Amendment log 補記（PATCH 級勘誤）**：plan 期發現憲法 Version 標 1.7.0（009 島 G 入憲、commit 821997a）但尾部 Amendment log 節止於 1.6.0、缺 1.7.0 對應行——009 收刀遺留的文檔漂移。user 親決**隨 v1.8.0 一併補記**。

## 決定

**§I.7 新增島 H — 選單域生命週期與授權連動（010、ADR 0051 總綱）**，方向性面凍結（反轉＝MAJOR）、常數/欄級留活書：

- **H1 選單域寫入序列化域**：選單樹五寫端（新增／編輯／刪除／批次刪除／復原）與選單維、按鈕維授權寫端（含授權回收桶復原之選單／按鈕維分支）MUST 於單一序列化域內互斥執行（DB 交易級 advisory 域鎖為載體、key 值留活書）；每一寫端 MUST 於域內鎖定標的並**重驗全部守門前提後才落寫**（lock-then-redecide、永不信 pre-read；與島 G5／B2 同範式）。端點維授權寫入不涉選單域、不屬本域。★方向反轉（拆散序列化域、改回無域逐列鎖或無鎖 pre-read）＝MAJOR。
- **H2 同鍵重建零繼承**：選單軟刪 MUST 同交易將其選單維授權（跨全角色）連動歸檔（reason=`menu_soft_delete`）；該選單「獨有」按鈕代碼（刪除後不再屬任何未刪選單）之按鈕維授權亦同交易歸檔；編輯移除按鈕代碼致其全域絕版時同理（reason=`menu_button_removed`）。此三類 reason 之歸檔列 MUST NOT 可手動復原（gate enforce 於復原權威判定）。同路由鍵重建之新選單 MUST NOT 經任何路徑（現役殘留、回收桶復原）繼承舊實例授權（單向不變式，與島 G3 撤銷必歸檔同源、選單實體側對偶）。
- **H3 樹結構不變式**：選單樹恆無環（改父層 MUST 過防環檢查）；活性子項 MUST NOT 掛於已軟刪父層之下；受保護種子選單 MUST NOT 可刪；存在未刪子項（不論啟用停用）之目錄 MUST NOT 可刪；批次刪除逐項驗證、任一違規**整批拒**（no-partial、單一交易、child-first 拓撲序）。此對偶島 G4 之選單實體側。
- **H4 不可變錨欄與治理域／顯示域分層**：`route_name`（授權列 v1 錨／i18n 錨）與 `menu_type` 建後不可變（寫端 MUST 顯式拒變更、MUST NOT 靜默忽略）；選單讀端分兩域——**治理域**（授權候選與映射）以「未軟刪」全集為準（含停用）、**顯示域**（使用者可見性）以「啟用且未軟刪」為準；停用 MUST NOT 使全量替換語意誤撤停用選單的授權（停用＝暫時下架、非撤銷）。
- **H5 復原不回灌**：選單復原 MUST 於序列化域內鎖定並重驗守門（同路由鍵活性衝突／父層未刪）；復原 MUST NOT 回灌任何授權——復原後選單零授權，可見性一律經授權面板重新勾選下放（與新增選單之兩步流一致）。

**§III.2(d) 錨點擴充**（軌道授權邊界擴展、MINOR；用途字串不動）——(d) 條目改為：

> **(d)** 選單復原／re-parent 維運控制：`menu-operate-modal.vue` edit 模式 parentId selector＋`views/manage/menu/index.vue` 的「顯示已刪除」列表切換（toggle）＋逐列 restore 鈕＋對應 i18n key——嚴格限「選單樹復原／父層級調整」

**Amendment log 補記＋新增＋version bump**：補失落之 1.7.0 行（島 G 進場＋(a) 枚舉澄清、觸發 009、PATCH 級勘誤）＋新增 1.8.0 行（本 Amendment）＋version `1.7.0 → 1.8.0`、Last Amended `2026-07-12 → 2026-07-13`。

憲法 MINOR bump（§V.3「行為島隨刀進場」＋「軌道授權邊界擴展」）→ **v1.7.0 → v1.8.0**。島 H 全文＋(d) 擴句＋log 補記入憲、與本 ADR＋ADR 0051 同 commit。

## 後果

- 010 plan Constitution Check Q9/Q2/Q7 GATE 解除；(d) 錨點擴充使 tasks T019（index.vue toggle＋restore 鈕接線）授權前提成立——「未過不施工」條件於本 Amendment 落地後解除。
- 島 H 方向性面凍結：後續刀拆散序列化域、改「整批拒」為部分成功、開放 route_name/menu_type 可變、拔連動歸檔、回灌復原授權——皆 MAJOR；常數（advisory key、上溯上限、route_name 形制上限）留活書可調。
- 1.7.0 log 補記後，Amendment log 與 Version 行一致（勘誤閉合）；日後版本算術以本次 1.8.0 為基準。
- 島 H 與島 G 為對偶關係（H2↔G3、H1/H5 鎖序↔G5、H3↔G4），條文以交叉引用承載、不重複條文本體；未來 user 頁刀（B-064）的 sys_user_role 指派寫端仍受島 G5 跨刀鉤子約束（與本島無涉）。
