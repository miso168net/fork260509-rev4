<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/schema — 全量正典表

來源＝docs/ops/reference-src/schema-snapshot.json（refresh 自實庫撈）＋docs/ops/reference-src/archetype-map.json（變體歸屬）；由 generate 重算。seaql_migrations 除外。

## casbin_rule（archetype D 治理）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('casbin_rule_id_seq'::regclass) |
| ptype | character varying(18) | 否 | — |
| v0 | character varying(125) | 否 | — |
| v1 | character varying(125) | 否 | — |
| v2 | character varying(125) | 否 | — |
| v3 | character varying(125) | 否 | — |
| v4 | character varying(125) | 否 | — |
| v5 | character varying(125) | 否 | — |
| protected | boolean | 否 | false |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |

索引：
- casbin_rule_pkey｜CREATE UNIQUE INDEX casbin_rule_pkey ON public.casbin_rule USING btree (id)
- unique_key_sea_orm_adapter｜CREATE UNIQUE INDEX unique_key_sea_orm_adapter ON public.casbin_rule USING btree (ptype, v0, v1, v2, v3, v4, v5)

約束：
- casbin_rule_created_at_not_null｜NOT NULL created_at
- casbin_rule_id_not_null｜NOT NULL id
- casbin_rule_pkey｜PRIMARY KEY (id)
- casbin_rule_protected_not_null｜NOT NULL protected
- casbin_rule_ptype_not_null｜NOT NULL ptype
- casbin_rule_v0_not_null｜NOT NULL v0
- casbin_rule_v1_not_null｜NOT NULL v1
- casbin_rule_v2_not_null｜NOT NULL v2
- casbin_rule_v3_not_null｜NOT NULL v3
- casbin_rule_v4_not_null｜NOT NULL v4
- casbin_rule_v5_not_null｜NOT NULL v5
- unique_key_sea_orm_adapter｜UNIQUE (ptype, v0, v1, v2, v3, v4, v5)

## sys_access_log（archetype B append-only 日誌）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_access_log_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 否 | — |
| http_status | integer | 否 | — |
| http_method | text | 否 | — |
| http_path | text | 否 | — |
| real_ip | inet | 否 | — |
| peer_ip | inet | 是 | — |
| x_forwarded_for | text | 是 | — |
| ip_confidence | text | 是 | — |
| region | text | 是 | — |
| trace_id | text | 是 | — |

索引：
- idx_access_log_created_at｜CREATE INDEX idx_access_log_created_at ON public.sys_access_log USING btree (created_at)
- idx_access_log_operator_time｜CREATE INDEX idx_access_log_operator_time ON public.sys_access_log USING btree (created_by, created_at)
- sys_access_log_pkey｜CREATE UNIQUE INDEX sys_access_log_pkey ON public.sys_access_log USING btree (id)

約束：
- sys_access_log_created_at_not_null｜NOT NULL created_at
- sys_access_log_created_by_not_null｜NOT NULL created_by
- sys_access_log_http_method_not_null｜NOT NULL http_method
- sys_access_log_http_path_not_null｜NOT NULL http_path
- sys_access_log_http_status_not_null｜NOT NULL http_status
- sys_access_log_id_not_null｜NOT NULL id
- sys_access_log_pkey｜PRIMARY KEY (id)
- sys_access_log_real_ip_not_null｜NOT NULL real_ip

## sys_casbin_policy_archive（archetype D 治理）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_casbin_policy_archive_id_seq'::regclass) |
| created_at | timestamp with time zone | 是 | — |
| created_by | bigint | 是 | — |
| archived_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| archived_by | bigint | 是 | — |
| archive_reason | character varying(32) | 否 | — |
| ptype | character varying(18) | 否 | — |
| v0 | character varying(125) | 否 | — |
| v1 | character varying(125) | 否 | — |
| v2 | character varying(125) | 否 | — |
| v3 | character varying(125) | 否 | ''::character varying |
| v4 | character varying(125) | 否 | ''::character varying |
| v5 | character varying(125) | 否 | ''::character varying |

索引：
- idx_casbin_archive_archived_at｜CREATE INDEX idx_casbin_archive_archived_at ON public.sys_casbin_policy_archive USING btree (archived_at)
- idx_casbin_archive_role_dim｜CREATE INDEX idx_casbin_archive_role_dim ON public.sys_casbin_policy_archive USING btree (v0, v2)
- sys_casbin_policy_archive_pkey｜CREATE UNIQUE INDEX sys_casbin_policy_archive_pkey ON public.sys_casbin_policy_archive USING btree (id)

