# Phase 1 Quickstart: 013-ip-rule-admin 驗收指引

**用途**：本刀的可跑驗收清單（全量閘＋負向自證＋CDP 實機）。實作細節見 tasks.md；契約見 [contracts](./contracts/ip-rule-admin-endpoints.md)、資料形見 [data-model](./data-model.md)。

---

## §0 前置

```bash
cd /home/anew/x_Project/fork260509-rev4          # 或 /mnt/d/AnewSpaces/x_Project/fork260509-rev4（同一棵樹）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait   # 五 service healthy
```
- rust build/test **一律容器內**（host 無 toolchain）、**單一 cargo 進程**（絕不平行跑多個 cargo）。
- base-web commit 一律 `--no-verify`；`.vue` template 標記用 `<!-- -->`（L-119）。
- ★**新 i18n key 後、CDP 前必 restart base-web**（vite 未必熱載新字典、否則顯 raw key、L-015）。
- ★base-web 容器易 OOMKilled(137)：CDP 前先驗 healthy＋vite 200；掛了 `docker compose up -d` 復活。

## §1 全量閘

```bash
# 後端（容器內、serial）
docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test -p server'
# 期望：全綠、零既有測試轉紅；契約 registry 筆數不變（零新 route）

# migration（m010）
docker exec rev4-admin-migrate-1 sh -c 'cd /app && cargo run --bin migration up'   # 或 compose up 自動套用
# 期望：'m010_ip_rule_admin' has been applied

# schema-gate（含新機制 self-test）
python3 tools/schema-gate gate2
python3 tools/schema-gate --self-test        # 期望：SEED_CONTENT_OVERRIDE_ALLOWLIST self-test 綠
# 期望：gate2 綠——casbin +4 走 additive allowlist、manage_ip-rule.buttons 一格走 content-override

# 前端
docker exec rev4-admin-base-web-1 sh -c 'cd /app && pnpm typecheck'
# 期望：綠（route.manage_ip-rule 三語不補即紅＝型閘生效證據）
bash tools/fork-delta-lint                    # 期望：綠（新檔零原行圈界）

# 文件
python3 tools/docs-sync check                 # 期望：一致
```

## §2 負向自證五條（拆除即紅＝load-bearing 證據）

| # | 自證項 | 拆除方式 → 期望轉紅 |
|---|---|---|
| ① | **ILIKE escape 生效** | 拿掉 `ilike_contains` 的 `%_\` 字面化／`ESCAPE` → 搜 `_` 被當萬用字元、斷言即紅 |
| ② | ★**單主機可被顯示值搜到** | 比對面自 `wbip_cidr::text` 改成剝遮罩式（如 `host(wbip_cidr)`）→ 搜 `203.0.113.7/32` 或 `/32` 零命中、斷言即紅（★釘死 R1 實測結論、防日後改動漏失） |
| ③ | **`deleted` 三態各自只列對應集合** | 拿掉三態 WHERE 分支 → `active`／`deleted` 視圖混入他集、total 失準、斷言即紅 |
| ④ | **enrich 已軟刪查得名＋查無回 null** | 改用「排除已軟刪」的查法 → 已軟刪建立者變 null、斷言即紅；餵不存在 id → 須 null 不 panic |
| ⑤ | **getIpRuleList query 契約形** | 契約 case 未隨三參數更新 → 契約裁判紅指名 |

★`selfLock` **dev 實機測不出**（還原位址落私網→結構豁免先放行、對其建 deny 又被自鎖拒）——以**單元測試 mock** 覆蓋（spec Edge Cases／Assumptions 明載侷限）。

## §3 CDP 實機（Edge@9229 → `http://127.0.0.1:42080`）

驅動法：`/json/list` 取 `type==page && url.includes('42080')` target → Node global `WebSocket` 送 `Runtime.evaluate`；quick-login 點「超級管理員」（Super/123456）。

| 場景 | 驗收 |
|---|---|
| **S1 清單混排** | 選單顯在地化名（**非 raw key**）、點擊不 404；現役＋已刪同表、現役沉頂已刪殿後、狀態欄辨識；已刪列**只顯復原鈕**、現役列顯編輯＋刪除；審計欄（建立/更新時間、建立/更新者）有值 |
| **S2 CRUD** | 新增（四欄）→列出現；編輯→值變更；刪除（NPopconfirm 二次確認、**DELETE 動詞**）→轉已刪 |
| **S3 復原** | 已刪列點復原（confirmRestore 二次確認）→回現役；建重複網段×類型→**conflict 拒因 toast** |
| **S4 搜尋三維** | 網段模糊（大小寫不敏感、**含單主機規則以顯示值／「/32」搜**）；類型精確；★**狀態三態**：切「已刪除」只列已刪、切「現役」只列現役、「全部」回混排（total 隨之誠實） |
| **S5 拒因三語** | 三語切換下拒因 toast 皆在地化文字、**零 raw key**（conflict 可實測；selfLock 註記 dev 侷限、以單測補） |
| **S6 hasAuth** | 超管四操作鈕全顯；`getAllButtons` 候選含 `ipRule:*` 四碼（角色頁按鈕面板可勾） |

★殘留清理：CDP 造的測試規則收尾刪除、確認 `cdp013_` 類前綴殘留歸零。

## §4 收刀前檢查

- [ ] 全量閘 §1 全綠
- [ ] 負向自證 §2 五條皆「拆除即紅」實證
- [ ] CDP §3 S1~S6 PASS＋殘留歸零
- [ ] **憲法 amendment 已親決落地**：ADR 0061~0064 → accepted；`constitution.md` §III.2 (d) 擴字串；version **v1.11.0**；獨立 commit `docs(constitution): amend`＋`docs-sync generate`
- [ ] BACKLOG 簿記：**B-061 刪列**（route locale 兌現）；B-083 不刪（013 不下放、ADR 0063 行為級 forward-link）；新增「系統軟刪掃描」＋「按鈕碼與 sys_menu.buttons 聯集漂移」兩追蹤項
- [ ] 兩段式 commit：worktree commit → 外層 bump pin（★先 `git add <submodule>` 再 `docs-sync generate`、否則 STATE pin 不一致被 L1 擋）
</content>
