# fixtures/ — 002-schema-baseline 凍結基準

- **來源**＝rev3 live、擷取 2026-07-03；本目錄 26 檔自來源 workspace `tmp/extract/`
  目錄整拷、byte 級原樣（憑據鏈見 `../data-model.md` §6）。
- **用途**＝閘 1 凍結基準（結構零漂移比對；contracts/gates.md §1／§2）。
- **scratch-columns.txt**＝research.md R7 轉錄互驗基準（雙庫互證時 scratch 庫實際
  欄序 dump；data-model §3 欄序表以此機器 diff 通過後閘 2 才啟用）。
- **seed 總數實測 244**：sys_user 3＋sys_role 3＋sys_user_role 3＋sys_menu 78＋
  casbin_rule 149＋system_settings 8（機器形式＝六支 `json-*.json`；閘 2 seed 基準）。
- 本目錄檔案凍結不改寫；本 README 為 rev4 新寫說明檔、不屬凍結集。
