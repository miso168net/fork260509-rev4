<!-- next: L-135 -->
# LESSONS — 教訓 registry

一教訓一段（`L-NNN｜坑＋防法`）、append-only；配號取檔頭 next-id 後 bump、號碼永不回收。
單卷逼近 25k tokens 時分卷（滿卷改名 `LESSONS-<起迄號>.md` 封存、主檔續寫、L 號跨卷連號）。
初始 101 筆＝rev3 教訓種子全量；`出處：rev3:…` 為史料標註（純文字、非連結）。

## 〔環境與工具鏈（WSL2／docker／cargo／vite）〕

- **L-001**｜Windows host 的 git autocrlf 會把 .sh/.yaml/.conf 換行改成 CRLF，容器內腳本與設定檔直接壞掉。
  防：repo 以 .gitattributes 強制 LF。｜出處：rev3:CLAUDE.md§2-目錄樹註
- **L-002**｜WSL2 NAT 網路模式下，host 的 127.0.0.1 打不進容器映射 port，curl 全失敗看似服務沒起。
  防：設 .wslconfig 的 mirrored networking（Win11 22H2 以上預設），或用 wsl hostname -I 拿 WSL IP 連。｜出處：rev3:CLAUDE.md§8.2.1
- **L-003**｜Docker Desktop WSL2 重度 churn 後，host 經 127.0.0.1 打容器 port 單請求可慢到超過 4 秒，短 --max-time 的 curl 回 000 看似 port-forward 死、實則 server 活著——曾因此誤判「網路全斷」還多請 user 重啟 Docker Desktop。
  防：別用短 timeout 判生死：改 curl localhost（走 IPv6 快路徑）或拉長 timeout；最可靠是容器網路內驗（docker compose exec 進 base-web 用 node http.request 直打 rust-api），完全繞過 host port-forward。｜出處：rev3:memory/wsl-host-portforward-slow-use-localhost-or-container-net
- **L-004**｜down -v 後或新機器首次 up --wait，base-web（約 140 秒 pnpm install）與 rust-api（約 240 秒 cargo build）冷編譯期間 healthcheck 會 flap、up --wait 可能非零退出，看似啟動失敗實為還在編譯。
  防：先 docker compose ps 判斷是否仍在編譯（非真失敗），待穩後重跑 up --wait 即過。｜出處：rev3:CLAUDE.md§8.2.1
- **L-005**｜dev image 升級 rust toolchain 後，cargo cache named volume 仍掛著舊 toolchain 內容、遮蓋 image 內新版。
  防：手動 docker volume rm 該 cargo cache 卷後重 build。｜出處：rev3:CLAUDE.md§8.2.1
- **L-006**｜host 開機過久後，glibc 基底容器（rust-api dev）內每次 cargo 都崩 ld.so 的 R_X86_64_RELATIVE 不一致、容器 exit 127——連純 cargo --version 都崩，代表是 host 層 WSL2 loader 故障，不是 volume 或容器狀態壞（alpine 基底映像不受影響）。
  防：重啟 Docker Desktop（完整 Quit 再開）或 wsl --shutdown 後重啟 stack 即復原；別誤刪 volume 重編，worktree 改動在 /mnt/d 安全。｜出處：rev3:CLAUDE.md§8.2.1
- **L-007**｜rust 各 task 即使被標為可平行，平行跑 cargo 會互撞共用 target 目錄。
  防：rust build/test 全程 serial，不平行 cargo。｜出處：rev3:CLAUDE.md§3-階段2
- **L-008**｜WSL2 /mnt/d 上改完 .rs 後 cargo 可能因 stale mtime 沒察覺變更、跑舊 binary 回假綠——沒重編、handler 簽名不符仍顯示通過。
  防：容器內編譯/測試前先 force-touch 對應 crate 的所有 .rs（find 加 exec touch）再 build。｜出處：rev3:CLAUDE.md§8.2.1
- **L-009**｜cargo test 後面裸接測試名會被當成 test-function 名 filter，0 命中卻顯示「ok. 0 passed; N filtered out」——測試根本沒跑卻看似綠。
  防：跑整支整合測試 binary 必用 --test 旗標指名；看到「0 passed / N filtered out」立即當警訊而非通過。｜出處：rev3:CLAUDE.md§8.2.1
- **L-010**｜server 是 bin-only crate（無 lib.rs），tests 目錄的整合測試無法 use 該 crate 的內部 API，硬寫就編不過。
  防：需呼叫 crate 內部 API 的測試放 in-crate 的 cfg(test) 模組、掛 ignore 標記加環境變數 gate——預設測試跳過（無 DB 仍綠），live 跑時加 --ignored --test-threads=1。｜出處：rev3:CLAUDE.md§8.2.1
- **L-011**｜WSL2 drvfs（/mnt/d 的 NTFS 掛載）上用 Edit 工具連發多筆編輯會間歇報 ENOENT statx 或「file modified since read」，但寫入多半其實已成功——當失敗重做會重複寫入或腦補錯誤狀態。
  防：逐一編輯不連發；報錯時先用 grep/Read 回讀磁碟驗證是否已生效，已生效就跳過不重做；大量改動時以確定性 grep 驗證為準、不信 Edit 回傳訊息。｜出處：rev3:memory/wsl-drvfs-edit-flakiness；另 rev3:CLAUDE.md§8.2.1
- **L-012**｜[流程] 工具環境抖動時 Write/驗證可能假性回報成功而檔案未落地（另見 stdout 重複、工具結果混入模型敘述）——「回報成功」不等於「真的成功」。
  防：關鍵寫檔（commit、不可重得資料、交棒文件）後用獨立命令二次驗證（git cat-file、wc -c、json.load）並展示輸出；結果錯亂就停下明說不可信、絕不腦補填補。｜出處：rev3:memory/tool-result-flakiness-incident
- **L-013**｜rust-api dev 用 cargo watch 的 poll 模式（刻意，因 WSL2/9p inotify 不可靠），重編有偵測延遲、且 stale mtime 可能讓它重編到舊碼——活體驗收會打到舊 binary、新 endpoint 回 404。
  防：跑 curl/psql/CDP 活體前先確認 rust-api log 有重編完成且新 endpoint 回 200；沒上就 force-touch 加 restart rust-api。｜出處：rev3:CLAUDE.md§8.2.1
- **L-014**｜base-web vite 沒熱載新加的 service fn 時，瀏覽器丟「does not provide an export named …」SyntaxError、該頁掛不起來、list API 完全不發。
  防：症狀出現即 restart base-web（pnpm install 走卷快取、秒級就緒）。｜出處：rev3:CLAUDE.md§8.2.1
