---
id: "0088"
title: 前後端 msg key 治理＝機生字典＋契約閘 Lint24（承 0074 字典生成、補契約守衛半邊）
date: 2026-08-02
status: accepted
supersedes: ["0074"]
superseded_by: []
provenance: "rev4:2026-08-02 圖譜 trace 雙線輪（i18n 契約鏡頭＋主線 parse_locale_backend 實測雙向差集）→B-133/B-134 立項；user 三題親決：閘住 docs-sync Lint24、supersede 0074 合併字典生成與契約守衛、error.rs biz.error 註解改寫"
tags: [i18n, docs-governance, lint, obs]
---

## 背景

ADR 0074 建立「觀測側拒因可讀性」：從 locale 檔機生 `backend.*` 兩語對照表＋grafana
面板 json，單一真相源＝locale 檔、永不手維。該閘守的是**前端字典的內部一致性**
（zh-TW/en-US 鍵集相等、生成物零手維），**契約的另一端（rust 實發 key 集）從未進過任何
比對器**——「後端新增 biz 鍵、前端漏補」全鏈零告警：cargo build 綠（字串字面無型別關聯）、
locale 未動故 docs-sync 零 diff 全綠、只有真人點到該路徑才發現（畫面吐裸識別字）。

2026-08-02 圖譜 trace 輪以機器對賬證實存量缺口恰兩鍵：`system.internal`（生產側 128 處
發射點——任何 DB 錯誤／hash 失敗皆命中）與 `system.notFound`（router fallback），自
error.rs 存在以來未被任何閘點名；人工紀律在高注意力新 feature 上命中率極高（68 個動態鍵
一個不漏）、在低注意力存量邊角上失效——缺乏機器閘的典型失效形。

## 決策

承接 0074 全部既有機制、補上契約守衛半邊，合併為一份 msg key 治理決策：

1. **字典生成面（0074 原機制、原樣續行）**：`backend.*` 兩語對照表落
   `docs/generated/reference/backend-msg-dict.md`＋grafana 面板 json 落 deploy
   provisioning 樹；生成的單一真相源＝locale 檔、永不手維；`docs-sync check` 守生成物
   零 diff。D9 兩語（zh-TW/en-US）對照形制不變。
2. **契約閘 Lint24（新增、B-134 兌現）**：docs-sync 新 lint 條款、pre-commit 每 commit
   無條件跑。後端側掃 `rust-api/server/src` 生產碼靜態抽「實發 msg key 集」＝
   `AppError::Biz|BizData` 構造點字面＋常數名冊間接形（`I18N_CONST_ROSTER` 字面釘死、
   宣告值互驗防腐）＋error.rs `key()` 固定八鍵；`#[cfg(test)]` 區間整段排除、不受支援
   cfg 形 fail-loud。前端側復用 `parse_locale_backend`（zh-tw）。
3. **方向性判準**：後端有前端無＝ERROR（逐鍵指名構造點 file:line＋「三語 locale＋
   app.d.ts Schema 同 commit 補鍵」修法、引 L-094）；前端有後端無＝比對
   `I18N_FRONTEND_INTERNAL_KEYS` 白名單（明細插值內部詞彙表；上線時九鍵＝
   passwordViolation×8＋listSeparator），白名單外＝孤兒鍵 ERROR。
4. **白名單治理雙向斷言**：白名單∩後端實發集必空（腐化即紅）；白名單鍵必在前端字典
   （存在性——九鍵被刪不得靜默綠、與 B-133 同失效類）。
5. **fail-loud 家族紀律**：無法靜態解析構造點／雙側空集／名冊漂移或查無宣告一律 ERROR；
   入口無條件 self-test 四型紅綠（Lint16/21/22 慣例）；severity 一律 ERROR、無 skip。
6. **error.rs 註解改寫**：拿掉「未指定慣傳 `biz.error`」宣稱（該鍵字典無、生產零構造點
   ＝純伏筆；閘上線後未來誤用會被 commit 當下攔下強制補鍵）。

落選／不含：後端 log 附譯文欄（0074 原落選理由續有效——雙源漂移＋「後端不在地化」憲章
緊張）；zh-cn 鍵集斷言不在本閘掃描面（由 app.d.ts Schema 之 vue-tsc typecheck 兜底、
不在 pre-commit——強化候選另立 B-135）；`BizData` 插值佔位符與譯文 `{xxx}` 對齊檢查
（範圍小、性價比低、需解析 rust 巨集——觸發時再議）。

## 後果

- 存量缺口即紅證：閘上線當下實彈恰紅 `system.internal`／`system.notFound` 兩鍵（B-133
  同刀補齊轉綠）——「後端加鍵、前端漏補」自此 commit 當下攔截，防線由人工紀律轉機器閘。
- 成本：Lint24 實測約 0.44s（53 檔 5 萬行、drvfs），佔整條 lint 3%。
- 供 0074 讀者：字典怎麼生成（材質、真相源、grafana 對照）本 ADR 第 1 條原樣承接；新增
  的是「兩端鍵集是否對得上」的契約斷言——生成與斷言正交，合併於此一站式治理。
