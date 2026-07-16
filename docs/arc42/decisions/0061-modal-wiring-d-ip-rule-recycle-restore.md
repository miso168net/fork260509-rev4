---
id: "0061"
title: 憲法 amend——MODAL-WIRING (d) 擴字串涵蓋 IP 規則回收桶復原（v1.10.0→v1.11.0 MINOR）
date: 2026-07-16
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-16 013-ip-rule-admin brainstorm（user 親決 D1 混排回收桶／D2 復原鈕走擴 (d)）；憲法前例＝v1.8.0 擴 (d) 至 menu 頁、v1.9.0 擴 (d) 至 user 頁回收桶（兩次 MINOR）"
tags: [ip-rule, constitution, modal-wiring, recycle-bin, amendment, backlog]
---

## 背景

013-ip-rule-admin 建 IP 規則管理面（MODAL-WIRING (e)「同 manage 範式新管理頁」主軌道）。頁含
軟刪列的逐列 restore 鈕（D1＝混排單清單、無 toggle：後端 getIpRuleList 為 hybrid 端點、含軟刪列
active 沉頂 deleted 殿後，前端以 deleted NTag 欄辨識、已刪列只顯復原鈕）。

MODAL-WIRING (d)（constitution §III.2 MODAL-WIRING 款）字面枚舉三用途「選單樹復原／父層級調整／使用者回收桶復原」
（錨點含 `menu-operate-modal.vue` edit 模式 parentId selector 為 re-parent 錨、與本案無涉）；**頁級
回收桶錨點僅 `views/manage/menu/index.vue` 與 `views/manage/user/index.vue` 兩頁**——逐字核實**無
ip-rule**。憲法沿革顯示「新頁回收桶 UI 非 (e) 天然涵蓋」：menu 頁與 user 頁的回收桶各以一次 MINOR
擴 (d) 授權（v1.8.0、v1.9.0），非靠 (e) 鏡像自動涵蓋。故 013 的 ip-rule 回收桶復原 UI 須顯式擴 (d)。

## 決定

- **擴 MODAL-WIRING (d) 用途字串**加「IP 規則回收桶復原」、錨點加 `views/manage/ip-rule/index.vue`
  混排清單（含已刪列顯示與狀態欄辨識、無 toggle）的逐列 restore 鈕。標頭 (a)~(i) 用途款集**不新增**
  （本次只擴 (d) 既有款字串、不立新用途 (j)）。
- **after 逐字終稿**（accepted 時據此改 constitution §III.2 MODAL-WIRING (d) 款，防省略號壓縮丟字面）：
  「**(d)** 選單／使用者／IP 規則復原、re-parent 維運控制：`menu-operate-modal.vue` edit 模式 parentId
  selector＋`views/manage/menu/index.vue` 與 `views/manage/user/index.vue` 的「顯示已刪除」列表切換
  （toggle）＋逐列 restore 鈕＋`views/manage/ip-rule/index.vue` 混排清單（含已刪列顯示與狀態欄辨識、
  無 toggle）的逐列 restore 鈕＋對應 i18n key——嚴格限「選單樹復原／父層級調整／使用者回收桶復原／
  IP 規則回收桶復原」」（★ip-rule 為混排無 toggle、異於 menu/user 的 toggle 形，故字面明寫；顯示面
  一併納入授權字面、不落 (d)/(e) 之間縫隙）。
- **版本**：MINOR（既有款擴字串／擴錨點；§V.3「軌道授權邊界擴展（新用途／新範圍）」＝MINOR，
  v1.8.0/v1.9.0 同判例）；v1.10.0→**v1.11.0**。
- **不需其他 amendment**：搜尋卡＝(e) 鏡像 user 頁；hasAuth 按鈕＝(b)；DELETE 接線＝WRAPPER 新檔
  （§III.1 預設軌道）＋(e) 新頁消費端點（013 全新檔零 placeholder、不掛 (a)）；i18n＝route-locale-隨
  頁走＋I18N-WIRING (ii)(iii)——全既有軌道，零額外用途款。
- **程序（§V.2）**：本檔 draft 隨 013 brainstorm 同 commit；spec 定稿期 user 親決轉 accepted、
  改 constitution.md (d) 款＋bump v1.11.0、獨立 commit `docs(constitution): amend`＋docs-sync generate。

## 後果

- **正**：ip-rule 回收桶復原有顯式軌道授權、與 menu/user 一致；紀律「新頁回收桶須顯式 (d) 授權」
  三度落實、判例穩固。
- **考量過的替代**：論證 (e)「鏡像 user/role/menu 結構」已隱含涵蓋 restore 鈕（零 amendment）——
  否決，因憲法沿革（menu/user 各自 MINOR 擴 (d)）明示 (e) 不天然涵蓋回收桶 UI，寬鬆讀法破「嚴格限」
  紀律精神。另考量：因 013 restore 鈕帶按鈕碼（hasAuth ipRule:restore，D5）、可主張純 (a)+(b) 涵蓋——
  否決，因 (b) 治「可見性 gating」、(d) 治「有回收桶復原這個用途」，兩軸正交、皆需。
- **負**：憲法 (d) 款字串隨每個帶回收桶的新頁增長（menu→user→ip-rule）；可接受（枚舉式授權的誠實成本）。
