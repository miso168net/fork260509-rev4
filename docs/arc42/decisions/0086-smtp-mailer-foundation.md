---
id: "0086"
title: SMTP 寄信基建首發＝lettre 同步寄送×設定全靜態 env×mailpit dev 驗收——效仿 GitLab Gmail 路徑
date: 2026-07-31
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-31 020-email-verify-smtp brainstorm——四鏡頭研究（wf_471a7c74：lettre／mailpit／Gmail 2026 政策官方文件查證）＋user 親決 D5~D8"
tags: [mail, infra, secrets, deploy, dev-experience]
---

## 背景

系統首次獲得對外寄信能力（現況零寄信依賴；SMTP 僅以 ADR 0071 落選理由存在）。效仿目標＝公司
現用 GitLab-ee 之 SMTP 設定面（smtp.gmail.com 587 STARTTLS＋AUTH LOGIN＋openssl_verify_mode
peer；十四鍵對映見 docs/brainstorms/020-email-verify-smtp.md §0.1）。查證（2026-07-31）：Gmail
2025-03 起停用 SMTP basic auth 但 **app password 明文保留為例外、無淘汰時程**（前提 2SV）；
2000 封/日；From 須為登入帳號或已驗證 alias 否則被改寫。首個消費場景＝ADR 0085 email 驗證碼信。

## 決策（user 親決 2026-07-31；細節見 docs/brainstorms/020-email-verify-smtp.md §1 D5~D8、§2.4~2.6）

1. **lettre 0.11.22 釘版**（雙查：rev3 無先例；官方最新 stable、MSRV 1.85 相容 rust 1.96.1）；
   `default-features = false`、features＝`builder, hostname, smtp-transport, pool, tokio1,
   tokio1-rustls-tls`（純 Rust TLS、容器免 OpenSSL 相依）。
2. **設定全靜態 compose env**（仿 GitLab；零 settings registry 觸及——現行 registry 拒收
   string 型、擴充屬獨立刀）：`APP_SMTP_HOST/PORT/STARTTLS`＋
   `APP_MAIL_FROM/DISPLAY_NAME/REPLY_TO` 六必填；`APP_SMTP_USERNAME` 與
   `APP_MAIL_SUBJECT_SUFFIX`＝**「不設鍵即空語意」兩特例**（plan 對抗式驗證校正——config 對
   「設鍵但空值」panic 拒啟動＝設鍵即必非空的機器強制；base compose 不設此兩鍵、dev 亦不設
   username＝跳過 AUTH、prod 部署層補真值）；`APP_SMTP_STARTTLS` true＝`starttls_relay`
   （`Tls::Required`、憑證＋hostname 驗證預設啟用＝嚴格度≥GitLab peer）、false＝明文僅 dev；
   465 隱式 TLS 不支援。兩態建構有單元測試背書（SC-008）。
3. **機密＝僅 `smtp_password` 一支入 SOPS**（019 全鏈儀式；亂數 leaf 生成——不用 CHANGE-ME
   佔位、config.rs 對其 panic 會炸 dev boot；prod 真值＝Gmail app password、填法入 RUNBOOK）；
   另 `email_verify_secret` 亂數 leaf（金鑰隔離先例、ADR 0085 決策 6 消費）；preflight
   REQUIRED 11→13。
4. **執行模型＝handler 同步 await＋timeout 15s**；失敗回明確錯誤碼；不建 queue、不重試、不做
   非同步投遞（首刀最小形、消費場景增多再議）。
5. **dev 驗收＝mailpit v1.30.6 入 `docker-compose.dev.yml`**（SMTP 1025 內網、UI+API
   127.0.0.1:8025、內建 healthcheck；prod 零痕跡）；E2E 以其 REST API 機器斷言「信寄達且內含
   碼」——真 SMTP 鏈路端對端驗收、非 mock。
6. **Gmail 運維約束入 RUNBOOK**：2SV＋app password 建立、From＝登入帳號或已驗證 alias 硬約束、
   2000 封/日配額與超限行為、帳號改密撤銷全部 app password、量大備選 smtp-relay.gmail.com
   （IP allowlist、10000 收件人/日；不實作僅記載）。

## 候選與落選

- mail-send 0.6.1（活躍但 0.x 早期、生態與文件遠小、需搭同家 builder——基本 SMTP 需求下風險
  高收益無）。
- system_settings 管理頁可調／混合落點（需擴 string 型 validator＋seed＋allowlist；寄信身分屬
  部署級設定、放 DB 實益低）。
- smtp_url 單條密文（非機密捲進密文、換 host 也走 SOPS 儀式、密碼特殊字元 URL encode 出錯面）；
  user＋password 兩支（帳號非真機密、多一支儀式收益無）。
- 腳本式 SMTP sink（自寫協定處理工程量反大）；純 mock（投遞鏈零機器驗收、風險後置 prod）；
  MailHog（2020 起停更）。

## 驗收與殘餘

- SC：dev 棧發碼→mailpit API 撈信抽碼全綠；STARTTLS 兩態建構單元測試；prod compose 對 mailpit
  零引用。
- 殘餘：其他寄信消費場景（密碼重設信、告警 email 通道——ADR 0071 webhook 維持不變）留擴充
  餘地不預建；prod 機密分層仍屬 B-115 遞延；smtp-relay 路徑未實作。
