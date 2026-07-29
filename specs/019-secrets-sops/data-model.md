# data-model.md — 019-secrets-sops Phase 1（零新表；七個治理／資產模型）

> 本刀零 DB schema 面（零 migration、零實體表）。以下為機密資產、掃描規則與落點接線的結構模型，
> 供 tasks 拆解與驗收斷言取用。行號為 2026-07-28 實測基準，施工時以符號重新定位。

---

## 1. 機密資產清單（四口徑，引用必言明）

| 口徑 | 數 | 內容 | 用途 |
|---|---|---|---|
| 機密檔 | **11** | 7 leaf＋3 composite＋1 user 自填 | `preflight` 的 `REQUIRED` 陣列（:17） |
| compose 條目 | **10** | 11 扣 `reaper_password`（僅 `setup-reaper-role.sh` 直讀） | 頂層 `secrets:`（:363-385） |
| 加密檔 key | **8** | 7 leaf＋`alert_webhook_url` | `secrets.dev.enc.yaml` |
| 含 TLS | **13** | 11＋`ca.key`＋`privkey.pem` | 全機密面盤點（TLS 兩支不進 SOPS） |

**7 leaf**（亂數可重生，生成器＝`docker run --rm alpine/openssl rand`）：

| 名稱 | 生成規格 | 位元組 |
|---|---|---|
| `postgres_password` | `-hex 24` | 48 |
| `redis_password` | `-hex 24` | 48 |
| `reaper_password` | `-hex 24` | 48 |
| `jwt_secret` | `-base64 48` | 64 |
| `refresh_token_secret` | `-base64 48` | 64 |
| `captcha_secret` | `-base64 48` | 64 |
| `grafana_admin_password` | `-base64 24` | 32 |

**3 composite**（由 leaf `cat` 組合、**絕不獨立亂數**、不進加密檔）：

| 名稱 | 組合式（`generate-secrets.sh:129-131`） | 位元組 |
|---|---|---|
| `database_url` | `postgres://soybean:{postgres_password}@postgres:5432/soybean_admin_rust` | 100 |
| `redis_url` | `redis://:{redis_password}@redis:6379` | 68 |
| `reaper_database_url` | `postgres://reaper:{reaper_password}@postgres:5432/soybean_admin_rust` | 99 |

**1 user 自填**：`alert_webhook_url`（現值 39 bytes＝**已填真值**；佔位字串
`https://CHANGE-ME.invalid/alert-webhook-placeholder` 長 51；`--force` 不重置、重置唯一法＝刪檔
重跑 → **絕不以刪檔為測試手段**）。

**不變式**：①所有檔**無尾端換行**（`printf '%s'` 寫入；實測位元組數全數吻合＝旁證）；
②composite 內嵌的 leaf 值與 leaf 檔 **byte-identical**；③加密檔恰 8 key、key 名不得以
`_unencrypted` 結尾。

---

## 2. 加密資產模型

```text
.sops.yaml（repo 根、tracked）
└── creation_rules[0]                    # 唯一一條、first-match-wins
    ├── path_regex: ^deploy/secrets\.dev\.enc\.yaml$   # 錨定式；比對「相對 config 目錄」路徑
    └── age: [ <recipient 公鑰清單，YAML 清單形> ]
    # 不設六個範圍選項任一 → 預設 unencrypted_suffix="_unencrypted"（全加密）

deploy/secrets.dev.enc.yaml（tracked 密文）
├── <8 個明文 key>: ENC[AES256_GCM,data:…]           # 值層加密、key 名明文
└── sops:                                            # metadata
    ├── age[]: {recipient, enc}                      # 每 recipient 一個信封（同一把 data key）
    ├── lastmodified / mac                           # 每次存檔必變 → merge 衝突主因
    └── version
```

**權限粒度＝檔案**：每檔一把 data key，能解開該檔者能解開其中每一個值。
**分層唯一手段＝切檔**（本刀 dev 單檔；prod 檔遞延 B-115）。

---

## 3. identity 與尋鑰模型

```text
~/.config/sops/age/keys.txt   # B′＝passphrase 加密內容（開頭 age-encryption 或 -----BEGIN AGE）
                              #  A＝明文（AGE-SECRET-KEY-1… 或 AGE-SECRET-KEY-PQ-1…）
```