約束：
- sys_casbin_policy_archive_archive_reason_not_null｜NOT NULL archive_reason
- sys_casbin_policy_archive_archived_at_not_null｜NOT NULL archived_at
- sys_casbin_policy_archive_id_not_null｜NOT NULL id
- sys_casbin_policy_archive_pkey｜PRIMARY KEY (id)
- sys_casbin_policy_archive_ptype_not_null｜NOT NULL ptype
- sys_casbin_policy_archive_v0_not_null｜NOT NULL v0
- sys_casbin_policy_archive_v1_not_null｜NOT NULL v1
- sys_casbin_policy_archive_v2_not_null｜NOT NULL v2
- sys_casbin_policy_archive_v3_not_null｜NOT NULL v3
- sys_casbin_policy_archive_v4_not_null｜NOT NULL v4
- sys_casbin_policy_archive_v5_not_null｜NOT NULL v5

## sys_ip_rule（archetype A 業務全六欄）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_ip_rule_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| updated_at | timestamp with time zone | 是 | — |
| updated_by | bigint | 是 | — |
| deleted_at | timestamp with time zone | 是 | — |
| deleted_by | bigint | 是 | — |
| order | integer | 是 | — |
| wbip_type | character varying | 否 | — |
| wbip_cidr | inet | 否 | — |
| wbip_memo | text | 是 | — |

索引：
- sys_ip_rule_cidr_type_active_uniq｜CREATE UNIQUE INDEX sys_ip_rule_cidr_type_active_uniq ON public.sys_ip_rule USING btree (wbip_cidr, wbip_type) WHERE (deleted_at IS NULL)
- sys_ip_rule_pkey｜CREATE UNIQUE INDEX sys_ip_rule_pkey ON public.sys_ip_rule USING btree (id)

約束：
- sys_ip_rule_created_at_not_null｜NOT NULL created_at
- sys_ip_rule_id_not_null｜NOT NULL id
- sys_ip_rule_pkey｜PRIMARY KEY (id)
- sys_ip_rule_wbip_cidr_not_null｜NOT NULL wbip_cidr
- sys_ip_rule_wbip_type_not_null｜NOT NULL wbip_type

## sys_login_attempt（archetype B append-only 日誌）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_login_attempt_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| success | boolean | 否 | — |
| attempted_user_name | text | 否 | — |
| real_ip | inet | 否 | — |
| peer_ip | inet | 是 | — |
| x_forwarded_for | text | 是 | — |
| ip_confidence | text | 是 | — |
| region | text | 是 | — |
| trace_id | text | 是 | — |

索引：
- idx_login_attempt_created_at｜CREATE INDEX idx_login_attempt_created_at ON public.sys_login_attempt USING btree (created_at)
- idx_login_attempt_ip_time｜CREATE INDEX idx_login_attempt_ip_time ON public.sys_login_attempt USING btree (real_ip, created_at)
- idx_login_attempt_user_time｜CREATE INDEX idx_login_attempt_user_time ON public.sys_login_attempt USING btree (attempted_user_name, created_at)
- sys_login_attempt_pkey｜CREATE UNIQUE INDEX sys_login_attempt_pkey ON public.sys_login_attempt USING btree (id)

約束：
- sys_login_attempt_attempted_user_name_not_null｜NOT NULL attempted_user_name
- sys_login_attempt_created_at_not_null｜NOT NULL created_at
- sys_login_attempt_id_not_null｜NOT NULL id
- sys_login_attempt_pkey｜PRIMARY KEY (id)
- sys_login_attempt_real_ip_not_null｜NOT NULL real_ip
- sys_login_attempt_success_not_null｜NOT NULL success

