# fixtures/ — 002-schema-baseline 凍結基準

- **來源**＝rev3 live、擷取 2026-07-03；本目錄 26 檔自來源 workspace `tmp/extract/`
  目錄整拷、byte 級原樣（憑據鏈見 `../data-model.md` §6）。
- **用途**＝閘 1 凍結基準（結構零漂移比對；contracts/gates.md §1／§2）。
- **scratch-columns.txt**＝research.md R7 轉錄互驗基準（雙庫互證時 scratch 庫實際
  欄序 dump；data-model §3 欄序表以此機器 diff 通過後閘 2 才啟用）。
- **seed 總數實測 244**：sys_user 3＋sys_role 3＋sys_user_role 3＋sys_menu 78＋
  casbin_rule 149＋system_settings 8（機器形式＝六支 `json-*.json`；閘 2 seed 基準）。
- **columns-maxlen.txt**＝B-055 varchar 長度 sidecar（ADR 0039；rev4 補件、**不屬凍結集**）：
  自 rev3 live（與 2026-07-03 凍結集同源）於 2026-07-10 唯讀重擷取 12 基線表全部
  `character varying` 欄的 `character_maximum_length`（46 欄；空值＝無長度上限）；
  凍結三檔 byte 不動、長度基準另立此檔，由 `tools/schema-gate gate1` 額外比對。
  欄名為基線原名（比對時經 rename map 映射）；post-baseline 新表（如 `session_event`）
  不在此檔屬正常設計——其長度治理歸各自刀。
- 本目錄檔案凍結不改寫；本 README 為 rev4 新寫說明檔、不屬凍結集。
