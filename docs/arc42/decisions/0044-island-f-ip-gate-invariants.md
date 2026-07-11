---
id: "0044"
title: 憲法 §I.7 行為島進場——島 F（IP 存取控制閘＋信任錨＋來源維節流）＋島 E2 射程釐清
date: 2026-07-11
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-11 008-ip-gate plan Constitution Check Q9（新島 F 進場＝MINOR Amendment；user 親決 2026-07-11）"
tags: [constitution-amendment, security, ingress, throttle]
---

## 背景

008-ip-gate 落地 IP 存取控制閘、信任錨基建與來源維度節流——為新行為島，依 §V.3「行為島隨刀進場」
以 MINOR Amendment 入憲 §I.7；並同步釐清島 E2（帳號維判定鍵）射程與本刀來源維並列判定不衝突。

## 決定

**§I.7 新增島 F — IP 存取控制閘（008、ADR 0043 真實 IP 還原／0045 來源維節流）**，方向性面凍結
（反轉＝MAJOR）、常數/欄級留活書：

- **F1（判定序與集合語意）**：閘門判定 MUST 依固定序——①健康/觀測放行 ②請求上下文缺席放行
  ③結構性豁免網段放行 ④命中放行規則放行 ⑤命中阻擋規則拒絕 ⑥其餘放行；規則集為 any-match 集合語意、
  **白＞黑＞default-allow、無順序化規則鏈或優先權欄**。
- **F2（真相分層）**：DB 規則表為真相、記憶體 ArcSwap 判定面（每請求零 DB/Redis）；真相暫不可讀時
  判定面 **沿用上一份已知良好規則集**（keep-last-good）、不清空。
- **F3（fail-OPEN 與唯一例外）**：全鏈 fail-OPEN（信任模型壞損→全空 all-direct、規則載入失敗→空集、
  快取/門鈴故障→放行）；**唯一 fail-closed 例外＝寫端自鎖拒寫**。每次降級 MUST 發結構化告警。
  **★入憲後 fail-OPEN 方向反轉＝MAJOR。**
- **F4（信任錨為唯一輸入、同源對稱）**：來源維度一切機制（閘門判定、來源維節流、稽核來源）的位址輸入
  MUST 為信任錨還原結果；信任集與跳過集 MUST 同源對稱導出。
- **F5（放行跳節流只認顯式規則）**：命中顯式放行規則的來源跳過來源維節流（含快取層）；**結構性豁免網段
  MUST NOT 跳節流**（結構豁免只豁免「阻擋」、不豁免節流）。

**島 E2 射程釐清**（已入憲 invariant 細項調整、MINOR）：島 E2「帳號維判定鍵＝所送出帳號名原文、
MUST NOT 依賴來源 IP」之射程為**帳號維度的判定鍵**；本刀新增的來源維度為獨立並列維度（FR-030），
兩者不衝突——避免憲法 E2 原文與並列雙維度實作解讀分歧。

憲法 MINOR bump（§V.3「行為島隨刀進場」＋「已入憲 invariant 細項調整」）→ **v1.5.0 → v1.6.0**。
島 F 全文入 §I.7、與本 ADR 同 commit。

## 後果

- 008 plan Constitution Check Q9 GATE 解除。
- 島 F 方向性面凍結：後續刀改 fail-OPEN 為 fail-closed（或反之）＝MAJOR；常數（門檻/豁免段/TTL）留活書可調。
- 島 E（007）四項不變式全數保持；E2 射程釐清後帳號維與來源維並列判定的解讀一致。
