---
id: "0028"
title: ★I18N-WIRING 軌道擴範圍 (iv)——授權 zh-TW 首發 locale 完整建置（全字典＋註冊＋語言選單）
date: 2026-07-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 004-system-settings plan Constitution Check（Q7 gate）＋clarify 拍板全字典；user 親決立 Amendment"
tags: [i18n, base-web, amendment, track-authorization]
---

## 背景

004-system-settings 為 base-web 首刀。clarify（2026-07-05）拍板 zh-TW＝全字典 zh-tw／zh-cn
全量對等（zh-tw 成完整 primary UI）。plan Phase 0 實測：soybean 的 locale **非資料驅動、需
inline 手動註冊**——加完整 zh-tw 除 `src/locales/langs/zh-tw.ts` 新檔外，須改 6 處既有 inline：
`locale.ts`（import＋locale map）、`app.d.ts` `LangType` union、`naive.ts`、`dayjs.ts`、
`store/modules/app/index.ts` `localeOptions`（語言選單）、`index.ts` 預設 locale fallback。這些
逾 ★BASE-WEB-I18N-WIRING (ii)「`src/locales/langs/*` 純新增 backend 命名空間、不改既有」邊界
＝新能力（§III.2 判準：跨面新能力須 Amendment）、Constitution Check Q7 gate 不過。ARCHITECTURE
§8 i18n 列本就宣稱 primary locale＝zh-TW＋語言選單「簡體／繁體／English」——本 Amendment 補齊
其軌道授權。

## 決定

★BASE-WEB-I18N-WIRING 加第 **(iv)** 範圍：

- **(iv)** zh-TW 首發 locale 完整建置：`src/locales/langs/zh-tw.ts` 全字典新檔（對齊 zh-cn
  鍵集）＋註冊 inline（`src/locales/locale.ts` locale map、`src/typings/app.d.ts` `LangType`
  加 `'zh-TW'`、`src/locales/naive.ts`、`src/locales/dayjs.ts`）＋語言選單（`src/store/modules/
  app/index.ts` `localeOptions` 加「繁體中文」）＋預設 locale（`src/locales/index.ts`／app store
  fallback `'zh-CN'`→`'zh-TW'`）——皆走 fork-delta `rev4-inline` 紀律、每改一處於 spec／plan 紀錄。

- 版本 bump 1.0.0 → **1.1.0**（MINOR：軌道授權邊界擴展、§V.3）。

## 後果

- base-web 首刀得完整建 zh-TW primary UI（全 ~515 鍵繁化）＋語言選單三語（簡／繁／English）。
- locale 對等 lint 守全字典 zh-tw／zh-cn 鍵集一致（ARCHITECTURE §8）。
- 本刀範圍較 ADR 0008「最輕」為重（user 明示採納）；zh-TW 全量翻譯落本刀、非另刀。
- (iv) 為一次性 locale 建置授權；後續 locale 維護（upstream rebase 同步）循既有 fork-delta 紀律。
