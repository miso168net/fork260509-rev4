# Phase 1 Contracts: 013-ip-rule-admin 端點契約

**零新 route**——013 消費 008 既有五端點；唯一契約變更＝`getIpRuleList` 之 **query 形擴充**（additive、不破既有呼叫）。
**契約 registry 筆數不變**（R7；`server::router::ROUTES` 不增→case_key 雙射無缺口）；`getIpRuleList` 既有 case 之 request query 形須更新＋斷言。

---

## §1 五端點總表（008 as-built；013 消費）

| # | 端點 | 動詞 | 路徑 | 保護 | 013 變更 |
|---|---|---|---|---|---|
| 1 | `getIpRuleList` | GET | `/systemManage/getIpRuleList` | Policy（super-only） | ★**query +3 filter** |
| 2 | `addIpRule` | POST | `/systemManage/addIpRule` | 〃 | 無（消費） |
| 3 | `updateIpRule` | POST | `/systemManage/updateIpRule` | 〃 | 無（消費） |
| 4 | `deleteIpRule` | **DELETE** | `/systemManage/deleteIpRule` | 〃 | 無（消費）★body 載 `{id}`、非 path/query |
| 5 | `restoreIpRule` | POST | `/systemManage/restoreIpRule` | 〃 | 無（消費） |

全端點 casbin 政策 m002 已 seed（R_SUPER）；非超管→**5003／HTTP 403**（`require_policy` 於 handler 前拒、零寫）。

## §2 `getIpRuleList`（★本刀唯一契約變更）

### Request（query、camelCase）

```text
GET /systemManage/getIpRuleList
  ?current=1&size=10
  &wbipCidr=<模糊片段>          # 新、可空；空字串等同未設
  &wbipType=<allow|deny>        # 新、可空；精確
  &deleted=<active|deleted|all> # 新、可空；三態、缺省 all
```

| 參數 | 型 | 預設／守門 |
|---|---|---|
| `current` | `Option<u64>` | 預設 1、下界 1 |
| `size` | `Option<u64>` | 預設 10、clamp [1,100] |
| `wbipCidr` | `Option<String>` | 空字串→None；比對面＝`wbip_cidr::text` ILIKE `%x%`（`%_\` 字面化＋`ESCAPE '\'`、複用 `ilike_contains`） |
| `wbipType` | `Option<String>` | 空字串→None；值域 `allow`｜`deny`、非法→`2222 biz.ipRule.invalidRuleType` |
| `deleted` | `Option<String>` | 空字串→None(=all)；值域 `active`｜`deleted`｜`all`、非法→`2222`（拒因鍵見 §5） |

★多 filter 並存＝**AND** 合取。★三態→WHERE 與排序恆定：見 data-model §3。

### Response（`PageRes<IpRuleRecord>`；envelope 凍結）

```jsonc
{
  "data": {
    "current": 1, "size": 10, "total": 42,
    "records": [{
      "id": 7,                              // JSON number（2^53 守衛）
      "wbipCidr": "203.0.113.7/32",         // ★恆帶遮罩（IpNetwork::to_string）
      "wbipType": "deny",
      "wbipMemo": "掃描源",                  // null 恆在
      "order": 10,                          // null 可
      "deleted": false,                     // 導出 bool
      "createdAt": "2026-07-16T10:00:00+08:00",  // ★新 RFC3339 帶 offset
      "updatedAt": null,                          // ★新（DB nullable）
      "createdBy": "Super",                       // ★新 帳號名｜null
      "updatedBy": null                           // ★新
    }]
  },
  "code": "0000", "msg": "common.success"
}
```

★`deletedAt`／`deletedBy` **不上 wire**。
★`createdBy`／`updatedBy` 經批次 enrich（`user_names_by_ids`）：**含已軟刪用戶查得名**、id 查無→`null`。

## §3 寫端四端點（013 零契約變更、僅消費）

| 端點 | body | 成功 | 備註 |
|---|---|---|---|
| `addIpRule` | `{wbipCidr, wbipType, wbipMemo?, order?}` | `0000`、`data:null` | memo 空字串→None 落庫；cidr 經 `normalize_cidr` |
| `updateIpRule` | `{id, wbipCidr, wbipType, wbipMemo?, order?}` | 〃 | 四欄皆可改（改動唯一鍵→可能 conflict） |
| `deleteIpRule` | `{id}` | 〃 | ★**DELETE 動詞＋JSON body**（前端 `method:'delete'`＋`data`） |
| `restoreIpRule` | `{id}` | 〃 | 已 active＝冪等 `0000`；重入 partial-uniq→conflict |

**四寫端皆過寫端自鎖守門**（島 F F3 唯一 fail-closed 例外）：組「變更後規則集」→同一 `decide` 純函式→操作者當下 `client_ip` 判 Deny＝**拒寫、不落庫、不 reload**。
**寫成功後端自動 reload＋門鈴 PUBLISH**——前端**毋需**追加生效呼叫。

## §4 m010 seed 增量（casbin）

```text
sys_casbin_rule +4（R_SUPER 按鈕政策）：
  ipRule:add / ipRule:edit / ipRule:delete / ipRule:restore
sys_menu.manage_ip-rule.buttons: NULL → ["ipRule:add","ipRule:edit","ipRule:delete","ipRule:restore"]
```
→ `getAllButtons`（＝`sys_menu.buttons` 聯集）候選納入四碼＝角色頁按鈕指派面板可勾（**本刀不指派給任何非 super 角色**）。

## §5 拒因鍵（008 已發射；013 補三語 locale）

`biz.ipRule.{invalidCidr, invalidRuleType, conflict, selfLock, notFound}`——全 `2222`＋HTTP 200 業務信封；非超管 `5003`／HTTP 403。**零新錯誤碼**。
★`deleted` 參數非法值之拒因鍵於實作期定（優先復用既有族、絕不新增碼；若復用不自然則於 tasks 期回報、不自行造碼）。

## §6 前端 fetcher 對帳（`src/service/api/rev4-ip-rule.ts`、WRAPPER 新檔零原行）

| fetcher | 呼叫 | 對應 |
|---|---|---|
| `fetchGetIpRuleList(params)` | `request({url:'/systemManage/getIpRuleList', method:'get', params})` | §2（params 含三 filter） |
| `fetchAddIpRule(data)` | `method:'post'` | §3 |
| `fetchUpdateIpRule(data)` | `method:'post'` | §3 |
| `fetchDeleteIpRule(id)` | ★`method:'delete'`＋`data:{id}` | §3（照 `fetchDeleteMenu` 等六處既有先例） |
| `fetchRestoreIpRule(id)` | `method:'post'`＋`data:{id}` | §3 |

★`id` 走 **number**（不需 rev3 的 `String(id)` 轉換）。
★不改凍結 `system-manage.ts`；直接路徑 `import { request } from '../request'`（不經 barrel、避 vite stale-export）。
</content>
