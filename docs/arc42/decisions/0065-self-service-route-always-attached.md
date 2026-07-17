---
id: "0065"
title: getUserRoutes 恆附掛 self-service 路由白名單——自助頁可達性與 RBAC 授權表脫鉤
date: 2026-07-17
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-17 014-user-center brainstorm（user 親決 D1；五鏡頭探索兩庫親驗 casbin user-center menu policy 僅 R_SUPER 一列＝rev3 同病未解）；B-090 自助改密受眾＝任何登入者、選單可達性不得依賴逐角色授權配置"
tags: [routes, self-service, user-center, menu, rbac]
---

## 背景

rev4 前端走 dynamic 路由模式：登入後 `getUserRoutes` 依 casbin menu policy 過濾、回傳該使用者可達路由。user-center（個人中心自助頁）的 casbin menu policy 在 m002 僅 seed 給 R_SUPER 一列（rev3 同病、兩庫親驗）——非-super 使用者點頭像下拉「個人中心」＝404。但自助改密／profile 編輯的受眾定義（憲法 §III.2(g)、ADR 0055）＝**任何登入者本人**，可達性不應依賴逐角色授權配置。

候選三案：①seed 全角色 menu policy（migration 補列）——未來每新建角色都要記得補、漏配即 404（rev3 即此病），除非再把「建角色自動帶列」做進 role 寫端（多一刀）；②getUserRoutes 恆附掛 self-service 白名單——結構性保證、零 seed；③sys_menu constant route——補查證僞：soybean constant routes＝免登入層（login/404、anon 端點回傳），需登入的 user-center 放入＝治理語意錯位。

## 決定

**getUserRoutes 組裝回傳時，於 casbin 過濾結果之後恆附掛一個寫死的 self-service 路由白名單**（現僅 `user-center` 一項）：

- 白名單＝後端碼內常數（非 DB、非 casbin）——「登入即可達」語意由型別／常數層固定，任何登入角色（含未來新建角色）必得、永不漏配。
- 憲法邊界：主錨＝§III.2(g) 明文 user-center「`hideInMenu:true`、經頭像下拉入口、**非 Casbin menu**」——憲法自身已將此頁劃出 Casbin menu 治理域，白名單附掛＝(g) 頁級豁免在路由樹組裝層的實作；§I.2 字面「menu 由 Casbin RBAC enforce、有權才顯示」「業務 menu 走 `/route/getUserRoutes` → 後端 Casbin enforce 過濾 → 前端顯示」**不受影響**——業務 menu 的 Casbin 過濾照舊，白名單僅將「非 Casbin menu」的 self-service 頁補進回傳路由樹（且 `hideInMenu:true` 下 §I.2「有權才顯示」的選單顯示語意對此頁本就不觸發）；前端仍只消費 getUserRoutes 單一來源（碼註層「後端唯一路由過濾源」慣例不變、該語彙非憲法字面）。plan 期 Constitution Check 復核一次。
- casbin 中既存的 `p|R_SUPER|user-center|menu` 列保留不動（聯集語意下冗餘無害；硬刪屬 seed 移除軌道＝B-060 家族、非本刀）。
- 白名單擴充紀律：僅限「受眾＝任何登入者本人」的 self-service 頁；任何 RBAC 資源頁禁入白名單（授權仍走 casbin 唯一路徑）。

## 後果

- 非-super 使用者登入即見「個人中心」、可自助改密——B-090 受眾語意成立。
- 新建角色零配置成本；不再有「漏配 menu policy 即 404」的 rev3 病。
- getUserRoutes 過濾語意多一層聯集——單元測試須覆蓋「無任何 menu policy 的角色仍得 self-service 路由」與「白名單外路由不受影響」兩向；另補 resolve_home 交互案（零 menu policy 角色的 home 兜底將落 user-center＝登入即見個人中心而非 404、屬改善但為新行為，測試明載）。
- 若未來自助頁家族擴充（如通知偏好頁），逐頁入白名單＝本 ADR 既定軌道、毋需新 ADR；若要把白名單移入 DB／做成可配置，屬翻案＝新 ADR supersede 本檔。