- **L-015**｜新增 i18n locale 鍵後 dev vite 可能沒熱載新字典，瀏覽器 toast 顯 raw key 而非譯文——curl（回業務碼＋key 看似正常）、typecheck、source grep 三者全綠都掩蓋，靜默無 error、唯 CDP 實渲染抓得到（curl 不等於 modal 的 i18n 變體）。
  防：加 i18n 鍵的 feature 跑 CDP toast 驗收前先 restart base-web，且腳本斷言頁面無 raw key（不只看有 toast）；committed 碼本身正確、prod build 會把 locale 編進去。｜出處：rev3:memory/vite-stale-locale-new-key-raw-toast；另 rev3:REVIEW§4（019 已閉合項）；rev3:CLAUDE.md§8.2.1
- **L-016**｜front-nginx 是 bind-mount 單一 conf 檔，改完 conf 跑 restart 會炸 OCI runtime mount not found（Docker Desktop WSL2 bind-mount 快照路徑失效）。
  防：front-nginx 改 conf 後一律 up -d --force-recreate 該 service，不能用 restart。｜出處：rev3:CLAUDE.md§8.2.1
- **L-017**｜prod baseline 模式不啟 acme、憑證不會自動取得，named certs volume 沒先 seed 憑證時 HTTPS 端無 cert 可用。
  防：啟 prod 前先把 fullchain/privkey 複製進 front-nginx 的 certs named volume。｜出處：rev3:CLAUDE.md§8.2.1
- **L-018**｜graphify 圖譜抓不全 .vue 檔的 template 與 import 關係，問 Vue SFC 之間 wiring 會得到殘缺答案。
  防：Vue component composition 問題直接讀 SFC，不靠圖譜推論。｜出處：rev3:CLAUDE.md§8.3
- **L-019**｜graphify 增量更新的標準 build_merge 預設開全域 fuzzy-label dedup，會把同名/近似 label 的 distinct 真節點誤併（實測一次誤刪約 700 個未變更真節點）；另 manifest 與 graph.json 會 desync（manifest 宣稱已索引、圖裡實缺整棵子樹），純 manifest-diff 增量補不了洞；obsidian export 也不清孤兒舊 note。
  防：增量一律外科式：顯式 prune 變更檔舊節點→build_merge 帶 dedup=False（prune_sources 只給已刪除檔）；merge 後節點數必須成長、縮水即停手不寫檔；update 前先 grep graph.json 實際 source 覆蓋、別只信 manifest；export obsidian 前先清舊 .md。｜出處：rev3:memory/graphify-update-fuzzy-dedup
- **L-020**｜spec-kit 有兩條獨立版本軸：repo release tag（如 v0.10.x）與 specify-cli 套件自報版本（如 0.8.x）本來就不相等，且安裝器把 tag 解析成 commit 釘著裝、uv 顯示裸 commit hash——看到落差容易誤判成裝錯或裝到 main HEAD。
  防：驗證是否釘在 release：比對 install log 的 build commit 是否等於該 tag peel 後的 commit（git ls-remote --tags）且不等於 HEAD；specify --version 只用來查 dev/rc/alpha/beta/pre 後綴、有就重裝穩定 tag。｜出處：rev3:memory/speckit-version-axes
- **L-106**｜base-web worktree 在主機 git commit 會觸發 soybean 上游 husky/lint-staged hook 跑 pnpm install，但 rev4 設計 node toolchain 全在容器、主機無→hook 跑不動且中斷會汙染 node_modules（★汙染只落主機側 9p bind 源目錄：base_web_node_modules named volume 自 001-U3 已宣告＋掛載＋實效、容器內 /app/node_modules＝ext4 volume 遮罩主機殘留、容器不受害——2026-07-10 B-057 偵察 docker inspect/mount 實證；原句「可能未掛載」係推測、已勘誤）。
  防：base-web 所有 commit 一律 `--no-verify`（驗證已於容器內 typecheck+lint load-bearing 完成）；node_modules 壞了在容器內 `pnpm install --prefer-offline`（CI=true frozen-lockfile、走 /pnpm-store、lock 不漂移）修復。｜出處：004 單元④/⑤ 實測
- **L-107**｜base-web `pnpm gen-route`（sa gen-route）是互動式新增-route 精靈、`-T` 無 TTY 會卡在 `please enter route name`，非 headless 重生成器；route 實際由運行中 dev 容器的 ElegantVueRouter vite plugin 於 .vue file-add 事件自動生成。
  防：base-web 驗收只跑容器內 `pnpm typecheck`＋`pnpm lint`（勿在腳本串 `pnpm gen-route`——會卡）；route 生成靠 dev 容器 plugin 自動觸發、手填 meta（roles/icon/order）regen 保留。｜出處：004 單元④ 實測

## 〔git／worktree／submodule〕

- **L-021**｜git push 或 git merge 出現在開發收尾階段之前（直接執行、或被排進 tasks 清單）會把未審完狀態推上共享 remote、事後難收回。
  防：push/merge 只允許在 finishing-a-development-branch 收尾階段出現，push 前需 user 明確同意，tasks 清單不得排入。｜出處：rev3:CLAUDE.md§3
- **L-022**｜merge 收尾想用「-F -」從 stdin 讀 commit 訊息會失敗，git 直接報 could not read file '-'。
  防：merge commit 訊息用 -m 直接給。｜出處：rev3:CLAUDE.md§3-收尾
- **L-023**｜進度檔回填（里程碑表、todo 檔、active-feature 標記）若排在 merge 之前做，要寫入的 merge SHA 與最終 worktree pin 都還沒確定、必然回頭改。
  防：進度檔回填一律排在 merge 之後（這些檔屬 workspace 層、本就在主幹上）。｜出處：rev3:CLAUDE.md§3-收尾
- **L-024**｜收尾把 feature branch 清掉會失去 spec-kit feature 的 audit／追溯線索。
  防：merge --no-ff 回主幹後保留 feature branch 不清理。｜出處：rev3:CLAUDE.md§3-收尾
- **L-025**｜submodule pin bump 延到 feature 末刀才一次做（rev3-001 曾把十餘個 task 的 pin 全延到最後一個 task），中繼 outer commit 的 pin 全部過期，checkout 任一中繼 commit 都不可重現當時 tasks 勾選聲明。
  防：worktree commit 落地的當個 task／單元就同步 bump outer pin，讓每個 outer pin commit 對應一個可重現的單元邊界。｜出處：rev3:CLAUDE.md§4.1；另 rev3:CLAUDE.md§4.1／§5
- **L-026**｜本機 worktree 模式下 git submodule status 行首的減號是永遠出現的正常現象，誤跑 git submodule update --init --recursive 會與 worktree 的 .git gitlink 衝突。
  防：先判 base-web/rust-api 的 .git 是檔案（worktree 模式、勿 update）還是不存在（新 clone 機器、才跑 init update）再處置。｜出處：rev3:CLAUDE.md§4.3
