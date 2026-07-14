---
id: "0054"
title: 密碼政策 enforcement——單一驗證點＋chars/bytes 雙約束＋forbid_username 相等語意＋密碼載體三重不洩（島 I5 設計理據）
date: 2026-07-14
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-13 011-user-admin brainstorm D3／D5（user 親決）＋對抗式審查 B2（op-log 洩 PHC）與 serious 群（長度單位未定／forbid_username 三重未定／DTO Debug 洩明文／torn-read）全折入＋plan Phase 0 research R4（payload 白名單＋回應逐欄）／R5（單一驗證點＋chars/bytes）；004 密碼政策 7 鍵 seed 之第一個真實執行消費者；憲法島 I5 條文草案見 ADR 0053 附錄"
tags: [password, policy, security, secrets, audit]
---

## 背景

004 已 seed 密碼政策 7 鍵（`password_min_length`(8)／`password_max_length`(64)／
`password_require_digit`／`_lowercase`／`_uppercase`／`_special`／`password_forbid_username`，
後五者 enum:on,off 預設 off），至今**零業務消費者**；密碼雜湊生產入口現制不存在（僅登入 verify
＋seed 期雜湊）、/auth/resetPwd＝永久 stub（ADR 0029）＝現制零改密路徑。011 交付 addUser（管理員
指定初始密碼）＋resetUserPassword（B-029 主路）——密碼政策首度被真實執行。

對抗式審查折入的缺陷群：①長度單位未定＋未對齊 007 的 512 bytes 形制上限→多位元組密碼「設得進
登不進」；②forbid_username 三重未定（大小寫繞過／子串 vs 相等矛盾／短帳號退化）；③逐鍵讀取
跨快照＝瞬時弱化政策（torn read）；④sys_user 若沿逐欄 AuditSerialize 範式倒出會把 argon2 PHC 寫進
append-only 稽核（B2 blocker：永久留存＋DBA/備份/op-log viewer 可讀＝離線爆破料）；⑤LoginReq
前例裸 derive Debug——fix 迴圈易誤加 `{:?}` 把密碼明文洩入容器 log；⑥argon2 夾鎖內拉長列鎖持有期。

## 決定

- **單一驗證點（FR-026）**：`password.rs` 新增 `hash(password)→PHC`（argon2id、`Argon2::default()`
  ＝v19、m=19456/t=2/p=1，與 seed／verify 參數一致；隨機 salt）＋
  `validate_against_policy(policy, user_name, candidate)→Result<(),Vec<違規碼>>`（收集全部違規、
  非首錯即返）——addUser 與 resetUserPassword 共用、**零分叉**；後端為規則唯一真源（前端 drawer
  hint 屬 best-effort 顯示、登入頁正則放寬 required-only＝research R8）。
- **7 鍵單快照讀（FR-026）**：`load_policy`＝一次 `find_by_keys` 單語句讀齊 7 鍵（沿 007 throttle
  前例）——杜絕逐鍵跨快照 torn read；缺鍵／不可解析→fail-default＝m002 seed 預設值
  （min 8／max 64／五 enum off；沿 throttle `DEFAULT_*` fail-default 範式、防禦性兜底）。
- **chars/bytes 雙約束（FR-027）**：`min_length`／`max_length` 單位＝**chars**
  （`candidate.chars().count()`）；另加固定位元組上界 `candidate.len()（bytes）≤
  LOGIN_PASSWORD_MAX_BYTES`（512、引 007 常數不硬編）——消滅「多位元組密碼設得進登不進」
  （login 端形制守門同界）。min>max 跨鍵收斂＝**安全側恆拒**（任意長度必違反其一、自然成立並以
  測試錨定）。字元類語意（實作期定形）：digit/lowercase/uppercase＝ASCII 字元類存在性；
  special＝非 ASCII 英數之任意字元（含標點與非 ASCII 字元）。
- **forbid_username＝case-insensitive 相等（FR-027）**：`candidate.to_lowercase() ==
  user_name.to_lowercase()` 即拒——**相等語意、非子串**（對齊 m002 seed 描述「禁止密碼與帳號
  相同」；無短帳號退化、不因大小寫繞過）。
- **密碼三重不洩（島 I5、FR-028、SC-008）**：
  1. **DTO 除錯遮蔽**：承載密碼的 DTO（AddUserReq／ResetUserPasswordReq）**不 derive Debug、
     手寫 `impl Debug`** 印 password 為 `<redacted>`（不印長度不印片段）；負向自證＝改回裸
     derive 即測試轉紅。
  2. **op-log payload 白名單**：使用者寫端稽核 payload 逐欄白名單、絕不含 password 明文／雜湊
     ／session_id；resetUserPassword payload 僅 `{id, user_name}`（snake_case、對齊 009 op-log 範式）；deleteUser 指派快照排除
     password。負向測試斷言 payload 不含 `$argon2` 子串與 password 鍵。
  3. **回應排除**：getUserList／getDeletedUsers 逐欄構造（比照 role.rs、不序列化 raw sys_user
     Model）——結構性無 password 與 session_id 欄。
- **雜湊時點（FR-028）**：argon2 hash MUST 於**取列鎖前**計算（毫秒級 CPU 工作不夾鎖內拉長
  advisory＋列鎖持有期）。

## 後果

- 違規明細經既有 BizData 明細通道下發（碼 2222、key `backend.biz.user.passwordPolicy`、data 帶
  違規清單；ADR 0050、零信封變更、零新錯誤碼）；受眾＝super（本可自查、無洩漏面擴大）。
- 違規碼字面（minLength／maxLength／maxBytes／requireDigit／requireLowercase／requireUppercase
  ／requireSpecial／forbidUsername）屬活書層字面、wire 形定稿於 T017；`maxBytes` 為固定守門
  非政策鍵（誠實區分）。
- U1（T004）已落 `hash`／`validate_against_policy`／`load_policy`＋7 鍵逐鍵矩陣＋多位元組 bytes
  上界＋大小寫繞過案單元測試；消費接線屬 T012（addUser）／T017（resetUserPassword）。
- 自助改密（user-center 驗舊密）與初始密碼隨機生成＋首登強制改密**不在本刀**——拆階段理據見
  ADR 0055；落地時 MUST 複用本單一驗證點（禁止另立驗證分叉）。
- 方向性面凍結（隨島 I5 入憲後反轉＝MAJOR）：拆單一驗證點、拔三重遮蔽、bytes 上界脫鉤登入端；
  常數（512、7 鍵字面、違規碼字面）留活書。
