---
id: "0041"
title: §III.2「補完 vs 新能力判準」之「零新 key」釋義（不含既有授權頁既有子命名空間下的資料級 label key）
date: 2026-07-10
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-10 007-login-throttle /speckit-analyze 的 C1 finding（CRITICAL、經獨立 skeptic 反駁驗證確認）＋user 親決 2026-07-10（§V.2；選項 (c) 釋義而非擴軌道）"
tags: [constitution-amendment, governance, fork-delta, base-web, i18n]
---

## 背景

007 的 US6 要在**既有授權**的系統設定頁（004 依 `MODAL-WIRING` 用途 (e) 建置）新增三個節流門檻設定鍵，
並為其補上 i18n label——`page.manage.systemSettings.items.*` 三語譯文與 `app.d.ts` 的型別鏡像。

`/speckit-analyze` 的憲法鏡頭指出一個 CRITICAL 級問題：§III.2 的「補完 vs 新能力判準」逐字要求
「單頁、純加、復用既有 wrapper、**零新 key**/元件/路由」**四條件全中**才算用途補完；新增 i18n key 使
「零新 key」直接不成立。而用途 (e) 授權的標的是「同 manage 範式**新管理頁**建置（含對應 route 與 i18n key）」
——004 已用畢，007 未建新頁、無法回頭套用。

若照字面套用，則**未來每一支新增 runtime 可調設定鍵的刀，都必須走一次 §V.2 Amendment**。

反向先例（同一鏡頭挖出）：006 seed `session_idle_timeout` 時**未加** `labelKeyMap`、**未加**任何
`page.manage` key，走 seed `description` fallback、零頁面改動——而該做法正是 BACKLOG **B-059** 追蹤的病灶
（三語 UI 直顯繁體 seed 描述、zh-CN／en-US 下腳本不符）。

## 決定

**釋義**（★非授權擴展、非邊界放寬）：§III.2「補完 vs 新能力判準」中的「**零新 key**」，指
**新 i18n 命名空間／新元件／新路由等「面」級的新增**；**不含**「既有授權頁、既有子命名空間之下的
**資料級 label key**」（例：`page.manage.systemSettings.items.<newKey>` 的三語譯文與其型別鏡像）。

依據三點：

1. **判準所舉的例子本身即不需新 key**。原文括號內的例示為「同頁補一種值型別的 render 控件分支」
   ——那是純 dispatcher 邏輯，天然零新 key。「零新 key」是在**描述該例示的形狀**，而非一條獨立的禁令。
2. **立法目的是限制 fork-delta 對 upstream 的衝突面**（§III 開篇：「upstream 常態更新，本紀律使 fork 差異在
   rebase 時可快速定位」）。`page.manage.systemSettings` 子樹係 004 新建的**我方領土**、已在 `rev4-inline`
   圈界內；於其下加 key 對 upstream 衝突面的擴大**近乎零**。
3. **字面套用逾越立法目的**：使「新增一個 runtime 可調設定鍵」這種常規演進恆需憲法 Amendment，
   且會制度性地把開發者推向 006 的 `description` fallback ——即 B-059 的病灶。

### ★仍受約束者（本釋義不放寬）

- 新增 **top-level i18n 命名空間**（如 `backend`）⇒ 仍走 `I18N-WIRING` 用途 (ii)。
- 新增 **route locale key** ⇒ 仍須**隨建頁走**、不得單獨新增（§III.2 (e)；B-061 語境）。
- 新增**元件／路由／跨頁能力** ⇒ 仍須 §V.2 Amendment。
- 動 **upstream 既有命名空間**（非我方新建子樹）之下的 key ⇒ **不在本釋義範圍**。
- 判準其餘三條件「單頁、純加、復用既有 wrapper」與「零新元件/路由」⇒ **仍須全中**。

### 憲法動作

§III.2 判準句後加一句釋義；version **1.4.0 → 1.4.1**（**PATCH**，§V.3「文字校正、釐清」）。

## 後果

- 007 的 T072／T073（設定頁 `labelKeyMap` 三鍵映射＋`numberRanges`＋三語 label 譯文＋型別鏡像）
  **屬用途補完**，得以照做、無須第二次 Amendment。
- 未來設定刀新增 `number`／`enum` 設定鍵並補 label 譯文，一律屬用途補完；plan Constitution Check
  Q2/Q7 仍須逐項紀錄改動位置與 upstream 衝突風險（§III.2 紀律不變）。
- **B-059 的病灶不再被制度性複製**：006 的 `description` fallback 屬特例、非典範。
  007 落 settings 三鍵時同檔已動，B-059 後作摩擦更小。
- ★本 ADR 是**釋義**：判準的其餘三條件、以及其他四條軌道的邊界，一律不受影響。
- 本次釋義源自 `/speckit-analyze` 的機器化跨 artifact 檢查——該閘在 tasks 生成後、implement 之前攔下，
  避免執行單元照 T072 原文（其引用判準時**恰好漏引「零新 key」**）自檢誤判為通過而逕行施工。
