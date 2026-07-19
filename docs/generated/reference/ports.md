<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/ports — 全量正典表

來源＝docker-compose.yml＋docker-compose.dev.yml＋docker-compose.example.yml 的 ports: 段（generate 重算；配號紀律歸 ADR 0019）。

| 服務 | host port | 容器內 port | 綁定 IP | 來源檔 |
|---|---|---|---|---|
| base-web | 42081 | 80 | 127.0.0.1 | docker-compose.dev.yml |
| front-nginx | 42080 | 80 | 127.0.0.1 | docker-compose.dev.yml |
| front-nginx | 42443 | 443 | 127.0.0.1 | docker-compose.dev.yml |
| grafana | 43000 | 3000 | 127.0.0.1 | docker-compose.dev.yml |
| loki | 43100 | 3100 | 127.0.0.1 | docker-compose.dev.yml |
| postgres | 45432 | 5432 | 127.0.0.1 | docker-compose.dev.yml |
| prometheus | 49090 | 9090 | 127.0.0.1 | docker-compose.dev.yml |
| pushgateway | 49091 | 9091 | 127.0.0.1 | docker-compose.dev.yml |
| redis | 46379 | 6379 | 127.0.0.1 | docker-compose.dev.yml |
| rust-api | 42079 | 8080 | 127.0.0.1 | docker-compose.dev.yml |
| example-dev | 42089 | 80 | 127.0.0.1 | docker-compose.example.yml |
