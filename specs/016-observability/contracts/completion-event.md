# Contract — completion log 事件（B-054）

- **形**: JSON log 單行事件、`target="http.request"`、level=INFO、message=`請求完成`。
- **欄位**: `method`（大寫動詞）／`path`（route path、非含 query）／`status`（HTTP 數值）／
  `latency_ms`（u64）／`trace_id`（sanitize 後值；標頭缺席或被棄用＝欄缺席）。
- **發射點**: 顯式 `tracing::info!`（非 span-close 依賴——/health 類無 in-span event 請求也有）；
  掛點＝request span 之內、ipgate 之外——被 ipgate 擋下（403）的請求亦發、閘門判定序零改動。
- **過濾開關**: env `APP_LOG_EXCLUDE_PATHS`（逗號分隔 path 清單、精確匹配）；預設空＝全記；
  命中之 path 不發 completion event（其餘 log 事件不受影響）；失讀＝視空。
- **loki 端**: json pipeline 攤平為 `fields_method`…`fields_trace_id`；`fields_trace_id` 與
  `sys_access_log.trace_id` 同源＝join 鍵（S2 驗收）。
- **TDD**: test_support 捕捉層斷 target＋全欄位；過濾開關正反測（設清單→該 path 零事件、
  清空→恢復）。
