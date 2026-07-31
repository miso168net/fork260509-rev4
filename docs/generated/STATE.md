<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=694741f

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：83（accepted 77、superseded 6）
- BACKLOG 待辦：39（next：B-127）｜滯後：2
- LESSONS：199 筆（next：L-200）
- events：33 筆（feature_close 19、misc 11、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-31｜misc｜B-116 收單（維護輕量軌走 workflow 編排：maint-b116 分支、implementer 繼承 Fable×spec/quality 雙審 Opus xhigh、spec blocker 升級主線後 resumeFromRunId 續跑）——docs-sync 新增 L21 條款：EXEC_BIT_ROSTER 顯式名冊 14 支（hooks 4＋deploy 5＋python 工具 5、成員資格逐檔叫用形實證、被 source／恆 bash·sh 前綴者 6 支除外記註解）斷言 index stage-0 必 100755、缺席與空名冊 fail-closed ERROR、無 skip、每跑紅綠 self-test；測試 349→360、突變 A~D 全殺、fixture 零汙染真 index；RUNBOOK §12 補列＋範圍字串 L3~L21 同步（.githooks/pre-commit 檔頭漏改由主線 fbf65ee 結清、errata 0 殘留）；復發模式（連兩刀漏改範圍字串）登記 B-126；merge SHA＝25883752c1395d911f616f5670dd48ead6e2f211
- 2026-07-31｜misc｜B-117 收單（維護輕量軌首例走 workflow 編排：maint-b117 分支、implementer 繼承 Fable×spec/quality 雙審 Opus xhigh、六件套全套）——RUNBOOK §15.7 步驟 3 重加密改先寫同目錄 .new 再 mv 蓋回（[ -s ] 擋 rc=0 空檔、失敗清殘檔原檔不動、同裝置警語、與 §15.2 防法同構、< /dev/null 與 --filename-override 語意保留）；spec 審 stub 五案機證修前窗口存在／修後關閉、零 blocker；quality 審唯一 blocker（BACKLOG 未刪列）屬 fix agent 允許清單外、依空間邊界紀律升級主線刪列；merge SHA＝c4326e07dd0463b81b8ed75d0724c5adc4e4d911
- 2026-07-30｜feature_close｜019-secrets-sops｜019-secrets-sops 收刀——機密管理：SOPS+age 密文入版控＋三層掃描防線＋明文落點遷出 repo（86 commits、純外層治理刀）。核心＝①工具鏈（ADR 0079）：sops v3.13.3 官方容器 digest 釘版 wrapper（P1 契約：互動旗標條件化、顯式三變數轉發、明文一律 host 收 stdout＋umask 077、exec bit 走 update-index）＋age v1.3.1 B′ passphrase 加殼 identity（ADR 0080 決策 3；零 gpg 前置）；②密文資產形（ADR 0081）：dev 單檔 deploy/secrets.dev.enc.yaml 8 key 全加密（P2 錨定式單規則、不設範圍選項＝全加密；key 名禁 _unencrypted 後綴連帶紀律）、3 支 composite 不進加密檔由 leaf 重組（dual-write 不變式）；③解密管線 decrypt-secrets.sh（P4 fail-loud：非裸量純量斷言、DIFF 守衛另存 .new 不覆寫、RAW/CLEAN 暫存落 repo 外 XDG 0700、pty 併流剝 CR 濾非資料行）＋preflight 11 支健康閘；④明文遷移（ADR 0080 決策 1/2 解法 2）：SECRETS_DIR 單一真值＝repo 根 .env、三級解析（env 優先→.env 嚴格單行剝 BOM/CR→回退吵鬧失敗）五消費端逐字同口徑（P5.1）＋RUNBOOK §7 輪替表同口徑、落點 ~/.cache/rev4-secrets（ext4；gate #11 翻轉實證＝\\wsl.localhost 可讀 WSL 明文、user 重拍解法 2 維持 B′）；⑤三層掃描防線（ADR 0082）：Betterleaks 事件型廣譜（.gitleaks.toml extend.useDefault＋DSN 自訂規則＋AND 條件 allowlist）×docs-sync L16 狀態型窄集×tools/secret-value-guard.py 值比對確定性層（41 案含 self-test；三盲區誠實入帳：明文缺席 skip fail-open／僅外層 repo／staged 新增行對 tracked 既存明文結構性失明——B-118 實證＝自家防線抓自家 alert_webhook_url 既存明文 L-190）＋pre-push 第二層三 repo 同套（決策 3/4：hooks 共用一檔、core.hooksPath per-machine 邊界由 bootstrap 斷言補償）＋base-web --no-verify 慣例廢止（決策 5：hooksPath 指外層即結構性旁路 husky）；⑥營運程序：RUNBOOK §15 十小節（§15.2 加人四步含產鑰機器化 deploy/generate-age-key.sh＋釘版兩處相等 docs-sync 斷言／§15.3 撤銷四步＋驗收五準則／§15.4 re-encrypt／§15.7 merge 衝突／§15.8 SSH identity 禁令／§15.9 提示次數不寫死）＋§7 輪替表；⑦團隊前提（ADR 0083）：單人期兩級觸發。收刀金鑰儀式（merge 前、user 拍板序）：user 親產真鑰僅交公鑰、加人 updatekeys（8 值密文逐字不變＝R13「不換 data key」實證）並以 SOPS_AGE_KEY_FILE 容器內路徑驗解、7 leaf＋3 composite 實值輪替推進活系統（ALTER ROLE／setup-reaper-role 自驗 SELECT 1／grafana CLI 臨時拉起重設後停回／redis+rust-api force-recreate healthy＋preflight 11 支健康）、set --value-file 逐支 re-encrypt 後 sops -d JSON 與落點 8/8 byte 一致、原子撤銷 rotate -i --rm-age 驗收五準則全過（否定測試＝暫代 stanza 貼回原廠解密 rc=25 MAC-fail 零明文；recipient 2→1；8/8 值密文必變）、暫代鑰刪除真鑰上位預設位、user 終驗 decrypt-secrets.sh 單提示走通 8 支 WRITTEN 零 DIFF；alert_webhook_url 全程不輪替 byte 不變＝SC-007 終證；暫代公鑰 tracked 樹零命中。品質＝測試 347→349、六執行單元 TDD 雙審（Fable 實作×Opus 審查異質配置）＋final holistic review 異質雙審（Opus 機制面×Fable 治理面）零 merge-blocker；SC-001~010 勾稽 PASS；submodule pin 逐字未變（web=d4c66e0、api=694741f）；憲法 v1.14.0 零 Amendment。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