- **L-027**｜outer pin 與本機 worktree HEAD 不同時跑 git submodule update，會把 worktree reset 掉、覆蓋尚未推出的本機改動。
  防：pin 與 worktree 分歧一律走「回外層更新 pin」方向，永不 submodule update。｜出處：rev3:CLAUDE.md§4.7
- **L-028**｜在 worktree 內裸跑 git push 不指定 remote/branch，預設推向 fork 源倉、可能誤推到非預期分支。
  防：worktree push 一律顯式 git push origin 加長名分支。｜出處：rev3:CLAUDE.md§5
- **L-029**｜用 git submodule add 註冊 base-web/rust-api 會嘗試 clone 進目錄、與既有 worktree 衝突。
  防：submodule 設定手寫 .gitmodules 加 git config 加 submodule init，外層只 git add 目錄記 SHA pin。｜出處：rev3:CLAUDE.md§4.4／§5
- **L-030**｜直接編輯 fork260509 系列源倉的檔案，改動不會落在整合分支的 worktree 上。
  防：base 與 rust 的改動一律透過 base-web/、rust-api/ worktree 進行；docs 源倉僅參考不改。｜出處：rev3:CLAUDE.md§5
- **L-031**｜跳過 spec-kit 標記為 mandatory 的 pre-hook（specify 前自動建 feature branch 那支），spec 文件與 pin 變動會直接落在 default branch 上。
  防：讓 pre-hook 跑、或手動先切出 feature branch；pre-hook 只在 local 建分支不 push，不違反 push 同意紀律。｜出處：rev3:CLAUDE.md§5
- **L-032**｜在外層 git add fork260509 系列源倉目錄會把它們變成 embedded git repo 污染外層。
  防：源倉維持 gitignored、只 add base-web/rust-api 兩個 gitlink；add gitlink 時 git 的 embedded repository 警告屬正常可忽略。｜出處：rev3:CLAUDE.md§5／§4.7
- **L-033**｜fork260509 系列源倉雖 gitignored，本機刪掉它會讓 worktree 的 .git 檔（指向源倉 worktrees 目錄）懸空、base-web/rust-api 全斷。
  防：源倉本機必留；真斷了走 worktree 重建流程，或新機器改用 recurse-submodules clone。｜出處：rev3:CLAUDE.md§2
- **L-034**｜源倉設了指向 soybeanjs 官方的 upstream remote 後，一個手滑 push 就會推到官方 repo。
  防：upstream 的 push URL 設成 no_push（fetch 留官方 URL），fetch 前 git remote -v 確認兩向 URL。｜出處：rev3:CLAUDE.md§4.6
- **L-035**｜base-web 對 upstream rebase 改寫 history 後若忘了回外層 bump pin，outer 記的 SHA 指向已被改寫掉的舊 history。
  防：rebase 加 force-with-lease push 後立即回外層 git add base-web 更新 pin。｜出處：rev3:CLAUDE.md§4.6
- **L-105**｜兩段式 commit 的外層 pin bump：docs-sync generate 必須跑在 git add <submodule>（暫存新 gitlink）之後——generate 與 pre-commit lint L1 的 check 都讀「已暫存的 gitlink」算 STATE 的 pin；generate 若跑在 add gitlink 前，STATE 沿用舊 pin、L1 擋 commit（003 U2 撞過、重跑修正）。
  防：正確序＝git add <submodule> → docs-sync generate → git add docs/generated/STATE.md → commit（一路到底不回頭）。｜出處：003-wire-foundation

## 〔流程與編排（spec-kit／superpowers／Workflow／subagent）〕

- **L-036**｜把 SDD 規格起手指令排進 brainstorm 流程內自動觸發時，負責建 feature branch 的 mandatory pre-hook 不會執行，spec 文件會落在錯的 branch 上。
  防：規格指令一律在 brainstorm 收尾後手動執行，讓 pre-hook 正常從 default branch 衍生 feature branch。｜出處：rev3:CLAUDE.md§3-階段0
- **L-037**｜實作階段若改用 spec-kit 內建的 implement 指令起手，會繞過 TDD 編排（implementer→spec 對照審→品質審的 fix 迴圈）與主線單元邊界 checkpoint。
  防：實作一律以 superpowers 的 executing-plans 讀 tasks 起手並批判審查分執行單元，從不使用 spec-kit 的 implement 指令。｜出處：rev3:CLAUDE.md§3
- **L-038**｜把純工程「怎麼做」選擇（優化手法、模組拆法、DTO 映射、命名、測試策略）做成選項題丟給 user，或拍板題用內部術語抽象列，浪費拍板頻寬又害 user 選錯。
  防：工程選擇自己拍；只有動 schema／加 migration、feature scope 邊界、破紀律例外等真拍板級才問，問時大白話＋每選項串回 user 核心目標＋trade-off 主張先 grep 實證。｜出處：rev3:CLAUDE.md§3-階段0
- **L-039**｜spec 設計 wire DTO 時盲信 brainstorm 假設而非 facade 實際返回型——rust-api 是 facade-only 存取（無 service trait 層），不同 facade fn 可能返 raw Model、也可能返 sanitized 形（濾軟刪列、遮密碼欄），對不上就是契約錯。
  防：plan 的 research 階段先 grep facade fn 真實返回型並對照 entity Model 欄位，再定 wire DTO。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-040**｜wire endpoint 三端（rust handler 返回型、前端 service 與 typings 宣告型、component 內部 state 型）任一端沒對齊就是 runtime bug 或 type lie，且單看任一端都全綠。
  防：每條 wire endpoint 動工前同時 grep 三端型別並互相對齊。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-041**｜spec/data-model 裡 brainstorm 推測的 struct/function 命名與檔案行號引用常與實碼不符，implementer 盲信 spec 字面命名會改錯地方。
  防：文件內每個程式引用先 grep 驗真實命名，實作以 actual code 為準而非 spec 命名。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-042**｜subagent 把長時間 cargo 丟 background 或 timeout 設太短，會在編譯結束前結束回合、拿不到真結論。
  防：長 cargo 不准 background、timeout 拉長、agent 得出結論前不得結束回合——此紀律要烤進每個 agent prompt。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/subagent-foreground-blocking
- **L-043**｜review agent 把 findings 寫成 repo 內檔案（review 報告檔之類）會污染 git status、混進後續 commit。
  防：spec 審與品質審兩個 review agent 一律只讀，findings 只放回傳訊息。｜出處：rev3:CLAUDE.md§3-階段2
