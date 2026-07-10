---
id: "0037"
title: 登入失敗節流合成終態（per-user 滑動窗＋負快取＋CAPTCHA 軟區＋手動解鎖；§I.7 島 E 進場）
date: 2026-07-10
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-10 007-login-throttle brainstorm 11 拍板＋對抗式健全性審查（6 鏡頭、5 blocker/23 major/17 minor 全折入）＋speckit-clarify 4 題＋plan Constitution Check Q2/Q7/Q9（user 親決 2026-07-10）；上游＝B-010（rev3:DECISIONS§1-⚠️w、K1-32、ADR 0018 B 組重審轉 BACKLOG），併 B-017/B-018/B-022/B-032/B-033"
tags: [auth, throttle, captcha, security, behavior, constitution-amendment]
---

## 背景

005 明示「無節流鎖定」（FR-016 邊界），登入端點對**線上**暴力猜密碼零設防——argon2 的離線抗性在線上通道毫無意義。

rev3 的節流經三次疊層演化：019 落地（滑動窗 gate、per-user 5 次/15 分＋per-ip 20 次/15 分、fail-OPEN、
D3 一般化訊息）→ 021 加 Redis 負快取並**有意識反轉**「鎖中逐筆寫稽核」→ 022 白名單 IP 整段跳過節流。
前刀 spec 只能靠 as-built 勘誤註記續命。B-010 要求以**合成終態**一次重新表述、終結勘誤鏈。

本刀 brainstorm 定案後跑 6 鏡頭對抗式健全性審查，抓出 5 個 blocker（皆通過獨立 skeptic 反駁驗證、零被駁回），
其中三個是設計層真漏洞：①captcha challenge 態寫入與 session 共用同一顆 Redis ⇒ 未認證者可撐爆之、
連帶使已撤銷會話在其 access 憑證時效內續活；②鎖中 L2 再判寫入的 sticky 列回饋進自身時窗 ⇒ 每 ~900s 一次
**免 captcha** 探測即可永久鎖死任一帳號；③captcha 降級方向反轉 ⇒ 合法使用者被 de facto fail-closed 擋死、
攻擊者附任意假 challenge 反而被放行且失敗照常計數。另 clarify 階段再揪出「輸入形制無上限」與
「無狀態改寫時靜默遺失『答錯即失效』性質」兩項。

## 決定

### A. 節流本體

1. **判定鍵＝所送出帳號名原文**（不區分帳號是否存在——防枚舉）；其正規化 MUST 與帳號身分解析的正規化
   嚴格一致（現況兩者皆為精確比對、大小寫敏感）。**per-IP 維度整組遞延 IP 閘刀**（見「不做」節）。
2. **權威源＝PG `sys_login_attempt` 滑動窗**（L2）；**reset-on-success** 以查詢形免費兌現（只數「最近一次
   窗內成功之後」的失敗）。**鎖的最長存續＝一個時窗**（非負快取存活時間）。
3. **Redis 負快取（L1）僅由「L2 再判路徑」寫入**——失敗路徑本身絕不直接武裝 L1。此為 blocker B4 的修正：
   否則並發成功登入推進計數下界後，失敗請求會以其密碼驗證前讀到的舊 count 造出與權威源矛盾的**假鎖**，
   且 L1 短路使其在存活期內無法自癒。現形之下假鎖在構造上不可能。命中不續期。
4. **鎖定期間被擋下的嘗試零稽核列**（含 L1 命中與 L2 再判兩路徑）。此為 blocker B2 的修正：`window` 可調至
   1440 分而 L1 TTL 上界 900s，若 L2 再判寫列，該列落入自身時窗 ⇒ 攻擊者每 ~900s 一次免-captcha 探測即可
   無限續鎖。**sticky 語意退場**——它對安全零貢獻（攻擊者本就被擋下），延長鎖只傷受害者，正是 B-018 的病。

### B. CAPTCHA 軟區（B-018 緩解主體）

5. 窗內失敗數 `≥ captcha_after` 時要求**圖形驗證碼**。challenge **無狀態**：以獨立 claims struct ＋
   `jsonwebtoken` HS256（第三把秘鑰 `APP_CAPTCHA_SECRET`）簽發，載 `nonce`／綁定帳號名／`exp`／
   `ans_mac = hex(SHA256(secret ‖ nonce ‖ lower(answer)))`。**產題對熱快取零寫入**（blocker B1 修正）。
