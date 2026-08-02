---
type: "query"
date: "2026-08-02T08:54:56.530291+00:00"
question: "AppError 為什麼能同時連到登入認證、casbin 授權、節流解鎖、密碼策略、稽核日誌等 21 個後端社群？"
contributor: "graphify"
outcome: "useful"
source_nodes: ["AppError", "error.rs", "envelope.rs", "enforce.rs", "throttle/mod.rs", "validation.rs", "middleware/mod.rs", "facade/sys_user.rs", "domain_lock.rs"]
---

# Q: AppError 為什麼能同時連到登入認證、casbin 授權、節流解鎖、密碼策略、稽核日誌等 21 個後端社群？

## Answer

Expanded from original query via vocab: [apperror, error, handler, middleware, enforce, throttle, validation, facade, audit]. Then traversed BFS from AppError (170 度) and verified against source by four read-only lenses.
AppError 連 21 社群的原因＝架構刻意設計：13 碼矩陣凍結單檔 error.rs（constitution I.3、碼常量+三映射 code/key/http 單一來源，散裝映射違約），全 backend 每支 handler 回傳簽名的錯誤臂都是 AppError，社群偵測把 170 度的消費邊壓倒性歸入 handler 共用型別社群 18，而 error.rs 檔節點與矩陣測試自閉合成錯誤碼矩陣社群 97。
碼面：9 可發（0000/1000/2222/3333/7777/8888/4040/5003/5000）+4 保留（7778/8889/9998/9999 無變體不可構造）；HTTP 唯二例外 4040 至 404、5003 至 403，其餘一律 200。轉換單點 error.rs IntoResponse，middleware 不二次轉換。
分層發射：3333 僅 enforce_mw（bearer/verify、fail-closed leeway 0）；refresh 一律 remap 8888 防前端死迴圈、唯 kicked 回 7777；5003 僅 require_policy（DB-fresh 角色、enforce Err 折 deny、reload 重建-swap 保舊判定面、init 失敗 boot panic＝全鏈 fail-closed）；節流/captcha/validation/密碼策略/資料層業務拒因全部收斂 2222 異 i18n key（防枚舉）；DbErr 三段式：facade 端點專屬錯誤 enum（From+問號）至 handler map 函式收斂 AppError（AppError 刻意無 From DbErr）；稽核寫失敗同交易 rollback 主操作（fail-closed 構造不可達「做了沒記」）。
邊數驗證：jwt.rs 4 邊＝恰 4 構造點；domain_lock 2 邊＝import+薄包；validation.rs 17 邊＝檔內密度（實際外部消費 6 檔）；user.rs 20/role.rs 25 居冠＝翻譯邊界整層收斂在 handler、map 函式是密度最高節點型態。

## Outcome

- Signal: useful

## Source Nodes

- AppError
- error.rs
- envelope.rs
- enforce.rs
- throttle/mod.rs
- validation.rs
- middleware/mod.rs
- facade/sys_user.rs
- domain_lock.rs