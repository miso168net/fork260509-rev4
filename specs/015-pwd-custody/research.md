# Phase 0 Research: 015-pwd-custody

接地定案（四鏡頭偵察 wf_ddcc0b57＋3 鏡頭對抗式審查 wf_c3b4f487 全處置；行號為 2026-07-17 實測）。

## R1 判定規則——單一純函式 seam（防分叉）

- **Decision**：判定「該帳號登入後是否須換密」＝該帳號名下 `sys_pwd_custody` 存在任一筆 `user_id≠created_by`。收斂為 facade 單一純函式 `need_change_pwd(conn, user_id) -> bool`（SQL `EXISTS(SELECT 1 FROM sys_pwd_custody WHERE user_id=$1 AND created_by<>$1)`），三處共用：getUserInfo 投影、pwd_gate_mw、（可選）login 後不阻擋僅供投影。
- **Rationale**：三處同規則若各自寫 SQL＝分叉風險（014 U9「比對源錯位」同類坑）；單點純函式一改全改、契合 ADR 0054 單一驗證點精神（雖非密碼驗證、同紀律取向）。
- **Alternatives**：各處內聯 SQL（分叉、落選）；快取判定於 claims（違 claims hint-only、keep-sid 殘留，brainstorm D5 落選）。

## R2 硬閘掛點——pwd_gate_mw 掛 build() 疊放縫

- **Decision**：新 `pwd_gate_mw`，於 `router.rs::build()` 掛 authed 與 policy **兩子** router，位置＝`enforce_mw` 之後（讀得到 Claims）、`access_log_mw` **內側**（access_log 先加＝內側後跑；pwd_gate 更後加＝更內側，使被拒請求仍經 access_log 記錄、可觀測「被強制者嘗試打什麼」）。判定真＋path 不在白名單→`AppError::Biz("biz.auth.mustChangePassword")`（2222）。白名單 path 集＝const 陣列（GATE_BYPASS_ENDPOINTS 先例 middleware/mod.rs:115、`req.uri().path()` 比對）。
- **白名單**（clarify＋審查定稿）：`/auth/getUserInfo`、`/route/getUserRoutes`、`/route/isRouteExist`、`/userCenter/getPasswordPolicy`、`/userCenter/getProfile`、`/userCenter/changePassword`。logout 與 refreshToken 為 Public 子 router、結構上不掛 pwd_gate＝天然放行（不列入 const、避誤導）。**兩子 router 皆掛**——漏掛 policy＝有管理權的被強制者可打全部 manage 端點（審查 sec-BK 併發面同源警示）。
- **Rationale**：build() 現行疊放（router.rs:697-753）＝enforce（外層先跑注入 Claims）→access_log（內層後跑）→handler；pwd_gate 插此縫最小侵入、與 require_policy（per-route 最內）不衝突。
- **Alternatives**：per-route 掛（每條 ROUTES 加、面大）；enforce_mw 內聯（污染認證層職責）——皆落選。

## R3 冷卻位置與語意

- **Decision**：同 `(user_id, created_by)` pair 距上次 `created_at` 未滿 N 秒→拒（2222 `biz.user.pwdSetTooFrequent`、msg 攜剩餘秒數由前端格式化或後端 BizData 帶值）。檢查位於各端點**既有拒因全過之後、UPDATE 之前**、鎖內（change_own_password 五拒因後、reset_password 二拒因後；addUser 為該對首筆、天然無冷卻）。N＝system_settings `password_change_min_interval`（單鍵讀、缺鍵 fail-default 60、0＝停用）。**一體適用零例外**（clarify Q1 親決：含強制換密狀態下本人改密不豁免、拒絕提示顯示剩餘秒數、自鎖窗最長 N 秒自癒）。
- **Rationale**：排既有拒因後＝不重排固定序、不入 ADR 0054 單一驗證點（端點固有規則分層、014「新≠舊」判例）；pair 計＝第三方構造不出他人 pair（審查證 DoS 不成立）。
- **Alternatives**：標的維限頻（改鍵、語意變、落選）；豁免強制態自改（clarify 否決）。

## R4 隨機密碼——前端本地 CSPRNG

