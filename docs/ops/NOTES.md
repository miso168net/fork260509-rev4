# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004 系統設定、005 認證縱切、006 會話生命週期、007 登入失敗節流、
  008 IP 存取控制閘）已收刀——**auth family 五刀收官**（005 認證→006 會話→007 帳號維節流→
  008 來源維節流＋信任錨）。各刀 pins／summary／ADR 見 events／STATE。
- 008 收刀（波1第五刀、auth family 最後一把）：一把刀兩台狀態機——①信任錨基建〔真實來源位址
  還原：三層信任錨〔傳輸層對端→CDN 位置錨〔最右 CDN 段、取左鄰非 CDN、剝錨右一切〕→信任代理段
  rightmost-untrusted〕＋兩 overlay〔通道 visitor 標頭、CF 驗證閘〕＋七態信心；XFF 正規化不 panic；
  ★fail-OPEN＝設定破損全空 all-direct、不擴大信任；supersede ADR 0017〕②IP 閘〔白＞黑＞default-allow、
  loopback／私網僅豁免 block、健康／觀測恆放行、既有禁止存取碼不新增〕；其上啟用 per-IP 節流〔IPv6 /64、
  IPv4 /32、GREATEST 兩源拔 reset-on-success、負快取沿 0038、supersede 0038 調整項二〕＋GeoIP region
  〔xdb 第 5 crate、§I.5 例外整檔拷貝、best-effort、boot 守門、ADR 0046〕＋nginx CF 閘與 refreshToken／
  logout 端點限流〔消化 B-072〕＋★寫端自鎖拒寫＝全鏈唯一 fail-closed（島 F3）。憲法 §I.7 島 F v1.6.0
  ＋島 E2 射程釐清＋新★devproxy 軌道（ADR 0042、v1.5.0）；ADR 0042-0047。cargo test 334 綠、base-web
  typecheck 綠、三 lint 閘綠。消化 B-019/020/024/032/035/046/072/073/079；新增 B-080/081。
- 下一步：**auth family 已收官、無既定下一刀**——下一個方向待 brainstorm 拍板。候選線索（見 BACKLOG）：
  ①prod 部署硬化〔信任模型 prod 設定落地＋B-037 TLS／信任拓樸 checklist＋B-080 CDN 錨碼層硬化＋
  B-081 prod Dockerfile xdb 資料檔 COPY〕；②admin 管理面〔B-064 停用帳號／改密／admin 踢除端點，消費
  006 revoke primitive〕；③殘餘清理〔B-074~B-077、B-060/061、B-063/069〕。★信任模型的 prod DNAT 爭點
  （對外 publish 是否保留外部來源 IP）未實測、屬 prod 部署刀 scope。
- 008 遺留：B-080（CDN 錨碼層硬化：Tier-1 只檢查最右 CDN 段、不檢查該 CDN 由傳輸層背書）／
  B-081（prod Dockerfile xdb 資料檔 COPY）。B-018 進一步消化（US5 白名單＝IP 信任豁免，第三方觸鎖
  殘餘再減；徹底緩解仍需信任裝置維度）。
- 007 遺留：B-074（軟區決策負快取）／B-075（captcha 強化＋兩則 UX 觀察）／B-076（schema-gate 白名單
  整批重凍退路）／B-077（unlock op-log 持久化）。
  〔B-072 refreshToken／logout 端點限流、B-073 region 地理解析＝008 已消化。〕
- 006 遺留 primitive／再議：停用帳號／改密／admin 踢除端點（B-064、消費 revoke_others_of_user primitive
  ＋發 session_event(revoked)；併 B-029 改密撤 session）；alova 棧接入真實 auth 時補 idle toast＋onError
  i18n（B-069、ADR 0035/0036 觸發再議）；孤兒 reaper（B-063）。005 遺留 B-060/B-061 仍在。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器＋
  CDP 實機）；★`.vue` template 區標記須用 `<!-- -->` 形（L-119）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite dev 未必熱載新字典、否則 toast／modal 顯 raw key、L-015）。
- ★CDP 驅動登入表單三坑（L-121~L-123）：錯密須先過 client rules（6-18 位字母／數字／底線）否則 validate
  早退零請求；dev API 走 vite proxy（`/proxy-default/*`、不含 `/api`）且 page-context hook 攔不到、resource
  timing buffer 需先 clear；`showErrorMsg` 有 errMsgStack 去重、連兩擊同訊息第二則恆空。
