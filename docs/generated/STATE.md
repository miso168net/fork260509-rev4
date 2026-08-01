<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=7e019d1｜rust-api=4ddb74d

## constitution
- 版本：1.15.0

## 帳面統計
- ADR：86（accepted 80、superseded 6）
- BACKLOG 待辦：32（next：B-128）｜滯後：2
- LESSONS：199 筆（next：L-200）
- events：39 筆（feature_close 19、misc 17、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-31｜misc｜B-127＋B-125 收單（維護輕量軌、maint-b125-b127 分支雙單元序做 workflow 編排、四審全零 blocker）——①B-127：治理工具補副檔名 bootstrap.sh／wf-watchdog.sh、15 檔 47 處活引用全改、L19 舊名禁令擴充（負向前瞻防前綴誤咬）、git mv 保 100755、測試 382→384；②B-125：host 暫存四用途統一 ~/.cache/fork260509-rev4/{secrets,decrypt.XXXXXX,merge.XXXXXX,keygen}、ADR 0084 accepted（不掛 frontmatter supersedes、只翻 0080 之落點值決策——並勘正該值實為 0080 決策 2 非 B-125 條目所稱決策 1）、遷移＝搬檔非重解密（sha256 11/11 全同、逐容器 inspect 全指新路徑、preflight 綠、migrate rc=0）、三舊字面活引用零殘留、舊落點保留待主線處置；看門狗一次 L-144 搶答已依防呆重掛；merge SHA＝6981173860d8a582990dc5d05e545941198243ae
- 2026-07-31｜misc｜B-126 收單（維護輕量軌走 workflow 編排：maint-b126 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——docs-sync 新增 L22 條款：lint 範圍字串「L3～LNN」漂移守衛＝掃源推導上界（finding 呼叫錨形、操作型定義、散文零誤收、推導失效 fail-closed）×RANGE_ROSTER 三檔四處字面逐筆比對（兩型波浪、零命中／缺檔／空名冊 ERROR、無 skip、每跑紅綠 self-test；史料明文排除防誤紅）；同 commit 四處 21→22 全 bump、上線即自證實錄（bump 半途真 repo lint 紅指名 RUNBOOK:296＋pre-commit:3＝018/B-116 連兩例復發那型漏法就此機器閉環）；測試 364→382、突變全殺、成本約 24.5ms；merge SHA＝ee837dcedf453ea1f91241bc8696b9354ee3be21
- 2026-07-31｜misc｜B-114 收單（維護輕量軌走 workflow 編排：maint-b114 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——index_pins 逐庫復用 index_gitlink 歸一 018 嚴格 stage-0 語意（回傳形 (SHA, 跳過原因) 同契約、零第二份過濾邏輯）；gitlink 衝突態與缺席 STATE 顯「未定（原因）」絕不顯 stage 值；條目誤述據實勘正（舊碼末筆 stage 3 theirs 勝出、非「首筆＝祖先」，tempdir 探針實證）；測試 360→364、突變殺證、真 repo generate 零 diff 健康態零回歸、L17/L18 零轉紅；merge SHA＝11efe94bbeafd64b02b52d962a1ace864f232586

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
