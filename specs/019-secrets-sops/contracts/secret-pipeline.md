# contracts/secret-pipeline.md — 019 加密／解密管線與落點接線契約

> 契約＝可機器驗證的行為邊界。所有「必須失敗」的條款皆為否定測試對象——本方案的失敗模式幾乎
> 全是「指令回報成功但做錯了」，故每條正向契約都配一條否定契約。

---

## P1 wrapper 契約（`deploy/sops.sh`；FR-010）

| # | 契約 | 違反後果 |
|---|---|---|
| P1.1 | 映像以 **digest** 釘版（非 tag） | tag 可被重新 push＝供應鏈不可變性喪失 |
| P1.2 | 互動旗標**條件化**（有 tty 才配 `-it`） | 寫死 `-it`＋輸出重導向 → pty 把換行改 CRLF、密碼尾多 `\r`（靜默）；非互動情境無限期 hang |
| P1.3 | **不轉發** host `EDITOR` | 官方映像已內建 `EDITOR=vim`；轉發 host 值會使 `sops edit` 失敗 |
| P1.4 | 顯式 `-e SOPS_AGE_KEY -e SOPS_AGE_KEY_FILE -e SOPS_AGE_KEY_CMD` | 未以 `-e` 列出的變數被**靜默丟棄** |
| P1.5 | 必須自 repo 根執行 | 否則 `.sops.yaml` 找不到 → `config file not found, or has no creation rules`（吵鬧失敗、可接受） |
| P1.6 | 明文產物一律由 **host shell 收 stdout**＋`umask 077`，不用 `--output`／`-i` 產明文 | 映像以 root 執行、host umask 不跨容器邊界 → 產物 `root:root`，後續 `chmod` 在 `set -euo pipefail` 下中止 |
| P1.7 | `chmod +x` 後 `git update-index --chmod=+x` | drvfs 上 exec bit 不落 index → 他機 clone 得到不可執行檔 |

---

## P2 `.sops.yaml` 契約（FR-013）

| # | 契約 | 違反後果 |
|---|---|---|
| P2.1 | `path_regex` **錨定式**（`^…$`） | 比對用 `MatchString`＝非錨定子字串命中 → 意外檔案被套規則 |
| P2.2 | **僅一條** `creation_rules` | first-match-wins，第二條被**靜默忽略** |
| P2.3 | 寫完**驗證規則確實命中**目標檔 | 目錄式或錯誤 regex → 比對不到任何檔案、分層形同虛設**且不報錯** |
| P2.4 | **不設**六個範圍選項任一 | 預設 `unencrypted_suffix="_unencrypted"`＝全加密；設 `encrypted_regex` 是**白名單**，新增欄位靜默不加密 → 明文密碼進 git |
| P2.5 | key 名**禁 `_unencrypted` 後綴** | 該後綴無法藉由「不設定」規避，命名踩中即該值明文入庫 |

---

## P3 加密檔契約（FR-014／FR-015）

| # | 契約 | 驗證方式 |
|---|---|---|
| P3.1 | 檔名 `deploy/secrets.dev.enc.yaml`（**格式副檔名在最後**） | 寫成 `.env.enc` → SOPS 當 binary 處理、**退化為整檔加密**（失去核心優勢） |
| P3.2 | 恰 **8 key**（7 leaf＋`alert_webhook_url`） | key 數斷言；composite 不進（缺席時由 preflight 攔下、且 composite 是唯一有自動修復機制的副本） |
| P3.3 | `git diff` 呈現 **key 名明文＋值全密文** | 目視／機判：每值以 `ENC[` 開頭 |
| P3.4 | `alert_webhook_url` **如實搬移現值** | byte 級比對搬移前後一致；**絕不重生、絕不以刪檔為測試手段** |
| P3.5 | 明文中間產物限 **repo 內 gitignored 目錄**、用完即刪、不得出現於 staged | wrapper 只掛載 `$PWD`，`$SECRETS_DIR` 在 repo 外→容器看不到；且 staged 檢查為驗收項 |

