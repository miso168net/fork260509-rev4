---
id: "0042"
title: 新增 ★BASE-WEB-DEVPROXY-WIRING 軌道（dev 反代拓樸修正，嚴限三處）
date: 2026-07-11
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-10 B-079 拍板（同源 /api＋vite proxy 直指 rust-api＋.env.prod 拆 apifox mock）＋2026-07-11 008-ip-gate analyze C1 拍板（env key 案、軌道授權三處；user 親決）；需求源＝FR-041 施工分段 S0 前置、L-125/L-126"
tags: [constitution-amendment, fork-delta, base-web, dev-topology]
---

## 背景

dev 環境現行反代拓樸有兩處實測缺陷（2026-07-10 偵察落簿）：

- **L-125**：vite proxy target 指回 front-nginx，dev 每發 API 雙穿反代（vite→front-nginx→rust-api）、
  且 `.env` 產生雙重身分（`/proxy-default` 前綴與 prod 的 `/api` 不同形）；`pnpm build:test` 產物無法連通後端。
- **L-126**：loopback publish 下 rust-api 看到的 `remote_addr` 恆為 docker gateway＝dev 的 per-IP 節流
  永遠落同一常數桶，008-ip-gate 的信任錨／per-IP 機制在 dev 無區辨力。

008-ip-gate 的 **FR-041**（施工分段 S0）要求 dev 的 API 請求與 prod 同形（同源相對前綴、單跳、
轉發鏈一元素），使本刀實機驗收與正式環境等價。B-079 拍板修法＝同源 `/api`＋vite proxy 直指
`rust-api:8080`＋`.env.prod` 拆 apifox mock。

此修正需動三個 base-web 受控檔，**皆逾現有五★軌道枚舉**（MODAL／I18N／AUTH／LOGOUT-UX／
LOGIN-CAPTCHA 皆與 dev 反代拓樸無關）：

- `src/utils/service.ts`、`build/config/proxy.ts`：**首筆 fork-delta 修改型**（兩檔現無任何 `rev4-inline` 標記）。
- `src/typings/vite-env.d.ts`：新增型——★**upstream 既有檔、非 `typings/api/` 新檔，不落 ADAPT 涵蓋**
  （008 analyze C1 CRITICAL：若軌道只授權前兩處，動此檔即違憲 §I.1）。

曾評估「寫死案」（proxy target 直接寫常數 `http://rust-api:8080`、不動 vite-env.d.ts、軌道僅兩處），
user 拍板取 **env key 案**（新增 `VITE_PROXY_TARGET`，保未來可換 target 的彈性）——故軌道授權**三處**。

比照 ADR 0031（AUTH-WIRING）／0034（LOGOUT-UX-WIRING）／0040（LOGIN-CAPTCHA-WIRING）先例，
於 008 plan Constitution Check Q2/Q7 觸發、走 §V.2 Amendment。

## 決定

新增 ★ 軌道 **BASE-WEB-DEVPROXY-WIRING**（constitution §III.2），授權且**嚴格限三處**：

- **(i) 同源前綴**：`src/utils/service.ts` `createProxyPattern` 預設值 `/proxy-default`→`/api`
  （修改型帶 `原行:`）——dev 的 API 請求與 prod 同形（同源相對前綴、單跳）。
- **(ii) proxy target 推導**：`build/config/proxy.ts` target 由 `item.baseURL` 改讀新 env key
  `VITE_PROXY_TARGET`（值＝`http://rust-api:8080`；修改型帶 `原行:`）——vite dev proxy 直指
  rust-api、消除雙穿 front-nginx 迴圈（L-125）。
- **(iii) env key 宣告**：`src/typings/vite-env.d.ts` 新增 `VITE_PROXY_TARGET` 宣告（新增型圈界）
  ——upstream 既有檔、不落 ADAPT，須本軌道顯式授權（C1 拍板＝env key 案）。

**紀律**：

- 嚴格限此三處、嚴限「dev 反代拓樸」用途；第四處／其他用途 → §V.2 Amendment。
- `.env`／`.env.test`／`.env.prod` 的值變更（含加 `VITE_PROXY_TARGET=`、`/proxy-default`→`/api`、
  拆 apifox mock）走既有 ADAPT 涵蓋、不屬本軌道射程。
- 走 fork-delta `rev4-inline` 紀律＋`tools/fork-delta-lint` 機器強制：修改型帶逐字 `原行:`、新增型走圈界標記。
- 每改一處在 spec／plan 內紀錄（位置＋改動內容＋upstream 衝突風險評估）。

constitution MINOR bump（§V.3「新增 ★ 軌道」）→ **v1.4.1 → v1.5.0**；軌道全文入 §III.2、與本 ADR 同 commit
（治理產物於 S0 完成時即 commit、不延收刀——plan Complexity Tracking 拍板）。

## 後果

- 008 plan Constitution Check **Q2／Q7 GATE 解除**（Q9 島 F 進場屬另一 Amendment、收刀期 T045 親決）。
- `service.ts`／`proxy.ts` 自本刀起帶 fork patch，upstream rebase 時依 `原行:` 註解對照解衝突；
  `vite-env.d.ts` 新增型圈界段落於 rebase 時整段保留。
- dev/prod 拓樸同形（單跳、XFF 一元素）→ 008 信任錨／per-IP 的 crafted-XFF 實機驗收有意義（SC-011）；
  `pnpm build:test` 產物可連通後端；`.env.prod` 與 apifox mock 解耦。
- ★dev 下 `:42081`（vite 直連）自此成零限流直達路徑，驗收一律經 `:42080`、`:42081` 同列禁用（quickstart 前提紀律）。
- DNAT 爭點（prod 對外 publish 是否保留外部來源 IP）不在本軌道射程（D8 拍板不實測、記 spec 風險節）。