- **L-044**｜Workflow script 裡 agent() 遇 transient API error 或 user skip 會回 null，直接取回傳物件的欄位就 throw、整支 workflow crash。
  防：agent() 回傳一律 null-guard，null 視為 inconclusive、retry 或跳過該步。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/workflow-review-loop-null-and-scope
- **L-045**｜reviewer prompt 沒寫明本單元 in/out scope 時，reviewer 會把下游單元/波次的 deferred 產物誤判成 critical、同時漏抓真 bug。
  防：每個 reviewer prompt 明列「本單元範圍＝X、後續 deferred 工作＝Y、不得 flag」。｜出處：rev3:CLAUDE.md§3-階段2
- **L-046**｜Workflow 用 args 物件傳 per-unit prompt 時，args 常被序列化成字串、script 內取欄位變 undefined——silent 不 throw，agent 收到字面「undefined」當任務內容。
  防：per-unit prompt 一律內聯進 script body 的 const，不靠 args 傳。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/workflow-args-stringified-undefined
- **L-047**｜[流程] 手動逐-subagent 編排時，reviewer 完成通知常被折進 sibling/parent 的通知串、不會喚醒 main loop——純被動等通知就出現長 idle gap，甚至誤信沒派過的 review「已通過」。
  防：多單元 pipeline 改用 Workflow 工具驅動（script 內 deterministic 串 implementer→review→fix、主線只在單元邊界醒）；保留手動模式時 agent 理應完成就主動用 git/test 自驗 ground-truth、等待期做非重疊 prep，不純等 flaky 通知。｜出處：rev3:memory/orchestration-avoid-idle-on-folded-notifications
- **L-048**｜[流程] Workflow implementer 的結構化自報（filesChanged、gitStatusClean）不可信——曾自報「5 檔乾淨」實際 commit 7 檔：偷 commit 該留在 /tmp 的測試檔、還動了明令不動的 package.json，自報摘要把偏離全部抹平。
  防：每個單元邊界 bump submodule pin 前，主線親自 git show --stat HEAD＋git status 對照該單元授權範圍，專抓多出的禁改檔（測試檔、package.json、lockfile、generated typings）。｜出處：rev3:memory/workflow-implementer-gitstate-claims-unreliable；另 rev3:CLAUDE.md§3-階段2
- **L-049**｜[流程] 部署層交付物（compose/deploy 檔）的驗收 grep 對前代 workspace 代號字樣零豁免，連 review 修補註解時順手寫入前代代號都會撞紅——同一人踩過兩次。
  防：部署層檔案提及前一代一律寫「前代」「前代 workspace」；僅既定豁免（migration 檔名、GitHub 永久倉名）例外。｜出處：rev3:memory/deploy-layer-zero-rev2-wording
- **L-050**｜[流程] 依賴/設定漂移若功能上惰性（如 feature-gated、永不編譯的 optional dep 被解析到新版），強制改回舊 pin 只是 churn；但默默吞掉又違反漂移必 surface 的紀律。
  防：先判 real/inert（cargo tree -i 看是否真在編譯圖）；惰性者仍要 surface，把「接受漂移＋把 stale 註解校正成真正的不變式（不啟用拉該 crate 的 feature）」列首選、「強制原 pin」列次選並標明是 churn。｜出處：rev3:memory/inert-drift-accept-and-correct-doc
- **L-051**｜[流程] review「從前代拉來且有調整」的檔案時只看衍生檔本身，抓不到周邊文件內嵌的舊結構殘影——章節序、子節編號慣例的引用點全指舊版結構而不自知。
  防：三方比對：先讀原版全結構（grep 標題）、diff 出結構差異清單、再 grep 全 repo 引用該檔結構的下游逐一核對。｜出處：rev3:memory/read-source-before-derived-review
- **L-052**｜[流程] 往文件階層寫識別碼的兩個坑：brainstorm 拍板自鑄新警示碼當小節編號會污染全域決策 registry；用行號當交叉引用（某檔 line NNN）則文件一改行號全飄、引用立即 rot、讀者看不懂。
  防：拍板表用描述名、只引用既有 registry 碼，新碼只給真正跨 feature 的長壽決策且按實際編入先後給號、不預留 gap；交叉引用一律用穩定語意錨（章節號/附錄名/描述名），程式碼註解就地自解釋、不回指動態 todo 檔。｜出處：rev3:memory/brainstorm-doc-decision-table-not-warn-codes
- **L-103**｜Workflow 工具的 args 參數在本環境一律以 JSON 字串抵達 script（canary 實證：傳格式正確的小物件仍是字串）——`args.欄位` 讀出 undefined、agent 收到字面 "undefined" 當任務；若迴圈上限也取自 args，`n > undefined` 恆 false、邊界與壞輸入同源靜默失效（曾空轉 144 輪／290 支 agent／5.4 小時）。
  防：agent prompt 全數烤進 script 本體模板字串、args 只傳短純量；script 首段斷言 args 型別＋必要欄位非空、不符零派發即 throw；一切邊界（fix 輪數、agent 總數保險絲）寫死 script 常數、與外部輸入不同源；派發前斷言 prompt 非空且不含字面 undefined。｜出處：2026-07-04 002-schema-baseline TDD 編排死迴圈事故檢討
- **L-104**｜背景 workflow「發射即睡、等完成通知」對非終止型故障（死迴圈、卡死）是盲區——完成通知永遠不來；且 LLM agent 對同一結論每輪措辭不同，result 字面去重抓不到語意空轉（290 筆 result 去重後 287 種）。
  防：發射後即讀 agent transcript 首行驗 prompt 完整抵達（冒煙）；掛 Monitor 保險絲（journal 事件數＞2× 單元理論上限告警＋停滯偵測、閾值＞最長合法 cargo 時長）；收斂偵測用結構化欄位比較（blocker 的 file×summary 集合連兩輪相同＝不收斂）、勿比自由文字；判死迴圈→TaskStop→修 script→resumeFromRunId 續跑（已完成 agent 走快取）。｜出處：2026-07-04 002-schema-baseline TDD 編排死迴圈事故檢討

## 〔review／驗收方法論〕

- **L-053**｜純靜態 review 對 runtime 漂移結構性失明——三輪純靜態審查給出全數 PASS、零真缺陷的結論，實際仍有設定列位置漂移、重置鈕行為、i18n raw key 洩漏等一批只有活體才看得到的問題，事後靠 live/CDP 輪才補抓。
  防：cumulative review 必配 live 讀端（curl/psql/redis）＋CDP 真瀏覽器補證輪；靜態輪對驗不到的項誠實標 needs-runtime，不得逕判 PASS。｜出處：rev3:REVIEW§1＋§7