## sys_menu（archetype A 業務全六欄）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_menu_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| updated_at | timestamp with time zone | 是 | — |
| updated_by | bigint | 是 | — |
| deleted_at | timestamp with time zone | 是 | — |
| deleted_by | bigint | 是 | — |
| status | smallint | 是 | — |
| order | integer | 是 | — |
| hide_in_menu | boolean | 是 | — |
| keep_alive | boolean | 是 | — |
| constant | boolean | 是 | — |
| multi_tab | boolean | 是 | — |
| protected | boolean | 否 | false |
| parent_id | bigint | 是 | — |
| menu_type | smallint | 是 | — |
| menu_name | character varying | 否 | — |
| menu_memo | text | 是 | — |
| route_name | character varying | 否 | — |
| route_path | character varying | 是 | — |
| component | character varying | 是 | — |
| icon | character varying | 是 | — |
| icon_type | smallint | 是 | — |
| i18n_key | character varying | 是 | — |
| href | character varying | 是 | — |
| active_menu | character varying | 是 | — |
| fixed_index_in_tab | integer | 是 | — |
| query | jsonb | 是 | — |
| buttons | jsonb | 是 | — |

索引：
- sys_menu_pkey｜CREATE UNIQUE INDEX sys_menu_pkey ON public.sys_menu USING btree (id)
- sys_menu_route_name_active_uniq｜CREATE UNIQUE INDEX sys_menu_route_name_active_uniq ON public.sys_menu USING btree (route_name) WHERE (deleted_at IS NULL)

約束：
- sys_menu_created_at_not_null｜NOT NULL created_at
- sys_menu_id_not_null｜NOT NULL id
- sys_menu_menu_name_not_null｜NOT NULL menu_name
- sys_menu_pkey｜PRIMARY KEY (id)
- sys_menu_protected_not_null｜NOT NULL protected
- sys_menu_route_name_not_null｜NOT NULL route_name

## sys_operation_log（archetype B append-only 日誌）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_operation_log_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| operation | character varying(20) | 否 | — |
| entity_table | character varying(64) | 否 | — |
| entity_id | bigint | 是 | — |
| payload_before | jsonb | 是 | — |
| payload_after | jsonb | 是 | — |
| operator_real_ip | inet | 是 | — |
| operator_peer_ip | inet | 是 | — |
| operator_x_forwarded_for | text | 是 | — |
| operator_ip_confidence | text | 是 | — |
| trace_id | character varying(64) | 是 | — |

索引：
- idx_operation_log_created_at｜CREATE INDEX idx_operation_log_created_at ON public.sys_operation_log USING btree (created_at)
- idx_operation_log_operator_time｜CREATE INDEX idx_operation_log_operator_time ON public.sys_operation_log USING btree (created_by, created_at)
- sys_operation_log_pkey｜CREATE UNIQUE INDEX sys_operation_log_pkey ON public.sys_operation_log USING btree (id)

約束：
- sys_operation_log_created_at_not_null｜NOT NULL created_at
- sys_operation_log_entity_table_not_null｜NOT NULL entity_table
- sys_operation_log_id_not_null｜NOT NULL id
- sys_operation_log_operation_not_null｜NOT NULL operation
- sys_operation_log_pkey｜PRIMARY KEY (id)

## sys_role（archetype A 業務全六欄）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_role_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| updated_at | timestamp with time zone | 是 | — |
| updated_by | bigint | 是 | — |
| deleted_at | timestamp with time zone | 是 | — |
| deleted_by | bigint | 是 | — |
| status | smallint | 是 | — |
| role_code | character varying | 否 | — |
| role_name | character varying | 否 | — |
| role_memo | text | 是 | — |
| role_home | character varying | 是 | — |
| role_desc | character varying | 是 | — |

索引：
- sys_role_code_active_uniq｜CREATE UNIQUE INDEX sys_role_code_active_uniq ON public.sys_role USING btree (role_code) WHERE (deleted_at IS NULL)
- sys_role_pkey｜CREATE UNIQUE INDEX sys_role_pkey ON public.sys_role USING btree (id)

約束：
- sys_role_created_at_not_null｜NOT NULL created_at
- sys_role_id_not_null｜NOT NULL id
- sys_role_pkey｜PRIMARY KEY (id)
- sys_role_role_code_not_null｜NOT NULL role_code
- sys_role_role_name_not_null｜NOT NULL role_name

## sys_token（archetype C 狀態機）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_token_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 否 | — |
| status | character varying(20) | 否 | — |
| token_hash | character varying(64) | 否 | — |
| rotation_chain | character varying(36) | 否 | — |
| issued_at | timestamp with time zone | 否 | — |
| expires_at | timestamp with time zone | 否 | — |
| used_at | timestamp with time zone | 是 | — |

