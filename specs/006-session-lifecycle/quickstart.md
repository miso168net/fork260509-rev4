# Quickstart / Validation Guide — 006-session-lifecycle

端到端驗證會話生命週期。契約/schema 細節見 `contracts/`＋`data-model.md`；此檔只列可跑的驗證步驟與預期。

## Prerequisites

- compose 三檔起 postgres＋redis（`46379:6379`）＋rust-api；migrate 至 m004（partial UNIQUE index＋session_event）。
- seed 三帳號（Super/Admin/User、密碼 123456）；`single_session_default`＝off、`session_idle_timeout`＝60。
- base-web restart（toast 項驗前必做、L-015）；CDP 入口 front-nginx `http://localhost:42080`、`CDP:127.0.0.1:9229`。
- redis crate 釘版：實作前 §6 双查＋攤 user（research R5）。

## 後端驗證（容器內、rust 全程 serial）

```
# 全套（lib＋契約）
cargo test --workspace
```

須綠的關鍵測試（對照 spec §9／SC-007）：
- **rotation**：happy rotate（active→rotated＋新 active）；reuse grace（並發同票→一成功一冪等回後繼、family 不撤）；
  更早世代/超 grace→撤 family；找不到/過期→8888。
- **lock-then-redecide race**（L-075）：撤先於 rotate→鎖後見 revoked 拒發。
- **撤銷完整性**：revoke 與 rotate 並發後該 chain 零 active（loop-until-0-active）。
- **partial UNIQUE index**：同 chain 二 active insert→unique violation fail-loud。
- **denylist**：撤銷三步（PG→Redis→session_event）；enforce 命中 7777/8888；absence 放行；
  **Err/timeout→退 PG vs Ok(None)→放行 分流**（R7、SC-005）。
- **7777-on-refresh-kicked**：kicked 者走 refresh→7777（非 8888、SC-002）。
- **single-session**：`effective_single` 解析矩陣（inherit×global on/off、single、multi）；login kick 後**新 session
  仍 active、未進 denylist**（keep_sid off-by-one 回歸）；並發登入 advisory lock 序列化。
- **精確 idle**：last_activity 僅 valid-access 更新、**refresh-loop 不繞過 idle**、逾 N→8888、
  `access_TTL≤N×30<N×60` 不變式、降級界線 [N,N+access_TTL]。
- **TTL 公式改寫**：`refresh_ttl_secs`→`N×60+access_secs`；改寫 `refresh_writes_zero_sys_token_rows`／
  `refresh_valid_super_returns_new_pair_public`／`refresh_n5_halves_access_and_slides_window`／
  `jwt_ttl_formula_boundaries`（新值 60→3900、5→450）。
- **session_event**：五類事件各落恰一列（變體 B、SC-006）。
- **契約**：`/auth/logout` per-route case＋ROUTES↔case 覆蓋閘綠；13 碼零新碼。

## CDP 實機驗收（Edge@9229、front-nginx 全鏈路、L-053；toast 項前 restart base-web＋斷言無 raw key L-015）

- **CDP-1 single-session**：★先於設定頁切 `single_session_default`→**on**（或直改 DB）→瀏覽器 A 登入→
  B 同帳號登入→A 下次請求→**7777 阻斷 modal「已在他處登入」**（SC-002）。
- **CDP-2 精確 idle**：`session_idle_timeout` 改短（UI 下限 5 分；更短直改 DB `setting_value` 繞驗證）→
  持續操作不登出→閒置滿 N→**恰 N 分登出＋「請重新登入」toast** 後靜默重導（SC-004）。
- **CDP-3 rotation/reuse**：正常換發連續不斷線；舊 refresh 重放（超 grace/更早世代）→family 撤、8888；
  **並發雙分頁換發不誤踢**（grace、SC-001）。
- **CDP-4 logout**：登出→伺服器端撤銷→被擷取舊 refresh 換發失敗 `8888`；**access 過期後登出仍能撤**
  （拍板7、SC-003）。

## 預期出口（對照 spec Success Criteria）

- SC-001~009 全滿足；SC-008 CDP-1~4 全過（各附 CDP 可觀察證據）。
- 靜態閘全綠：cargo test --workspace／entity_access_lint／fork-delta-lint／契約覆蓋閘／wire-schema 重抽 diff 空。
- 憲法 §I.7 島 A/B/C/D 不變式於實作保持；base-web 改動限 ★LOGOUT-UX-WIRING 兩用途、帶 `原行:`。