---

## P4 解密管線契約（`deploy/decrypt-secrets.sh`；FR-016）

> **命名空間注意**：本表 (a)~(e) 為 **FR-016 五要求的本地編號**，與 spec Clarifications 的
> 驗收升格字母 a／b／c／d／f／h（＝brainstorm 候選驗收編號）**屬不同命名空間、指涉不同**；
> 引用時必言明出處（對照表見 spec Clarifications）。

| # | 契約（FR-016 要求代號） | 否定測試 |
|---|---|---|
| P4.1 (a) | 寫檔**無尾端換行**（`printf '%s'`） | leaf byte 數 vs composite 內嵌值 byte 數必須一致；不一致＝不變式破裂（而腳本只印 SKIPPED、preflight 印 OK＝零警告） |
| P4.2 (b) | tty 守衛（B′ 需互動） | 非互動呼叫必須**吵鬧失敗**，不得 hang 死或寫出帶 CR 的檔 |
| P4.3 (c) | key 數與名稱斷言，不符 → **零寫入 + 非零退出 + 指名缺哪個 key** | 刻意刪 enc 檔一 key → 管線必紅；**絕不可**落到 `generate-secrets.sh` 靜默造新亂數的路徑 |
| P4.4 (d) | 輸出目錄 `mkdir -p` + `chmod 700`，且**早於任何 `up`** | 目錄不存在時 docker daemon 會以 root 建出 `drwxr-xr-x root root`，使用者不能寫也不能刪 |
| P4.5 (e) | 現值 ≠ 解密值 → 另存 `<name>.txt.new` + 警示，**不覆寫** | 構造 `alert_webhook_url` 差異 → 必產 `.new`；此為 decrypt 引入的**原本不存在的覆寫路徑**，`generate` 印 SKIPPED、`preflight` 只檢存在與非空，兩者都不告警 |
| P4.6 | 落點自建 **0700 子目錄** | ★原理由「`/dev/shm` 為 `drwxrwxrwt`（world-writable）」屬 2′ 原值、隨重拍作廢（2026-07-29、#11 反轉後改 `$HOME/.cache/rev4-secrets`＝`drwx------`；ADR 0080）；要求維持＝縱深防禦、與落點無關——否定測試：將 `SECRETS_DIR` 指入**權限非 0700 的父目錄**下跑解密，`stat -c %a` 子目錄**仍必為 `700`**（**唯一權威落點＝`tasks.md` T023 之否定測試列舉**；`quickstart.md` §S5「解密管線五要求與否定測試」之表**現為六列、尚未列入本項**——待 T023 施工時同步補列〔已記於 T023 重拍連帶〕，補列前一律以 T023 為準，勿據 §S5 逐列核對推定本項不存在；★§S 亦為跨檔同號不同義之命名空間〔`quickstart.md` §S6＝落點遷移五步、`contracts/scan-gates.md` §S6＝三層互補不變式，兩者皆不含權限斷言〕，引用必附檔名） |
| P4.7 | 檔案權限終值 **644**、目錄 **700** | 600 → grafana(472)／postgres-exporter(65534)／redis-exporter(59000) 全部 Permission denied，且**只在開 obs／metrics 軌時才炸** |

---

## P5 落點接線契約（FR-017～FR-020）

