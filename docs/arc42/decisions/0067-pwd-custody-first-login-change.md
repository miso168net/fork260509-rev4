---
id: "0067"
title: 密碼經手表 sys_pwd_custody＋首登強制換密（鎖態 token 硬閘）——B-030 兌現選型
date: 2026-07-17
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-17 015-pwd-custody brainstorm——四鏡頭偵察（wf_ddcc0b57）＋user 親決 8 題（含經手表模型與一體適用規則兩次 user 主動規則升級）；ADR 0055 殘餘義務兌現"
tags: [auth, password, schema, security, user-admin, user-center]
---

## 背景

B-030（新帳號初始密碼政策化）殘餘段＝隨機生成＋首登強制改密（ADR 0055 拆階段、011 已兌現
admin 指定＋政策驗證半件；014 自助改密落地＝觸發條件達成）。rev3 純綠地（K2-14/F-7 停在登記
候選、無 as-built）。B-030 條目原預估「sys_user 加欄＋login 插閘＋強制改密頁」，brainstorm 期
user 親決推翻「加欄」半件、改立經手表模型；並將觸發規則從「僅隨機密碼」升級為「凡 admin 經手
設定的密碼一體適用」。

## 決策（user 親決 2026-07-17；細節見 docs/brainstorms/015-pwd-custody.md §1 D1~D8）

1. **經手表 `sys_pwd_custody`**（取代 sys_user 加欄）：`user_id`＋`created_by`（複合 PK；
   **零 FK**——沿 ADR 0009「其餘業務表零 FK、參照完整性應用層承擔」既定原則對齊，並消除雙 FK
   對 sys_user 交叉列鎖的併發死鎖窗）＋`created_at`（NN default now()、語意＝該對最後設定
   時間）；憲法 §I.6 變體 C（零審計欄、硬刪）、不存密碼。**判定單一規則**：該 user 名下存在
   任一筆 `user_id≠created_by` → 首登須換密。**寫入**：別人設（addUser／resetUserPassword
   手輸／隨機）→ upsert `(user, admin)`；本人改（強制頁／user-center 自助，含 operator=標的之
   自我重設——沿 reset_password 既有 keep-sid 自我分支點同點分岔）→ 同交易全刪＋寫一筆
   `(user, user)`（全刪範圍恆＝WHERE user_id=標的；自改列長存＝最後本人改密時間、為密碼有效期
   留錨）。seed 三帳號 migration 直寫無操作者＝零列不強制；015 前既有帳號零列不回填。
2. **插閘＝鎖態 token 硬閘**：登入照常發 token；getUserInfo 曝 `needChangePwd`（additive）；
   前端 route guard 攔至強制改密專頁（constant route、免曝光鏈；判定置於路由存在性解析之先。
   **不做 axios 攔截器兜底**——憲法攔截器禁令字面維持、「admin 重設活躍 session」情境由既有
   8888 撤銷管線覆蓋）；後端 middleware 硬閘（enforce_mw 後、authed 與 policy 兩子 router 皆
   掛）——判定真時白名單（changePassword／getPasswordPolicy／getUserInfo／getUserRoutes／
   getProfile／isRouteExist；path 字面匹配；logout 與 refreshToken 本 Public 結構性不經閘）外
   一律 2222 `mustChangePassword`。改完成功→前端 logout→持新密碼重登；後端 changePassword
   語意零偏差（keep-sid＋撤他裝置照 014）→ ADR 0055 不變式「保留當前操作 session」字面維持。
3. **隨機生成＝前端本地產密浮層**（產生／唯讀 input／顯示密碼／複製／帶入；三掛載點：add 抽屜
   ／operate 欄「密碼」動作〔與「重設密碼」並存、隨機專用〕／user-center 改密卡）；伺服器回應
   不含密碼（島 I5 零衝突、後端零生成邏輯）。