**sops 尋鑰＝聯集載入（非 first-match）**，依序收集五類來源：

| # | 來源 | 本刀立場 |
|---|---|---|
| 1 | SSH：`SOPS_AGE_SSH_PRIVATE_KEY_FILE`／`_CMD`／**預設 `~/.ssh/id_ed25519`、`id_rsa`** | **明文禁令**（爆炸半徑不得綁 SSH 私鑰） |
| 2 | `SOPS_AGE_KEY`（內容本身） | 紅線不用（現形於 argv／environ） |
| 3 | `SOPS_AGE_KEY_FILE`（路徑） | wrapper 顯式轉發、備用 |
| 4 | `SOPS_AGE_KEY_CMD`（stdout 為 identity） | 不採（容器邊界複雜化） |
| 5 | 預設 `$XDG_CONFIG_HOME/sops/age/keys.txt` | **主路徑** |

**推論**：聯集語意 ⇒ 切換來源後舊來源可能默默生效 ⇒ **#10 反向驗證（移走 identity 後必須失敗）
為不可省測項**。

**passphrase 取得順序（B′）**：先試 gpg-agent（快取鍵 `SopsAge` 前綴）→ 連不上回退終端互動
⇒ 官方容器內無 gpg-agent ⇒ **必須有 tty**（wrapper `-it` 條件化的根據）。

---

## 4. 落點與接線模型（SECRETS_DIR 單一事實來源）

```text
.env（repo 根、gitignored、bootstrap 代勞產生）
└── SECRETS_DIR=/dev/shm/rev4-secrets
      # ★重拍（2026-07-29、#11 反轉後）：改 $HOME/.cache/rev4-secrets、詳 ADR 0080「決策」節第 2 點
      │
      ├──→ docker compose（原生讀 .env）→ 頂層 secrets 10 條目變數展開
      ├──→ deploy/decrypt-secrets.sh   （source .env〔存在時〕；未設時回退 deploy/secrets）
      ├──→ deploy/generate-secrets.sh  （source .env；:41 改帶預設展開）
      ├──→ deploy/preflight-secrets.sh （source .env；:12 同上）
      ├──→ deploy/setup-reaper-role.sh （source .env；:16 PW_FILE 同步點）
      └──→ tools/bootstrap             （體檢 glob 隨之）
```

**落點屬性（2′ 原值、★已隨 2′ 作廢、保留供反轉軌跡）**：`/dev/shm`＝tmpfs、16G、
`rw,nosuid,nodev,noatime`（**未帶 noswap**）、目錄權限 `drwxrwxrwt`（world-writable＋sticky）
→ **解密腳本必須自建 0700 子目錄**。系統有 8 GiB swap 啟用中 ⇒ tmpfs 內容理論上可能落入
Windows 側 VHD＝**2′ 保護上限的誠實登記**（ADR）。

**落點屬性（★重拍後現行值、2026-07-29、#11 反轉後）**：`$HOME/.cache/rev4-secrets` 之父目錄
`$HOME/.cache`＝**ext4**（`/dev/sdd` on `/`、`rw,relatime,discard,errors=remount-ro,data=ordered`）、
目錄權限 `drwx------`（0700、owner-only，非 world-writable）→ **解密腳本自建 0700 子目錄之
要求維持**（縱深防禦、與落點無關；ADR 0080 決策 4）。**殘餘風險改登記於 ext4 at-rest 面**：
明文長駐 WSL2 `ext4.vhdx`（Windows 側檔案）、`wsl --shutdown` 後仍在＝解法 2 的已拍代價；
`/dev/shm` 之 swap 殘餘風險登記**隨 2′ 作廢、不再適用**。補償面＝私鑰 B′＋三層掃描防線＋
RUNBOOK §4 BitLocker 確認項（總表化歸 T034）。

**權限終值**：目錄 700／檔案 644（三個非 root service 要讀：grafana 472／postgres-exporter 65534／
redis-exporter 59000；600 會在開 obs／metrics 軌時才炸）。

