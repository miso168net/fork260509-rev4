<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=f615aa2｜rust-api=3d8074e

## constitution
- 版本：1.2.0

## 帳面統計
- ADR：32（accepted 31、superseded 1）
- BACKLOG 待辦：52（next：B-060）
- LESSONS：108 筆（next：L-109）
- events：5 筆（feature_close 4、misc 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-05｜feature_close｜004-system-settings｜系統設定縱切收刀（波1首功能刀＋base-web 首刀）：後端首建 auth seam（enforce_mw JWT-decode＋require_policy DB-fresh roles→casbin enforce super-only→5003；JWT sign/登入延 auth 刀）＋facade/op-log（mutate_in_txn 同 txn、KV String-PK entity_id=None、setting_key 進 payload）＋型別驗證 registry（ADR 0026 per-key 範圍＋canonical 正規化＋未知型 fail-loud）＋兩端點（getSystemSettings/updateSystemSetting、SettingItem camelCase settingType、審計欄不上 wire）＋entity_access_lint 首建＋per-route 契約裁判（SettingItem vs 快照 Api.SystemManage.SystemSetting）＋demo 清償（B-056、覆蓋閘 3↔3）；前端 base-web 首刀＝ADAPT typings/WRAPPER service/★MODAL-WIRING(e) 設定頁（前綴分區＋型別驅動控件＋恆 refetch＋密碼策略固定排序＋i18n label＋info-icon tooltip）＋★I18N-WIRING(i)~(iv)（攔截器 msg→$t backend 命名空間、全 zh-TW primary locale 525 鍵繁化、三語選單簡/繁/English）；jsonwebtoken 10.4.0(rust_crypto)/metrics 0.24.6 拍板釘版；cargo test --workspace 74 綠、quickstart A~H 全綠、SC-001~007/FR-001~016/US1-3 全滿足、holistic review SHIP-READY；fork-delta 原行紀律機器化（tools/fork-delta-lint 掛 pre-commit）
- 2026-07-05｜feature_close｜003-wire-foundation｜統一信封＋13碼守門＋契約機器化骨架落地：Res/PageRes 信封（欄序 data→code→msg、code 字串、錯誤 data:null 不省略、id string-id 序列化＋number 2^53 守衛 unsigned_abs 防 i64::MIN 溢位）＋13 碼 AppError（9 可發變體＋4 保留碼構造層不可構造、code/key/http 三映射單一來源、不帶 From<DbErr> 防回歸）＋router 註冊表資料化（ROUTES 單一來源、/health 遷入例外、fallback→4040）＋demo 端點（暫時物、對外 /api/demo-wire）＋三類守門（13碼 table-driven／保留碼列舉完整性／時間欄 offset）＋tools/wire-schema 抽取管線（typescript-json-schema@0.67.4 釘版 npx、35 defs/26 Api.*、原子替換、確定性 byte 一致）＋契約裁判（jsonschema 0.46.9 draft-07、通用形 PageRes vs Api.Common.PaginatingQueryRecord、clone def 為 root 注入 definitions 解 $ref:T）＋雙向覆蓋閘（ROUTES↔case registry、缺 case/殭屍 case 皆紅指名）；cargo test --workspace 32 綠、quickstart A~F 全綠、波0出口六組整波重跑（down -v 從零 429 crate 重編＋migrate 閘＋11+casbin+seaql 表＋seed 244＋三閘綠）全綠、base-web 零 fork 改動、rev3 同機並行零擾動
- 2026-07-04｜feature_close｜002-schema-baseline｜基線 schema＋seed 落地：m001 建表（11 業務表＋casbin 委派＋治理欄）＋m002 定稿 seed 244 列（argon2 執行期雜湊、冪等可逆、掛 001 migrate 閘門）＋tools/schema-gate 三閘（gate1 結構零漂移 vs 凍結 fixtures 含 --live-rev3 交叉、gate2 欄序/seed 定稿落實、audit 審計欄四變體守門＋archetype-map）＋entity crate 13 檔（欄序照定稿）＋docs-sync refresh 快照管線（reference/schema＋accounts 轉真＝B-003/B-004 落地）；quickstart A~G 全綠、SC-001~008 全過、001 SC-007 迴歸 18.86s、base-web 零 fork 改動、rev3 零擾動；閘 1 抓出定稿產物漏摺 2 索引並補齊（L-102）

## reference 對賬
- reference/routes：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
