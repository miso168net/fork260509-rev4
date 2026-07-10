# 路由契約（specs/001-compose-stack/contracts/http-surface.md）。
# 本檔不以 .conf 結尾＝不被 conf.d glob 誤載（by design），由 dev.conf 兩個 server 顯式 include。

# nginx 自答健康點（不轉發；compose healthcheck 與驗收共用）
location = /health {
    default_type text/plain;
    return 200 "ok\n";
}

# ★ 擋門：/metrics 永不對外（紅線的提前閘、先於觀測刀存在）。
#   location /api/ 會剝前綴把 /api/metrics 轉成後端 /metrics；此 exact-match 優先於
#   prefix /api/、直接 404。日後內網 scrape 直打 rust-api:8080/metrics、不經本層、不受影響。
location = /api/metrics {
    return 404;
}

# ★ 007 登入節流：登入端點與取題端點 dedicated exact-match 限流塊（ADR 0037 §F.17 落點 (B)）。
#   專用桶不與 /api/ 一般流量共享——共享桶會逼 burst 開大而稀釋防護精度（rev3 註解自承此妥協）。
#   burst=40 準則：≥ CDP-1(~8)/CDP-2(~10) 單次驗收請求數上限 ×2、優先確保 CDP 驗收不 flaky（L-100）；
#   應用層 per-account 節流才是主防線，本層僅為 per-IP 粗閘。
#   ★exact-match 塊不繼承外層 proxy 指令 ⇒ 完整複製 location /api/ 的 proxy 語意；
#   proxy_pass 帶 URI 形＝匹配整段被替換（/api/auth/login → /auth/login），等價 strip /api 前綴、query string 自動保留。
location = /api/auth/login {
    limit_req zone=auth_limit burst=40 nodelay;
    proxy_pass http://rust-api:8080/auth/login;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-Id $request_id;
}

location = /api/auth/loginCaptcha {
    limit_req zone=auth_limit burst=40 nodelay;
    proxy_pass http://rust-api:8080/auth/loginCaptcha;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-Id $request_id;
}

location /api/ {
    proxy_pass http://rust-api:8080/;   # ★ 末尾 / 必要：strip /api 前綴（路由契約：後端 route 不帶 /api）
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-Id $request_id;
}

location / {
    proxy_pass http://base-web:80;
    # vite dev server HMR 需 websocket 升級頭透傳（$connection_upgrade map 定義於 nginx.conf）
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
