# Contract — auth-api（後端 10 端點）

wire 權威＝base-web upstream `Api.Auth`／`Api.Route` 凍結 typings；後端 serde camelCase 遷就、
零 typings 新增（stub 除外、走 ADAPT 新檔）。信封＝`Res{data,code,msg}`（§I.3）；13 碼零新碼。
路徑不帶 `/api`（front-nginx strip）。每端點掛 ROUTES 註冊＋契約 case（缺 case 覆蓋閘紅）。

## 認證（3）

### POST /auth/login — Public
- req: `{ userName, password }`
- resp ok: `Res<{ token, refreshToken }>`（`0000`）
- 行為: find_by_user_name（濾軟刪）→ argon2 verify（miss 也跑 dummy、R5）→ status==2 判（verify 後）
  → 三態 collapse **1000**（`auth.login.failed`、不洩存在性）；成功→DB-fresh roles→簽對（access
  `min(300,N×60÷2)`s／refresh `N×60`s）→ 終局寫 sys_login_attempt（exactly-one、best-effort）
- err: `1000`（登入失敗三態合一）；`5000`（設定列缺失／DbErr／簽發失敗）

### POST /auth/refreshToken — Public
- req: `{ refreshToken }`
- resp ok: `Res<{ token, refreshToken }>`（`0000`）
- 行為: `jwt::verify(refresh_secret/iss/aud/exp)` 失敗→**8888**；活性 gate（find_by_id：status==2
  或 deleted_at→**8888**）；讀 N→簽新對（新 jti、窗推 now+N）；**零 sys_token 落庫/查詢**
- err: `8888`（`auth.session.reLogin`：驗失敗／活性拒——**絕不** 3333/9999/9998）；`5000`（設定缺失/簽發失敗）

### GET /auth/getUserInfo — Authed
- req: 無（Authorization header）
- resp ok: `Res<{ userId, userName, roles, buttons }>`
- 行為: DB-fresh roles；buttons=casbin `act='button'` 枚舉去重；userId 字串、userName=nick_name
- err: `3333`（無/壞 token）；`5000`（DbErr）

## 動態路由（3）

### GET /route/getUserRoutes — Authed
- resp ok: `Res<{ routes: MenuRoute[], home }>`
- 行為: DB-fresh roles→casbin `act='menu'` 枚舉→sys_menu list_active→祖先包含組樹；home=角色首個非空
- err: `3333`；`5000`

### GET /route/getConstantRoutes — Public
- resp ok: `Res<MenuRoute[]>`（seed 現況 `constant=true` 空集→`[]`）

### GET /route/isRouteExist — Authed（R4：rev3 as-built auth-only）
- req: query `?routeName=<name>`
- resp ok: `Res<boolean>`
- err: `3333`

## 替代登入 stub（4、ADR 0029）— Public

`POST /auth/sendCaptcha`／`/auth/codeLogin`／`/auth/register`／`/auth/resetPwd`
- resp: 一律 `Res`（`2222`、msg=`biz.auth.notSupported`、data:null）
- req 形: rev4-auth-stub.d.ts（ADAPT 新檔、各表單欄位）；bind-wechat 空殼不立端點

## 錯誤碼用表（13 碼零新碼、§I.3）

| 碼 | key | 用處 |
|---|---|---|
| `0000` | common.success | 全 ok |
| `1000` | auth.login.failed | 登入三態合一 |
| `2222` | biz.auth.notSupported | 4 stub |
| `3333` | auth.token.expired | Authed/Policy 無/壞 token |
| `8888` | auth.session.reLogin | refresh 驗失敗/活性拒（閒置過期 UX） |
| `5003` | system.forbidden | Policy 端點非授權（HTTP 403） |
| `5000` | system.internal | 設定缺失/DbErr/簽發失敗 |

保留碼（7778/8889/9998/9999）＋7777 本刀不發（contract test 斷言不變）。

## casbin 過濾規則（零新 policy 列）

- Policy 端點 enforce `(role, path, method)`；本刀 auth/route 端點皆 Public/Authed（**不掛
  require_policy**、無 endpoint p 列需求）。
- getUserRoutes menu 過濾＝`get_filtered_policy` 枚舉 `act='menu'`（85 列 seed）、v1=route_name；
  getUserInfo buttons＝枚舉 `act='button'`（16 列）。

## 守門（沿既有）

- 每端點補 `contract.rs` case（免-DB 形＝Authed/Policy 無 token→3333 信封欄序）＋覆蓋閘雙向；
- typings 新增（stub）→ `wire-schema extract` 重抽、byte 冪等；
- handler 零 path-root `entity::`（entity_access_lint）；13 碼 table-driven／保留碼不可發斷言不變。