- **L-054**｜一批 UI/runtime 真相只有 CDP 真瀏覽器抓得到：axios 空字串 query 的真實序列化形、搜尋重置鈕行為、匯出鈕收合後的可發現性、列表無排序時的位置漂移、i18n raw-key 洩漏、三態排序箭頭與持久化還原——curl、typecheck、grep 全綠都掩蓋。
  防：UI 行為類驗收一律排 CDP 軌；curl 只當補充、且刻意模擬前端請求形（帶空參數）而非乾淨 query。｜出處：rev3:REVIEW§7
- **L-055**｜review 輪受非破壞紀律約束（禁寫端操作、禁觸發鎖定、禁建 IP 規則），寫端需求實際只有「實碼閱讀＋當年收刀驗收全綠」等級的背書——review 報 PASS 容易被誤讀成寫端已被重新驗證。
  防：review 報告逐項明標證據等級（純靜態／live 讀端／CDP／收刀背書），寫端回歸靠自動化測試覆蓋，否則明示「未重演」。｜出處：rev3:REVIEW§7
- **L-056**｜cumulative 多刀審查若平行跑，後刀合法推翻前刀的行為會被 reviewer 誤判成漂移缺陷，或反向漏掉真正無依據的漂移。
  防：依刀序 serial 審查＋維護 supersession 映射表作為「所有偏離皆有拍板依據」的合法依據；前刀行為被後刀改變時，同步在前刀 spec 補 as-built 勘誤註記。｜出處：rev3:REVIEW§5＋§7
- **L-057**｜多個 reviewer 各自登入做 live 驗證會污染登入嘗試/存取日誌、甚至觸發帳號鎖定，把審計類斷言弄成偽紅。
  防：reviewer 共用同一 token（前提＝單一 session 政策關閉）；token 過期從瀏覽器 localStorage 唯讀恢復；CDP 分頁登出態用 token 注入 SOP 而非重走登入表單。｜出處：rev3:REVIEW§7
- **L-058**｜upstream 原樣繼承的頁面行為是審查盲區——搜尋重置鈕不重新查詢、帳號名欄改了顯示成功卻靜默不寫，兩個缺陷都不屬任何一把刀的 spec 範圍，拖到最終 cumulative 輪才浮出。
  防：把繼承自 upstream 的頁面行為也納入驗收/審查面，別假設 upstream＝正確；發現後把「修（產生 fork-delta）vs 維持原樣（零 delta）」做成 user 拍板題而非默改。｜出處：rev3:REVIEW§3.2-F-4/F-5
- **L-059**｜fan-out 出的大量疑似 findings 若直接全修會浪費工甚至誤修——對抗式查證後仍有一批「聽起來合理但未確認」的項。
  防：走對抗式 verifier 把 findings 分 CONFIRMED/PLAUSIBLE 兩級，只有 CONFIRMED 進修復清單；PLAUSIBLE 留完整 reasoning 於紀錄、不動碼。｜出處：rev3:REVIEW§1＋§6
- **L-060**｜多輪 review 的 findings 混雜不分流時，會重修已閉合項、漏掉需 user 拍板的行為變更、或把該登記遞延的項當場亂修。
  防：統一修復輪把 findings 分四類分流（直接修／需 user 拍板／登記不修碼／明確不修）並逐項標處置結果；另設「已閉合 findings」節防重修。｜出處：rev3:REVIEW§3＋§4
- **L-061**｜行為變更的拍板題用抽象語意句問 user，容易讓 user 選錯方向（實際發生過選項誤選）。
  防：問拍板題附具體渲染範例（mock／前後對照畫面）、正交維度拆開列選項、「隱藏/不顯示」類行為必明示其可見結果。｜出處：rev3:REVIEW§3.2 標頭（引 memory ui-behavior-options-need-concrete-examples）
- **L-062**｜驗收計畫把 CDP browser smoke 延後、只留 curl 直打時，「curl 直送不等於前端 modal 行為」的破口會靜默漏到下游。
  防：要 defer 就在 spec 內明示此風險，並在 follow-up backlog 登記補測。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律
- **L-102**｜把多支 migration squash 成單支後，用「已知清單逐項在場」驗收會漏掉「基準有、產物沒有」的反向缺項——雙庫互證八軌全綠仍漏 2 支索引（索引軌只單向點名在場、未做集合 diff），缺陷潛伏到閘 1 雙向比對才現形。
  防：結構驗收一律雙向集合 diff（右缺＝多、左缺＝漏、同時列出），不用單向清單點名。｜出處：002-schema-baseline U3（gate1 抓 sys_casbin_policy_archive 2 索引漏摺）

## 〔文件紀律〕

- **L-063**｜文件勘誤只修被點名那一行、同檔另一行同語意殘留（檔頭仍寫三端點、下方已修成四端點、上方漏改），下一輪 review 再被抓一次。
  防：做勘誤時對同語意字串跑全檔／全 repo grep 掃描，一次改齊所有出現點。｜出處：rev3:REVIEW§3.1-F-1
- **L-064**｜指引文件的 schema 欄位清單只列部分欄（實十六欄只列五欄）又未標明是節選，連續兩輪 review 點名、且曾實際誤導加欄規劃、靠外部記憶補救。
  防：文件列欄位/schema 清單要嘛列全、要嘛明說 partial，並註記以資料庫實況（psql）對過。｜出處：rev3:REVIEW§3.1-F-3；另 rev3:memory/rev3-sys-user-profile-fields-exist
- **L-065**｜spec 寫死數量口徑（表數、設定列數、路由總數、service 數）必被後續刀推翻——每加一項都得補一條 supersession 或勘誤，口徑本身變成維護債。
  防：spec 口徑改指權威 registry/migration「以現況為準」或標 as-of 時點；由加項的那把刀負責同步勘誤前刀 spec。｜出處：rev3:REVIEW§5（表數/設定列數/路由總數多列）
- **L-066**｜歷次 review 報告逐輪堆積且互相引用，一旦清理刪檔、其他文件的引用點全部 dangling。
  防：定期把多份 review 報告整併為單一自包含留存版，詳版全文靠 git 史以 SHA 引用；cross-ref 紀律＝只引用留存文件與 git SHA、不引用已刪檔名路徑。｜出處：rev3:REVIEW檔頭＋§1
- **L-067**｜repo 內 git-tracked 文件引用本機 Claude memory（per-machine／per-user、不在 repo），換機、換維護者、別人 clone 都不存在，引用即 dangling、對他人無意義。
  防：重要記憶內容先提取進 repo 文件（設計/決策/指引檔），再引用該 repo 段落；memory 只供跨 session recall、非引用目標。｜出處：rev3:CLAUDE.md§7
