# 波 0 規劃 — infra 刀群定案（wave-0-plan）

日期：2026-07-03｜性質：**波規劃**（三把刀的共同上游輸入、不佔刀號——刀號留給各刀自己的
brainstorm 檔）｜方法：superpowers:brainstorming 互動問答（一題一拍）。
決策正文：ADR 0020（波 0 組成與切法）＋ADR 0021（schema 基線 user 定稿制、supersedes 0014）。

## 0. 拍板紀錄

| # | 題目 | 拍定 |
|---|---|---|
| 1 | 波 0 刀組成 | **三把**：compose stack＋schema 基線＋wire 地基（rev3 前例 001~003 同標波 0；活書 §8 守門表點名 wire 地基刀） |
| 2 | compose 刀服務範圍 | **五服務＋migrate gate**（照 rev3 001 前例）；obs 四件套不進、隨觀測刀 |
| 3 | 部署資產來源 | **rev3 裁剪帶入**——yaml／conf／sh 屬「設定」非「實碼」、不觸憲法 §I.5 防回歸條款（先例：docker-compose.example.yml 搬入） |
| 4 | wire 刀範圍 | **後端縱深版**——只動 rust-api；前端 $t 接線、locale 外包層隨首功能刀 |
| 5 | seed 基線定義 | **定稿即基線**——m002 灌 user 過目定稿後的 seed；閘改「實庫＝定稿清單」（三案比較：定稿即基線／鏡像＋調整分離／豁免清單） |
| 6 | 欄位順序 | **user 逐表親排**（002 刀 brainstorm 內建欄序過目工作坊；原「慣例規則推導」廢止） |

另兩項既有輸入：port 全照 ADR 0019；映像釘數字版走「查 rev3 現值＋官方最新、給 user 選」程序。

## 1. 刀清單、順序與命名

三把刀嚴格串行（後刀依賴前刀交付物）；編號從 001 起佔 `specs/<NNN>` 序列，
system-settings（ADR 0008 第一把**功能**刀）順推 004。

| # | 刀名 | 一句話 | 上游依賴 | rev3 對照 |
|---|---|---|---|---|
| 001 | `001-compose-stack` | master compose 五服務＋migrate gate＋rust-api 最小 scaffold＋secrets | —（第一把） | `001-infra-deploy` |
| 002 | `002-schema-baseline` | rev3 終態語意 squash＋欄序 user 親排＋seed 過目定稿＋兩道閘 | 001 的 migrate 容器與 DB | `002-rev2-schema-baseline` |
| 003 | `003-wire-foundation` | 後端信封＋13 碼單一來源＋三類守門＋契約機器化骨架 | 001 的 rust-api scaffold | `003-envelope`（範圍縮後端縱深） |

每把刀照 CLAUDE.md §2 完整工作流：各自 brainstorm（輕量——本規劃已拍大半）→ SDD 5 步 →
TDD → 收刀簿記三步。

## 2. 各刀範圍與驗收

### 2.1 刀 001-compose-stack：一鍵開發環境

**交付物**：

1. `docker-compose.yml`（base 層）——六 service：front-nginx／base-web／rust-api／postgres／
   redis-stack／migrate（one-shot 閘門：DB healthy 後跑 migration、成功退出後 API 才准起）；
   named volumes、secrets 宣告、network。base 層不放 host port（rev3 坑：ports list append、
   dev/prod 疊加衝突）。
2. `docker-compose.dev.yml`——host port 照 ADR 0019（42079 api／42080 入口／42081 前端／
   42443 TLS／45432 DB／46379 redis、全綁 127.0.0.1）；熱重載（cargo-watch、vite dev）與
   healthcheck 在此層。
3. `deploy/nginx/`（nginx.conf＋conf.d/dev.conf＋_locations.inc）——`/`→base-web、`/api`→rust-api；
   容器內 listen 80/443（rev3 的 31080/31443 改掉）。
4. `deploy/generate-secrets.sh`＋`preflight-secrets.sh`＋`secrets/*.txt.example`＋README——六機密
   （postgres_password／redis_password／jwt_secret／refresh_token_secret／database_url／redis_url）；
   實值 gitignore；rust-api 讀取走 `_FILE` 機制。
5. `deploy/generate-dev-cert.sh`——42443 自簽憑證；私鑰不入版控。
6. `deploy/Dockerfile.rust-api`（dev target：toolchain＋cargo-watch）＋entrypoint＋.dockerignore；
   base-web 不建 Dockerfile（dev 用裸 node 映像釘數字版＋pnpm dev；prod build 歸部署刀）。
