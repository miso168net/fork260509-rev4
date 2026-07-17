---
id: "0066"
title: global-content 頁面切換 Transition 去 out-in＋fade-slide leave absolute——上游 isLeaving 卡死 workaround
date: 2026-07-17
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-17 user 實機回報（快速連點左側 menu 後 main 永久空渲染、點 tab 無法恢復）＋主線 CDP 診斷（B-104 證據鏈）＋spike 實證＋user 親決選型（同日）；憲法 v1.13.0 (j) 新用途首案"
tags: [layout, transition, upstream-bug, workaround, base-web]
---

## 背景

base-web 頁面切換動畫走 `layouts/modules/global-content/index.vue` 的 `Transition mode="out-in"`＋`KeepAlive` 組合（soybean 上游原檔、零 fork 改動；Vue 3.5.34 lockfile 版本）。快速連續導航（~80ms 間隔、肉手快速連點左側 menu 即達）會觸發 Vue `BaseTransition` 的競態：`state.isLeaving` 卡在 `true`，此後 render 函式**永久回傳空佔位**——main（`#__SCROLL_EL_ID__`）空白，且後續點 tab／menu／內建刷新鈕（`reloadFlag` toggle）全部無效，**唯一復原＝整頁 F5**。

診斷證據鏈（2026-07-17 CDP、逐項消去）：route 匹配正常且 `components.default` 在（排除路由層）；`reloadFlag=true`（排除 reload 機制）；關動畫仍空（排除動畫進行中表層）；`reloadFlag` toggle 救不回（證明空洞在 `v-if` 之上的 Transition 層）；煙槍＝`contentXScrollable` 恆 `true`（`@before-leave` 已跑、`@after-enter` 從未跑）。重現法＝新分頁 80ms 間隔連續 `router.push` 14 次（40ms 不中——須正中 fade-slide ~300ms leave 窗）。歸屬＝上游（vuejs/core `out-in`＋`KeepAlive` 已知 bug 族；rev3 同構同病）。

## 決策

採「去 out-in＋leave absolute」（user 親決 2026-07-17、spike 實證後三案擇一）：

1. `global-content/index.vue`：Transition 移除 `mode="out-in"`（改預設並行模式）——`isLeaving` 卡死路徑機制上不存在（該狀態為 out-in 專屬）。修改型 inline、原行逐字標。
2. `src/styles/css/transition.css`：`.fade-slide-leave-active` 加 `position: absolute`（Vue 官方並行模式建議形）——舊頁脫離文檔流、新舊頁原地交疊淡出淡入（cross-fade）、零版面跳動。`fade-slide` 類全站唯一消費點＝global-content 頁面切換（`theme.page.animateMode`），副作用面窄。

Spike 實證（worktree 熱改＋CDP 新分頁）：去 out-in 後 80/60/120ms 三輪連打全綠（同條件 out-in 版 80ms 必卡）；代價＝轉場 300ms 交疊期並行節點（單次導航 2、連打風暴峰值 6）——由第 2 項 absolute 化消除版面下擠。

## 候選與落選

- **僅去 out-in（不動 CSS）**：卡死同樣根除，但舊頁淡出期間仍佔文檔流、新頁被下擠 300ms＝輕微版面跳動——落選（多改一檔即可消除）。
- **預設關頁面動畫（page.animate=false）**：治標——isLeaving 機制仍在、使用者於主題抽屜開回動畫即復發——落選。
- **導航防抖（menu/tab 點擊節流）**：治標（程式化導航不經 menu 仍可觸發）且同樣要動軌道外 layout 檔（global-menu）——落選。
- **升級 Vue 等上游修**：3.5.34 已為 lockfile 現版且實測仍卡；升版屬版本治理面、回歸面大、時程不可控——不採、留 upstream rebase 時覆核（B-104 條目原註記精神）。

## 驗收與殘餘

- 機器閘：typecheck＋`python3 tools/fork-delta-lint`（global-content 修改型原行標、transition.css 修改型原行標）。
- CDP 雙驗證：①80/60/120ms 連打不卡（卡死指紋——main 空＋`contentXScrollable` 恆 true——不再出現）②正常導航轉場交疊零版面跳動（absolute 生效、新舊頁 offsetTop 同位）。
- 殘餘風險：absolute 定位依賴 main 滾動容器的定位上下文——實作期以 CDP 幾何量測驗證；其他 animateMode（fade／fade-bottom 等）未 absolute 化，切換該模式時舊頁下擠輕微跳動仍在（僅 fade-slide＝預設模式收口；他模式屬同形擴充、需要時援引本 ADR 加列）。
- 復原路（若 workaround 引入回歸）：revert 兩檔即回上游原形（bug 復existing、F5 復原法仍在）。
