---
id: "0022"
title: 部署腳本輔助映像沿 latest——FR-013 釘版義務的邊界豁免
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-03 001-compose-stack U2 釘版程序問答（雙查攤開、user 拍板）"
tags: [deploy, versioning]
---

## 背景

001-compose-stack 的 FR-013 要求版本全數釘完整數字版（映像 tag、工具鏈、工具安裝）；
brainstorm R1 已修掉 rev3 三處浮動（postgres／node／pnpm）。U2 實作部署腳本時發現
R1 清單外一處：generate-secrets.sh／generate-dev-cert.sh 在容器內跑 openssl 所用的
輔助映像，rev3 現值＝`alpine/openssl:latest`（浮動）。照釘版程序雙查（Docker Hub
最新數字 tag＝3.5.7，與 latest 同日發布＝同內容）後兩案攤開，user 拍板沿 latest。

## 決定

部署腳本的**輔助容器映像**（alpine/openssl）沿 `latest` 浮動 tag。FR-013 的釘版
義務範圍界定為：環境組成映像（compose service）、工具鏈、工具安裝——腳本輔助映像
不在其內。理由：該容器僅執行 `openssl rand`／x509 簽章的短命一次性工作，不進
compose stack、不影響運行環境的重現性；對 openssl CLI 介面的版本敏感度極低。

## 後果

- 腳本零版本維護成本；日後若 openssl CLI 介面不相容變更弄壞腳本，屆時再釘（風險
  已拍板承擔）。
- 本豁免僅及腳本輔助映像；任何 compose service 映像、工具鏈、工具安裝仍受 FR-013
  全額約束。
- spec.md FR-013 補記本例外（引 ADR 0022）。
