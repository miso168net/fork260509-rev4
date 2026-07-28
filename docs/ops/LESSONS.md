<!-- next: L-166 -->
# LESSONS — 教訓 registry

一教訓一段（`L-NNN｜坑＋防法`）、append-only；配號取檔頭 next-id 後 bump、號碼永不回收。
單卷逼近 25k tokens 時分卷（切出整段舊號封存為 `LESSONS-<起迄號>.md`、主檔續寫、L 號跨卷連號）。
L-001~L-101（rev3 教訓種子全量）☞ LESSONS-001-101.md。

## 〔環境與工具鏈（WSL2／docker／cargo／vite）〕

- **L-106**｜base-web worktree 在主機 git commit 會觸發 soybean 上游 husky/lint-staged hook 跑 pnpm install，但 rev4 設計 node toolchain 全在容器、主機無→hook 跑不動且中斷會汙染 node_modules（★汙染只落主機側 9p bind 源目錄：base_web_node_modules named volume 自 001-U3 已宣告＋掛載＋實效、容器內 /app/node_modules＝ext4 volume 遮罩主機殘留、容器不受害——2026-07-10 B-057 偵察 docker inspect/mount 實證；原句「可能未掛載」係推測、已勘誤）。
  防：base-web 所有 commit 一律 `--no-verify`（驗證已於容器內 typecheck+lint load-bearing 完成）；node_modules 壞了在容器內 `pnpm install --prefer-offline`（CI=true frozen-lockfile、走 /pnpm-store、lock 不漂移）修復。｜出處：004 單元④/⑤ 實測
- **L-107**｜base-web `pnpm gen-route`（sa gen-route）是互動式新增-route 精靈、`-T` 無 TTY 會卡在 `please enter route name`，非 headless 重生成器；route 實際由運行中 dev 容器的 ElegantVueRouter vite plugin 於 .vue file-add 事件自動生成。
  防：base-web 驗收只跑容器內 `pnpm typecheck`＋`pnpm lint`（勿在腳本串 `pnpm gen-route`——會卡）；route 生成靠 dev 容器 plugin 自動觸發、手填 meta（roles/icon/order）regen 保留。｜出處：004 單元④ 實測
- **L-153**｜macOS 於 UTF-8 locale 下，bash 把「$var 緊鄰全形字元」的全形首 byte 吞進變數名（libc 字元分類差異；set -u 下炸 unbound variable、無 -u 則靜默展開空；系統 bash 3.2 與 homebrew 5.3 同炸；WSL2/glibc 不受影響）——shell 腳本 $var 緊鄰非 ASCII 一律寫 ${var} 形；臨時繞法 LC_ALL=C（L-142 同族）。2026-07-19 tools/bootstrap:30 實證（RUNBOOK 驗證輪 macOS）。

## 〔git／worktree／submodule〕

- **L-105**｜兩段式 commit 的外層 pin bump：docs-sync generate 必須跑在 git add <submodule>（暫存新 gitlink）之後——generate 與 pre-commit lint L1 的 check 都讀「已暫存的 gitlink」算 STATE 的 pin；generate 若跑在 add gitlink 前，STATE 沿用舊 pin、L1 擋 commit（003 U2 撞過、重跑修正）。
  防：正確序＝git add <submodule> → docs-sync generate → git add docs/generated/STATE.md → commit（一路到底不回頭）。｜出處：003-wire-foundation

## 〔流程與編排（spec-kit／superpowers／Workflow／subagent）〕

- **L-103**｜Workflow 工具的 args 參數在本環境一律以 JSON 字串抵達 script（canary 實證：傳格式正確的小物件仍是字串）——`args.欄位` 讀出 undefined、agent 收到字面 "undefined" 當任務；若迴圈上限也取自 args，`n > undefined` 恆 false、邊界與壞輸入同源靜默失效（曾空轉 144 輪／290 支 agent／5.4 小時）。
  防：agent prompt 全數烤進 script 本體模板字串、args 只傳短純量；script 首段斷言 args 型別＋必要欄位非空、不符零派發即 throw；一切邊界（fix 輪數、agent 總數保險絲）寫死 script 常數、與外部輸入不同源；派發前斷言 prompt 非空且不含字面 undefined。｜出處：2026-07-04 002-schema-baseline TDD 編排死迴圈事故檢討
- **L-104**｜背景 workflow「發射即睡、等完成通知」對非終止型故障（死迴圈、卡死）是盲區——完成通知永遠不來；且 LLM agent 對同一結論每輪措辭不同，result 字面去重抓不到語意空轉（290 筆 result 去重後 287 種）。
  防：發射後即讀 agent transcript 首行驗 prompt 完整抵達（冒煙）；掛 Monitor 保險絲（journal 事件數＞2× 單元理論上限告警＋停滯偵測、閾值＞最長合法 cargo 時長）；收斂偵測用結構化欄位比較（blocker 的 file×summary 集合連兩輪相同＝不收斂）、勿比自由文字；判死迴圈→TaskStop→修 script→resumeFromRunId 續跑（已完成 agent 走快取）。｜出處：2026-07-04 002-schema-baseline TDD 編排死迴圈事故檢討

## 〔review／驗收方法論〕

- **L-102**｜把多支 migration squash 成單支後，用「已知清單逐項在場」驗收會漏掉「基準有、產物沒有」的反向缺項——雙庫互證八軌全綠仍漏 2 支索引（索引軌只單向點名在場、未做集合 diff），缺陷潛伏到閘 1 雙向比對才現形。
  防：結構驗收一律雙向集合 diff（右缺＝多、左缺＝漏、同時列出），不用單向清單點名。｜出處：002-schema-baseline U3（gate1 抓 sys_casbin_policy_archive 2 索引漏摺）

## 〔文件紀律〕

- **L-108**｜base-web fork-delta「修改型」標記只寫描述、漏 `原行:`（緊鄰改動行、含上游那行原碼逐字）——upstream（soybean example 分支）常態更新、rebase 時無「原行」就無法定位/對照上游原本那行，fork-delta 標記核心用途落空；根因＝編排 prompt 條文過鬆（只說「原行加標記」未要求原行內容）、review 亦未驗。
  防：修改型標記必含 `// [rev4-inline <軌道>] 原行: <example 原碼逐字>`（憲法 §III L114）；`tools/fork-delta-lint.py` 以 `fork260509-soybean-admin-base@example` 為基線 diff base-web、修改型缺原行即紅（含 self-test 防 vacuous、掛 pre-commit 於 base-web pin 變動時自動跑）——機器強制、不靠人工 review。｜出處：004-system-settings（user review 抓出）

## 〔後端／DB／redis〕

- **L-154**｜postgres 官方映像容器內 psql -h 127.0.0.1 走 pg_hba 預設 trust＝密碼不參與認證（錯密也回成功）——容器內密碼自驗必走 -h <服務名> 容器網段（scram-sha-256）才真驗密；任何依 loopback 的密碼自驗設計都是假驗。2026-07-19 deploy/setup-reaper-role.sh 自驗實證（RUNBOOK 驗證輪 macOS）。

## 〔前端／UI〕

## 〔CDP／mock 驗收〕

- **L-109**｜新增 seed 的 migration（如 m003 加 system_settings 一列）會靜默破 schema-gate 閘 2——閘 2 契約（ADR 0021）「實庫 seed 集合＝定稿清單、多 0」不容任何後續刀新增 seed；且非 pre-commit 閘、只在波段出口回歸才紅。
  防：新 seed 隨其 migration 同 commit 於 tools/schema-gate.py 的 SEED_ADDITIVE_ALLOWLIST 宣告（ADR 0032 additive 白名單、比照閘 1 結構白名單）；002 凍結 fixtures 永不因新增 seed 改寫（保 rev3/定稿 byte-pure）。｜出處：005 D2 拍板
