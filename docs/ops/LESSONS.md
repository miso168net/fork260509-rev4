<!-- next: L-143 -->
# LESSONS — 教訓 registry

一教訓一段（`L-NNN｜坑＋防法`）、append-only；配號取檔頭 next-id 後 bump、號碼永不回收。
單卷逼近 25k tokens 時分卷（切出整段舊號封存為 `LESSONS-<起迄號>.md`、主檔續寫、L 號跨卷連號）。
L-001~L-101（rev3 教訓種子全量）☞ LESSONS-001-101.md。

## 〔環境與工具鏈（WSL2／docker／cargo／vite）〕

- **L-106**｜base-web worktree 在主機 git commit 會觸發 soybean 上游 husky/lint-staged hook 跑 pnpm install，但 rev4 設計 node toolchain 全在容器、主機無→hook 跑不動且中斷會汙染 node_modules（★汙染只落主機側 9p bind 源目錄：base_web_node_modules named volume 自 001-U3 已宣告＋掛載＋實效、容器內 /app/node_modules＝ext4 volume 遮罩主機殘留、容器不受害——2026-07-10 B-057 偵察 docker inspect/mount 實證；原句「可能未掛載」係推測、已勘誤）。
  防：base-web 所有 commit 一律 `--no-verify`（驗證已於容器內 typecheck+lint load-bearing 完成）；node_modules 壞了在容器內 `pnpm install --prefer-offline`（CI=true frozen-lockfile、走 /pnpm-store、lock 不漂移）修復。｜出處：004 單元④/⑤ 實測
- **L-107**｜base-web `pnpm gen-route`（sa gen-route）是互動式新增-route 精靈、`-T` 無 TTY 會卡在 `please enter route name`，非 headless 重生成器；route 實際由運行中 dev 容器的 ElegantVueRouter vite plugin 於 .vue file-add 事件自動生成。
  防：base-web 驗收只跑容器內 `pnpm typecheck`＋`pnpm lint`（勿在腳本串 `pnpm gen-route`——會卡）；route 生成靠 dev 容器 plugin 自動觸發、手填 meta（roles/icon/order）regen 保留。｜出處：004 單元④ 實測

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
  防：修改型標記必含 `// [rev4-inline <軌道>] 原行: <example 原碼逐字>`（憲法 §III L114）；`tools/fork-delta-lint` 以 `fork260509-soybean-admin-base@example` 為基線 diff base-web、修改型缺原行即紅（含 self-test 防 vacuous、掛 pre-commit 於 base-web pin 變動時自動跑）——機器強制、不靠人工 review。｜出處：004-system-settings（user review 抓出）

## 〔後端／DB／redis〕

## 〔前端／UI〕

## 〔CDP／mock 驗收〕