- **L-068**｜其他文件跨檔深連結動態 todo 檔的揮發章節（波狀態、follow-up 節會滾動收縮歸檔），章節錨必 rot 成死連結。
  防：cross-ref 一律改指權威或永久檔（設計藍圖、決策帳、里程碑、spec）；只有 todo 檔內部互引與整檔指向屬結構性例外。｜出處：rev3:CLAUDE.md§7.3
- **L-069**｜todo 檔「最新進展」清單後緊貼的「下一步」blockquote marker 若前面不留空行，會被前一個 list item 的 lazy-continuation 吸收成子項、渲染錯亂。
  防：marker 前必留空行且 marker 勿刪、下一步勿併入最新進展，改完回讀渲染驗證。｜出處：rev3:CLAUDE.md§7.5
- **L-070**｜進度/帳本文件記「已push／未push」這類揮發 git 狀態，push 後立即 stale、誤導後續 session。
  防：只記 commit/merge SHA（可追溯、非揮發），推沒推看 git 本身。｜出處：rev3:CLAUDE.md§7.5
- **L-108**｜base-web fork-delta「修改型」標記只寫描述、漏 `原行:`（緊鄰改動行、含上游那行原碼逐字）——upstream（soybean example 分支）常態更新、rebase 時無「原行」就無法定位/對照上游原本那行，fork-delta 標記核心用途落空；根因＝編排 prompt 條文過鬆（只說「原行加標記」未要求原行內容）、review 亦未驗。
  防：修改型標記必含 `// [rev4-inline <軌道>] 原行: <example 原碼逐字>`（憲法 §III L114）；`tools/fork-delta-lint` 以 `fork260509-soybean-admin-base@example` 為基線 diff base-web、修改型缺原行即紅（含 self-test 防 vacuous、掛 pre-commit 於 base-web pin 變動時自動跑）——機器強制、不靠人工 review。｜出處：004-system-settings（user review 抓出）

## 〔後端／DB／redis〕

- **L-071**｜workspace 的 sea-orm 刻意 default-features=false、無 date-time backend，新增帶 timestamptz 欄的 entity Model 會編譯失敗（DateTimeWithTimeZone 型別找不到）——每個帶 timestamp 欄的新 entity 刀都會再撞。
  防：在消費該型的 crate 對 sea-orm 加 with-chrono feature（絕不用 with-time、避免把 time crate 拉進編譯圖）；另注意複合主鍵 join 表兩個 PK 欄都要標 primary_key＋auto_increment=false。｜出處：rev3:memory/sea-orm-entity-datetime-feature-gate
- **L-072**｜jsonwebtoken 9 經 simple_asn1 把 time crate 拉進「真實」編譯圖（與 sea-orm 路徑那個永不編譯的惰性 time 性質相反），不 pin 時 cargo 解析到需 rustc 1.88 的 time 版本、在 pin 1.86 的 toolchain 上 build 硬失敗。
  防：遇 time 鏈 MSRV 衝突先 cargo tree -i time 判 real/inert：真在編譯圖就先 pin simple_asn1 0.6.3（放寬 time 需求下限）再 pin time 0.3.37，順序不可顛倒（反序 cargo update 直接失敗）；只經未啟用 feature 的惰性路徑則接受不 pin。｜出處：rev3:memory/jsonwebtoken9-msrv-time-real-graph
- **L-073**｜server crate 沒有 chrono 直接依賴，寫端 facade 要塞「現在時間」進 timestamptz 欄時 use chrono::Utc 不編譯——但也不必為此動 Cargo.toml。
  防：走 sea-orm 的 sqlx re-export：sea_orm::sqlx::types::chrono::Utc::now().into() 得 DateTimeWithTimeZone（prelude 只 re-export 型別別名、拿不到 Utc 建構子）；要 DB 端時間可用 Expr::current_timestamp() 但取不回更新後的 Model。｜出處：rev3:memory/seaorm-now-via-sqlx-chrono-reexport
- **L-074**｜初判「sea-orm DbErr 無乾淨路徑辨識 unique violation、只能 string-match 破壞封裝」是錯的——官方 DbErr::sql_err() 直接回 SqlErr::UniqueConstraintViolation（底層解析 SQLSTATE 23505），撞碼並發 race 守門「同業務拒、永不系統錯」就靠它。
  防：unique/FK 偵測一律用 sql_err() 在 handler remap 成業務錯誤碼；facade 保持回 DbErr 免層級倒置，txn rollback 傳回的原始 DbErr 在 handler 仍辨識得出。｜出處：rev3:memory/seaorm-sqlerr-unique-violation-23505
- **L-075**｜token rotation 這類狀態機寫端只靠冪等守門（UPDATE … WHERE status='active'）擋不住「撤銷穿插」race——pre-read 見 active 到上鎖之間鏈被撤，rows=0 被當良性照樣重鑄新 token、繞過撤銷。
  防：「讀狀態→決定→寫」的發放決策要在 FOR UPDATE 鎖住的列上重判（lock-then-redecide）、鎖住列已撤即拒；但非萬用——集合 toggle 且有 DB UNIQUE 兜底者（如 casbin policy 寫端）靠冪等＋unique violation rollback 已足、不需 FOR UPDATE。｜出處：rev3:memory/lock-then-redecide-toctou
- **L-076**｜casbin policy 寫端若走 enforcer MgmtApi（remove_filtered_policy/add_policies）＝改 in-memory＋adapter auto-save 旁路、審計非原子——這是前代被推翻並被 constitution 明禁的 anti-pattern；研究 agent 給的「MgmtApi 怎麼用」是 API 層知識、不等於專案 mandate。
  防：任何 policy 寫端一律 DB-first：facade 在同一 txn 直寫 casbin_rule 實體（含 protected 拒改、與操作日誌原子），寫後 enforcer load_policy 全量重載；設計前先讀 constitution 與設計權威的 casbin 寫入章。｜出處：rev3:memory/casbin-write-db-first-not-mgmtapi
- **L-077**｜研究與 spec 文件曾假設 casbin seed 沒有 button 維度、getUserInfo 的 buttons 回空陣列——實機驗證推翻：初始 seed 實有 16 筆 button 政策（超管角色佔 12 個 button code）與 83 筆 menu 政策，live 端點回真按鈕清單。
  防：推論按鈕/選單權限設計前先 psql 查 casbin_rule 實際維度分佈，別信文件「現空」的舊假設；code 對而文件錯時不必回頭改史料、但後續推論別再引用錯假設。｜出處：rev3:memory/casbin-seed-has-button-policies
