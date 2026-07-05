---
id: "0030"
title: 會話閒置逾時＝無狀態 sliding refresh（設定可調、無絕對上限）
date: 2026-07-05
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 005-auth-login brainstorm 問答（拍板 2＋5＋6/7、user 指定閒置語意）"
tags: [auth, session, settings, behavior]
---

## 背景

user 拍板的會話語意＝閒置逾時：有活動就活著、閒置滿 N 分鐘後任一請求跳訊息登出、
N 可於 /manage/system-settings「工作階段設定」群組調整（預設 60 分）。純 JWT `exp`
不會隨活動滑動；session 生命週期完整設計（rotation／single-session／denylist）屬
session 刀（B-021 一次設計完整），本刀不得預佔。004 已預埋 seam：refresh secret 配線
零消費、Claims sid/jti 欄、sys_token 表零寫入。

## 決定

- **sliding refresh（無狀態）**：access TTL＝`min(300s, N×60÷2)`（上限常數 300s；折半條款
  保證 refresh 窗恆長於 access 窗、sliding 恆成立）；refresh TTL＝N＝`session_idle_timeout`
  設定值（分鐘、m003 seed、number、預設 60、registry 範圍 5..=1440）。
  前端 upstream 自動 refresh 機制原樣吃（零前端改動）：access 過期→3333→單飛 refresh→
  後端驗簽＋換發新對（新 jti）→閒置窗推到 now+N 分。
- refresh handler **不落、不查 sys_token**（零 token 狀態、無 rotation／reuse 偵測）；
  僅一條 **使用者活性 gate**（PK 讀 sys_user：status==2 或軟刪→8888）。
- **閒置過期回 8888**（`auth.session.reLogin`、toast＋回登入頁）；不挪用 7777（凍結語意
  ＝`auth.session.kicked` 他處登入、碼→key 映射單一來源）。
- **無絕對上限**：閒置是唯一登出條件；連續活躍永不強制重登。

## 後果（含明示接受的風險）

- 登出界線＝閒置 **[N−access, N]**（顆粒＝access TTL；N=60→[55,60] 分；要更精須 server
  記最後活動時間＝session 狀態、留 session 刀）。
- **refresh token 被竊可無限續命**（每次續命滑窗、無偵測/撤銷手段）——內部 admin 系統
  ＋session 刀將補 rotation/reuse 偵測，本刀明示接受。
- 設定值變更對既有 session 於**下一次續命**生效（最壞舊 N 分窗活完才收斂）。
- 停用帳號：活躍者 ≤5 分內被活性 gate 擋（8888）、閒置者 ≤N 分自然過期；即時逐出
  （denylist）留 session 刀。
- 設定列缺失＝fail-loud 5000（migrate 閘保證存在；壞值防線在寫入端 registry，ADR 0026）。
- session 刀進場時本機制為其重設計輸入；若翻案（如改 rotation 帶狀態）立新 ADR supersede。