4. **設密冷卻**：同 `(user_id, created_by)` 對距上次 created_at 未滿 N 秒再設密→2222 拒
   （pair 計＝不同 admin 對同一標的互不受限）；N＝system_settings 新鍵
   `password_change_min_interval`（seed 60、0＝停用、settings 頁可調）；檢查位於鎖內、各端點
   既有拒因全過之後、UPDATE 之前（change_own_password 五拒因／reset_password 二拒因；序零重排、
   端點固有規則分層判例）。已識別自鎖窗（user 自改後 N 秒內被 admin 重設→強制頁撞自列冷卻、
   最長 N 秒自癒）——specify 期 user 親決＝**不豁免**（否決豁免傾向案）：
   冷卻一體適用零例外、拒絕提示攜剩餘秒數（BizData 帶 remainingSeconds、各入口一致）。
5. **紀律沿用**：密碼驗證 MUST 複用 ADR 0054 單一驗證點（0055 不變式）；治理面隨刀＝憲法
   MINOR Amendment 新用途 (k)（枚舉含強制改密頁＋route guard＋auth store inline＋manage「密碼」
   動作與浮層＋add 抽屜與 user-center 改密卡隨機鈕＋「＋對應 i18n key」字樣＋兩檔位錨——產密浮層共用元件（src/components/ 新檔、
   新增型圈界）與 constantRoutes 名單觸點（build/plugins/router.ts、修改型）；併敘 §I.2
   constantRoutes 射程釋義一句（constant route 集合可經 §III.2 授權新增、builtin 三頁與 Casbin
   豁免語意不變）；順帶勘誤憲法
   §III.2 紀律行「嚴格限九用途」與標頭十用途 (a)~(j) 之失步）＋Q8（變體 C 歸類論證＋audit 分支
   聯動）＋Q9 行為島判定
   （specify/plan Constitution Check 定案）。

## 候選與落選

- **sys_user 加旗標欄**：單欄無法承載「誰經手」語意（一體適用規則需操作者維）；且 NOT NULL
  DEFAULT false 形撞 schema-gate 白名單三條件（可空＋無預設、schema-gate:258-263）需工具級
  ADR——落選。
- **不發 token＋login 頁內改（Public 改密端點）**：需新開未認證驗密 oracle（須整套接 007 節流）
  ＋登入稽核新終局語意＋政策端點公開化＋撞 AUTH-WIRING(b) 不改 pwd-login——用更大攻擊面保護
  已持真密碼者——落選。
- **純前端閘（不疊 API 硬閘）**：user 明確要求「不該讓他能打所有需登入 API」——落選。
- **claims 烙旗標**：違「claims 僅 hint、判定 DB-fresh」紀律＋keep-sid 下本 sid 舊 claims 殘留
  ——落選。
- **後端生成隨機密碼＋回應一次性回傳**：正面撞島 I5「API 回應 MUST NOT 含密碼」——落選、
  不默做。

## 驗收與殘餘

- 機器閘：schema-gate 三子命令（表級＋seed 白名單登記；**audit_table 變體 C 加 sys_pwd_custody
  專屬分支＋自帶測試同步**——現行表名硬編碼、不擴必紅）＋contract registry＋typecheck＋
  fork-delta-lint；rust 判定三態／三寫入路徑／冷卻正負向／硬閘白名單內外正負向／getUserInfo
  欄正負向；CDP 七場景（brainstorm §2.6）。
- **判例錨（rev4 首例）**：凍結 `Api.Auth.UserInfo` interface 之成員級 declaration merging——
  邊界＝僅 additive optional 欄、net-new ADAPT `.d.ts` 承載、凍結檔永不動、contract 測試吃合併後
  視圖；日後同型操作引本 ADR 為判例。
- 殘餘：B-102（changePassword 舊密暴力試節流）不併——D7 冷卻僅限制成功改密頻率、失敗嘗試不
  寫列、非其替代；隨機密碼有效期＝未來選項（created_at 錨點已留、屆時另刀）；B-103 不提煉、
  條目措辭釐清（觸及雙卡本體時）。
- 本 ADR 隨 015 刀 specify/plan Constitution Check 與憲法 Amendment 同批轉 accepted。
