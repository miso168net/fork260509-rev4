---
id: "0001"
title: constitution v1.0 重鑄——B6 逐筆過目拍板（17 題）
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:constitution v1.3.0＋rev3:DECISIONS§1（對應 K1 條目見本文表）"
tags: [governance, bootstrap]
---

## 背景

rev4 bootstrap B6：constitution 級的 rev3 承襲候選須經 user 逐筆過目才算正式拍板（無默認繼承）。
以互動式問答一題一拍完成 17 題（2026-07-03、user 逐筆點頭），本 ADR 為該批拍板的唯一正式紀錄；
constitution v1.0.0 全文即拍板結果的凍結載體。

## 決定

| # | 條目 | 拍板 | 出處 |
|---|---|---|---|
| 1 | 凍結邊界（審計欄 archetype＋行為島不變式＋wire 錯誤碼表；常數值留活書）＋MAJOR/MINOR/PATCH 三級修訂 | 沿用 | ｜出處：rev3:DECISIONS§1-待決⑤（K1-05） |
| 2 | 行為島不變式進場時機 | **隨刀進場**（v1.0 §I.7 留空位＋進場規則；每台狀態機隨其刀以 MINOR amendment 入憲）——rev4 新拍板 | ｜出處：（rev3 無此問題——鑄憲時系統已在） |
| 3 | Compliance Check 九題承接；「不增 push/merge 題」封案維持 | 沿用 | ｜出處：rev3:DECISIONS§1-⚠️u（K1-30） |
| 4 | 排程性拍板重議必走 amendment、不得默改 | 沿用 | ｜出處：rev3:DECISIONS§1-⚠️h（K1-17） |
| 5 | 內部錯誤（5000）一律 HTTP 200 信封；business error 走 200 總則 | 沿用 | ｜出處：rev3:DECISIONS§1-⚠️e（K1-14） |
| 6 | 13 碼矩陣整組凍結（含 4 保留碼後端永不發出、優先 reuse） | 沿用 | ｜出處：rev3:DECISIONS§1-⚠️f（K1-15） |
| 7 | id 逐欄位忠實 typings＋DB i64＋2^53 fail-loud＋型別謊言帳本歸零 | 沿用 | ｜出處：rev3:DECISIONS§1-⚠️r（K1-27） |
| 8 | msg＝i18n key、前端翻譯 | 沿用＋**掛 BACKLOG 觀測側可讀性補強候選（B-007）**；措辭釐清一併承接 | ｜出處：rev3:DECISIONS§1-⚠️y（K1-34）＋⚠️ab（K1-37） |
| 9 | 「不動 inline 為預設＋顯式授權軌道制＋新用途必 amendment」總則 | 沿用 | ｜出處：rev3:DECISIONS§1-⚠️i（K1-18） |
| 10 | MODAL-WIRING ★ 初始用途集 | **一次全授 (a)~(g)**（七用途皆 rev3 落地驗證；比照 rev3 對前代已驗證用途的批發授權模式） | ｜出處：rev3:constitution§III.2（(f)＝⚠️af/K1-42、(g)＝⚠️ah/K1-44） |
| 11 | 「單頁純加零新資源＝補完不修憲；跨頁新能力＝須修憲」判準 | **成文寫入憲法**（§III.2 紀律） | ｜出處：rev3:DECISIONS§1-⚠️ag（K1-43） |
| 12 | I18N-WIRING ★ 三範圍 | 照授（zh-TW 首發 locale 字典同循範圍 (ii)） | ｜出處：rev3:DECISIONS§1-⚠️aa（K1-36） |
| 13 | 前代源碼受控參照（讀允許／拷貝禁止／防回歸）＋工具 crate 整檔拷貝例外 | 沿用（對象更新＝rev3 為主、rev2 溯源） | ｜出處：rev3:DECISIONS§1-⚠️g（K1-16）＋sub-crate 拍板 |
| 14 | fork 差異標記紀律（修改型原行註解／新增型圈界／統一 token／rebase 同步更新） | 沿用（token 改 `rev4-inline`） | ｜出處：rev3:DECISIONS§1-⚠️s（K1-28） |
| 15 | 無 retrofit 條款 | **條款＋範圍釋義一起寫入**（標的＝archetype 審計欄；規劃性 domain 欄演進不在此限） | ｜出處：rev3:DECISIONS§1-⚠️ac（K1-39） |
| 16 | 角色軟刪同交易清授權＋FOR UPDATE 併發防護 | **不入 v1.0；B8 立 ADR、隨對應刀作為行為島不變式入憲**（循第 2 題規則） | ｜出處：rev3:DECISIONS§1-P-011-1（K1-38） |
| 17 | 其餘承接整批：A 承接（base-web 權威／Casbin enforce／權威序／帳號命名／unknown header／demo seed／dynamic route／`/api` 前綴）；B 不預載（alova 端點包、obs 排程、alt-login stub 排程——B8 逐筆重審）；C 機械改寫（分支名、token、brainstorm 路徑、文件系統引用、權威鏈） | 照單執行 | ｜出處：rev3:constitution §I.1~I.3＋§II（#1/#2/#4/#5/#7/#8/#11/#12/#13） |

## 後果

- constitution v1.0.0 於同 commit 落地（Ratified 2026-07-03）；後續改動一律 Amendment（ADR＋版本 bump）。
- §I.7 行為島為空位：對應刀開跑時，brainstorm 以 rev3 已驗證不變式為直接輸入、收刀前隨刀 amendment 入憲（MINOR）。
- BACKLOG 新增 B-007（觀測側 msg 可讀性補強候選）。
- 未入本批的 K1 條目（含 7 筆開放項）續走 B8 處置流水；排程性拍板於入波排程時逐筆重審。
