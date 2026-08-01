<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=ec6ca69｜rust-api=bcd0496

## constitution
- 版本：1.15.0

## 帳面統計
- ADR：87（accepted 81、superseded 6）
- BACKLOG 待辦：34（next：B-133）｜滯後：3
- LESSONS：200 筆（next：L-201）
- events：41 筆（feature_close 20、misc 18、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-08-01｜misc｜mailpit host 配號歸位（維護輕量軌、user 收刀後質詢觸發）——020 引入 mailpit 時 host 配 127.0.0.1:8025、為 reference/ports 全表唯一不帶 4 字頭者，違反 ADR 0019 之 infra 群「4＋well-known」制（grafana 43000／loki 43100／prom 49090／pushgateway 49091／pg 45432／redis 46379 逐項遵守）。成因三段追溯：①SDD 期六產物（research/spec/plan/data-model/contracts/quickstart）直抄 mailpit 官方預設值 8025、全程無人以 ADR 0019 對照 ②U1 唯讀偵察確實示警「配號須避開此表、需 U1 決策」、衝突被機器發現並傳到主線 ③主線裁錯＝選「照 SDD 字面走」並烤進 implementer prompt，且於 review prompt 列「勿翻案」封死質疑通道。歸位＝host 48025（容器內側 8025 官方預設不動、ADR 0019 明定；tests 走服務名 mailpit:8025 與 host 正交零改動）；ADR 0087 accepted 承載配號歸位＋★判例「SDD 產物與既有 accepted ADR 衝突時 ADR 優先、MUST 升級 user 拍板、不得主線自行選邊或封死 review 質疑通道」；ADR 0086 body 依 accepted 不可變不動。驗證＝compose config 綠／mailpit 重建 healthy／48025 readyz 200／舊 8025 refused／容器內 email_verify 14 passed。
- 2026-08-01｜feature_close｜020-email-verify-smtp｜020-email-verify-smtp 收刀——B-028 信箱半邊兌現＋系統首次 SMTP 寄信基建（外層 11＋rust-api 12＋base-web 8 commits、十執行單元 U1~U10 全 workflow 編排）。核心＝①驗證即提交（D3/ADR 0085）：新信箱驗過六位碼才寫入、零 pending 態；已驗證＝lower 比對導出（衛星表 sys_user_email_verify 變體 C、m014＋sys_user 活性唯一 email 索引＋up 前置重複掃描 fail-loud）、單一 seam is_email_verified。②四自助端點（/userCenter：emailCaptcha／sendEmailCode／verifyEmailCode／unbindEmail、皆 Authed 零新 casbin）：captcha claims 加 ctx 必填欄兩端斷言（login/email 機器語境隔離、login 行為案 27 支零紅機器證）；send 固定六步序（captcha 提交即消耗→格式單一守門→SET NX 原子先佔＋日上限 10〔並發 k 筆突發恰 1 封實證 SC-003〕→唯一預檢不回補＝枚舉抑制→同步寄信失敗盡力回補→HS256 憑據簽發〔第四秘鑰、TTL 600s、code_mac 單向、3 次即廢〕）；verify 八步序（島 I1 鎖內重驗＋唯一終判＋used SET NX 消耗先於效果＋衛星 upsert RETURNING＋op-log 恰 2 鍵同 txn）。③admin 守門：validate_email_format 單一驗證點三消費者（無值未變豁免＝存量怪值自癒動線）＋EmailTaken 預檢與 23505 索引兜底雙保險（四寫端齊一）＋清空落 NULL（空字串佔唯一額度之結構性修正）。④mailer（lettre 0.11.22 釘版）：兩態 transport（STARTTLS Required／dev 明文）＋timeout 15s＋charset=utf-8＋明文 AUTH 守門 boot panic（B-131）；SOPS +2 key（10 key）＋preflight 13＋mailpit v1.30.6 dev 收信（prod 零痕跡 SC-008）。⑤前端 email-card：U4 接真後 user 於 CDP 原型拍板 U9 浮窗化改造（卡面 Phone 同構三件式＋Send Code Layer、標題組合式 sendCode＋emailTitle 零新鍵 Phone 可共用）＋U10 修繕（開層先取後開＋in-flight 防重＋三態對稱清理）。⑥三語 backend 12＋2 鍵＋page.userCenter 8 鍵（comingSoon 拍定翻案保留——實測 B-028 另半兩活佔位消費者）。驗收＝全量閘八條全綠（lib 767＋八靶＋schema-gate 四綠＋typecheck＋fork-delta＋preflight＋docs-sync）＋CDP 九場景全 PASS＋負向自證名冊全載體（含 m014 前置掃描 Err 與唯一索引直插 DB 拒實彈）＋final review 異質雙審（安全八不變式對抗推演＋治理九題 as-built 全過；唯一 merge-blocker＝wire 快照未隨 U4 重抽、已修並立 B-128 防再犯）。防呆⑥空間邊界兩度正確運作（U2 13 處 AppState literal＋U8 .dockerignore 皆零擅改升級主線）。RUNBOOK §16 Gmail 節＋§15 勘誤 11 處＋§15.7 守衛擴 10 key。
- 2026-07-31｜misc｜B-127＋B-125 收單（維護輕量軌、maint-b125-b127 分支雙單元序做 workflow 編排、四審全零 blocker）——①B-127：治理工具補副檔名 bootstrap.sh／wf-watchdog.sh、15 檔 47 處活引用全改、L19 舊名禁令擴充（負向前瞻防前綴誤咬）、git mv 保 100755、測試 382→384；②B-125：host 暫存四用途統一 ~/.cache/fork260509-rev4/{secrets,decrypt.XXXXXX,merge.XXXXXX,keygen}、ADR 0084 accepted（不掛 frontmatter supersedes、只翻 0080 之落點值決策——並勘正該值實為 0080 決策 2 非 B-125 條目所稱決策 1）、遷移＝搬檔非重解密（sha256 11/11 全同、逐容器 inspect 全指新路徑、preflight 綠、migrate rc=0）、三舊字面活引用零殘留、舊落點保留待主線處置；看門狗一次 L-144 搶答已依防呆重掛；merge SHA＝6981173860d8a582990dc5d05e545941198243ae

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