7. **rust-api 最小 scaffold**（全新手寫、不拷 rev3）：cargo workspace（server＋migration 兩 crate）
   ＋rust-toolchain.toml；server＝axum＋config（_FILE 優先）＋`GET /health` plain text（憲法例外）；
   migration＝sea-orm-migration 空殼、`migration up` 可跑（零支、成功退出）＝migrate gate 載體；
   至少一支冒煙測試打通容器內 `cargo test`（serial）。
8. **B-002 ports extractor**——docs-sync 讀 compose 生成 `reference/ports` 全量表、stub 轉真＋
   該來源 L2 對賬啟用。
9. 收刀簿記：pin bump、活書 §7＋§2 更新、BACKLOG 刪 B-002、events、NOTES。

**驗收**：①secrets＋憑證生成 → `up -d --wait` 退出碼 0、六服務 healthy（migrate Exited(0)）；
②六連通點：`curl :42080/health`→ok、`curl -k :42443/health`→ok、`curl :42079/health`→ok、
`curl :42081`→HTML、`psql -p 45432`→SELECT 1、`redis-cli -p 46379 PING`→PONG；
③docker inspect 證 migrate 時序（DB healthy 後啟動、Exit 0 後 API 才 healthy）；
④down／up 冪等；⑤reference/ports 與 compose 一致、lint 全綠。

**留刀內 brainstorm**：rust／axum／sea-orm 版本釘定值（查 rev3＋官方最新給 user 選）、
workspace 細部佈局、healthcheck 參數、要不要另給單服務獨立 compose 檔（rev3 有）。

### 2.2 刀 002-schema-baseline：基線 schema＋seed（user 定稿制）

接地事實（2026-07-03 自 rev3 活庫 psql 撈）：rev3 終態 13 表＝11 業務表（sys_user、sys_role、
sys_user_role、sys_menu、system_settings、sys_token、sys_login_attempt、sys_operation_log、
sys_access_log、sys_ip_rule、sys_casbin_policy_archive）＋casbin_rule（ADR 0015 adapter 委派建、
不入 squash；其授權政策 seed 隨 casbin 進場刀）＋seaql_migrations（框架自管）。
rev3 九支 migration（m001~m009）淨效果 → rev4 壓成 m001 建表＋m002 seed（短編號照 ADR 0013）。

**交付物**：

1. **欄序過目工作坊**（brainstorm 內建、先於寫碼）——逐表攤開 rev3 欄位清單
   （欄名／型別／nullable／default），user 重排每張表欄序；定案錄 `specs/002-*/data-model.md`
   （凍結史料）。活書欄序節記「欄序＝基線刀 user 定稿、後續加欄一律 append」。
2. **seed 全量過目**（同為 brainstorm 內建）——自 rev3 活庫撈 seed 淨效果逐表逐列全量列示
   （帳號、選單樹、角色、user-role 綁定、settings／password_policy），附連動關係
   （menu id↔casbin 引用↔父子鏈↔user_role）；user 調整內容（id、排序欄等；調 id 時連動列
   同步改並確認）。定稿清單＝凍結設計檔；執行期生成值以規則表示（如 argon2id(123456)）。
3. `m001`——建齊 11 業務表：結構語意忠實 rev3、欄序照 user 排定；複合索引／複合主鍵內部
   欄序屬語意、原樣保留。
4. `m002`——灌 user 定稿 seed（非 rev3 鏡像）。
5. `entity/` crate——sea-orm entity 檔。
6. **兩道閘**：閘 1＝結構零漂移（vs rev3 參考庫、information_schema 按欄名配對、忽略表內欄序、
   複合索引欄序嚴格；只管結構不管 seed）；閘 2＝定稿落實（實庫欄序＝data-model.md、
   實庫 seed 列集合＝定稿清單）。
7. **B-003 schema extractor＋B-004 accounts extractor**——reference/schema、reference/accounts
   stub 轉真＋L2 啟用。
8. **審計欄建表守門**——活書 §8「隨 schema 基線刀建立」義務清掉。
9. ADR 0021（本規劃已立）承載此刀的制度基礎；收刀簿記同慣例（BACKLOG 刪 B-003／B-004）。

**驗收**：空庫 `migration up` → 11 表＋定稿 seed 就位；閘 1 綠＋閘 2 綠；extractor 一致；
容器內 cargo test 全綠；清庫重跑冪等。

**留刀內 brainstorm**：欄序過目的呈現形式（逐表問答 vs 可編輯清單檔）、rev3 參考庫重放來源
（9 支 migration 重放 vs 活庫 schema dump）、entity 檔生成 vs 手寫。

### 2.3 刀 003-wire-foundation：統一信封＋錯誤碼守門（後端縱深）

