# Quickstart / 驗收: 015-pwd-custody

## 全量閘（收刀前全綠）

```bash
# rust（容器內、serial）
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test --lib -- --test-threads=1'
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test --test contract --test wire_schema -- --test-threads=1'

# schema-gate 三子命令（需 stack；migration 落庫後）
python3 tools/schema-gate gate1   # 結構零漂移（含新表 sys_pwd_custody）
python3 tools/schema-gate gate2   # 定稿落實（含 settings 新鍵 seed）
python3 tools/schema-gate audit   # 變體矩陣（sys_pwd_custody 變體 C 分支必須已補、否則 FAIL）
python3 tools/schema-gate --self-test   # 工具 self-test（TestAuditTable 案例同步）

# base-web（容器內 typecheck；host commit 一律 --no-verify）
docker exec rev4-admin-base-web-1 sh -c 'cd /app && pnpm typecheck'
python3 tools/fork-delta-lint    # 直跑（bash 假紅 L-143）

# docs 治理
python3 tools/docs-sync check
```

## 前置

- migration 熱套後 restart rust-api（新表可見）；含 casbin 者本刀無（零 casbin seed）。
- 新 i18n key 加入後 restart base-web（vite 未必熱載新字典、L-015）；CDP 前驗 base-web healthy＋vite 200。

## CDP 七場景（rev4-cdp 速查；Edge@9229 42080）

1. **首登強制＋硬閘實彈**：admin 對測試會員按 operate 欄「密碼」→浮層「產生」→複製→確認送出；該會員登入→驗證直接落強制改密頁（點選單/直輸網址/F5 皆導回）；**以該會員 token 用 Runtime fetch 直打 `/systemManage/getUserList`→回 2222 mustChangePassword**（硬閘實彈）；改密成功→自動登出→新密碼重登→getUserInfo needChangePwd=false、API 面全開、custody 收斂為 (u,u)。
2. **手輸重設同觸發**：admin「重設密碼」手輸→該會員登入同樣被強制。
3. **建帳首登觸發**：新增使用者（手輸或隨機）→新會員首登被強制。
4. **seed 三帳號零影響**：Super/Admin/User 登入→needChangePwd=false、直接進系統。
5. **冷卻連按**：admin 對同一會員連續兩次重設（間隔 < N）→第二次 2222 pwdSetTooFrequent＋剩餘秒數；等滿 N 秒重試成功；settings 改 0→不受限。
6. **user-center 自助不觸發**：會員自助改密（含用改密卡隨機鈕）→成功、needChangePwd 保持 false、014 撤他裝置行為不變。
7. **三語零 raw key**：zh-TW/zh-CN/en-US 各切一次走 US1 全流程＋三掛載點浮層＋settings 新項→零 raw key。

## 負向自證（拆即紅）

- 判定三態測試：拆「純自改列→false」邏輯即紅（含他人經手→true 誤放）。
- 硬閘白名單：拆 policy 子 router 掛載→有管理權被強制者可打 manage 端點（測試紅）。
- 冷卻：拆「失敗嘗試不啟動冷卻」→舊密錯後正確重試被誤拒（測試紅）。
- getUserInfo needChangePwd 正負向：拆投影→前端導向失效（測試紅）。

## 資料清理

- CDP 測試造的 custody 列＋測試會員：測後 psql 清（sys_pwd_custody WHERE user_id IN 測試帳號）；settings `password_change_min_interval` 還原 60。