索引：
- idx_sys_token_chain｜CREATE INDEX idx_sys_token_chain ON public.sys_token USING btree (rotation_chain)
- idx_sys_token_expires_at｜CREATE INDEX idx_sys_token_expires_at ON public.sys_token USING btree (expires_at)
- idx_sys_token_user_active｜CREATE INDEX idx_sys_token_user_active ON public.sys_token USING btree (created_by) WHERE ((status)::text = 'active'::text)
- sys_token_pkey｜CREATE UNIQUE INDEX sys_token_pkey ON public.sys_token USING btree (id)
- sys_token_token_hash_key｜CREATE UNIQUE INDEX sys_token_token_hash_key ON public.sys_token USING btree (token_hash)

約束：
- sys_token_created_at_not_null｜NOT NULL created_at
- sys_token_created_by_not_null｜NOT NULL created_by
- sys_token_expires_at_not_null｜NOT NULL expires_at
- sys_token_id_not_null｜NOT NULL id
- sys_token_issued_at_not_null｜NOT NULL issued_at
- sys_token_pkey｜PRIMARY KEY (id)
- sys_token_rotation_chain_not_null｜NOT NULL rotation_chain
- sys_token_status_not_null｜NOT NULL status
- sys_token_token_hash_key｜UNIQUE (token_hash)
- sys_token_token_hash_not_null｜NOT NULL token_hash

## sys_user（archetype A 業務全六欄）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| id | bigint | 否 | nextval('sys_user_id_seq'::regclass) |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| updated_at | timestamp with time zone | 是 | — |
| updated_by | bigint | 是 | — |
| deleted_at | timestamp with time zone | 是 | — |
| deleted_by | bigint | 是 | — |
| status | smallint | 是 | — |
| user_gender | smallint | 是 | — |
| user_name | character varying | 否 | — |
| password | character varying | 否 | — |
| nick_name | character varying | 是 | — |
| session_policy | character varying(20) | 否 | 'inherit'::character varying |
| session_id | character varying(36) | 是 | — |
| user_phone | character varying | 是 | — |
| user_email | character varying | 是 | — |
| user_memo | text | 是 | — |

索引：
- sys_user_pkey｜CREATE UNIQUE INDEX sys_user_pkey ON public.sys_user USING btree (id)
- sys_user_user_name_active_uniq｜CREATE UNIQUE INDEX sys_user_user_name_active_uniq ON public.sys_user USING btree (user_name) WHERE (deleted_at IS NULL)

約束：
- sys_user_created_at_not_null｜NOT NULL created_at
- sys_user_id_not_null｜NOT NULL id
- sys_user_password_not_null｜NOT NULL password
- sys_user_pkey｜PRIMARY KEY (id)
- sys_user_session_policy_not_null｜NOT NULL session_policy
- sys_user_user_name_not_null｜NOT NULL user_name

## sys_user_role（archetype C join）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| user_id | bigint | 否 | — |
| role_id | bigint | 否 | — |

索引：
- sys_user_role_pkey｜CREATE UNIQUE INDEX sys_user_role_pkey ON public.sys_user_role USING btree (user_id, role_id)

約束：
- fk_sys_user_role_role｜FOREIGN KEY (role_id) REFERENCES sys_role(id) ON DELETE RESTRICT
- fk_sys_user_role_user｜FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE RESTRICT
- sys_user_role_pkey｜PRIMARY KEY (user_id, role_id)
- sys_user_role_role_id_not_null｜NOT NULL role_id
- sys_user_role_user_id_not_null｜NOT NULL user_id

## system_settings（archetype A 業務全六欄）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| setting_key | character varying(64) | 否 | — |
| created_at | timestamp with time zone | 否 | CURRENT_TIMESTAMP |
| created_by | bigint | 是 | — |
| updated_at | timestamp with time zone | 是 | — |
| updated_by | bigint | 是 | — |
| deleted_at | timestamp with time zone | 是 | — |
| deleted_by | bigint | 是 | — |
| setting_type | character varying | 否 | — |
| setting_value | character varying | 否 | — |
| description | character varying | 是 | — |

索引：
- system_settings_pkey｜CREATE UNIQUE INDEX system_settings_pkey ON public.system_settings USING btree (setting_key)

約束：
- system_settings_created_at_not_null｜NOT NULL created_at
- system_settings_pkey｜PRIMARY KEY (setting_key)
- system_settings_setting_key_not_null｜NOT NULL setting_key
- system_settings_setting_type_not_null｜NOT NULL setting_type
- system_settings_setting_value_not_null｜NOT NULL setting_value
