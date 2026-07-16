---
id: "0063"
title: ip-rule RBAC 按鈕碼 seed＋sys_menu.buttons 回填——為未來非-super 授權下放預留完整基建（B-083 前置鏈）
date: 2026-07-16
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-16 013-ip-rule-admin brainstorm（user 親決 D5 保留按鈕碼、provenance 明述「未來 ip-rule 會下放權限給非 R_SUPER 其它角色」；D8 buttons 回填走 B-mech）；家族前例＝011 user 頁 seed user:restore 等四支按鈕碼（super-only 頁亦 seed、但未回填 sys_menu.buttons）；反例＝012 audit 頁零按鈕碼（super-only 免 hasAuth）"
tags: [ip-rule, rbac, casbin, seed, authorization-delegation, b-083]
---

## 背景

ip-rule 五端點全 super-only（casbin 只 seed R_SUPER route 政策、m002 選單列 buttons=NULL、零按鈕碼）。
012 audit 頁（同 super-only）選零按鈕碼、整頁免 hasAuth。013 選保留按鈕碼，provenance 明述：
**未來 ip-rule 功能會下放權限給非 R_SUPER 的其它角色**——按鈕碼非裝飾、而是為未來授權下放**預留基建**。

★審查揭露一個「等同 011」同構的缺口：角色頁按鈕權限指派面板的候選來源＝`getAllButtons`＝
`sys_menu.buttons` 欄聯集（role.rs getAllButtons／SC-002 契約測試）。若只 seed casbin 政策列、不回填
`manage_ip-rule.buttons`（NULL），未來下放刀經面板**根本勾不到** `ipRule:*` 四碼。011 正是此缺口
（m008 只 seed casbin、`manage_user.buttons` 至今僅 add/edit/delete、`user:restore` 等四碼同樣不在面板候選）。

## 決定

- **casbin 按鈕政策 seed**（additive）：`ipRule:add`／`ipRule:edit`／`ipRule:delete`／`ipRule:restore`
  於 R_SUPER 底下；schema-gate `SEED_ADDITIVE_ALLOWLIST` 加對應列（ADR 0032/0039 範式）。
- **回填 `sys_menu.buttons`**（D8、走 B-mech）：同 migration `UPDATE manage_ip-rule` 列的 buttons 欄＝
  四碼 jsonb，使 `ipRule:*` 進角色頁指派面板候選。此為「改既有凍結 seed 列內容」（非 additive）→走
  **ADR 0064 的 `SEED_CONTENT_OVERRIDE_ALLOWLIST`** 登記 `(sys_menu, manage_ip-rule, buttons)`＝預期四碼。
- **前端 hasAuth gating**（MODAL-WIRING (b)）：index.vue 四操作鈕掛 `hasAuth('ipRule:*')`。
- **明確界定：本刀不構成授權下放**——按鈕碼＋buttons 候選當下僅可指派給 R_SUPER 的既有全權；非 super
  角色未獲任何 ipRule:* 政策；013 不觸 B-083（B-083 觸發前提＝使非 super 獲 ipRule:* 政策之行為）。

## 後果

- **正**：未來下放非 super 時，前端 hasAuth 軌道、casbin 碼、**面板候選（buttons）三者皆就位**，下放刀
  只需經角色頁指派政策列＋補 B-083 護欄，無 seed 回填殘工。
- **★B-083 前置鏈（forward-link，MUST 遵守；行為級非刀級）**：★**任何使非 R_SUPER 角色獲得 ipRule:*
  政策之行為**（含經 009 role 頁執行期指派、非必然另起「下放刀」）皆屬授權下放、同受 B-083 約束，MUST
  先建三護欄——①非超管寫端「不得授出超過自身所有」no-escalation 上限檢查（FR-045）②seeded 受保護護欄
  與「超管恆禁停用」結構護欄複評（FR-015/FR-018）③明細通道受眾邊界重評（FR-035／ADR 0050——明細「自查
  等價」前提隨受眾改變即失效）。★**殘餘風險：此前置鏈無機器強制、依賴流程紀律**（009 已有執行期指派通道、
  營運操作即可完成下放而不觸發任何「刀」）；本 ADR 為其 forward-link 錨。B-083 不因 013 刪列、續待落實。
- **H2 歸檔缺口 decouple**：`manage_ip-rule`（protected=false、可軟刪）被軟刪時，其獨有按鈕碼是否連動歸檔
  依島 H2、判定源自 buttons 欄；本刀回填 buttons 後 H2 標的存在，但**歸檔覆蓋的通用正確性**（casbin 按鈕碼
  與 sys_menu.buttons 聯集在各種軟刪路徑下的一致性）交未來通用「系統軟刪掃描」刀，另記 BACKLOG，013 不解。
- **011 同款缺口不順手補**：`manage_user.buttons` 的 user:restore 等四碼面板缺口屬 011 域既存債、013 不蔓延
  修（保持本刀專注）；另記 BACKLOG 追蹤「casbin 按鈕碼與 sys_menu.buttons 聯集漂移（m008 四碼＋013 四碼）」。
- **負**：super-only 現況下按鈕碼＋buttons 回填零當下實益、代價＝一支 migration（additive casbin＋
  content-override buttons）＋ADR 0064 新機制＋本 ADR；user 知情拍板（未來下放預留）、非隱性膨脹。
