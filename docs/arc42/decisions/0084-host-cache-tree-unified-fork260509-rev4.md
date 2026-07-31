---
id: "0084"
title: host 暫存／落點樹統一 ~/.cache/fork260509-rev4/（secrets／decrypt／merge／keygen 四層）——取代 0080 之 SECRETS_DIR 落點值
date: 2026-07-31
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-30 019 收刀 user 指出 host 落點命名應用 repo 名（BACKLOG B-125 登記）＋2026-07-31 user 拍板四項（①樹形四層②工具副檔名歸 B-127／U1③舊落點本單元不刪、主線 merge 後處置④接受分鐘級 stack 中斷）"
tags: [security, secrets, deployment, naming]
---

## 背景

019 收刀後 host 側暫存／落點目錄命名呈雙軌：新資產 `deploy/generate-age-key.sh` 用
**repo 目錄名** `~/.cache/fork260509-rev4`，而既有三處仍用短代號家族——
`~/.cache/rev4-secrets`（SECRETS_DIR 拍板值、`.env` 與 compose 掛載來源）、
`rev4-decrypt.XXXXXX`（`decrypt-secrets.sh` mktemp 模板）、`rev4-merge.XXXXXX`
（RUNBOOK §15.7 mktemp 模板）。雙軌屬刻意暫留（B-125 登記為拍板級）：改落點值＝改拍板
＋重跑落點遷移，只改 mktemp 模板反而與拍板值不一致。本 ADR 即該拍板的結清。

## 決策

1. **host 暫存／落點統一為一棵樹** `${XDG_CACHE_HOME:-$HOME/.cache}/fork260509-rev4/`，
   下分四層：
   - `secrets/`（持久、目錄 700）＝**SECRETS_DIR 新拍板值**（`.env` 真值＝絕對路徑字面）；
   - `decrypt.XXXXXX`（transient、mktemp 直落樹根）＝解密管線明文暫存；
   - `merge.XXXXXX`（transient、mktemp 直落樹根）＝加密檔 merge 衝突之 host 側明文暫存
     （RUNBOOK §15.7；「須落 repo 內」之例外檔不在此列、維持原契約）；
   - `keygen/`（持久）＝產鑰腳本之工具快取（age 二進位＋公鑰捕捉 `pub.txt`）。
2. **本 ADR 取代 ADR 0080 決策 2（SECRETS_DIR＝解法 2 之落點值、即 user 重拍三點定案之①）
   的「落點值」部分：`$HOME/.cache/rev4-secrets` 改為 `$HOME/.cache/fork260509-rev4/secrets`。
   0080 其餘決策全部維持有效**——含決策 2 自身的 ext4 落點語意（持久碟、免開機儀式、
   at-rest 代價誠實登記）、決策 1（私鑰 B′）、決策 3（退路）、決策 4（解密腳本自建 0700
   子目錄）、決策 5（產鑰儀式 C 案）與全部附屬規則。
   - ★**frontmatter 刻意不掛 `supersedes: [0080]`**（user 已拍板此口徑）：0080 是多決策
     ADR、本 ADR 只翻其中一個決策的一個值；掛了會使工具把 0080 整支回填為
     `superseded`＝帳面錯（其餘決策仍為現行權威）。取代關係由本節文字承載。
3. **命名採 repo 目錄名的理由＝零撞名**：同一台機器並存 `fork260509-rev1`～`rev4` 四代
   與其他專案（`work260730-rev1` 等），短代號 `rev4-` 家族與 compose project name
   `rev4-admin`、刀號皆非穩定識別；repo 目錄名才是跨代並存下唯一不撞名的鍵。
4. **遷移法＝搬檔、非重解密**：以保留 mode 之複製（`cp -p`）把舊落點 11 支 `.txt` 搬進
   新 `secrets/`，逐支 sha256 舊 vs 新比對全同＋mode 斷言（檔 644／目錄 700）後才切
   `.env`。理由：重解密需 user 親輸 passphrase（B′ 走 `/dev/tty`、結構上不可無頭自動化），
   而搬檔終態與重解密終態等價（同一組明文值、同權限形）——sha256 全同即等價之機器證明。
5. **舊落點 `~/.cache/rev4-secrets` 本單元不刪**：留待主線 merge 後處置（落點遷移契約
   §P6 五步之末步「才刪舊落點」）；遷移期間舊落點唯讀。
6. **接受分鐘級 stack 中斷**：切 `.env` 需 compose down→up 一輪，dev 環境可承受。

## 後果

- `.env` 真值、`tools/bootstrap.sh` 產檔預設值、`deploy/decrypt-secrets.sh` mktemp 模板、
  `deploy/generate-age-key.sh` CACHE、RUNBOOK §7／§15.6／§15.7 等活引用同刀統一；
  `SECRETS_DIR` 消費者聯集七處之單一權威清單（contracts §P5.1）不變。
- 舊字面 `rev4-secrets`／`rev4-decrypt`／`rev4-merge` 於活文件零殘留；史料（specs／
  brainstorms／events／已 accepted ADR）照舊不動。
- 新增第二個 host 暫存用途時直接落本樹下新層，不再產生第二軌命名。