- **L-109**｜新增 seed 的 migration（如 m003 加 system_settings 一列）會靜默破 schema-gate 閘 2——閘 2 契約（ADR 0021）「實庫 seed 集合＝定稿清單、多 0」不容任何後續刀新增 seed；且非 pre-commit 閘、只在波段出口回歸才紅。
  防：新 seed 隨其 migration 同 commit 於 tools/schema-gate 的 SEED_ADDITIVE_ALLOWLIST 宣告（ADR 0032 additive 白名單、比照閘 1 結構白名單）；002 凍結 fixtures 永不因新增 seed 改寫（保 rev3/定稿 byte-pure）。｜出處：005 D2 拍板
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
- **L-119**｜`.vue` 檔 template 區不認 `//`／`/* */` 註解，fork-delta 標記在 template 區必須用 HTML 註解形 `<!-- [rev4-inline …] -->`（007 首用；`tools/fork-delta-lint` 已支援該形）。
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
- **L-129**｜`tools/docs-sync`／`tools/schema-gate`／`tools/fork-delta-lint` 皆 **python3 shebang**——`bash tools/<x>` 會把 python 原始碼當 shell 解譯、噴 `import: command not found`＋syntax error 假失敗；一律直接執行（`tools/<x>`）或 `python3 tools/<x>`。★`schema-gate` 另需子命令 `gate1`／`gate2`／`audit`（無參回 exit 64 EX_USAGE、只印 usage）。
- **L-130**｜`tools/docs-sync generate` 的 submodule pin（STATE.md `pins:`）**取自 git index 的 gitlink**、非 worktree HEAD——故 submodule pin bump 的兩段式 commit 中，須先 `git add rust-api`（或 base-web）再跑 generate，否則 STATE pin 不更新、check 報不一致（008 U1 起每單元收單實測）。
- **L-131**｜CDP 驅動 base-web 時 Edge **背景分頁會被凍結**（`document.visibilityState==='hidden'`、任務佇列停擺）→ 頁面發出的 `fetch` 在 `requestWillBeSent` 後**永不 settle**、連 `AbortSignal.timeout` 都不觸發，點擊（如 quick-login）看似完全無反應、症狀與「後端沒回應」無法區分。★驅動前必先 `Page.bringToFront`（visible 後同請求立即完成）；凍結期在途請求會隨 `Page.reload` 一併作廢。
- **L-132**｜Workflow 看門狗 `RUNAWAY=25`（journal 行數保險絲）對 **fan-out 型 review/偵察 workflow 會誤觸**——每 agent journal 約 2 行，多鏡頭並行（如 6 鏡頭＝12 行＋log、或 21 agent＝42 行）易超 25。★掛錶前估 journal 理論行數（agent 數×2＋log），逼近或超過就改 stall-only 監控、勿反射性 TaskStop 健康 workflow。
- **L-133**｜WSL2 drvfs 可**整批 clobber worktree 檔案回舊狀態、但 git index（staged）內容倖存**——008 U15 收尾實測：憲法 amendment／五 ADR／spec 承重前提全被 worktree 回退，但 `git add` 過的版本全在 index。★復原＝`git restore --worktree <files>`（worktree ← index，含還原被刪的 `AD` 狀態檔）；中斷/交接後**一律先核 `git status` 的 staged(index) vs worktree 分歧方向**再判斷內容是否遺失——多半沒遺失、只是 worktree 被回退。與 [[drvfs-commit-phantom-success]] 同源（drvfs 對 git 狀態的干擾）。
- **L-134**｜IPv4-mapped IPv6 家族不符：`::ffff:a.b.c.d` 形的 client_ip 與 v4 規則網段（gate `decide`／`would_self_lock`）、v4 計數桶 inet（`real_ip <<=` 比對）**家族不符恆 false**＝閘門漏判＋per-IP 計數恆 0。★修法＝**單點** canonical：兩 overlay 產出真實來源後、注入 RequestContext 前 `client_ip.to_canonical()` 折 v4（對純 v4/v6 恆等、無副作用），使下游全拿 canonical 形；`peer_ip` 保持原形（不參與桶比對）。008 final review #1 修正 A。
- **L-135**｜以 CDP 驗「debounce／`watch` 觸發次數」有兩個陷阱：①**Vue `watch` 對同步多次改值只 flush 一次**——在 `Runtime.evaluate` 內同步連改被觀察值 N 次，watcher 僅作動一次、下游（含被測 debounce）只發 1 次請求，**有無 debounce 皆得 1**＝假綠；須以真實延遲分散（各改動間 `await setTimeout`、如 50ms×5＝250ms＜300ms 窗），令每次改動各觸發一次 flush，debounce 的 coalesce 才可觀測（B-075① 實測：軟區開、連改 userName → `/auth/loginCaptcha` 恰 1 發；無 debounce 應 5 發）。②**計數走 CDP `Network.requestWillBeSent`**（瀏覽器側、含 vite proxy 請求）、**非** page-context 的 `fetch`／XHR hook（request 層載入時已捕獲參考、page-context hook 攔不到＝L-122 ②）。狀態注入沿 captcha-inspect 範式（`el.__vueParentComponent` 上溯 `setupState` 設 `captchaVisible`／驅動 `model`）＋驅動前 `Page.bringToFront`（L-131）。
- **L-136**｜對**凍結基線表加尾欄**（gate2 欄序面覆蓋、data-model §3 十二張欄序表凍結）會破 gate2——既有 ADR 0039 結構 additive 容差**只放寬 gate1**（post-baseline 新表／新索引），**不含 gate2「既有表加欄」**；而 gate2 欄序面對每表 `information_schema.ordinal_position` 逐位比對 §3 欄序表，尾端多一欄即整段位移假紅（且 gate2 非 pre-commit 閘、只波段出口回歸才紅）。009 m007＝`sys_casbin_policy_archive` 加 `role_id`（唯一結構變更）即撞。
  防：加欄隨其 migration 同 commit 於 `tools/schema-gate` **欄序面 additive 容差白名單**登記（`WHITELIST_TYPE[(table,col)]=期望型別`，如 `("sys_casbin_policy_archive","role_id"):"bigint"`）——gate2 把「實庫尾端多出且登記之欄」剝除後再逐位比對（只放寬尾端新增、不放寬改動/重排）＋gate1 欄面白名單同步登記；§3 定稿與 psql 快照凍結不改（比照 STRUCT_ADDITIVE_ALLOWLIST／SEED_ADDITIVE_ALLOWLIST 範式、逐項註來源刀零萬用字元）。此為欄序面容差首例＝009 m007 archive.role_id。｜出處：009 U1（m007）／schema-gate 欄序面容差擴充
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
  前綴執行；腳本若 spawn python 且需讀 UTF-8 檔（如 `tools/fork-delta-lint` 讀 `原行:` 註解）
  再加 **`PYTHONUTF8=1`** 保 python 在 C locale 下仍以 UTF-8 `open()`。定案指令：
  `cd <repo 根>; LC_ALL=C PYTHONUTF8=1 bash tools/bootstrap`；`bash tools/wf-watchdog <token>`
  同理前綴 `LC_ALL=C`（此為 Workflow 編排看門狗、macOS 上不加會靜默壞）。跨平台根治（可選、
  與環境變數繞法二擇一）：把所有「`$var` 緊接非 `[A-Za-z0-9_]` 字元」處改 `${var}` 顯式界定
  （braces 使 bash 不吃後續 byte、macOS/Linux 皆安全），惟涉改多支 committed 工具、非必要。
  ｜出處：2026-07-13 macOS fresh-clone bootstrap 實測（Darwin 25；bash 3.2.57＋Homebrew 5.3.15
  雙證、locale 矩陣＋`LC_ALL=C` 修正實證；交接檔 2026-07-14 以 L-142 收錄——原配號 L-139 已被佔用）
