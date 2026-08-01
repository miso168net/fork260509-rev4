---
id: "0087"
title: mailpit host 配號歸位 48025＋判例「SDD 產物與既有 accepted ADR 衝突時 ADR 優先、應升級拍板」
date: 2026-08-01
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-08-01 020 收刀後 user 質詢「mailpit 為何 8025 而非 4xxxx」→查證確認破例→user 親決歸位"
tags: [deploy, governance, dev-experience]
---

## 背景

ADR 0019 定 rev4 dev host 配號制：**app 群 42xxx 序號制、infra 群「4＋well-known」制**
（grafana 43000／loki 43100／prometheus 49090／pushgateway 49091／postgres 45432／
redis 46379 逐項遵守），容器內側則回歸各容器官方預設值。

020-email-verify-smtp 引入 mailpit（dev 收信件）時，host 側配了 `127.0.0.1:8025`——
`docs/generated/reference/ports.md` 全表唯一不帶 4 字頭者。追溯成因有三段：

1. **SDD 期疏漏**：research／spec／plan／data-model／contracts／quickstart 六份產物皆寫死
   `127.0.0.1:8025`（mailpit 官方預設值直抄），全程無人以 ADR 0019 對照檢查。
2. **施工期示警確實發出**：U1 唯讀偵察報告明文「★T006 mailpit 配號須避開此表
   （1025/8025 對應之 4xxxx 位需 U1 決策）」——衝突被機器發現、球傳到主線。
3. **主線裁決失誤**：主線選擇「照 SDD 字面走」並烤進 implementer prompt
   （「★mailpit 8025 配號＝SDD 四處拍定字面、照 SDD 走勿自改」），且在 review prompt
   將其列入「勿翻案」清單——既沿用了疏漏，又主動封死了 review 質疑該項的通道。

功能面當時未撞號（rev3 走 3xxxx），但 8025 正是 mailpit 官方預設值——多 stack 並行時
（他專案、rev3 補測）必撞，而「4 字頭前綴制」的存在理由正是消滅此類撞號。

## 決策（user 親決 2026-08-01）

1. **host 配號歸位 `127.0.0.1:48025`**（＝4＋well-known 8025，回歸 ADR 0019 infra 群制）；
   **容器內側 8025 不動**（ADR 0019 明定容器內回歸官方預設值、原本即合規）。
   射程＝`docker-compose.dev.yml` ports 與註解、`ARCHITECTURE.md` §7、`quickstart.md`
   三處 curl 指令、`reference/ports.md`（generate 重算）。
2. **容器內測試路徑不受影響**：`tests/email_verify.rs` 的 `http://mailpit:8025` 走 compose
   服務名＋容器內 port，與 host 配號正交、零改動。
3. **ADR 0086 body 保持不動**（accepted 後 body 不可變；其記載＝當時決策事實、git 即史）；
   port 現況以本 ADR 與 compose／ports.md 為權威。
4. **判例（本 ADR 的主要價值）**：**SDD 產物（spec/plan/data-model/contracts/quickstart）
   與既有 accepted ADR 衝突時，ADR 優先**——SDD 產物是本刀的設計輸出，不因寫在紙上就
   取得推翻既有治理決定的效力。施工期若機器或人發現此類衝突，**MUST 升級為 user 拍板題**
   （屬「破紀律例外」層級），**不得由主線自行選邊**，更不得以「SDD 已拍定」為由封死
   review 的質疑通道——後者使唯一能攔下疏漏的機制失效。

## 後果

- dev 收件匣網址改為 `http://127.0.0.1:48025`（舊書籤失效、一次性）。
- `reference/ports.md` 恢復「全表皆 4 字頭」的可掃描性質，配號制零具名破口。
- SDD 定稿產物（tasks／plan／data-model／contracts／research）保留原 8025 字面＝當時決策
  紀錄，不追改（時態分離：過去式住 git 與定稿產物、現在式住活書與 compose）。
- 判例入庫後，未來刀遇「SDD 字面 vs 既有 ADR」衝突有明確處置路徑，不必再逐案重新判斷。