**回退語意**：未設變數時 compose 解析回 `./deploy/secrets`（向後相容；代價＝忘設即保護失效，
由 preflight＋bootstrap 斷言補償）。

---

## 5. 掃描規則模型（`.gitleaks.toml`，三 repo 共用）

```toml
# 僅使用 gitleaks 子集欄位 → 兩支 scanner 雙向可攜（Betterleaks 自動 fallback 此檔名）
[[rules]]                      # DSN 自訂規則（必填：id + regex）
  id / description / regex / keywords

[[rules.allowlists]]           # per-rule 精確圈定
  condition = "AND"            # ★ 預設 OR；漏寫即退化為過寬放行且不報錯
  paths / regexes / regexTarget
```

**allowlist 欄位集**：`description`／`condition`（AND｜OR，預設 OR）／`commits`／`paths`／
`regexes`／`regexTarget`（`secret`｜`match`｜`line`）／`stopwords`；全域 `[[allowlists]]` 另有
`targetRules`。至少需 `commits`／`paths`／`regexes`／`stopwords` 其一，全空即 config 載入失敗。

**誤報源清單（U0 現場重建基線後定稿）**：

| 來源 | 樣態 | 圈定方式 |
|---|---|---|
| `docs/ops/events.jsonl` | 40-hex：`merge` 18＋`pins.web` 18＋`pins.api` 18＝**54 筆** | paths 限該檔 × regexes 限 40-hex × AND |
| `deploy/secrets/*.txt.example` | 11 支 tracked 假值（各 22 bytes） | 同上（限該 glob × 假值樣式） |
| `specs/017-audit-retention/quickstart.md` | `curl -u admin:…` 示例 | 同上 |

---

## 6. 三層防線覆蓋矩陣（clarify 拍板結果）

| 層 | 型 | 外層 | rust-api | base-web | 攔截樣態 |
|---|---|---|---|---|---|
| Betterleaks 樣式掃描 | 事件型 | pre-commit＋pre-push | 同 | 同 | 廣譜樣式＋自訂 DSN |
| `tools/secret-value-guard.py` 值比對 | 事件型 | pre-commit | — | — | 現值原文（裸值形唯一防線） |
| docs-sync L16 憑證掃描 | **狀態型** | lint（每次 commit） | pin bump 增量 | pin bump 增量 | 窄樣式四類（`--no-verify` 躲不掉） |

**hook 目錄拓樸**：

```text
.githooks/                      # 外層（core.hooksPath 相對路徑，bootstrap:35 既有）
├── pre-commit                  # 掃描 → docs-sync check → lint → 值比對 → 條件觸發自測
├── pre-push                    # 範圍掃描
└── lib/scan-range.sh           # 共用：stdin 解析＋範圍推導（含全零 oid 退階）
.githooks-submodule/            # 兩源倉（bootstrap 設絕對路徑 hooksPath）
├── pre-commit                  # 僅樣式掃描（零 python 依賴）
└── pre-push                    # 同 → 以 dirname "$0" 自我定位後 source ../.githooks/lib/
```

---

## 7. 解密管線狀態模型（`decrypt-secrets.sh` 五要求）

```text
[前置] tty 守衛（B′ 需互動）→ source .env（存在時；未設時回退 deploy/secrets）
       → mkdir -p $SECRETS_DIR && chmod 700（自建 0700 子目錄）
   │
[解密] wrapper 收 stdout（umask 077；不用 --output／-i，避免 root 產物）
   │
[斷言] key 數＝8 且名稱集合相符？──否──→ 零寫入 + 非零退出 + 指名缺哪個 key
   │是
[逐檔寫入] printf '%s'（無尾端換行）→ chmod 644
   │
   ├─ 目標檔已存在且現值 ≠ 解密值？──是──→ 另存 <name>.txt.new + 警示，不覆寫原檔
   └─ 否 → 直接寫入
   │
[後續] generate-secrets.sh --compose-only（重組 3 composite）→ preflight
```

**否定測試對應**：刪 key → 零寫入報錯（f）｜CR 注入 → preflight 護欄紅（a）｜構造
`alert_webhook_url` 差異 → 產生 `.new` 而非覆寫（SC-007）｜移走 identity → 解密必失敗（#10）。
