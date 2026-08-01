---
id: "0085"
title: 帳號 email 驗證＝驗證即提交×已驗證值衛星表×partial unique——B-028 信箱半邊兌現選型
date: 2026-07-31
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-31 020-email-verify-smtp brainstorm——四鏡頭研究（wf_471a7c74）＋user 親決 9 題（含衛星表取代加欄、created_{at,by} 成對兩次 user 主動升級）；clarify 4 題親決（解除綁定／captcha 前置／admin 格式守門無豁免／冷卻拒因攜秒數）＋plan 3 鏡頭對抗式驗證校正（wf_f9597e2e：節流原子先佔、captcha ctx 語境欄、updateUser 清空契約、變體 C 釋義）"
tags: [auth, email, schema, security, user-center]
---

## 背景

B-028（手機/信箱真實驗證）信箱半邊。現況：`sys_user.user_email` 可空、無唯一約束、零索引、
無驗證態欄；後端零 email 格式驗證；user-center email 卡驗證碼組為純佔位。下一刀 G-Suite SSO
以「已驗證 email」對映帳號，唯一性與驗證語意是其前提。效仿對象 GitLab 走連結式驗證，本系統
依現成 UI 與 dev 可達性拍碼式。

## 決策（user 親決 2026-07-31；細節見 docs/brainstorms/020-email-verify-smtp.md §1 D1~D4、D9）

1. **驗證流形＝六位驗證碼回填**：信件載短效六位數字碼、user 於 user-center 回填完成驗證；
   無對外 base URL 依賴（dev/內網可跑）、現成三件式 UI 直接接上。
2. **驗證即提交**：新 email 驗過碼才寫入 `sys_user.user_email`（同 txn 併衛星 upsert＋op-log）；
   庫無 pending 態、驗證中狀態活在無狀態 token。決定性論證：partial unique 之下「先存後驗」
   使未驗證值佔用唯一額度＝佔位攻擊面（任何人可先存別人信箱擋住真擁有者），驗證即提交結構性
   消滅之。副作用：updateProfile DTO 移除 `userEmail` 欄（堵直寫後門、四欄→三欄）。
3. **已驗證值衛星表 `sys_user_email_verify`**（取代 sys_user 加欄——sys_user 從未加欄、功能態
   走衛星表為既成範式 m004/m011）：`user_id` 單一 PK＋`verified_email`（驗過的值、原樣保存）＋
   `verified_at`（upsert 刷新）＋`created_at`/`created_by`（首建成對、upsert 不動）；零 FK
   （ADR 0009 對齊）、硬刪、變體 C（m011 同形）。**已驗證＝比對導出**
   `lower(sys_user.user_email)=lower(verified_email)`、不存狀態欄——admin 改 email 衛星列自然
   失配→自動未驗證，任何現在與未來寫入路徑零清除義務（結構保證、非程序紀律）。變體 C 歸類
   釋義（隨 (g) 擴字串 Amendment 併入親決）：1:1 已驗證值衛星表之 upsert 刷新＝重驗事件覆寫、
   `verified_at` 即其時戳、不設 `updated_{at,by}`——§I.6 成對條款於此形之權威釋義（m011 為零
   可變欄先例、本表為變體 C 可變欄首例）。
4. **email partial unique**：`lower(user_email)` 唯一、`WHERE deleted_at IS NULL AND
   user_email IS NOT NULL`（未填不受限、軟刪不佔用、大小寫同一；沿 user_name 先例形；純索引、
   sys_user 零欄位改動）。
5. **admin 填寫恆未驗證**：驗證語意＝擁有者本人證明控制權；由決策 3 結構兌現。語意註記：
   admin 改回曾驗過的舊值→已驗證自動恢復（證明事件確實發生過、op-log 有軌；GitLab confirmed
   同語意）。
6. **token 範式＝007 captcha 簽題平移**：claims `{nonce, uid, new_email, exp, code_mac}`、
   HS256 獨立金鑰 `email_verify_secret`、`code_mac=SHA256(secret‖nonce‖碼)`、TTL 600s；兩處
   刻意偏差——容 3 次嘗試（redis INCR 計數；email 往返成本高）、成功才消耗（SET NX）。
