<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/backend-msg-dict — 拒因字典（機器生成）

來源＝base-web/src/locales/langs/zh-tw.ts＋base-web/src/locales/langs/en-us.ts 之 backend.* 鍵樹（generate 重算；B-007／FR-014、全鏈零手維）。

| key | zh-TW | en-US |
|---|---|---|
| auth.login.captchaRequired | 請完成驗證碼後再試 | Please complete the captcha and try again |
| auth.login.failed | 使用者名稱或密碼錯誤 | Incorrect username or password |
| auth.login.locked | 登入失敗次數過多，請稍後再試 | Too many failed login attempts, please try again later |
| auth.session.kicked | 您的帳號已在他處登入 | Your account is logged in on another device |
| auth.session.reLogin | 請重新登入 | Please log in again |
| auth.token.expired | 登入已過期 | Login expired |
| biz.audit.invalidTable | 清理標的不在允許清單內 | The purge target is not in the allowed list |
| biz.audit.purgeBelowFloor | 清理保留天數不可低於 {minDays} 天 | Retention days cannot be below {minDays} days |
| biz.auth.mustChangePassword | 請先變更密碼後再繼續操作 | Please change your password before continuing |
| biz.auth.notSupported | 該功能暫未開放 | This feature is not yet available |
| biz.ipRule.conflict | 相同網段與類型的現役規則已存在 | An active rule with the same CIDR and type already exists |
| biz.ipRule.invalidCidr | 網段格式不正確（IPv4／IPv6 CIDR） | Invalid CIDR format (IPv4/IPv6) |
| biz.ipRule.invalidRuleType | 規則類型或參數值無效 | Invalid rule type or parameter value |
| biz.ipRule.notFound | IP 規則不存在或已刪除 | IP rule does not exist or has been deleted |
| biz.ipRule.selfLock | 此寫入會封鎖您目前的來源位址，操作已拒絕 | This change would block your current source address; operation rejected |
| biz.menu.cycleDetected | 不可將選單移至自身或其子孫之下 | A menu cannot be moved under itself or its descendants |
| biz.menu.hasChildren | 選單下尚有子項，請先處理子項 | This menu still has child items; please handle the child items first |
| biz.menu.menuTypeImmutable | 選單類型建立後不可修改 | Menu type cannot be changed after creation |
| biz.menu.notFound | 選單不存在 | Menu not found |
| biz.menu.parentDeleted | 父層選單已刪除，請先復原父層 | Parent menu has been deleted; please restore the parent first |
| biz.menu.parentNotFound | 父層選單不存在 | Parent menu not found |
| biz.menu.protectedMenu | 系統內建選單，不可刪除 | System built-in menu cannot be deleted |
| biz.menu.routeNameExists | 路由名稱已存在 | Route name already exists |
| biz.menu.routeNameImmutable | 路由名稱建立後不可修改 | Route name cannot be changed after creation |
| biz.menu.routeNameInvalid | 路由名稱格式不正確（僅允許字母、數字、底線、連字號，最長 100 位） | Invalid route name (letters, digits, underscore and hyphen only, up to 100 characters) |
| biz.policy.notRestorable | 該歸檔授權不可復原 | This archived grant cannot be restored |
| biz.role.cannotDeleteSelfRole | 不能刪除目前登入使用者所屬的角色 | Cannot delete a role assigned to the current user |
| biz.role.cannotDisableSelfRole | 不能停用目前登入使用者所屬的角色 | Cannot disable a role assigned to the current user |
| biz.role.codeExists | 角色編碼已存在 | Role code already exists |
| biz.role.codeImmutable | 角色編碼建立後不可修改 | Role code cannot be changed after creation |
| biz.role.codeInvalid | 角色編碼格式不正確（僅允許字母、數字、底線，最長 64 位） | Invalid role code (letters, digits and underscore only, up to 64 characters) |
| biz.role.inUse | 該角色掛有 {userCount} 個使用者，不可刪除 | This role is assigned to {userCount} user(s) and cannot be deleted |
| biz.role.notFound | 角色不存在 | Role not found |
| biz.role.protectedRevoke | 存在受保護的授權，無法撤銷 | Some protected grants exist and cannot be revoked |
| biz.role.seededProtected | 系統內建角色，不可刪除 | System built-in role cannot be deleted |
| biz.role.superCannotDisable | 超級管理員角色不可停用 | The super administrator role cannot be disabled |
| biz.systemSettings.invalidValue | 設定值無效 | Invalid setting value |
| biz.systemSettings.notFound | 設定項不存在 | Setting item not found |
| biz.unlock.invalidDimension | 解鎖維度無效（僅支援帳號維與 IP 源維） | Invalid unlock dimension (only the user and IP dimensions are supported) |
| biz.unlock.invalidTarget | 解鎖標的無效（帳號維需帳號名稱、IP 源維需有效 IP 位址） | Invalid unlock target (user dimension requires a user name; IP dimension requires a valid IP address) |
| biz.user.cannotChangeSelfRoles | 不能變更目前登入使用者的角色指派 | Cannot change the role assignment of the currently logged-in user |
| biz.user.cannotDeleteSelf | 不能刪除目前登入使用者 | Cannot delete the currently logged-in user |
| biz.user.cannotDisableSelf | 不能停用目前登入使用者 | Cannot disable the currently logged-in user |
| biz.user.cannotKickSelf | 不能踢除目前登入使用者 | Cannot kick the currently logged-in user |
| biz.user.oldPasswordMismatch | 舊密碼不符 | Old password is incorrect |
| biz.user.passwordMismatch | 兩次輸入的新密碼不一致 | The two new passwords do not match |
| biz.user.passwordPolicy | 密碼不符合密碼政策：{violations} | Password does not meet the password policy: {violations} |
| biz.user.passwordSameAsOld | 新密碼不得與舊密碼相同 | New password must not be the same as the old password |
| biz.user.passwordViolation.forbidUsername | 不可與使用者名稱相同 | must not be identical to the user name |
| biz.user.passwordViolation.maxBytes | 位元組數超過上限 | byte length exceeds the limit |
| biz.user.passwordViolation.maxLength | 長度超過政策上限 | length exceeds the policy maximum |
| biz.user.passwordViolation.minLength | 長度未達政策下限 | length below the policy minimum |
| biz.user.passwordViolation.requireDigit | 須包含數字 | must contain a digit |
| biz.user.passwordViolation.requireLowercase | 須包含小寫字母 | must contain a lowercase letter |
| biz.user.passwordViolation.requireSpecial | 須包含特殊符號 | must contain a special character |
| biz.user.passwordViolation.requireUppercase | 須包含大寫字母 | must contain an uppercase letter |
| biz.user.pwdSetTooFrequent | 密碼設定過於頻繁，請於 {remainingSeconds} 秒後再試 | Password was set too recently, please try again in {remainingSeconds} seconds |
| biz.user.roleNotFound | 所選角色不存在或已刪除 | The selected role does not exist or has been deleted |
| biz.user.seededProtected | 系統內建帳號，不可刪除 | System built-in account cannot be deleted |
| biz.user.sessionPolicyInvalid | 會話策略值無效（僅允許 inherit、single、multi） | Invalid session policy value (inherit, single or multi only) |
| biz.user.superCannotDisable | 超級管理員帳號不可停用 | The super administrator account cannot be disabled |
| biz.user.superRoleProtected | 不可解除超級管理員帳號的超管角色指派 | Cannot remove the super administrator role assignment from the super administrator account |
| biz.user.userNameExists | 使用者名稱已存在 | User name already exists |
| biz.user.userNameImmutable | 使用者名稱建立後不可修改 | User name cannot be changed after creation |
| biz.user.userNameInvalid | 使用者名稱格式不正確（僅允許字母、數字、底線、連字號，最長 64 位） | Invalid user name (letters, digits, underscore and hyphen only, up to 64 characters) |
| biz.user.userNotFound | 使用者不存在 | User not found |
| common.listSeparator | 、 | ,  |
| common.success | 操作成功 | Operation successful |
| system.forbidden | 沒有權限執行此操作 | You do not have permission to perform this action |
