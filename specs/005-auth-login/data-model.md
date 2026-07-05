# Data Model — 005-auth-login（Phase 1）

實體＝憑證/身分/稽核/選單/設定形＋狀態轉移。DB 面沿 baseline（zero 新表）＋m003 一列 seed。

## 1. 憑證對（Credential Pair、無伺服器狀態）

| 憑證 | TTL（秒） | 用途 | 密鑰 |
|---|---|---|---|
| access | `min(300, N×60÷2)` | 請求身分載體（Authorization: Bearer） | `access_secret` |
| refresh | `N×60` | 換發專用（`/auth/refreshToken` body） | `refresh_secret` |

`N` = `session_idle_timeout`（分鐘、DB-fresh 每次 login/refresh 讀）。**無 sys_token 落庫、無
rotation**（session 刀 B-021）。憑證＝HS256 JWT，claims 如下。

## 2. Claims（JWT body、004 已定形沿用）

| 欄 | 型 | 本刀語意 |
|---|---|---|
| `uid` | i64 | 使用者 id（授權查庫鍵） |
| `sid` | String(uuid) | session id——login 生成、refresh 沿用（同 session lineage）；**本刀不消費**（single-session 留 session 刀、forward-compat） |
| `jti` | String(uuid) | per-token uuid——每次簽發新生成 |
| `roles` | Vec<String> | 角色 hint——**不作授權依據**（enforce 一律 DB-fresh、FR-005） |
| `iss`/`aud` | String | 發行方/受眾（config 配線、verify set_issuer/set_audience） |
| `exp`/`iat` | i64 | 到期/簽發（access/refresh 僅 exp、密鑰不同） |

## 3. 使用者（sys_user、entity 已建、facade 新增）

存取欄（登入相關）：`id`／`user_name`（活性唯一 partial uniq WHERE deleted_at IS NULL）／
`password`（argon2id PHC）／`nick_name`（→ wire userName、User→User01）／`status: Option<i16>`
（**1=啟用、2=停用**；seed 全 1）／`deleted_at`（軟刪）。

**facade（sys_user.rs）**：
- `find_by_user_name(conn, name)` → 濾 `deleted_at IS NULL`（軟刪併入 not-found）；
- `find_by_id(conn, uid)` → refresh 活性 gate 用（讀 status／deleted_at）。

**登入狀態轉移（collapse→1000）**：

```
輸入(user_name, password)
  ├ find_by_user_name miss  ─┐
  ├ argon2 verify 失敗       ─┼─→ 皆 dummy/實 verify 後 → AppError::LoginFailed(1000)
  └ status==2（verify 後判）  ─┘   （不洩存在性；稽核：miss→operator None、其餘→Some(uid)）
成功（found＋verify ok＋status!=2）→ DB-fresh roles → 簽對 → LoginToken
```

## 4. 登入稽核（sys_login_attempt、entity 已建、facade 新增 insert）

每登入終局恰一列（exactly-one、best-effort）。欄（entity 現成）：`id`／`created_at`／
`created_by`(operator uid、識別前 None)／`success: bool`／`attempted_user_name`／`real_ip`
(inet=peer)／`peer_ip`／`x_forwarded_for`(XFF 原文)／`ip_confidence`(低標)／`region`／`trace_id`。
寫失敗→warn、不改登入回應。**本刀唯一寫者**；節流刀（B-010）未來讀者。

## 5. 閒置逾時設定（session_idle_timeout、m003 seed）

| 欄 | 值 |
|---|---|
| setting_key | `session_idle_timeout` |
| setting_value | `60`（預設） |
| setting_type | `number` |
| description | `工作階段閒置逾時（分鐘）`（繁體、當設定頁 label fallback、R10） |

驗證範圍（validation registry NUMBER_RANGES）：`("session_idle_timeout", 5, 1440)`；壞值→2222
（寫入端 registry 防線）；設定列缺失→登入/換發 fail-loud 5000。**m003**：up 冪等 ON CONFLICT、
down 對稱 `DELETE … WHERE setting_key IN ('session_idle_timeout')`；基線 m002 不動、casbin 零新列。

## 6. 路由保護三態（Protection enum、router）

| 態 | 掛載 | 拒絕碼 | 端點 |
|---|---|---|---|
| Public | 無 mw | — | /health、/auth/login、/auth/refreshToken、/route/getConstantRoutes、4 stub |
| Authed | enforce_mw（JWT decode→Claims；無 require_policy） | 3333（無/壞 token） | /auth/getUserInfo、/route/getUserRoutes、/route/isRouteExist |
| Policy | enforce_mw ＋ require_policy（DB-fresh roles→casbin） | 3333／5003 | /systemManage/*（004 兩端點、改此態） |

## 7. 選單樹（MenuRoute、getUserRoutes 組建）

- 來源：casbin `act='menu'` 枚舉（DB-fresh roles、85 列 seed）→ 可見 `route_name` 集；
  sys_menu `list_active`（status=1＋deleted_at IS NULL）flat → **祖先包含組樹**（命中葉之
  parent 鏈全保留、防 `manage` 目錄孤兒斷鏈）。
- 節點序列化（upstream `MenuRoute = ElegantConstRoute + id:string`）：`{id:string, name:route_name,
  path:route_path, component, meta:{title←i18n_key, icon, order, hideInMenu, ...}}`，children 非空才插。
- `home` = 角色集內啟用角色（id 升冪）首個非空 `sys_role.home`、預設 `"home"`。

**facade**：sys_menu（`list_active`＋`build_user_route_tree`）、sys_role（`home_of_roles`）。

## 8. wire 形（upstream 凍結、後端 serde 遷就；零 typings 新增）

- `LoginToken { token, refreshToken }`（camelCase）
- `UserInfo { userId:string, userName, roles:string[], buttons:string[] }`（userId＝i64→string 2^53 守衛）
- `UserRoute { routes: MenuRoute[], home }`
- stub req（rev4-auth-stub.d.ts 新檔、ADAPT）：各表單欄位形；resp `data:null`＋2222。

## 9. 替代登入 stub（4 端點、無資料變更）

`sendCaptcha`／`codeLogin`／`register`／`resetPwd` → 一律 `AppError::Biz("biz.auth.notSupported")`
（2222）；零 DB 觸碰、零狀態。未來做真時為替換點（ADR 0029）。