7. **發碼節流＝原子先佔＋失敗回補**（plan 對抗式驗證校正——原 check-then-act 案可被多張預解
   captcha 題並發突發整批穿透、已撤）：冷卻鍵 SET NX EX 60 先佔＋日計數原子 INCR（UTC 日、上限
   10、超限回補）；寄信失敗盡力回補（回補失敗＝寧誤擋不誤寄）；唯一性預檢排先佔後、命中不回補
   （枚舉抑制）；常數寫死；redis 不可用 fail-closed＋結構化降級告警；不掛 login throttle 狀態機
   （B-102 結構原因同源）。唯一衝突誠實回報（防枚舉 collapse 口徑僅屬 login 家族）。
8. **發碼前置 captcha＝機器強制語境隔離**（clarify 親決加閘、plan 校正定形）：複用 captcha 模組
   與既有 captcha_secret、claims additive 加 `ctx` 欄（login／email 兩端簽發與驗證各自斷言、
   零新金鑰；login 行為零改動、舊題 TTL 內自然過期）；email 語境 subject＝uid 字串；提交即消耗
   照 E4 語意。fail 方向耦合（login 側島 E1 fail-OPEN vs 本刀 fail-closed 同池 used 鍵）＝ctx
   斷言分流、於此明記。驗證提交與解除綁定不受此閘。
9. **解除綁定**（clarify 親決、否決「接受能力消失」推薦案）：新自助端點、確認後清空信箱；驗證
   記錄留存不動（清空＝失配呈未驗證、非刪驗證史）；無寄信、無 captcha、不計節流；同 txn op-log；
   updateProfile 移欄後自助信箱寫入僅兩路徑＝驗證提交（換值）＋解除綁定（清空）。
10. **admin 格式守門＝單一驗證點、無「值未變豁免」**（clarify user 自訂案）：sendEmailCode／
    addUser／updateUser 共用 `validate_email_format`（trim／基本形／長度 ≤254）；存量怪值於
    admin 下次觸及即被迫修正或清空；updateUser 沿 011 FR-007 契約（None 不動；Some 空字串＝
    清空、跳過守門；Some 非空才驗——plan 校正、防清空能力被靜默降級）；唯一性雙層（預檢＋DB
    索引兜底映射 2222）。

## 候選與落選

- 連結式驗證／碼＋連結並行（D1 落選：base URL 依賴、掃描器誤觸、UI 重做／攻擊面倍增）。
- 先存後驗（D3 落選：佔位攻擊面＋四態複雜度）。
- sys_user 加欄 `email_verified_at`（D9 落選：破壞衛星表範式、動共用 entity、清除靠各寫入
  路徑自律）；衛星表鏡像現值＋狀態欄（D9 落選：同一事實兩個家、漏同步即靜默假態）。
- 不加唯一／full unique 含軟刪（D2 落選）；admin 視同已驗證／可勾選標記（D4 落選）。
- 接受自助清空能力消失／updateProfile 保留僅收空值特例（clarify Q1 落選）；發碼不加 captcha
  （clarify Q2 落選）；admin 格式守門不加／加且值未變豁免（clarify Q3 落選）；發碼回應帶冷卻
  截止＋前端持久化（clarify Q4 落選）。
- 節流 check-then-act＋「captcha 單耗抑制並發」論證（plan 對抗式驗證推翻、撤）；captcha 跨語境
  「subject 形制擋死」論證（同上、撤——loginCaptcha 屬 Public 對任意字串發題）。

## 驗收與殘餘

- SC：E2E 真鏈路（寄達且碼可驗）；錯 3 次即廢＋冷卻＋日上限；admin 改 email 即未驗證、改回
  自動恢復；唯一索引擋重複含大小寫變體；updateProfile 直寫 email 路徑不存在（契約級）。
- 殘餘：B-028 phone 半邊＋驗證碼改密另刀；多 email／admin 列表驗證態欄不做；SSO 對映消費
  本表＝下一刀輸入。
