<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/routes — 全量正典表

來源＝rust-api/server/src/router.rs 的 ROUTES const（generate 重算；handler 閉包不入表）。

| path | method | protection | case_key | envelope 例外 |
|---|---|---|---|---|
| /auth/codeLogin | POST | Public | auth-code-login | 否 |
| /auth/getUserInfo | GET | Authed | auth-get-user-info | 否 |
| /auth/login | POST | Public | auth-login | 否 |
| /auth/loginCaptcha | GET | Public | auth-login-captcha | 否 |
| /auth/logout | POST | Public | auth-logout | 否 |
| /auth/refreshToken | POST | Public | auth-refresh-token | 否 |
| /auth/register | POST | Public | auth-register | 否 |
| /auth/resetPwd | POST | Public | auth-reset-pwd | 否 |
| /auth/sendCaptcha | POST | Public | auth-send-captcha | 否 |
| /health | GET | Public | health | 是 |
| /route/getConstantRoutes | GET | Public | route-get-constant-routes | 否 |
| /route/getUserRoutes | GET | Authed | route-get-user-routes | 否 |
| /route/isRouteExist | GET | Authed | route-is-route-exist | 否 |
| /systemManage/addIpRule | POST | Policy | add-ip-rule | 否 |
| /systemManage/addRole | POST | Policy | add-role | 否 |
| /systemManage/batchDeleteRole | DELETE | Policy | batch-delete-role | 否 |
| /systemManage/deleteIpRule | DELETE | Policy | delete-ip-rule | 否 |
| /systemManage/deleteRole | DELETE | Policy | delete-role | 否 |
| /systemManage/getAllButtons | GET | Policy | get-all-buttons | 否 |
| /systemManage/getAllEndpoints | GET | Policy | get-all-endpoints | 否 |
| /systemManage/getAllPages | GET | Policy | get-all-pages | 否 |
| /systemManage/getAllRoles | GET | Policy | get-all-roles | 否 |
| /systemManage/getIpRuleList | GET | Policy | get-ip-rule-list | 否 |
| /systemManage/getMenuTree | GET | Policy | get-menu-tree | 否 |
| /systemManage/getRoleButton | GET | Policy | get-role-button | 否 |
| /systemManage/getRoleEndpoints | GET | Policy | get-role-endpoints | 否 |
| /systemManage/getRoleList | GET | Policy | get-role-list | 否 |
| /systemManage/getRoleMenu | GET | Policy | get-role-menu | 否 |
| /systemManage/getSystemSettings | GET | Policy | get-system-settings | 否 |
| /systemManage/restoreIpRule | POST | Policy | restore-ip-rule | 否 |
| /systemManage/unlockLogin | POST | Policy | unlock-login | 否 |
| /systemManage/updateIpRule | POST | Policy | update-ip-rule | 否 |
| /systemManage/updateRole | POST | Policy | update-role | 否 |
| /systemManage/updateRoleButton | POST | Policy | update-role-button | 否 |
| /systemManage/updateRoleEndpoints | POST | Policy | update-role-endpoints | 否 |
| /systemManage/updateRoleMenu | POST | Policy | update-role-menu | 否 |
| /systemManage/updateSystemSetting | POST | Policy | update-system-setting | 否 |
