# Quickstart / 驗收: 020-email-verify-smtp

## 全量閘（收刀前全綠）

```bash
# rust（容器內、serial）
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test --lib -- --test-threads=1'
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test --test contract --test wire_schema -- --test-threads=1'
# 整合測試（需 mailpit up；發碼→撈信→驗證全鏈）
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test --test email_verify -- --test-threads=1'

# schema-gate 三子命令（m014 落庫後）
python3 tools/schema-gate.py gate1     # 結構零漂移（含新表＋sys_user 唯一索引）
python3 tools/schema-gate.py gate2     # 定稿落實
python3 tools/schema-gate.py audit     # 變體矩陣（sys_user_email_verify 變體 C 分支必補、否則 FAIL）
python3 tools/schema-gate.py --self-test

# base-web
docker exec rev4-admin-base-web-1 sh -c 'cd /app && pnpm typecheck'
python3 tools/fork-delta-lint.py       # 直跑（bash 假紅 L-143）；預期全新增型

# secrets 面
bash deploy/preflight-secrets.sh       # REQUIRED 13 檔全在場
python3 tools/docs-sync.py check
```

## 前置

- `deploy/generate-secrets.sh` 重跑補 2 新 key→依 RUNBOOK §15 解密落 `$SECRETS_DIR`→
  `docker compose up -d`（mailpit 隨 dev override 起、驗 `curl -s http://127.0.0.1:8025/readyz`
  ——與內建 HEALTHCHECK 同口徑）。
- m014 熱套後 restart rust-api（新表＋索引可見）；本刀零 casbin migration（免重登）。
- 新 i18n key 後 restart base-web（vite 未必熱載字典、L-015）；CDP 前驗 healthy＋vite 200。

## CDP 場景（rev4-cdp 速查；Edge@9229 42080）

1. **快樂路徑全鏈**：登入測試會員→user-center email 卡輸入新信箱＋答 captcha→發送→
   `curl 'http://127.0.0.1:8025/api/v1/search?query=to:<新信箱>'` 取最新 ID→
   `curl http://127.0.0.1:8025/api/v1/message/<ID>` 讀 Text 抽六位碼（★收件人條件取信、不用
   latest——spec edge case 明令防誤抓他測試殘留）→回填→驗證成功→徽章顯已驗證（含時刻）；
   DB 斷言：`sys_user.user_email` 已更新＋衛星列 (uid, 值, 時刻)＋op-log 一筆前後值。
   **洩漏面子步（SC-007 載體）**：以剛抽出的六位碼與 verifyToken 前綴 grep
   `docker logs rev4-admin-rust-api-1` 零命中；psql 查該筆 op-log payload 零碼零憑據；
   發碼回應 JSON 零碼欄。
2. **錯碼三次即廢**：故意錯碼 ×3→第 4 次（含正確碼）仍拒 `emailCodeAttemptsExceeded`→重發新碼
   後成功。
3. **冷卻、日上限與重整重建**：發碼後立即重發→`emailCooldown`＋剩餘秒數；F5 重整→倒數消失、
   誤按→拒因重建倒數；滿 60s 重發成功。**日上限子步（SC-003 載體）**：redis 預置
   `emailverify:day:{uid}:{今日}`＝10→發碼→`emailDailyLimit` 拒且 mailpit 零新信；DEL 該鍵復原。
4. **唯一衝突**：帳號 B 對帳號 A 已驗值（含大小寫變體）發碼→預檢 `emailTaken`。
5. **admin 語意**：admin 改 A 的信箱→A 端徽章翻未驗證；改回原值→恢復；admin 對 B 填 A 的信箱
   →`emailTaken`；admin 填 `not-an-email`→`emailFormatInvalid`（含「重送既存怪值也擋」子步：
   先以 psql 植入怪值→admin 編輯該員任一欄→被擋→同表單修正後成功）。
6. **解除綁定**：A 解綁→確認→呈未綁定；DB `user_email IS NULL`、衛星列仍在；admin 回填原值
   →徽章自動恢復已驗證（D9 導出語意實彈）。
7. **captcha 閘**：captcha 空／錯／重放（重送同 token）→`emailCaptchaInvalid`＋mailpit 零新信；
   答錯後自動換題可繼續。
8. **fail-closed**：`docker stop rev4-admin-redis-1`→發碼與驗證皆明確拒（零寄信）＋
   `warn_degraded` 日誌可查→`start` 後自癒。
9. **三語零 raw key**：zh-TW/zh-CN/en-US 各切一次走場景 1＋3＋6→零 raw key。

## 負向自證（拆即紅）

- mailer 兩態建構單元測試（SC-008 後半載體）：starttls=true→transport 為 STARTTLS `Tls::Required`
  形；false→明文 builder 形；拆兩態分支→測試紅。
- 節流原子先佔（SC-003 載體）：整合測試以 k 筆預解題並發突發打 sendEmailCode→恰 1 筆成功、
  mailpit 恰 1 封信；拆 SET NX 先佔改回只讀檢查→穿透（紅）。
- 洩漏斷言測試：發碼／驗證全流程後斷言 log 與 op-log payload 零六位碼零憑據；拆遮蔽→紅（SC-007）。
- captcha ctx 語境：以 login 語境簽出的題（ctx="login"）打 sendEmailCode→`emailCaptchaInvalid`
  （拆 ctx 斷言→跨語境重放通過、紅）。

- 導出判定三態測試：拆 lower() 歸一→大小寫變體誤判失配（紅）。
- 契約：拆 UpdateProfileReq 移欄斷言→直寫後門復活可測（紅）。
- 憑據：拆 uid 綁定→跨帳號重放通過（紅）；拆 used SET NX→重放通過（紅）；拆 code_mac secret
  參與→離線可暴力（單元測試斷言 mac 含 secret 輸入、紅）。
- 節流：拆「失敗不計額度」→寄信失敗後冷卻仍被佔（紅）。
- 唯一預檢命中不回補（枚舉抑制、spec FR-001）：對他活性帳號已持有信箱發碼→`emailTaken` 後
  冷卻鍵仍佔、日計數不回補、mailpit 零信；拆「命中不回補」改回補→「此信箱已否被綁」
  枚舉成本歸零（紅）。
- 唯一索引：直插重複 lower 值→DB 拒（紅）；m014 前置掃描對預植重複資料→up Err 指名（紅）。
- prod 形：grep compose base 無 mailpit（斷言存在即紅、SC-008）。

## 資料清理

- 測試會員與衛星列：psql 清（`sys_user_email_verify WHERE user_id IN 測試帳號`＋還原 user_email）；
  mailpit `DELETE /api/v1/messages` 清箱；redis `emailverify:*` 鍵 TTL 自清毋需手動。
