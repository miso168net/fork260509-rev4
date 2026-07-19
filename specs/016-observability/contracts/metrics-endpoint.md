# Contract — `/metrics` 指標暴露端點

- **Route**: `GET /metrics`（router.rs `ROUTES` 常數登記＋**contract registry case**——§I.3 覆蓋
  gate：每條 route 必有 case；case 斷言＝非 envelope、text 格式、無認證要求）。
- **回應**: Prometheus text exposition format（`text/plain; version=0.0.4`）；**非 wire 信封**——
  憲法 §I.3 明文 universal 例外之一（另一＝/health）。
- **認證**: 無（prometheus scrape 用）；三處既有預留接上＝`GATE_BYPASS_ENDPOINTS`（ipgate 判定
  序①放行）＋`ENVELOPE_EXCEPTION_ENDPOINTS`（error.rs）＋nginx `location = /api/metrics` 404
  擋塊（不經反向代理對外；dev host loopback 42079 可達＝明文接受、prod 歸部署刀）。
- **內容**: data-model §1 全序列；服務啟動後首次 scrape 即含全部 pre-register 序列（顯式 0）。
- **實作錨**: metrics-exporter-prometheus 0.18.3 df=false——recorder 安裝於 main.rs、handler 吐
  `render()`；HLL gauge 於 handler 現場 PFCOUNT（best-effort、失敗回前值或 0 並計 fail counter）。
