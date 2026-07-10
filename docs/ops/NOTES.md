# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004 系統設定、005 認證縱切、006 會話生命週期、007 登入失敗節流）已收刀
  （007 merge 3500c68；pins/summary/ADR 見 events／STATE）：007 以合成終態落地 B-010——per-user 滑動窗計數
  （facade raw SQL 單 statement、GREATEST 三源下界）＋Redis 負快取 L1（★僅由 L2 再判路徑③寫入、命中不續期、
  TTL=min(window,900)，假鎖構造上不可能；supersede ADR 0016）＋CAPTCHA 軟區（無狀態 HS256 簽題、第三把秘鑰、
  ans_mac 答案不可還原、★提交即消耗、產題零 Redis 寫入）＋超管手動解鎖（★SET marker→DEL lock→op-log 寫死動作序）
  ＋七源降級矩陣（全鏈 fail-OPEN、⑤unlock marker 讀故障為唯一 fail-closed 例外、七 label 結構化告警＋壓制麵包屑）
  ＋稽核邊界收斂 FR-010＋三門檻鍵 runtime 可調＋nginx limit_req（5r/s burst40、429 非信封）；順帶清償 B-071＋B-055
  的 schema 閘既有紅燈（ADR 0039）。憲法 v1.4.1（§I.7 島 E＋§III.2 LOGIN-CAPTCHA-WIRING＋「零新 key」釋義）；
  ADR 0037(節流合成終態)/0038(負快取 supersede 0016)/0039(schema 閘批次)/0040(★新軌道)/0041(MODAL-WIRING 用途補完)；
  cargo test 220 綠、三閘全綠、CDP-1/2 實機全綠、T085 六鏡頭零 confirmed finding。
- 下一步：**auth family 最後一把＝IP 閘刀**（B-019/B-024、上游 ADR 0017）。★**前提未定**：需先拍板 ingress 拓樸
  （rev3 有完整三層信任模型〔peer-gate → CDN 位置錨 → rightmost-untrusted〕，rev4 尚無等值信任錨基建；per-IP 節流的
  安全性 100% 由「防偽的真實來源位址」承擔，013 XFF 取證明確不承襲不重建）。該刀進場前 007 的 per-user 節流
  **結構性無法涵蓋**輪換帳號名的資源消耗型攻擊（已由 FR-022 形制上限＋FR-017 網路層限流分擔）。
  ★brainstorm 起手前先讀 B-032／B-033 殘餘（IPv6 前綴鍵、IP 白名單跳節流、鎖定專屬審計欄／grafana 規則、HLL 廣度、
  IP 維 TTL 拆分）與 B-072（refreshToken/logout 端點零節流）。
- 007 遺留：B-072（refreshToken/logout 無節流）／B-073（region 地理解析恆空之去處）／B-074（軟區決策負快取）／
  B-075（captcha 強化＋兩則 UX 觀察）／B-076（schema-gate 白名單整批重凍退路）／B-077（unlock op-log 持久化）／
  B-078（refresh ±5s 容差測試在全量並行下偶發 flaky）。B-018 部分消化（三層緩解已落；殘餘＝per-user 維度結構性
  無法阻止第三方觸鎖，徹底緩解需 IP 信任白名單或信任裝置）。
- 006 遺留 primitive／再議：停用帳號/改密/admin 踢除端點（B-064、消費 revoke_others_of_user primitive＋發
  session_event(revoked)；併 B-029 改密撤 session）；alova 棧接入真實 auth 時補 idle toast＋onError i18n
  （B-069、ADR 0035/0036 觸發再議）；孤兒 reaper（B-063）。005 遺留 B-060/B-061 仍在。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器＋CDP 實機）；
  ★`.vue` template 區標記須用 `<!-- -->` 形（007 首用、L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite dev 未必熱載新字典、否則 toast/modal 顯 raw key、L-015）。
- ★CDP 驅動登入表單三坑（L-121~L-123）：錯密須先過 client rules（6-18 位字母/數字/底線）否則 validate 早退零請求；
  dev API 走 vite proxy（`/proxy-default/*`、不含 `/api`）且 page-context hook 攔不到、resource timing buffer 需先 clear；
  `showErrorMsg` 有 errMsgStack 去重、連兩擊同訊息第二則恆空。
