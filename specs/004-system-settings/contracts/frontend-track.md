# Contract: 前端軌道＋i18n＋守門（004-system-settings；base-web 首刀）

前端行為契約（機器基準＝data-model.md §6；軌道授權＝constitution §III．2）。所有 base-web
inline 改動走 fork-delta `rev4-inline` 標記（修改型原行註解保留＋標記、新增型圈界；每處於 tasks 紀錄）。

## 1. 軌道歸屬（逐檔）

| 檔／面 | 軌道 | 類型 |
|---|---|---|
| `src/typings/api/rev4-system-settings.d.ts` | BASE-WEB-ADAPT（免授權） | 純新增新檔 |
| `src/service/api/rev4-system-settings.ts` | BASE-WEB-WRAPPER（免授權） | 純新增新檔（rev4- 前綴、直接路徑 import） |
| `views/manage/system-settings/index.vue`（＋route regen） | ★MODAL-WIRING (e) | 新管理頁（設定表單＝標準 manage 頁、spec 記授權依據） |
| `src/service/request/index.ts:71/109` msg→$t | ★I18N-WIRING (i) | 修改型 inline（不碰碼分組/retry） |
| `backend` 命名空間＋settings key（zh-cn/en-us/zh-tw 三檔） | ★I18N-WIRING (ii) | 純新增命名空間 |
| `App.I18n.Schema` 加 backend／systemSettings 型 | ★I18N-WIRING (iii) | 純新增型 |
| `langs/zh-tw.ts` 全字典＋6 inline 註冊 | ★I18N-WIRING (iv)（ADR 0028、v1.1.0） | 新檔＋修改型 inline |

## 2. i18n 契約

- **(i)**：`index.ts:71`（modal content）＋`:109`（onError message）將 wire `msg`（key）經 `$t` 譯 `backend.*` 顯示；**不改** logout/modalLogout/expiredToken 碼分組與 retry 控制流（改＝FAIL）。
- **(ii)**：`backend` top-level 命名空間、key＝`backend.<root>.<entity>.<condition>`（映射 wire msg 如 `biz.systemSettings.*`／`system.forbidden`／`common.success`）；settings 頁字串＝`page.manage.systemSettings.*`。
- **(iv) 全 zh-tw**：`langs/zh-tw.ts` 對齊 zh-cn 全 10 命名空間（~515 鍵）＋backend＋settings；6 inline 註冊（locale.ts/app.d.ts LangType 加 zh-TW/naive.ts/dayjs.ts/store localeOptions 加繁體/index.ts 預設 zh-TW）。

## 3. 頁面契約（★(e)）

- KV 頁：前綴分區（`password_*`→密碼策略區／其餘→會話設定區、空區略過、保 server 序）。
- 型別驅動控件：`enum:on,off`→`NSwitch`（on/off 值對映）／`number`→`NInputNumber`（per-key min/max/step 1/precision 0、失焦提交）／其他→純文字。
- 互動：提交後**恆 refetch** server 真值（成功 toast、失敗攔截器 modal）。
- route：elegant-router `pnpm gen-route` 自動生成 `manage_system-settings`；手填 meta（roles=super/icon/order）regen 保留性施工實測。

## 4. 守門（typecheck+lint、無 vitest——user 拍板 B）

- **locale 對等 lint**（§8「隨 base-web 首刀建立」）：zh-tw／zh-cn／en-us **全字典**鍵集一致、pre-commit 擋；漏鍵指名。
- **vue-tsc typecheck**（型別閘門）：`Record<LangType,Schema>`／`Record<LangType,NaiveLocale>`／route `Record<I18nRouteKey,string>`——漏語言/漏鍵/型不符全紅。★`localeOptions` 純陣列不受型強制、語言選單漏加繁體不會紅（tasks 明列此手動項）。
- **datetime formatter lint**（§8 後半、base-web 首刀建立）：前端 lint 禁繞過 formatter 裸格式化。
- **lint**（oxlint+eslint）＋**typecheck** 綠＝前端驗收面（無 runtime 單元測試）。
- **fork-delta lint**（若建）：`rev4-inline` 標記覆蓋掃描（B-052 面、實作定是否本刀建）。

## 5. 前端 live 驗證限制（拍板 7）

- 動態路由/選單需 super 身分（roles 過濾）＝無登入無法瀏覽器點進設定頁；本刀維持 static 模式（dynamic 需 getUserRoutes＝auth 刀）。
- 前端達成＝typecheck＋lint＋locale lint 綠＋契約與後端 wire 對齊（typings match）；login-gated 走查留 auth 刀。
