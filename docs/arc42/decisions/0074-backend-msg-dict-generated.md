---
id: "0074"
title: 觀測側拒因可讀性＝機生字典＋grafana 對照（B-007 兌現、ADR 0001 第 8 題配套結案）
date: 2026-07-19
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——user 親決 D9；ADR 0001 第 8 題掛 B-007 之配套；審查 B3 材質歸家拍定"
tags: [obs, i18n, docs-governance, grafana]
---

## 背景

憲法 §I.3 拍死「wire msg 載穩定 i18n key、後端不在地化」（翻譯全在前端）；維運直讀觀測面
（grafana 查 access-log／稽核面板／API 回應）時只見 key（如 auth.login.failed）不見人話。
ADR 0001 第 8 題沿用該憲章並掛 B-007（log 附譯文或維運字典對照表）為觀測側補強候選。
實貌釐清：後端業務拒因不落 tracing log（只進 DB 與 wire）、痛點主要在 grafana 面對照 key 語意。

## 決策

- **機生字典＋grafana 對照**：`tools/` 新生成器掛 `docs-sync generate`、從 base-web 三語
  locale 檔抽 `backend.*` key→zh-TW/en 對照。落選：後端 log 附譯文欄（字典雙源漂移＋與
  「後端不在地化」憲章精神緊張）、won't-fix（biz.role.protectedRevoke 類鍵對維運仍不友善）。
- **雙產物材質歸家**：對照表落 `docs/generated/reference/`（既有機器生成守門）；拒因字典
  grafana 面板 json 落 deploy 側 provisioning 樹（供容器消費、檔頭注機器生成勿手改），
  `docs-sync check` 延伸一條「該 json 與 locale 重算 diff 零」檢查＝deploy 側生成物同獲機器
  守門。單一真相源＝locale 檔、永不手維。

## 後果

- B-007 收單；後端零改動、憲法零觸碰；洩漏面近零（locale 譯文本已隨前端 bundle 公開、
  grafana 有管理密碼）。
- locale 新增 backend.* 鍵時 generate 自動重算、lint 抓漂移。
