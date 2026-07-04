# NOTES — 當前意圖／下一步

- 波 0 已收口（三刀串行 001→002→003 全收刀、波 0 出口六組檢查表整波重跑全綠——
  含第 1 組 `down -v` 從零重來 429 crate 重編＋migrate 閘＋seed 244；merge SHA 與 pins
  見 events／STATE）：一鍵 dev stack（活書 §7）＋基線 schema＋244 列 seed＋三閘 schema-gate
  ＋entity crate＋統一信封 Res/PageRes（2^53 守衛）＋13 碼 AppError（映射單一來源、保留碼
  構造層凍結）＋router 註冊表＋三類守門＋wire-schema 抽取管線＋契約裁判＋雙向覆蓋閘落地
  （活書 §5／§8）。
- 下一步：波 1 第一功能刀 system-settings（ADR 0008；輸入 B-023／B-051）階段 0 brainstorm
  起手——基建齊備（DB＋entity＋wire envelope／error／router＋契約管線），不需先蓋任何基建。
- demo 驗證端點為暫時物、由首功能刀執行刪除（B-056）；動 typings／加 route 的刀必於單元
  邊界重跑 `python3 tools/wire-schema extract` 並隨 commit（活書 §8 wire 契約列）。