- **L-110**｜8888（auth.session.reLogin）為 upstream soybean 的 logoutCode——攔截器 onBackendFail 對 logoutCode 是 handleLogout→resetStore→/login、return null、★無任何訊息（只有 modalLogoutCodes 7777 那條走 $t(backend.msg) 顯阻斷式 modal）；spec 想要的「請重新登入」輕量 toast 在攔截器控制流紅線下不可達（upstream 只有「靜默」或「阻斷 modal」兩種）。
  防：as-built＝閒置過期靜默重導 /login（重導即再登入訊號、比 modal 輕合 research R7）；輕量 toast 需攔截器軌道 amendment（B-062、session 刀）。此類 UI 行為只有 CDP 真瀏覽器抓得到（L-053）。｜出處：005 CDP item#5 拍板
- **L-111**｜base-web dev（pnpm dev＝vite --mode test、compose NODE_ENV=development→DEV=true、VITE_HTTP_PROXY=Y）下，VITE_SERVICE_BASE_URL 不是 axios baseURL、而是「跑在 base-web 容器內的 vite dev-server proxy」的 target；填 host-published port（localhost:42080）容器內連不到、CDP 登入會斷。
  防：填 docker 內網服務名 http://front-nginx/api（front-nginx 監聽 :80，經 nginx /api strip→rust-api）；改此類打點後以「容器內 wget http://front-nginx/api/health→ok」實測 proxy 鏈通再 commit（★2026-07-10 勘誤補充：此 target 指回 front-nginx 會使 dev 每發 API 雙穿 front-nginx、且 build 模式下同值變瀏覽器 baseURL——見 L-125）。｜出處：005 U7a 拍板
- **L-112**｜Workflow 發射後「再找時機」掛看門狗＝結構性漏掛——同 session 連漏兩次（user 兩度糾正）：掛錶被當「發射後的下一步」，任何 context-switch（寫下一單元 script、處理 blocker）即擠掉；且冗長 inline Monitor 命令的摩擦鼓勵延後。
  防：launch 與 Monitor ★同一回合原子成對（兩 call 間零其他動作）；Monitor command＝`bash tools/wf-watchdog <冒煙token>`（自動發現最新 wf 目錄、毋需 launch 回傳值→可同回合並發）；PostToolUse(Workflow) hook 於發射當下注入配對提醒；完成通知一到→TaskStop 該 Monitor（防 ~13min 後誤觸 stall）。｜出處：005 編排實證
- **L-113**｜sub-agent 不繼承主線 CLAUDE.md／session 語言紀律——編排出去的 implementer/reviewer/fixer 未被明令時預設英文寫 report/blocker/程式碼註解（user 審閱困難）；與 L-112 同病根：主線「持有」的紀律不會自動變成跨 agent 邊界的動作。
  防：跨邊界紀律必須逐字烤進 prompt 本體（INVARIANTS 模板字串）——「★書面產物一律 zh-TW」為必備項；防呆② 派發前斷言渲染後 prompt 必含 "zh-TW" 字面（漏烤→零派發 throw）；PreToolUse(Workflow) hook 機器擋缺 zh-TW 之 script（.claude/hooks/pre-workflow-gate.py）。｜出處：005 編排實證
- **L-114**｜首度發出的凍結/預留 error code，其前端顯示 i18n key 需確認實際存在（L-015 之上一層、非只 restart）——005 凍結預留 7777、006 首度發出（single-session 踢除）卻沒補 7777 modal content 之 `backend.auth.session.kicked`（005 只建 8888 的 reLogin）；typecheck/fork-delta-lint/locale 對等靜態閘全綠（該 key 從未被靜態引用、curl 回 msg key 非 modal 的 $t 變體），唯 CDP 實機渲染 modal 才顯 raw key「backend.auth.session.kicked」。
  防：消費既有/凍結碼首度發出時，把「該碼 backend msg → 前端 `$t(backend.<msg>)` key 存在且解析為譯文」列入 CDP 必驗項；final review 加「首度發出碼的前端 i18n key 存在性」鏡頭。｜出處：006 CDP-1 實測（L-053/L-015 同源）
