# Contract — 告警⑥/⑥b 新增＋⑤/⑤b 射程收斂（017；擴充 016 contracts/alerting-delivery.md）

016 告警評估鏈慣例（A query→B reduce last→C threshold；for: 0s；noDataState: OK；
execErrState: Alerting；severity: warning；annotation 僅規則名/現值/時戳、零原始 log 行；
單一 webhook contact point 全路由）全數繼承。本檔載四條規則的 expr 契約——逐字對齊面。

## 背景（research R1）

prometheus scrape pushgateway `honor_labels: true`＝push 端 grouping key label（`reaper_job`）
保留進序列；⑤/⑤b 現行 expr 無 job 維 matcher——audit-retention 心跳進場後將被⑤/⑤b 誤掃
（射程重疊）。故本刀**四條規則一組交付**：⑤/⑤b 收斂＋⑥/⑥b 新增。

## ⑤ reaper-heartbeat-timeout（既有、expr 收斂）

- uid 不變 `obs016-reaper-heartbeat-timeout`；僅 A 段 expr 改：
  `time() - reaper_last_success_timestamp{mode="execute", reaper_job="token-reap"}`
- 門檻 gt 172800 不變；其餘欄零改動。

## ⑤b reaper-mode-misconfig（既有、expr 收斂）

- uid 不變 `obs016-reaper-mode-misconfig`；A 段 expr 兩側補 matcher：
  `reaper_last_success_timestamp{mode="dry-run", reaper_job="token-reap"} unless ignoring(mode) reaper_last_success_timestamp{mode="execute", reaper_job="token-reap"}`

## ⑥ audit-retention-heartbeat-timeout（新）

- uid `obs017-audit-retention-heartbeat-timeout`；title `audit-retention-heartbeat-timeout`。
- A 段 expr：
  `time() - reaper_last_success_timestamp{mode="execute", reaper_job="audit-retention"}`
- C threshold gt **172800**（＝2×`REAPER_INTERVAL_SECS` 預設 86400——與⑤共用同一互錨；
  調 INTERVAL MUST 同步改⑤/⑥兩門檻＋compose 兩檔註解錨）。
- noDataState: OK＝未起 jobs profile／零序列不誤紅（⑤ 拍板沿用）。
- annotation summary 形：`audit-retention-heartbeat-timeout：retention 心跳逾時（現值 {{ $values.B }} 秒、判準 > 172800）`。

## ⑥b audit-retention-mode-misconfig（新）

- uid `obs017-audit-retention-mode-misconfig`；title `audit-retention-mode-misconfig`。
- A 段 expr：
  `reaper_last_success_timestamp{mode="dry-run", reaper_job="audit-retention"} unless ignoring(mode) reaper_last_success_timestamp{mode="execute", reaper_job="audit-retention"}`
- 復歸機制＝execute 心跳 PUT 整組替換汰換本組 dry-run 序列（contracts/reaper-cli-audit-retention.md 心跳節）。

## 交付與驗收約束

- rules.yml 規則總數 11→**13**；四條變更（⑤/⑤b 改＋⑥/⑥b 新）同 commit 原子交付
  （分批＝射程重疊窗）。
- 部署順序無害性：新規則先載而新心跳未推期間、matcher 查無序列→noDataState=OK 不誤紅；
  舊組殘留序列（無 reaper_job label）不 match 任何收斂後規則→不誤紅（清舊組＝衛生步驟）。
- 驗收（quickstart S6）：13 條全載 health=ok；⑥/⑥b 正負向實轉紅＋復歸；⑤/⑤b 對
  token-reap 行為零回歸；webhook 投遞 annotation 契約零原始 log 行。
