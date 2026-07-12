---
id: "0048"
title: 憲法 §I.7 行為島進場——島 G（casbin 授權治理）＋MODAL-WIRING (a) 檔名枚舉澄清
date: 2026-07-12
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-12 009-role-admin plan Constitution Check Q9（新島 G 進場＝MINOR Amendment）＋analyze A1 拍板甲案（(a) 枚舉澄清升必辦、user 親決 2026-07-12）；拍板鏈＝brainstorm D1~D7＋對抗式審查兩 blocker 折入"
tags: [constitution-amendment, security, authz, governance]
---

## 背景

009-role-admin 落地角色管理與 casbin 授權治理寫端（全量替換、受保護拒絕、撤銷必歸檔、回收桶復原）——為新行為島，依 §V.3「行為島隨刀進場」以 MINOR Amendment 入憲 §I.7。同 Amendment 順載 MODAL-WIRING (a) 檔名枚舉澄清（analyze A1：原「補完判準四條件全中」論證被打掉兩條〔stub 接線＝修改型非純加；wrapper＝本刀新建非既有〕，user 拍甲案——擴句明文授權、白紙黑字）。

對抗式多鏡頭審查（2026-07-12、7 鏡頭×3 核驗）兩 blocker 已折入本島條文：①restorePolicy 納入 FOR UPDATE 鎖序（G5）；②判定面同步失敗契約（G1、casbin 2.20.0 `load_policy` 實碼核實為 clear-then-load）。

## 決定

**§I.7 新增島 G — casbin 授權治理（009、ADR 0049 歸檔 role_id／0050 明細通道）**，方向性面凍結（反轉＝MAJOR）、常數/欄級留活書：

- **G1（真相唯一與同步失敗契約）**：授權真相＝DB 政策表；授權變更與其操作稽核 MUST 同一交易落地、絕不走判定引擎管理 API 寫面（DB-first）；判定面由真相全量重載導出（Applied 含空 diff 才觸發、Rejected/NoOp/NotFound 不觸發）。★同步失敗契約：重載 MUST 以「**重建成功才 swap**」實現、絕不對 live 判定面就地 clear-then-load；失敗→**保留上一份已知良好判定面**（絕不空窗或半載）＋結構化告警＋有界重試，耗盡仍失敗→維持舊面持續告警（恢復待下次成功同步或維運介入）。★方向反轉（同步失敗改為清空／全 deny）＝MAJOR。
- **G2（受保護拒絕）**：撤銷集觸及 protected 政策→整批拒絕、零變更（任何寫之前判定）＋結構化明細；un-protect／re-protect 經一般管理介面永不提供（防鎖死 by-design；保護集變更屬 seed 基線層級決策）。
- **G3（撤銷必歸檔）**：revoke＝archive-move（完整快照＋來源角色識別 role_id＋reason 區分）、grant＝INSERT 補齊治理欄（protected=false＋created_at/by）；刪角色 MUST 同交易全維連動歸檔（含 protected 列、reason=`role_soft_delete`）；`role_soft_delete` 列 MUST NOT 可手動復原；角色刪除單向、無 role restore。
- **G4（刪除守門與批次原子）**：刪除依固定序三層守門（①seeded ②in-use ③self-role）；批次逐項驗證、任一違規**整批拒**（no-partial）、單一交易。
- **G5（復原同實例與全端點鎖序）**：一切向現役授權寫入、或改動角色活性／啟用狀態的寫端（三維寫入、**授權復原**、刪除、停用）MUST 同交易 `FOR UPDATE` 鎖標的角色列、**鎖內重判前提**後才落寫（lock-then-redecide——與島 B2 同範式的授權面對應〔類比引用、L-075；B2 射程仍限 token 面〕、永不信 pre-read）；復原判定＝reason≠`role_soft_delete` **且** 現存同 code 活角色 `id == 歸檔列 role_id`（同實例；NULL→不可復原、誠實退化）。★未來 `sys_user_role` 指派寫端落地時 MUST 同納本鎖序（跨刀鉤子、BACKLOG 條目綁定）。

**MODAL-WIRING (a) 檔名枚舉澄清**（§III.2 軌道邊界擴展、MINOR；analyze A1 甲案）——(a) 條目擴句：

> **(a)** `// request` placeholder 接線：`modules/*-operate-{modal,drawer}.vue`（create/update）與 `index.vue` 的 delete/batchDelete handler，**及同頁 `modules/*-auth-modal.vue` 既有 placeholder 接線；附屬模板行為小修（如 search reset 補 emit('search')）同屬本用途**

憲法 MINOR bump（§V.3「行為島隨刀進場」＋「軌道授權邊界擴展」）→ **v1.6.0 → v1.7.0**。島 G 全文＋(a) 擴句入憲、與本 ADR 同 commit。

## 後果

- 009 plan Constitution Check Q9 GATE 解除；Q2/Q7 的 (a) 歸屬爭議白紙黑字收口（T015/T022/T035 授權前提成立、U11/U12 可開工）。
- 附帶拍板記載（拍板歸 ADR、條文歸活書、不入 G 條文）：**停用斷權＝D6**（roles_of_user 解出口徑加 status=1 濾；「活性」一詞專指 deleted_at IS NULL）＋**停用雙護欄**（不可停用自己所屬角色＋R_SUPER 恆禁停用，spec FR-014/015）；**前端生效延遲語意**（顯隱等下次載入、不做推播）落點＝收刀活書更新；**roleHome**＝寫端不驗一致性＋讀端兜底（首頁不在可見樹→先序第一可導航葉頁；spec FR-037/039、005 as-built 勘誤連動）。（若日後欲將停用類守門升為 G 條文＝顯式擴項、另行 Amendment。）
- 島 G 方向性面凍結：後續刀改「整批拒」為部分成功、改「keep-last-good」為清空、拔鎖序、開放 un-protect UI——皆 MAJOR；常數（重試次數、role_code 形制上限）留活書可調。
- casbin 版本鎖註記：G1 同步失敗契約的技術根據釘 casbin 2.20.0（load_policy＝clear-then-load）；升版 MUST 重核該語意（實作留特性鎖定測試）。