實作依據（憲法 §I.3 凍結）：13 碼＝0000/1000/2222/3333/7777/7778/8888/8889/9998/9999/4040/
5003/5000；HTTP 例外僅 4040→404、5003→403、內部錯誤 5000 一律 HTTP 200 信封；保留碼
7778/8889/9998/9999 後端永不發出；業務驗證一律 2222；信封例外僅 /health 與 /metrics；
分頁形 {current,size,total,records}；msg 載穩定 i18n key。

**交付物**：

1. 統一信封型別＋serializer——handler 回傳一律 `{code,msg,data}`；/health、/metrics 例外。
2. 13 碼常量表單一來源——一個模組定義全部碼＋HTTP 映射；發碼只准 import 它。
3. 錯誤型→業務碼映射收單一來源（rev3 教訓：散在各 handler 會漂）。
4. msg＝i18n key 落地——錯誤 msg 載 key 不載人話；翻譯歸前端（隨首功能刀接線）。
5. **三類守門測試**（活書 §8 義務）：13 碼逐碼 table-driven contract test（HTTP status＋信封形狀）；
   保留碼永不發出斷言；時間欄必 ISO-8601 帶 offset 斷言。
6. **契約機器化骨架**（憲法明文隨此刀落地）：base-web typings 抽 JSON Schema 當裁判
   （唯讀、不動官方檔）＋coverage gate（每條 route 必有 contract case）。
7. demo 驗證端點（回帶時間欄假資料；功能刀進場後可刪）；收刀簿記：活書 §8 兩行守門改已就位、
   §4 敘事對齊、events、NOTES。

**驗收**：容器內 cargo test 全綠（三類守門在內）；curl demo 端點驗信封實形＋msg 是 key；
curl /health 仍 plain text；lint 全綠。

**留刀內 brainstorm**：信封／錯誤型放哪（server 內 vs 獨立 crate）、JSON Schema 裁判載體、
coverage gate 落點（cargo test vs docs-sync lint）。

**三刀共通**（CLAUDE.md §2 既有紀律）：rust 全程容器內 serial；review agent 只讀；
絕不在 finishing 前 push/merge；波 0 全程 base-web 零 fork 改動。

## 3. 波 0 出口條件（六組檢查表）

收 003 刀時整波重跑（單刀驗收各自綠 ≠ 整波綠——後刀可能弄壞前刀鏈路）；全綠才宣告波 0 收口。

**第 1 組：一鍵環境活著（從零重來）**——`down -v` 歸零 → secrets 生成 → `up -d --wait` 退出碼 0、
五常駐服務 healthy＋migrate Exited(0)；六連通點（42080/42443/42079/42081/45432/46379）全過；
down→up 冪等且更快。

**第 2 組：基線資料就位**——歸零啟動後 `\dt`＝11 業務表＋seaql_migrations（casbin_rule 不存在
屬正常）；逐表抽查 seed＝user 定稿；閘 1 結構零漂移綠；閘 2 定稿落實綠。

**第 3 組：wire 地基就位**——容器內 cargo test 全綠（三類守門）；demo 端點信封＋offset 正確、
msg 是 key；/health 仍 plain text。

**第 4 組：文件面**——reference/ports、schema、accounts 轉真（STATE 對賬區剩 routes、screens
兩行 stub）；活書 §8 三處「隨◯◯刀建立」清掉、§7 有 dev stack 敘事、§5 起頭、§2 更新；
BACKLOG 刪 B-002/B-003/B-004；events 三筆 feature_close；NOTES 指波 1；ADR 0021 生效
（0014 已回填 superseded）。

**第 5 組：紀律面**——git log 三個 merge --no-ff、feature branch 保留；pin 與 worktree 一致；
base-web 停在 9c6f223e 零新 commit（可驗不變式）；lint 全程綠。

**第 6 組：波 1 就緒判定**——system-settings 刀（ADR 0008；輸入 B-023/B-051）brainstorm
可直接開場、不需先蓋任何基建；反例檢查：若還缺基建＝波 0 出口漏項、回頭補。

## 4. 產出物與簿記（本規劃自身）

- 本檔＋ADR 0020／0021＋NOTES 更新＝一筆 commit（lint 綠放行）；push 待 user 同意。
- BACKLOG 不動；活書不動（波 0 未發生、活書只寫現在式）；specs/ 待各刀 /speckit-specify
  手動起手才出現。

## 5. 與各刀 brainstorm 的關係

本檔是三把刀的上游輸入；各刀開工時各有輕量 brainstorm（`docs/brainstorms/001-compose-stack.md`
等、編號對應刀號），引用本檔、只補「留刀內」項。specify 一律手動起手（CLAUDE.md §2）。
