---
id: "0020"
title: 波 0 規劃定案——三刀組成串行、compose 五服務、部署資產裁剪帶入、wire 後端縱深
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-03 波 0 規劃問答（rev3 波 0 前例 001~003 為對照輸入、user 逐題拍板）；全文脈絡＝docs/brainstorms/wave-0-plan.md"
tags: [planning, foundation, deploy]
---

## 背景

第一把功能刀（ADR 0008 system-settings）開工前需 infra 地基。rev3 前例在功能刀前排了
001-infra-deploy／002-rev2-schema-baseline／003-envelope 等地基刀；rev4 的對應決策多已凍結
（憲法 13 碼矩陣、ADR 0002/0004/0014/0019），波 0 屬純實作波。逐題問答拍板。

## 決定

- **波 0＝三把刀、嚴格串行**：001-compose-stack → 002-schema-baseline → 003-wire-foundation；
  system-settings 順推編號 004（ADR 0008 只綁「功能刀序第一」、不綁編號）。
- **compose 刀範圍**＝五服務（front-nginx／base-web／rust-api／postgres／redis-stack）＋
  migrate one-shot gate＋rust-api 最小 scaffold（axum /health＋sea-orm-migration 空殼）＋
  secrets `_FILE` 機制；觀測四件套不進（隨觀測刀；ADR 0019 已留號）；port 全照 ADR 0019。
- **部署資產＝「設定」非「實碼」**：compose yaml／nginx conf／secrets 腳本／Dockerfile 自 rev3
  裁剪帶入、逐檔改 rev4 語境（port／名稱／釘版／註解），不觸憲法 §I.5 rust 實碼防回歸條款
  （先例：docker-compose.example.yml 搬入）。
- **wire 地基刀＝後端縱深**：統一信封＋13 碼常量表單一來源＋錯誤型→碼映射單一來源＋
  三類守門（碼表 contract test／保留碼斷言／datetime offset 斷言）＋契約機器化骨架
  （base-web typings 唯讀抽 JSON Schema＋coverage gate）；前端 $t 接線與 locale 外包層
  隨首功能刀——**波 0 全程 base-web 零 fork 改動**（可 git 稽核）。
- 波 0 出口＝六組檢查表（環境／基線／wire／文件／紀律／波 1 就緒），詳 wave-0-plan.md §3；
  收 003 時整波重驗。

## 後果

- 各刀仍走完整工作流（brainstorm→SDD 5 步→TDD→收刀）；各刀 brainstorm 輕量化（上游已拍大半）。
- base-web 首個 rev4-inline 改動延至首功能刀。
- schema 基線的 user 定稿制另立 ADR 0021（翻案 0014）。
