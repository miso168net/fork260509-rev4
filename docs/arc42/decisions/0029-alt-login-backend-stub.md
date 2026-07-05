---
id: "0029"
title: 替代登入端點包處置＝後端 stub（B-008 三選一收斂）
date: 2026-07-05
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 005-auth-login brainstorm 問答（拍板 1/7）；rev3:DECISIONS§1-⚠️c＋⚠️m（K1-12/22、帳實分叉）"
tags: [auth, scope, fork-delta]
---

## 背景

soybean upstream 登入頁自帶 4 個替代登入表單殼（code-login／register／reset-pwd／
bind-wechat）＋假 captcha（setTimeout 假動作）：前端可達、按「確定」彈假「驗證成功」、
後端零實作。rev3 曾拍「做」（⚠️c）卻始終未落地（⚠️m 註記 mapping 實測全缺）——決策帳
記「已決做」、實碼「全缺」，即帳實分叉；最終整包延未來版。rev4 立 B-008 要求 auth 刀
開場即三選一（做真／stub／砍表單）收斂帳實。真登入（pwd-login）不在此題、一定做真。

## 決定

- **後端 stub**：立 4 條 public stub route（`POST /auth/sendCaptcha`／`codeLogin`／
  `register`／`resetPwd`），一律回 `2222 Biz("biz.auth.notSupported")`；照常掛 ROUTES
  註冊＋契約 case。
- **前端表單保留可達、改真打 stub**：三表單 handleSubmit＋captcha hook（成功才倒數）
  改為呼叫 stub wrapper（`service/api/rev4-auth-stub.ts` 新檔；表單檔修改型 fork-delta
  帶 `原行:`）；訊息經 `backend.biz.auth.notSupported` 三語 i18n toast「該功能暫未開放」。
- bind-wechat 空殼（無提交行為）不立 stub、不接線。

## 後果

- 帳實收斂：UI 不再對使用者說謊（假 success 消滅）、後端與前端行為一致且可測。
- 未來做真時（alt-login 真流程＋captcha 收發基建），stub 端點即替換點；B-027（confirm-rule
  race）／B-028（真驗證）／B-030（初始密碼政策）屆時觸發，本刀不預佔。
- 養護成本：4 route＋4 契約 case＋1 locale 鍵＋若干 fork-delta 修改型標記（fork-delta-lint
  護航 upstream rebase）。
