# Contract: 統一信封與錯誤碼（003-wire-foundation）

信封／錯誤面的行為契約（驗收比對規則；機器基準＝data-model.md §1~§2）。

## 1. 信封形（universal）

| 面向 | 契約 |
|---|---|
| 欄序 | `data` → `code` → `msg`（序列化輸出逐字此序） |
| code | JSON string（如 `"0000"`）；絕非 number |
| 錯誤 data | `null` 且**不省略**（`{"data":null,...}`） |
| success bool | 不存在（出現＝FAIL） |
| HTTP 總則 | 業務錯誤一律 HTTP 200 信封；例外恰 `4040`→404、`5003`→403 |
| 信封例外端點 | 恰 `/health`（plain text）與 `/metrics`（exposition；endpoint 歸 obs 刀、規則先入常量註記） |

## 2. 錯誤碼與 msg

- 13 碼矩陣逐碼照 data-model §1（code／key／HTTP／可發性）；發碼唯一來源＝碼表
  常量模組；錯誤型→碼映射唯一來源＝錯誤型模組（散裝映射＝FAIL）。
- 4 保留碼：後端**構造層**即不可發出（錯誤型無對應變體）；矩陣列舉測完整性
  （可發碼集合恰 9）。
- `msg` 一律去前綴語意 key（`auth.*`／`system.*`／`biz.*`／`common.*`）；人話字串
  出現於 msg＝FAIL；前端字典接線不在本刀。

## 3. 序列化不變式

- 時間欄：RFC3339 帶時區偏移；naive datetime（無 offset）＝FAIL。
- string 宣告 id 欄：JSON string；number 宣告欄：JSON number＋2^53 守衛
  （超限 fail-loud、靜默截斷＝FAIL）。
- 分頁 `PageRes`：`{current,size,total,records}` camelCase、空頁 `records:[]`；
  `pages`／`success` 出現＝FAIL。

## 4. 負面驗證形（驗收用）

- 未知路由 → HTTP 404＋`4040` 錯誤信封（`data:null`、msg=`system.notFound`）。
- 13 碼逐碼 case：可發碼由測試構造錯誤型→序列化→斷言 HTTP＋信封三欄；保留碼
  斷言不可構造（編譯期）＋集合完整性。
- demo 端點成功形：`code "0000"`、msg=`common.success`、時間欄帶 offset、
  string-id 為字串。