6. **提交即消耗**：單次使用標記的寫入 MUST 發生於「簽章／有效期／帳號綁定」驗證通過**之後**、
   「答案比對」**之前**——一張題只能作答一次，答錯即失效、必須重取新題。**答案空間 ≥ 10⁶**。
   （clarify 修正：無狀態改寫時「答錯即失效」性質靜默遺失，且該改寫發生於對抗式審查之後、未經審查。）
7. **缺／錯／過期／重放之 captcha 嘗試 MUST NOT 計入失敗數、MUST NOT 落稽核列**——此為 B-018 緩解的
   **安全支點**：一旦計數，自動化工具只需送出不帶驗證碼的請求即可推滿計數、鎖住任意帳號。
8. **硬鎖優先於 captcha**：帳號已鎖定時，即使呈遞有效 captcha 亦不受理、且該 captcha 不被消耗。
   **未達軟區時完全忽略請求所帶的 captcha 欄位**（不驗、不消耗）——否則會白白消耗合法使用者手上那題。

### C. 手動解鎖與稽核

9. **`POST /systemManage/unlockLogin`**（super-only，消費基線已 seed 的 casbin 政策、零新 seed）。
   動作序**寫死**：①`SET` 解鎖標記（其時刻成為失敗計數的新起算下界）②`DEL` 鎖定負快取
   ③op-log 單寫 best-effort。**順序不可換**——反序留 race 窗，兩步之間的一擊登入會以舊列重新武裝 L1。
   `sys_login_attempt` 為 append-only、舊失敗列刪不得，故標記不可省。
10. **稽核邊界收斂為一句**：**只有被密碼雜湊實際驗證過的登入終局才落恰一列。** 其餘（L1 命中短路、
    L2 再判鎖、captcha-gate 拒絕、輸入形制超限）一律零列，量級走觀測層麵包屑。
    ★此規則**取代 005 FR-003／SC-002 的「每次登入終局恰一列」口徑**，其守門測試連動改寫。
    第一性論證：憲法 §I.6 archetype B 只規範 append-only／不可竄改，**未規範「每嘗試必寫」**；
    上鎖前歷程與觸發那一發皆照寫 ⇒ 鑑識鏈完整、鎖的成因可回溯。

### D. 降級方向（B-017）與告警

11. **全鏈 fail-OPEN**（定義＝不因基建故障而拒絕本應放行的登入），七個降級源：
    ①L1 讀故障→退 L2 並**整體停用 captcha 要求**；②captcha 單次標記寫故障→拒絕但**零計數**（不懲罰）；
    ③L2 count 故障→視 0 放行，★**若快取可用則無條件要求 captcha**（登入 fail-OPEN、機器人阻力 fail-safe）；
    ④稽核寫故障→不改登入回應（沿襲 005 best-effort，⇒ 計數斷供、永不鎖亦永不 captcha）；
    ⑤解鎖標記讀故障→**視為無標記**；⑥settings 缺值/不可解析→退預設常數；⑦L1 寫故障→忽略。
12. **⑤ 為全鏈唯一 fail-closed 例外**，明文入憲。★**不採**對抗式審查三支鏡頭一致建議的「視 marker 為 `now`」
    ——該案會使 Redis 故障期間**全站每個帳號的 count 下界都推到 `now`、節流整體關閉**，與 ① 的
    「退 L2、節流仍生效」直接矛盾。受影響集合僅「一個 window 內剛被 admin 解鎖」的帳號、admin 可重解。
13. **每一次降級 MUST 發結構化告警訊號**（`target="security.throttle"`＋`degraded=<源>`）＋預埋計數器。
    此為 K2-01「fail-OPEN 期間暴力嘗試裸奔且**無降級告警**」的清償。具體告警規則配置屬觀測層刀。

### E. 可調門檻與輸入形制

14. **三個 number 設定鍵**（super runtime 可調、改值即時生效）：`login_throttle_max_fails`（5、1..100）／
    `login_throttle_window_minutes`（15、1..1440）／`login_throttle_captcha_after`（2、1..100）。
    「軟區門檻 ≥ 失敗次數門檻」為**合法退化配置**（captcha 實質停用），不以跨鍵約束阻擋。