- **L-078**｜host 無 rust toolchain，且 live smoke 測試共用 DB 資料表、多執行緒跑會互踩出偽失敗。
  防：rust build/test 一律在 rust-api dev 容器內 docker exec 跑，live smoke 帶 DATABASE_URL 並加 --test-threads=1 單緒。｜出處：rev3:CLAUDE.md§3-階段2；另 rev3:memory/live-ignore-tests-need-serial
- **L-079**｜live 測試對共享 seed 實體（如 seed 管理員角色）的操作日誌下絕對計數斷言（等於 1），隱含「我是唯一寫者」假設——別的 feature 經真 server 提交的審計列會累積、READ COMMITTED 下計數大於 1 偽紅；連補表名述詞也擋不住同表同 id 的累積污染。
  防：斷言「本測試自身寫了一筆」唯一可靠隔離＝本測試專屬 trace_id 過濾、或計數前後 delta，絕不用絕對計數。｜出處：rev3:memory/oplog-count-assert-nonidempotent-shared-entity-id
- **L-080**｜per-request access-log 中介層對每個已認證請求（含審計查詢端點自身的 GET）都寫一列 access log——spec 寫「查詢絕不產生新稽核紀錄」就與現實矛盾。
  防：「唯讀」端點只能宣稱不寫操作日誌、不主動自審，不能宣稱零 DB 寫；驗收的唯讀證只查操作日誌零新增（access-log 每查加一列屬基建預期、非污染）。｜出處：rev3:memory/audit-read-endpoints-not-db-write-free
- **L-081**｜Redis 快取的讀端（查命中）與寫端（set）若由兩個獨立函式各自渲染 key 字串，IPv6 canonical/expanded、CIDR /32 與 /128、格式差異會讓讀端永遠 miss——快取靜默失效、無任何 error，單看讀端或寫端的測試都是綠。
  防：讀寫兩端 key 一律由同一個 helper 導出；純函式測試斷言 write_key(x)==read_key(x)，live 驗收必含「寫端觸發→讀端命中→證明短路」的交叉軌。｜出處：rev3:memory/redis-cache-key-shared-helper
- **L-082**｜redis-rs 的 MultiplexedConnection 在 redis 容器 stop→start 後不自動重連，之後每個操作回 broken pipe、全走 fail-open 降級值，要重啟 rust-api 拿新連線才恢復——含 redis 重啟軌的驗收裡，排在後面的「需 redis 寫成功」斷言會假失敗。
  防：驗收把需 redis 寫成功的斷言排在 redis stop/start 之前；必須排後面就先 restart rust-api＋探針確認 key 寫得進去再續；log 大量 broken pipe＝連線斷未重連、非偶發錯誤。｜出處：rev3:memory/redis-multiplexed-no-auto-reconnect
- **L-083**｜vendored ip2region xdb crate 的初始化對缺檔是 .expect() panic（非 best-effort），xdb 資料檔不在時 boot 或 request path 直接炸。
  防：boot 先 guard 檔案存在才 init 並設 ready flag，middleware 只在 ready 時查 IP 歸屬、否則 region 給 None；prod runtime image 必須 COPY xdb 資料檔（dev bind-mount 會遮住這個缺口）。｜出處：rev3:memory/xdb-searcher-panics-on-missing-file
- **L-084**｜新增 rust workspace crate 時 prod 多階段 Dockerfile 實際要補四處 COPY（Manifest 段、Source 段、builder 產物 cp 到輸出目錄、runtime stage COPY 進 /usr/local/bin）——檔頭註解只寫兩處會誤導；漏後兩處時 docker build 照綠，只在 runtime 執行該 binary 才 exec not found。
  防：加 crate 的刀在 prod build 驗收必加 runtime binary 斷言（docker run prod image 列出該 binary 或走 entrypoint dispatch smoke），不可只靠 compose build 綠。｜出處：rev3:memory/rev3-new-crate-dockerfile-four-copy；另 rev3:CLAUDE.md§3-Phase1紀律
- **L-085**｜把前代多支 migration 的 seed squash 成一次性 INSERT 後，用「排序後 md5」比對 pg_dump 會同時掩蓋兩層問題：sequence id 落值真漂移（INSERT 順序沒對齊前代按 id 排序的終態）與 COPY 物理列序假紅（heap ctid 序經 UPDATE 移位、不可能用 INSERT 順序重現）。
  防：對 pristine dump 跑未排序逐列（含 id 欄）diff；normalize 規則把 COPY 段整列 sort 消物理序假紅、id 漂移則修 migration 的 INSERT 順序；並跑 negative test 證明比對不遮實質差異。｜出處：rev3:memory/seed-squash-rowid-drift
- **L-086**｜Cloudflare Tunnel 第三 ingress（cloudflared 繞過 nginx 直連 rust-api 內部 port）下，若 tunnel 信任網段沒有包含於內網信任預設清單，還原真實 client IP 的 header fallback 根本不會觸發——IP 存取控制閘刀（rev3-022）的實測 footgun。
  防：trust-model 設定裡 tunnel 段必須是內網預設段的子集，且只含 cloudflared origin、不放整個內網（防內網偽造 header）。｜出處：rev3:CLAUDE.md§8.2-ingress註（rev3-022 IP 閘刀）
- **L-087**｜供 UI 列表消費的查全表 facade 沒加 ORDER BY 時走 heap 實體序，任一列被更新後在頁面上位置漂移——靜態讀碼與單次 curl 都看不出，只有「更新後再看列序」的實測才現形。
  防：任何供列表/設定頁消費的 find-all 一律加穩定排序鍵；review 時把「無 ORDER BY 的全表查詢」列為缺陷候選並實測更新後列序。｜出處：rev3:REVIEW§3.1-F-2
- **L-088**｜寫端 handler 把 facade 的 no-op 回傳（目標列已消失、回 None）直接映成成功回應——實際沒寫入卻報成功；僅併發硬刪自身列的極端邊角可達，平時測不到。
  防：handler 對 facade 的 Option 回 None 一律轉 notFound 類業務碼，不得靜默映成成功；同族「no-op 假成功」模式列為 review 檢查點。｜出處：rev3:REVIEW§3.2-F-6
- **L-089**｜base-web axios 把未填的搜尋欄序列化成空字串 query 參數、serde 端收到 Some("") 而非 None，handler 沒守門就把空字串當真值過濾、曾致列表整頁變空；curl 手打的乾淨 query 完全掩蓋此 bug。
  防：handler 一律把空字串當「未設」（Option 濾掉空字串、enum/數值轉換把空字串映成 None），驗收必跑瀏覽器/CDP 軌，curl 測試刻意帶空參數模擬前端。｜出處：rev3:CLAUDE.md§3-Phase0研究紀律；另 rev3:REVIEW§2（012 列空字串守門 CDP 實證）＋rev3:CLAUDE.md§3
