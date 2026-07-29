<!-- next: L-183 -->
# LESSONS — 教訓 registry

一教訓一段（`L-NNN｜坑＋防法`）、append-only；配號取檔頭 next-id 後 bump、號碼永不回收。
單卷逼近 25k tokens 時分卷（切出整段舊號封存為 `LESSONS-<起迄號>.md`、主檔續寫、L 號跨卷連號）。
L-001~L-101（rev3 教訓種子全量）☞ LESSONS-001-101.md。
L-102~L-150（rev4 波 0～018 治理硬化）☞ LESSONS-102-150.md。

## 〔環境與工具鏈（WSL2／docker／cargo／vite）〕

- **L-153**｜macOS 於 UTF-8 locale 下，bash 把「$var 緊鄰全形字元」的全形首 byte 吞進變數名（libc 字元分類差異；set -u 下炸 unbound variable、無 -u 則靜默展開空；系統 bash 3.2 與 homebrew 5.3 同炸；WSL2/glibc 不受影響）——shell 腳本 $var 緊鄰非 ASCII 一律寫 ${var} 形；臨時繞法 LC_ALL=C（L-142 同族）。2026-07-19 tools/bootstrap:30 實證（RUNBOOK 驗證輪 macOS）。

- **L-168**｜docker `-t`（容器 pty）互動程式＋stdout 重導向＝三重雜訊同流入檔：①提示行寫進重導向檔而非螢幕（pty 驅動監看 pty 流永遠等不到提示＝結構性 hang；互動 user 則盲打）②ANSI 清行序列（ESC[F ESC[K）黏在首資料行 ③全輸出被 pty ONLCR 改 CRLF。而改用 `-i` 無 `-t` 想繞開＝sops 之類 term.ReadPassword 對 pipe stdin 直接失敗（rc=128、吵鬧不 hang——此半邊反而是 P1.2 要的性質）。另 sops 加密時 `--age` **不能**繞過 `.sops.yaml` 規則比對：config 存在且 path 不匹配→`no matching creation rules` 即使帶 `--age`（實驗性加密須 `--config` 指到臨時 catch-all 規則檔）。
  防：捕捉互動容器 stdout 前先假定「提示＋ANSI＋CRLF 與資料同流」——拆資料一律 `tr '\r' '\n'`＋剝 CSI 序列＋只認資料行形（deploy/decrypt-secrets.sh 的 key 行 parser 即此形）；pty 盲餵驅動改監看**重導向目標檔**出現提示字樣再餵（勿監看 pty 流）；臨時加密實驗帶 `--config` 臨時規則檔。｜出處：019 U3（T022 施工實測；probe 全程見 tasks T018／T022 備註）

- **L-170**｜「只認 `key: value` 行」的自製 YAML 逐行拆解，只在值恰好是**裸量純量**時正確——sops（go-yaml v3）對不能當裸量的值改吐引號形／區塊純量形，拆出來的是**含引號字元的原樣 token**，逐字寫檔即靜默壞值：2026-07-29 sops v3.13.3-alpine 真容器實測＝空字串吐 `""`（2 byte，還會**架空**「值為空」那條斷言，因為 `""` 非空）／含「冒號空白」吐 `'a: b'`（多 2 byte 引號）／含「井號」吐 `'v #f'`／前後帶空白吐 `'trail '`／含換行吐 `|-` 加縮排續行；反之以 `- : ~ =` 等開頭者仍是裸量、拆解正確。下游 preflight 只測 `-f`／`-s`，2 byte 壞檔照樣放行。**同族第二坑**：容器 pty 是**單流**（stdout 與 stderr 同流入捕捉檔），故失敗分支把捕捉檔整份倒進 stderr＝明文洩漏面——「解密失敗就不含明文」只是 sops 正常錯誤路徑（MAC 檢查早於 Emit）的性質、**不是腳本自己的保證**，已 Emit 後才死（寫入失敗／SIGINT）即整份明文上終端與日誌；程式碼裡寫「不含明文」的**註解不是防護**。**第三坑（驗證側）**：以 `script(1)` 開 pty 驅動時，若其 stdin 已 EOF，pty 會把 Ctrl-@ 回顯成**字面兩 byte `^@`**（0x5e 0x40，非 NUL——`cat -A` 顯示相同、必須 `xxd` 才分得出）黏在首資料行前，害首個 key 不匹配而報「缺 xxx」，且隨無關的腳本改動時有時無、極像 Heisenbug。
  防：①值形制一律**斷言而非猜測**——首字元落 `" ' | >` 四者即 fail-loud 指名（零依賴、不誤傷任何裸量值），把靜默壞值翻成吵鬧失敗；②任何「把捕捉檔倒給人看」的失敗分支，倒出前先濾掉 key 行**及其縮排續行**（區塊純量形的承載面），只留診斷訊息；③pty 驅動測試把 stdin 撐開（如 `sleep N | script -qec …`），並以 `xxd` 而非 `cat -A` 判前導雜訊；④改動前先跑**對照組**（同一 harness 餵 `git show HEAD:` 版本），才分得清「我改壞的」與「harness 假象」。｜出處：019 U3 quality 第 1 輪 blocker 修復（隔離沙箱＋暫代 age 金鑰＋假值探針，全程未觸真機密）

- **L-171**｜「明文落點」盤點必須連**暫存／捕捉檔**一起算，否則消滅暴露面的整條需求會被自己的暫存檔架空：decrypt-secrets.sh 把 8 支完整明文以 `mktemp -d tmp/…` 落在 repo 內，而 repo 在 /mnt/d（v9fs）上——`umask 077` 與 `chmod` 皆結構性 **no-op**（實跑 `ls -ld tmp`＝`drwxrwxrwx`），等於實效 777、Windows 側可見，且 SIGKILL／當機時**持久殘留**（SIGINT／SIGTERM 會跑 EXIT trap、SIGKILL 不會）。三個讓它躲過審查的措辭陷阱：①**「gitignored」只擋 git 入庫、不擋檔案系統暴露**；②**「trap 即刪」只覆蓋可捕捉訊號**；③同一支腳本上方才為 `SECRETS_DIR` 承認並 WARN 過 9p 的 chmod no-op 性質，**局部承認沒有推及全檔**。更隱蔽的是**方向套錯**：契約寫「暫存明文必須落 repo 內（wrapper 只掛載 `$PWD`）」，那只約束**要餵回容器加密的輸入檔**；由 host shell 重導向產生的**解密輸出**不受此限——把單向限制當雙向讀，會把本來可修的洞鎖成「設計如此」。
  防：①凡會寫出明文的路徑（落點檔＋暫存＋捕捉＋診斷倒帶）逐一列落點清單，判準用 `stat -f -c '%T'`（fs）與 `stat -c '%a'`（mode）**機判**，不接受 gitignore／trap 之類的口頭保證；②落點性質**斷言 fail-loud 且早於解密呼叫**——不合格時連一 byte 明文都還沒產生（本例：fs 為 `v9fs` 或 mode≠700 即 `exit 1`）；③容器 wrapper 的掛載限制一律拆「進容器的輸入」與「host 收的輸出」兩個方向討論再引用；④驗證落點不必真解密：stub 掉 `sops.sh`、在 stub 內 `exec 9>&1` 後 `readlink -f /proc/self/fd/9` 即可機判 RAW 的真實路徑（★**不能**直接 `readlink /proc/self/fd/1`——該命令自身的 `> probe` 重導向已把 fd1 換掉，量到的是 probe 檔本身＝假結果），再加「對照組跑 `git show HEAD:` 版」即可證明修前修後落點差異。｜出處：019 U3 quality 第 2 輪 blocker 修復（隔離沙箱＋stub sops＋假值，全程未觸真機密）

## 〔review／驗收方法論〕

- **L-169**｜權限／owner 之類「終值型」契約不變式，happy path 綠不代表成立——腳本自陳的**補救指示**是另一條會改變終值的路徑：decrypt-secrets.sh 正向寫出 644 全過，但差異守衛的 `.new` 給 600，而 WARN 教人 `mv .new` 蓋回（同 fs＝rename、**mode 原樣保留**、非重建檔），落點檔終值遂成 600、違反 P4.7／FR-022，且只在開 obs／metrics 軌時才炸（grafana 472／postgres-exporter 65534／redis-exporter 59000 全 Permission denied）＝延遲且遠離現場的爆點。
  防：①凡契約寫「終值必為 X」，驗收要沿**腳本自己印出的每條補救／分支路徑**各走一遍量測終值，不只主線；②暫存／staging 檔（`.new`／`.tmp`／`.bak`）的 mode 一律設成**落點檔的終值**，別預設「暫存就該更緊」——`mv`／`rename` 不會替你重算 mode；③這類缺陷用隔離 fs 沙箱＋stub 掉互動相依（此處 stub `sops.sh`）即可機判複現，不必真跑完整解密。｜出處：019 U3 spec review 第 1 輪（deploy/decrypt-secrets.sh `.new` 600→644）

## 〔後端／DB／redis〕

- **L-154**｜postgres 官方映像容器內 psql -h 127.0.0.1 走 pg_hba 預設 trust＝密碼不參與認證（錯密也回成功）——容器內密碼自驗必走 -h <服務名> 容器網段（scram-sha-256）才真驗密；任何依 loopback 的密碼自驗設計都是假驗。2026-07-19 deploy/setup-reaper-role.sh 自驗實證（RUNBOOK 驗證輪 macOS）。

## 〔CDP／mock 驗收〕

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

- **L-166**｜施工中途發生的併問拍板，就近記進當時正在編輯的 tasks、事後才以「引用」節補進
  ADR＝製造**循環錨＋逐字鏡像**：019 的產鑰儀式拍板（C 案）在 T002 釘版呈報時併問拍定，
  ADR 0080 寫「正式鑰產製走 C 案（tasks T019 註記為權威）」，而 tasks T019 同段末寫「誠實
  記入 ADR-B」——兩處互指對方為權威，讀者無從裁決何者為準；且兩段除末句外近乎逐字相同
  （暫代鑰全自動施工／收刀親產真鑰加人四步＋撤銷四步／passphrase 視同已洩露），拍板一改
  就要兩處同步、漏一處即失真（CLAUDE.md：每個事實只有一個人寫的家，鏡像不是機器生成、
  就是不存在）。危害不只是體例：此拍板屬**安全後果級**（暫代鑰視同已洩露、收刀有撤銷與
  7 支 leaf 輪替的硬性義務），而唯一自稱權威的落點是 task 清單——task 勾完即失去閱讀動機、
  收刀後幾乎不再被讀，義務會隨清單一起沉底；ADR 才是收刀後仍被讀的產物。
  防法：①拍板一律先落 ADR 決策節並**明寫「本決策 N 即此拍板唯一權威落點」**，tasks／RUNBOOK
  只留一行指路（檔名＋節號＋本任務範圍界線，依 L-164 全寫不裸引）；②中途併問的拍板當回合
  即補 ADR，**不得用「引用」節形式帶過**——「引用」節就是鏡像的偽裝，命名騙過了自己；
  ③跨檔權威宣告只能單向，被指方**不得回指**，自查法＝對拍板關鍵詞跑 `docs-sync.py errata`，
  兩份以上文件出現同義段落且各自帶「為權威／記入」字樣即為循環錨；④判斷落點時問「這份文件
  在收刀後還會被讀嗎」，答否者不得作為權威落點。
  ｜出處：2026-07-29 019 U2 quality 第 2 輪（改法＝ADR 0080 新增決策 5 收拍板全文並宣告唯一
  權威、刪去原「儀式拍板引用」節，tasks T002／T008／T019／T034 四處改為指路；errata
  「儀式拍板」4 處／「暫代」7 處／「視同已洩露」2 處逐處核為單一權威落點或指路）。

- **L-167**｜當回合新立的 lesson 只套回「觸發它的那一個樣本」：L-166（拍板收歸 ADR 唯一權威、
  tasks 只留指路）在 019 U2 quality 第 2 輪立案並就地施工，卻只治了觸發樣本「產鑰儀式拍板」；
  同一份 `tasks.md` 裡體量更大的**主拍板**（user 重拍三點定案）仍與 ADR 0080 該節近乎逐字
  鏡像（「跨 git 歷史與未來輪替的根信物」「at-rest 代價＝明文長駐 ext4.vhdx」等句兩處並存），
  下游八處還寫「詳 T005 備註與 ADR 0080」＝雙頭權威。漏掃之因是**自查母體取自觸發樣本、
  而非取自類別**：第 2 輪的 errata 只跑「儀式拍板／暫代／視同已洩露」三詞，全是儀式拍板自己
  的詞彙，另一個拍板天然掃不到。與 L-156（只修被點名那一處）同族但更隱蔽——L-156 漏的是同一
  錯值的複本（關鍵詞共用、grep 掃得到），這裡漏的是**同一規則的另一個適用對象**，兩者無共用
  字串。防法：①新立 lesson 的當回合，自查母體是**類別枚舉**而非關鍵詞——「本刀有哪些 user
  拍板」的現成 registry ＝ ADR front-matter `provenance` 欄（0080 該欄同時列著「user 重拍
  三點定案」與「user 產鑰儀式拍板 C 案」，逐項核對即會命中漏網者）；②出處行要記**掃描母體
  與逐項結論**、不只記跑過哪幾個關鍵詞（母體不全才是失效點，只列關鍵詞看不出來）；
  ③同型多例時先治體量最大者、再治觸發樣本——先治小的容易誤判「已收斂」。
  ｜出處：2026-07-29 019 U2 quality 第 3 輪（母體＝ADR 0080 provenance 欄之兩項 user 拍板：
  儀式拍板＝第 2 輪已收歸決策 5、重拍三點定案＝本輪收歸「決策」節 1~3 與其理由段並宣告唯一
  權威；改法＝tasks T005 改指路一行＋任務範圍界線，`tasks.md` 3 處／`spec.md` 3 處／
  `plan.md` 1 處／`data-model.md` 1 處共八處「T005 備註與 ADR 0080」全改為單指 ADR 節號）。

- **L-172**｜docker inspect 的 Mounts.Source 是 compose 專案 working_dir 的**邏輯路徑**、
  不是物理路徑：本機以 `/home/anew/x_Project`（symlink → `/mnt/d/AnewSpaces/x_Project`）
  起過 compose，遷移前 secret 掛載 Source 就顯示 `/home/anew/x_Project/...`——對「來源皆非
  /mnt/d」的驗收做字面 grep 會**在遷移前就全綠**（假陰性），驗收形同虛設。防法：判「來源
  已離開 9p」必以 host 側 `readlink -f` 把每筆 Source 物理化後再比對前綴（物理路徑落
  `/mnt/d/*` 即紅），且逐容器逐 mount 列證、不抽樣；與閘 #11 的教訓同族——Mounts JSON
  同形不代表定址語意相同，字面相符不是證據、物理解析才是。
  ｜出處：2026-07-29 019 U4 T030 步驟④施工前偵察（遷移前 rust-api 之 5 筆 secret Source
  全顯示 symlink 邏輯路徑、字面不含 /mnt/d；步驟④遂以 readlink -f 物理化斷言落地，
  遷移後 14 容器 12 筆 secret mount 全數物理落 ext4）。

- **L-173**｜bind source 檔「刪除重建」（新 inode）後，既存容器**不會**因 up 而重掛：
  running 容器抓著舊 inode 照常跑（值同無感）；**已 Exited 的 oneshot 服務**（migrate）
  下次 `up` 要重新 start，其 Docker Desktop bind-mount 快照路徑（docker-desktop-bind-mounts/
  …）已隨舊 inode 消失 → mount 直接 fail（`no such file or directory`）、服務起不來——
  ＝contracts §P6 否定契約「bind 到已刪 inode、下次重啟才炸」的實證形，且 `up -d` 對
  config 未變的服務只 Start 不 Recreate、絕不會自癒。防法：任何「清空落點→重解密」之後，
  凡是**在清空前就存在**的容器（含 Exited 的 oneshot 與 stopped 的 profile 件）一律
  `up -d --force-recreate`（或 down→up）重建 bind；只驗 running 件健康＝漏掉停著的地雷，
  下次 profile 起用或重啟才炸。
  ｜出處：2026-07-29 019 U4 T039 乾淨重建（清空 $SECRETS_DIR 重解密後 up：5 業務件
  running 健康、migrate start 即炸 mount error；--force-recreate 6 業務件＋8 觀測件後
  全綠，pg_up／redis_up 復 1）。

- **L-174**｜**落點類設計變更的「消費者清單」漏一支＝該防線靜默失效且全綠**——019 把機密明文落點
  自 repo 內遷至 `$HOME/.cache` 時，契約 §P5.2 的同刀齊改清單只列了三支 shell 腳本
  （後補至四支），漏掉第五消費者 `tools/secret-value-guard.py`（三層掃描防線的確定性層）。
  該工具只讀環境變數 `SECRETS_DIR`、不解析 repo 根 `.env`，而 git hook 純繼承呼叫端 shell
  環境、**不會有人替它 export**——遷移後 pre-commit 每次都走「目錄缺席→skip→rc=0」那條
  fail-open 路徑，於是 FR-007／US1 情境 4／SC-001 裸值格**結構性失守卻全綠**（樣式層對裸值
  本就不中＝契約明訂預期，這一格只有值比對能守）。
  ｜防法：①**落點／路徑類變更動手前先枚舉全部消費者**（`git grep` 該常數名與其預設值字面
  ＋掃 hook 與工具面，不只看 contracts 既有清單——清單本身可能就是漏的）②消費者清單寫進
  契約時附「漏列即靜默失效」的後果句，讓下次讀者知道那不是裝飾③**fail-open 的層級必須有
  「我這次真的在守」的正向證據**：skip 是合法設計，但收單前要用端到端反證（構造裸值 staged
  探針→必須 rc≠0 且指名）證明它沒在恆 skip；④驗完務必 `git prune --expire=now` 清物件庫
  （L-158）。｜出處：2026-07-29 019 U4 spec 審抓出（實證：`env -u SECRETS_DIR … check` 印
  skip 且 rc=0；修＝補與四腳本逐字同口徑的三級解析〔環境變數→`.env` 只嚴格解析該一行、
  非法值吵鬧失敗不靜默回退→回退 `deploy/secrets`〕＋7 案單元測試，端到端反證回 rc=1 指名）。

- **L-175**｜**「設定檔讀值」的兩支解析器只要偵測面不等寬，窄的那支就會靜默回退到舊行為**——019
  把落點 `SECRETS_DIR` 寫進 repo 根 `.env` 後，compose 用自己的 dotenv 解析器讀，六支自寫
  消費者（四支 deploy 腳本＋`tools/secret-value-guard.py`＋`tools/bootstrap`）用 `grep
  '^SECRETS_DIR='` 讀。compose 那支接受 UTF-8 BOM／行首空白／`export ` 前綴／等號兩側空白
  ／CRLF 行尾，窄樣式對前四形一律**漏認並靜默回退**舊落點（`rc=0`、零訊息）：compose 掛得到
  新落點、容器跑得動、operator 毫無異狀，唯獨 pre-commit 的裸值比對層從此掃空目錄恆 `skip`
  （＝L-174 才剛關掉的失守面經另一條路復發），且 decrypt 會把 8 支明文寫回 repo 內 `/mnt/d`
  舊落點（9p、chmod no-op、實效 777）。CRLF 形更是四支腳本 FAIL（訊息還指稱「空白／shell
  元字元」＝與真因不符）而 guard 與 compose 正常採用的 4:1 分裂。★補償控制當時也不成立：
  bootstrap 同用窄樣式，其 warn 文字「compose 將回退（保護失效）」與實測相反，等於用錯誤
  診斷把人導離真因。｜防法：①**寬進窄出**——偵測樣式必須寬到涵蓋權威解析器接受的每一種
  行形（撈出「對方會讀到的那一行」），值校驗才收窄成嚴格白名單；漏認一形＝多一條靜默回退
  路徑，而回退恰恰是「看起來全綠」的那個方向 ②同一組語料跑**三方矩陣**（權威解析器／自寫
  shell／自寫 python）逐案對答案，任一案分裂即 blocker——單支自測全綠證明不了跨支一致
  ③錯誤訊息要能指向真因：CR 既非空白也非 shell 元字元，卻被歸進那條訊息＝診斷失真
  ④「非法值吵鬧失敗」的紀律若只套在**值**上、不套在**行形**上，等於留了個靜默後門。
  ｜出處：2026-07-29 019 U4 quality 審抓出（實證：compose v5.3.1 六形皆解析為新落點，窄樣式
  四形回退舊落點 rc=0；修＝六處同刀改寬樣式＋guard 4 案單元測試〔退回窄樣式即 3 紅〕，
  八形三方矩陣逐案同解）。

- **L-176**｜**寫檔守住 byte-identical，讀取比對卻用命令替換＝不變式在比對面破功**——019 機密檔
  一律 `printf '%s'` 寫入（零尾端換行）並立 CR 護欄，但 preflight 的 composite↔leaf 一致性
  與 generate 的 dual-write drift 判定都用 `[ "$(cat f)" = "$v" ]`：命令替換會剝掉尾端換行，
  於是「檔尾多一個 LF」這一格對兩者**結構性失明**——實測 `redis_password.txt` 尾多一個 LF
  （15 byte、健康值 14 byte）時 preflight 仍回「齊備且健康、可 up」`rc=0`，compose 卻會把
  15 byte 密碼掛進 redis、把內嵌 14 byte 版本的 `redis_url` 掛進 rust-api＝認證必失敗而
  上機前的 fail-loud 承載者放行；generate 同情境印 SKIPPED、劣化不修復。尾端換行正是編輯器
  覆存最常見的產物（與 CRLF 同一個編輯器、同一次覆存），而護欄當初只立了 CR 那一半。
  ｜防法：①位元組不變式的檢查也要走位元組——`printf '%s' "$v" | cmp -s - "$f"`，不用
  `$(cat)` 字串相等（decrypt 當時已是這個形，是三支消費者裡唯一真的在驗位元組的）
  ②護欄要對著**不變式**寫、不要對著**單一已知劣化樣本**寫：CR 護欄的判準若寫成「零換行
  字元」（`stat -c %s` ＝ 剝除 CR／LF 後 byte 數），LF 這格從一開始就在射程內
  ③fixture 的劣化樣本要跨形取樣（尾附字串／尾 CR／尾 LF／中段換行），只測一種就只守一種。
  ｜出處：2026-07-29 019 U4 quality 審抓出（修＝preflight 加 LF 護欄、preflight 與 generate
  比對改 `printf | cmp`；機判＝尾 LF 組 rc=1 指名、尾 CR 對照組維持原訊息、真 drift 組仍抓、
  generate 連動重寫至與健康對照組同 sha256 前 8 碼且重跑冪等）。

- **L-177**｜**「未設」與「已設為空」是兩種狀態，`${VAR:-default}` 與 `[ -z "$VAR" ]` 對它們的
  判讀恰好相反**——`SECRETS_DIR` 匯出為空字串時，compose 因 shell 環境勝出 `.env` 而直接吃預設
  值回退舊落點、根本不讀 `.env`；五支自寫解析器的 `[ -z ]`／python `if val:` 卻當「未設」續讀
  `.env` 取新落點。兩邊都有答案、都 `rc=0`，分裂全靜默：實測 preflight 印「可 up」rc=0、guard
  rc=0，而 `compose config` 全指向遷移後零 `.txt` 的舊落點（`up` 遂在該處建空目錄當 secret 掛
  入）。同族 L-175／L-176 同因：只驗典型輸入、未逐格驗狀態空間邊界。｜防法：①「環境變數→設定
  檔→預設值」口徑至少三格（未設／已設非空／**已設為空**）逐格與權威解析器對答案；②bash 判有無
  設定用 `${VAR+set}`、判空用 `-z`，分開寫（python＝`is None` 與 `== ""`）；③邊界格無合法用途
  者一律吵鬧失敗＋自癒指引——靜默選一邊必有一半機率與權威分裂，且分裂方向恰是全綠那邊；④三方
  矩陣語料須含空值格。｜出處：2026-07-29 019 U4 quality 審（修＝五處同刀加前置守衛；機判＝空
  字串組四腳本＋guard 全 rc=1 指名〔decrypt 於 pty 實跑〕、unset 對照組三方同解、guard 41
  tests OK 移除守衛即紅）。

- **L-178**｜**相對路徑的「錨定基準」不一致＝同一個值指向兩個目錄、雙方各自全綠**——019 落點
  `SECRETS_DIR` 允許以環境變數覆寫，五支消費者對**絕對值**行為一致，但值為**相對路徑**時
  分裂：compose 以**專案目錄**（＝repo 根）解析、`secret-value-guard.py` 以 repo 根 `join`、
  `decrypt`／`setup-reaper-role` 因先 `cd` 或斷言 CWD 而等價，唯 `generate`／`preflight`
  逕用相對值＝**以 CWD 錨定**。於是自 repo 子目錄執行時，preflight 檢查 A 目錄印
  「齊備且健康、可 up」`rc=0`，compose 卻掛 B 目錄（零檔、`up` 自動建空目錄當 secret 掛入），
  generate 更把 11 支明文寫進 CWD 相對目錄——落回 `/mnt/d` repo 樹內，而值比對層錨定 repo 根
  掃不到＝L-174 型假綠經第三道門復發（FR-021／SC-005 與 SC-001 同時受損）。
  ｜防法：①**凡「路徑類設定」必在契約明訂錨定基準**（本刀＝repo 根、非 CWD），並在每支
  消費者以 `case "$V" in /*) ;; *) V="$ROOT/$V" ;; esac` 顯式正規化——**依賴「CWD 恰為 repo
  根」或首行 `cd` 屬隱性保證**，斷言或 `cd` 日後被動即靜默改變落點；②驗收要以**多方矩陣**
  跑（每支消費者 × 值形態〔絕對／相對／空字串／純空白〕），單支自測全綠證明不了跨消費者
  一致；③矩陣的判準是「**所有消費者解析出同一路徑**」，不是「每支各自 rc=0」。
  ｜出處：2026-07-29 019 U4 quality 審第 4 輪（實證：`cd deploy && SECRETS_DIR=rel/dir` 下
  preflight 修前指 `deploy/rel/dir` 假綠、修後與 guard、compose config 三方同指
  repo 根 `rel/dir` 並正確 FAIL 指名缺檔；四支 `bash -n` 綠、`.env` 正常路徑零回歸）。

- **L-179**｜**自動化「互動式解密」時，「等提示才餵」與「盲餵」各有一個坑，兩個都會咬人**——
  019 撤銷演練以 pty 驅動 `deploy/decrypt-secrets.sh`：①**等提示才餵＝必然 timeout**。腳本把
  sops 的 stdout（提示行與解密輸出**同一條容器 pty 流**）重導向進暫存檔，pty 流上因此**永遠
  不會出現** `Enter passphrase…`；以該字串當觸發錨的驅動器就一直等到自己的 deadline，看起來
  像「解密卡死」，實際是**觸發錨選在一條被重導向的流上**。②改盲餵（以腳本自己印的預告行為
  錨）解決 timeout，卻踩第二格：預告行是 **host shell** 印的、此時容器還沒接管 tty，寫進去的
  字元被 host 行編輯**回顯**——passphrase 於是以明文留在捕捉檔與畫面 scrollback（實測同一支
  驅動器的 `ECHO_LEAK` 欄位由 0 變 1；換成容器已接管後才餵的呼叫則恆 0）。
  ｜防法：①判斷「提示是否看得到」以**該流有沒有被重導向**為準，別用「互動程式總會印提示」
  推定；②盲餵的捕捉檔一律**視同機密**（700 目錄、驗畢即刪），且驅動器要有 `ECHO_LEAK`
  之類**機判欄位**（捕捉檔中 passphrase 出現次數）——只看畫面看不出回顯；③這條同時是**操作面
  結論**：真人操作也一樣，搶在容器起來前打字就會把 passphrase 打在畫面上——RUNBOOK §15 已
  收錄「等容器起來再輸入」的提醒。｜出處：2026-07-29 019 U5（T033 撤銷演練；首次呼叫
  timeout 120s 零寫入、改盲餵後 rc=0／8 支 WRITTEN／零 `.new`）

- **L-180**｜**修掉「錯誤前提」的程式實例，不等於修掉那個前提**——同語意句子散在契約與手冊
  各處，程式面全綠會讓人以為整條收工：019 U3 已把 `deploy/decrypt-secrets.sh` 的暫存明文遷出
  repo 內 `tmp/` 並補 fail-loud 落點斷言（L-171），但 RUNBOOK §15.7 merge 衝突程序仍逐字寫著
  「暫存明文**必須落 repo 內**——wrapper 只掛載 `$PWD`」，等於**用手冊指示營運者去做腳本剛剛
  拒絕的事**（該步驟的檔由 host shell 重導向產生、根本不進容器，那個理由對它不成立；repo 根
  實測 `v9fs`、`tmp/` 實測 `drwxrwxrwx`）。機器擋不到——只有讀者照著做才引爆。
  ｜防法：①「某某必須落 X」這種**帶理由的限制**，勘誤時要連「**理由在每個引用點是否成立**」
  一起判，`tools/docs-sync.py errata` 枚舉出的每一處都要逐處給結論、不可只改被 review 點名那
  一處（本例四處：RUNBOOK §15.1 `set --value-file` 值檔＝成立、§15.7 步驟 1＝**不成立**、
  §15.7 步驟 3 `merged.yaml`＝成立、`contracts/secret-pipeline.md` **§P7**「合併衝突」列＝敘述過寬
  〔★**已結清**：2026-07-30 commit 23a3846 改為落點兩分、原無條件敘述標作廢；★本行原寫「contracts
  §P4」＝L-164 所禁的懸空錨點（§P4 是解密管線契約、表列僅 P4.1~P4.7、無合併衝突列），同刀勘誤，
  漏認原因見 L-181〕）；②程式面補完 fail-loud
  守衛後，立刻反向搜「手冊有沒有教人走那條剛被擋掉的路」。｜出處：2026-07-29 019 U5
  （spec 第 1 輪 blocker；e5b4967 修完程式面之後手冊面仍存活）

- **L-181**｜**用自己拼的窄樣式 grep 去證明「全 repo 零殘留」，證到的只是那個樣式**——019 U5
  把 contracts 錯編號 `§P4`→`§P7` 同刀勘誤（23a3846）後，以 `git grep '§P4「合併'` 得 rc=1 即
  宣告零殘留；實際漏掉第四處，且就在同刀教訓 L-180 自己的防法①枚舉裡——那行寫的是
  `contracts §P4 合併衝突列`（**不含全形引號**），樣式差一個標點就漏認。放寬一格
  （`git grep -nE '§P4[[:space:]]*合併'`）或直接跑 CLAUDE.md §4 指定的枚舉器
  （`tools/docs-sync.py errata '合併衝突列'`）都立刻命中同一行。第二層原因是**枚舉範圍漏掉自己**：
  勘誤的來源就是 L-180，寫的人不會回頭搜自己剛寫下的段落，於是「錯編號」與「已結清」兩件事在
  該段同時失修。｜防法：①宣稱「全 repo 零殘留／零命中」一律以 `tools/docs-sync.py errata
  <關鍵詞>` 的計數為準，關鍵詞取**不含標點的語意核心**（用「合併衝突列」，別用夾全形引號的
  `§P4「合併`），自拼 grep 只當補充；②同刀勘誤的枚舉範圍必含**本次新寫／剛改的正文**（教訓
  條目、tasks 備註——commit message 屬 git 史不追改）；③錯編號類勘誤收尾反向核一次被指節
  （`grep -n '^## '` 對照該節表列），確認新指標確有那一列，此即 L-164 防法②的機判形。
  ★**本條與 L-180 勘誤註記為求可重現而逐字引用錯誤原字串**，故 `errata '合併衝突列'`／
  `'§P4'` 會在此數行命中——一律判**「引例、不動」**，勿當殘留再修（判定依據＝本行）。
  ｜出處：2026-07-30 019 U5（spec 第 1 輪 blocker；23a3846 宣稱結清、殘留活在 L-180 自身）

- **L-182**｜**腳本註解裡寫下的「呼叫端須自行處理」，只被腳本作者當成契約；手冊教人手打的
  那條路上，人也是呼叫端**——019 `deploy/sops.sh` 的 P1.2 註解已逐字載明「stdout 重導向＋`-t`
  並存時，容器 pty 把換行改 CRLF、且 passphrase 提示行與 stderr 與 stdout 同流，呼叫端須自行剝
  CR 並濾掉非資料行」，`deploy/decrypt-secrets.sh` 也照此寫了 `normalize_raw`；但 RUNBOOK §15.7
  的 merge 衝突程序（互動程序＝必走帶 `-t` 分支）兩處重導向都是**裸的**——步驟 1 把提示行與
  CRLF 一起寫進要拿去三方合併的明文 YAML，步驟 3 再把它加密回**權威密文檔**，提示行含冒號會
  被當成多出來的 YAML key，要到下次 `decrypt-secrets.sh` 的 P4.3 key 斷言才 fail-loud，屆時壞
  密文可能已 commit 給他人。零機密實證：`./deploy/sops.sh --version` 經 pty 重導向得 3 個 CR
  且 `[warning]` 行併入同檔；`-d` 未輸入 passphrase 的重導向檔 67 bytes、含 1 行提示、零 key
  行（提示確實落檔而非落畫面）。｜防法：①腳本註解寫「呼叫端須…」時，同刀枚舉**全部呼叫端**
  ——含手冊裡教人手打的命令（此即 L-180「程式面修完反向搜手冊」的 pty 面同構）；②`-d` 這類
  必須互動的子命令，重導向後一律接正規化片段（`tr '\r' '\n'` **轉行界不可用 `tr -d`**，提示
  行末尾可能只有 CR）＋「恰 8 支裸量純量 key 行」斷言，讓漏濾變吵鬧失敗；③不需 passphrase 的
  子命令（`-e`）補 `< /dev/null` 把 tty 拔掉，讓 wrapper 不帶 `-t`＝從根上不生此類污染。
  ｜出處：2026-07-30 019 U5（quality 第 1 輪 blocker；RUNBOOK §15.7 兩處裸重導向）
