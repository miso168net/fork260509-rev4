# Implementation Plan: 008-ip-gate IP 存取控制閘＋信任錨基建

**Branch**: `008-ip-gate` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-ip-gate/spec.md`

## Summary

一把刀、兩台狀態機、四個施工分段。**P0** 前置＝dev 反代拓樸修正（B-079，使 dev/prod 拓樸同形、實機驗收有意義）；**P1** 信任錨基建＝operator TOML 信任模型 → 真實來源位址還原（三層＋兩 overlay、七態 confidence，純函式 test-first）→ `request_context_mw` 全域注入 → 稽核三欄值語意升級＋GeoIP → nginx CF 驗證閘；**P2** IP 閘門＝`sys_ip_rule` facade（表已 baseline）→ `ip_gate_mw` 白黑判定（ArcSwap lock-free＋Redis 門鈴）→ 寫端五端點（自鎖防護＝模擬變更後規則集）；**P3** per-IP 節流＝兩段式獨立三鍵（IP 維 GREATEST 只取兩源、拔 reset-on-success）→ L0 白名單跳節流 → unlock 加維度欄 → B-072 nginx 兩塊 → 降級/觀測收口。

技術途徑全新寫（RUSTAPI-SOURCE-ISOLATION），rev3 rust 源倉實碼作機理參照；xdb 工具 crate 依 §I.5 例外整檔拷貝。本刀**零建表 migration**（`sys_ip_rule` 已於 m001 凍結基線）、唯一 schema 變更＝三個 per-IP 門檻 settings seed。

## Technical Context

**Language/Version**: Rust（rust-api，容器內 serial build/test）；TypeScript/Vue（base-web，P0）

**Primary Dependencies**（釘版皆取 lockfile 現值、零新編譯，符 §6 雙查——lockfile 現值即採用並報告）：
- `arc-swap 1.9.2`（現為 redis transitive dep、加為直接依賴；lock-free 規則集熱交換）
- `once_cell 1.21.4`（現 transitive；xdb crate 的全域 region 快取需要）
- `futures-util`（redis pub/sub 的 `on_message()` stream 消費；redis 已拉進 compile graph）
- `ipnetwork 0.20.0`（現有，經 sea-orm `with-ipnetwork`；IPv6 /64 聚合用 `Ipv6Network::new(v6,64)?.network()`）
- `xdb`（vendored path crate，version 0.1.0、publish=false，§I.5 例外整檔拷貝自 rev3；依賴 once_cell＋tracing）

**Storage**: PostgreSQL（`sys_ip_rule` 規則表已 baseline、`sys_login_attempt` 稽核表、`system_settings` 三新 seed）；Redis（規則集門鈴 pub/sub＋per-IP 節流 L1 負快取）；operator TOML 信任模型檔（boot 一次載入、非 DB）；xdb 二進位資料檔（git-tracked、進 repo）

**Testing**: cargo test --workspace（容器內、全程 serial）；純函式 table-driven（`resolve_client_ip`／`decide`／`would_self_lock`）；負向自證守門（IP 維 GREATEST 誤加 reset-on-success／破壞 Tier-2 walk／關自鎖／per-IP 計數漏 WHERE）；crafted-XFF 實機驗收（經 :42080）；schema-gate 三閘

**Target Platform**: Linux 容器（rust-api＝axum 0.8.9；front-nginx 反代）

**Project Type**: web-service（rust-api 後端）＋前端接線（base-web，僅 P0）

**Performance Goals**: 閘門判定每請求零 DB/Redis（ArcSwap `.load()` 微秒級）；規則變更 ≤5s 多副本收斂；per-IP 節流沿 007 的 L1/L2 分層

**Constraints**: 全鏈 fail-OPEN（唯一例外＝寫端自鎖 fail-closed）；zero 新錯誤碼（reuse 5003/2222）；零建表 migration；base-web inline 改動走 fork-delta 紀律

**Scale/Scope**: 13~17 執行單元（近 007 的 13 單元先例上緣）；admin 規模規則集（記憶體 `Vec<IpNetwork>`）

## Constitution Check

*GATE: 對照 constitution v1.4.1 逐題 yes/no（§IV 九題）。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否**。IP 規則五端點的 casbin 政策已於 m002 baseline seed（getIpRuleList/addIpRule/updateIpRule/deleteIpRule/restoreIpRule）；`unlockLogin` 為 007 既有端點本刀擴維度欄。base-web 目前無 ipRule service 呼叫（D4 拍出 UI）——後端先出端點、前端頁遞延（B-061），不違權威（base-web 未用即無對應缺口）。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是**（僅 P0）。B-079 改 `src/utils/service.ts`＋`build/config/proxy.ts`（兩檔首筆 fork-delta 修改型、逐字 `原行:`）＋`.env.test`／`.env.prod` 修改型（ADAPT 涵蓋）＋`vite-env.d.ts` 新增型。前兩檔**逾現有★軌道涵蓋** ⇒ **需登記新★軌道**（§V.2 Amendment、MINOR bump、user 親決，比照 ADR 0040）。→ 見 Complexity Tracking。 |
| Q3 | menu 顯示走 Casbin enforce？demo menu 進 seed 而非隱藏？ | **不涉**。`manage_ip-rule` 選單項 002 已 seed、本刀不建頁（D4）；無新 menu。 |
| Q4 | wire 設計對齊 §I.3 權威序與不變式？（envelope／id 型／13 碼／msg=key） | **是**。阻擋 reuse `5003`→403；selfLock 走既有業務碼（`2222` 系，plan 定）；unlock 加**選用** `dimension` 欄（未帶＝帳號維、向後相容）＝既有端點契約擴充、有契約案覆蓋；**零新碼**。 |
| Q5 | 從前代 source 拷貝 code？屬 §I.5 例外？觸發防回歸？ | **部分**。`xdb` 工具 crate 屬 §I.5 明列例外（整檔拷貝、已預授權）。信任錨/閘門/節流全新寫、rev3 實碼僅機理參照；防回歸＝rev3 已被本刀改善的四項（tunnel skip 集對稱、decide 單一來源、信任錨最小化、CF overlay peer 條件）與 IP 維 GREATEST 兩源**不得帶回 rev3 舊行為**。 |
| Q6 | 抵觸 §II 拍板？ | **否**。§II #3 prod 路徑前綴 `/api/*` strip 主流不動；本刀在 nginx 加 CF 閘與兩塊 exact-match，不改 strip 語意。 |
| Q7 | 觸及 §III ★ 軌道？授權邊界內？補完還是新能力？ | **是**（同 Q2）。B-079 兩檔屬**新能力**（新 dev 反代拓樸接線、逾現有五★軌道枚舉）→ 立新★軌道 ADR、user 親決。 |
| Q8 | 新建業務表？含 §I.6 六審計欄？ | **否**。`sys_ip_rule` 已於 m001 凍結基線建齊（11 欄含六審計欄、partial-uniq、archetype-map variant A 已登記、fixtures 已凍結）。本刀唯一 schema 變更＝三個 settings seed（gate2 additive 白名單）。→ 零建表、零 archetype 登記、零表數 bump、零 gate1 結構白名單。 |
| Q9 | 觸及 §I.7 已入憲行為島？invariants 保持？state-machine 鏡頭？新島進場？ | **是**。①**新島 F（IP 閘）進場**＝MINOR Amendment、不變式入 §I.7（F1~F5）；②**島 E 交互**＝E1~E4 全數保持（IP 維 GREATEST 兩源、跨維度硬鎖優先、captcha 綁帳號提交即消耗、審計邊界、防枚舉一般化）；③supersede ADR 0038 調整項二（啟用 IP 維）。全走 state-machine 鏡頭（判定序、真相分層、降級方向）。 |

**Gate 結論**：通過。唯一需 Amendment 者＝Q2/Q7 的 B-079 新★軌道（user 親決、於 P0 完成時 commit）＋Q9 的新島 F 進場（MINOR）＋四份 ADR draft。皆為既定治理動作、非違規；記於 Complexity Tracking。

## Project Structure

### Documentation (this feature)

```text
specs/008-ip-gate/
├── plan.md              # 本檔（/speckit-plan 產出）
├── research.md          # Phase 0：8 拍板/技術決策（含兩 plan 拍板題定案）
├── data-model.md        # Phase 1：實體＋欄位＋狀態轉移＋三閘影響
├── quickstart.md        # Phase 1：實機驗收（crafted-XFF／nginx CF 閘 dev 驗／429／自傷復原）
├── contracts/
│   └── ip-gate-endpoints.md   # Phase 1：五規則端點＋unlock 維度欄擴充契約
├── checklists/
│   └── requirements.md  # /speckit-specify 產出（已存在）
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本步）
```

### Source Code (repository root)

```text
rust-api/                         # RUSTAPI-SOURCE-ISOLATION 軌道、全新寫
├── xdb/                          # ★新增：§I.5 例外整檔拷貝自 rev3（crate＋resources/ip2region.xdb）
├── server/src/
│   ├── config.rs                 # ＋TrustModel TOML 載入（fail-safe fallback）＋xdb 路徑
│   ├── state.rs                  # AppState ＋ip_rules(Arc<ArcSwap<RuleSet>>)＋trust_model＋xdb_ready（改全部 8 處字面建構）
│   ├── main.rs                   # boot：load_ruleset＋trust_model＋xdb 守門＋spawn watcher
│   ├── trust/                    # ★新增：resolve_client_ip 純函式（三層＋兩 overlay＋七態 confidence）
│   ├── ipgate/                   # ★新增：RuleSet／decide 純函式／load_ruleset／would_self_lock／watcher
│   ├── middleware/               # ★新增：request_context_mw（注入 RequestContext）＋ip_gate_mw（判定）
│   ├── router.rs                 # ＋HttpMethod::Delete；＋規則五端點路由；掛 request_context_mw（:259）
│   ├── redis/mod.rs              # ＋DIM_IP 常數；pub/sub（另存 Client）；throttle_key 零改動
│   ├── throttle/mod.rs           # precheck 加 IP 入參；IP 維並列判定；DIM_IP
│   ├── model/facade/
│   │   ├── sys_ip_rule.rs        # ★新增：load_active／list／CRUD（mutate_in_txn＋op-log）
│   │   └── sys_login_attempt.rs  # per-IP count SQL（WHERE 改 IP 欄、GREATEST 拔源②）；region 落值
│   ├── handler/
│   │   ├── ip_rule.rs            # ★新增：五端點（normalize_cidr／validate＋自鎖檢查）
│   │   ├── throttle.rs           # unlock 加 dimension 欄（預設帳號維）
│   │   └── auth.rs               # audit_from_request 讀 ctx；region 組裝；precheck 傳 real_ip
│   └── validation.rs             # ＋IP 三鍵 NUMBER_RANGES
├── migration/src/
│   ├── m00X_ip_throttle_seed.rs  # ★新增：三 settings seed（照 m005 形）
│   └── lib.rs                    # ＋註冊
tools/
├── schema-gate                   # ＋SEED_ADDITIVE_ALLOWLIST 三條
└── docs-sync                     # ＋ROUTE_METHODS["Delete"]；self-test 探針換 Patch
deploy/nginx/                     # 外層 repo、零 fork-delta
├── nginx.conf                    # ＋CF geo/map 閘（:41）；:45 註解補述
└── conf.d/_locations.inc         # ＋refreshToken/logout 兩塊 exact-match；三 /api 塊＋X-CF-Verified 注入
base-web/                         # 僅 P0（B-079 新★軌道）
├── src/utils/service.ts          # 修改型（首筆）：createProxyPattern → '/api'
├── build/config/proxy.ts         # 修改型（首筆）：target → rust-api:8080
├── src/typings/vite-env.d.ts     # 新增型：新 proxy target env key
└── .env / .env.test / .env.prod  # 修改型（ADAPT）
```

**Structure Decision**: rust-api 全新寫，新增 `trust/`（信任錨純函式）、`ipgate/`（規則集＋判定＋watcher）、`middleware/`（兩支 mw）、`xdb/`（§I.5 例外拷貝）四個模組群；middleware 拆兩支（`request_context_mw` 注入＋`ip_gate_mw` 判定）契合 B-046 單一來源與 rev3 疊放先例。P2 的 facade/handler 沿既有 archetype B 先例（`sys_login_attempt.rs`）。

## Complexity Tracking

> 本刀的「複雜度」皆為既定治理動作（非違規），逐項列出治理路徑：

| 項目 | 為何需要 | 治理路徑 |
|---|---|---|
| B-079 新★軌道（Q2/Q7） | `service.ts`／`proxy.ts` 兩檔首筆 fork-delta 逾現有五★軌道枚舉 | 立新★軌道 ADR（比照 0040）、user 親決、軌道全文入 §III.2＋MINOR bump；於 **P0 完成時** commit（不延收刀），使治理產物不與 008 主體耦合 |
| 新島 F 進場（Q9） | IP 閘為新行為島 | MINOR Amendment、F1~F5 入 §I.7；入憲後 fail-OPEN 方向反轉＝MAJOR |
| supersede ADR 0017 真實 IP 還原節 | 四項改善（tunnel skip 集對稱／decide 單一來源／信任錨最小化／CF overlay peer 條件）翻案 0017 骨架 | 新 ADR `supersedes: [0017 對應節]`、user 親決 |
| supersede ADR 0038 調整項二 | 啟用 IP 維（0038 只啟用帳號維） | 新 ADR、含 IP 維 GREATEST 兩源拍板 |
| region/GeoIP 語意 ADR | 消化 B-073、xdb 進 repo（P-Q2 拍板） | 新 ADR、記 §I.5 例外拷貝＋資料檔 provenance |
| B-032「鎖定專屬審計欄」won't-fix ADR | 島 E3 鎖定零稽核列⇒該審計區分無標的 | won't-fix/by-design ADR（CLAUDE.md §4） |
| HttpMethod::Delete（P-Q1） | 全站首個非 GET/POST 動詞、對齊 rev3 as-built | 非 Amendment（wire 慣例延伸、零凍結面改動）；docs-sync self-test 探針換 Patch |