- **L-090**｜前端 axios 把未填的 search filter 送成空字串 query（如 ?entityId=），handler 的 Query DTO 數字欄若直接宣告 Option<i64>，axum 抽取層在進 handler 之前就整個請求 400（空字串 parse 不成整數）、頁面整掛——curl 乾淨 query 測不到，只有 browser/CDP 真送空參數才抓得到。
  防：query 來的數字/bool 欄一律 Option<String>＋parse 守門（空→None、合法→Some、畸形→業務錯誤碼），絕不直接 serde 成數字型；驗收刻意帶空參數、並跑 browser 軌。｜出處：rev3:memory/numeric-query-param-empty-string-400

## 〔前端／UI〕

- **L-091**｜flex-height 的 NDataTable 包進 NCard＋NTabs 後，NCard 內容區是 display:block、截斷 flex 高度鏈，table body 塌成 0px——分頁顯示「共 N 條」、列在 DOM 且文字齊全，但視覺整片空白；空表期潛伏、有資料才引爆，數 DOM 列數會誤判正常。
  防：診斷量 table body 元素的 getBoundingClientRect().height（0 即此 bug）、再沿祖先鏈找 flex 斷點；修法在頁面補回連續 flex-column 鏈（NCard content-style 改 flex＋各層 flex:1 與 min-height:0），子表元件不動。｜出處：rev3:memory/soybean-flex-height-table-in-ntabs-body-collapse
- **L-092**｜照抄 table 頁模板的頁 root class（min-h-500px flex-col-stretch overflow-hidden）用在卡片/表單類非-table 頁，內容一多就被裁在摺疊線下且無法下滾——table 頁靠 NDataTable 內部滾動所以正確，非-table 頁無內部滾動容器接手；內容少時潛伏無感、加項目後才引爆。
  防：非-table 頁 root 改 flex-col-stretch gap-16px（去掉 overflow-hidden 與最小高度），讓 layout main 接手滾動、別動既有 table 頁；診斷用 CDP 沿祖先鏈找 scrollHeight 大於 clientHeight 且 overflow hidden 的裁切層。｜出處：rev3:memory/soybean-page-root-overflow-hidden-clips-nontable
- **L-093**｜新增 base-web view 後，4 個 git-tracked route 檔（elegant-router 的 imports/routes/transform＋route 型宣告）要等 running dev server 掃描時才重生、不在建檔當下——implementer 建完立即 git status 看不到而誤報無變動；漏 commit 則 fresh checkout 該頁不可達、漏補 route i18n 鍵則兩語系字典 typecheck 紅。
  防：建 view 後 restart base-web 觸發重生，git status 見 route 檔變動就連同 view 一起 commit、同 commit 補兩語系 route 鍵、typecheck 綠才算完；i18n 改動要在 running app 驗收（CDP）前也必先 restart，否則 vite stale locale 分不清 source 缺漏還是快取。｜出處：rev3:memory/base-web-elegant-router-regen-on-new-view
- **L-094**｜只把後端業務錯誤碼譯文加進 locale 字典、沒同步擴 typings/app.d.ts 的 I18n Schema 型，locale 字典因 excess-property 直接 typecheck 紅——i18n 接線三範圍（攔截器/字典/Schema 型）最常漏第三個，每個加業務譯文鍵的切片都會遇。
  防：先擴 Schema 型再加 locale 譯文、兩者同 commit 且鍵集完全對齊（任一側單獨 commit 都 typecheck 紅）。｜出處：rev3:memory/base-web-i18n-schema-iii-gotcha
- **L-095**｜base-web 在 alpine（musl）dev 容器內 git commit 被 simple-git-hooks pre-commit 擋死——oxlint 缺 musl native binding 直接 crash、加上 upstream 既有 eslint error，失敗與本次改動無關。
  防：base-web commit 一律 --no-verify（環境缺陷、非偷懶），改為獨立自驗：容器內跑 pnpm typecheck 確認無新 type error；修 hook 工具鏈屬 scope creep 不做。｜出處：rev3:memory/base-web-precommit-hook-broken-in-alpine；另 rev3:CLAUDE.md§3-階段2
- **L-096**｜base-web view 首次使用某個 naive-ui 元件時，dev 容器的 unplugin-vue-components 會自動重生 git-tracked 的元件型別宣告檔，漏 commit 它會讓 fresh checkout（無 dev server）缺全域型別、typecheck 失敗。
  防：第一段 commit 前在 base-web 內 git status 檢查元件型別宣告檔有無變動，有就與引入元件的 commit 一起 add（只有全新元件才觸發）。｜出處：rev3:CLAUDE.md§4.1

## 〔CDP／mock 驗收〕

- **L-097**｜CDP 連線用截短的 page id（非完整 32 字元 hex）時，WebSocket 直接 reject、close 1006 且 error message 為空、無從診斷。
  防：從 targets 列表取完整 32 字元 id，篩 type=page 加目標 URL。｜出處：rev3:000-bootstrap§3.1
- **L-098**｜瀏覽器內部頁（edge:// 、chrome:// ）不可 CDP attach，對新開 tab 直接連會失敗。
  防：新 tab 先 navigate 到任一 http URL 再 attach，並注意 navigate 後 page id 會換。｜出處：rev3:000-bootstrap§3.1
- **L-099**｜CDP 的 targets 列表列出所有 targets，腳本操作的 tab 不一定是 user 親眼看的那個、雙方各看各的狀態。
  防：讓 user 開一個專用 tab 供自動化操作，選 target 時比對 URL。｜出處：rev3:000-bootstrap§3.1
- **L-100**｜CDP browser smoke 走 login-form 自動化很 flaky；且 localhost 與 127.0.0.1 是不同 origin、localStorage token 不共享，origin 混用時注入的 session 白做。
  防：curl 打登入端點取 token→CDP 把 JSON-stringify 的 token 寫進 localStorage 的 SOY_token（前綴來自 VITE_STORAGE_PREFIX）→navigate 到 front-nginx 整合路徑，全程鎖同一 origin；CDP 專驗 curl 抓不到的「頁面真的 render、i18n toast 在地化」。｜出處：rev3:memory/cdp-session-inject-soy-token；另 rev3:000-bootstrap§3.1
- **L-101**｜apifox 雲端 mock 有四坑：不帶 apifoxToken header 回 HTTP 500 內包 401；取用戶路由無 Bearer token 回「用户已失效」、refreshToken 給 dummy 值回錯誤；連打觸發頻率限制回 5xx；限流時 login 顯 timeout toast 但請求常在背景完成並跳轉
  防：打 mock 帶齊 header/token、限流時間隔重試、驗收以頁面實際跳轉為準而非 toast｜出處：rev3:superpowers/000（雲端 mock 段）

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
