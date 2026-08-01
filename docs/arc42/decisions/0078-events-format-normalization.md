---
id: "0078"
title: events.jsonl append-only 例外——機器可證語意不變的格式正規化允許動既有列（獨立勘誤 commit 逐筆附證據）
date: 2026-07-28
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-28 018-governance-hardening brainstorm §4 ADR draft 候選（user 親決「events 史料 4 筆 7 位短 SHA 一次性正規化、規則不帶史料豁免」）＋spec Clarifications（append-only 射程＝DB 資料表、不及文件帳本，零 amendment）；research R8／R9、contracts G3、data-model §4；首例＝本刀 T010 勘誤 commit"
tags: [governance, events, lint, docs-system]
---

## 背景

`docs/ops/events.jsonl` 是 rev4 文件系統的**事件源**材質：一行一事件、只往後追加，收刀與
review 的簿記全落在這裡，機器生成的 MILESTONES／STATE 都由它重算。實務上這份帳本被當成
「動不得」的——只 append、不改既有列。

018 這一刀要把帳本升級成**機器自證**：每列的 `merge` 與 `pins` SHA 逐列拿去問 git，抄錯、
造假、事後改史都會當場紅（contracts G3、FR-010）。條款要生效，SHA 格式必須先統一：帳本裡
有 4 筆是 7 位短 SHA（列 12 `71c68bb`、列 14 `e7c2daf`、列 15 `9d4b47c`、列 17 `0a3f790`，
分別屬 011-user-admin／012-audit-admin／013-ip-rule-admin／014-user-center 四刀），其餘 47
筆是 40 位。

於是撞上一個治理問題：**要收緊格式，就得動既有列**——而既有列「不可改」正是帳本的信用來源。
兩條路：規則帶史料豁免（`RE_SHA` 永遠接受 7~40 位，雙格式共存），或一次性把 4 筆展開、
規則此後全域收 40。前者讓「格式」這件事永遠有兩套答案，新列也就永遠能偷渡短 SHA；後者要
正面回答「什麼情況下可以動既有列」。本 ADR 回答後者。

## 決策

1. **append-only 的約束射程：憲法 §I.6 變體 B 管的是資料庫的 append-only 日誌表，不及於文件
   帳本**。變體 B（連同 §I.7 島 J3 的 retention 釋義）約束的是三個 log 表的 schema 與寫入
   語意——無 soft-delete、無 update、不可竄改，那是**執行期系統對使用者資料的承諾**。
   `docs/ops/events.jsonl` 是版控在 git 裡的文件材質，其不可竄改性由 git 物件圖與 review
   保證，不由憲法變體 B 保證。故本 ADR **零 constitution amendment**（spec Clarifications
   已拍板事項），只是把文件帳本這一側的規則寫清楚。

2. **例外的定義：機器可證語意不變的格式修正，允許動既有列**。合格條件三項，缺一不可：
   - **語意不變可由機器證明**：不是「我看起來一樣」，而是有一條任何人都能重跑的命令輸出
     同一結論。本刀的證明是 `git rev-parse <短 SHA>^{commit}` 展開後與寫入值逐字相同、
     且 `git cat-file -t` 為 `commit`——短寫與全寫指向同一個 git 物件。
   - **修正屬格式面，不動事實面**：可以改的是同一事實的書寫形（SHA 的位數、鍵序、空白），
     不可以改的是事實本身（哪一刀、哪一天、收了哪些 ADR、消化了哪些 BACKLOG 條目）。事實
     錯了不走本例外——那是新事件、或勘誤事件，不是格式修正。
   - **獨立勘誤 commit、逐筆附證據**：正規化必須自己一個 commit（內容純粹、零條款碼、零
     其他**人寫**文件改動；`generate` 連帶重算的機器生成物同 commit 落地——`check` 閘要求
     生成物與來源一致，分開落反而製造紅窗），commit message 逐筆列「舊值 → 新值」與所屬
     feature，並說明機器證據怎麼取得。證據住 commit message＝住 git 史，日後任何人做 `git log` 或 `git blame`
     都直接看得到「這一列為什麼被動過」。

3. **首例＝本刀 T010 的四筆短 SHA 展開**（列 12／14／15／17 的 `merge` 欄，7 位 → 40 位）。
   四筆皆已預核可解為 commit 物件；勘誤 commit 落地後跑 `generate` 對賬（MILESTONES 的
   merge 欄連帶重算，屬預期）。

4. **順序寫死：正規化 commit 必須先於條款上線 commit**。先落格式修正、再落
   `RE_SHA` 收 40 與逐列實證條款——條款上線那一刻帳本已經是乾淨的，引擎不會被自己新增的
   規則打紅。反過來做會產生一段「庫是紅的」窗口期，而窗口期紅是紀律最容易被繞過的時候。

5. **此後帳本無任何格式豁免分支**：`RE_SHA` 全域 `[0-9a-f]{40}`，新列與舊列一體適用；
   工具內不留「舊列從寬」的旁路。要再動既有列，一律重走本 ADR 的三項條件——沒有第二條路徑，
   也不接受在工具裡加一個 inline 例外把某列跳過（同 ADR 0077 對 inline 豁免 marker 的
   立場：繞過閘的權力不交給任何單次 commit）。

## 後果

- 帳本的「不可改」從一句慣例升級為**有條件、有程序、有證據**的規則：條件是機器可證語意
  不變，程序是獨立勘誤 commit，證據是 commit message 與 git 物件圖。日後遇到同型需求
  （例如另一種書寫形統一）不必再開一次治理討論，照本 ADR 的三項條件走即可。
- 代價是每次格式修正都多一個 commit 與一份逐筆對照——這是刻意的摩擦：讓「動既有列」永遠
  是一件顯眼、可稽核、要打字的事，而不是順手夾在別的 commit 裡。
- 條款側的連帶：`RE_SHA` 收 40 後，任何人手寫新列若貼了短 SHA 會被 L3 (Lint03) schema 當場擋下
  （lint 紅、pre-commit 不放行），而不是靜默寫進帳本、等到日後對賬才發現對不上。
- 本例外**不是**改史授權：git 史本身（已 commit 的內容、已推遠端的物件）不在射程內；
  帳本裡記錄的事實面錯誤，處置方式是補一筆新事件，不是回頭改舊列。