15. **設定缺值走 fail-default（退預設常數）**，與 `session_idle_timeout` 的 fail-loud `5000` 先例**刻意分歧**：
    TTL 缺值無法猜（影響簽章有效期）；節流門檻缺值可退常數且不該打斷登入入口。
16. **登入輸入形制上限**（clarify 新增）：於節流判定與密碼雜湊**之前**檢查帳號名與密碼長度上界，
    超限回 `1000`、**零稽核列、零雜湊運算、不消耗計數桶**。理由：節流判定鍵為攻擊者可控的帳號名，
    輪換超長帳號名可使每一發落入全新計數桶而永不觸鎖，卻仍各燒一次 memory-hard 雜湊並各寫一列
    長度無上限的 append-only 稽核列。字元集限制不加（無正確性影響）。

### F. 網路層與 wire

17. **nginx `limit_req` 納本刀 scope**（`nginx.conf` 裁剪聲明逐字指名「limit_req_zone 速率限制 → auth 功能刀」）：
    zone key `$binary_remote_addr`（nginx 自身觀察到的 TCP peer、偽造不了，**不依賴 XFF 信任模型**，
    故與 per-IP 遞延不矛盾）；**落點採 dedicated exact-match location**（登入端點與取題端點各一塊，
    照 `/api/metrics` 範式）而非套共享 `location /api/`——後者會使正常高頻操作與登入共用同一桶、
    逼 burst 開大而稀釋防護精度（rev3 註解自承此妥協）。觸發回 **HTTP `429`**（rev3 無此指令、本刀新增）。
18. **`429` 為基建層拒絕**：請求根本不進 rust-api、不走信封，與反向代理的 `502`／`504` 同類，
    **不受憲法 §I.3「信封普遍性」約束**（該條文治理的是 rust-api 的 API 面）。
19. **13 碼矩陣零新碼**：reuse `2222`（`Biz` 自帶 key）／`1000`／`5003`。新增兩個 msg key
    `auth.login.locked`／`auth.login.captchaRequired`，沿 `auth.login.*` 語意族（**非** `biz.*` 碼族）
    ——與同為登入失敗語意的既有 `auth.login.failed` 同族，語意族優先於碼族。

### G. 治理

20. **§I.7 進場島 E（登入失敗節流）**：E1 真相分層與 fail 方向（含唯一 fail-closed 例外）／E2 防枚舉延伸／
    E3 審計邊界／E4 captcha gate 與硬鎖優先。條文全文入 constitution §I.7、與本 ADR 同 commit。
    MINOR（§V.3「行為島隨刀進場」）。★**E1 的 fail-OPEN 方向一經入島，反轉即 MAJOR。**
21. **解除 005 FR-016「無節流鎖定」邊界**——屬破紀律例外，比照 006 反轉 005 FR-016（sys_token 零寫入）之慣例，
    以本 ADR 記錄。
22. **產圖 crate 釘版**（全域 §6 雙源查核：rev3 **無**圖形驗證碼先例）：**`captcha` 1.0.0**（user 拍板
    2026-07-10）。理由＝1.0.0 穩定（API 不破）、8 年專案、輸出 PNG（與設計假設吻合、零文件勘誤）。
    ★其 `stateless`／簽章能力一律不用——簽章、帳號綁定、單次標記全由我方自寫。
23. **常數時間比對之精確界定**：`ans_mac` 比對的兩側皆為 secret-keyed 高熵摘要，逐位元組比對的時序至多洩漏
    摘要前綴、對還原答案毫無幫助 ⇒ **by construction 安全**，不需 `subtle`。★`subtle`／`hmac` 在 rev4 僅為
    **傳遞依賴**（Rust 不允許直接 `use`，需新增 Cargo.toml 宣告）；採此構造使「零新增 crypto 依賴」在
    **build-graph 與 Cargo.toml 宣告兩層皆成立**。實作註解必須寫明此理由，防後人反射性 `use subtle`。

### H. 明確不做（won't-do，理由入本 ADR）

