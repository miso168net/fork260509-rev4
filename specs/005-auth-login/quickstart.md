# Quickstart — 005-auth-login 驗證指南（Phase 1）

驗證/執行指南（非實作碼）。三層：①後端 cargo（容器 serial）②命令級活體（curl/psql）
③★CDP 實機瀏覽器 9 項。端口：rust-api `127.0.0.1:42079`、front-nginx `42080`、postgres `45432`。

## 前置

```bash
# dev stack（001）已起；本刀新增 m003 → 需重跑 migrate（容器內）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
# rust-api 重編上線後確認新端點回應（避免假綠 L-011）
curl -s 127.0.0.1:42079/health
```

## 層一：後端 cargo（容器內、全程 serial）

```bash
# 一道命令全綠＝後端驗收（容器內執行、host 無工具鏈）
docker compose exec rust-api cargo test --workspace
```

涵蓋（測試即產品）：
- **login**：Super 正確帳密→`0000`＋憑證對；三態（not-found／錯密／status==2 停用）→同一 `1000`；
  dummy-argon2 時序（not-found 也 verify）；sys_login_attempt exactly-one（成功/失敗各一列、含 IP 欄）。
- **refresh**：有效 refresh→換發新對＋新 jti＋窗=now+N；過期/垃圾/錯簽→`8888`；活性 gate
  （fixture status=2 或 deleted→`8888`）；改 `session_idle_timeout`→新續命窗生效；access TTL=
  `min(300,N×60÷2)`（N=5→150s）。
- **getUserInfo**：DB-fresh roles（claims.roles hint 填垃圾證不採信）；buttons casbin 枚舉；userId 字串。
- **getUserRoutes**：Super 樹含 `manage_system-settings`、R_USER_COMMON 不含；祖先包含（`manage`
  目錄隨葉保留）；home 正確；getConstantRoutes→`[]`；isRouteExist Authed。
- **stub**：4 端點→`2222 biz.auth.notSupported`。
- **三態保護**：Authed 端點無 token→`3333`；Policy（settings）非 super→`5003`。
- **守門**：契約 case 逐條＋覆蓋閘雙向；`wire-schema extract` 重抽 byte 冪等（stub typings）；
  entity_access_lint（handler 零 path-root `entity::`）；13 碼/保留碼斷言不變。

## 層二：命令級活體（自鑄 token、承 004 模式）

```bash
# 真登入取 token（seed 帳密 Super/123456）
TOK=$(curl -s -XPOST 127.0.0.1:42079/auth/login \
  -H 'content-type: application/json' -d '{"userName":"Super","password":"123456"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["token"])')

# getUserInfo（Authed）
curl -s 127.0.0.1:42079/auth/getUserInfo -H "Authorization: Bearer $TOK"
# getUserRoutes（Super 應含 manage_system-settings）
curl -s 127.0.0.1:42079/route/getUserRoutes -H "Authorization: Bearer $TOK" | grep -o 'manage_system-settings'
# 無 token→3333
curl -s 127.0.0.1:42079/auth/getUserInfo | python3 -c 'import sys,json;print(json.load(sys.stdin)["code"])'  # 3333
# stub→2222
curl -s -XPOST 127.0.0.1:42079/auth/register -H 'content-type: application/json' -d '{}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["code"])'  # 2222

# psql 佐證稽核列
docker compose exec postgres psql -U soybean -d soybean_admin_rust \
  -c "SELECT attempted_user_name, success, real_ip FROM sys_login_attempt ORDER BY created_at DESC LIMIT 3;"
```

期望：getUserInfo 回 `userId`(字串)/`userName`=Super/`roles`含 R_SUPER；getUserRoutes 命中
`manage_system-settings`；無 token→`3333`；register→`2222`；psql 見本輪登入列。

## 層三：★CDP 實機瀏覽器（9 項、`CDP:127.0.0.1:9229`、入口 `http://localhost:42080`）

紀律：跑 toast 項前 `docker compose restart base-web`＋斷言頁面**無 raw i18n key**（L-015）；
每項需 CDP network/DOM/console 可觀察證據、**不得**以 curl 或靜態綠代替（L-053）。

| # | 操作 | 期望 CDP 證據 |
|---|---|---|
| 1 | pwd-login 輸 Super/123456 登入 | network `/auth/login`→`0000`；localStorage `token` 有值（真 JWT、非 mock 固定值）；URL 跳 home |
| 2 | 觀察左側選單 | network `/route/getUserRoutes` 回應含 `manage_system-settings`；DOM 側欄有「系統設定」；全頁無 raw key |
| 3 | 進系統設定→改「工作階段閒置逾時」60→61→復原 | `updateSystemSetting`→`0000`；成功 toast 為譯文 |
| 4 | 停留操作跨過 access TTL（設定調短便觀察） | network 自動出現 `refreshToken`→`0000`；頁面零中斷、無登出 |
| 5 | 設定調 5 分→登出→重登→閒置 ~6 分後點任一操作 | network `3333`→`refreshToken`→`8888`；toast「請重新登入」譯文；落在 `/login` |
| 6 | 輸錯密碼登入 | toast「使用者名稱或密碼錯誤」（譯文、對應 1000）；停在登入頁 |
| 7 | 切 code-login/register/reset-pwd 各提交＋點「取驗證碼」 | 各 network→`2222`；toast「該功能暫未開放」；表單原地不動、倒數不啟動 |
| 8 | 登出→以 User/123456 登入 | 側欄無「系統設定」；手動導 `/manage/system-settings`→被擋（dynamic 下路由不存在） |
| 9 | psql 覆核 | sys_login_attempt 見 #1 成功列＋#6 失敗列（attempted_user_name、success、real_ip 欄齊） |

#4/#5 同輪串測（#5 需真實等待閒置窗、排最後）。

## 通過準則（對應 SC）

SC-001~002（登入/collapse/稽核）＝層一+層二+#1/#6/#9；SC-003~004（閒置/續命/設定）＝#3/#4/#5；
SC-005（動態選單/祖先包含/擋）＝#2/#8+層一；SC-006（stub）＝#7；SC-007（守門/契約/lint）＝層一；
SC-008（CDP 9 項）＝層三全過。
