# Implementation Plan: 007-login-throttle 登入失敗節流

**Branch**: `007-login-throttle` | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-login-throttle/spec.md`

## Summary

登入失敗節流以**合成終態**落地（supersede ADR 0016 負快取層）：per-user 滑動窗計數（權威＝`sys_login_attempt`）＋
Redis 負快取短路（★**僅由 L2 再判路徑寫入**、命中不續期、TTL ≤ 窗）＋CAPTCHA 軟區（**無狀態 HMAC 簽題、產題零快取
寫入、提交即消耗、答案空間 ≥ 10⁶**）＋超管手動解鎖（**先寫 marker、後清快取**）＋七源降級矩陣（全鏈 fail-OPEN、
唯一例外＝marker 讀故障）＋結構化降級告警。稽核邊界收斂為「**只有被密碼雜湊實際驗證過的終局才落恰一列**」。
技術取徑：零結構變更（唯一 migration＝三設定鍵純 seed）、L2 計數落 facade raw SQL 單 statement（GREATEST 三源下界）、
challenge 走獨立 claims struct＋`jsonwebtoken` HS256 第三把秘鑰、nginx `limit_req`（`$binary_remote_addr`、429、
不依賴 XFF）。治理：ADR 0037/0038/0039/0040＋§I.7 入島 E＋§III.2 新★軌道＋version 1.3.0→1.4.0。

## Technical Context

**Language/Version**: Rust（rust-api、全新寫 §I.5；容器內 build/test、全程 serial）；TypeScript/Vue（base-web fork、
fork-delta `rev4-inline`）；nginx conf（deploy/）

**Primary Dependencies**: sea-orm／jsonwebtoken 10.4.0（`rust_crypto`）／argon2 0.5.3／sha2 0.10.9／hex 0.4.3／
redis 1.3.0／tracing 0.1.44＋tracing-subscriber 0.3.23／metrics 0.24.6（**以上全為 `server` 直接依賴、皆既有**）
＋**唯一新 crate＝`captcha` 1.0.0**（圖形驗證碼產圖；★user 拍板 2026-07-10、ADR 0037 §G.22；rev3 無先例、
雙源查核見 research R2。輸出 PNG；其 `stateless`／簽章能力一律不用）

**Storage**: PostgreSQL（`sys_login_attempt`＝**節流計數權威源**、`system_settings`＝三門檻鍵、`sys_operation_log`
＝解鎖稽核）＋Redis（鎖定負快取／解鎖標記／captcha 單次標記／壓制麵包屑，**皆可重建、非權威**）

**Testing**: `cargo test --workspace`（容器內 serial）＋契約覆蓋閘（`tests/contract.rs` bijective）＋
`entity_access_lint`／`fork-delta-lint`／locale 對等＋CDP 實機（`127.0.0.1:9229`／Edge@9229／front-nginx 全鏈路）

**Target Platform**: Linux 容器（compose 三檔）；單實例

**Project Type**: web-service（rust-api）＋ web-app fork（base-web 接线）＋ deployment config（nginx）

**Performance Goals**: admin 內部規模（低 QPS）、無硬延遲目標。★節流熱路徑分層：鎖中＝1×Redis GET（零 DB）；
軟區缺-captcha＝1×Redis GET（marker）＋1×settings 查詢＋1×L2 COUNT（**未被負快取隔離**，成本誠實記入 ADR 0038、
真實量級閘＝nginx `limit_req`）；正常登入＝上述＋argon2（~百 ms、主宰成本）

**Constraints**: 零結構變更（不建表/不加欄/不加索引）；13 碼零新碼；rust 容器內 serial build/test；base-web 無測試
框架→靜態閘＋CDP；fork-delta 紀律；★**四項測試機制先決須先建**（否則守門恆綠，spec Assumptions）

**Scale/Scope**: admin 後台、單實例；`sys_login_attempt` 為 append-only（retention 政策＝B-016，不在本刀）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

§IV 9 題逐項（對照 constitution **v1.3.0**）：

| # | 題 | 判定 |
|---|---|---|
| 1 | §I.1 base-web 為權威——rust-api 未提供 base-web 用到的 endpoint？ | **PASS**（無 under-provide；新增 `GET /auth/loginCaptcha`＋`POST /systemManage/unlockLogin` 皆 rev4-new、各帶契約 case；`LoginReq` 加兩 optional 欄為 additive、既有 client 不破） |
| 2 | 動 base-web inline？屬 §III.2 哪用途？授權內？ | **⛔GATE→Amendment**：動 `views/_builtin/login/modules/pwd-login.vue`（驗證碼條件渲染／點圖換題／答錯重取）——**逾現有四★軌道**：AUTH-WIRING 三用途 (a)~(c) 無 pwd-login、無圖形驗證碼 UI；I18N-WIRING (i) 明訂「不改控制流」；MODAL-WIRING 限 `views/manage/**`＋user-center；LOGOUT-UX-WIRING 限兩用途。→ 需**新★軌道 `BASE-WEB-LOGIN-CAPTCHA-WIRING`**（ADR 0040、§V.2 MINOR）。★`authStore.login` 回傳形是否納軌道邊界 → research R12 |
| 3 | menu 走 Casbin enforce？demo 進 seed？ | **PASS/N/A**（本刀無新 menu／demo；兩新端點皆非 menu） |
| 4 | wire 對齊 §I.3？ | **PASS**（envelope 三欄形不動、錯誤信封 MUST NOT 加欄；**13 碼零新碼**——reuse `2222`(Biz 自帶 key)／`1000`／`5003`；`msg`＝穩定 i18n key；逐欄 id 型不涉。★**nginx `429` 為基建層拒絕**、請求根本不進 rust-api，與 `502`/`504` 同類，不受「信封普遍性」約束——clarify 2026-07-10 已定調、理由入 ADR 0037） |
| 5 | 前代 source 拷貝？ | **PASS**（rev3 019/021/022 唯讀參照、全新寫、防回歸條款；★**013 XFF 取證明確不承襲不重建**；rev3 **無**圖形驗證碼先例〔research R2 已查證〕，故無可拷之碼） |
| 6 | 抵觸 §II 拍板？ | **PASS**（#1 unknown header／#2 auth route dynamic／#3 prod `/api/*` 前綴 皆不動；nginx 改動落在 `/api/` 之下、不改前綴語意） |
| 7 | 觸及 §III ★軌道？補完 vs 新能力？ | **⛔GATE→Amendment**（同 Q2）：**新能力**（登入頁圖形驗證碼 UI＝全新互動面，非既有授權頁的 dispatcher 補完）→ §V.2 MINOR 新★軌道 |
| 8 | 新建業務表？§I.6 審計欄？ | **PASS/N/A**：★**零結構變更**——不建表、不加欄、不加索引（FR-015）。唯一 migration `m005` 為 `system_settings` 三列**純增量 seed**（照 m003 模板、`ON CONFLICT DO NOTHING`、down 限定鍵 DELETE），不觸 archetype。★連帶：本刀於 schema 期修 gate1／gate2／audit 三閘既有紅燈（FR-016、ADR 0039），其中 archetype-map 補登記 006 的 `session_event`（變體 B） |
| 9 | 觸及 §I.7 行為島？該入憲未入憲？ | **⛔GATE→Amendment**：本刀引入**節流狀態機**（未鎖→軟區→鎖定→解鎖/自癒），§I.7 現有島 A/B/C/D 皆不涵蓋 ⇒「該入憲而未入憲的新行為島」→ 隨本刀排入 **§I.7 MINOR Amendment（島 E）**；provenance ADR 0037。設計以 state-machine 鏡頭（非 CRUD 格子）。★E1 的 fail-OPEN 方向一經入島、反轉即 MAJOR |

**Gate 結論**：Q2/Q7（新★軌道）＋Q9（§I.7 島 E）→ **需 §V.2 Amendment（user 親決；憲法明訂「Claude 不主動 amend」）**。
兩者皆 MINOR，其餘七題 PASS。

### Amendment 提案（★待 user 親決；§V.2 步驟 2）

- **A1（§III.2 新★軌道）**：新增 `BASE-WEB-LOGIN-CAPTCHA-WIRING`，**嚴限一用途**：
  「(i) 密碼登入表單的圖形驗證碼接线——`views/_builtin/login/modules/pwd-login.vue` 於收到需驗證碼回應時條件渲染
  驗證碼圖與輸入欄、點圖換題、帳號名變更重取、答錯後自動重取；含其資料取得所需之最小 store/service 接线。
  嚴格限『登入表單驗證碼 UI』，不改攔截器碼分組／logout／refresh／retry 控制流。」
  ADR **0040** draft→accepted；MINOR（§V.3「新增 ★ 軌道」）。
- **A2（§I.7 行為島進場）**：島 **E（登入失敗節流）** 之方向性不變式入 §I.7——E1 真相分層與 fail 方向（含**唯一
  fail-closed 例外**＝解鎖標記讀故障）／E2 防枚舉延伸／E3 審計邊界／E4 captcha gate 與硬鎖優先。
  措辭＝brainstorm §8（經 clarify 修訂：E4 併入「提交即消耗」與「答案空間下界」）。provenance ADR **0037**。
  MINOR（§V.3「行為島隨刀進場」）。
- **version**：1.3.0 → **1.4.0**（兩 MINOR 同一 amendment commit；比照 1.3.0「島填充＋新軌道同筆」先例）。
- **執行**（approval 後）：ADR 0037/0038/0039/0040 寫入 `docs/arc42/decisions/`＋status accepted；更新
  constitution §I.7（島 E）＋§III.2（新軌道全文）＋version＋Amendment log；`tools/docs-sync generate`
  （回填 `0016.superseded_by=[0038]`＋DECISIONS-INDEX＋STATE）；獨立 commit
  `docs(constitution): amend §I.7 島 E＋§III.2 LOGIN-CAPTCHA-WIRING（1.3.0→1.4.0）`。

## Project Structure

### Documentation (this feature)

```text
specs/007-login-throttle/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1 常數時間比對／R2 產圖 crate 兩案／R5 L2 查詢／R7 測試四先決／R8 nginx／R12 前端接线）
├── data-model.md        # Phase 1（節流狀態機／Redis key 表／challenge claims／settings 三鍵／稽核落列規則）
├── quickstart.md        # Phase 1（後端測試＋七源降級＋CDP-1/2）
├── contracts/           # Phase 1（loginCaptcha／unlockLogin／login additive／nginx 429）
└── tasks.md             # Phase 2（/speckit-tasks）
```

### Source Code (repository root)

```text
rust-api/
├── migration/src/m005_login_throttle_seed.rs   # 三設定鍵純 seed（照 m003 模板）＋lib.rs 註冊
└── server/src/
    ├── config.rs / state.rs                    # 新增 captcha 簽章 secret（_FILE 優先＋boot fail-loud）
    ├── validation.rs                           # NUMBER_RANGES 加三行＋界值測試
    ├── throttle/                               # ★新模組：門檻解析＋fail-default／狀態機判定／降級告警
    ├── captcha/                                # ★新模組：產圖＋簽題（獨立 claims）＋驗題＋單次標記
    ├── redis/mod.rs                            # 新 key-builder（throttle_dim_key）＋單次標記 SET NX
    ├── model/facade/
    │   ├── sys_login_attempt.rs                # ★新增 count_recent_failures（首支 facade raw SQL）＋cfg(test) 注入接點
    │   ├── system_settings.rs                  # ★新增 find_by_keys（is_in）
    │   └── sys_operation_log.rs                # ★新增 insert（單寫 best-effort、非 txn 綁定）
    ├── model/audit.rs                          # AuditOperation 加 Unlock → "UNLOCK"
    ├── handler/auth.rs                         # run_login 插入節流閘（FR-022 形制檢查 → ① → ② → ③ → ④ → ⑤）
    ├── handler/throttle.rs                     # ★新：loginCaptcha 產題／unlockLogin 解鎖
    └── router.rs                               # ROUTES const append 兩條（Public／Policy）

rust-api/server/tests/contract.rs               # 補兩 case＋case 數 14→16

base-web/  (★BASE-WEB-LOGIN-CAPTCHA-WIRING、fork-delta rev4-inline)
├── src/views/_builtin/login/modules/pwd-login.vue  # ★本刀首觸此檔（零既有標記）；template 用 <!-- --> 標記
├── src/service/api/rev4-login-captcha.ts           # 我方新檔（取題 wrapper）
├── src/typings/api/rev4-login-captcha.d.ts         # 我方新檔（declaration merging，不動凍結的 auth.d.ts）
├── src/locales/langs/{zh-tw,zh-cn,en-us}.ts        # 兩新 backend.* 鍵（zh-tw 免標記；zh-cn/en-us 落既有 START…END）
└── src/typings/app.d.ts                            # Schema.backend 型（既有 START…END 圈界內）

deploy/nginx/
├── nginx.conf                                  # 取代裁剪聲明：limit_req_zone＋limit_req_status 429（http context）
└── conf.d/_locations.inc                       # 套用 limit_req（落點 → research R8 拍板）

tools/schema-gate                               # gate1 結構 additive 白名單＋B-055 長度 sidecar（ADR 0039）
docs/ops/reference-src/archetype-map.json       # 補登記 session_event（audit 閘現紅）
```

**Structure Decision**: rust-api 後端主體（全新寫 §I.5）＋base-web 前端接线（fork-delta）＋deploy/nginx（網路層限流）。
沿用 005 三態 router（Public/Authed/Policy）／facade 分層（handler 禁 path-root `entity::`、facade 豁免）／
契約機器化（ROUTES↔case bijective 覆蓋閘）。★新增兩個 server 子模組（`throttle/`、`captcha/`）而非塞進
`handler/auth.rs`——後者已 3000+ 行含測試，且節流／captcha 是可獨立推理的單元（brainstorming「isolation and clarity」）。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| 新★軌道（§III.2 Amendment） | 登入頁圖形驗證碼 UI 逾既有四軌道紅線（AUTH-WIRING 無 pwd-login／無 captcha UI；I18N-WIRING (i) 不改控制流） | 塞進既有軌道＝踩穿授權紅線；新軌道最小、精確一用途 |
| §I.7 島 E 入憲 | rev3 節流經三次疊層（019→021→022）＋as-built 勘誤續命；fail 方向與審計邊界須凍結防翻案 | 不入憲＝§IV Q9「該入憲未入憲」不通過；島設計本就 state-machine 鏡頭 |
| 首支 facade raw SQL（`count_recent_failures`） | `GREATEST(now()-window, 最近窗內 success MAX, unlock marker)` ＋相關 scalar subquery 無法以 SeaORM builder 單 statement 表達 | 拆多次查詢＝破「單 statement」＋增 round-trip；handler 已有 production raw SQL 先例（`advisory_lock_user`），facade 化零紀律風險（`entity_access_lint` 只掃 handler） |
| 解除 005 FR-016「無節流鎖定」邊界 | 本刀存在的全部理由；比照 006 反轉 005 FR-016 之慣例、立 ADR 記錄 | 不解除＝本刀不存在 |
| nginx `limit_req` 納 scope | FR-017；`nginx.conf` 裁剪聲明逐字指名「limit_req_zone 速率限制 → auth 功能刀」＝本刀 | app-level 限流仍燒請求處理成本，違「產題運算成本由網路層承擔」；且 `$binary_remote_addr` 不依賴 XFF 信任模型，與 per-IP 遞延不矛盾 |
| 新增 `sys_operation_log::insert`（單寫） | unlock 業務寫落 Redis、**無法**與 op-log 共 DB txn | 複用 `mutate_in_txn` 空業務閉包＝語意謊報（該函式全部目的就是「業務寫＋op-log 綁同一 txn」），可讀性與意圖失真 |

## Phase 進度

- **Phase 0（research.md）** ✅：R1 常數時間比對之精確界定（★spec 措辭 refine）／R2 產圖 crate 兩案（★user 拍板）／
  R3 nonce 沿 `OsRng` 既定 pattern／R4 challenge 獨立 claims struct／R5 L2 查詢＋NULL marker 安全性／R6 `find_by_keys`／
  R7 測試四先決可行形／R8 nginx 落點（★plan 拍板）＋**dev 繞過缺口**／R9 端點接線＋契約閘／R10 op-log `Unlock`／
  R11 wire-schema 只抽回應型／R12 前端接线障礙（`authStore.login` 吞 msg）。
- **Phase 1** ✅：data-model.md／contracts/throttle-endpoints.md／quickstart.md。

## Post-Design Constitution Re-Check

✅ **GATE 已解除**——Amendment 落地於 commit `1ffc1f8`（憲法 **v1.4.0**；user 親決 2026-07-10、§V.2）。逐題：

- **Q2/Q7**（base-web inline）：**PASS**。★軌道 `BASE-WEB-LOGIN-CAPTCHA-WIRING` 已授權（§III.2 一用途，ADR 0040）；
  邊界收斂為單一用途（pwd-login 驗證碼 UI），未溢出到攔截器控制流（`2222` 走既有一般錯誤通道、`.env` 碼分組不動）。
  ★`authStore.login` 回傳形的最小擴充（research R12）已由軌道文字「含其資料取得所需之最小 store/service 接线」涵蓋。
- **Q9**（§I.7 行為島）：**PASS**。島 **E** 已入憲（E1~E4，ADR 0037）；data-model.md 以 state-machine 鏡頭
  （非 CRUD 格子）坐實四條不變式（L1 唯一寫入者、提交即消耗、fail 方向七源表與唯一例外）。
- **Q4**（wire §I.3）：**PASS**（contracts 坐實：零新碼、信封不加欄、`429` 為基建層拒絕已於 ADR 0037 §F.18 記錄）。
- **Q8**（§I.6）：**PASS**（data-model 坐實零結構變更；m005 純 seed；archetype 不觸）。
- 其餘題維持 PASS。

**結論**：**Post-Design Constitution Check 全通過**；Complexity Tracking 六項皆 justified、無未解違規。
兩項 user 拍板亦已定案：**產圖 crate＝`captcha` 1.0.0**（ADR 0037 §G.22）、**nginx 限流落點＝(B) dedicated
exact-match**（ADR 0037 §F.17）。**可進 `/speckit-tasks`。**