| # | 契約 | 違反後果 |
|---|---|---|
| P5.1 | `SECRETS_DIR` 單一事實來源＝repo 根 `.env`；★**相對值錨定基準＝repo 根**（非 CWD——compose 以**專案目錄**解析相對值；五支賦值型消費者一律正規化：四支 shell 以 `case` 判 `/*` 後補**自腳本位置推導**之 repo 根〔非 `$PWD`——押在 CWD 上等於押在別處的斷言〕、`secret-value-guard.py` 早以 `os.path.join(ROOT, val)` 同錨，違者自 repo 子目錄執行即與 compose 指向不同目錄且雙方各自 `rc=0`＝**靜默分裂**，實測 preflight 印「齊備且健康、可 up」而 compose 掛另一個空目錄、generate 更把明文寫進 repo 樹內而 guard 掃不到；019 U4 quality、L-178）；**取值口徑三級**＝環境變數優先（與 compose 口徑一致）→ repo 根 `.env` **只嚴格解析 `SECRETS_DIR=` 一行**（★**明令禁用整檔 `source`**）→ 皆缺回退 `deploy/secrets`。★**消費者聯集＝七處、本列為唯一權威清單**（落點類變更動手前先枚舉本列＝L-174 防法①）：compose（原生讀 `.env`）／`deploy/decrypt-secrets.sh`／`deploy/generate-secrets.sh`／`deploy/preflight-secrets.sh`／`deploy/setup-reaper-role.sh`／`tools/secret-value-guard.py`／`tools/bootstrap`（體檢讀值：只讀 `.env`＋回退、不吃環境變數）——分工＝P5.2（五支賦值點）＋P5.3（compose）＋P5.4（bootstrap），**任一單列皆非全集** | 只寫 `.env` 不同步 → **compose 讀新落點、腳本查舊落點**；preflight 回 OK 而 compose 掛掉。★原表「compose 原生讀、三腳本 `source`」為施工前敘述、**已作廢**（019 U3／U4 as-built）：`source` 屬**刻意拒用**的機制——compose 的 `.env` 允許不加引號的含空白值、`#` 語意亦與 shell 不同，且值內 `$()`／反引號 `source` 時**會被執行**＝把落點設定變成可執行碼；照舊敘述「回歸合規」＝安全倒退。四腳本＋guard 現皆嚴格單行解析、非法值（空白／shell 元字元／非絕對路徑字面）**吵鬧失敗不靜默回退**。★**行形偵測寬、值校驗窄**（019 U4 quality as-built）：`compose` 的 `.env` 解析器接受 **UTF-8 BOM／行首空白／`export ` 前綴／等號兩側空白／CRLF 行尾**（實測 compose v5.3.1 六形皆解析為新落點），故六處解析器（五支賦值型＋`bootstrap`）之**偵測樣式必須同等寬**、再對取出的值套上述嚴格白名單——偵測窄於 compose ＝該行漏認即**靜默回退**舊落點，是本列違反後果欄那條路的另一個入口（修前實證：前四形四腳本與 guard 全部靜默回退 `deploy/secrets` 且 `rc=0`，CRLF 形則四腳本 `FAIL` 而 guard 與 compose 正常採用＝五支解析器 4:1 分裂）。★**空字串邊界＝同一條路的第三個入口**（019 U4 quality as-built）：「**已匯出但為空**」≠「未設」——shell 環境已勝出 `.env`，compose 的 `${SECRETS_DIR:-./deploy/secrets}` 對空字串**直接吃預設值回退 repo 內舊落點、根本不讀 `.env` 該鍵**，而 `[ -z "${SECRETS_DIR:-}" ]`／`if val:` 把它當未設而續讀 `.env`＝腳本查新落點、compose 掛舊落點（修前實證：同一空字串環境下 preflight 印「可 up」`rc=0`、guard `rc=0`，`compose config` 卻全數指向遷移後零 `.txt` 的 `deploy/secrets`，`up` 會在該處自動建空目錄當 secret 掛入＝P5.4 違反後果欄那個誤導型失敗）。故五支賦值型解析器一律以 `${VAR+set}` 判「有無設定」、與 `-z` 判「是否為空」**分離**，**已設且為空＝吵鬧失敗**（指名真因＋`unset` 自癒指引），絕不代 operator 猜邊；`tools/bootstrap` 依本列分工只讀 `.env`／不吃環境變數，故不在此守衛之列 |
| P5.2 | 落點**賦值型**消費者全員同刀齊改——★**五支**（原表只列前三、019 U4 遷移後補齊）：`generate-secrets.sh`／`preflight-secrets.sh`（`SECRETS_DIR` 賦值）／`setup-reaper-role.sh`（`PW_FILE`）／`decrypt-secrets.sh`／**`tools/secret-value-guard.py`**（三層防線之確定性層）。★**本列非全集**——compose 見 P5.3、`tools/bootstrap` 見 P5.4，**完整消費者聯集七處＝P5.1** | 任一未改 → 該處**無條件賦值**吃掉外部值（靜默）。★第五支漏列之實害（U4 實證）：guard 只讀環境變數而 hook 環境不設該變數 → 落點遷出後 pre-commit 一律 `skip` 且 `rc=0`，FR-007／US1 情境 4／SC-001 裸值格**結構性失守而全綠**（L-174） |
| P5.3 | compose 10 條目改帶預設值變數展開；未設變數時 `docker compose config` 解析回 `./deploy/secrets` | 向後相容的代價＝**忘設變數即保護失效**（誠實登記於 ADR，由 P5.4 補償） |
| P5.4 | **fail-loud 的承載者＝preflight**（落點目錄缺席或機密缺檔→非零退出、指名缺項）；**bootstrap 的角色＝自癒與斷言**：`.env` 缺失時代勞產生（非 die）、hooksPath 與掃描器二進位斷言為 **die 級**、**機密實值缺檔維持 warn 級**（既有慣例：實值人對人交接、bootstrap 不生成） | 否則「`level=warning secret file does not exist` 但容器照樣 Started」＝解法 2 系列的靜默失敗。★三者等級刻意不同、非疏漏：preflight＝上機前把關（fail-loud）／bootstrap 工具鏈完整性＝die／bootstrap 機密實值＝warn |
| P5.5 | `generate-secrets.sh` 增 `--compose-only`（缺 leaf **報錯退出**、不生成） | 缺 leaf 時靜默造新亂數＝每台機器各拿到不同的值 |
| P5.6 | preflight 增 CR 偵測與 composite↔leaf 一致性檢查。★**CR 護欄之外另須 LF 護欄**（019 U4 quality as-built）：機密檔判準＝**零換行字元**（`stat` 位元組數 ＝ 剝除 CR／LF 後位元組數） | 現況只檢「檔在且非空」：塞入密碼已過期的 `database_url.txt` 也回 OK。★**尾端換行**是 CR 之外的第二格且 CR 護欄照不到：composite 一致性用命令替換取值比較（`$(cat)` 剝尾端換行）對它結構性失明——修前實證 `redis_password.txt` 尾多一個 LF 時 preflight 仍回「齊備且健康、可 up」`rc=0`，而 compose 把 15 byte 密碼掛進 redis、把內嵌 14 byte 版本的 `redis_url` 掛進 rust-api＝認證必失敗而上機前把關放行 |
| P5.7 | `printf '%s'` 寫檔形**不得改為 echo**。★**值比對亦同**：一致性／drift 判定一律 `printf '%s' … \| cmp -s -`（019 U4 quality as-built，三支消費者 decrypt／generate／preflight 同一形） | byte-identical 不變式的前提。★命令替換（`$(cat)`／`$(…)` 字串相等）會剝尾端換行＝寫檔形守住的不變式在**讀取比對面**破功：修前 `generate --compose-only` 對尾多一個 LF 的 composite 判為相等、印 `SKIPPED`、`rc=0`，劣化未修復 |