24. **漸進延遲**：評估後不採——`sleep` 持有連線槽、攻擊者可並行繞過、且懲罰合法手滑使用者。
25. **「剩餘 N 分鐘倒數」提示**：rev3 019 原單的 v1-defer 項，在 rev4 被**島 E2 憲法級封死**
    （MUST NOT 洩剩餘時間）。
26. **音訊驗證碼**：語音辨識已成熟，音訊通道的自動化破解難度遠低於圖形——一旦提供即成為 B-018 緩解的
    **普遍後門**（攻擊者一律走音訊）。
27. **帳號級 captcha 豁免旗標**：攻擊者可探測（對目標帳號連錯至軟區、看有無要求驗證碼）得知哪些帳號豁免，
    隨即對其免摩擦鎖人——B-018 緩解對最需保護的帳號歸零；且加欄破「零結構變更」。
28. **per-IP 維度計數與 XFF 真實 IP 防偽解析**：per-IP 節流的安全性 100% 由「防偽的真實來源位址」承擔。
    rev3 的 per-IP 節流是其獨立 XFF 取證刀（013、早 019 四天落地）的**下游唯讀消費者**——019 spec 逐字
    「本功能為下游唯讀消費⋯0 新表／0 migration／0 新元件」、FR-004 逐字「來源判定 MUST 以**經防偽解析的
    真實 client IP** 為準」。rev4 尚無等值信任錨基建（`ip_confidence` 恆 `"low"` 即誠實標記此事），
    在此基礎上做 per-IP 鍵可被 XFF 任意偽造規避。歸 IP 閘刀（B-019/B-024、ADR 0017）。
29. **地理解析**（`sys_login_attempt.region` 維持恆空）／**IP 白名單跳節流**（ADR 0017 已定歸屬）／
    **手動解鎖 UI**（歸 manage 頁刀）／**設定熱讀快取與其失效通知**（本刀未成為首個快取消費者）。

## 後果

- **005 連動改寫**：FR-003／SC-002 的 exactly-one 口徑改為「只有被密碼雜湊驗證過的終局才落恰一列」，
  其守門測試連動改寫（屬破紀律例外、本 ADR 記錄）。
- **B-018 為部分緩解、非徹底消滅**：captcha 可被人工／ML 農場破解，鎖死一個帳號的成本＝解出
  「鎖定門檻 − 軟區門檻」張題（預設 3 張）。徹底緩解需 IP 信任白名單（IP 閘刀）或信任裝置；殘餘另立條目。
- **拒絕路徑時序面 accepted**：`captchaRequired` 與 `locked` 回應不執行密碼雜湊、快於正常失敗數十毫秒。
  該差異揭露「該帳號名近期失敗數」，**不揭露帳號存在性**（真假帳號同鍵同計、同時進軟區與鎖定）。
- **無障礙 accepted**：不提供圖形驗證碼的無障礙替代（理由見 26）。救濟通道＝等一個時窗自癒／由**另一位**
  超級管理員手動解鎖。★配套部署紀律：**至少保留兩個超級管理員帳號**——此紀律亦是「唯一 Super 被鎖」
  邊角的通用解。
- **dev 曝露 accepted**：dev override 把 rust-api 直接曝在 host debug port，直連該 port 繞過 nginx `limit_req`。
  **prod 無此缺口**（base 層鐵律禁 host ports）。驗收紀律：不得以直連 debug port 規避限流。
- **軟區為未被 L1 隔離的熱路徑**：缺-captcha 的軟區請求永不計數、故永不上鎖、故永不被 L1 短路，每發都走
  一次快取讀＋一次設定查詢＋一次 L2 count。誠實記載於 ADR 0038；該路徑仍**比正常登入便宜**（argon2 主宰成本），
  真實量級閘為 nginx `limit_req`。
- **負快取層調整走 supersede**：ADR 0016 的「固定 900 秒 TTL」與「帳號／IP 雙維度 key」需調整 ⇒ **ADR 0038
  supersede 0016**。
- **schema 閘既有紅燈隨本刀 schema 期修復** ⇒ ADR 0039。
- **base-web inline 需新★軌道** ⇒ ADR 0040；plan Constitution Check Q2/Q7/Q9 GATE 隨兩者解除。
- 憲法 **v1.3.0 → v1.4.0**（島 E 進場＋新★軌道，兩 MINOR 同一 amendment commit）。