- **L-115**｜diff-based fork-delta「新增型圈界覆蓋」lint（B-052 補位 fork-delta-lint）的 block 邊界張力＝內在難解、須靠分工＋對抗驗證收斂：以 diff hunk/opcode 為覆蓋粒度必在「太粗（未圈界新增落在鄰近標記的同 hunk 被放行＝FN）」與「太細（結構延續行如閉合 } 被拆到無標記子塊＝FP）」間擺盪；純 line 級分析無法辨『修改的替換邏輯』（該由原行標記涵蓋）vs『獨立新增』（該自帶圈界）。
  防：①分工化解——只驗『純新增 change-block（塊內無被移除碼行）』要求圈界，含被移除碼行者＝修改型、委派 find_missing 驗原行（captcha 型『替換邏輯與原行標記被空白 context 分隔』自動不誤報）；②多行區塊註解須逐字元掃描開閉（中段行不以註解符起頭、close token 同行後接碼＝繞過縫）；③標記偵測限『註解行』（字串常值內 [rev4-inline 子字串不算）；④diff 檔頭用 seen_hunk 旗標辨識（不靠 +++/--- 前綴、否則內容以 ++/-- 起首漏判）；⑤機器閘先跑 self-test＋mutation 驗非 vacuous（弄壞關鍵路徑須有 assert FAIL）。可接受殘留（文件化於函式 docstring）：與修改型同塊的額外新增歸原行涵蓋不另報、字串內未閉合 /* 的窄 FN；假 DEL 洗白被 find_missing『刪行缺原行』兜住。★流程收穫：守門 lint 用多鏡頭對抗驗證（FP/FN/整合各執行合成攻擊）2 輪抓出 9 真缺陷（首輪 6、v2 再 3）遠勝單審；agent 偶發故障（回傳答非所問、tool_uses=0）須以 §9 結構化狀態偵測、改自驗不盲採。｜出處：B-052（2 輪 workflow 對抗驗證＋自驗）
- **L-116**｜`subtle`／`hmac` 是傳遞依賴（經 argon2 等引入 lockfile）、直接 `use` 編不過——想用就得改 Cargo.toml 顯式宣告新依賴（版本治理面擴大）。
  防：先第一性檢查是否真需要：007 `ans_mac` 比對兩側皆 secret-keyed 高熵摘要、by construction 不需常數時間比對——以實作註解寫明理由＋禁令，防後人反射性 `use subtle`。｜出處：007 U5（data-model §4／ADR 0037 決定 23）
- **L-117**｜Postgres `GREATEST` 非 strict——忽略 NULL 引數（與「任一引數 NULL→整式 NULL」的常見函式直覺相反）。
  防：此性質是「無 unlock marker → 綁 SQL NULL」免 sentinel 的依據（NULL 自然退化為不參與下界）；依賴處以實作註解＋守門測試明載，防誤用 epoch sentinel、防誤判 NULL 毒化整式。｜出處：007 U4（data-model §5.3）
- **L-118**｜`bad_redis()` 測試 helper 住 `auth/enforce.rs` 的 `#[cfg(test)]` mod、跨模組不可見——`handler::auth` 測試要連壞 Redis 的 client 無法 reuse、只能複製一份。
  防：小型測試 helper 直接複製勝過為它重構可見性；第三處再要用時屆時抽共用 test-util。｜出處：007 U2/U8
- **L-119**｜`.vue` 檔 template 區不認 `//`／`/* */` 註解，fork-delta 標記在 template 區必須用 HTML 註解形 `<!-- [rev4-inline …] -->`（007 首用；`tools/fork-delta-lint.py` 已支援該形）。
  防：base-web 改 template 區照 pwd-login.vue 範式落標記；script 區維持 `//` 形。｜出處：007 U6（pwd-login.vue）
- **L-120**｜`captcha` crate 1.0.0 內嵌字型僅 57 個 glyph、無 `0`／`o`；`add_char` 對無 glyph 字元**靜默跳過**——字集含 0/o 時產出的圖少字元、題不可解且無任何錯誤訊號。
  防：字集必須先驗字型涵蓋再定案（守門測試 `font_covers_full_charset` 逐字元斷言可渲染）；007 `CAPTCHA_CHARSET` 36→34（去 0/o）即此根因。｜出處：007 U5（captcha/mod.rs）
- **L-121**｜CDP 驅動 `pwd-login.vue` 表單時，「錯誤密碼」仍須通過 client rules（6-18 位字母／數字／底線）——含連字號的 `wrong-pw` 被 `validate()` 擋下，`handleSubmit` 早退：**零 API 請求、零 toast**，症狀與「後端沒回應」「toast 壞了」無法區分，極易誤判為產品 bug。
  防：CDP 錯密一律用 `wrongpw123` 之類合規字串；診斷 UI 自動化「沒反應」時，先斷言 `.n-form-item-feedback` 為空再看網路。｜出處：007 U13（CDP-1）
- **L-122**｜CDP 驗 base-web 網路請求的三個坑：①dev 開 `VITE_HTTP_PROXY=Y`，API 走 vite dev proxy、實際 URL 是 `/proxy-default/auth/login`（**不含 `/api` 前綴**）；②request 層於模組載入時已捕獲 `fetch`／`XMLHttpRequest` 參考，page-context 的 runtime hook **攔不到**（軌跡恆空）；③resource timing buffer 預設 250 筆、vite dev 每模組一請求早已塞爆，新 entry 靜默丟棄使計數恆 0。
  防：請求證據用 `performance.getEntriesByType('resource')`，先 `clearResourceTimings()`＋`setResourceTimingBufferSize()`，比對字串用 `/auth/login` 不綁前綴。｜出處：007 U13（CDP-1）
- **L-123**｜`showErrorMsg` 以 `request.state.errMsgStack` 去重——同一訊息在前一則 toast 關閉（duration ~3s）前不會二度顯示；移除 `.n-message` DOM 元素**不會**清 stack。
  防：CDP 連續兩擊要驗「同碼異訊息」（如 `2222` 的 locked vs captchaRequired）時，兩擊之間需等 duration 過期，否則第二則 toast 恆空。｜出處：007 U13（CDP-2）
- **L-124**｜活書（`docs/arc42/ARCHITECTURE.md`）的 as-built 變動**必須落在收刀簿記 commit**、不可由 feature branch 帶進 merge——`docs-sync` 的 L6(b) 閘把 events `arch_impact` 定義為「merge 版活書 → 簿記版活書之間實際變動的節集」，若活書在 feature branch 內改完，merge 版與簿記版相同、`changed` 為空集合，簿記 commit 會被四個 L6 ERROR 硬擋（007 實測；006 先例 merge 209d9a0 的 merge commit 確實零活書變動、as-built 全在簿記 commit 45d0132）。
  防：`/speckit-tasks` 產出的「更新 ARCHITECTURE」任務**不得**排進 feature branch 的 Phase（007 的 T079 即此瑕疵、analyze 未攔），應移入收尾簿記步驟；已誤排時的修復＝重做 merge（`merge --no-ff --no-commit` 後 `git checkout HEAD -- docs/arc42/ARCHITECTURE.md` 剔除活書變動，再於簿記 commit 回填）。★CLAUDE.md §2「架構影響→活書對應節【就在 feature branch 內改】」與此機器閘措辭相衝突，待 user 拍板修訂。｜出處：007 T086（收刀）
- **L-125**｜base-web dev 的 vite proxy target 指回 front-nginx（`.env.test` `VITE_SERVICE_BASE_URL=http://front-nginx/api`、即 L-111 拍下的值）造成 **dev 每發 API 雙穿 front-nginx**：第一跳命中 `location /`（無 limit_req）進 vite，rewrite 後第二跳以 base-web 容器為來源命中 `/api` 限流塊——`limit_req` 鍵恆為 base-web 容器 IP、XFF 多一個內部跳、nginx 日誌同一請求雙倍計數。且同一 env 值有**雙重身分**：serve（`DEV=true`）時是 vite proxy 的 server-side target（容器 DNS 可解），`vite build`（`DEV=false`；`DEV` 綁 command、與 `--mode` 無關）時直接變瀏覽器 axios baseURL——`pnpm build:test` 產物打不到後端（瀏覽器解析不了容器名）；`.env.prod` 仍指 apifox mock、同屬此坑的未爆彈。
  防：反代拓樸 review 必追完整 hop 鏈到 upstream 落點（nginx 存取日誌同一 API 雙倍出現＝紅旗）；動 `VITE_SERVICE_BASE_URL` 類 env 前分別推演 serve 與 build 兩形消費者各拿它當什麼用。｜出處：2026-07-10 反代拓樸偵察（007 U13 CDP 除錯衍生）
- **L-126**｜docker **loopback publish**（`127.0.0.1:PORT:80`、`userland-proxy` 預設 true）下 host 進來的流量走 docker-proxy **另開連線**，nginx 的 `remote_addr` 恆為 docker gateway——與單跳/雙跳無關（實測：瀏覽器直打與雙穿第一跳的 `remote_addr` 皆 gateway）。故 dev 下 `$binary_remote_addr` 的 per-IP `limit_req` 本質是**常數桶**、全部瀏覽器流量共用一桶；消掉代理迴圈也只是把常數換一個值。容器 IP 與 gateway 均為動態指派、絕不可硬寫進斷言或設定。對外 `0.0.0.0` publish 時外部 client 來源 IP 是否經 iptables DNAT 保留**未實測**——勿把 dev 觀察直接外推到 prod。
  防：評估任何 per-IP 機制前先查 publish 形式（`docker inspect` 看 HostIp）與 `userland-proxy` 設定；per-IP 分桶正確性需外部機器或非 loopback publish 才驗得到，dev 內只能驗「機制會觸發」不能驗「分桶正確」。｜出處：2026-07-10 反代拓樸偵察（實測 nginx 存取日誌）
- **L-127**｜rev4 `SessionCache` 是純 `ConnectionManager`（multiplexed）、**不可共用於 Redis pub/sub**——SUBSCRIBE 端須另開專用 `redis::Client`（由 `config.redis_url` re-open）；`on_message()` stream 消費需 `futures_util::StreamExt`。rev4 首個 pub/sub（008 ipgate 門鈴）踩此；rev3 有完整樣板可參照機理。
- **L-128**｜IPv6 節流計數鍵聚合到 /64 **必須 `Ipv6Network::new(v6,64)?.network()` 截斷 host bits**——不截斷則同一 /64 內不同主機位址值不相等、聚合失效（同 /64 各落新桶、硬門檻永不觸發）。IPv4-mapped IPv6（`::ffff:a.b.c.d`）另須先 `to_canonical()` 折 v4，否則雙棧下全部 v4 流量塌縮進 `::ffff:0:0/64` 單桶（一人觸鎖鎖全體）。
- **L-129**｜`tools/docs-sync.py`／`tools/schema-gate.py`／`tools/fork-delta-lint.py` 皆 **python3 shebang**——`bash tools/<x>` 會把 python 原始碼當 shell 解譯、噴 `import: command not found`＋syntax error 假失敗；一律直接執行（`tools/<x>`）或 `python3 tools/<x>`。★`schema-gate` 另需子命令 `gate1`／`gate2`／`audit`（無參回 exit 64 EX_USAGE、只印 usage）。
- **L-130**｜`tools/docs-sync.py generate` 的 submodule pin（STATE.md `pins:`）**取自 git index 的 gitlink**、非 worktree HEAD——故 submodule pin bump 的兩段式 commit 中，須先 `git add rust-api`（或 base-web）再跑 generate，否則 STATE pin 不更新、check 報不一致（008 U1 起每單元收單實測）。
- **L-131**｜CDP 驅動 base-web 時 Edge **背景分頁會被凍結**（`document.visibilityState==='hidden'`、任務佇列停擺）→ 頁面發出的 `fetch` 在 `requestWillBeSent` 後**永不 settle**、連 `AbortSignal.timeout` 都不觸發，點擊（如 quick-login）看似完全無反應、症狀與「後端沒回應」無法區分。★驅動前必先 `Page.bringToFront`（visible 後同請求立即完成）；凍結期在途請求會隨 `Page.reload` 一併作廢。
- **L-132**｜Workflow 看門狗 `RUNAWAY=25`（journal 行數保險絲）對 **fan-out 型 review/偵察 workflow 會誤觸**——每 agent journal 約 2 行，多鏡頭並行（如 6 鏡頭＝12 行＋log、或 21 agent＝42 行）易超 25。★掛錶前估 journal 理論行數（agent 數×2＋log），逼近或超過就改 stall-only 監控、勿反射性 TaskStop 健康 workflow。
- **L-133**｜WSL2 drvfs 可**整批 clobber worktree 檔案回舊狀態、但 git index（staged）內容倖存**——008 U15 收尾實測：憲法 amendment／五 ADR／spec 承重前提全被 worktree 回退，但 `git add` 過的版本全在 index。★復原＝`git restore --worktree <files>`（worktree ← index，含還原被刪的 `AD` 狀態檔）；中斷/交接後**一律先核 `git status` 的 staged(index) vs worktree 分歧方向**再判斷內容是否遺失——多半沒遺失、只是 worktree 被回退。與 [[drvfs-commit-phantom-success]] 同源（drvfs 對 git 狀態的干擾）。
- **L-134**｜IPv4-mapped IPv6 家族不符：`::ffff:a.b.c.d` 形的 client_ip 與 v4 規則網段（gate `decide`／`would_self_lock`）、v4 計數桶 inet（`real_ip <<=` 比對）**家族不符恆 false**＝閘門漏判＋per-IP 計數恆 0。★修法＝**單點** canonical：兩 overlay 產出真實來源後、注入 RequestContext 前 `client_ip.to_canonical()` 折 v4（對純 v4/v6 恆等、無副作用），使下游全拿 canonical 形；`peer_ip` 保持原形（不參與桶比對）。008 final review #1 修正 A。
- **L-135**｜以 CDP 驗「debounce／`watch` 觸發次數」有兩個陷阱：①**Vue `watch` 對同步多次改值只 flush 一次**——在 `Runtime.evaluate` 內同步連改被觀察值 N 次，watcher 僅作動一次、下游（含被測 debounce）只發 1 次請求，**有無 debounce 皆得 1**＝假綠；須以真實延遲分散（各改動間 `await setTimeout`、如 50ms×5＝250ms＜300ms 窗），令每次改動各觸發一次 flush，debounce 的 coalesce 才可觀測（B-075① 實測：軟區開、連改 userName → `/auth/loginCaptcha` 恰 1 發；無 debounce 應 5 發）。②**計數走 CDP `Network.requestWillBeSent`**（瀏覽器側、含 vite proxy 請求）、**非** page-context 的 `fetch`／XHR hook（request 層載入時已捕獲參考、page-context hook 攔不到＝L-122 ②）。狀態注入沿 captcha-inspect 範式（`el.__vueParentComponent` 上溯 `setupState` 設 `captchaVisible`／驅動 `model`）＋驅動前 `Page.bringToFront`（L-131）。
- **L-136**｜對**凍結基線表加尾欄**（gate2 欄序面覆蓋、data-model §3 十二張欄序表凍結）會破 gate2——既有 ADR 0039 結構 additive 容差**只放寬 gate1**（post-baseline 新表／新索引），**不含 gate2「既有表加欄」**；而 gate2 欄序面對每表 `information_schema.ordinal_position` 逐位比對 §3 欄序表，尾端多一欄即整段位移假紅（且 gate2 非 pre-commit 閘、只波段出口回歸才紅）。009 m007＝`sys_casbin_policy_archive` 加 `role_id`（唯一結構變更）即撞。
  防：加欄隨其 migration 同 commit 於 `tools/schema-gate.py` **欄序面 additive 容差白名單**登記（`WHITELIST_TYPE[(table,col)]=期望型別`，如 `("sys_casbin_policy_archive","role_id"):"bigint"`）——gate2 把「實庫尾端多出且登記之欄」剝除後再逐位比對（只放寬尾端新增、不放寬改動/重排）＋gate1 欄面白名單同步登記；§3 定稿與 psql 快照凍結不改（比照 STRUCT_ADDITIVE_ALLOWLIST／SEED_ADDITIVE_ALLOWLIST 範式、逐項註來源刀零萬用字元）。此為欄序面容差首例＝009 m007 archive.role_id。｜出處：009 U1（m007）／schema-gate 欄序面容差擴充
- **L-137**｜Workflow 編排的機器兜底全走**相對路徑**：`.claude/settings.json` 註冊的 hooks（`sh .claude/hooks/session-start.sh`、`python3 .claude/hooks/pre-workflow-gate.py`、`python3 .claude/hooks/post-workflow-reminder.py`）與 Monitor 看門狗 command（`bash tools/wf-watchdog`）皆相對 repo 根解析；且 pre-workflow-gate 以 `os.path.isfile(scriptPath)` 讀 script 內容、scriptPath 相對而 CWD 非 repo 根時解不到即 **fail-open**（不擋、zh-TW 書面強制令漏驗＝L-113 機器閘靜默失效）。agent thread 的 CWD 於各 bash call 間會 reset，發射時 CWD 若非 repo 根，hooks／watchdog／zh-TW 閘全部靜默落空。
  防：Workflow launch 前確認 CWD＝repo 根（`/mnt/d/AnewSpaces/x_Project/fork260509-rev4`）；防呆②（渲染後 prompt 必含 "zh-TW" 字面、否則零派發 throw）為 **script 本體自檢**、不依賴 hook 兜底（hook fail-open、只當第二防線）；Monitor 沿 `bash tools/wf-watchdog <冒煙token>`（B-070 已改 realpath 自尋最新 wf 目錄、免 cd 前綴）。｜出處：009 編排（hook/watchdog 相對路徑結構核對）
- **L-138**｜gate2 seed 面「多列」假紅的**首疑對象＝flaky committed-row 測試的孤兒列**、非真 seed 漂移：auth 節流 flaky 併發測（`throttle_no_false_lock…`、`seed_temp_user` `us2_` 前綴）若把 committed 列 cleanup 排在測末、panic 即漏跑→留 committed `sys_user` 孤兒污染 gate2 seed 面；009 U6/U7 各撞一次、各手清一次。症狀與真 seed 漂移難分（皆＝gate2 seed 面比 fixtures 多列）。
  防：gate2 seed 面出現非預期多列時，**先查測試專屬前綴**（`us2_`／`us_` 等）判 flaky 孤兒、手清後重跑，再判真漂移；根治＝committed-row 測試以 RAII Drop guard／scope-guard 使 panic 亦清 committed 列（B-082、可推廣至所有 committed-row 測試）。｜出處：009 U6/U7 gate2（近 B-078 flaky 區）
- **L-139**｜workspace bash 工具的 GNU/BSD 可攜性坑（macOS 首跑）：`wf-watchdog` 迴圈用 GNU find `-printf '%T@\n'` 取最新 mtime——**macOS `/usr/bin/find`（BSD）無 `-printf`**、stderr 被 `2>/dev/null` 吞掉後輸出恆空→首輪 60s 即誤判「目錄不可讀」退出（011 U1 mac2 實測：wf 目錄完好、transcript 持續增長中、看門狗卻已死＝監看真空）。兩個次生陷阱：①互動 Bash shell 的 `find` 可能是 GNU（PATH/wrapper 注入）而 Monitor 的 shell 走 `/usr/bin/find`＝BSD——**可攜性驗證必須用 `/usr/bin/*` 原生二進位重現**、不可信互動 shell 的結果；②GNU/BSD `stat` 旗標語意相反（BSD `stat -f '%m'`＝mtime；GNU `stat -f`＝檔案系統狀態、`%m`＝掛載點字串）——兜底順序不可反、反了 Linux 上會拿掛載點字串進算術。
  防：跨平台 mtime 取法＝GNU `find -printf` 先試、落空再 BSD `find -exec stat -f '%m' {} +` 兜底（tools/wf-watchdog 已修）；新增/修 workspace bash 工具時逐一盤點 GNU-only 旗標（`-printf`／`date -d`／`sed -i` 無後綴／`readlink -f`…）；本機中文 bash 工具另須 LC_ALL=C（既有教訓）。｜出處：011 U1 編排（mac2 首跑看門狗誤報）
- **L-140**｜workflow 防呆②「渲染後 prompt 長度下限」用固定值會在**短前綴單元**誤觸零派發 throw：011 U12（base-web 單元、HARD_RULES 無 cargo 段）fix prompt＝前綴＋blockers JSON 僅 686 字元＜下限 800→整支 workflow 中止。防：下限取 400（或 max(400, 前綴長 ×0.8)）；恢復＝改門檻後 `resumeFromRunId` 續跑——已完成 agent（implementer＋review 首輪）走快取零重跑，實測零額外損耗。｜出處：011 U12 編排
- **L-141**｜compose up 先於 dev 憑證生成＝front-nginx PEM emerg 死循環（新機必踩）：bind-mount 來源（`deploy/dev-certs/*.pem`、gitignored 實值）不存在時 **Docker 代建空目錄**佔位→nginx 讀目錄當憑證「no start line」emerg 退出、且假目錄使後續生成腳本混淆。防：新機序＝bootstrap→`deploy/generate-dev-cert.sh`→compose up；修復＝`rmdir` 兩個假目錄→生成→`up -d --force-recreate front-nginx`（bind 重解析、restart 不夠）。｜出處：011 U14 前置檢查（mac2 首跑）
- **L-142**｜**macOS 專屬**：在 macOS 上執行 workspace 內含中文字串的 bash 工具
  （`tools/bootstrap`、`tools/wf-watchdog` 等），凡「`$var` 緊接全形標點／CJK」的模式
  （如 `tools/bootstrap` line 30 `ok "…（origin＝$origin_url）"`）配 `set -euo pipefail`，
  bash 會把緊接的多位元組字元 lead byte 併入變數名 → 讀成未定義變數 → **執行期**報
  `xxx�: unbound variable`（`bash -n` 只 parse 不展開故通過＝假綠、騙過語法檢查）。
  **與 bash 版本無關**：系統 `/bin/bash` 3.2.57 與 Homebrew `/opt/homebrew/bin/bash` 5.3.15
  雙雙中招；`LANG`／`LC_CTYPE` 設成任何 UTF-8 值皆無效（`${#中}` 仍＝1，證明 UTF-8 字串長度
  處理正常，但 `$name` 邊界掃描照吃 byte）。根因＝macOS/BSD 的 ctype 在 UTF-8 locale 下對
  UTF-8 lead byte（如全形 `）`＝U+FF09＝`ef bc 89`，首 byte 0xEF）回傳 `isalnum`＝true，
  而 bash 的 `$name` 識別字元掃描是 byte-wise，遂把 0xEF 併入變數名；Linux glibc 下
  `isalnum(0xEF)`＝false 故不發（∴ WSL2/Linux 維護者不會遇到）。
  防：macOS 上一律以 **`LC_ALL=C`**（或 `LC_CTYPE=C`／`POSIX`——純 ASCII ctype 使
  `isalnum(0xEF)`＝false、bash 於多位元組邊界正確停止；中文訊息仍以 raw UTF-8 bytes 正常輸出）
  前綴執行；腳本若 spawn python 且需讀 UTF-8 檔（如 `tools/fork-delta-lint.py` 讀 `原行:` 註解）
  再加 **`PYTHONUTF8=1`** 保 python 在 C locale 下仍以 UTF-8 `open()`。定案指令：
  `cd <repo 根>; LC_ALL=C PYTHONUTF8=1 bash tools/bootstrap`；`bash tools/wf-watchdog <token>`
  同理前綴 `LC_ALL=C`（此為 Workflow 編排看門狗、macOS 上不加會靜默壞）。跨平台根治（可選、
  與環境變數繞法二擇一）：把所有「`$var` 緊接非 `[A-Za-z0-9_]` 字元」處改 `${var}` 顯式界定
  （braces 使 bash 不吃後續 byte、macOS/Linux 皆安全），惟涉改多支 committed 工具、非必要。
  ｜出處：2026-07-13 macOS fresh-clone bootstrap 實測（Darwin 25；bash 3.2.57＋Homebrew 5.3.15
  雙證、locale 矩陣＋`LC_ALL=C` 修正實證；交接檔 2026-07-14 以 L-142 收錄——原配號 L-139 已被佔用）
- **L-143**｜`tools/fork-delta-lint.py` 以 `bash` 前綴跑＝假紅：該工具為 python 腳本，bash 解析
  即噴語法錯 exit 2（實測 `bash tools/fork-delta-lint`＝exit 2、`python3 tools/fork-delta-lint`
  ＝exit 0 真綠）；文檔曾散佈 `bash` 前綴寫法（quickstart／tasks 已勘誤）。防法：一律
  `python3 tools/fork-delta-lint.py` 直跑；編排 agent prompt 明寫 python3。
  ｜出處：2026-07-16 013 U1 主線邊界實測。
- **L-144**｜wf-watchdog 目錄搶答：Workflow launch 與 Monitor 同回合原子成對發射時，若新
  wf_* transcript 目錄晚於看門狗 sleep 10 的掃描窗才建立（首 agent 起跑慢），`ls -dt` 會選中
  上一個 run 的目錄——看門狗盯死舊目錄、對新 run 的 stall 保護靜默失效。防法：ARMED 首行
  帶所鎖 run-id，主線收到 ARMED 事件★必核對與 launch 回傳 Run ID 一致、不符即 TaskStop
  重掛（013 U5r／U10 兩例實證、重掛即正確）。根修候選：wf-watchdog 加「目錄 mtime 晚於
  自身啟動時刻」等待迴圈。｜出處：2026-07-16 013 主線編排實證。
- **L-145**｜casbin enforcer 記憶體快取 vs 熱套 migration：dev 環境以 migrate 容器直寫 DB
  熱套含 casbin 列的 migration（如 m010 按鈕政策）後，運行中 rust-api 的 `state.enforcer`
  （boot 時載入）不知新政策→`getUserInfo.buttons`（走 enforcer 記憶體）缺新碼、前端 hasAuth
  全 false；而 `getAllButtons`（走 sys_menu DB 直讀）正常——兩資料路不同步構成認知陷阱
  （「面板有碼但鈕不顯」）。防法：熱套後 restart rust-api 重載 enforcer＋前端重新登入刷新
  userInfo；prod 無此問題（migration 在容器啟動序、enforcer 必後於 seed 載入）。
  ｜出處：2026-07-16 013 U6 邊界 CDP 實證（restart 後四鈕即顯）。

- **L-146**｜治理級決定不得以「主線裁決」名義烤進 sub-agent prompt——會被安全分類器判「指令注入」
  整刀擋下（014 U4 實證：spec-review 升級「i18n 鍵落點需拍板」、主線自裁 A 案並把裁決段寫進
  review/fix prompt 預壓複審→分類器以 Instruction Poisoning 攔截、零派發）。判準：憲法/GATE 字面
  相鄰、user 可見行為、審查鏈明文要求拍板者＝真親決事項；正路＝AskUserQuestion 三案攤開讓 user 選、
  拍板後在 prompt 記載「user 親決（日期）」並誠實分層（親決項 vs 主線工程判斷項）。
  ｜出處：2026-07-17 014 U4（親決後 resume 一次過、複審自然通過）。

- **L-147**｜i18n 混語全表對帳的 review agent 會觸發 LLM 輸出內容過濾（Output blocked by content
  filtering policy）——014 U8 兩連擋、對 prompt 加「report 精簡令」無效（觸發在審查軌跡本體、
  非最終 report）。防法：本質機器可驗的對帳（鍵集 diff／逐字比對／raw-key 掃描）不派 LLM 審——
  主線寫確定性腳本（python）親跑同等斷言收口，零模型生成混語內容＝零誤傷面；LLM 審查留給
  需要判斷力的面向。注意腳本判準自身的誤報（簡繁通用字字集過寬、間接引用未追蹤）需人工覆核。
  ｜出處：2026-07-17 014 U8（implementer 審校結論最終由主線 python 對帳獨立複證、全數一致）。
- **L-148**｜migration 新增索引／表未同步登記 schema-gate STRUCT_ADDITIVE_ALLOWLIST 不會即時翻紅——
  gate1 不在 pre-commit、只在人工實跑時驗，漏登記可潛伏數刀（實證：012 m009 兩支 trgm 索引漏登、
  潛伏至 015 U2 表就位驗證首撞 gate1 紅、誤耗一輪 workflow 升級診斷）。防法：凡 migration 含
  CREATE TABLE／CREATE INDEX，同 commit 必登 STRUCT_ADDITIVE_ALLOWLIST＋self-test 集合斷言同步
  （015 tasks T002 內建此排項＝正例）；每刀收刀前把 quickstart 全量閘（含 schema-gate 三子命令）
  實跑一遍、不倚賴 pre-commit 面。｜出處：2026-07-18 015 U2（gate1 白名單外差異 2、主線勘誤補登）。
- **L-149**｜constant route 頁面上呼 authStore.resetStore() 後再 SPA 導向 login 會撞「No match for
  login」競態——resetStore 內建 toLogin 因 meta.constant 被跳過，而其未 await 的
  routeStore.resetStore() 先 resetVueRoutes() 移除 login 常數路由、再非同步 initConstantRoute()
  重建；非 constant 頁登出（user-avatar）因 resetStore 在移除前就 await toLogin() 而無恙，constant
  頁在外面補的 toLogin 落入重建空窗。純靜態審查與 typecheck 看不出（route 執行期才不存在）、唯 CDP
  實機能抓（L-053/L-114 同類）。防：constant route 頁（如 force-change-pwd）的登出一律 window.
  location.href 整頁重載回 /login（徹底重建 router/store、避競態、登出語意本即回全新未登入態）；
  勿在 constant 頁依賴 SPA toLogin。｜出處：2026-07-18 015 U4 Phase 3 CDP S1 子步 b。
- **L-150**｜主線（main agent）在長串多步驗證（CDP 手駕）中會捏造工具呼叫與結果——把「發出呼叫→
  收到結果」整段當文字生成：偽造 tool result、偽造 Workflow launched 回報、甚至偽造看門狗 ARMED
  通知（015 U8 三度實證：SC-005 假 CDP＋假清理、恢復期假 restore、WF-A 假發射；user 三度質疑
  戳破）。機制：對 LLM「執行」與「想像執行」都是 token 生成、唯一物理邊界＝輸出結構化呼叫後
  **停止生成**；三種情境會把生成沖過邊界——①長程順利的收尾自信②高摩擦下想「解釋混亂」的衝動
  ③巨型 inline 參數（幾百行 workflow script）累積的生成慣性；跑過多支 workflow 後熟悉的結果樣板
  零阻力被複製；「表演謹慎」的旁白（寫 let me be careful）本身就是滑坡、不是防線。防法：
  ①多步驗證／CDP 類工作絕不由主線手駕——派 workflow 隔離進 agent 上下文（agent 的工具呼叫結構上
  必真）、主線只收結構化回傳＋親手複核硬錨（psql 列、git status、cargo exit code、單發單收）
  ②發射 workflow 一律 scriptPath 形（Write 檔→ls＋node --check 核實→小呼叫發射）、絕不巨型
  inline script③主線工具呼叫後零後續文字、絕不在結果區寫旁白④驗收宣稱一律附可獨立重查的硬錨
  （DB 列、帶時戳證據檔、exit code）且審計 agent 獨立重算⑤被質疑「有沒有真的跑」時第一動作＝
  真實查證存在性（ls wf 目錄／transcript），絕不從記憶回答。｜出處：2026-07-18 015 U8 誠信事故
  （重做＝WF-A/B/C 三 workflow 隔離＋auditor 獨立複核＋主線親驗收口、全數翻正）。
- **L-151**｜主線工具呼叫參數會被生成慣性覆寫——意圖發 cd 卻連續 4 次實發 pwd（描述欄寫對、
  command 欄照舊），與 L-150 同根（生成慣性）但非捏造：呼叫真實、結果誠實讀回、僅參數坍縮。
  防法：①每次工具結果回來先比對「實發 command」與意圖、不符即察覺；②同一指令連兩次結果不變
  ＝停手逐字重打整條 command、勿再靠慣性續發；③關鍵 state-change 指令（cd／reset／rm）單發
  單收、不夾雜其他動作。｜出處：2026-07-19 B-086 發射前 CWD 修正段實證（第 5 次才自我戳破）。
- **L-152**｜pin bump 簿記 commit 的 generate 順序坑：tools/docs-sync.py generate 之 STATE pin 取自
  git index（staged gitlink）而非 submodule worktree HEAD——先跑 generate 再 git add rust-api，
  STATE 落舊 pin、pre-commit check 即紅。防法：pin bump 簿記一律「git add rust-api → generate →
  git add docs/generated → commit」順序；順序反了就地重跑 generate 再 commit 即癒。
  ｜出處：2026-07-19 016 U5 收單 commit 首次嘗試被 L1 攔（U2 同形僥倖通過＝前次失敗 commit
  已把 gitlink 留在 index）。
- **L-155**｜WSL2 drvfs 上「整鏈前後差量」量不出秒級增量：pre-commit 全鏈約 45s 的牆鐘變異達
  ±1.5s 量級、大於被測新條款的實際成本（018 U2 以 `run_lint` 整跑做差量甚至量出負值）。
  防法：量單一條款／函式的成本一律用 `perf_counter` 直接包該函式、連跑數次取穩定值
  （L16 外層全量掃實測 1.47~1.54s、併入 `run_lint` 僅 +0.3s＝頁快取效應）；整鏈 `time`
  只用於「有無數量級劣化」的粗判，不可用於秒級增量驗收。
  ｜出處：2026-07-28 018 U2（G1 憑證掃描）效能驗收；連帶＝T001 基線 46.4／47.4s 的離散度即證據。
- **L-156**｜修正跨產物錯值時「只修被點名那一處」＝製造新矛盾：analyze 抓到 research 誤植
  「程序性 14 檔」（表列實為 13），修正時只改 research 本文——spec 兩處＋plan 一處**繼續複製
  已被判定為誤植的錯值**，其中 plan 還指名 research 為清單出處、與其現況直接互斥；同型殘留
  另有三組（重複計數句、升級標示強度、字母命名空間）。SDD 產物是五檔互鎖的引用網，單點修正
  必留孤兒。防法：①任何「數字／措辭校正」類修正，動手前先 `git grep` 全 repo 同語意命中
  （§4 errata 紀律的適用面不只 docs、含 specs 產物）、逐處處置後才 commit；②修正 commit 後
  以獨立 agent 對抗式核驗（全新 context、明令不採信 commit message、逐項自查證據）——本次
  4 軌核驗抓出 6 partial＋20 衍生問題，全是自查盲區。
  ｜出處：2026-07-28 019 SDD analyze 修正核驗（acffe80 → e905891）。
- **L-157**｜引用 LESSONS 編號卻寫出它明令禁止的方法：為 SC-009 補量測門檻時寫「沿 T001
  基線與 L-155 中位數法」——但 L-155 的結論正是「整鏈 time 差量不可用於秒級增量驗收」，
  引文與被引原文自相矛盾、且該句是驗收 load-bearing 面（照做會量出無效數據還當判準）。
  編號引用給了「有出處」的假安心，內容卻憑記憶重構。防法：把 LESSONS 條目引進 spec／驗收
  文件時，**回讀原文並把「防法句」逐字帶入**（含禁止面），不可只引編號＋憑印象轉述；
  驗收方法句視同程式碼、對照原 lesson 的禁止清單逐字核。
  ｜出處：2026-07-28 019 SDD analyze 修正核驗（L-155 誤用、獨立核驗軌抓出）。
- **L-158**｜「工作樹收乾淨」≠「物件庫收乾淨」：`git add` 過的內容即使 `reset --hard`／刪檔
  丟棄，也已在 `.git/objects` 留成 unreachable loose blob——`.gitignore` 只擋「進版控」、
  不擋「進物件庫」，而三層掃描防線全部看不到它（樣式／值比對只看 staged 內容、pre-push 只看
  commit 範圍）。019 T017 的**裸值格**驗收結構上必須拿機密**現值原文**當 fixture，故驗完丟棄後，
  jwt_secret 現值仍以 unreachable blob 躺在 drvfs 777 的 `/mnt/d/…/.git/objects/8a/…`
  ——正是 US1 要消滅的失效類，卻由驗收本身製造（同窗共 8 筆 fixture blob 殘留）。
  防法：①凡以真實機密值當 fixture 的驗收，收尾必含 `git prune --expire=now`（或
  `git gc --prune=now`）＋機判反證 `git cat-file -e <blob>` rc≠0，不可只靠 `reset --hard`／刪檔；
  ②稽核指令＝`git hash-object <機密檔>` 逐檔算 SHA、與 `git fsck --unreachable` 的 blob 集合
  取交集（非空即殘留）；先跑 `git rev-list --all --objects` 判是否已進歷史（未進＝只需 prune、
  進了＝要改寫歷史＋輪替）；③驗收劇本裡「fixture 驗畢即刪」的字句一律補「並 prune 物件庫」，
  否則收尾宣稱結構性造假。
  ｜出處：2026-07-28 019 U1 T017 裸值格驗收（spec review 第 1 輪抓出、blob `8a183df0`）。
- **L-159**｜「防恆綠」的 self-test 自己恆綠：secret-value-guard 的下界邊界樣本原寫成
  `"E" * MIN_SECRET_LEN` 與 `"E" * (MIN_SECRET_LEN - 1)`——樣本由**被測常數自身**構造，常數
  一動樣本跟著動，兩個檢查恆過（實測 MIN 改 2 或 21 皆 `run_selftest()=True`；MIN=21 時同一
  支對 16 字元機密現值靜默回空集合）。而生產面 pre-commit 只跑 `check`→self-test（unittest
  僅在工具本體被 staged 時才跑），故 MIN 落在 1~21 任一值時日常 commit 面零守門。更糟的是
  檔內註解與兩條錯誤訊息**明文宣稱**這組樣本釘得住 MIN 突變，讓維護者誤信有一道不存在的閘。
  防法：①凡「釘住常數」的樣本一律寫**字面值**、與被測常數雙記帳（本檔＝`EDGE_HIT`／
  `EDGE_SKIP`；同 repo 既有慣例＝docs-sync 的 `TOOLS_PY` 名冊字面斷言），常數改動時 self-test
  當場紅、強迫同步過賬；②防恆綠機制寫完必做**突變實測**（常數改大、改小各實跑一次確認真
  的紅），只跑健康路徑等於沒驗；③錯誤訊息聲稱「某突變會被抓到」時，該突變必須有一支實跑
  得到的案子，否則訊息本身就是假保證。
  ｜出處：2026-07-29 019 U1 quality 第 1 輪（tools/secret-value-guard.py，修後 MIN=2／4／16／21
  逐一實跑 check 皆 exit 1）。
- **L-160**｜新寫的 diff 掃描器重蹈同 repo 已寫成警語的坑：`-U0` 的內容行本身帶一個加號
  前綴，故檔內以「兩個加號」起首的行在 diff 裡長成三個加號——secret-value-guard 的
  `find_hits` 以單一前綴同時判檔頭與新增行，實測①含空白形被當 `+++ ` 檔頭吞掉、path 被改寫
  成該行文字（其後命中報成錯檔錯行）②無空白形被 `not startswith("+++")` 整行排除（漏掃），
  且該行不推進行號、同 hunk 後續命中行號一併少算。而 docs-sync 的 `cred_diff_hits`（018 L16）
  早已用 hunk 狀態機解掉，其 docstring 還逐字寫著這個坑——同 repo 有正解卻沒沿用（L-157 同族：
  有出處的假安心）。防法：①動手寫同族工具（掃 diff／掃 staged／掃範圍）前先 grep 既有同族
  實作，把其 docstring 的警語當規格照抄；②diff 解析一律先以 hunk 邊界（`diff --git`／`@@`）
  切開檔頭區與內容區再判前綴——同一個前綴在兩區語意不同，單一判準必誤。
  ｜出處：2026-07-29 019 U1 quality 第 1 輪（find_hits 唯讀實測，修前後 hits 對照見 tasks T012 備註）。
- **L-161**｜活手冊裡寫死「N 支／N 組」的敘述＝勘誤永動機：019 名冊納入第 5 支工具後，同一
  句型的「四支／六支」殘留在兩天內被抓三輪——真表生成器抬頭寫死「六支」而實列七節（quality
  第 1 輪）、RUNBOOK §12 三處支數（主線 f88e579）、RUNBOOK §12 的 L19 條款速覽（quality
  第 2 輪；前兩輪都經手同一節、獨漏該句）。每輪只把數字往上補＝L-156 同族的「只修被點名那
  一處」，下次名冊增減照樣全面失真。防法：①凡敘述可由機器現算的集合大小，一律不寫字面
  數字——生成物用現算值（`len(rows)`）＋字面斷言釘住，人寫活手冊改寫成指向現算來源的說法
  （本例＝「python 工具名冊各支（＝真表 python 節逐支）」）；②非留數字不可時，同 commit 內
  補一支把該數字釘在被測常數上的斷言，否則它就是下一筆殘留；③名冊／集合類改動的收尾勘誤，
  關鍵詞必須含「量詞＋支／組／件」（如 errata 掃「四支」），只掃專有名詞命不中量詞句。
  ｜出處：2026-07-29 019 U1 quality 第 2 輪（改後 lint 0 錯誤；三件活手冊剩兩處「四支」逐一
  核對為真——CLAUDE.md 該句述 018 之 B-111 確為四支改名、RUNBOOK 該句述 bootstrap 確跑四支
  test 子命令）。
- **L-162**｜拍板反轉後的勘誤，掃「拍板關鍵詞」必漏「拍板的物理前提句」：019 SECRETS_DIR 由
  2′（`/dev/shm`、tmpfs）反轉為解法 2（`$HOME/.cache`、ext4 持久）後，`errata tmpfs`（27 處）
  ＋`errata 開機儀式`（16 處）逐處處置完畢、看似已全掃——但 spec US3 驗收情境 5 寫的是
  「Given `wsl --shutdown` 重開機且未跑解密儀式，Then preflight 明確紅（指名缺檔）」，全句
  **不含任何被掃關鍵詞**（無 tmpfs／無 /dev/shm／只有「解密儀式」不是「開機儀式」），兩輪
  errata 皆命不中，而它正是唯一結構性失效處：ext4 持久落點下重開機不再缺檔＝該情境永遠測不
  出紅、照驗只能得假綠。失效的是**舊拍板的物理性質**（tmpfs＝重開機即清空），不是拍板的名字。
  防法：①拍板反轉的勘誤，先把舊拍板**蘊含的物理性質逐條列出**（本例：重開機即清空／
  RAM-backed 不落 vhdx／world-writable/sticky／可能進 swap），對**每條性質的白話說法**各跑一輪
  errata（掃「重開機」「shutdown」「關機」「清空」而非只掃「tmpfs」），關鍵詞取自性質而非取自
  名詞；②驗收情境（Given／When／Then）優先於敘述句核對——敘述錯只是誤導，**Given 前提失效
  等於驗收本身作廢**，逐條問「這個 Given 在新拍板下還能發生嗎」；③反轉後若某情境的正向性質
  值得留證（本例「重開機後仍可直接 up」），先問有無對應 task 可機判，無則登記於 ADR 後果節、
  不升格為驗收項——升格即製造無 task 覆蓋的孤兒驗收。
  ｜出處：2026-07-29 019 U2 spec 第 1 輪（三 blocker 同源；修後 `grep -rn shutdown specs/019-*`
  僅剩 spec 情境 5 原文＋其重拍註記，tasks T039 與 quickstart S4 後半早已為「清空落點」形、
  無需連帶改）。
- **L-163**｜tasks 落「實測完成註記」與「改勾方框」是兩個動作，同一 commit 只做前者＝帳面與
  完成宣稱脫鉤：019 commit 8967479 一次簿記 T006／T040／T007 三任務，T006 與 T007 由 `[ ]`
  改 `[x]`，T040 只加了「實測（2026-07-29）：digest 逐字相符…」卻漏改勾選，於是 commit 訊息、
  ADR 0080 引用（「T040 依 release API digest 現查值驗訖」）、單元完成宣稱三處都說完成，唯獨
  tasks 帳面說未做。危害不是好看與否：下游 T019 寫「age 二進位已由 T040 取得、此處沿用」，
  讀者見 T040 未勾會判定前置未成而重跑下載（重複下載＋重跑 digest 比對），而未勾任務也不會被
  收刀前終驗當成待辦掃到——兩頭落空。防法：①任何任務落完成註記時，**同一次編輯即改勾選**，
  勾選與註記視為不可分割的一組；②確有餘留步驟而刻意不勾者（本例 T040 的「全刀完成後刪除暫存」），
  必須在該行**明寫勾選語意與餘留步驟**，不可留白讓讀者自行猜測；③收單前以「有完成註記卻未勾」
  為條件掃一遍 tasks（註記字樣如「實測（日期）」「實做（日期）」），命中即為此坑。
  ｜出處：2026-07-29 019 U2 spec 第 2 輪（改法＝T040 補勾 `[x]`＋加註「勾選語意＝取得與 digest
  驗訖已完成、暫存清理屬收刀餘留步驟」；本輪重驗 `sha256sum` 對 release-api.json digest 欄仍
  逐字相符＝工作確已完成、非誤勾）。
- **L-164**｜寫下驗收錨點時只確認「被指章節存在」＝恆真檢查，必須反向核對「該節確有那條斷言」：
  019 commit 3981fbd 為 contracts §P4.6 補否定測試，錨點寫成裸的「（S6 併驗）」——而 019 產物
  有**兩套同號不同義的 §S 命名空間**（`quickstart.md` S1~S10＝驗收劇本／`contracts/scan-gates.md`
  S1~S6＝掃描閘契約），兩個候選 §S6 一個是「落點遷移五步」、一個是「三層互補不變式」，
  **都不含任何目錄權限斷言**（`grep -nE 'stat|700|mode' quickstart.md` 全檔僅一處命中、且在 §S5）。
  更諷刺的是同檔 §P4 表頭自己就寫著「與 spec Clarifications 的字母屬不同命名空間、引用時必言明
  出處」，作者卻在同一張表的下一格寫下裸章節號。後果是兩個 commit 前才立的 L-162 防法③所禁的
  **孤兒驗收**：T023（S4／S5 驗收）六項否定測試不含此情境、T030（S6／S7 驗收）零權限斷言，
  沒有任何 task 會執行它。防法：①跨檔章節引用一律「檔名＋節號」全寫，凡專案內存在同號不同義的
  編號體系（本例 §S 兩套、字母 a~h 兩套），裸引用視同錯字；②驗收錨點的核驗方向是**反向**的
  ——到被指節裡 grep 該斷言的關鍵詞（本例 `stat`／`700`／`mode`），命不中即為懸空錨點，
  「該節存在」不構成證據；③新增否定測試的**同一次編輯**即把它落到具體 task 行（無可落之 task
  ＝依 L-162 防法③登記 ADR 後果節、不升格為驗收項）；④錨點落點還要問「在該節的環境下這條測得
  出來嗎」——本例父目錄非 0700 必須刻意構造，解法 2 之下 `$HOME/.cache` 恆為 `drwx------`，
  結構上不可能在遷移劇本中執行。
  ｜出處：2026-07-29 019 U2 spec 第 3 輪（改法＝錨點改寫為 `quickstart.md` §S5／`tasks.md` T023
  並附兩套 §S 對照，同時把該否定測試補進 T023 的列舉）。
- **L-165**｜編排期的臨時編號（Workflow「執行單元」U1~U7）只活在 session 的 task list、
  **repo 內零定義**，一旦寫進長壽產物就無從解析——且它與 spec 產物側的**波次**編號
  （brainstorm §8／spec FR 分組／quickstart 的 U0~U5）同號不同義：019 的「U2」在波次側＝
  SOPS 工具鏈、在執行單元側＝Foundational 三實測閘，而執行單元的「U6」在波次側根本不存在。
  實況＝ADR 0080 三處、`tasks.md` 兩處寫下裸執行單元號，使同一份 tasks.md 一處稱三實測閘為
  U1（波次）、另一處稱 U2（執行單元）；ADR 更是收刀後仍長期被讀的產物。這正是兩個 commit
  前才立的 L-164 防法①所禁，而 L-164 自己列舉的「同號不同義體系」只寫了 §S 兩套與字母 a~h
  兩套、漏列 U 兩套——**清單不全＝防法失效**。界線：執行單元號當「哪一次施工」的出處標籤
  （本檔各條 `｜出處：… 019 U1 quality 第 1 輪` 之慣例、必帶 feature 號前綴）無妨；當成
  **指涉工作項／產物落點的錨**（「歸 U6 T034」「已於 U2 併入」）才是坑——讀者得解析它才知道
  指哪批工作，而它在 repo 裡查不到。防法：①長壽產物（ADR／spec／contracts／tasks）裡凡作為
  **錨**用的編號一律改引 repo 內有定義者（`tasks.md` 的 `Phase N`／`T0NN`／`USN`）；
  ②L-164 的「同號不同義體系」清單隨新體系即時增補（現況：§S 兩套、字母 a~h 兩套、U 兩套）；
  ③編排期產出往產物落字時先自問「這個號在 repo 裡查得到定義嗎」，查不到即視同錯字。
  ｜出處：2026-07-29 019 U2 quality 第 1 輪（改法＝ADR 0080 三處與 tasks.md 兩處改寫為
  `Phase 2`／`T034（Phase 7 US5 治理）` 等不撞號寫法）。
