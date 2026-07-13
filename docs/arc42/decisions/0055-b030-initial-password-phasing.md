---
id: "0055"
title: B-030 初始密碼拆階段——admin 指定＋政策驗證先行；隨機生成＋首登強制改密延後、綁自助改密
date: 2026-07-14
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-13 011-user-admin brainstorm D4／D5（user 逐題親決：自助改密不入留 BACKLOG 新條；B-030 整包延後）；spec Clarifications（B-030 做多深）＋FR-029；BACKLOG B-030 觸發條件隨收刀簿記改「自助改密落地後」"
tags: [password, onboarding, phasing, backlog]
---

## 背景

B-030（初始密碼隨機生成＋首登強制改密）源自密碼生命週期的安全訴求：管理員知悉初始密碼的窗口
應最小化。011 是密碼政策的第一個真實執行刀（addUser 初始密碼＋resetUserPassword），B-030 的
掛點自然浮現：本刀做多深？

全包（隨機生成＋首登強制改密）的真實成本盤點（2026-07-13 偵察＋brainstorm D5 親決）：
- **首登強制改密需 schema 變更**：sys_user 須加「須改密」旗標欄（002 凍結基線無此欄）——
  撞本刀「零 schema 變更」邊界（FR-041）。
- **需 login 流程插閘**：登入成功後攔強制改密態、導向強制改密頁——動 005 既有 auth 碼的第二處
  （本刀已因 B1 動 run_login/run_refresh，再疊強制改密閘＝風險面翻倍）。
- **需自助改密能力為前置**：強制改密頁本質＝自助改密（驗舊密→換新密→撤其他 session）的受迫
  變體；而自助改密（user-center、受眾＝登入者本人、§III.2(g) 軌道）D4 親決不入本刀、自成一塊。
- **需隨機密碼的傳遞通道設計**（顯示一次／複製／有效期）——UX 與安全語意皆非本刀射程。

## 決定

**B-030 拆階段（D5 親決）**：

- **本刀（011）交付**：admin 指定初始密碼＋密碼政策驗證（單一驗證點、ADR 0054）——addUser 的
  password 必填、經 `validate_against_policy` 守門；resetUserPassword 覆蓋「忘記密碼」救援
  （管理面重設、B-029 主路）。初始密碼安全底線＝政策 enforcement（管理員可設強政策使弱初始密碼
  進不來）。
- **延後（不在本刀）**：初始密碼隨機生成＋首登強制改密整包——**觸發條件改綁「自助改密
  （user-center）落地後」**（收刀簿記時改寫 B-030 條目；新增「自助改密」BACKLOG 條目為其前置）。
  屆時所需 schema 加欄（須改密旗標）與 login 插閘隨該刀走各自的 Amendment／migration 程序。
- **不變式（落地時必守）**：隨機生成與首登強制改密落地時，密碼驗證 MUST 複用 ADR 0054 單一
  驗證點（禁止分叉）；強制改密流程 MUST 沿島 I2 撤 session 連動語意（改密撤他 session、保留
  當前操作 session）。

## 後果

- 011 保持零 schema 變更、auth 碼觸面收束於 B1 一處（run_login/run_refresh 鎖內重驗）——風險
  可控、負向自證與併發機器證聚焦。
- 「管理員知悉初始密碼」窗口暫存續（admin 指定＝admin 知悉）——以政策 enforcement＋改密撤
  session 兜底；此為有意識接受的階段性取捨（spec 設計取捨節明文）。
- BACKLOG 簿記（收刀）：B-030 觸發條件改寫＋新增「自助改密（user-center、驗舊密→換新密→撤其他
  session）」條目；B-029 主路消化。
- 若未來親決改變（如 demo 需先行首登改密），推翻本拆階段＝立新 ADR supersede 本檔。