---

## P6 遷移契約（FR-021；順序即契約）

```text
① docker compose down            # 略過＝假性完成（SECRETS_DIR 改變不觸發重建、config-hash 相同，
                                 #   up -d 顯示 Starting 而非 Recreated，容器仍 bind 舊 inode）
② ./deploy/decrypt-secrets.sh    # 腳本內先 mkdir -p + chmod 700（P4.4／P4.6）
③ 設好 SECRETS_DIR 後 docker compose up -d
④ docker inspect <c> --format '{{range .Mounts}}{{.Source}}{{end}}'   # 逐容器驗來源已非 /mnt/d
⑤ 確認無誤後「才」刪除舊落點 deploy/secrets/*.txt
```

**否定契約**：④未通過前刪除 ⑤ 的檔 → 容器仍運作（bind 到已刪 inode）、**下次重啟才炸**。

---

## P7 營運程序契約（FR-023／FR-024）

| 操作 | 契約 | 陷阱 |
|---|---|---|
| 編輯機密 | `sops edit` → decrypt → `up -d --force-recreate <svc>` | **不用 `restart`**（可能撞 Docker Desktop bind-mount 快照失效） |
| 加人／換機 | ①新機產鑰 ②公鑰交付（公鑰非機密）③管理者 `updatekeys -y` ④新機 `git pull`＋decrypt | 「換機器 `git pull` 即可用」是錯的；`updatekeys` 只影響**執行當下存在**的加密檔，未來新建檔由 `creation_rules` 決定（兩機制都要對） |
| 撤銷 | ①`.sops.yaml` 移除 recipient ②`rotate -i --rm-age <公鑰>` **逐檔一行** ③**輪替實際機密值** | `rotate` **只處理第一個位置參數**，多檔其餘**靜默略過且 exit code 不變**；只做 `updatekeys` 不換 data key → 對方可把舊 `enc:` stanza 貼回新檔用原廠 `sops decrypt` 解開（門檻＝任何前同事＋文字編輯器）；git 歷史永久 ⇒ 第③步不可省 |
| 輪替 | 依 RUNBOOK §7 逐支程序 → **輪替後 re-encrypt 回加密檔** | 漏此步 → 輪替值與加密檔脫鉤，下次 decrypt 觸發 `.new` 守衛 |
| 遺失 | 私鑰遺失＝走加人流程重加入；B′ 下 passphrase 遺失＝該 identity 永久失效 | 離線備份義務**含 passphrase 本身**（私鑰檔在磁碟上是密文，光有檔案沒有 passphrase 等於沒有） |
| 合併衝突 | 雙方解密 → 明文三方合併 → 重加密 → **核對 `sops.age` 清單與 `.sops.yaml` 一致** | 對暫存路徑加密時 `path_regex` 可能比對不到規則 → recipients 被悄悄改變（解法＝`--filename-override`）。★**暫存明文落點兩分**（2026-07-29 as-built 勘誤、L-171／L-180；原表無條件寫「必須落 repo 內」＝**已作廢**）：「落 repo 內」**只適用於要當參數餵回容器內 sops 的那一個檔**（wrapper 只掛載 `$PWD`、且 P1.2 下 stdin 非 tty 不帶 `-i` 故管線不可用）；由 host shell 重導向產生、**從不進容器**的暫存明文一律落 **repo 外**之 0700 且非 v9fs 目錄——repo 根在 `/mnt/d`＝v9fs、`chmod` 結構性 no-op（實效 777、Windows 側可見），違者由 `decrypt-secrets.sh` 落點守衛 fail-loud 拒絕（FR-021／SC-005）。**操作程序＝RUNBOOK §15.7**（唯一權威落點；照舊敘述「回復一致」＝把已消滅的暴露面裝回去） |

---

## P8 撤銷演練五準則（#7；FR-024）

1. **否定測試（核心）**：把舊版本中屬自己的 `enc:` stanza 用文字編輯器貼回新檔的 `sops.age`
   清單，跑**原廠** `sops decrypt` → **必須失敗於 MAC 驗證**（`cipher: message authentication failed`）。
2. recipient 清單前後確實不含被撤銷者。
3. rotate 前後**值密文必變**（未變＝data key 未換）。
4. 人工確認 dev 檔內不含 prod 等級機密（**此規則測不出來、只能靠流程保證**）。
5. 前置：演練用第二把金鑰已備妥。

**只驗「被撤銷者無法直接解開 HEAD」＝假通過**（錯誤流程下也會通過）。