- **Decision**：瀏覽器 `crypto.getRandomValues` 產生、字元集構造性滿足現行密碼政策 7 鍵（讀既有 getPasswordPolicy——admin/authed 可用）；伺服器回應恆不含密碼（產生零網路請求、送出走既有密碼欄）。浮層＝產生／唯讀 input／顯示密碼切換／複製／帶入。
- **Rationale**：繞開島 I5「API 回應 MUST NOT 含密碼」（brainstorm D1 落選丙案＝後端生成回傳撞 I5）；CSPRNG 非 Math.random（審查 sec-suggestion）。
- **Alternatives**：後端生成一次性回傳（撞 I5、須修憲、落選）。

## R5 治理路徑（R-GOV）

- **Decision**：憲法 MINOR Amendment **新用途 (k)**（v1.13.0→v1.14.0）：枚舉＝強制改密頁（constant route）＋route guard 攔截控制流＋auth store inline＋manage「密碼」動作與浮層＋add 抽屜與 user-center 改密卡隨機鈕＋「＋對應 i18n key」字樣；(a)/(g)/(h) 擴字面併敘；順帶勘誤「九用途／十用途」紀律行失步。ADR 0067 draft→accepted。Q9 島 I 細項擴充字面併入。
- **Rationale**：十用途 (a)~(j)（§III.2 標頭）無涵蓋控制流層新頁與攔截；(g) 補擴「＋i18n key」四度判例（v1.12.0 前例）自始寫入防重演。
- **Alternatives**：寬讀塞既有用途（字面縫隙以擴字串正名、不走寬讀，013 判例）。

## R6 rev3 承襲——純綠地

- **Decision**：rev3 未實作首登強制改密（sys_user 16 欄無旗標、login 無插閘、grep 全零），僅 K2-14/F-7 登記候選；rev4 全新設計、不承襲 as-built。
- **Rationale**：條目「加欄＋插閘＋改密頁」係 rev4 預估、本刀已推翻「加欄」半件（改經手表）。
- **Alternatives**：照條目字面加 sys_user 旗標欄（審查證撞 schema-gate 三條件＋單欄無法承載「誰經手」，落選）。

## R7 經手表零 FK（ADR 0009 對齊）

- **Decision**：`sys_pwd_custody` 零 FK（user_id／created_by 皆不加 FK constraint），參照完整性由應用層承擔（寫入全在序列化鎖與既有查核後）。ADR 0067 明文引 ADR 0009。
- **Rationale**：ADR 0009「僅 user-role join 加 FK、其餘業務表零 FK」——經手表非 join、落「其餘」；雙 FK→sys_user 另引入交叉列鎖死鎖窗（審查 gov-BK5），拔 FK 自然消除。
- **Alternatives**：雙 FK→sys_user（撞 ADR 0009＋死鎖窗，落選）。

## R8 audit_table 分支聯動（不補即紅）

- **Decision**：`tools/schema-gate` audit_table 對變體 C 為表名硬編碼（schema-gate:585 sys_user_role／589 sys_token、else FAIL「archetype-map 登記異常」）；m011 同 commit 加 `elif variant=="C" and table=="sys_pwd_custody":` 分支＝檢 created_at NOT NULL＋禁 `updated_*`/`deleted_*`（不可竄改語意）＋TestAuditTable 案例同步。
- **Rationale**：登記變體 C 後不擴分支＝audit 子命令必紅（審查 gov-BK4 實碼證）。
- **Alternatives**：無（機器閘硬性）。

## R9 getUserInfo additive 加欄——首例成員級 declaration merging

- **Decision**：UserInfo 回應加 `needChangePwd:boolean`（後端 struct 加欄＋既有 sys_user 重讀旁 +1 EXISTS）；前端 typing 走 net-new `rev4-pwd-custody.d.ts` 對凍結 `Api.Auth.UserInfo` interface 成員級 declaration merging（前端宣告 optional、auth store reactive 免補初值）。contract 測試吃合併後視圖。
- **Rationale**：`typings/api/auth.d.ts` 憲法凍結（:238）；現有 9 支 rev4-*.d.ts 皆 namespace 加新 interface、無成員級 augment 先例＝本刀首例（TS 機制可行、ADAPT 軌道相容、審查 gov-suggestion s4）。
- **Alternatives**：動凍結 auth.d.ts（違憲、落選）。

## R10 軟刪／復原與經手記錄

- **Decision**：會員軟刪不清經手記錄（登入本被活性判定擋）；復原後判定沿刪前狀態（密碼未變、語意合理）。spec 明載、無額外實作。
- **Rationale**：經手記錄非角色指派（島 I4 只清指派）、與軟刪正交。
