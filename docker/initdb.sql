-- JB Agent clean database initialization
-- Generated from current project migrations
-- Target database: initdb

DROP DATABASE IF EXISTS initdb;
CREATE DATABASE initdb;
\connect initdb
CREATE EXTENSION IF NOT EXISTS vector;

--
-- PostgreSQL database dump
--

\restrict hgfa6Scol4LPZvhulSYGENjQa9lmTB6Gpm8YknXbdnb3LWUFj8s2N6AXXEzoWRU

-- Dumped from database version 18.1 (Debian 18.1-1.pgdg13+2)
-- Dumped by pg_dump version 18.1 (Debian 18.1-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.workspace_user_resource_permission DROP CONSTRAINT IF EXISTS workspace_user_resource_permission_user_id_623d7674_fk_user_id;
ALTER TABLE IF EXISTS ONLY public.workspace DROP CONSTRAINT IF EXISTS workspace_create_user_id_3ef6501e_fk_user_id;
ALTER TABLE IF EXISTS ONLY public.user_role_relation DROP CONSTRAINT IF EXISTS user_role_relation_workspace_id_d2bebed7_fk_workspace_id;
ALTER TABLE IF EXISTS ONLY public.user_role_relation DROP CONSTRAINT IF EXISTS user_role_relation_user_id_0df4472b_fk_user_id;
ALTER TABLE IF EXISTS ONLY public.user_role_relation DROP CONSTRAINT IF EXISTS user_role_relation_role_id_e55c1c54_fk_role_setting_id;
ALTER TABLE IF EXISTS ONLY public.user_group_relation DROP CONSTRAINT IF EXISTS user_group_relation_user_id_0a38580e_fk_chat_user_id;
ALTER TABLE IF EXISTS ONLY public.user_group_relation DROP CONSTRAINT IF EXISTS user_group_relation_group_id_8ee53fb6_fk_user_group_id;
ALTER TABLE IF EXISTS ONLY public.tool_record DROP CONSTRAINT IF EXISTS tool_record_tool_id_32995d93_fk_tool_id;
ALTER TABLE IF EXISTS ONLY public.tool_folder DROP CONSTRAINT IF EXISTS tool_folder_parent_id_cbcf6a00_fk_tool_folder_id;
ALTER TABLE IF EXISTS ONLY public.tool DROP CONSTRAINT IF EXISTS tool_folder_id_ecc041f8_fk_tool_folder_id;
ALTER TABLE IF EXISTS ONLY public.system_api_key DROP CONSTRAINT IF EXISTS system_api_key_user_id_cd4d9463_fk_user_id;
ALTER TABLE IF EXISTS ONLY public.role_setting DROP CONSTRAINT IF EXISTS role_setting_create_user_id_6b445527_fk_user_id;
ALTER TABLE IF EXISTS ONLY public.role_permission DROP CONSTRAINT IF EXISTS role_permission_role_id_877a80a4_fk_role_setting_id;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_group_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_g_user_group_id_3798efb8_fk_user_grou;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_authorize_user_id_326419b7_fk_chat_user_id;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_a_user_group_id_5f3021d3_fk_user_grou;
ALTER TABLE IF EXISTS ONLY public.paragraph DROP CONSTRAINT IF EXISTS paragraph_knowledge_id_4adce37e_fk_knowledge_id;
ALTER TABLE IF EXISTS ONLY public.knowledge_folder DROP CONSTRAINT IF EXISTS knowledge_folder_parent_id_88bfda49_fk_knowledge_folder_id;
ALTER TABLE IF EXISTS ONLY public.knowledge DROP CONSTRAINT IF EXISTS knowledge_folder_id_c2644e2c_fk_knowledge_folder_id;
ALTER TABLE IF EXISTS ONLY public.event_trigger_task DROP CONSTRAINT IF EXISTS event_trigger_task_trigger_id_fe513725_fk_event_trigger_id;
ALTER TABLE IF EXISTS ONLY public.event_trigger_task_record DROP CONSTRAINT IF EXISTS event_trigger_task_r_trigger_id_e2820298_fk_event_tri;
ALTER TABLE IF EXISTS ONLY public.document DROP CONSTRAINT IF EXISTS document_knowledge_id_419c566f_fk_knowledge_id;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictask DROP CONSTRAINT IF EXISTS django_celery_beat_p_solar_id_a87ce72c_fk_django_ce;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictask DROP CONSTRAINT IF EXISTS django_celery_beat_p_interval_id_a8ca27da_fk_django_ce;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictask DROP CONSTRAINT IF EXISTS django_celery_beat_p_crontab_id_d3cba168_fk_django_ce;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictask DROP CONSTRAINT IF EXISTS django_celery_beat_p_clocked_id_47a69f82_fk_django_ce;
ALTER TABLE IF EXISTS ONLY public.django_apscheduler_djangojobexecution DROP CONSTRAINT IF EXISTS django_apscheduler_djangojobexecution_job_id_daf5090a_fk;
ALTER TABLE IF EXISTS ONLY public.application_version DROP CONSTRAINT IF EXISTS application_version_application_id_ee35744a_fk_application_id;
ALTER TABLE IF EXISTS ONLY public.application_setting DROP CONSTRAINT IF EXISTS application_setting_application_id_50f30183_fk_application_id;
ALTER TABLE IF EXISTS ONLY public.application_knowledge_mapping DROP CONSTRAINT IF EXISTS application_knowledg_knowledge_id_767ec6f1_fk_knowledge;
ALTER TABLE IF EXISTS ONLY public.application_knowledge_mapping DROP CONSTRAINT IF EXISTS application_knowledg_application_id_784ccbaf_fk_applicati;
ALTER TABLE IF EXISTS ONLY public.application_folder DROP CONSTRAINT IF EXISTS application_folder_parent_id_b82d1c52_fk_application_folder_id;
ALTER TABLE IF EXISTS ONLY public.application DROP CONSTRAINT IF EXISTS application_folder_id_0d598f52_fk_application_folder_id;
ALTER TABLE IF EXISTS ONLY public.application_chat_user_stats DROP CONSTRAINT IF EXISTS application_chat_use_application_id_2080bbf7_fk_applicati;
ALTER TABLE IF EXISTS ONLY public.application_chat_share_link DROP CONSTRAINT IF EXISTS application_chat_sha_chat_id_8d8b6456_fk_applicati;
ALTER TABLE IF EXISTS ONLY public.application_chat_share_link DROP CONSTRAINT IF EXISTS application_chat_sha_application_id_49c6403d_fk_applicati;
ALTER TABLE IF EXISTS ONLY public.application_chat_record DROP CONSTRAINT IF EXISTS application_chat_record_chat_id_21aeb7ef_fk_application_chat_id;
ALTER TABLE IF EXISTS ONLY public.application_chat DROP CONSTRAINT IF EXISTS application_chat_application_id_0c9f6b90_fk_application_id;
ALTER TABLE IF EXISTS ONLY public.application_api_key DROP CONSTRAINT IF EXISTS application_api_key_application_id_376d9a01_fk_application_id;
ALTER TABLE IF EXISTS ONLY public.application_access_token DROP CONSTRAINT IF EXISTS application_access_t_application_id_d90b8cec_fk_applicati;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_workspace_id_6d34f020_like;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_workspace_id_6d34f020;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_user_id_623d7674;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_update_time_f944478e;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_target_d0c6532f;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_create_time_d3397f88;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_auth_type_43a49931_like;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_auth_type_43a49931;
DROP INDEX IF EXISTS public.workspace_user_resource_permission_auth_target_type_33deef7a;
DROP INDEX IF EXISTS public.workspace_user_resource__auth_target_type_33deef7a_like;
DROP INDEX IF EXISTS public.workspace_name_cff03e24_like;
DROP INDEX IF EXISTS public.workspace_id_76599053_like;
DROP INDEX IF EXISTS public.workspace_create_user_id_3ef6501e;
DROP INDEX IF EXISTS public.workspace_create_time_1d030cbe;
DROP INDEX IF EXISTS public.user_username_cf016618_like;
DROP INDEX IF EXISTS public.user_update_time_ccf08206;
DROP INDEX IF EXISTS public.user_source_51744f77_like;
DROP INDEX IF EXISTS public.user_source_51744f77;
DROP INDEX IF EXISTS public.user_role_relation_workspace_id_d2bebed7_like;
DROP INDEX IF EXISTS public.user_role_relation_workspace_id_d2bebed7;
DROP INDEX IF EXISTS public.user_role_relation_user_id_0df4472b;
DROP INDEX IF EXISTS public.user_role_relation_role_id_e55c1c54_like;
DROP INDEX IF EXISTS public.user_role_relation_role_id_e55c1c54;
DROP INDEX IF EXISTS public.user_phone_fcd7f7da_like;
DROP INDEX IF EXISTS public.user_phone_fcd7f7da;
DROP INDEX IF EXISTS public.user_nick_name_580ea5e6_like;
DROP INDEX IF EXISTS public.user_is_active_74579245;
DROP INDEX IF EXISTS public.user_group_relation_user_id_0a38580e;
DROP INDEX IF EXISTS public.user_group_relation_group_id_8ee53fb6_like;
DROP INDEX IF EXISTS public.user_group_relation_group_id_8ee53fb6;
DROP INDEX IF EXISTS public.user_group_name_d36097b4_like;
DROP INDEX IF EXISTS public.user_group_id_9e420a50_like;
DROP INDEX IF EXISTS public.user_email_54dc62b2_like;
DROP INDEX IF EXISTS public.user_create_time_d69e5f54;
DROP INDEX IF EXISTS public.tool_workspace_id_bf0fd790_like;
DROP INDEX IF EXISTS public.tool_workspace_id_bf0fd790;
DROP INDEX IF EXISTS public.tool_workflow_workspace_id_6700c059_like;
DROP INDEX IF EXISTS public.tool_workflow_workspace_id_6700c059;
DROP INDEX IF EXISTS public.tool_workflow_version_workspace_id_e99217f6_like;
DROP INDEX IF EXISTS public.tool_workflow_version_workspace_id_e99217f6;
DROP INDEX IF EXISTS public.tool_workflow_version_update_time_6daf9080;
DROP INDEX IF EXISTS public.tool_workflow_version_tool_id_b4671e40;
DROP INDEX IF EXISTS public.tool_workflow_version_create_time_8a513673;
DROP INDEX IF EXISTS public.tool_workflow_update_time_afd5559b;
DROP INDEX IF EXISTS public.tool_workflow_is_publish_d8c55450;
DROP INDEX IF EXISTS public.tool_workflow_create_time_cb25a2c6;
DROP INDEX IF EXISTS public.tool_user_id_fd36dfa4;
DROP INDEX IF EXISTS public.tool_update_time_2e4efd57;
DROP INDEX IF EXISTS public.tool_tool_type_204cdc98_like;
DROP INDEX IF EXISTS public.tool_tool_type_204cdc98;
DROP INDEX IF EXISTS public.tool_template_id_717d147f;
DROP INDEX IF EXISTS public.tool_scope_6387be58_like;
DROP INDEX IF EXISTS public.tool_scope_6387be58;
DROP INDEX IF EXISTS public.tool_record_workspace_id_88320155_like;
DROP INDEX IF EXISTS public.tool_record_workspace_id_88320155;
DROP INDEX IF EXISTS public.tool_record_update_time_3ef56090;
DROP INDEX IF EXISTS public.tool_record_tool_id_32995d93;
DROP INDEX IF EXISTS public.tool_record_create_time_0e96de5e;
DROP INDEX IF EXISTS public.tool_name_ec029465_like;
DROP INDEX IF EXISTS public.tool_name_ec029465;
DROP INDEX IF EXISTS public.tool_label_66e517a8_like;
DROP INDEX IF EXISTS public.tool_label_66e517a8;
DROP INDEX IF EXISTS public.tool_is_active_f3d326d1;
DROP INDEX IF EXISTS public.tool_folder_workspace_id_20b66b15_like;
DROP INDEX IF EXISTS public.tool_folder_workspace_id_20b66b15;
DROP INDEX IF EXISTS public.tool_folder_user_id_be38331b;
DROP INDEX IF EXISTS public.tool_folder_update_time_ba9be14e;
DROP INDEX IF EXISTS public.tool_folder_tree_id_60fc41dd;
DROP INDEX IF EXISTS public.tool_folder_parent_id_cbcf6a00_like;
DROP INDEX IF EXISTS public.tool_folder_parent_id_cbcf6a00;
DROP INDEX IF EXISTS public.tool_folder_name_d6438754_like;
DROP INDEX IF EXISTS public.tool_folder_name_d6438754;
DROP INDEX IF EXISTS public.tool_folder_id_ecc041f8_like;
DROP INDEX IF EXISTS public.tool_folder_id_ecc041f8;
DROP INDEX IF EXISTS public.tool_folder_id_940ad233_like;
DROP INDEX IF EXISTS public.tool_folder_create_time_2a019328;
DROP INDEX IF EXISTS public.tool_create_time_e0880b81;
DROP INDEX IF EXISTS public.termbase_update_time_68470b36;
DROP INDEX IF EXISTS public.termbase_knowledge_id_fe5e8d87;
DROP INDEX IF EXISTS public.termbase_create_time_c46bd6cc;
DROP INDEX IF EXISTS public.termbase_content_5cb3da68_like;
DROP INDEX IF EXISTS public.termbase_content_5cb3da68;
DROP INDEX IF EXISTS public.tag_value_0d236690_like;
DROP INDEX IF EXISTS public.tag_value_0d236690;
DROP INDEX IF EXISTS public.tag_update_time_928c2700;
DROP INDEX IF EXISTS public.tag_knowledge_id_5816b5de;
DROP INDEX IF EXISTS public.tag_knowled_cba590_idx;
DROP INDEX IF EXISTS public.tag_key_08a35336_like;
DROP INDEX IF EXISTS public.tag_key_08a35336;
DROP INDEX IF EXISTS public.tag_create_time_36d78b7c;
DROP INDEX IF EXISTS public.system_setting_update_time_a3d325d1;
DROP INDEX IF EXISTS public.system_setting_create_time_7c21ded3;
DROP INDEX IF EXISTS public.system_api_key_user_id_cd4d9463;
DROP INDEX IF EXISTS public.system_api_key_secret_key_cc2faff6_like;
DROP INDEX IF EXISTS public.system_api_key_is_active_69a5ddbb;
DROP INDEX IF EXISTS public.system_api_key_create_time_7ca80d97;
DROP INDEX IF EXISTS public.shared_resource_workspace_authorization_resource_type_7c2189b7;
DROP INDEX IF EXISTS public.shared_resource_workspace_authorization_id_782f59e4_like;
DROP INDEX IF EXISTS public.shared_resource_workspace_authorization_create_time_1911b445;
DROP INDEX IF EXISTS public.shared_resource_workspac_resource_type_7c2189b7_like;
DROP INDEX IF EXISTS public.role_setting_type_96416659_like;
DROP INDEX IF EXISTS public.role_setting_type_96416659;
DROP INDEX IF EXISTS public.role_setting_role_name_d08bc838_like;
DROP INDEX IF EXISTS public.role_setting_role_name_d08bc838;
DROP INDEX IF EXISTS public.role_setting_internal_efb75f8b;
DROP INDEX IF EXISTS public.role_setting_id_77e4dc9c_like;
DROP INDEX IF EXISTS public.role_setting_create_user_id_6b445527;
DROP INDEX IF EXISTS public.role_setting_create_time_c94535ed;
DROP INDEX IF EXISTS public.role_permission_role_id_877a80a4_like;
DROP INDEX IF EXISTS public.role_permission_role_id_877a80a4;
DROP INDEX IF EXISTS public.role_permission_permission_id_ee9c5982_like;
DROP INDEX IF EXISTS public.role_permission_permission_id_ee9c5982;
DROP INDEX IF EXISTS public.resource_mapping_update_time_1c3672d3;
DROP INDEX IF EXISTS public.resource_mapping_target_type_85c62bbb_like;
DROP INDEX IF EXISTS public.resource_mapping_target_type_85c62bbb;
DROP INDEX IF EXISTS public.resource_mapping_target_id_6e1f2685_like;
DROP INDEX IF EXISTS public.resource_mapping_target_id_6e1f2685;
DROP INDEX IF EXISTS public.resource_mapping_source_type_65569047_like;
DROP INDEX IF EXISTS public.resource_mapping_source_type_65569047;
DROP INDEX IF EXISTS public.resource_mapping_source_id_4ea1216b_like;
DROP INDEX IF EXISTS public.resource_mapping_source_id_4ea1216b;
DROP INDEX IF EXISTS public.resource_mapping_create_time_bda4e392;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_workspace_id_b75c61b5_like;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_workspace_id_b75c61b5;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_user_group_id_3798efb8_like;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_user_group_id_3798efb8;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_resource_type_91c5cda5_like;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_resource_type_91c5cda5;
DROP INDEX IF EXISTS public.resource_chat_user_group_authorize_resource_id_25ffb4f9;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_workspace_id_515407f9_like;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_workspace_id_515407f9;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_user_id_326419b7;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_user_group_id_5f3021d3_like;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_user_group_id_5f3021d3;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_resource_type_dfd85ed2_like;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_resource_type_dfd85ed2;
DROP INDEX IF EXISTS public.resource_chat_user_authorize_resource_id_efef323e;
DROP INDEX IF EXISTS public.public_file_source__a961f4_idx;
DROP INDEX IF EXISTS public.public_file_access_update_time_a5dd6071;
DROP INDEX IF EXISTS public.public_file_access_source_type_a345336c_like;
DROP INDEX IF EXISTS public.public_file_access_source_type_a345336c;
DROP INDEX IF EXISTS public.public_file_access_source_id_6d3fa282_like;
DROP INDEX IF EXISTS public.public_file_access_source_id_6d3fa282;
DROP INDEX IF EXISTS public.public_file_access_create_time_c322ec98;
DROP INDEX IF EXISTS public.problem_update_time_16392c6e;
DROP INDEX IF EXISTS public.problem_paragraph_mapping_update_time_677e4106;
DROP INDEX IF EXISTS public.problem_paragraph_mapping_problem_id_937b9858;
DROP INDEX IF EXISTS public.problem_paragraph_mapping_paragraph_id_f0be2e98;
DROP INDEX IF EXISTS public.problem_paragraph_mapping_knowledge_id_84e4e42a;
DROP INDEX IF EXISTS public.problem_paragraph_mapping_document_id_74b9f617;
DROP INDEX IF EXISTS public.problem_paragraph_mapping_create_time_30dae711;
DROP INDEX IF EXISTS public.problem_knowledge_id_656d8e09;
DROP INDEX IF EXISTS public.problem_create_time_3a2d1421;
DROP INDEX IF EXISTS public.problem_content_93727706_like;
DROP INDEX IF EXISTS public.problem_content_93727706;
DROP INDEX IF EXISTS public.platform_display_setting_id_15c39485_like;
DROP INDEX IF EXISTS public.platform_display_setting_create_time_73008bbc;
DROP INDEX IF EXISTS public.paragraph_update_time_0e8da622;
DROP INDEX IF EXISTS public.paragraph_title_57663bca_like;
DROP INDEX IF EXISTS public.paragraph_title_57663bca;
DROP INDEX IF EXISTS public.paragraph_status_ebef6bfe_like;
DROP INDEX IF EXISTS public.paragraph_status_ebef6bfe;
DROP INDEX IF EXISTS public.paragraph_position_00aa9a2f;
DROP INDEX IF EXISTS public.paragraph_knowledge_id_4adce37e;
DROP INDEX IF EXISTS public.paragraph_is_active_d6ea683a;
DROP INDEX IF EXISTS public.paragraph_document_id_2e0722cc;
DROP INDEX IF EXISTS public.paragraph_create_time_521ed7f0;
DROP INDEX IF EXISTS public.model_workspace_id_1edf80e5_like;
DROP INDEX IF EXISTS public.model_workspace_id_1edf80e5;
DROP INDEX IF EXISTS public.model_user_id_a841bfc8;
DROP INDEX IF EXISTS public.model_update_time_11b3490c;
DROP INDEX IF EXISTS public.model_status_e8e46844_like;
DROP INDEX IF EXISTS public.model_status_e8e46844;
DROP INDEX IF EXISTS public.model_provider_cdbe3bf6_like;
DROP INDEX IF EXISTS public.model_provider_cdbe3bf6;
DROP INDEX IF EXISTS public.model_name_1f9cfbc9_like;
DROP INDEX IF EXISTS public.model_name_1f9cfbc9;
DROP INDEX IF EXISTS public.model_model_type_b693061b_like;
DROP INDEX IF EXISTS public.model_model_type_b693061b;
DROP INDEX IF EXISTS public.model_model_name_c1d139d8_like;
DROP INDEX IF EXISTS public.model_model_name_c1d139d8;
DROP INDEX IF EXISTS public.model_create_time_c34d0337;
DROP INDEX IF EXISTS public.log_workspace_id_3f8e9902_like;
DROP INDEX IF EXISTS public.log_workspace_id_3f8e9902;
DROP INDEX IF EXISTS public.log_update_time_a65e7f1e;
DROP INDEX IF EXISTS public.log_status_77474674;
DROP INDEX IF EXISTS public.log_operate_bb4f8ada_like;
DROP INDEX IF EXISTS public.log_operate_bb4f8ada;
DROP INDEX IF EXISTS public.log_create_time_44520a52;
DROP INDEX IF EXISTS public.knowledge_workspace_id_795138c3_like;
DROP INDEX IF EXISTS public.knowledge_workspace_id_795138c3;
DROP INDEX IF EXISTS public.knowledge_workflow_workspace_id_79c20e29_like;
DROP INDEX IF EXISTS public.knowledge_workflow_workspace_id_79c20e29;
DROP INDEX IF EXISTS public.knowledge_workflow_version_workspace_id_d4df3903_like;
DROP INDEX IF EXISTS public.knowledge_workflow_version_workspace_id_d4df3903;
DROP INDEX IF EXISTS public.knowledge_workflow_version_update_time_3f96de1d;
DROP INDEX IF EXISTS public.knowledge_workflow_version_knowledge_id_34bf3175;
DROP INDEX IF EXISTS public.knowledge_workflow_version_create_time_10b25ccb;
DROP INDEX IF EXISTS public.knowledge_workflow_update_time_1036d552;
DROP INDEX IF EXISTS public.knowledge_workflow_is_publish_74629d52;
DROP INDEX IF EXISTS public.knowledge_workflow_create_time_3d79e7e6;
DROP INDEX IF EXISTS public.knowledge_user_id_18293b47;
DROP INDEX IF EXISTS public.knowledge_update_time_588f12b8;
DROP INDEX IF EXISTS public.knowledge_type_7a89fb9d;
DROP INDEX IF EXISTS public.knowledge_scope_c8877d39_like;
DROP INDEX IF EXISTS public.knowledge_scope_c8877d39;
DROP INDEX IF EXISTS public.knowledge_name_41f67f24_like;
DROP INDEX IF EXISTS public.knowledge_name_41f67f24;
DROP INDEX IF EXISTS public.knowledge_folder_workspace_id_23488b49_like;
DROP INDEX IF EXISTS public.knowledge_folder_workspace_id_23488b49;
DROP INDEX IF EXISTS public.knowledge_folder_user_id_48c7f505;
DROP INDEX IF EXISTS public.knowledge_folder_update_time_14aa2e30;
DROP INDEX IF EXISTS public.knowledge_folder_tree_id_a575de4c;
DROP INDEX IF EXISTS public.knowledge_folder_parent_id_88bfda49_like;
DROP INDEX IF EXISTS public.knowledge_folder_parent_id_88bfda49;
DROP INDEX IF EXISTS public.knowledge_folder_name_ab2c51ae_like;
DROP INDEX IF EXISTS public.knowledge_folder_name_ab2c51ae;
DROP INDEX IF EXISTS public.knowledge_folder_id_d2636e62_like;
DROP INDEX IF EXISTS public.knowledge_folder_id_c2644e2c_like;
DROP INDEX IF EXISTS public.knowledge_folder_id_c2644e2c;
DROP INDEX IF EXISTS public.knowledge_folder_create_time_9f79917a;
DROP INDEX IF EXISTS public.knowledge_embedding_model_id_d8ebfba0;
DROP INDEX IF EXISTS public.knowledge_create_time_73058bbd;
DROP INDEX IF EXISTS public.knowledge_action_update_time_b7da00ac;
DROP INDEX IF EXISTS public.knowledge_action_knowledge_id_8c71df84;
DROP INDEX IF EXISTS public.knowledge_action_create_time_e8782fff;
DROP INDEX IF EXISTS public.file_update_time_e55a692a;
DROP INDEX IF EXISTS public.file_source_type_aae7b5e3_like;
DROP INDEX IF EXISTS public.file_source_type_aae7b5e3;
DROP INDEX IF EXISTS public.file_source_id_f68d803c_like;
DROP INDEX IF EXISTS public.file_source_id_f68d803c;
DROP INDEX IF EXISTS public.file_create_time_940439ad;
DROP INDEX IF EXISTS public.event_trigger_workspace_id_a19f6584_like;
DROP INDEX IF EXISTS public.event_trigger_workspace_id_a19f6584;
DROP INDEX IF EXISTS public.event_trigger_user_id_fa647614;
DROP INDEX IF EXISTS public.event_trigger_update_time_8b613ce6;
DROP INDEX IF EXISTS public.event_trigger_task_update_time_f61d2e08;
DROP INDEX IF EXISTS public.event_trigger_task_trigger_id_fe513725;
DROP INDEX IF EXISTS public.event_trigger_task_record_update_time_0085d148;
DROP INDEX IF EXISTS public.event_trigger_task_record_trigger_id_e2820298;
DROP INDEX IF EXISTS public.event_trigger_task_record_create_time_da67dbbf;
DROP INDEX IF EXISTS public.event_trigger_task_is_active_fb6a8ed7;
DROP INDEX IF EXISTS public.event_trigger_task_create_time_ea019477;
DROP INDEX IF EXISTS public.event_trigger_name_463b9244_like;
DROP INDEX IF EXISTS public.event_trigger_name_463b9244;
DROP INDEX IF EXISTS public.event_trigger_is_active_59ad09bf;
DROP INDEX IF EXISTS public.event_trigger_create_time_72037f02;
DROP INDEX IF EXISTS public.embedding_source_type_23488528_like;
DROP INDEX IF EXISTS public.embedding_source_type_23488528;
DROP INDEX IF EXISTS public.embedding_source_id_60f7e2f4_like;
DROP INDEX IF EXISTS public.embedding_source_id_60f7e2f4;
DROP INDEX IF EXISTS public.embedding_search_vector_gin_idx;
DROP INDEX IF EXISTS public.embedding_paragraph_id_9f39681c;
DROP INDEX IF EXISTS public.embedding_knowledge_id_00e08fa7;
DROP INDEX IF EXISTS public.embedding_id_f61adc5f_like;
DROP INDEX IF EXISTS public.embedding_document_id_3c89d1f3;
DROP INDEX IF EXISTS public.document_user_id_9e7ccb71;
DROP INDEX IF EXISTS public.document_update_time_4e517386;
DROP INDEX IF EXISTS public.document_type_7fb9c2c3;
DROP INDEX IF EXISTS public.document_tag_update_time_2c460bdf;
DROP INDEX IF EXISTS public.document_tag_tag_id_acaa7b3b;
DROP INDEX IF EXISTS public.document_tag_document_id_953cb93d;
DROP INDEX IF EXISTS public.document_tag_create_time_4ef5590c;
DROP INDEX IF EXISTS public.document_status_a4cf573b_like;
DROP INDEX IF EXISTS public.document_status_a4cf573b;
DROP INDEX IF EXISTS public.document_name_8eb44882_like;
DROP INDEX IF EXISTS public.document_name_8eb44882;
DROP INDEX IF EXISTS public.document_knowledge_id_419c566f;
DROP INDEX IF EXISTS public.document_is_active_ab67f847;
DROP INDEX IF EXISTS public.document_create_time_5168c411;
DROP INDEX IF EXISTS public.django_celery_beat_periodictask_solar_id_a87ce72c;
DROP INDEX IF EXISTS public.django_celery_beat_periodictask_name_265a36b7_like;
DROP INDEX IF EXISTS public.django_celery_beat_periodictask_interval_id_a8ca27da;
DROP INDEX IF EXISTS public.django_celery_beat_periodictask_crontab_id_d3cba168;
DROP INDEX IF EXISTS public.django_celery_beat_periodictask_clocked_id_47a69f82;
DROP INDEX IF EXISTS public.django_apscheduler_djangojobexecution_run_time_16edd96b;
DROP INDEX IF EXISTS public.django_apscheduler_djangojobexecution_job_id_daf5090a;
DROP INDEX IF EXISTS public.django_apscheduler_djangojob_next_run_time_2f022619;
DROP INDEX IF EXISTS public.chat_user_username_7c2763ef_like;
DROP INDEX IF EXISTS public.chat_user_update_time_d6b6010c;
DROP INDEX IF EXISTS public.chat_user_source_4957074b_like;
DROP INDEX IF EXISTS public.chat_user_source_4957074b;
DROP INDEX IF EXISTS public.chat_user_nick_name_9f856cf5_like;
DROP INDEX IF EXISTS public.chat_user_is_active_c3391505;
DROP INDEX IF EXISTS public.chat_user_email_9db37d4b_like;
DROP INDEX IF EXISTS public.chat_user_email_9db37d4b;
DROP INDEX IF EXISTS public.chat_user_create_time_04d18e13;
DROP INDEX IF EXISTS public.chat_platform_is_valid_77760718;
DROP INDEX IF EXISTS public.chat_platform_is_active_e29f11f7;
DROP INDEX IF EXISTS public.chat_platform_id_942bd9e5_like;
DROP INDEX IF EXISTS public.chat_platform_auth_type_9ac6f177_like;
DROP INDEX IF EXISTS public.chat_auth_setting_create_time_5267d1bd;
DROP INDEX IF EXISTS public.chat_auth_setting_auth_type_13ab0604_like;
DROP INDEX IF EXISTS public.application_workspace_id_43da6674_like;
DROP INDEX IF EXISTS public.application_workspace_id_43da6674;
DROP INDEX IF EXISTS public.application_version_workspace_id_cc3b81bf_like;
DROP INDEX IF EXISTS public.application_version_workspace_id_cc3b81bf;
DROP INDEX IF EXISTS public.application_version_user_id_61a6abb2;
DROP INDEX IF EXISTS public.application_version_update_time_c6e2da69;
DROP INDEX IF EXISTS public.application_version_create_time_d37c6d5c;
DROP INDEX IF EXISTS public.application_version_application_id_ee35744a;
DROP INDEX IF EXISTS public.application_user_id_e0323977;
DROP INDEX IF EXISTS public.application_update_time_1ef68ba2;
DROP INDEX IF EXISTS public.application_tts_model_id_63215f2e;
DROP INDEX IF EXISTS public.application_stt_model_id_10e736db;
DROP INDEX IF EXISTS public.application_setting_id_de129745_like;
DROP INDEX IF EXISTS public.application_name_b2d4898f_like;
DROP INDEX IF EXISTS public.application_name_b2d4898f;
DROP INDEX IF EXISTS public.application_model_id_e80b5b34;
DROP INDEX IF EXISTS public.application_long_term_model_id_d4500da7;
DROP INDEX IF EXISTS public.application_long_term_memory_update_time_11820ff2;
DROP INDEX IF EXISTS public.application_long_term_memory_create_time_09279212;
DROP INDEX IF EXISTS public.application_long_term_memory_chat_user_id_f0c804ca_like;
DROP INDEX IF EXISTS public.application_long_term_memory_chat_user_id_f0c804ca;
DROP INDEX IF EXISTS public.application_long_term_memory_application_id_cebbbeea;
DROP INDEX IF EXISTS public.application_knowledge_mapping_update_time_5d8dc346;
DROP INDEX IF EXISTS public.application_knowledge_mapping_knowledge_id_767ec6f1;
DROP INDEX IF EXISTS public.application_knowledge_mapping_create_time_b5b82de1;
DROP INDEX IF EXISTS public.application_knowledge_mapping_application_id_784ccbaf;
DROP INDEX IF EXISTS public.application_folder_workspace_id_753461f7_like;
DROP INDEX IF EXISTS public.application_folder_workspace_id_753461f7;
DROP INDEX IF EXISTS public.application_folder_user_id_45def139;
DROP INDEX IF EXISTS public.application_folder_update_time_078e64d2;
DROP INDEX IF EXISTS public.application_folder_tree_id_e467c15b;
DROP INDEX IF EXISTS public.application_folder_parent_id_b82d1c52_like;
DROP INDEX IF EXISTS public.application_folder_parent_id_b82d1c52;
DROP INDEX IF EXISTS public.application_folder_name_d221e0c2_like;
DROP INDEX IF EXISTS public.application_folder_name_d221e0c2;
DROP INDEX IF EXISTS public.application_folder_id_bdb97e27_like;
DROP INDEX IF EXISTS public.application_folder_id_0d598f52_like;
DROP INDEX IF EXISTS public.application_folder_id_0d598f52;
DROP INDEX IF EXISTS public.application_folder_create_time_69889312;
DROP INDEX IF EXISTS public.application_create_time_ee39f1ea;
DROP INDEX IF EXISTS public.application_chat_user_stats_update_time_0e9f4d3b;
DROP INDEX IF EXISTS public.application_chat_user_stats_create_time_32742378;
DROP INDEX IF EXISTS public.application_chat_user_stats_application_id_2080bbf7;
DROP INDEX IF EXISTS public.application_chat_update_time_f9735fce;
DROP INDEX IF EXISTS public.application_chat_share_link_user_id_5dc5097c;
DROP INDEX IF EXISTS public.application_chat_share_link_update_time_8b535cf5;
DROP INDEX IF EXISTS public.application_chat_share_link_create_time_84a2f494;
DROP INDEX IF EXISTS public.application_chat_share_link_chat_id_8d8b6456;
DROP INDEX IF EXISTS public.application_chat_share_link_application_id_49c6403d;
DROP INDEX IF EXISTS public.application_chat_record_update_time_32fb05dc;
DROP INDEX IF EXISTS public.application_chat_record_create_time_8878f099;
DROP INDEX IF EXISTS public.application_chat_record_chat_id_21aeb7ef;
DROP INDEX IF EXISTS public.application_chat_create_time_ebb5f9d3;
DROP INDEX IF EXISTS public.application_chat_application_id_0c9f6b90;
DROP INDEX IF EXISTS public.application_applica_7a56a7_idx;
DROP INDEX IF EXISTS public.application_applica_1652ba_idx;
DROP INDEX IF EXISTS public.application_api_key_workspace_id_01fbdbc0_like;
DROP INDEX IF EXISTS public.application_api_key_workspace_id_01fbdbc0;
DROP INDEX IF EXISTS public.application_api_key_update_time_ce7b0d9b;
DROP INDEX IF EXISTS public.application_api_key_secret_key_fd1b76e9_like;
DROP INDEX IF EXISTS public.application_api_key_create_time_0013df4c;
DROP INDEX IF EXISTS public.application_api_key_application_id_376d9a01;
DROP INDEX IF EXISTS public.application_access_token_update_time_8e6632af;
DROP INDEX IF EXISTS public.application_access_token_create_time_64979b17;
DROP INDEX IF EXISTS public.application_access_token_access_token_3823531a_like;
ALTER TABLE IF EXISTS ONLY public.workspace_user_resource_permission DROP CONSTRAINT IF EXISTS workspace_user_resource_permission_pkey;
ALTER TABLE IF EXISTS ONLY public.workspace_user_resource_permission DROP CONSTRAINT IF EXISTS workspace_user_resource__workspace_id_user_id_aut_692d4734_uniq;
ALTER TABLE IF EXISTS ONLY public.workspace DROP CONSTRAINT IF EXISTS workspace_pkey;
ALTER TABLE IF EXISTS ONLY public.workspace DROP CONSTRAINT IF EXISTS workspace_name_key;
ALTER TABLE IF EXISTS ONLY public."user" DROP CONSTRAINT IF EXISTS user_username_key;
ALTER TABLE IF EXISTS ONLY public.user_role_relation DROP CONSTRAINT IF EXISTS user_role_relation_workspace_id_role_id_user_id_458d2c05_uniq;
ALTER TABLE IF EXISTS ONLY public.user_role_relation DROP CONSTRAINT IF EXISTS user_role_relation_pkey;
ALTER TABLE IF EXISTS ONLY public."user" DROP CONSTRAINT IF EXISTS user_pkey;
ALTER TABLE IF EXISTS ONLY public."user" DROP CONSTRAINT IF EXISTS user_nick_name_key;
ALTER TABLE IF EXISTS ONLY public.user_group_relation DROP CONSTRAINT IF EXISTS user_group_relation_pkey;
ALTER TABLE IF EXISTS ONLY public.user_group DROP CONSTRAINT IF EXISTS user_group_pkey;
ALTER TABLE IF EXISTS ONLY public.user_group DROP CONSTRAINT IF EXISTS user_group_name_key;
ALTER TABLE IF EXISTS ONLY public."user" DROP CONSTRAINT IF EXISTS user_email_key;
ALTER TABLE IF EXISTS ONLY public.django_apscheduler_djangojobexecution DROP CONSTRAINT IF EXISTS unique_job_executions;
ALTER TABLE IF EXISTS ONLY public.tool_workflow_version DROP CONSTRAINT IF EXISTS tool_workflow_version_pkey;
ALTER TABLE IF EXISTS ONLY public.tool_workflow DROP CONSTRAINT IF EXISTS tool_workflow_tool_id_key;
ALTER TABLE IF EXISTS ONLY public.tool_workflow DROP CONSTRAINT IF EXISTS tool_workflow_pkey;
ALTER TABLE IF EXISTS ONLY public.tool_record DROP CONSTRAINT IF EXISTS tool_record_pkey;
ALTER TABLE IF EXISTS ONLY public.tool DROP CONSTRAINT IF EXISTS tool_pkey;
ALTER TABLE IF EXISTS ONLY public.tool_folder DROP CONSTRAINT IF EXISTS tool_folder_pkey;
ALTER TABLE IF EXISTS ONLY public.termbase DROP CONSTRAINT IF EXISTS termbase_pkey;
ALTER TABLE IF EXISTS ONLY public.tag DROP CONSTRAINT IF EXISTS tag_pkey;
ALTER TABLE IF EXISTS ONLY public.tag DROP CONSTRAINT IF EXISTS tag_knowledge_id_key_value_eb5f0e5d_uniq;
ALTER TABLE IF EXISTS ONLY public.system_setting DROP CONSTRAINT IF EXISTS system_setting_pkey;
ALTER TABLE IF EXISTS ONLY public.system_api_key DROP CONSTRAINT IF EXISTS system_api_key_secret_key_key;
ALTER TABLE IF EXISTS ONLY public.system_api_key DROP CONSTRAINT IF EXISTS system_api_key_pkey;
ALTER TABLE IF EXISTS ONLY public.shared_resource_workspace_authorization DROP CONSTRAINT IF EXISTS shared_resource_workspace_authorization_pkey;
ALTER TABLE IF EXISTS ONLY public.role_setting DROP CONSTRAINT IF EXISTS role_setting_pkey;
ALTER TABLE IF EXISTS ONLY public.role_permission DROP CONSTRAINT IF EXISTS role_permission_role_id_permission_id_0a48a767_uniq;
ALTER TABLE IF EXISTS ONLY public.role_permission DROP CONSTRAINT IF EXISTS role_permission_pkey;
ALTER TABLE IF EXISTS ONLY public.resource_mapping DROP CONSTRAINT IF EXISTS resource_mapping_pkey;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_group_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_group_user_group_id_resource_t_5eccc9b0_uniq;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_group_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_group_authorize_pkey;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_authorize_pkey;
ALTER TABLE IF EXISTS ONLY public.resource_chat_user_authorize DROP CONSTRAINT IF EXISTS resource_chat_user_autho_user_group_id_resource_t_7fc1cc94_uniq;
ALTER TABLE IF EXISTS ONLY public.public_file_access DROP CONSTRAINT IF EXISTS public_file_access_pkey;
ALTER TABLE IF EXISTS ONLY public.problem DROP CONSTRAINT IF EXISTS problem_pkey;
ALTER TABLE IF EXISTS ONLY public.problem_paragraph_mapping DROP CONSTRAINT IF EXISTS problem_paragraph_mapping_pkey;
ALTER TABLE IF EXISTS ONLY public.platform_display_setting DROP CONSTRAINT IF EXISTS platform_display_setting_pkey;
ALTER TABLE IF EXISTS ONLY public.paragraph DROP CONSTRAINT IF EXISTS paragraph_pkey;
ALTER TABLE IF EXISTS ONLY public.model DROP CONSTRAINT IF EXISTS model_pkey;
ALTER TABLE IF EXISTS ONLY public.model DROP CONSTRAINT IF EXISTS model_name_workspace_id_68e244ba_uniq;
ALTER TABLE IF EXISTS ONLY public.log DROP CONSTRAINT IF EXISTS log_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_workflow_version DROP CONSTRAINT IF EXISTS knowledge_workflow_version_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_workflow DROP CONSTRAINT IF EXISTS knowledge_workflow_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_workflow DROP CONSTRAINT IF EXISTS knowledge_workflow_knowledge_id_key;
ALTER TABLE IF EXISTS ONLY public.knowledge DROP CONSTRAINT IF EXISTS knowledge_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_folder DROP CONSTRAINT IF EXISTS knowledge_folder_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_action DROP CONSTRAINT IF EXISTS knowledge_action_pkey;
ALTER TABLE IF EXISTS ONLY public.file DROP CONSTRAINT IF EXISTS file_pkey;
ALTER TABLE IF EXISTS ONLY public.event_trigger_task DROP CONSTRAINT IF EXISTS event_trigger_task_trigger_id_source_id_sou_f3530a5f_uniq;
ALTER TABLE IF EXISTS ONLY public.event_trigger_task_record DROP CONSTRAINT IF EXISTS event_trigger_task_record_pkey;
ALTER TABLE IF EXISTS ONLY public.event_trigger_task DROP CONSTRAINT IF EXISTS event_trigger_task_pkey;
ALTER TABLE IF EXISTS ONLY public.event_trigger DROP CONSTRAINT IF EXISTS event_trigger_pkey;
ALTER TABLE IF EXISTS ONLY public.embedding DROP CONSTRAINT IF EXISTS embedding_pkey;
ALTER TABLE IF EXISTS ONLY public.document_tag DROP CONSTRAINT IF EXISTS document_tag_pkey;
ALTER TABLE IF EXISTS ONLY public.document_tag DROP CONSTRAINT IF EXISTS document_tag_document_id_tag_id_55f500a6_uniq;
ALTER TABLE IF EXISTS ONLY public.document DROP CONSTRAINT IF EXISTS document_pkey;
ALTER TABLE IF EXISTS ONLY public.django_migrations DROP CONSTRAINT IF EXISTS django_migrations_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_app_label_model_76bd3d3b_uniq;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_solarschedule DROP CONSTRAINT IF EXISTS django_celery_beat_solarschedule_pkey;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_solarschedule DROP CONSTRAINT IF EXISTS django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictasks DROP CONSTRAINT IF EXISTS django_celery_beat_periodictasks_pkey;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictask DROP CONSTRAINT IF EXISTS django_celery_beat_periodictask_pkey;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_periodictask DROP CONSTRAINT IF EXISTS django_celery_beat_periodictask_name_key;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_intervalschedule DROP CONSTRAINT IF EXISTS django_celery_beat_intervalschedule_pkey;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_crontabschedule DROP CONSTRAINT IF EXISTS django_celery_beat_crontabschedule_pkey;
ALTER TABLE IF EXISTS ONLY public.django_celery_beat_clockedschedule DROP CONSTRAINT IF EXISTS django_celery_beat_clockedschedule_pkey;
ALTER TABLE IF EXISTS ONLY public.django_apscheduler_djangojobexecution DROP CONSTRAINT IF EXISTS django_apscheduler_djangojobexecution_pkey;
ALTER TABLE IF EXISTS ONLY public.django_apscheduler_djangojob DROP CONSTRAINT IF EXISTS django_apscheduler_djangojob_pkey;
ALTER TABLE IF EXISTS ONLY public.chat_user DROP CONSTRAINT IF EXISTS chat_user_username_key;
ALTER TABLE IF EXISTS ONLY public.chat_user DROP CONSTRAINT IF EXISTS chat_user_pkey;
ALTER TABLE IF EXISTS ONLY public.chat_user DROP CONSTRAINT IF EXISTS chat_user_nick_name_key;
ALTER TABLE IF EXISTS ONLY public.chat_platform DROP CONSTRAINT IF EXISTS chat_platform_pkey;
ALTER TABLE IF EXISTS ONLY public.chat_platform DROP CONSTRAINT IF EXISTS chat_platform_auth_type_key;
ALTER TABLE IF EXISTS ONLY public.chat_auth_setting DROP CONSTRAINT IF EXISTS chat_auth_setting_pkey;
ALTER TABLE IF EXISTS ONLY public.application_version DROP CONSTRAINT IF EXISTS application_version_pkey;
ALTER TABLE IF EXISTS ONLY public.application_setting DROP CONSTRAINT IF EXISTS application_setting_pkey;
ALTER TABLE IF EXISTS ONLY public.application_setting DROP CONSTRAINT IF EXISTS application_setting_application_id_key;
ALTER TABLE IF EXISTS ONLY public.application DROP CONSTRAINT IF EXISTS application_pkey;
ALTER TABLE IF EXISTS ONLY public.application_long_term_memory DROP CONSTRAINT IF EXISTS application_long_term_memory_pkey;
ALTER TABLE IF EXISTS ONLY public.application_long_term_memory DROP CONSTRAINT IF EXISTS application_long_term_me_application_id_chat_user_7f1bd03b_uniq;
ALTER TABLE IF EXISTS ONLY public.application_knowledge_mapping DROP CONSTRAINT IF EXISTS application_knowledge_mapping_pkey;
ALTER TABLE IF EXISTS ONLY public.application_folder DROP CONSTRAINT IF EXISTS application_folder_pkey;
ALTER TABLE IF EXISTS ONLY public.application_chat_user_stats DROP CONSTRAINT IF EXISTS application_chat_user_stats_pkey;
ALTER TABLE IF EXISTS ONLY public.application_chat_share_link DROP CONSTRAINT IF EXISTS application_chat_share_link_pkey;
ALTER TABLE IF EXISTS ONLY public.application_chat_record DROP CONSTRAINT IF EXISTS application_chat_record_pkey;
ALTER TABLE IF EXISTS ONLY public.application_chat DROP CONSTRAINT IF EXISTS application_chat_pkey;
ALTER TABLE IF EXISTS ONLY public.application_api_key DROP CONSTRAINT IF EXISTS application_api_key_secret_key_key;
ALTER TABLE IF EXISTS ONLY public.application_api_key DROP CONSTRAINT IF EXISTS application_api_key_pkey;
ALTER TABLE IF EXISTS ONLY public.application_access_token DROP CONSTRAINT IF EXISTS application_access_token_pkey;
ALTER TABLE IF EXISTS ONLY public.application_access_token DROP CONSTRAINT IF EXISTS application_access_token_access_token_key;
DROP TABLE IF EXISTS public.workspace_user_resource_permission;
DROP TABLE IF EXISTS public.workspace;
DROP TABLE IF EXISTS public.user_role_relation;
DROP TABLE IF EXISTS public.user_group_relation;
DROP TABLE IF EXISTS public.user_group;
DROP TABLE IF EXISTS public."user";
DROP TABLE IF EXISTS public.tool_workflow_version;
DROP TABLE IF EXISTS public.tool_workflow;
DROP TABLE IF EXISTS public.tool_record;
DROP TABLE IF EXISTS public.tool_folder;
DROP TABLE IF EXISTS public.tool;
DROP TABLE IF EXISTS public.termbase;
DROP TABLE IF EXISTS public.tag;
DROP TABLE IF EXISTS public.system_setting;
DROP TABLE IF EXISTS public.system_api_key;
DROP TABLE IF EXISTS public.shared_resource_workspace_authorization;
DROP TABLE IF EXISTS public.role_setting;
DROP TABLE IF EXISTS public.role_permission;
DROP TABLE IF EXISTS public.resource_mapping;
DROP TABLE IF EXISTS public.resource_chat_user_group_authorize;
DROP TABLE IF EXISTS public.resource_chat_user_authorize;
DROP TABLE IF EXISTS public.public_file_access;
DROP TABLE IF EXISTS public.problem_paragraph_mapping;
DROP TABLE IF EXISTS public.problem;
DROP TABLE IF EXISTS public.platform_display_setting;
DROP TABLE IF EXISTS public.paragraph;
DROP TABLE IF EXISTS public.model;
DROP TABLE IF EXISTS public.log;
DROP TABLE IF EXISTS public.knowledge_workflow_version;
DROP TABLE IF EXISTS public.knowledge_workflow;
DROP TABLE IF EXISTS public.knowledge_folder;
DROP TABLE IF EXISTS public.knowledge_action;
DROP TABLE IF EXISTS public.knowledge;
DROP TABLE IF EXISTS public.file;
DROP TABLE IF EXISTS public.event_trigger_task_record;
DROP TABLE IF EXISTS public.event_trigger_task;
DROP TABLE IF EXISTS public.event_trigger;
DROP TABLE IF EXISTS public.embedding;
DROP TABLE IF EXISTS public.document_tag;
DROP TABLE IF EXISTS public.document;
DROP TABLE IF EXISTS public.django_migrations;
DROP TABLE IF EXISTS public.django_content_type;
DROP TABLE IF EXISTS public.django_celery_beat_solarschedule;
DROP TABLE IF EXISTS public.django_celery_beat_periodictasks;
DROP TABLE IF EXISTS public.django_celery_beat_periodictask;
DROP TABLE IF EXISTS public.django_celery_beat_intervalschedule;
DROP TABLE IF EXISTS public.django_celery_beat_crontabschedule;
DROP TABLE IF EXISTS public.django_celery_beat_clockedschedule;
DROP TABLE IF EXISTS public.django_apscheduler_djangojobexecution;
DROP TABLE IF EXISTS public.django_apscheduler_djangojob;
DROP TABLE IF EXISTS public.chat_user;
DROP TABLE IF EXISTS public.chat_platform;
DROP TABLE IF EXISTS public.chat_auth_setting;
DROP TABLE IF EXISTS public.application_version;
DROP TABLE IF EXISTS public.application_setting;
DROP TABLE IF EXISTS public.application_long_term_memory;
DROP TABLE IF EXISTS public.application_knowledge_mapping;
DROP TABLE IF EXISTS public.application_folder;
DROP TABLE IF EXISTS public.application_chat_user_stats;
DROP TABLE IF EXISTS public.application_chat_share_link;
DROP TABLE IF EXISTS public.application_chat_record;
DROP TABLE IF EXISTS public.application_chat;
DROP TABLE IF EXISTS public.application_api_key;
DROP TABLE IF EXISTS public.application_access_token;
DROP TABLE IF EXISTS public.application;
DROP EXTENSION IF EXISTS vector;
--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--



--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: application; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    workspace_id character varying(64) NOT NULL,
    is_publish boolean NOT NULL,
    name character varying(128) NOT NULL,
    "desc" character varying(512) NOT NULL,
    prologue character varying(40960) NOT NULL,
    dialogue_number integer NOT NULL,
    knowledge_setting jsonb NOT NULL,
    model_setting jsonb NOT NULL,
    model_params_setting jsonb NOT NULL,
    tts_model_params_setting jsonb NOT NULL,
    problem_optimization boolean NOT NULL,
    icon character varying(256) NOT NULL,
    work_flow jsonb NOT NULL,
    type character varying(256) NOT NULL,
    problem_optimization_prompt character varying(102400),
    tts_model_enable boolean NOT NULL,
    stt_model_enable boolean NOT NULL,
    tts_type character varying(20) NOT NULL,
    tts_autoplay boolean NOT NULL,
    stt_autosend boolean NOT NULL,
    clean_time integer NOT NULL,
    publish_time timestamp with time zone,
    file_upload_enable boolean NOT NULL,
    file_upload_setting jsonb NOT NULL,
    model_id uuid,
    stt_model_id uuid,
    tts_model_id uuid,
    user_id uuid,
    folder_id character varying(64) CONSTRAINT application_folder_id_not_null1 NOT NULL,
    mcp_enable boolean NOT NULL,
    mcp_servers jsonb NOT NULL,
    mcp_source character varying(20) NOT NULL,
    mcp_tool_ids jsonb NOT NULL,
    tool_enable boolean NOT NULL,
    tool_ids jsonb NOT NULL,
    mcp_output_enable boolean NOT NULL,
    stt_model_params_setting jsonb NOT NULL,
    application_enable boolean NOT NULL,
    application_ids jsonb NOT NULL,
    file_clean_time integer NOT NULL,
    skill_tool_ids jsonb NOT NULL,
    long_term_enable boolean NOT NULL,
    long_term_model_id uuid,
    long_term_model_params_setting jsonb NOT NULL,
    long_term_trigger_setting jsonb NOT NULL,
    long_term_trigger_type character varying NOT NULL
);


--
-- Name: application_access_token; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_access_token (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    application_id uuid NOT NULL,
    access_token character varying(128) NOT NULL,
    is_active boolean NOT NULL,
    access_num integer NOT NULL,
    white_active boolean NOT NULL,
    white_list character varying(128)[] NOT NULL,
    show_source boolean NOT NULL,
    show_exec boolean NOT NULL,
    authentication boolean NOT NULL,
    authentication_value jsonb NOT NULL,
    language character varying(10)
);


--
-- Name: application_api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_api_key (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    secret_key character varying(1024) NOT NULL,
    workspace_id character varying(64) NOT NULL,
    is_active boolean NOT NULL,
    allow_cross_domain boolean NOT NULL,
    cross_domain_list character varying(128)[] NOT NULL,
    application_id uuid NOT NULL,
    expire_time timestamp with time zone NOT NULL,
    is_permanent boolean NOT NULL
);


--
-- Name: application_chat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_chat (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    abstract character varying(1024) NOT NULL,
    chat_user_id character varying,
    chat_user_type character varying(64) NOT NULL,
    is_deleted boolean NOT NULL,
    asker jsonb NOT NULL,
    meta jsonb NOT NULL,
    star_num integer NOT NULL,
    trample_num integer NOT NULL,
    chat_record_count integer NOT NULL,
    mark_sum integer NOT NULL,
    application_id uuid NOT NULL,
    ip_address character varying(128) NOT NULL,
    source jsonb NOT NULL
);


--
-- Name: application_chat_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_chat_record (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    vote_status character varying(10) NOT NULL,
    problem_text character varying(10240) NOT NULL,
    answer_text character varying(40960) NOT NULL,
    answer_text_list jsonb[] NOT NULL,
    message_tokens integer NOT NULL,
    answer_tokens integer NOT NULL,
    const integer NOT NULL,
    details jsonb NOT NULL,
    improve_paragraph_id_list uuid[] NOT NULL,
    run_time double precision NOT NULL,
    index integer NOT NULL,
    chat_id uuid NOT NULL,
    vote_other_content character varying(1024) NOT NULL,
    vote_reason character varying(50),
    ip_address character varying(128) NOT NULL,
    source jsonb NOT NULL
);


--
-- Name: application_chat_share_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_chat_share_link (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    share_type character varying(20) NOT NULL,
    chat_record_ids uuid[] NOT NULL,
    application_id uuid NOT NULL,
    chat_id uuid NOT NULL,
    user_id uuid
);


--
-- Name: application_chat_user_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_chat_user_stats (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    chat_user_id uuid NOT NULL,
    chat_user_type character varying(64) NOT NULL,
    access_num integer NOT NULL,
    intraday_access_num integer NOT NULL,
    application_id uuid NOT NULL
);


--
-- Name: application_folder; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_folder (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id character varying(64) NOT NULL,
    name character varying(64) NOT NULL,
    "desc" character varying(200),
    workspace_id character varying(64) NOT NULL,
    lft integer NOT NULL,
    rght integer NOT NULL,
    tree_id integer NOT NULL,
    level integer NOT NULL,
    parent_id character varying(64),
    user_id uuid,
    CONSTRAINT application_folder_level_check CHECK ((level >= 0)),
    CONSTRAINT application_folder_lft_check CHECK ((lft >= 0)),
    CONSTRAINT application_folder_rght_check CHECK ((rght >= 0)),
    CONSTRAINT application_folder_tree_id_check CHECK ((tree_id >= 0))
);


--
-- Name: application_knowledge_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_knowledge_mapping (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    knowledge_id uuid NOT NULL
);


--
-- Name: application_long_term_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_long_term_memory (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    chat_user_id character varying(128) NOT NULL,
    memory text NOT NULL,
    application_id uuid NOT NULL
);


--
-- Name: application_setting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_setting (
    id character varying(128) NOT NULL,
    show_history boolean NOT NULL,
    draggable boolean NOT NULL,
    show_guide boolean NOT NULL,
    avatar character varying(1024) NOT NULL,
    show_avatar boolean NOT NULL,
    float_icon character varying(1024) NOT NULL,
    disclaimer boolean NOT NULL,
    disclaimer_value text NOT NULL,
    custom_theme jsonb NOT NULL,
    user_avatar character varying(1024) NOT NULL,
    show_user_avatar boolean NOT NULL,
    show_share boolean NOT NULL,
    float_location jsonb NOT NULL,
    chat_background character varying(1024) NOT NULL,
    application_id uuid NOT NULL
);


--
-- Name: application_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_version (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying(128) NOT NULL,
    publish_user_id uuid,
    publish_user_name character varying(128) NOT NULL,
    workspace_id character varying(64) NOT NULL,
    application_name character varying(128) NOT NULL,
    "desc" character varying(512) NOT NULL,
    prologue character varying(40960) NOT NULL,
    dialogue_number integer NOT NULL,
    model_id uuid,
    knowledge_setting jsonb NOT NULL,
    model_setting jsonb NOT NULL,
    model_params_setting jsonb NOT NULL,
    tts_model_params_setting jsonb NOT NULL,
    problem_optimization boolean NOT NULL,
    icon character varying(256) NOT NULL,
    work_flow jsonb NOT NULL,
    type character varying(256) NOT NULL,
    problem_optimization_prompt character varying(102400),
    tts_model_id uuid,
    stt_model_id uuid,
    tts_model_enable boolean NOT NULL,
    stt_model_enable boolean NOT NULL,
    tts_type character varying(20) NOT NULL,
    tts_autoplay boolean NOT NULL,
    stt_autosend boolean NOT NULL,
    clean_time integer NOT NULL,
    file_upload_enable boolean NOT NULL,
    file_upload_setting jsonb NOT NULL,
    application_id uuid NOT NULL,
    user_id uuid,
    mcp_enable boolean NOT NULL,
    mcp_servers jsonb NOT NULL,
    mcp_source character varying(20) NOT NULL,
    mcp_tool_ids jsonb NOT NULL,
    tool_enable boolean NOT NULL,
    tool_ids jsonb NOT NULL,
    mcp_output_enable boolean NOT NULL,
    stt_model_params_setting jsonb NOT NULL,
    application_enable boolean NOT NULL,
    application_ids jsonb NOT NULL,
    skill_tool_ids jsonb NOT NULL,
    long_term_enable boolean NOT NULL,
    long_term_model_id uuid,
    long_term_model_params_setting jsonb NOT NULL,
    long_term_trigger_setting jsonb NOT NULL,
    long_term_trigger_type character varying NOT NULL,
    knowledge_ids jsonb NOT NULL
);


--
-- Name: chat_auth_setting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_auth_setting (
    auth_type character varying(64) NOT NULL,
    name character varying(64) NOT NULL,
    enabled boolean NOT NULL,
    config jsonb NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone
);


--
-- Name: chat_platform; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_platform (
    id character varying(128) NOT NULL,
    auth_type character varying(64) NOT NULL,
    name character varying(150) NOT NULL,
    is_active boolean NOT NULL,
    is_valid boolean NOT NULL,
    config jsonb NOT NULL
);


--
-- Name: chat_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_user (
    id uuid NOT NULL,
    email character varying(254),
    phone character varying(20) NOT NULL,
    nick_name character varying(150) NOT NULL,
    username character varying(150) NOT NULL,
    password character varying(150) NOT NULL,
    source character varying(10) NOT NULL,
    is_active boolean NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone
);


--
-- Name: django_apscheduler_djangojob; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_apscheduler_djangojob (
    id character varying(255) NOT NULL,
    next_run_time timestamp with time zone,
    job_state bytea NOT NULL
);


--
-- Name: django_apscheduler_djangojobexecution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_apscheduler_djangojobexecution (
    id bigint NOT NULL,
    status character varying(50) NOT NULL,
    run_time timestamp with time zone NOT NULL,
    duration numeric(15,2),
    finished numeric(15,2),
    exception character varying(1000),
    traceback text,
    job_id character varying(255) NOT NULL
);


--
-- Name: django_apscheduler_djangojobexecution_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_apscheduler_djangojobexecution ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_apscheduler_djangojobexecution_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_clockedschedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_celery_beat_clockedschedule (
    id integer NOT NULL,
    clocked_time timestamp with time zone NOT NULL
);


--
-- Name: django_celery_beat_clockedschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_clockedschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_clockedschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_crontabschedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_celery_beat_crontabschedule (
    id integer NOT NULL,
    minute character varying(240) NOT NULL,
    hour character varying(96) NOT NULL,
    day_of_week character varying(64) NOT NULL,
    day_of_month character varying(124) NOT NULL,
    month_of_year character varying(64) NOT NULL,
    timezone character varying(63) NOT NULL
);


--
-- Name: django_celery_beat_crontabschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_crontabschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_crontabschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_intervalschedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_celery_beat_intervalschedule (
    id integer NOT NULL,
    every integer NOT NULL,
    period character varying(24) NOT NULL
);


--
-- Name: django_celery_beat_intervalschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_intervalschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_intervalschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_periodictask; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_celery_beat_periodictask (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    task character varying(200) NOT NULL,
    args text NOT NULL,
    kwargs text NOT NULL,
    queue character varying(200),
    exchange character varying(200),
    routing_key character varying(200),
    expires timestamp with time zone,
    enabled boolean NOT NULL,
    last_run_at timestamp with time zone,
    total_run_count integer NOT NULL,
    date_changed timestamp with time zone NOT NULL,
    description text NOT NULL,
    crontab_id integer,
    interval_id integer,
    solar_id integer,
    one_off boolean NOT NULL,
    start_time timestamp with time zone,
    priority integer,
    headers text NOT NULL,
    clocked_id integer,
    expire_seconds integer,
    CONSTRAINT django_celery_beat_periodictask_expire_seconds_check CHECK ((expire_seconds >= 0)),
    CONSTRAINT django_celery_beat_periodictask_priority_check CHECK ((priority >= 0)),
    CONSTRAINT django_celery_beat_periodictask_total_run_count_check CHECK ((total_run_count >= 0))
);


--
-- Name: django_celery_beat_periodictask_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_periodictask ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_periodictask_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_periodictasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_celery_beat_periodictasks (
    ident smallint NOT NULL,
    last_update timestamp with time zone NOT NULL
);


--
-- Name: django_celery_beat_solarschedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_celery_beat_solarschedule (
    id integer NOT NULL,
    event character varying(24) NOT NULL,
    latitude numeric(9,6) NOT NULL,
    longitude numeric(9,6) NOT NULL
);


--
-- Name: django_celery_beat_solarschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_celery_beat_solarschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_solarschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: document; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying(150) NOT NULL,
    char_length integer NOT NULL,
    status character varying(20) NOT NULL,
    status_meta jsonb NOT NULL,
    is_active boolean NOT NULL,
    type integer NOT NULL,
    hit_handling_method character varying(20) NOT NULL,
    directly_return_similarity double precision NOT NULL,
    meta jsonb NOT NULL,
    knowledge_id uuid NOT NULL,
    user_id uuid
);


--
-- Name: document_tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_tag (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    tag_id uuid NOT NULL
);


--
-- Name: embedding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.embedding (
    id character varying(128) NOT NULL,
    source_id character varying(128) NOT NULL,
    source_type character varying(5) NOT NULL,
    is_active boolean NOT NULL,
    embedding public.vector NOT NULL,
    search_vector tsvector NOT NULL,
    meta jsonb NOT NULL,
    document_id uuid NOT NULL,
    knowledge_id uuid NOT NULL,
    paragraph_id uuid NOT NULL
);


--
-- Name: event_trigger; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_trigger (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    workspace_id character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    "desc" character varying(512) NOT NULL,
    trigger_type character varying(256) NOT NULL,
    trigger_setting jsonb NOT NULL,
    meta jsonb NOT NULL,
    is_active boolean NOT NULL,
    user_id uuid
);


--
-- Name: event_trigger_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_trigger_task (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    source_type character varying(256) NOT NULL,
    source_id uuid NOT NULL,
    is_active boolean NOT NULL,
    parameter jsonb NOT NULL,
    meta jsonb NOT NULL,
    trigger_id uuid NOT NULL
);


--
-- Name: event_trigger_task_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_trigger_task_record (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    source_type character varying(256) NOT NULL,
    source_id uuid NOT NULL,
    task_record_id uuid NOT NULL,
    meta jsonb NOT NULL,
    state character varying(20) NOT NULL,
    run_time double precision NOT NULL,
    trigger_id uuid NOT NULL,
    trigger_task_id uuid NOT NULL
);


--
-- Name: file; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.file (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    file_name character varying(256) NOT NULL,
    file_size integer NOT NULL,
    sha256_hash character varying NOT NULL,
    source_type character varying NOT NULL,
    source_id character varying NOT NULL,
    loid integer NOT NULL,
    meta jsonb NOT NULL
);


--
-- Name: knowledge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying(150) NOT NULL,
    workspace_id character varying(64) NOT NULL,
    "desc" character varying(256) NOT NULL,
    type integer NOT NULL,
    scope character varying(20) NOT NULL,
    file_size_limit integer NOT NULL,
    file_count_limit integer NOT NULL,
    meta jsonb NOT NULL,
    embedding_model_id uuid,
    user_id uuid,
    folder_id character varying(64) CONSTRAINT knowledge_folder_id_not_null1 NOT NULL
);


--
-- Name: knowledge_action; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_action (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    state character varying(20) NOT NULL,
    details jsonb NOT NULL,
    run_time double precision NOT NULL,
    meta jsonb NOT NULL,
    knowledge_id uuid NOT NULL
);


--
-- Name: knowledge_folder; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_folder (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id character varying(64) NOT NULL,
    name character varying(64) NOT NULL,
    "desc" character varying(200),
    workspace_id character varying(64) NOT NULL,
    lft integer NOT NULL,
    rght integer NOT NULL,
    tree_id integer NOT NULL,
    level integer NOT NULL,
    parent_id character varying(64),
    user_id uuid,
    CONSTRAINT knowledge_folder_level_check CHECK ((level >= 0)),
    CONSTRAINT knowledge_folder_lft_check CHECK ((lft >= 0)),
    CONSTRAINT knowledge_folder_rght_check CHECK ((rght >= 0)),
    CONSTRAINT knowledge_folder_tree_id_check CHECK ((tree_id >= 0))
);


--
-- Name: knowledge_workflow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_workflow (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    workspace_id character varying(64) NOT NULL,
    work_flow jsonb NOT NULL,
    is_publish boolean NOT NULL,
    publish_time timestamp with time zone,
    knowledge_id uuid NOT NULL
);


--
-- Name: knowledge_workflow_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_workflow_version (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    workspace_id character varying(64) NOT NULL,
    work_flow jsonb NOT NULL,
    publish_user_id uuid,
    publish_user_name character varying(128) NOT NULL,
    knowledge_id uuid NOT NULL,
    name character varying(128) NOT NULL
);


--
-- Name: log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.log (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    menu character varying(128) NOT NULL,
    operate character varying(128) NOT NULL,
    operation_object jsonb NOT NULL,
    "user" jsonb NOT NULL,
    status integer NOT NULL,
    ip_address character varying(128) NOT NULL,
    details jsonb NOT NULL,
    workspace_id character varying(64) NOT NULL
);


--
-- Name: model; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying(128) NOT NULL,
    status character varying(20) NOT NULL,
    model_type character varying(128) NOT NULL,
    model_name character varying(128) NOT NULL,
    provider character varying(128) NOT NULL,
    credential character varying(102400) NOT NULL,
    meta jsonb NOT NULL,
    model_params_form jsonb NOT NULL,
    workspace_id character varying(64) NOT NULL,
    user_id uuid
);


--
-- Name: paragraph; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paragraph (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    content character varying(102400) NOT NULL,
    title character varying(256) NOT NULL,
    status character varying(20) NOT NULL,
    status_meta jsonb NOT NULL,
    hit_num integer NOT NULL,
    is_active boolean NOT NULL,
    "position" integer NOT NULL,
    document_id uuid NOT NULL,
    knowledge_id uuid NOT NULL,
    chunks character varying[] NOT NULL
);


--
-- Name: platform_display_setting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_display_setting (
    id character varying(64) NOT NULL,
    meta jsonb NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone
);


--
-- Name: problem; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.problem (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    content character varying(256) NOT NULL,
    hit_num integer NOT NULL,
    knowledge_id uuid NOT NULL
);


--
-- Name: problem_paragraph_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.problem_paragraph_mapping (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    knowledge_id uuid NOT NULL,
    paragraph_id uuid NOT NULL,
    problem_id uuid NOT NULL
);


--
-- Name: public_file_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_file_access (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    source_type character varying(20) NOT NULL,
    source_id character varying(128) NOT NULL
);


--
-- Name: resource_chat_user_authorize; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_chat_user_authorize (
    id uuid NOT NULL,
    workspace_id character varying(64),
    resource_id uuid NOT NULL,
    resource_type character varying NOT NULL,
    is_auth boolean NOT NULL,
    user_id uuid NOT NULL,
    user_group_id character varying(128) NOT NULL
);


--
-- Name: resource_chat_user_group_authorize; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_chat_user_group_authorize (
    id uuid NOT NULL,
    workspace_id character varying(64),
    resource_id uuid NOT NULL,
    resource_type character varying NOT NULL,
    is_auth boolean NOT NULL,
    user_group_id character varying(128) NOT NULL
);


--
-- Name: resource_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_mapping (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    source_type character varying NOT NULL,
    target_type character varying NOT NULL,
    source_id character varying(128) NOT NULL,
    target_id character varying(128) NOT NULL
);


--
-- Name: role_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permission (
    id uuid NOT NULL,
    permission_id character varying(256) NOT NULL,
    role_id character varying(128) NOT NULL
);


--
-- Name: role_setting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_setting (
    id character varying(128) NOT NULL,
    role_name character varying(64) NOT NULL,
    type character varying(64) NOT NULL,
    internal boolean NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone,
    create_user_id uuid
);


--
-- Name: shared_resource_workspace_authorization; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shared_resource_workspace_authorization (
    id character varying(128) NOT NULL,
    resource_type character varying(32) NOT NULL,
    authentication_type character varying(32) CONSTRAINT shared_resource_workspace_authoriz_authentication_type_not_null NOT NULL,
    workspace_id_list character varying(128)[] CONSTRAINT shared_resource_workspace_authorizat_workspace_id_list_not_null NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone
);


--
-- Name: system_api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_api_key (
    id uuid NOT NULL,
    secret_key character varying(1024) NOT NULL,
    is_active boolean NOT NULL,
    allow_cross_domain boolean NOT NULL,
    cross_domain_list character varying(128)[] NOT NULL,
    expire_time timestamp with time zone NOT NULL,
    is_permanent boolean NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone,
    user_id uuid NOT NULL
);


--
-- Name: system_setting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_setting (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    type integer NOT NULL,
    meta jsonb NOT NULL
);


--
-- Name: tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tag (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    key character varying(64) NOT NULL,
    value character varying(128) NOT NULL,
    knowledge_id uuid NOT NULL
);


--
-- Name: termbase; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.termbase (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    content character varying(256) NOT NULL,
    knowledge_id uuid NOT NULL
);


--
-- Name: tool; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tool (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying(64) NOT NULL,
    "desc" character varying(128) NOT NULL,
    code character varying(102400) NOT NULL,
    input_field_list jsonb NOT NULL,
    init_field_list jsonb NOT NULL,
    icon character varying(256) NOT NULL,
    is_active boolean NOT NULL,
    scope character varying(20) NOT NULL,
    tool_type character varying(20) NOT NULL,
    template_id character varying(128),
    workspace_id character varying(64) NOT NULL,
    init_params character varying(102400),
    label character varying(128),
    user_id uuid,
    folder_id character varying(64) CONSTRAINT tool_folder_id_not_null1 NOT NULL,
    version character varying(64)
);


--
-- Name: tool_folder; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tool_folder (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id character varying(64) NOT NULL,
    name character varying(64) NOT NULL,
    "desc" character varying(200),
    workspace_id character varying(64) NOT NULL,
    lft integer NOT NULL,
    rght integer NOT NULL,
    tree_id integer NOT NULL,
    level integer NOT NULL,
    parent_id character varying(64),
    user_id uuid,
    CONSTRAINT tool_folder_level_check CHECK ((level >= 0)),
    CONSTRAINT tool_folder_lft_check CHECK ((lft >= 0)),
    CONSTRAINT tool_folder_rght_check CHECK ((rght >= 0)),
    CONSTRAINT tool_folder_tree_id_check CHECK ((tree_id >= 0))
);


--
-- Name: tool_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tool_record (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    source_type character varying(256) NOT NULL,
    source_id uuid NOT NULL,
    meta jsonb NOT NULL,
    state character varying(20) NOT NULL,
    run_time double precision NOT NULL,
    tool_id uuid,
    workspace_id character varying(64) NOT NULL
);


--
-- Name: tool_workflow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tool_workflow (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    workspace_id character varying(64) NOT NULL,
    work_flow jsonb NOT NULL,
    is_publish boolean NOT NULL,
    publish_time timestamp with time zone,
    tool_id uuid NOT NULL
);


--
-- Name: tool_workflow_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tool_workflow_version (
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    workspace_id character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    work_flow jsonb NOT NULL,
    publish_user_id uuid,
    publish_user_name character varying(128) NOT NULL,
    tool_id uuid NOT NULL
);


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id uuid NOT NULL,
    email character varying(254),
    phone character varying(20) NOT NULL,
    nick_name character varying(150) NOT NULL,
    username character varying(150) NOT NULL,
    password character varying(150) NOT NULL,
    role character varying(150) NOT NULL,
    source character varying(10) NOT NULL,
    is_active boolean NOT NULL,
    language character varying(10),
    create_time timestamp with time zone,
    update_time timestamp with time zone
);


--
-- Name: user_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_group (
    id character varying(128) NOT NULL,
    name character varying(150) NOT NULL
);


--
-- Name: user_group_relation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_group_relation (
    id uuid NOT NULL,
    group_id character varying(128) NOT NULL,
    user_id uuid NOT NULL
);


--
-- Name: user_role_relation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_role_relation (
    id uuid NOT NULL,
    role_id character varying(128) NOT NULL,
    user_id uuid NOT NULL,
    workspace_id character varying(128) NOT NULL
);


--
-- Name: workspace; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workspace (
    id character varying(128) NOT NULL,
    name character varying(64) NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone,
    create_user_id uuid
);


--
-- Name: workspace_user_resource_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workspace_user_resource_permission (
    id uuid NOT NULL,
    workspace_id character varying(128) NOT NULL,
    auth_target_type character varying(128) NOT NULL,
    target character varying(128) NOT NULL,
    auth_type character varying DEFAULT 'ROLE'::character varying NOT NULL,
    permission_list character varying(256)[] NOT NULL,
    create_time timestamp with time zone NOT NULL,
    update_time timestamp with time zone NOT NULL,
    user_id uuid NOT NULL
);


--
-- Data for Name: application; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application (create_time, update_time, id, workspace_id, is_publish, name, "desc", prologue, dialogue_number, knowledge_setting, model_setting, model_params_setting, tts_model_params_setting, problem_optimization, icon, work_flow, type, problem_optimization_prompt, tts_model_enable, stt_model_enable, tts_type, tts_autoplay, stt_autosend, clean_time, publish_time, file_upload_enable, file_upload_setting, model_id, stt_model_id, tts_model_id, user_id, folder_id, mcp_enable, mcp_servers, mcp_source, mcp_tool_ids, tool_enable, tool_ids, mcp_output_enable, stt_model_params_setting, application_enable, application_ids, file_clean_time, skill_tool_ids, long_term_enable, long_term_model_id, long_term_model_params_setting, long_term_trigger_setting, long_term_trigger_type) FROM stdin;
\.


--
-- Data for Name: application_access_token; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_access_token (create_time, update_time, application_id, access_token, is_active, access_num, white_active, white_list, show_source, show_exec, authentication, authentication_value, language) FROM stdin;
\.


--
-- Data for Name: application_api_key; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_api_key (create_time, update_time, id, secret_key, workspace_id, is_active, allow_cross_domain, cross_domain_list, application_id, expire_time, is_permanent) FROM stdin;
\.


--
-- Data for Name: application_chat; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_chat (create_time, update_time, id, abstract, chat_user_id, chat_user_type, is_deleted, asker, meta, star_num, trample_num, chat_record_count, mark_sum, application_id, ip_address, source) FROM stdin;
\.


--
-- Data for Name: application_chat_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_chat_record (create_time, update_time, id, vote_status, problem_text, answer_text, answer_text_list, message_tokens, answer_tokens, const, details, improve_paragraph_id_list, run_time, index, chat_id, vote_other_content, vote_reason, ip_address, source) FROM stdin;
\.


--
-- Data for Name: application_chat_share_link; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_chat_share_link (create_time, update_time, id, share_type, chat_record_ids, application_id, chat_id, user_id) FROM stdin;
\.


--
-- Data for Name: application_chat_user_stats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_chat_user_stats (create_time, update_time, id, chat_user_id, chat_user_type, access_num, intraday_access_num, application_id) FROM stdin;
\.


--
-- Data for Name: application_folder; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_folder (create_time, update_time, id, name, "desc", workspace_id, lft, rght, tree_id, level, parent_id, user_id) FROM stdin;
2026-08-10 01:24:00.486443+00	2026-08-10 01:24:00.486453+00	default	根目录	\N	default	1	2	1	0	\N	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Data for Name: application_knowledge_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_knowledge_mapping (create_time, update_time, id, application_id, knowledge_id) FROM stdin;
\.


--
-- Data for Name: application_long_term_memory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_long_term_memory (create_time, update_time, id, chat_user_id, memory, application_id) FROM stdin;
\.


--
-- Data for Name: application_setting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_setting (id, show_history, draggable, show_guide, avatar, show_avatar, float_icon, disclaimer, disclaimer_value, custom_theme, user_avatar, show_user_avatar, show_share, float_location, chat_background, application_id) FROM stdin;
\.


--
-- Data for Name: application_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.application_version (create_time, update_time, id, name, publish_user_id, publish_user_name, workspace_id, application_name, "desc", prologue, dialogue_number, model_id, knowledge_setting, model_setting, model_params_setting, tts_model_params_setting, problem_optimization, icon, work_flow, type, problem_optimization_prompt, tts_model_id, stt_model_id, tts_model_enable, stt_model_enable, tts_type, tts_autoplay, stt_autosend, clean_time, file_upload_enable, file_upload_setting, application_id, user_id, mcp_enable, mcp_servers, mcp_source, mcp_tool_ids, tool_enable, tool_ids, mcp_output_enable, stt_model_params_setting, application_enable, application_ids, skill_tool_ids, long_term_enable, long_term_model_id, long_term_model_params_setting, long_term_trigger_setting, long_term_trigger_type, knowledge_ids) FROM stdin;
\.


--
-- Data for Name: chat_auth_setting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_auth_setting (auth_type, name, enabled, config, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: chat_platform; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_platform (id, auth_type, name, is_active, is_valid, config) FROM stdin;
019fe945-0a2e-77c2-b2b7-6df349a7fb1c	LOCAL	本地账号	t	t	{}
\.


--
-- Data for Name: chat_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_user (id, email, phone, nick_name, username, password, source, is_active, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: django_apscheduler_djangojob; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_apscheduler_djangojob (id, next_run_time, job_state) FROM stdin;
\.


--
-- Data for Name: django_apscheduler_djangojobexecution; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_apscheduler_djangojobexecution (id, status, run_time, duration, finished, exception, traceback, job_id) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_clockedschedule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_celery_beat_clockedschedule (id, clocked_time) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_crontabschedule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_celery_beat_crontabschedule (id, minute, hour, day_of_week, day_of_month, month_of_year, timezone) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_intervalschedule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_celery_beat_intervalschedule (id, every, period) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_periodictask; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_celery_beat_periodictask (id, name, task, args, kwargs, queue, exchange, routing_key, expires, enabled, last_run_at, total_run_count, date_changed, description, crontab_id, interval_id, solar_id, one_off, start_time, priority, headers, clocked_id, expire_seconds) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_periodictasks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_celery_beat_periodictasks (ident, last_update) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_solarschedule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_celery_beat_solarschedule (id, event, latitude, longitude) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	contenttypes	contenttype
2	users	user
3	tools	toolfolder
4	tools	tool
5	tools	toolrecord
6	tools	toolworkflow
7	tools	toolworkflowversion
8	knowledge	file
9	knowledge	knowledge
10	knowledge	document
11	knowledge	knowledgefolder
12	knowledge	paragraph
13	knowledge	embedding
14	knowledge	problem
15	knowledge	problemparagraphmapping
16	knowledge	tag
17	knowledge	documenttag
18	knowledge	knowledgeworkflow
19	knowledge	knowledgeworkflowversion
20	knowledge	knowledgeaction
21	knowledge	termbase
22	knowledge	publicfileaccess
23	system_manage	chatuser
24	system_manage	log
25	system_manage	systemsetting
26	system_manage	usergroup
27	system_manage	usergrouprelation
28	system_manage	workspaceuserresourcepermission
29	system_manage	resourcechatusergroupauthorize
30	system_manage	resourcechatuserauthorize
31	system_manage	resourcemapping
32	models_provider	model
33	django_celery_beat	crontabschedule
34	django_celery_beat	intervalschedule
35	django_celery_beat	periodictask
36	django_celery_beat	periodictasks
37	django_celery_beat	solarschedule
38	django_celery_beat	clockedschedule
39	application	application
40	application	applicationaccesstoken
41	application	applicationapikey
42	application	applicationfolder
43	application	applicationknowledgemapping
44	application	applicationversion
45	application	chat
46	application	chatrecord
47	application	applicationchatuserstats
48	application	chatsharelink
49	application	applicationlongtermmemory
50	trigger	trigger
51	trigger	triggertask
52	trigger	taskrecord
53	xpack_lite	chatauthsetting
54	xpack_lite	workspace
55	xpack_lite	rolesetting
56	xpack_lite	rolepermissionmapping
57	xpack_lite	workspaceuserrolemapping
58	xpack_lite	chatplatform
59	xpack_lite	applicationsetting
60	xpack_lite	platformdisplaysetting
61	xpack_lite	systemapikey
62	xpack_lite	sharedresourceworkspaceauthorization
63	django_apscheduler	djangojob
64	django_apscheduler	djangojobexecution
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	users	0001_initial	2026-08-10 01:23:57.156155+00
2	tools	0001_initial	2026-08-10 01:23:57.320857+00
3	system_manage	0001_initial	2026-08-10 01:23:57.675093+00
4	system_manage	0002_refresh_collation_reindex	2026-08-10 01:23:58.366274+00
5	models_provider	0001_initial	2026-08-10 01:23:59.902087+00
6	knowledge	0001_initial	2026-08-10 01:24:00.290395+00
7	application	0001_initial	2026-08-10 01:24:00.752021+00
8	system_manage	0003_alter_workspaceuserresourcepermission_target	2026-08-10 01:24:00.877118+00
9	system_manage	0004_alter_systemsetting_type_and_more	2026-08-10 01:24:00.942679+00
10	knowledge	0002_alter_file_source_type	2026-08-10 01:24:00.964362+00
11	knowledge	0003_tag_documenttag	2026-08-10 01:24:01.058337+00
12	knowledge	0004_alter_document_type_alter_knowledge_type_and_more	2026-08-10 01:24:01.152727+00
13	knowledge	0005_knowledgeaction	2026-08-10 01:24:01.186338+00
14	knowledge	0006_paragraph_chunks	2026-08-10 01:24:01.193793+00
15	knowledge	0007_remove_knowledgeworkflowversion_workflow_and_more	2026-08-10 01:24:01.222921+00
16	application	0002_application_simple_mcp	2026-08-10 01:24:01.331046+00
17	application	0003_application_stt_model_params_setting_and_more	2026-08-10 01:24:01.52316+00
18	system_manage	0005_resourcemapping	2026-08-10 01:24:01.625312+00
19	application	0004_application_application_enable_and_more	2026-08-10 01:24:01.659707+00
20	application	0005_chatrecord_vote_other_content_chatrecord_vote_reason	2026-08-10 01:24:01.667854+00
21	application	0006_application_file_clean_time	2026-08-10 01:24:01.694981+00
22	application	0007_applicationapikey_expire_time_and_more	2026-08-10 01:24:01.712773+00
23	application	0008_chat_ip_address_chat_source_chatrecord_ip_address_and_more	2026-08-10 01:24:01.734324+00
24	application	0009_clean_application_knowledge_mapping	2026-08-10 01:24:01.740187+00
25	application	0010_chatsharelink	2026-08-10 01:24:01.788703+00
26	application	0011_application_skill_tool_ids	2026-08-10 01:24:01.806558+00
27	application	0012_remove_applicationapikey_user	2026-08-10 01:24:01.823489+00
28	application	0013_application_long_term_enable_and_more	2026-08-10 01:24:01.961576+00
29	application	0014_applicationversion_knowledge_ids	2026-08-10 01:24:02.006196+00
30	contenttypes	0001_initial	2026-08-10 01:24:02.023137+00
31	contenttypes	0002_remove_content_type_name	2026-08-10 01:24:02.041296+00
32	django_apscheduler	0001_initial	2026-08-10 01:24:02.092312+00
33	django_apscheduler	0002_auto_20180412_0758	2026-08-10 01:24:02.09611+00
34	django_apscheduler	0003_auto_20200716_1632	2026-08-10 01:24:02.106265+00
35	django_apscheduler	0004_auto_20200717_1043	2026-08-10 01:24:02.16965+00
36	django_apscheduler	0005_migrate_name_to_id	2026-08-10 01:24:02.221849+00
37	django_apscheduler	0006_remove_djangojob_name	2026-08-10 01:24:02.22615+00
38	django_apscheduler	0007_auto_20200717_1404	2026-08-10 01:24:02.261103+00
39	django_apscheduler	0008_remove_djangojobexecution_started	2026-08-10 01:24:02.280654+00
40	django_apscheduler	0009_djangojobexecution_unique_job_executions	2026-08-10 01:24:02.287957+00
41	django_celery_beat	0001_initial	2026-08-10 01:24:02.344968+00
42	django_celery_beat	0002_auto_20161118_0346	2026-08-10 01:24:02.36806+00
43	django_celery_beat	0003_auto_20161209_0049	2026-08-10 01:24:02.378597+00
44	django_celery_beat	0004_auto_20170221_0000	2026-08-10 01:24:02.38136+00
45	django_celery_beat	0005_add_solarschedule_events_choices	2026-08-10 01:24:02.385221+00
46	django_celery_beat	0006_auto_20180322_0932	2026-08-10 01:24:02.409828+00
47	django_celery_beat	0007_auto_20180521_0826	2026-08-10 01:24:02.420424+00
48	django_celery_beat	0008_auto_20180914_1922	2026-08-10 01:24:02.436411+00
49	django_celery_beat	0006_auto_20180210_1226	2026-08-10 01:24:02.447255+00
50	django_celery_beat	0006_periodictask_priority	2026-08-10 01:24:02.454622+00
51	django_celery_beat	0009_periodictask_headers	2026-08-10 01:24:02.461342+00
52	django_celery_beat	0010_auto_20190429_0326	2026-08-10 01:24:02.55179+00
53	django_celery_beat	0011_auto_20190508_0153	2026-08-10 01:24:02.578629+00
54	django_celery_beat	0012_periodictask_expire_seconds	2026-08-10 01:24:02.585668+00
55	django_celery_beat	0013_auto_20200609_0727	2026-08-10 01:24:02.592558+00
56	django_celery_beat	0014_remove_clockedschedule_enabled	2026-08-10 01:24:02.597268+00
57	django_celery_beat	0015_edit_solarschedule_events_choices	2026-08-10 01:24:02.600624+00
58	django_celery_beat	0016_alter_crontabschedule_timezone	2026-08-10 01:24:02.60775+00
59	django_celery_beat	0017_alter_crontabschedule_month_of_year	2026-08-10 01:24:02.613674+00
60	django_celery_beat	0018_improve_crontab_helptext	2026-08-10 01:24:02.619302+00
61	django_celery_beat	0019_alter_periodictasks_options	2026-08-10 01:24:02.622249+00
62	knowledge	0008_termbase	2026-08-10 01:24:02.665538+00
63	knowledge	0009_document_user	2026-08-10 01:24:02.684515+00
64	knowledge	0010_publicfileaccess	2026-08-10 01:24:02.716476+00
65	tools	0002_alter_tool_tool_type	2026-08-10 01:24:02.723258+00
66	tools	0003_alter_tool_template_id	2026-08-10 01:24:02.843829+00
67	tools	0004_alter_tool_tool_type	2026-08-10 01:24:02.918362+00
68	tools	0005_taskrecord	2026-08-10 01:24:03.054673+00
69	tools	0006_alter_tool_tool_type	2026-08-10 01:24:03.063088+00
70	tools	0007_alter_tool_tool_type_toolworkflow_and_more	2026-08-10 01:24:03.182444+00
71	trigger	0001_initial	2026-08-10 01:24:03.361448+00
72	trigger	0002_remove_taskrecord_trigger_task_and_more	2026-08-10 01:24:03.389987+00
73	xpack_lite	0001_initial	2026-08-10 01:24:03.678046+00
74	xpack_lite	0002_chat_auth_runtime	2026-08-10 01:24:03.787349+00
75	xpack_lite	0003_platform_display_setting	2026-08-10 01:24:03.836289+00
76	xpack_lite	0004_system_api_key	2026-08-10 01:24:03.892222+00
77	xpack_lite	0005_shared_resource_workspace_authorization	2026-08-10 01:24:03.922068+00
\.


--
-- Data for Name: document; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.document (create_time, update_time, id, name, char_length, status, status_meta, is_active, type, hit_handling_method, directly_return_similarity, meta, knowledge_id, user_id) FROM stdin;
\.


--
-- Data for Name: document_tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.document_tag (create_time, update_time, id, document_id, tag_id) FROM stdin;
\.


--
-- Data for Name: embedding; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.embedding (id, source_id, source_type, is_active, embedding, search_vector, meta, document_id, knowledge_id, paragraph_id) FROM stdin;
\.


--
-- Data for Name: event_trigger; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_trigger (create_time, update_time, id, workspace_id, name, "desc", trigger_type, trigger_setting, meta, is_active, user_id) FROM stdin;
\.


--
-- Data for Name: event_trigger_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_trigger_task (create_time, update_time, id, source_type, source_id, is_active, parameter, meta, trigger_id) FROM stdin;
\.


--
-- Data for Name: event_trigger_task_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_trigger_task_record (create_time, update_time, id, source_type, source_id, task_record_id, meta, state, run_time, trigger_id, trigger_task_id) FROM stdin;
\.


--
-- Data for Name: file; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.file (create_time, update_time, id, file_name, file_size, sha256_hash, source_type, source_id, loid, meta) FROM stdin;
\.


--
-- Data for Name: knowledge; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge (create_time, update_time, id, name, workspace_id, "desc", type, scope, file_size_limit, file_count_limit, meta, embedding_model_id, user_id, folder_id) FROM stdin;
\.


--
-- Data for Name: knowledge_action; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge_action (create_time, update_time, id, state, details, run_time, meta, knowledge_id) FROM stdin;
\.


--
-- Data for Name: knowledge_folder; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge_folder (create_time, update_time, id, name, "desc", workspace_id, lft, rght, tree_id, level, parent_id, user_id) FROM stdin;
2026-08-10 01:24:00.015709+00	2026-08-10 01:24:00.015719+00	default	根目录	\N	default	1	2	1	0	\N	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Data for Name: knowledge_workflow; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge_workflow (create_time, update_time, id, workspace_id, work_flow, is_publish, publish_time, knowledge_id) FROM stdin;
\.


--
-- Data for Name: knowledge_workflow_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge_workflow_version (create_time, update_time, id, workspace_id, work_flow, publish_user_id, publish_user_name, knowledge_id, name) FROM stdin;
\.


--
-- Data for Name: log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.log (create_time, update_time, id, menu, operate, operation_object, "user", status, ip_address, details, workspace_id) FROM stdin;
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.model (create_time, update_time, id, name, status, model_type, model_name, provider, credential, meta, model_params_form, workspace_id, user_id) FROM stdin;
2026-08-10 01:23:59.823078+00	2026-08-10 01:23:59.823085+00	42f63a3d-427e-11ef-b3ec-a8a1595801ab	telecom-ai-embedding	SUCCESS	EMBEDDING	telecom-ai-local-hash-embedding	model_local_provider	YfNkB3jzeXwKC1Er4JZEIAAX2Mgzj/vRVOt5gzD6Uo/9RVuZTdz04SadBNnrBuA9SkRVF3qC1+KMDwiZBEwC/++nfy2dl+5PTDpfXEES1/1UV6mPx60BO118ylQR8M0VeoBIglCdOmY5Z+BVhO1cjJhD3mx58N4WnecMOJEI3HTfaKT3SOn1aaUN51nOo9fvW+JJ/MX2KmqzJqN3CnuncCJc2jxprvS+6EgIMHluNxJMsgSyNFunukBTKnErFUAuXITlw2/NEoMA8Di+HM2NuOhT95HPmtO25luZZfEF+IA0ZAsVZ/4wWlcmO8pUeNno27lPVb3fe4kvzzzjRKGFug==	{}	[]	default	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Data for Name: paragraph; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.paragraph (create_time, update_time, id, content, title, status, status_meta, hit_num, is_active, "position", document_id, knowledge_id, chunks) FROM stdin;
\.


--
-- Data for Name: platform_display_setting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.platform_display_setting (id, meta, create_time, update_time) FROM stdin;
default	{"icon": "", "theme": "#3370FF", "title": "电信智能体", "slogan": "开箱即用、灵活编排的企业级智能体平台", "forumUrl": "", "loginLogo": "", "showForum": false, "loginImage": "", "projectUrl": "", "showProject": false, "userManualUrl": "", "showUserManual": false}	2026-08-10 01:24:03.82215+00	2026-08-10 01:24:03.82216+00
\.


--
-- Data for Name: problem; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.problem (create_time, update_time, id, content, hit_num, knowledge_id) FROM stdin;
\.


--
-- Data for Name: problem_paragraph_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.problem_paragraph_mapping (create_time, update_time, id, document_id, knowledge_id, paragraph_id, problem_id) FROM stdin;
\.


--
-- Data for Name: public_file_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.public_file_access (create_time, update_time, id, source_type, source_id) FROM stdin;
\.


--
-- Data for Name: resource_chat_user_authorize; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resource_chat_user_authorize (id, workspace_id, resource_id, resource_type, is_auth, user_id, user_group_id) FROM stdin;
\.


--
-- Data for Name: resource_chat_user_group_authorize; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resource_chat_user_group_authorize (id, workspace_id, resource_id, resource_type, is_auth, user_group_id) FROM stdin;
\.


--
-- Data for Name: resource_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resource_mapping (create_time, update_time, id, source_type, target_type, source_id, target_id) FROM stdin;
\.


--
-- Data for Name: role_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_permission (id, permission_id, role_id) FROM stdin;
019fe945-381f-7293-afe8-5720e5d169be	HOMEPAGE:READ	ADMIN
019fe945-381f-7293-afe8-573fd89e1d82	HOMEPAGE:READ	USER
019fe945-381f-7293-afe8-574c836a801e	HOMEPAGE:READ	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-575f149c32db	HOMEPAGE:READ+EXPORT	ADMIN
019fe945-381f-7293-afe8-576ff9a8e2c0	HOMEPAGE:READ+EXPORT	USER
019fe945-381f-7293-afe8-5779268f9612	HOMEPAGE:READ+EXPORT	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-578ebda1fde0	KNOWLEDGE	ADMIN
019fe945-381f-7293-afe8-5790790e4838	KNOWLEDGE	USER
019fe945-381f-7293-afe8-57a32e7ddad9	APPLICATION	ADMIN
019fe945-381f-7293-afe8-57bc0e9ca4d6	APPLICATION	USER
019fe945-381f-7293-afe8-57c627d8e55c	MODEL	ADMIN
019fe945-381f-7293-afe8-57d56684efae	MODEL	USER
019fe945-381f-7293-afe8-57e88c842679	TOOL	ADMIN
019fe945-381f-7293-afe8-57ff66f9906c	TOOL	USER
019fe945-381f-7293-afe8-5803fa6fe8ac	USER_MANAGEMENT:READ	ADMIN
019fe945-381f-7293-afe8-581432a1040f	USER_MANAGEMENT:READ	USER
019fe945-381f-7293-afe8-582a7c49fa75	USER_MANAGEMENT:READ+CREATE	ADMIN
019fe945-381f-7293-afe8-583ded5316f1	USER_MANAGEMENT:READ+EDIT	ADMIN
019fe945-381f-7293-afe8-58421cbc45ba	USER_MANAGEMENT:READ+DELETE	ADMIN
019fe945-381f-7293-afe8-5859d8977d84	MODEL:READ	ADMIN
019fe945-381f-7293-afe8-586cce0c170e	MODEL:READ	USER
019fe945-381f-7293-afe8-58751b56e740	MODEL:READ	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5881e6731118	MODEL:READ+CREATE	ADMIN
019fe945-381f-7293-afe8-589765277727	MODEL:READ+CREATE	USER
019fe945-381f-7293-afe8-58acea57df93	MODEL:READ+CREATE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-58b2628f980c	MODEL:READ+EDIT	ADMIN
019fe945-381f-7293-afe8-58c51ec6aacb	MODEL:READ+EDIT	USER
019fe945-381f-7293-afe8-58d98bb393db	MODEL:READ+EDIT	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-58e9d5fa1b41	MODEL:READ+DELETE	ADMIN
019fe945-381f-7293-afe8-58fb72fae1a9	MODEL:READ+DELETE	USER
019fe945-381f-7293-afe8-5900bef68497	MODEL:READ+DELETE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-591887fae341	MODEL:READ+AUTH	ADMIN
019fe945-381f-7293-afe8-592c08c87cdb	MODEL:READ+AUTH	USER
019fe945-381f-7293-afe8-5931c72e31f5	MODEL:READ+AUTH	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-594b8a0f9b54	MODEL:READ+RELATE_VIEW	ADMIN
019fe945-381f-7293-afe8-595e8a658c2d	MODEL:READ+RELATE_VIEW	USER
019fe945-381f-7293-afe8-596ce1b7d89a	MODEL:READ+RELATE_VIEW	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5978c55ddbb3	TRIGGER:READ	ADMIN
019fe945-381f-7293-afe8-5989a5ffe77f	TRIGGER:READ	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-599b7f04a332	TRIGGER:READ+CREATE	ADMIN
019fe945-381f-7293-afe8-59a8ef609ae6	TRIGGER:READ+CREATE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-59bc67e005ec	TRIGGER:READ+EDIT	ADMIN
019fe945-381f-7293-afe8-59c690f4d27e	TRIGGER:READ+EDIT	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-59ddec320c0d	TRIGGER:READ+DELETE	ADMIN
019fe945-381f-7293-afe8-59ef99972eda	TRIGGER:READ+DELETE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-59fbb3ff5de7	TRIGGER:READ+RECORD	ADMIN
019fe945-381f-7293-afe8-5a00d1682b6c	TRIGGER:READ+RECORD	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5a125f9abe4c	TOOL:READ	ADMIN
019fe945-381f-7293-afe8-5a2f656f6476	TOOL:READ	USER
019fe945-381f-7293-afe8-5a3d96a5c340	TOOL:READ	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5a4c8bd96a2b	TOOL:READ+CREATE	ADMIN
019fe945-381f-7293-afe8-5a5567afa909	TOOL:READ+CREATE	USER
019fe945-381f-7293-afe8-5a6cc7eab939	TOOL:READ+CREATE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5a7f119fd43c	TOOL:READ+BATCH_MOVE	ADMIN
019fe945-381f-7293-afe8-5a8170be273b	TOOL:READ+BATCH_MOVE	USER
019fe945-381f-7293-afe8-5a9e3b25ec8e	TOOL:READ+BATCH_MOVE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5aabb11fbd2d	TOOL:READ+BATCH_DELETE	ADMIN
019fe945-381f-7293-afe8-5ab52c6587df	TOOL:READ+BATCH_DELETE	USER
019fe945-381f-7293-afe8-5acc0f2c2d90	TOOL:READ+BATCH_DELETE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5adc3b13387e	TOOL:READ+EDIT	ADMIN
019fe945-381f-7293-afe8-5ae7428911fb	TOOL:READ+EDIT	USER
019fe945-381f-7293-afe8-5afd8aeac4de	TOOL:READ+EDIT	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5b048878e288	TOOL:READ+DELETE	ADMIN
019fe945-381f-7293-afe8-5b1de9a8f8e2	TOOL:READ+DELETE	USER
019fe945-381f-7293-afe8-5b27fbb56af4	TOOL:READ+DELETE	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5b30c43cbb8e	TOOL:READ+IMPORT	ADMIN
019fe945-381f-7293-afe8-5b4e4e955cef	TOOL:READ+IMPORT	USER
019fe945-381f-7293-afe8-5b525a4c9aa3	TOOL:READ+IMPORT	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5b6ef74f41e8	TOOL:READ+EXPORT	ADMIN
019fe945-381f-7293-afe8-5b7be247eab0	TOOL:READ+EXPORT	USER
019fe945-381f-7293-afe8-5b8f92a04f8d	TOOL:READ+EXPORT	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5b980d0cc27b	TOOL:READ+AUTH	ADMIN
019fe945-381f-7293-afe8-5ba8c49423af	TOOL:READ+AUTH	USER
019fe945-381f-7293-afe8-5bb2f5c2ccd7	TOOL:READ+AUTH	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5bc3f04c5897	TOOL:READ+RELATE_VIEW	ADMIN
019fe945-381f-7293-afe8-5bda1c88a20c	TOOL:READ+RELATE_VIEW	USER
019fe945-381f-7293-afe8-5be750bb1825	TOOL:READ+RELATE_VIEW	WORKSPACE_MANAGE
019fe945-381f-7293-afe8-5bfb7701c63e	TOOL:READ+PUBLISH	ADMIN
019fe945-381f-7293-afe8-5c07096c65b1	TOOL:READ+PUBLISH	USER
019fe945-3820-75b0-856b-0ef3a3adb281	TOOL:READ+PUBLISH	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-0f055b5194a5	TOOL:READ+RECORD	ADMIN
019fe945-3820-75b0-856b-0f1d85262f35	TOOL:READ+RECORD	USER
019fe945-3820-75b0-856b-0f26fd1668b6	TOOL:READ+RECORD	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-0f350a85ab58	TOOL:READ+TRIGGER_READ	ADMIN
019fe945-3820-75b0-856b-0f4cde4530cc	TOOL:READ+TRIGGER_READ	USER
019fe945-3820-75b0-856b-0f58b1ab214a	TOOL:READ+TRIGGER_READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-0f64428baf51	TOOL:READ+TRIGGER_CREATE	ADMIN
019fe945-3820-75b0-856b-0f759c305c7b	TOOL:READ+TRIGGER_CREATE	USER
019fe945-3820-75b0-856b-0f8aa90e1540	TOOL:READ+TRIGGER_CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-0f998cd6561a	TOOL:READ+TRIGGER_EDIT	ADMIN
019fe945-3820-75b0-856b-0fae7fc56ae7	TOOL:READ+TRIGGER_EDIT	USER
019fe945-3820-75b0-856b-0fbe79765f9c	TOOL:READ+TRIGGER_EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-0fc3a0b4539f	TOOL:READ+TRIGGER_DELETE	ADMIN
019fe945-3820-75b0-856b-0fdfaefef7d7	TOOL:READ+TRIGGER_DELETE	USER
019fe945-3820-75b0-856b-0fe003a30ac0	TOOL:READ+TRIGGER_DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-0ff27402128e	TOOL_FOLDER:READ	ADMIN
019fe945-3820-75b0-856b-10000bc81483	TOOL_FOLDER:READ	USER
019fe945-3820-75b0-856b-1012711dbe9f	TOOL_FOLDER:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-102ce6d45f18	TOOL_FOLDER:READ+CREATE	USER
019fe945-3820-75b0-856b-103df8c825cb	TOOL_FOLDER:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1047edee2bc8	TOOL_FOLDER:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-10583b658658	TOOL_FOLDER:READ+EDIT	USER
019fe945-3820-75b0-856b-106e00bd20a1	TOOL_FOLDER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1072ad14aeed	TOOL_FOLDER:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-108f777fab3d	TOOL_FOLDER:READ+DELETE	USER
019fe945-3820-75b0-856b-10997a53c967	TOOL_FOLDER:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-10aee7780ea5	TOOL_FOLDER:READ+AUTH	ADMIN
019fe945-3820-75b0-856b-10bec2aef292	TOOL_FOLDER:READ+AUTH	USER
019fe945-3820-75b0-856b-10c60bded78f	TOOL_FOLDER:READ+AUTH	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-10d712641ca4	KNOWLEDGE:READ	ADMIN
019fe945-3820-75b0-856b-10e64715173a	KNOWLEDGE:READ	USER
019fe945-3820-75b0-856b-10fa2859a43c	KNOWLEDGE:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-110644e2b00c	KNOWLEDGE:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-111a68521247	KNOWLEDGE:READ+CREATE	USER
019fe945-3820-75b0-856b-1124d805662d	KNOWLEDGE:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-11312cda2b2b	KNOWLEDGE:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1149292eabf7	KNOWLEDGE:READ+EDIT	USER
019fe945-3820-75b0-856b-115baa553c0a	KNOWLEDGE:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-11642b94de85	KNOWLEDGE:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-117b565bcea8	KNOWLEDGE:READ+DELETE	USER
019fe945-3820-75b0-856b-1184040ec0d5	KNOWLEDGE:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-119593fc73de	KNOWLEDGE:READ+SYNC	ADMIN
019fe945-3820-75b0-856b-11a4efe72e69	KNOWLEDGE:READ+SYNC	USER
019fe945-3820-75b0-856b-11b1095ed233	KNOWLEDGE:READ+SYNC	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-11ca8865e030	KNOWLEDGE:READ+EXPORT	ADMIN
019fe945-3820-75b0-856b-11d5d30c0136	KNOWLEDGE:READ+EXPORT	USER
019fe945-3820-75b0-856b-11e4040ca7b7	KNOWLEDGE:READ+EXPORT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-11f95562ca90	KNOWLEDGE:READ+VECTOR	ADMIN
019fe945-3820-75b0-856b-120a7d5b4806	KNOWLEDGE:READ+VECTOR	USER
019fe945-3820-75b0-856b-1211a7a20aa4	KNOWLEDGE:READ+VECTOR	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-122f3f2164d2	KNOWLEDGE:READ+GENERATE	ADMIN
019fe945-3820-75b0-856b-1235afb46f27	KNOWLEDGE:READ+GENERATE	USER
019fe945-3820-75b0-856b-1249617423ba	KNOWLEDGE:READ+GENERATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1257ccead71b	KNOWLEDGE:READ+BATCH_DELETE	ADMIN
019fe945-3820-75b0-856b-126c8dbfeaff	KNOWLEDGE:READ+BATCH_DELETE	USER
019fe945-3820-75b0-856b-127310239142	KNOWLEDGE:READ+BATCH_DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-12843858b3b3	KNOWLEDGE:READ+BATCH_MOVE	ADMIN
019fe945-3820-75b0-856b-129e437cf398	KNOWLEDGE:READ+BATCH_MOVE	USER
019fe945-3820-75b0-856b-12a74a4084bf	KNOWLEDGE:READ+BATCH_MOVE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-12ba02961ebf	KNOWLEDGE:READ+AUTH	ADMIN
019fe945-3820-75b0-856b-12c86a6dc08e	KNOWLEDGE:READ+AUTH	USER
019fe945-3820-75b0-856b-12d8b45f5b76	KNOWLEDGE:READ+AUTH	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-12e04e9c1fbd	KNOWLEDGE:READ+RELATE_VIEW	ADMIN
019fe945-3820-75b0-856b-12f026005dfc	KNOWLEDGE:READ+RELATE_VIEW	USER
019fe945-3820-75b0-856b-1303aa26347b	KNOWLEDGE:READ+RELATE_VIEW	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1310f6c86ac2	KNOWLEDGE_FOLDER:READ	ADMIN
019fe945-3820-75b0-856b-1326c8f39aba	KNOWLEDGE_FOLDER:READ	USER
019fe945-3820-75b0-856b-1331a2e56c9d	KNOWLEDGE_FOLDER:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-1346726c9037	KNOWLEDGE_FOLDER:READ+CREATE	USER
019fe945-3820-75b0-856b-135e9d3688c4	KNOWLEDGE_FOLDER:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-136919a29636	KNOWLEDGE_FOLDER:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-137959420de5	KNOWLEDGE_FOLDER:READ+EDIT	USER
019fe945-3820-75b0-856b-1387b82318da	KNOWLEDGE_FOLDER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-13904d6e3aba	KNOWLEDGE_FOLDER:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-13a79c49ad6a	KNOWLEDGE_FOLDER:READ+DELETE	USER
019fe945-3820-75b0-856b-13b8836ea9d3	KNOWLEDGE_FOLDER:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-13c20e1b35be	KNOWLEDGE_FOLDER:READ+AUTH	ADMIN
019fe945-3820-75b0-856b-13d35a3920d3	KNOWLEDGE_FOLDER:READ+AUTH	USER
019fe945-3820-75b0-856b-13e59e80a3de	KNOWLEDGE_FOLDER:READ+AUTH	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-13f94c8b5842	KNOWLEDGE_WORKFLOW:READ	ADMIN
019fe945-3820-75b0-856b-1409e3977ab8	KNOWLEDGE_WORKFLOW:READ	USER
019fe945-3820-75b0-856b-141d0cf936eb	KNOWLEDGE_WORKFLOW:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-142daf918e43	KNOWLEDGE_WORKFLOW:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-143df885f2bc	KNOWLEDGE_WORKFLOW:READ+EDIT	USER
019fe945-3820-75b0-856b-14423c2de803	KNOWLEDGE_WORKFLOW:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-145ecac92d69	KNOWLEDGE_WORKFLOW:READ+EXPORT	ADMIN
019fe945-3820-75b0-856b-146f4a704567	KNOWLEDGE_WORKFLOW:READ+EXPORT	USER
019fe945-3820-75b0-856b-147a747a95f8	KNOWLEDGE_WORKFLOW:READ+EXPORT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1481a5a4ebba	KNOWLEDGE_WORKFLOW:READ+PUBLISH	ADMIN
019fe945-3820-75b0-856b-149d8ccc7c30	KNOWLEDGE_WORKFLOW:READ+PUBLISH	USER
019fe945-3820-75b0-856b-14a251ac3d64	KNOWLEDGE_WORKFLOW:READ+PUBLISH	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-14b350a60210	KNOWLEDGE_DOCUMENT:READ	ADMIN
019fe945-3820-75b0-856b-14c708d0a552	KNOWLEDGE_DOCUMENT:READ	USER
019fe945-3820-75b0-856b-14d7cded66d4	KNOWLEDGE_DOCUMENT:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-14e3697c77d6	KNOWLEDGE_DOCUMENT:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-14f85b16b724	KNOWLEDGE_DOCUMENT:READ+CREATE	USER
019fe945-3820-75b0-856b-15004116548f	KNOWLEDGE_DOCUMENT:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1516c2a01392	KNOWLEDGE_DOCUMENT:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-152f54bdc62f	KNOWLEDGE_DOCUMENT:READ+EDIT	USER
019fe945-3820-75b0-856b-1536bc78383b	KNOWLEDGE_DOCUMENT:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-15428557c5d1	KNOWLEDGE_DOCUMENT:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-1557e000bf2b	KNOWLEDGE_DOCUMENT:READ+DELETE	USER
019fe945-3820-75b0-856b-1566f9aa6248	KNOWLEDGE_DOCUMENT:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-157689b743cd	KNOWLEDGE_DOCUMENT:READ+SYNC	ADMIN
019fe945-3820-75b0-856b-1588f6db4432	KNOWLEDGE_DOCUMENT:READ+SYNC	USER
019fe945-3820-75b0-856b-15906f6d22ae	KNOWLEDGE_DOCUMENT:READ+SYNC	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-15a740232741	KNOWLEDGE_DOCUMENT:READ+EXPORT	ADMIN
019fe945-3820-75b0-856b-15bbb0c4888d	KNOWLEDGE_DOCUMENT:READ+EXPORT	USER
019fe945-3820-75b0-856b-15ce3f08f779	KNOWLEDGE_DOCUMENT:READ+EXPORT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-15dbf2903e7e	KNOWLEDGE_DOCUMENT:READ+DOWNLOAD	ADMIN
019fe945-3820-75b0-856b-15e00821513a	KNOWLEDGE_DOCUMENT:READ+DOWNLOAD	USER
019fe945-3820-75b0-856b-15f88f2c1658	KNOWLEDGE_DOCUMENT:READ+DOWNLOAD	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1603869b94c1	KNOWLEDGE_DOCUMENT:READ+GENERATE	ADMIN
019fe945-3820-75b0-856b-161a8c61844b	KNOWLEDGE_DOCUMENT:READ+GENERATE	USER
019fe945-3820-75b0-856b-1622e18060e8	KNOWLEDGE_DOCUMENT:READ+GENERATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1637384964bc	KNOWLEDGE_DOCUMENT:READ+VECTOR	ADMIN
019fe945-3820-75b0-856b-164d2c00cc05	KNOWLEDGE_DOCUMENT:READ+VECTOR	USER
019fe945-3820-75b0-856b-16531cca035f	KNOWLEDGE_DOCUMENT:READ+VECTOR	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-16608232350e	KNOWLEDGE_DOCUMENT:READ+MIGRATE	ADMIN
019fe945-3820-75b0-856b-167d79c3deca	KNOWLEDGE_DOCUMENT:READ+MIGRATE	USER
019fe945-3820-75b0-856b-168e7782ed02	KNOWLEDGE_DOCUMENT:READ+MIGRATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1691bf7190c6	KNOWLEDGE_DOCUMENT:READ+TAG	ADMIN
019fe945-3820-75b0-856b-16a2544758ee	KNOWLEDGE_DOCUMENT:READ+TAG	USER
019fe945-3820-75b0-856b-16b2444a8fa7	KNOWLEDGE_DOCUMENT:READ+TAG	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-16c5f9808ec0	KNOWLEDGE_DOCUMENT:READ+REPLACE	ADMIN
019fe945-3820-75b0-856b-16df360c64c6	KNOWLEDGE_DOCUMENT:READ+REPLACE	USER
019fe945-3820-75b0-856b-16ec99279852	KNOWLEDGE_DOCUMENT:READ+REPLACE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-16f975537c32	KNOWLEDGE_DOCUMENT:READ+TOKEN	ADMIN
019fe945-3820-75b0-856b-170eb70d4c51	KNOWLEDGE_DOCUMENT:READ+TOKEN	USER
019fe945-3820-75b0-856b-171fcdf9856b	KNOWLEDGE_DOCUMENT:READ+TOKEN	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-172afe7022a6	KNOWLEDGE_HIT_TEST:READ	ADMIN
019fe945-3820-75b0-856b-17357a7f00c7	KNOWLEDGE_HIT_TEST:READ	USER
019fe945-3820-75b0-856b-17418aa977b6	KNOWLEDGE_HIT_TEST:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-175c0750b6d8	KNOWLEDGE_PROBLEM:READ	ADMIN
019fe945-3820-75b0-856b-176aed7fe4c5	KNOWLEDGE_PROBLEM:READ	USER
019fe945-3820-75b0-856b-177f8e0a9ac0	KNOWLEDGE_PROBLEM:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-178c472847a0	KNOWLEDGE_PROBLEM:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-17945d892511	KNOWLEDGE_PROBLEM:READ+CREATE	USER
019fe945-3820-75b0-856b-17a04611ae00	KNOWLEDGE_PROBLEM:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-17b88aae9630	KNOWLEDGE_PROBLEM:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-17c5c28a3631	KNOWLEDGE_PROBLEM:READ+EDIT	USER
019fe945-3820-75b0-856b-17d0a306fe3b	KNOWLEDGE_PROBLEM:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-17ee25a2d3d4	KNOWLEDGE_PROBLEM:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-17f545685862	KNOWLEDGE_PROBLEM:READ+DELETE	USER
019fe945-3820-75b0-856b-1809234487fb	KNOWLEDGE_PROBLEM:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-18109538e2ae	KNOWLEDGE_PROBLEM:READ+RELATE	ADMIN
019fe945-3820-75b0-856b-182ff3144e70	KNOWLEDGE_PROBLEM:READ+RELATE	USER
019fe945-3820-75b0-856b-1837e1210c71	KNOWLEDGE_PROBLEM:READ+RELATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-18434e442fe9	KNOWLEDGE_TERMBASE:READ	ADMIN
019fe945-3820-75b0-856b-185641af5834	KNOWLEDGE_TERMBASE:READ	USER
019fe945-3820-75b0-856b-18624f59a718	KNOWLEDGE_TERMBASE:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-18753e259828	KNOWLEDGE_TERMBASE:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-18803e5d3800	KNOWLEDGE_TERMBASE:READ+CREATE	USER
019fe945-3820-75b0-856b-18926e9ee229	KNOWLEDGE_TERMBASE:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-18adff817378	KNOWLEDGE_TERMBASE:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-18b823883798	KNOWLEDGE_TERMBASE:READ+EDIT	USER
019fe945-3820-75b0-856b-18c068b9e032	KNOWLEDGE_TERMBASE:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-18dc9a272f9f	KNOWLEDGE_TERMBASE:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-18e779249ffd	KNOWLEDGE_TERMBASE:READ+DELETE	USER
019fe945-3820-75b0-856b-18f0d661bd4c	KNOWLEDGE_TERMBASE:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1900562bff26	KNOWLEDGE_TAG:READ	ADMIN
019fe945-3820-75b0-856b-191d1b3ca181	KNOWLEDGE_TAG:READ	USER
019fe945-3820-75b0-856b-192951a82b60	KNOWLEDGE_TAG:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1933b2d94035	KNOWLEDGE_TAG:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-194060ce7ca7	KNOWLEDGE_TAG:READ+CREATE	USER
019fe945-3820-75b0-856b-195def5ebd18	KNOWLEDGE_TAG:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-196dcee9dd11	KNOWLEDGE_TAG:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1972b6e021a7	KNOWLEDGE_TAG:READ+EDIT	USER
019fe945-3820-75b0-856b-198c1b626964	KNOWLEDGE_TAG:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-199a882ee51a	KNOWLEDGE_TAG:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-19acabdda489	KNOWLEDGE_TAG:READ+DELETE	USER
019fe945-3820-75b0-856b-19b107112cb2	KNOWLEDGE_TAG:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-19cd3e00ef91	APPLICATION_WORKSPACE_USER_RESOURCE_PERMISSION:READ	ADMIN
019fe945-3820-75b0-856b-19d125d49216	APPLICATION_WORKSPACE_USER_RESOURCE_PERMISSION:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-19fb12da1a02	APPLICATION_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1a0512e9e4bd	APPLICATION_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1a2c3148fa1b	KNOWLEDGE_WORKSPACE_USER_RESOURCE_PERMISSION:READ	ADMIN
019fe945-3820-75b0-856b-1a32b806bbe8	KNOWLEDGE_WORKSPACE_USER_RESOURCE_PERMISSION:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1a544ebf5fca	KNOWLEDGE_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1a6b328eade1	KNOWLEDGE_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1a8fe15faca1	TOOL_WORKSPACE_USER_RESOURCE_PERMISSION:READ	ADMIN
019fe945-3820-75b0-856b-1a9c5c53d569	TOOL_WORKSPACE_USER_RESOURCE_PERMISSION:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1ab11352d5de	TOOL_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1ac8fe9d7524	TOOL_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1ae8a463e737	MODEL_WORKSPACE_USER_RESOURCE_PERMISSION:READ	ADMIN
019fe945-3820-75b0-856b-1afe330a0431	MODEL_WORKSPACE_USER_RESOURCE_PERMISSION:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1b18efd50b9a	MODEL_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1b200cf6b65a	MODEL_WORKSPACE_USER_RESOURCE_PERMISSION:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1b49120206f0	EMAIL_SETTING:READ	ADMIN
019fe945-3820-75b0-856b-1b5fcbdae368	EMAIL_SETTING:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1b636b838e16	ROLE:READ	ADMIN
019fe945-3820-75b0-856b-1b76c188fc83	ROLE:READ	USER
019fe945-3820-75b0-856b-1b83d11cfca2	ROLE:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-1b9740d304d8	ROLE:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1baaf8a151ea	ROLE:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-1bb92db17378	ROLE:READ+ADD_MEMBER	ADMIN
019fe945-3820-75b0-856b-1bc1f200981e	ROLE:READ+REMOVE_MEMBER	ADMIN
019fe945-3820-75b0-856b-1bdaff1140e9	WORKSPACE_ROLE:READ	ADMIN
019fe945-3820-75b0-856b-1bee3ab18963	WORKSPACE_ROLE:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1bf7f7700ad9	WORKSPACE_ROLE:READ+ADD_MEMBER	ADMIN
019fe945-3820-75b0-856b-1c049b4860a3	WORKSPACE_ROLE:READ+ADD_MEMBER	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1c1dda389f72	WORKSPACE_ROLE:READ+REMOVE_MEMBER	ADMIN
019fe945-3820-75b0-856b-1c23bf83ac2f	WORKSPACE_ROLE:READ+REMOVE_MEMBER	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1c31101b1417	WORKSPACE:READ	ADMIN
019fe945-3820-75b0-856b-1c452fe9bc46	WORKSPACE:READ	USER
019fe945-3820-75b0-856b-1c58a2f3cd6d	WORKSPACE:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-1c66593ce90e	WORKSPACE:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1c79b51a6641	WORKSPACE:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-1c8a4d8f2ce8	WORKSPACE:READ+ADD_MEMBER	ADMIN
019fe945-3820-75b0-856b-1c9a710423cd	WORKSPACE:READ+REMOVE_MEMBER	ADMIN
019fe945-3820-75b0-856b-1ca4fa39c073	WORKSPACE_WORKSPACE:READ	ADMIN
019fe945-3820-75b0-856b-1cbae967c95e	WORKSPACE_WORKSPACE:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1cc4579f32e6	WORKSPACE_WORKSPACE:READ+ADD_MEMBER	ADMIN
019fe945-3820-75b0-856b-1cd72db1ac70	WORKSPACE_WORKSPACE:READ+ADD_MEMBER	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1ce2120250c2	WORKSPACE_WORKSPACE:READ+REMOVE_MEMBER	ADMIN
019fe945-3820-75b0-856b-1cf5a7b8901c	WORKSPACE_WORKSPACE:READ+REMOVE_MEMBER	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1d00d3621454	LOGIN_AUTH:READ	ADMIN
019fe945-3820-75b0-856b-1d1b68033d63	LOGIN_AUTH:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1d2ee9cad8f5	APPLICATION:READ	ADMIN
019fe945-3820-75b0-856b-1d3c22f8a83a	APPLICATION:READ	USER
019fe945-3820-75b0-856b-1d4f4ed4e724	APPLICATION:READ	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1d53f0d2e3e5	APPLICATION:READ+CREATE	ADMIN
019fe945-3820-75b0-856b-1d608aed6e10	APPLICATION:READ+CREATE	USER
019fe945-3820-75b0-856b-1d752125ed1f	APPLICATION:READ+CREATE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1d860463d8ac	APPLICATION:READ+COPY	ADMIN
019fe945-3820-75b0-856b-1d9a63d74477	APPLICATION:READ+COPY	USER
019fe945-3820-75b0-856b-1da8f98f7123	APPLICATION:READ+COPY	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1db5fe46c779	APPLICATION:READ+EDIT	ADMIN
019fe945-3820-75b0-856b-1dc3c1a183dd	APPLICATION:READ+EDIT	USER
019fe945-3820-75b0-856b-1dd94cc64a92	APPLICATION:READ+EDIT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1dead626e602	APPLICATION:READ+DELETE	ADMIN
019fe945-3820-75b0-856b-1df6a3c9a923	APPLICATION:READ+DELETE	USER
019fe945-3820-75b0-856b-1e0881958cf6	APPLICATION:READ+DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1e10b55e57f0	APPLICATION:READ+IMPORT	ADMIN
019fe945-3820-75b0-856b-1e291133dc17	APPLICATION:READ+IMPORT	USER
019fe945-3820-75b0-856b-1e3eca04320c	APPLICATION:READ+IMPORT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1e4c113dffdc	APPLICATION:READ+EXPORT	ADMIN
019fe945-3820-75b0-856b-1e59276453ad	APPLICATION:READ+EXPORT	USER
019fe945-3820-75b0-856b-1e6aca563bb8	APPLICATION:READ+EXPORT	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1e7831978226	APPLICATION:READ+PUBLISH	ADMIN
019fe945-3820-75b0-856b-1e8a476d17a8	APPLICATION:READ+PUBLISH	USER
019fe945-3820-75b0-856b-1e95595b284b	APPLICATION:READ+PUBLISH	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1ea04ea7b890	APPLICATION:READ+BATCH_DELETE	ADMIN
019fe945-3820-75b0-856b-1eb96a805a7c	APPLICATION:READ+BATCH_DELETE	USER
019fe945-3820-75b0-856b-1ec6b50a0245	APPLICATION:READ+BATCH_DELETE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1edf4167e04b	APPLICATION:READ+BATCH_MOVE	ADMIN
019fe945-3820-75b0-856b-1ee401a5c705	APPLICATION:READ+BATCH_MOVE	USER
019fe945-3820-75b0-856b-1efa31256fd1	APPLICATION:READ+BATCH_MOVE	WORKSPACE_MANAGE
019fe945-3820-75b0-856b-1f01082051c0	APPLICATION:READ+AUTH	ADMIN
019fe945-3821-7093-949d-bdcf9dc139d9	APPLICATION:READ+AUTH	USER
019fe945-3821-7093-949d-bddb0a1c9e19	APPLICATION:READ+AUTH	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bdee80038469	APPLICATION:READ+RELATE_VIEW	ADMIN
019fe945-3821-7093-949d-bdfdfa274fa1	APPLICATION:READ+RELATE_VIEW	USER
019fe945-3821-7093-949d-be0523f534f9	APPLICATION:READ+RELATE_VIEW	WORKSPACE_MANAGE
019fe945-3821-7093-949d-be1c7cb8a13f	APPLICATION:READ+TRIGGER_READ	ADMIN
019fe945-3821-7093-949d-be23fa93cb75	APPLICATION:READ+TRIGGER_READ	USER
019fe945-3821-7093-949d-be3266ccfc76	APPLICATION:READ+TRIGGER_READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-be447f7ced54	APPLICATION:READ+TRIGGER_CREATE	ADMIN
019fe945-3821-7093-949d-be5c53d51065	APPLICATION:READ+TRIGGER_CREATE	USER
019fe945-3821-7093-949d-be65ad3c3615	APPLICATION:READ+TRIGGER_CREATE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-be7bf4e140b1	APPLICATION:READ+TRIGGER_EDIT	ADMIN
019fe945-3821-7093-949d-be8b5f3bb847	APPLICATION:READ+TRIGGER_EDIT	USER
019fe945-3821-7093-949d-be99ff6a87e7	APPLICATION:READ+TRIGGER_EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bea8f7f8d157	APPLICATION:READ+TRIGGER_DELETE	ADMIN
019fe945-3821-7093-949d-beb5db106137	APPLICATION:READ+TRIGGER_DELETE	USER
019fe945-3821-7093-949d-bec104dce57d	APPLICATION:READ+TRIGGER_DELETE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bed918f150af	APPLICATION_FOLDER:READ	ADMIN
019fe945-3821-7093-949d-beeab28792ba	APPLICATION_FOLDER:READ	USER
019fe945-3821-7093-949d-bef5742d4dda	APPLICATION_FOLDER:READ+CREATE	ADMIN
019fe945-3821-7093-949d-bf0972634504	APPLICATION_FOLDER:READ+CREATE	USER
019fe945-3821-7093-949d-bf1f2360d554	APPLICATION_FOLDER:READ+CREATE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bf212cfb643a	APPLICATION_FOLDER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-bf3ac78bc338	APPLICATION_FOLDER:READ+EDIT	USER
019fe945-3821-7093-949d-bf4304c4e041	APPLICATION_FOLDER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bf5b6c3e53df	APPLICATION_FOLDER:READ+DELETE	ADMIN
019fe945-3821-7093-949d-bf68d83fbbab	APPLICATION_FOLDER:READ+DELETE	USER
019fe945-3821-7093-949d-bf7f43b30eca	APPLICATION_FOLDER:READ+DELETE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bf86978da0a6	APPLICATION_FOLDER:READ+AUTH	ADMIN
019fe945-3821-7093-949d-bf94b7445063	APPLICATION_FOLDER:READ+AUTH	USER
019fe945-3821-7093-949d-bfaa08d344bf	APPLICATION_FOLDER:READ+AUTH	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bfb6412e95ab	APPLICATION_OVERVIEW:READ	ADMIN
019fe945-3821-7093-949d-bfc48dd62977	APPLICATION_OVERVIEW:READ	USER
019fe945-3821-7093-949d-bfd0ef210466	APPLICATION_OVERVIEW:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-bfe7328497de	APPLICATION_OVERVIEW:READ+EMBED	ADMIN
019fe945-3821-7093-949d-bff36e8a117e	APPLICATION_OVERVIEW:READ+EMBED	USER
019fe945-3821-7093-949d-c0009f434474	APPLICATION_OVERVIEW:READ+EMBED	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c013034bbbee	APPLICATION_OVERVIEW:READ+ACCESS	ADMIN
019fe945-3821-7093-949d-c0243e10baaf	APPLICATION_OVERVIEW:READ+ACCESS	USER
019fe945-3821-7093-949d-c03965dccdd1	APPLICATION_OVERVIEW:READ+ACCESS	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c04a07aeabe6	APPLICATION_OVERVIEW:READ+DISPLAY	ADMIN
019fe945-3821-7093-949d-c052c23cec28	APPLICATION_OVERVIEW:READ+DISPLAY	USER
019fe945-3821-7093-949d-c06e1c484fb4	APPLICATION_OVERVIEW:READ+DISPLAY	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c07f07ba8ccb	APPLICATION_OVERVIEW:READ+API_KEY	ADMIN
019fe945-3821-7093-949d-c08843b9bf33	APPLICATION_OVERVIEW:READ+API_KEY	USER
019fe945-3821-7093-949d-c09ac690101b	APPLICATION_OVERVIEW:READ+API_KEY	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c0ad9f6f3966	APPLICATION_OVERVIEW:READ+PUBLIC_ACCESS	ADMIN
019fe945-3821-7093-949d-c0b68a910363	APPLICATION_OVERVIEW:READ+PUBLIC_ACCESS	USER
019fe945-3821-7093-949d-c0cc7af965de	APPLICATION_OVERVIEW:READ+PUBLIC_ACCESS	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c0d28a47cec0	APPLICATION_ACCESS:READ	ADMIN
019fe945-3821-7093-949d-c0e3ea6b377f	APPLICATION_ACCESS:READ	USER
019fe945-3821-7093-949d-c0f6ae762873	APPLICATION_ACCESS:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c10a8ce08a94	APPLICATION_ACCESS:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c11749208f33	APPLICATION_ACCESS:READ+EDIT	USER
019fe945-3821-7093-949d-c1233b22ec39	APPLICATION_ACCESS:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c13f358dd610	APPLICATION_CHAT_USER:READ	ADMIN
019fe945-3821-7093-949d-c143c89be4b3	APPLICATION_CHAT_USER:READ	USER
019fe945-3821-7093-949d-c151748edc07	APPLICATION_CHAT_USER:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c16eca1d6886	APPLICATION_CHAT_USER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c170c8f9e756	APPLICATION_CHAT_USER:READ+EDIT	USER
019fe945-3821-7093-949d-c18e1ade6d8e	APPLICATION_CHAT_USER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c19b218ed793	KNOWLEDGE_CHAT_USER:READ	ADMIN
019fe945-3821-7093-949d-c1afe44ceb4e	KNOWLEDGE_CHAT_USER:READ	USER
019fe945-3821-7093-949d-c1b8f720ec83	KNOWLEDGE_CHAT_USER:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c1cc8029315f	KNOWLEDGE_CHAT_USER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c1d35bbc3cb8	KNOWLEDGE_CHAT_USER:READ+EDIT	USER
019fe945-3821-7093-949d-c1efbf43aa9b	KNOWLEDGE_CHAT_USER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c1f9dc1dad6a	APPLICATION_CHAT_LOG:READ	ADMIN
019fe945-3821-7093-949d-c20f594fd80e	APPLICATION_CHAT_LOG:READ	USER
019fe945-3821-7093-949d-c21bc67dc943	APPLICATION_CHAT_LOG:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c2265a974502	APPLICATION_CHAT_LOG:READ+ANNOTATION	ADMIN
019fe945-3821-7093-949d-c23a394600ca	APPLICATION_CHAT_LOG:READ+ANNOTATION	USER
019fe945-3821-7093-949d-c2495f4d9ab7	APPLICATION_CHAT_LOG:READ+ANNOTATION	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c254826e6974	APPLICATION_CHAT_LOG:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-c2694368aacf	APPLICATION_CHAT_LOG:READ+EXPORT	USER
019fe945-3821-7093-949d-c2790817c061	APPLICATION_CHAT_LOG:READ+EXPORT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c284e6ccddcf	APPLICATION_CHAT_LOG:READ+CLEAR_POLICY	ADMIN
019fe945-3821-7093-949d-c291c4c3278e	APPLICATION_CHAT_LOG:READ+CLEAR_POLICY	USER
019fe945-3821-7093-949d-c2a8312f3480	APPLICATION_CHAT_LOG:READ+CLEAR_POLICY	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c2bd7098dec1	APPLICATION_CHAT_LOG:READ+ADD_KNOWLEDGE	ADMIN
019fe945-3821-7093-949d-c2c5df5cef03	APPLICATION_CHAT_LOG:READ+ADD_KNOWLEDGE	USER
019fe945-3821-7093-949d-c2dd417fe25d	APPLICATION_CHAT_LOG:READ+ADD_KNOWLEDGE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c2e23143c56a	OTHER:READ	ADMIN
019fe945-3821-7093-949d-c2f99209e20d	OTHER:READ	USER
019fe945-3821-7093-949d-c3042b4f736d	OTHER:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c314ef63dd36	OTHER:READ+UPDATE	ADMIN
019fe945-3821-7093-949d-c32bcea19914	OTHER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c33387ed80df	OTHER:READ+EDIT	USER
019fe945-3821-7093-949d-c3462145f570	OTHER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c357b810f68e	OTHER:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c36aefce5635	OTHER:READ+CREATE	USER
019fe945-3821-7093-949d-c370977b6638	OTHER:READ+CREATE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c38d22b9f5c0	OTHER:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c39edf66b345	OTHER:READ+DELETE	USER
019fe945-3821-7093-949d-c3aba9b2d8e8	OTHER:READ+DELETE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c3b7c57cf558	APPEARANCE_SETTINGS:READ	ADMIN
019fe945-3821-7093-949d-c3c0719655a0	APPEARANCE_SETTINGS:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c3de4ae66897	CHAT_USER:READ	ADMIN
019fe945-3821-7093-949d-c3ef32522d24	CHAT_USER:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c3f862d04edd	CHAT_USER:READ+SYNC	ADMIN
019fe945-3821-7093-949d-c40a8cad9cd4	CHAT_USER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c4137685737c	CHAT_USER:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c421be18f2ca	CHAT_USER:READ+USER_GROUP	ADMIN
019fe945-3821-7093-949d-c434a0260f32	USER_GROUP:READ	ADMIN
019fe945-3821-7093-949d-c44c0f6dcb9e	USER_GROUP:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c4541d909634	USER_GROUP:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c46c62485590	USER_GROUP:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c479721be6c3	USER_GROUP:READ+ADD_MEMBER	ADMIN
019fe945-3821-7093-949d-c4869193aa52	USER_GROUP:READ+REMOVE_MEMBER	ADMIN
019fe945-3821-7093-949d-c4973c1a30f5	CHAT_USER_AUTH:READ	ADMIN
019fe945-3821-7093-949d-c4a8b49b948e	CHAT_USER_AUTH:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c4be9de3f5d4	WORKSPACE_CHAT_USER:READ	ADMIN
019fe945-3821-7093-949d-c4cd5c7d3f99	WORKSPACE_CHAT_USER:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c4d4913458fb	WORKSPACE_CHAT_USER:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c4ee449a576a	WORKSPACE_CHAT_USER:READ+CREATE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c4fc545e3944	WORKSPACE_CHAT_USER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c5066749656f	WORKSPACE_CHAT_USER:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c517130f4ec8	WORKSPACE_CHAT_USER:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c52cd01f18a6	WORKSPACE_CHAT_USER:READ+DELETE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c5346f45b850	WORKSPACE_CHAT_USER:READ+USER_GROUP	ADMIN
019fe945-3821-7093-949d-c54fd30dcee2	WORKSPACE_CHAT_USER:READ+USER_GROUP	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c55647b66de8	WORKSPACE_USER_GROUP:READ	ADMIN
019fe945-3821-7093-949d-c5688f5eb124	WORKSPACE_USER_GROUP:READ	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c57e111b311d	WORKSPACE_USER_GROUP:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c58eb379de7d	WORKSPACE_USER_GROUP:READ+CREATE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c598f9fb3ad4	WORKSPACE_USER_GROUP:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c5a0c1e7bc0a	WORKSPACE_USER_GROUP:READ+EDIT	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c5bc5cee8fb7	WORKSPACE_USER_GROUP:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c5caef022ca5	WORKSPACE_USER_GROUP:READ+DELETE	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c5d4df93967e	WORKSPACE_USER_GROUP:READ+ADD_MEMBER	ADMIN
019fe945-3821-7093-949d-c5e0dfc84def	WORKSPACE_USER_GROUP:READ+ADD_MEMBER	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c5f35835c218	WORKSPACE_USER_GROUP:READ+REMOVE_MEMBER	ADMIN
019fe945-3821-7093-949d-c6071a1dcecb	WORKSPACE_USER_GROUP:READ+REMOVE_MEMBER	WORKSPACE_MANAGE
019fe945-3821-7093-949d-c61837db47f6	SYSTEM_TOOL:READ	ADMIN
019fe945-3821-7093-949d-c627cfb8c10e	SYSTEM_TOOL:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c63590599d6b	SYSTEM_TOOL:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c645bb65e2e1	SYSTEM_TOOL:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c652f5bdd78f	SYSTEM_TOOL:READ+IMPORT	ADMIN
019fe945-3821-7093-949d-c664b219c41b	SYSTEM_TOOL:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-c67116d24461	SYSTEM_TOOL:READ+PUBLISH	ADMIN
019fe945-3821-7093-949d-c68c2508ce92	SYSTEM_TOOL:READ+RELATE_VIEW	ADMIN
019fe945-3821-7093-949d-c69d3afe8257	SYSTEM_TOOL:READ+RECORD	ADMIN
019fe945-3821-7093-949d-c6a0c3406e51	SYSTEM_TOOL:READ+TO_WORKSPACE	ADMIN
019fe945-3821-7093-949d-c6bd62c78c43	SYSTEM_KNOWLEDGE:READ	ADMIN
019fe945-3821-7093-949d-c6c506a53a0a	SYSTEM_KNOWLEDGE:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c6d7cb1b4f75	SYSTEM_KNOWLEDGE:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c6e9125bd844	SYSTEM_KNOWLEDGE:READ+SYNC	ADMIN
019fe945-3821-7093-949d-c6fe2549d77a	SYSTEM_KNOWLEDGE:READ+VECTOR	ADMIN
019fe945-3821-7093-949d-c707cf908da3	SYSTEM_KNOWLEDGE:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-c71799856401	SYSTEM_KNOWLEDGE:READ+GENERATE	ADMIN
019fe945-3821-7093-949d-c72964bb7d78	SYSTEM_KNOWLEDGE:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c7365733d57f	SYSTEM_KNOWLEDGE:READ+RELATE_VIEW	ADMIN
019fe945-3821-7093-949d-c74adbb1c792	SYSTEM_KNOWLEDGE:READ+TO_WORKSPACE	ADMIN
019fe945-3821-7093-949d-c75c772d26f8	SYSTEM_KNOWLEDGE_WORKFLOW:READ	ADMIN
019fe945-3821-7093-949d-c764d46e6cfe	SYSTEM_KNOWLEDGE_WORKFLOW:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c77c26e9afe9	SYSTEM_KNOWLEDGE_WORKFLOW:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-c78ee7a19569	SYSTEM_KNOWLEDGE_WORKFLOW:READ+PUBLISH	ADMIN
019fe945-3821-7093-949d-c79c3fef1f75	SYSTEM_KNOWLEDGE_DOCUMENT:READ	ADMIN
019fe945-3821-7093-949d-c7a95f854afe	SYSTEM_KNOWLEDGE_DOCUMENT:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c7b53c761a6e	SYSTEM_KNOWLEDGE_DOCUMENT:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c7c7ed90f62f	SYSTEM_KNOWLEDGE_DOCUMENT:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c7de1a94cc40	SYSTEM_KNOWLEDGE_DOCUMENT:READ+SYNC	ADMIN
019fe945-3821-7093-949d-c7e1212c9e03	SYSTEM_KNOWLEDGE_DOCUMENT:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-c7ff8bd22484	SYSTEM_KNOWLEDGE_DOCUMENT:READ+DOWNLOAD	ADMIN
019fe945-3821-7093-949d-c80f943f9c57	SYSTEM_KNOWLEDGE_DOCUMENT:READ+GENERATE	ADMIN
019fe945-3821-7093-949d-c816031187a4	SYSTEM_KNOWLEDGE_DOCUMENT:READ+VECTOR	ADMIN
019fe945-3821-7093-949d-c82d55060c21	SYSTEM_KNOWLEDGE_DOCUMENT:READ+MIGRATE	ADMIN
019fe945-3821-7093-949d-c8313ca9cdb7	SYSTEM_KNOWLEDGE_DOCUMENT:READ+TAG	ADMIN
019fe945-3821-7093-949d-c84087cea84f	SYSTEM_KNOWLEDGE_DOCUMENT:READ+REPLACE	ADMIN
019fe945-3821-7093-949d-c8592c4dc011	SYSTEM_KNOWLEDGE_DOCUMENT:READ+TOKEN	ADMIN
019fe945-3821-7093-949d-c860a7815805	SYSTEM_KNOWLEDGE_TAG:READ	ADMIN
019fe945-3821-7093-949d-c87cf52665cb	SYSTEM_KNOWLEDGE_TAG:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c88e7c9e1fdc	SYSTEM_KNOWLEDGE_TAG:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c8905d32f742	SYSTEM_KNOWLEDGE_TAG:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c8af0d88a071	SYSTEM_KNOWLEDGE_PROBLEM:READ	ADMIN
019fe945-3821-7093-949d-c8b035f75790	SYSTEM_KNOWLEDGE_PROBLEM:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c8c90314ea95	SYSTEM_KNOWLEDGE_PROBLEM:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c8d62a856db9	SYSTEM_KNOWLEDGE_PROBLEM:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c8eaeeb00e97	SYSTEM_KNOWLEDGE_PROBLEM:READ+RELATE	ADMIN
019fe945-3821-7093-949d-c8f421af75d4	SYSTEM_KNOWLEDGE_TERMBASE:READ	ADMIN
019fe945-3821-7093-949d-c90d9c8c5ac6	SYSTEM_KNOWLEDGE_TERMBASE:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c91f2c39d392	SYSTEM_KNOWLEDGE_TERMBASE:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c92338f8ed10	SYSTEM_KNOWLEDGE_TERMBASE:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c933cb6fa880	SYSTEM_KNOWLEDGE_TERMBASE:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-c94f9c013d21	SYSTEM_KNOWLEDGE_HIT_TEST:READ	ADMIN
019fe945-3821-7093-949d-c957e269dee5	SYSTEM_KNOWLEDGE_CHAT_USER:READ	ADMIN
019fe945-3821-7093-949d-c96eca2d53ec	SYSTEM_KNOWLEDGE_CHAT_USER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c9786a97b7ac	SYSTEM_MODEL:READ	ADMIN
019fe945-3821-7093-949d-c989ace7e0ae	SYSTEM_MODEL:READ+CREATE	ADMIN
019fe945-3821-7093-949d-c992a752280d	SYSTEM_MODEL:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c9a9a08b6cfb	SYSTEM_MODEL:READ+DELETE	ADMIN
019fe945-3821-7093-949d-c9b5417a9628	SYSTEM_MODEL:READ+RELATE_VIEW	ADMIN
019fe945-3821-7093-949d-c9c69310deb5	SYSTEM_MODEL:READ+TO_WORKSPACE	ADMIN
019fe945-3821-7093-949d-c9de0e036802	SYSTEM_RESOURCE_APPLICATION:READ	ADMIN
019fe945-3821-7093-949d-c9ebe53f5b81	SYSTEM_RESOURCE_APPLICATION:READ+EDIT	ADMIN
019fe945-3821-7093-949d-c9f5b69efd68	SYSTEM_RESOURCE_APPLICATION:READ+DELETE	ADMIN
019fe945-3821-7093-949d-ca04a48e722a	SYSTEM_RESOURCE_APPLICATION:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-ca17cbeecad9	SYSTEM_RESOURCE_APPLICATION:READ+COPY	ADMIN
019fe945-3821-7093-949d-ca2efb7e0104	SYSTEM_RESOURCE_APPLICATION:READ+AUTH	ADMIN
019fe945-3821-7093-949d-ca3a5f33f546	SYSTEM_RESOURCE_APPLICATION:READ+PUBLISH	ADMIN
019fe945-3821-7093-949d-ca41403d6713	SYSTEM_RESOURCE_APPLICATION:READ+TRIGGER_READ	ADMIN
019fe945-3821-7093-949d-ca5108d86983	SYSTEM_RESOURCE_APPLICATION:READ+TRIGGER_CREATE	ADMIN
019fe945-3821-7093-949d-ca67d64c1395	SYSTEM_RESOURCE_APPLICATION:READ+TRIGGER_EDIT	ADMIN
019fe945-3821-7093-949d-ca76a134ab10	SYSTEM_RESOURCE_APPLICATION:READ+TRIGGER_DELETE	ADMIN
019fe945-3821-7093-949d-ca87bd487f6a	SYSTEM_RESOURCE_APPLICATION:READ+RELATE_VIEW	ADMIN
019fe945-3821-7093-949d-ca9febef78d1	SYSTEM_RESOURCE_APPLICATION_OVERVIEW:READ	ADMIN
019fe945-3821-7093-949d-caae8478f5b5	SYSTEM_RESOURCE_APPLICATION_OVERVIEW:READ+EMBED	ADMIN
019fe945-3821-7093-949d-cab61acfc111	SYSTEM_RESOURCE_APPLICATION_OVERVIEW:READ+ACCESS	ADMIN
019fe945-3821-7093-949d-cacd350b6428	SYSTEM_RESOURCE_APPLICATION_OVERVIEW:READ+DISPLAY	ADMIN
019fe945-3821-7093-949d-cada26132413	SYSTEM_RESOURCE_APPLICATION_OVERVIEW:READ+API_KEY	ADMIN
019fe945-3821-7093-949d-cae4d4cb8ee2	SYSTEM_RESOURCE_APPLICATION_OVERVIEW:READ+PUBLIC_ACCESS	ADMIN
019fe945-3821-7093-949d-cafc5e09ff05	SYSTEM_RESOURCE_APPLICATION_ACCESS:READ	ADMIN
019fe945-3821-7093-949d-cb0b195c7906	SYSTEM_RESOURCE_APPLICATION_ACCESS:READ+EDIT	ADMIN
019fe945-3821-7093-949d-cb171759f743	SYSTEM_RESOURCE_APPLICATION_CHAT_USER:READ	ADMIN
019fe945-3821-7093-949d-cb2b6a52ca17	SYSTEM_RESOURCE_APPLICATION_CHAT_USER:READ+EDIT	ADMIN
019fe945-3821-7093-949d-cb3a34a987a1	SYSTEM_RESOURCE_APPLICATION_CHAT_LOG:READ	ADMIN
019fe945-3821-7093-949d-cb4ba4ab0bec	SYSTEM_RESOURCE_APPLICATION_CHAT_LOG:READ+ADD_KNOWLEDGE	ADMIN
019fe945-3821-7093-949d-cb58ad060f0a	SYSTEM_RESOURCE_APPLICATION_CHAT_LOG:READ+ANNOTATION	ADMIN
019fe945-3821-7093-949d-cb63c50630a5	SYSTEM_RESOURCE_APPLICATION_CHAT_LOG:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-cb7fb3adec32	SYSTEM_RESOURCE_APPLICATION_CHAT_LOG:READ+CLEAR_POLICY	ADMIN
019fe945-3821-7093-949d-cb815a92b048	SYSTEM_RESOURCE_KNOWLEDGE:READ	ADMIN
019fe945-3821-7093-949d-cb97ddb3f78b	SYSTEM_RESOURCE_KNOWLEDGE:READ+EDIT	ADMIN
019fe945-3821-7093-949d-cba65ed5d193	SYSTEM_RESOURCE_KNOWLEDGE:READ+DELETE	ADMIN
019fe945-3821-7093-949d-cbb9b7f8ecc5	SYSTEM_RESOURCE_KNOWLEDGE:READ+SYNC	ADMIN
019fe945-3821-7093-949d-cbc94aa9579e	SYSTEM_RESOURCE_KNOWLEDGE:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-cbd7e6f98b8d	SYSTEM_RESOURCE_KNOWLEDGE:READ+PUBLISH	ADMIN
019fe945-3821-7093-949d-cbe244ea4b7e	SYSTEM_RESOURCE_KNOWLEDGE:READ+VECTOR	ADMIN
019fe945-3821-7093-949d-cbfde0654d73	SYSTEM_RESOURCE_KNOWLEDGE:READ+GENERATE	ADMIN
019fe945-3821-7093-949d-cc0d3535441f	SYSTEM_RESOURCE_KNOWLEDGE:READ+AUTH	ADMIN
019fe945-3821-7093-949d-cc1a9d2aa6af	SYSTEM_RESOURCE_KNOWLEDGE:READ+RELATE_VIEW	ADMIN
019fe945-3821-7093-949d-cc28b3bd561b	SYSTEM_RESOURCE_KNOWLEDGE_WORKFLOW:READ	ADMIN
019fe945-3821-7093-949d-cc386cf4f8b1	SYSTEM_RESOURCE_KNOWLEDGE_WORKFLOW:READ+EDIT	ADMIN
019fe945-3821-7093-949d-cc454c5f44e1	SYSTEM_RESOURCE_KNOWLEDGE_WORKFLOW:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-cc5c3baed610	SYSTEM_RESOURCE_KNOWLEDGE_WORKFLOW:READ+PUBLISH	ADMIN
019fe945-3821-7093-949d-cc6df9de9751	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ	ADMIN
019fe945-3821-7093-949d-cc7e6abf9613	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+CREATE	ADMIN
019fe945-3821-7093-949d-cc883911e97e	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+EDIT	ADMIN
019fe945-3821-7093-949d-cc94c5b1de92	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+DELETE	ADMIN
019fe945-3821-7093-949d-cca3266ccb39	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+SYNC	ADMIN
019fe945-3821-7093-949d-ccb6f2c5177b	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+EXPORT	ADMIN
019fe945-3821-7093-949d-ccc5392bfaca	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+DOWNLOAD	ADMIN
019fe945-3821-7093-949d-ccd0cbf5d69b	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+GENERATE	ADMIN
019fe945-3821-7093-949d-cceb136dcce5	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+VECTOR	ADMIN
019fe945-3821-7093-949d-ccfb0f73a6bc	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+MIGRATE	ADMIN
019fe945-3821-7093-949d-cd085ce895b8	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+TAG	ADMIN
019fe945-3821-7093-949d-cd1c944a377d	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+REPLACE	ADMIN
019fe945-3822-7872-bcc8-c68233bc9566	SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT:READ+TOKEN	ADMIN
019fe945-3822-7872-bcc8-c693d804b408	SYSTEM_RESOURCE_KNOWLEDGE_HIT_TEST:READ	ADMIN
019fe945-3822-7872-bcc8-c6a72e947a12	SYSTEM_RESOURCE_KNOWLEDGE_PROBLEM:READ	ADMIN
019fe945-3822-7872-bcc8-c6b2ece5a868	SYSTEM_RESOURCE_KNOWLEDGE_PROBLEM:READ+CREATE	ADMIN
019fe945-3822-7872-bcc8-c6cfbd19d8cd	SYSTEM_RESOURCE_KNOWLEDGE_PROBLEM:READ+EDIT	ADMIN
019fe945-3822-7872-bcc8-c6db8eb26bd4	SYSTEM_RESOURCE_KNOWLEDGE_PROBLEM:READ+DELETE	ADMIN
019fe945-3822-7872-bcc8-c6e58a37884b	SYSTEM_RESOURCE_KNOWLEDGE_PROBLEM:READ+RELATE	ADMIN
019fe945-3822-7872-bcc8-c6f078787cfd	SYSTEM_RESOURCE_KNOWLEDGE_TERMBASE:READ	ADMIN
019fe945-3822-7872-bcc8-c70f28a9acf8	SYSTEM_RESOURCE_KNOWLEDGE_TERMBASE:READ+CREATE	ADMIN
019fe945-3822-7872-bcc8-c714cc7eb78b	SYSTEM_RESOURCE_KNOWLEDGE_TERMBASE:READ+EDIT	ADMIN
019fe945-3822-7872-bcc8-c721fe6d6938	SYSTEM_RESOURCE_KNOWLEDGE_TERMBASE:READ+DELETE	ADMIN
019fe945-3822-7872-bcc8-c73712c86cec	SYSTEM_RESOURCE_KNOWLEDGE_TERMBASE:READ+EXPORT	ADMIN
019fe945-3822-7872-bcc8-c74a73d7189c	SYSTEM_RES_KNOWLEDGE_TAG:READ	ADMIN
019fe945-3822-7872-bcc8-c750885a3518	SYSTEM_RES_KNOWLEDGE_TAG:READ+CREATE	ADMIN
019fe945-3822-7872-bcc8-c76deb56d260	SYSTEM_RES_KNOWLEDGE_TAG:READ+EDIT	ADMIN
019fe945-3822-7872-bcc8-c777f0bb59f7	SYSTEM_RES_KNOWLEDGE_TAG:READ+DELETE	ADMIN
019fe945-3822-7872-bcc8-c784c6bdabc6	SYSTEM_RESOURCE_KNOWLEDGE_CHAT_USER:READ	ADMIN
019fe945-3822-7872-bcc8-c7918e2f4f32	SYSTEM_RESOURCE_KNOWLEDGE_CHAT_USER:READ+EDIT	ADMIN
019fe945-3822-7872-bcc8-c7ab74456f99	SYSTEM_RESOURCE_TOOL:READ	ADMIN
019fe945-3822-7872-bcc8-c7b992827825	SYSTEM_RESOURCE_TOOL:READ+EDIT	ADMIN
019fe945-3822-7872-bcc8-c7c57e20b600	SYSTEM_RESOURCE_TOOL:READ+DELETE	ADMIN
019fe945-3822-7872-bcc8-c7d2646bf5fe	SYSTEM_RESOURCE_TOOL:READ+EXPORT	ADMIN
019fe945-3822-7872-bcc8-c7ef6754df9c	SYSTEM_RESOURCE_TOOL:READ+PUBLISH	ADMIN
019fe945-3822-7872-bcc8-c7f6b64b31e0	SYSTEM_RESOURCE_TOOL:READ+AUTH	ADMIN
019fe945-3822-7872-bcc8-c80cf2347435	SYSTEM_RESOURCE_TOOL:READ+RELATE_VIEW	ADMIN
019fe945-3822-7872-bcc8-c817dcb18ec1	SYSTEM_RESOURCE_TOOL:READ+RECORD	ADMIN
019fe945-3822-7872-bcc8-c821dfd036c5	SYSTEM_RESOURCE_TOOL:READ+TRIGGER_READ	ADMIN
019fe945-3822-7872-bcc8-c8306ee5d9ee	SYSTEM_RESOURCE_TOOL:READ+TRIGGER_CREATE	ADMIN
019fe945-3822-7872-bcc8-c8402a87074b	SYSTEM_RESOURCE_TOOL:READ+TRIGGER_EDIT	ADMIN
019fe945-3822-7872-bcc8-c85ccee4e76a	SYSTEM_RESOURCE_TOOL:READ+TRIGGER_DELETE	ADMIN
019fe945-3822-7872-bcc8-c86d1d326778	SYSTEM_RESOURCE_MODEL:READ	ADMIN
019fe945-3822-7872-bcc8-c87533030d34	SYSTEM_RESOURCE_MODEL:READ+EDIT	ADMIN
019fe945-3822-7872-bcc8-c88c14beff75	SYSTEM_RESOURCE_MODEL:READ+DELETE	ADMIN
019fe945-3822-7872-bcc8-c892e97bfcb0	SYSTEM_RESOURCE_MODEL:READ+AUTH	ADMIN
019fe945-3822-7872-bcc8-c8a040db2eb9	SYSTEM_RESOURCE_MODEL:READ+RELATE_VIEW	ADMIN
019fe945-3822-7872-bcc8-c8b0843807cf	OPERATION_LOG:READ	ADMIN
019fe945-3822-7872-bcc8-c8c40b676ad9	OPERATION_LOG:READ+EXPORT	ADMIN
019fe945-3822-7872-bcc8-c8d2962a00e4	OPERATION_LOG:READ+CLEAR_POLICY	ADMIN
\.


--
-- Data for Name: role_setting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_setting (id, role_name, type, internal, create_time, update_time, create_user_id) FROM stdin;
ADMIN	系统管理员	ADMIN	t	2026-08-10 01:24:03.534572+00	2026-08-10 01:24:03.534581+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
WORKSPACE_MANAGE	工作空间管理员	WORKSPACE_MANAGE	t	2026-08-10 01:24:03.539978+00	2026-08-10 01:24:03.539986+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
USER	普通用户	USER	t	2026-08-10 01:24:03.542438+00	2026-08-10 01:24:03.542445+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Data for Name: shared_resource_workspace_authorization; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shared_resource_workspace_authorization (id, resource_type, authentication_type, workspace_id_list, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: system_api_key; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_api_key (id, secret_key, is_active, allow_cross_domain, cross_domain_list, expire_time, is_permanent, create_time, update_time, user_id) FROM stdin;
\.


--
-- Data for Name: system_setting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_setting (create_time, update_time, type, meta) FROM stdin;
2026-08-10 01:23:59.795534+00	2026-08-10 01:23:59.795544+00	1	{"key": "-----BEGIN PUBLIC KEY-----\\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqGmtEFLUdvH04fFq63sD\\n5ndtWt/e7BpEW99ZMR1ItHjC4LsQb6mo0qWqMtmsLaVfIcOXVrfXpMGIzvQshsqP\\nHF5gSOCIfn+zuQTSbBK/hybjqZw11a6YHc53t6pVamwEQVHyBisN0hMo7dwkfTe+\\nEvmYVVppktAs2bEQujjA4RdCSpdSAMDGzwTUTYt6SmAOFLhWFgGS7ffmEY5aAgWX\\nF2kRJ0ObLE5Xh6nenLSeXNzDHVKS2fmGcT8B6/Xio9wbrwf85e2IetUR7kDA7+AK\\niN9Vda4QqeRDoqldxiDnhbmqKOoM5j5CiZkBQKUQXwkr64/+cKNmwLC3XdlIQVk0\\nnwIDAQAB\\n-----END PUBLIC KEY-----", "value": "-----BEGIN ENCRYPTED PRIVATE KEY-----\\nMIIFJTBPBgkqhkiG9w0BBQ0wQjAhBgkrBgEEAdpHBAswFAQIJZuhyTFqOq0CAkAA\\nAgEIAgEBMB0GCWCGSAFlAwQBAgQQZmFm6OJnlCdxt8sjQ3PG2QSCBNB7W4gQY8VL\\nCpYJFPu5d8zez8o7O7StLaWGLUdbH4JrU0pXV3CUzw1B4BS/ZJL94tHBqUGxa0gl\\nMn7Y/2h/vcXqj8FIWz9oR+qoLTA7wABXkr+49id3pJ3MUa2Nv4Rznm4QwUJp0Mkm\\nmp7fajkQVVRrYeGRWFWHw0w6+9geVo/gmFTL6QrGbJzF5ERX/OGnSWU1SlAdkqbA\\nit7CJZzOYQ1VdnjMVMLwUf315BnN1BsFx0xobtSan0H4I0h/a3sd5Rqfxuzng9v0\\nrMec14zUSd5YFmx34bwKgnquEi78kfLWwKOAb3Bvi0Mh7xyA27aKUusLoeNaM9sg\\nGMH1DD3+BjkA/ugwGGF8GWbjYlPIsYQGiWavpnfRDQoOzB+W2H7tqc6cPQb7loN3\\nDruk0XAMBURsUK2VEC6swWWNh334N9AaYOt/ASyOui8ixiLkVdKbDNWRWl/XsyaD\\nSjnmMfThz2vaAoK2hnaDkFzJ+H4co4zYtJrWODvxs0vUF9PekQw9HZEhIOecS8E/\\nQQbxiFB4sRYF11kXMnWvLA4WrjhU9OxzZV2515S0DmlknjVWuTrTGnSGVLPeF8+k\\n08A/zo9R6DzFpx4D5GpYwmU1QyejN4UsTEMsny1BvcjFOMm+aqmz6/ERvrmhfkCx\\n1SAi4UgqYCvkbd+4UIZHPXXqUufaRUkRwBiEjUmukPjIGz2U8FVIfsg4piaaAyRN\\nizDxULFeKUXD+skrsgFqWiIlqVgaNFtho5d1PToyOfIRqioyt/Y3XxZLalxcCct4\\nB7d00uxk194MDEWCa0UbfGYrcwkN1Yiz41b8217bfkdrboeebRw8YF1gIqnQhQAg\\nVDTZSCx4huIZE5mwSYS11G83CVO4Ub/y9+/kN+foX39iqTkihSPXQ1aIXHmA8fEV\\nVujFQpj2Ib8Ab1doNcak5GNp/2s3pZbPStEVoauouNt6tmNNUEVasGBBSl8ANFZL\\nUPpfOyqP5WgS80ETncNqo8gLZeXph2ZdAGH3W09tR6SK8Xmu7lvix3snLHs1znEj\\ng49SIgGQBgjReH/gKdf+kVG8iwROie4LscbMDJrz2kcoXOCjXg7o3cpwlzLsr6q9\\niYqgDGGhkswRSdWxGRQUw7npBfnc9OZuy1wm5P8BB5DQMB6P9JznX/2N+HocIwwv\\nnHfp0/y2bHqAP1u5tAijsiJrEQEfBI24/IVZ0G11bHSN3Ue8OT2uBQMowwNURvyC\\nfFDENddreKfpd7PchYCrCNeNbRd+/1tRI+M2X8G2b/i6rG5UyM3CIyqyzkMyDr9V\\nef90PvjPHPTF1I2M1yoFCj43h48g4l4pRQLH33lgBJQob15An02c8Ati3QA4O5O5\\nkgqSlkM92DgtEzN68knMvf6sZ3ZYoz/NvC/xVWpqtmzk7CTL07Ra4zn98brL7yJg\\nV+FLjqu5lVdb3WUC5PfamiJJpEvKFf974vagymYkPjfj3wbWfmrxv6+rzlCc4frf\\nmoP9FIrTdIc14gUyvZMN22iBGYv3nMbcKp9HmIF4lfHJSSOQ9KeZncgawSWJgCfn\\nA5oURBN7l9YKTtCnBF5St0I8FdTazIqdl4c/TI/IYc4MA9z1l9cUuE0jxfsk7KKb\\nPCUrKLhT3y7/fAaqBfokO5joPEb23oSzXg==\\n-----END ENCRYPTED PRIVATE KEY-----"}
\.


--
-- Data for Name: tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tag (create_time, update_time, id, key, value, knowledge_id) FROM stdin;
\.


--
-- Data for Name: termbase; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.termbase (create_time, update_time, id, content, knowledge_id) FROM stdin;
\.


--
-- Data for Name: tool; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tool (create_time, update_time, id, name, "desc", code, input_field_list, init_field_list, icon, is_active, scope, tool_type, template_id, workspace_id, init_params, label, user_id, folder_id, version) FROM stdin;
2025-03-10 06:20:35.945414+00	2025-03-10 09:19:23.608026+00	c75cb48e-fd77-11ef-84d2-5618c4394482	博查搜索	从博查搜索任何信息和网页URL	def bocha_search(query, apikey):\n    import requests\n    import json\n    url = "https://api.bochaai.com/v1/web-search"\n    payload = json.dumps({\n        "query": query,\n        "summary": True,\n        "count": 8\n    })\n\n    headers = {\n        "Authorization": "Bearer " + apikey, #鉴权参数，示例：Bearer xxxxxx，API KEY请先前往博查AI开放平台（https://open.bochaai.com）> API KEY 管理中获取。\n        "Content-Type": "application/json"\n    }\n\n    response = requests.request("POST", url, headers=headers, data=payload)\n    if response.status_code == 200:\n        return response.json()\n    else:\n        raise Exception(f"API请求失败: {response.status_code}, 错误信息: {response.text}")\n        return (response.text)	[{"name": "query", "type": "string", "source": "reference", "is_required": true}]	[{"attrs": {"type": "password", "maxlength": 200, "minlength": 1, "show-password": true, "show-word-limit": true}, "field": "apikey", "label": "API Key", "required": true, "input_type": "PasswordInput", "props_info": {"rules": [{"message": "API Key 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "API Key 长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}]	./tool/bochaai/icon.png	t	INTERNAL	INTERNAL	\N	None		web_search	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default	\N
2025-02-26 03:36:48.187286+00	2025-03-11 07:23:46.123972+00	e89ad2ae-f3f2-11ef-ad09-0242ac110002	Google Search	Google Web Search	def google_search(query, apikey, cx):\n    import requests\n    import json\n    url = "https://customsearch.googleapis.com/customsearch/v1"\n    params = {\n        "q": query,\n        "key": apikey,\n        "cx": cx,\n        "num": 10,  # 每次最多返回10条\n    }\n\n    response = requests.get(url, params=params)\n    if response.status_code == 200:\n        return response.json()\n    else:\n        raise Exception(f"API请求失败: {response.status_code}, 错误信息: {response.text}")\n        return (response.text)	[{"name": "query", "type": "string", "source": "reference", "is_required": true}]	[{"attrs": {"type": "password", "maxlength": 200, "minlength": 1, "show-password": true, "show-word-limit": true}, "field": "apikey", "label": "API Key", "required": true, "input_type": "PasswordInput", "props_info": {"rules": [{"message": "API Key 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "API Key 长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}, {"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "cx", "label": "cx", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "cx 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "cx长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}]	./tool/google_search/icon.png	t	INTERNAL	INTERNAL	\N	None		web_search	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default	\N
2025-02-25 07:44:40.141515+00	2025-03-11 06:33:53.248495+00	5e912f00-f34c-11ef-8a9c-5618c4394482	LangSearch	A Web Search tool supporting natural language search\n	\ndef langsearch(query, apikey):\n    import json\n    import requests\n\n    url = "https://api.langsearch.com/v1/web-search"\n    payload = json.dumps({\n        "query": query,\n        "summary": True,\n        "freshness": "noLimit",\n        "livecrawl": True,\n        "count": 20\n    })\n    headers = {\n        "Authorization": apikey,\n        "Content-Type": "application/json"\n    }\n    # key从官网申请 https://langsearch.com/\n    response = requests.request("POST", url, headers=headers, data=payload)\n    if response.status_code == 200:\n        return response.json()\n    else:\n        raise Exception(f"API请求失败: {response.status_code}, 错误信息: {response.text}")\n        return (response.text)	[{"name": "query", "type": "string", "source": "reference", "is_required": true}]	[{"attrs": {"type": "password", "maxlength": 200, "minlength": 1, "show-password": true, "show-word-limit": true}, "field": "apikey", "label": "API Key", "required": true, "input_type": "PasswordInput", "props_info": {"rules": [{"message": "API Key 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "API Key 长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}]	./tool/langsearch/icon.png	t	INTERNAL	INTERNAL	\N	None		web_search	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default	\N
2025-03-17 08:16:32.626245+00	2025-03-17 08:16:32.626308+00	22c21b76-0308-11f0-9694-5618c4394482	MySQL 查询	一个连接MySQL数据库执行SQL查询的工具	\ndef query_mysql(host,port, user, password, database, sql):\n    import pymysql\n    import json\n    from pymysql.cursors import DictCursor\n    from datetime import datetime, date\n\n    def default_serializer(obj):\n        from decimal import Decimal\n        if isinstance(obj, (datetime, date)):\n            return obj.isoformat()  # 将 datetime/date 转换为 ISO 格式字符串\n        elif isinstance(obj, Decimal):\n            return float(obj)  # 将 Decimal 转换为 float\n        raise TypeError(f"Type {type(obj)} not serializable")\n\n    try:\n        # 创建连接\n        db = pymysql.connect(\n            host=host,\n            port=int(port),\n            user=user,\n            password=password,\n            database=database,\n            cursorclass=DictCursor  # 使用字典游标\n        )\n\n        # 使用 cursor() 方法创建一个游标对象 cursor\n        cursor = db.cursor()\n\n        # 使用 execute() 方法执行 SQL 查询\n        cursor.execute(sql)\n\n        # 使用 fetchall() 方法获取所有数据\n        data = cursor.fetchall()\n\n        # 处理 bytes 类型的数据\n        for row in data:\n            for key, value in row.items():\n                if isinstance(value, bytes):\n                    row[key] = value.decode("utf-8")  # 转换为字符串\n\n        # 将数据序列化为 JSON\n        json_data = json.dumps(data, default=default_serializer, ensure_ascii=False)\n        return json_data\n\n        # 关闭数据库连接\n        db.close()\n\n    except Exception as e:\n        print(f"Error while connecting to MySQL: {e}")\n        raise e	[{"name": "sql", "type": "string", "source": "reference", "is_required": true}]	[{"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "host", "label": "host", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "host 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "host长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}, {"attrs": {"maxlength": 20, "minlength": 1, "show-word-limit": true}, "field": "port", "label": "port", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "port 为必填属性", "required": true}, {"max": 20, "min": 1, "message": "port长度在 1 到 20 个字符", "trigger": "blur"}]}, "default_value": "3306", "show_default_value": false}, {"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "user", "label": "user", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "user 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "user长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "root", "show_default_value": false}, {"attrs": {"type": "password", "maxlength": 200, "minlength": 1, "show-password": true, "show-word-limit": true}, "field": "password", "label": "password", "required": true, "input_type": "PasswordInput", "props_info": {"rules": [{"message": "password 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "password长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}, {"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "database", "label": "database", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "database 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "database长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}]	./tool/mysql/icon.png	t	INTERNAL	INTERNAL	\N	None	\N	database_search	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default	\N
2025-03-17 07:37:54.620836+00	2025-03-17 07:37:54.620887+00	bd1e8b88-0302-11f0-87bb-5618c4394482	PostgreSQL 查询	一个连接PostgreSQL数据库执行SQL查询的工具	\ndef queryPgSQL(database, user, password, host, port, query):\n    import psycopg2\n    import json\n    from datetime import datetime\n\n    # 自定义 JSON 序列化函数\n    def default_serializer(obj):\n        from decimal import Decimal\n        if isinstance(obj, datetime):\n            return obj.isoformat()  # 将 datetime 转换为 ISO 格式字符串\n        elif isinstance(obj, Decimal):\n            return float(obj)  # 将 Decimal 转换为 float\n        raise TypeError(f"Type {type(obj)} not serializable")\n\n    # 数据库连接信息\n    conn_params = {\n        "dbname": database,\n        "user": user,\n        "password": password,\n        "host": host,\n        "port": port\n    }\n    try:\n        # 建立连接\n        conn = psycopg2.connect(**conn_params)\n        print("连接成功！")\n        # 创建游标对象\n        cursor = conn.cursor()\n        # 执行查询语句\n        cursor.execute(query)\n        # 获取查询结果\n        rows = cursor.fetchall()\n        # 处理 bytes 类型的数据\n        columns = [desc[0] for desc in cursor.description]\n        result = [dict(zip(columns, row)) for row in rows]\n        # 转换为 JSON 格式\n        json_result = json.dumps(result, default=default_serializer, ensure_ascii=False)\n        return json_result\n    except Exception as e:\n        print(f"发生错误：{e}")\n        raise e\n    finally:\n        # 关闭游标和连接\n        if cursor:\n            cursor.close()\n        if conn:\n            conn.close()	[{"name": "query", "type": "string", "source": "reference", "is_required": true}]	[{"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "host", "label": "host", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "host 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "host长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}, {"attrs": {"maxlength": 20, "minlength": 1, "show-word-limit": true}, "field": "port", "label": "port", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "port 为必填属性", "required": true}, {"max": 20, "min": 1, "message": "port长度在 1 到 20 个字符", "trigger": "blur"}]}, "default_value": "5432", "show_default_value": false}, {"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "user", "label": "user", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "user 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "user长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "root", "show_default_value": false}, {"attrs": {"type": "password", "maxlength": 200, "minlength": 1, "show-password": true, "show-word-limit": true}, "field": "password", "label": "password", "required": true, "input_type": "PasswordInput", "props_info": {"rules": [{"message": "password 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "password长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}, {"attrs": {"maxlength": 200, "minlength": 1, "show-word-limit": true}, "field": "database", "label": "database", "required": true, "input_type": "TextInput", "props_info": {"rules": [{"message": "database 为必填属性", "required": true}, {"max": 200, "min": 1, "message": "database长度在 1 到 200 个字符", "trigger": "blur"}]}, "default_value": "x", "show_default_value": false}]	./tool/postgresql/icon.png	t	INTERNAL	INTERNAL	\N	None	\N	database_search	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default	\N
\.


--
-- Data for Name: tool_folder; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tool_folder (create_time, update_time, id, name, "desc", workspace_id, lft, rght, tree_id, level, parent_id, user_id) FROM stdin;
2026-08-10 01:23:57.173072+00	2026-08-10 01:23:57.173085+00	default	根目录	\N	default	1	2	1	0	\N	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Data for Name: tool_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tool_record (create_time, update_time, id, source_type, source_id, meta, state, run_time, tool_id, workspace_id) FROM stdin;
\.


--
-- Data for Name: tool_workflow; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tool_workflow (create_time, update_time, id, workspace_id, work_flow, is_publish, publish_time, tool_id) FROM stdin;
\.


--
-- Data for Name: tool_workflow_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tool_workflow_version (create_time, update_time, id, workspace_id, name, work_flow, publish_user_id, publish_user_name, tool_id) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."user" (id, email, phone, nick_name, username, password, role, source, is_active, language, create_time, update_time) FROM stdin;
f0dd8f71-e4ee-11ee-8c84-a8a1595801ab			系统管理员	admin	pbkdf2_sha256$1000000$7rx2ehYcqK71Z8nOAVEpBM$ygXzHTqTRTnPt8ZqxAT1K4P7Cf+b/w1Ml6J4KQVYNMY=	ADMIN	LOCAL	t	\N	2026-08-10 01:23:57.098397+00	2026-08-10 01:23:57.09841+00
\.


--
-- Data for Name: user_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_group (id, name) FROM stdin;
default	默认用户组
\.


--
-- Data for Name: user_group_relation; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_group_relation (id, group_id, user_id) FROM stdin;
\.


--
-- Data for Name: user_role_relation; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_role_relation (id, role_id, user_id, workspace_id) FROM stdin;
019fe945-0957-7980-8c9b-956775b43922	ADMIN	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default
019fe945-095d-7390-a4e2-2f38d67c193d	WORKSPACE_MANAGE	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default
019fe945-0960-7ed1-9061-21e0ecd10ccb	USER	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab	default
\.


--
-- Data for Name: workspace; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.workspace (id, name, create_time, update_time, create_user_id) FROM stdin;
default	默认空间	2026-08-10 01:24:03.527907+00	2026-08-10 01:24:03.527917+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Data for Name: workspace_user_resource_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.workspace_user_resource_permission (id, workspace_id, auth_target_type, target, auth_type, permission_list, create_time, update_time, user_id) FROM stdin;
019fe944-febf-7282-b122-8159c6d4a35e	default	APPLICATION	default	RESOURCE_PERMISSION_GROUP	{VIEW,MANAGE}	2026-08-10 01:24:00.865965+00	2026-08-10 01:24:00.865994+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
019fe944-fec9-7ec3-b706-9eadde268e95	default	TOOL	default	RESOURCE_PERMISSION_GROUP	{VIEW,MANAGE}	2026-08-10 01:24:00.866056+00	2026-08-10 01:24:00.866065+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
019fe944-fed4-7180-ae6b-56b03040b6e6	default	KNOWLEDGE	default	RESOURCE_PERMISSION_GROUP	{VIEW,MANAGE}	2026-08-10 01:24:00.866097+00	2026-08-10 01:24:00.866105+00	f0dd8f71-e4ee-11ee-8c84-a8a1595801ab
\.


--
-- Name: django_apscheduler_djangojobexecution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_apscheduler_djangojobexecution_id_seq', 1, false);


--
-- Name: django_celery_beat_clockedschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_clockedschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_crontabschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_crontabschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_intervalschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_intervalschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_periodictask_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_periodictask_id_seq', 1, false);


--
-- Name: django_celery_beat_solarschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_celery_beat_solarschedule_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 64, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 77, true);


--
-- Name: application_access_token application_access_token_access_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_access_token
    ADD CONSTRAINT application_access_token_access_token_key UNIQUE (access_token);


--
-- Name: application_access_token application_access_token_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_access_token
    ADD CONSTRAINT application_access_token_pkey PRIMARY KEY (application_id);


--
-- Name: application_api_key application_api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_api_key
    ADD CONSTRAINT application_api_key_pkey PRIMARY KEY (id);


--
-- Name: application_api_key application_api_key_secret_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_api_key
    ADD CONSTRAINT application_api_key_secret_key_key UNIQUE (secret_key);


--
-- Name: application_chat application_chat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat
    ADD CONSTRAINT application_chat_pkey PRIMARY KEY (id);


--
-- Name: application_chat_record application_chat_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_record
    ADD CONSTRAINT application_chat_record_pkey PRIMARY KEY (id);


--
-- Name: application_chat_share_link application_chat_share_link_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_share_link
    ADD CONSTRAINT application_chat_share_link_pkey PRIMARY KEY (id);


--
-- Name: application_chat_user_stats application_chat_user_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_user_stats
    ADD CONSTRAINT application_chat_user_stats_pkey PRIMARY KEY (id);


--
-- Name: application_folder application_folder_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_folder
    ADD CONSTRAINT application_folder_pkey PRIMARY KEY (id);


--
-- Name: application_knowledge_mapping application_knowledge_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_knowledge_mapping
    ADD CONSTRAINT application_knowledge_mapping_pkey PRIMARY KEY (id);


--
-- Name: application_long_term_memory application_long_term_me_application_id_chat_user_7f1bd03b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_long_term_memory
    ADD CONSTRAINT application_long_term_me_application_id_chat_user_7f1bd03b_uniq UNIQUE (application_id, chat_user_id);


--
-- Name: application_long_term_memory application_long_term_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_long_term_memory
    ADD CONSTRAINT application_long_term_memory_pkey PRIMARY KEY (id);


--
-- Name: application application_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application
    ADD CONSTRAINT application_pkey PRIMARY KEY (id);


--
-- Name: application_setting application_setting_application_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_setting
    ADD CONSTRAINT application_setting_application_id_key UNIQUE (application_id);


--
-- Name: application_setting application_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_setting
    ADD CONSTRAINT application_setting_pkey PRIMARY KEY (id);


--
-- Name: application_version application_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_version
    ADD CONSTRAINT application_version_pkey PRIMARY KEY (id);


--
-- Name: chat_auth_setting chat_auth_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_auth_setting
    ADD CONSTRAINT chat_auth_setting_pkey PRIMARY KEY (auth_type);


--
-- Name: chat_platform chat_platform_auth_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_platform
    ADD CONSTRAINT chat_platform_auth_type_key UNIQUE (auth_type);


--
-- Name: chat_platform chat_platform_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_platform
    ADD CONSTRAINT chat_platform_pkey PRIMARY KEY (id);


--
-- Name: chat_user chat_user_nick_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_user
    ADD CONSTRAINT chat_user_nick_name_key UNIQUE (nick_name);


--
-- Name: chat_user chat_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_user
    ADD CONSTRAINT chat_user_pkey PRIMARY KEY (id);


--
-- Name: chat_user chat_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_user
    ADD CONSTRAINT chat_user_username_key UNIQUE (username);


--
-- Name: django_apscheduler_djangojob django_apscheduler_djangojob_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_apscheduler_djangojob
    ADD CONSTRAINT django_apscheduler_djangojob_pkey PRIMARY KEY (id);


--
-- Name: django_apscheduler_djangojobexecution django_apscheduler_djangojobexecution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_apscheduler_djangojobexecution
    ADD CONSTRAINT django_apscheduler_djangojobexecution_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_clockedschedule django_celery_beat_clockedschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_clockedschedule
    ADD CONSTRAINT django_celery_beat_clockedschedule_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_crontabschedule django_celery_beat_crontabschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_crontabschedule
    ADD CONSTRAINT django_celery_beat_crontabschedule_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_intervalschedule django_celery_beat_intervalschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_intervalschedule
    ADD CONSTRAINT django_celery_beat_intervalschedule_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_periodictask django_celery_beat_periodictask_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_periodictask_name_key UNIQUE (name);


--
-- Name: django_celery_beat_periodictask django_celery_beat_periodictask_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_periodictask_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_periodictasks django_celery_beat_periodictasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictasks
    ADD CONSTRAINT django_celery_beat_periodictasks_pkey PRIMARY KEY (ident);


--
-- Name: django_celery_beat_solarschedule django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_solarschedule
    ADD CONSTRAINT django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq UNIQUE (event, latitude, longitude);


--
-- Name: django_celery_beat_solarschedule django_celery_beat_solarschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_solarschedule
    ADD CONSTRAINT django_celery_beat_solarschedule_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: document document_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document
    ADD CONSTRAINT document_pkey PRIMARY KEY (id);


--
-- Name: document_tag document_tag_document_id_tag_id_55f500a6_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_tag
    ADD CONSTRAINT document_tag_document_id_tag_id_55f500a6_uniq UNIQUE (document_id, tag_id);


--
-- Name: document_tag document_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_tag
    ADD CONSTRAINT document_tag_pkey PRIMARY KEY (id);


--
-- Name: embedding embedding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.embedding
    ADD CONSTRAINT embedding_pkey PRIMARY KEY (id);


--
-- Name: event_trigger event_trigger_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_trigger
    ADD CONSTRAINT event_trigger_pkey PRIMARY KEY (id);


--
-- Name: event_trigger_task event_trigger_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_trigger_task
    ADD CONSTRAINT event_trigger_task_pkey PRIMARY KEY (id);


--
-- Name: event_trigger_task_record event_trigger_task_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_trigger_task_record
    ADD CONSTRAINT event_trigger_task_record_pkey PRIMARY KEY (id);


--
-- Name: event_trigger_task event_trigger_task_trigger_id_source_id_sou_f3530a5f_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_trigger_task
    ADD CONSTRAINT event_trigger_task_trigger_id_source_id_sou_f3530a5f_uniq UNIQUE (trigger_id, source_id, source_type);


--
-- Name: file file_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file
    ADD CONSTRAINT file_pkey PRIMARY KEY (id);


--
-- Name: knowledge_action knowledge_action_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_action
    ADD CONSTRAINT knowledge_action_pkey PRIMARY KEY (id);


--
-- Name: knowledge_folder knowledge_folder_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_folder
    ADD CONSTRAINT knowledge_folder_pkey PRIMARY KEY (id);


--
-- Name: knowledge knowledge_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge
    ADD CONSTRAINT knowledge_pkey PRIMARY KEY (id);


--
-- Name: knowledge_workflow knowledge_workflow_knowledge_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_workflow
    ADD CONSTRAINT knowledge_workflow_knowledge_id_key UNIQUE (knowledge_id);


--
-- Name: knowledge_workflow knowledge_workflow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_workflow
    ADD CONSTRAINT knowledge_workflow_pkey PRIMARY KEY (id);


--
-- Name: knowledge_workflow_version knowledge_workflow_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_workflow_version
    ADD CONSTRAINT knowledge_workflow_version_pkey PRIMARY KEY (id);


--
-- Name: log log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_pkey PRIMARY KEY (id);


--
-- Name: model model_name_workspace_id_68e244ba_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_name_workspace_id_68e244ba_uniq UNIQUE (name, workspace_id);


--
-- Name: model model_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_pkey PRIMARY KEY (id);


--
-- Name: paragraph paragraph_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paragraph
    ADD CONSTRAINT paragraph_pkey PRIMARY KEY (id);


--
-- Name: platform_display_setting platform_display_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_display_setting
    ADD CONSTRAINT platform_display_setting_pkey PRIMARY KEY (id);


--
-- Name: problem_paragraph_mapping problem_paragraph_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.problem_paragraph_mapping
    ADD CONSTRAINT problem_paragraph_mapping_pkey PRIMARY KEY (id);


--
-- Name: problem problem_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.problem
    ADD CONSTRAINT problem_pkey PRIMARY KEY (id);


--
-- Name: public_file_access public_file_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_file_access
    ADD CONSTRAINT public_file_access_pkey PRIMARY KEY (id);


--
-- Name: resource_chat_user_authorize resource_chat_user_autho_user_group_id_resource_t_7fc1cc94_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_authorize
    ADD CONSTRAINT resource_chat_user_autho_user_group_id_resource_t_7fc1cc94_uniq UNIQUE (user_group_id, resource_type, resource_id, user_id);


--
-- Name: resource_chat_user_authorize resource_chat_user_authorize_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_authorize
    ADD CONSTRAINT resource_chat_user_authorize_pkey PRIMARY KEY (id);


--
-- Name: resource_chat_user_group_authorize resource_chat_user_group_authorize_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_group_authorize
    ADD CONSTRAINT resource_chat_user_group_authorize_pkey PRIMARY KEY (id);


--
-- Name: resource_chat_user_group_authorize resource_chat_user_group_user_group_id_resource_t_5eccc9b0_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_group_authorize
    ADD CONSTRAINT resource_chat_user_group_user_group_id_resource_t_5eccc9b0_uniq UNIQUE (user_group_id, resource_type, resource_id);


--
-- Name: resource_mapping resource_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_mapping
    ADD CONSTRAINT resource_mapping_pkey PRIMARY KEY (id);


--
-- Name: role_permission role_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permission
    ADD CONSTRAINT role_permission_pkey PRIMARY KEY (id);


--
-- Name: role_permission role_permission_role_id_permission_id_0a48a767_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permission
    ADD CONSTRAINT role_permission_role_id_permission_id_0a48a767_uniq UNIQUE (role_id, permission_id);


--
-- Name: role_setting role_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_setting
    ADD CONSTRAINT role_setting_pkey PRIMARY KEY (id);


--
-- Name: shared_resource_workspace_authorization shared_resource_workspace_authorization_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_resource_workspace_authorization
    ADD CONSTRAINT shared_resource_workspace_authorization_pkey PRIMARY KEY (id);


--
-- Name: system_api_key system_api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_api_key
    ADD CONSTRAINT system_api_key_pkey PRIMARY KEY (id);


--
-- Name: system_api_key system_api_key_secret_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_api_key
    ADD CONSTRAINT system_api_key_secret_key_key UNIQUE (secret_key);


--
-- Name: system_setting system_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_setting
    ADD CONSTRAINT system_setting_pkey PRIMARY KEY (type);


--
-- Name: tag tag_knowledge_id_key_value_eb5f0e5d_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_knowledge_id_key_value_eb5f0e5d_uniq UNIQUE (knowledge_id, key, value);


--
-- Name: tag tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_pkey PRIMARY KEY (id);


--
-- Name: termbase termbase_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.termbase
    ADD CONSTRAINT termbase_pkey PRIMARY KEY (id);


--
-- Name: tool_folder tool_folder_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_folder
    ADD CONSTRAINT tool_folder_pkey PRIMARY KEY (id);


--
-- Name: tool tool_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool
    ADD CONSTRAINT tool_pkey PRIMARY KEY (id);


--
-- Name: tool_record tool_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_record
    ADD CONSTRAINT tool_record_pkey PRIMARY KEY (id);


--
-- Name: tool_workflow tool_workflow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_workflow
    ADD CONSTRAINT tool_workflow_pkey PRIMARY KEY (id);


--
-- Name: tool_workflow tool_workflow_tool_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_workflow
    ADD CONSTRAINT tool_workflow_tool_id_key UNIQUE (tool_id);


--
-- Name: tool_workflow_version tool_workflow_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_workflow_version
    ADD CONSTRAINT tool_workflow_version_pkey PRIMARY KEY (id);


--
-- Name: django_apscheduler_djangojobexecution unique_job_executions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_apscheduler_djangojobexecution
    ADD CONSTRAINT unique_job_executions UNIQUE (job_id, run_time);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user_group user_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_group
    ADD CONSTRAINT user_group_name_key UNIQUE (name);


--
-- Name: user_group user_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_group
    ADD CONSTRAINT user_group_pkey PRIMARY KEY (id);


--
-- Name: user_group_relation user_group_relation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_group_relation
    ADD CONSTRAINT user_group_relation_pkey PRIMARY KEY (id);


--
-- Name: user user_nick_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_nick_name_key UNIQUE (nick_name);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user_role_relation user_role_relation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role_relation
    ADD CONSTRAINT user_role_relation_pkey PRIMARY KEY (id);


--
-- Name: user_role_relation user_role_relation_workspace_id_role_id_user_id_458d2c05_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role_relation
    ADD CONSTRAINT user_role_relation_workspace_id_role_id_user_id_458d2c05_uniq UNIQUE (workspace_id, role_id, user_id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: workspace workspace_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace
    ADD CONSTRAINT workspace_name_key UNIQUE (name);


--
-- Name: workspace workspace_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace
    ADD CONSTRAINT workspace_pkey PRIMARY KEY (id);


--
-- Name: workspace_user_resource_permission workspace_user_resource__workspace_id_user_id_aut_692d4734_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace_user_resource_permission
    ADD CONSTRAINT workspace_user_resource__workspace_id_user_id_aut_692d4734_uniq UNIQUE (workspace_id, user_id, auth_target_type, target);


--
-- Name: workspace_user_resource_permission workspace_user_resource_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace_user_resource_permission
    ADD CONSTRAINT workspace_user_resource_permission_pkey PRIMARY KEY (id);


--
-- Name: application_access_token_access_token_3823531a_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_access_token_access_token_3823531a_like ON public.application_access_token USING btree (access_token varchar_pattern_ops);


--
-- Name: application_access_token_create_time_64979b17; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_access_token_create_time_64979b17 ON public.application_access_token USING btree (create_time);


--
-- Name: application_access_token_update_time_8e6632af; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_access_token_update_time_8e6632af ON public.application_access_token USING btree (update_time);


--
-- Name: application_api_key_application_id_376d9a01; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_api_key_application_id_376d9a01 ON public.application_api_key USING btree (application_id);


--
-- Name: application_api_key_create_time_0013df4c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_api_key_create_time_0013df4c ON public.application_api_key USING btree (create_time);


--
-- Name: application_api_key_secret_key_fd1b76e9_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_api_key_secret_key_fd1b76e9_like ON public.application_api_key USING btree (secret_key varchar_pattern_ops);


--
-- Name: application_api_key_update_time_ce7b0d9b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_api_key_update_time_ce7b0d9b ON public.application_api_key USING btree (update_time);


--
-- Name: application_api_key_workspace_id_01fbdbc0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_api_key_workspace_id_01fbdbc0 ON public.application_api_key USING btree (workspace_id);


--
-- Name: application_api_key_workspace_id_01fbdbc0_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_api_key_workspace_id_01fbdbc0_like ON public.application_api_key USING btree (workspace_id varchar_pattern_ops);


--
-- Name: application_applica_1652ba_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_applica_1652ba_idx ON public.application_chat_user_stats USING btree (application_id, chat_user_id);


--
-- Name: application_applica_7a56a7_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_applica_7a56a7_idx ON public.application_long_term_memory USING btree (application_id, chat_user_id);


--
-- Name: application_chat_application_id_0c9f6b90; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_application_id_0c9f6b90 ON public.application_chat USING btree (application_id);


--
-- Name: application_chat_create_time_ebb5f9d3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_create_time_ebb5f9d3 ON public.application_chat USING btree (create_time);


--
-- Name: application_chat_record_chat_id_21aeb7ef; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_record_chat_id_21aeb7ef ON public.application_chat_record USING btree (chat_id);


--
-- Name: application_chat_record_create_time_8878f099; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_record_create_time_8878f099 ON public.application_chat_record USING btree (create_time);


--
-- Name: application_chat_record_update_time_32fb05dc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_record_update_time_32fb05dc ON public.application_chat_record USING btree (update_time);


--
-- Name: application_chat_share_link_application_id_49c6403d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_share_link_application_id_49c6403d ON public.application_chat_share_link USING btree (application_id);


--
-- Name: application_chat_share_link_chat_id_8d8b6456; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_share_link_chat_id_8d8b6456 ON public.application_chat_share_link USING btree (chat_id);


--
-- Name: application_chat_share_link_create_time_84a2f494; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_share_link_create_time_84a2f494 ON public.application_chat_share_link USING btree (create_time);


--
-- Name: application_chat_share_link_update_time_8b535cf5; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_share_link_update_time_8b535cf5 ON public.application_chat_share_link USING btree (update_time);


--
-- Name: application_chat_share_link_user_id_5dc5097c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_share_link_user_id_5dc5097c ON public.application_chat_share_link USING btree (user_id);


--
-- Name: application_chat_update_time_f9735fce; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_update_time_f9735fce ON public.application_chat USING btree (update_time);


--
-- Name: application_chat_user_stats_application_id_2080bbf7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_user_stats_application_id_2080bbf7 ON public.application_chat_user_stats USING btree (application_id);


--
-- Name: application_chat_user_stats_create_time_32742378; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_user_stats_create_time_32742378 ON public.application_chat_user_stats USING btree (create_time);


--
-- Name: application_chat_user_stats_update_time_0e9f4d3b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_chat_user_stats_update_time_0e9f4d3b ON public.application_chat_user_stats USING btree (update_time);


--
-- Name: application_create_time_ee39f1ea; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_create_time_ee39f1ea ON public.application USING btree (create_time);


--
-- Name: application_folder_create_time_69889312; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_create_time_69889312 ON public.application_folder USING btree (create_time);


--
-- Name: application_folder_id_0d598f52; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_id_0d598f52 ON public.application USING btree (folder_id);


--
-- Name: application_folder_id_0d598f52_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_id_0d598f52_like ON public.application USING btree (folder_id varchar_pattern_ops);


--
-- Name: application_folder_id_bdb97e27_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_id_bdb97e27_like ON public.application_folder USING btree (id varchar_pattern_ops);


--
-- Name: application_folder_name_d221e0c2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_name_d221e0c2 ON public.application_folder USING btree (name);


--
-- Name: application_folder_name_d221e0c2_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_name_d221e0c2_like ON public.application_folder USING btree (name varchar_pattern_ops);


--
-- Name: application_folder_parent_id_b82d1c52; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_parent_id_b82d1c52 ON public.application_folder USING btree (parent_id);


--
-- Name: application_folder_parent_id_b82d1c52_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_parent_id_b82d1c52_like ON public.application_folder USING btree (parent_id varchar_pattern_ops);


--
-- Name: application_folder_tree_id_e467c15b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_tree_id_e467c15b ON public.application_folder USING btree (tree_id);


--
-- Name: application_folder_update_time_078e64d2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_update_time_078e64d2 ON public.application_folder USING btree (update_time);


--
-- Name: application_folder_user_id_45def139; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_user_id_45def139 ON public.application_folder USING btree (user_id);


--
-- Name: application_folder_workspace_id_753461f7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_workspace_id_753461f7 ON public.application_folder USING btree (workspace_id);


--
-- Name: application_folder_workspace_id_753461f7_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_folder_workspace_id_753461f7_like ON public.application_folder USING btree (workspace_id varchar_pattern_ops);


--
-- Name: application_knowledge_mapping_application_id_784ccbaf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_knowledge_mapping_application_id_784ccbaf ON public.application_knowledge_mapping USING btree (application_id);


--
-- Name: application_knowledge_mapping_create_time_b5b82de1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_knowledge_mapping_create_time_b5b82de1 ON public.application_knowledge_mapping USING btree (create_time);


--
-- Name: application_knowledge_mapping_knowledge_id_767ec6f1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_knowledge_mapping_knowledge_id_767ec6f1 ON public.application_knowledge_mapping USING btree (knowledge_id);


--
-- Name: application_knowledge_mapping_update_time_5d8dc346; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_knowledge_mapping_update_time_5d8dc346 ON public.application_knowledge_mapping USING btree (update_time);


--
-- Name: application_long_term_memory_application_id_cebbbeea; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_long_term_memory_application_id_cebbbeea ON public.application_long_term_memory USING btree (application_id);


--
-- Name: application_long_term_memory_chat_user_id_f0c804ca; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_long_term_memory_chat_user_id_f0c804ca ON public.application_long_term_memory USING btree (chat_user_id);


--
-- Name: application_long_term_memory_chat_user_id_f0c804ca_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_long_term_memory_chat_user_id_f0c804ca_like ON public.application_long_term_memory USING btree (chat_user_id varchar_pattern_ops);


--
-- Name: application_long_term_memory_create_time_09279212; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_long_term_memory_create_time_09279212 ON public.application_long_term_memory USING btree (create_time);


--
-- Name: application_long_term_memory_update_time_11820ff2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_long_term_memory_update_time_11820ff2 ON public.application_long_term_memory USING btree (update_time);


--
-- Name: application_long_term_model_id_d4500da7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_long_term_model_id_d4500da7 ON public.application USING btree (long_term_model_id);


--
-- Name: application_model_id_e80b5b34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_model_id_e80b5b34 ON public.application USING btree (model_id);


--
-- Name: application_name_b2d4898f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_name_b2d4898f ON public.application USING btree (name);


--
-- Name: application_name_b2d4898f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_name_b2d4898f_like ON public.application USING btree (name varchar_pattern_ops);


--
-- Name: application_setting_id_de129745_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_setting_id_de129745_like ON public.application_setting USING btree (id varchar_pattern_ops);


--
-- Name: application_stt_model_id_10e736db; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_stt_model_id_10e736db ON public.application USING btree (stt_model_id);


--
-- Name: application_tts_model_id_63215f2e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_tts_model_id_63215f2e ON public.application USING btree (tts_model_id);


--
-- Name: application_update_time_1ef68ba2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_update_time_1ef68ba2 ON public.application USING btree (update_time);


--
-- Name: application_user_id_e0323977; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_user_id_e0323977 ON public.application USING btree (user_id);


--
-- Name: application_version_application_id_ee35744a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_version_application_id_ee35744a ON public.application_version USING btree (application_id);


--
-- Name: application_version_create_time_d37c6d5c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_version_create_time_d37c6d5c ON public.application_version USING btree (create_time);


--
-- Name: application_version_update_time_c6e2da69; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_version_update_time_c6e2da69 ON public.application_version USING btree (update_time);


--
-- Name: application_version_user_id_61a6abb2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_version_user_id_61a6abb2 ON public.application_version USING btree (user_id);


--
-- Name: application_version_workspace_id_cc3b81bf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_version_workspace_id_cc3b81bf ON public.application_version USING btree (workspace_id);


--
-- Name: application_version_workspace_id_cc3b81bf_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_version_workspace_id_cc3b81bf_like ON public.application_version USING btree (workspace_id varchar_pattern_ops);


--
-- Name: application_workspace_id_43da6674; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_workspace_id_43da6674 ON public.application USING btree (workspace_id);


--
-- Name: application_workspace_id_43da6674_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_workspace_id_43da6674_like ON public.application USING btree (workspace_id varchar_pattern_ops);


--
-- Name: chat_auth_setting_auth_type_13ab0604_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_auth_setting_auth_type_13ab0604_like ON public.chat_auth_setting USING btree (auth_type varchar_pattern_ops);


--
-- Name: chat_auth_setting_create_time_5267d1bd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_auth_setting_create_time_5267d1bd ON public.chat_auth_setting USING btree (create_time);


--
-- Name: chat_platform_auth_type_9ac6f177_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_platform_auth_type_9ac6f177_like ON public.chat_platform USING btree (auth_type varchar_pattern_ops);


--
-- Name: chat_platform_id_942bd9e5_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_platform_id_942bd9e5_like ON public.chat_platform USING btree (id varchar_pattern_ops);


--
-- Name: chat_platform_is_active_e29f11f7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_platform_is_active_e29f11f7 ON public.chat_platform USING btree (is_active);


--
-- Name: chat_platform_is_valid_77760718; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_platform_is_valid_77760718 ON public.chat_platform USING btree (is_valid);


--
-- Name: chat_user_create_time_04d18e13; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_create_time_04d18e13 ON public.chat_user USING btree (create_time);


--
-- Name: chat_user_email_9db37d4b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_email_9db37d4b ON public.chat_user USING btree (email);


--
-- Name: chat_user_email_9db37d4b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_email_9db37d4b_like ON public.chat_user USING btree (email varchar_pattern_ops);


--
-- Name: chat_user_is_active_c3391505; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_is_active_c3391505 ON public.chat_user USING btree (is_active);


--
-- Name: chat_user_nick_name_9f856cf5_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_nick_name_9f856cf5_like ON public.chat_user USING btree (nick_name varchar_pattern_ops);


--
-- Name: chat_user_source_4957074b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_source_4957074b ON public.chat_user USING btree (source);


--
-- Name: chat_user_source_4957074b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_source_4957074b_like ON public.chat_user USING btree (source varchar_pattern_ops);


--
-- Name: chat_user_update_time_d6b6010c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_update_time_d6b6010c ON public.chat_user USING btree (update_time);


--
-- Name: chat_user_username_7c2763ef_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chat_user_username_7c2763ef_like ON public.chat_user USING btree (username varchar_pattern_ops);


--
-- Name: django_apscheduler_djangojob_next_run_time_2f022619; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_apscheduler_djangojob_next_run_time_2f022619 ON public.django_apscheduler_djangojob USING btree (next_run_time);


--
-- Name: django_apscheduler_djangojobexecution_job_id_daf5090a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_apscheduler_djangojobexecution_job_id_daf5090a ON public.django_apscheduler_djangojobexecution USING btree (job_id);


--
-- Name: django_apscheduler_djangojobexecution_run_time_16edd96b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_apscheduler_djangojobexecution_run_time_16edd96b ON public.django_apscheduler_djangojobexecution USING btree (run_time);


--
-- Name: django_celery_beat_periodictask_clocked_id_47a69f82; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_celery_beat_periodictask_clocked_id_47a69f82 ON public.django_celery_beat_periodictask USING btree (clocked_id);


--
-- Name: django_celery_beat_periodictask_crontab_id_d3cba168; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_celery_beat_periodictask_crontab_id_d3cba168 ON public.django_celery_beat_periodictask USING btree (crontab_id);


--
-- Name: django_celery_beat_periodictask_interval_id_a8ca27da; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_celery_beat_periodictask_interval_id_a8ca27da ON public.django_celery_beat_periodictask USING btree (interval_id);


--
-- Name: django_celery_beat_periodictask_name_265a36b7_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_celery_beat_periodictask_name_265a36b7_like ON public.django_celery_beat_periodictask USING btree (name varchar_pattern_ops);


--
-- Name: django_celery_beat_periodictask_solar_id_a87ce72c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_celery_beat_periodictask_solar_id_a87ce72c ON public.django_celery_beat_periodictask USING btree (solar_id);


--
-- Name: document_create_time_5168c411; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_create_time_5168c411 ON public.document USING btree (create_time);


--
-- Name: document_is_active_ab67f847; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_is_active_ab67f847 ON public.document USING btree (is_active);


--
-- Name: document_knowledge_id_419c566f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_knowledge_id_419c566f ON public.document USING btree (knowledge_id);


--
-- Name: document_name_8eb44882; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_name_8eb44882 ON public.document USING btree (name);


--
-- Name: document_name_8eb44882_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_name_8eb44882_like ON public.document USING btree (name varchar_pattern_ops);


--
-- Name: document_status_a4cf573b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_status_a4cf573b ON public.document USING btree (status);


--
-- Name: document_status_a4cf573b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_status_a4cf573b_like ON public.document USING btree (status varchar_pattern_ops);


--
-- Name: document_tag_create_time_4ef5590c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_tag_create_time_4ef5590c ON public.document_tag USING btree (create_time);


--
-- Name: document_tag_document_id_953cb93d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_tag_document_id_953cb93d ON public.document_tag USING btree (document_id);


--
-- Name: document_tag_tag_id_acaa7b3b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_tag_tag_id_acaa7b3b ON public.document_tag USING btree (tag_id);


--
-- Name: document_tag_update_time_2c460bdf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_tag_update_time_2c460bdf ON public.document_tag USING btree (update_time);


--
-- Name: document_type_7fb9c2c3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_type_7fb9c2c3 ON public.document USING btree (type);


--
-- Name: document_update_time_4e517386; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_update_time_4e517386 ON public.document USING btree (update_time);


--
-- Name: document_user_id_9e7ccb71; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX document_user_id_9e7ccb71 ON public.document USING btree (user_id);


--
-- Name: embedding_document_id_3c89d1f3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_document_id_3c89d1f3 ON public.embedding USING btree (document_id);


--
-- Name: embedding_id_f61adc5f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_id_f61adc5f_like ON public.embedding USING btree (id varchar_pattern_ops);


--
-- Name: embedding_knowledge_id_00e08fa7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_knowledge_id_00e08fa7 ON public.embedding USING btree (knowledge_id);


--
-- Name: embedding_paragraph_id_9f39681c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_paragraph_id_9f39681c ON public.embedding USING btree (paragraph_id);


--
-- Name: embedding_search_vector_gin_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_search_vector_gin_idx ON public.embedding USING gin (search_vector);


--
-- Name: embedding_source_id_60f7e2f4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_source_id_60f7e2f4 ON public.embedding USING btree (source_id);


--
-- Name: embedding_source_id_60f7e2f4_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_source_id_60f7e2f4_like ON public.embedding USING btree (source_id varchar_pattern_ops);


--
-- Name: embedding_source_type_23488528; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_source_type_23488528 ON public.embedding USING btree (source_type);


--
-- Name: embedding_source_type_23488528_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX embedding_source_type_23488528_like ON public.embedding USING btree (source_type varchar_pattern_ops);


--
-- Name: event_trigger_create_time_72037f02; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_create_time_72037f02 ON public.event_trigger USING btree (create_time);


--
-- Name: event_trigger_is_active_59ad09bf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_is_active_59ad09bf ON public.event_trigger USING btree (is_active);


--
-- Name: event_trigger_name_463b9244; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_name_463b9244 ON public.event_trigger USING btree (name);


--
-- Name: event_trigger_name_463b9244_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_name_463b9244_like ON public.event_trigger USING btree (name varchar_pattern_ops);


--
-- Name: event_trigger_task_create_time_ea019477; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_create_time_ea019477 ON public.event_trigger_task USING btree (create_time);


--
-- Name: event_trigger_task_is_active_fb6a8ed7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_is_active_fb6a8ed7 ON public.event_trigger_task USING btree (is_active);


--
-- Name: event_trigger_task_record_create_time_da67dbbf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_record_create_time_da67dbbf ON public.event_trigger_task_record USING btree (create_time);


--
-- Name: event_trigger_task_record_trigger_id_e2820298; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_record_trigger_id_e2820298 ON public.event_trigger_task_record USING btree (trigger_id);


--
-- Name: event_trigger_task_record_update_time_0085d148; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_record_update_time_0085d148 ON public.event_trigger_task_record USING btree (update_time);


--
-- Name: event_trigger_task_trigger_id_fe513725; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_trigger_id_fe513725 ON public.event_trigger_task USING btree (trigger_id);


--
-- Name: event_trigger_task_update_time_f61d2e08; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_task_update_time_f61d2e08 ON public.event_trigger_task USING btree (update_time);


--
-- Name: event_trigger_update_time_8b613ce6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_update_time_8b613ce6 ON public.event_trigger USING btree (update_time);


--
-- Name: event_trigger_user_id_fa647614; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_user_id_fa647614 ON public.event_trigger USING btree (user_id);


--
-- Name: event_trigger_workspace_id_a19f6584; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_workspace_id_a19f6584 ON public.event_trigger USING btree (workspace_id);


--
-- Name: event_trigger_workspace_id_a19f6584_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX event_trigger_workspace_id_a19f6584_like ON public.event_trigger USING btree (workspace_id varchar_pattern_ops);


--
-- Name: file_create_time_940439ad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_create_time_940439ad ON public.file USING btree (create_time);


--
-- Name: file_source_id_f68d803c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_source_id_f68d803c ON public.file USING btree (source_id);


--
-- Name: file_source_id_f68d803c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_source_id_f68d803c_like ON public.file USING btree (source_id varchar_pattern_ops);


--
-- Name: file_source_type_aae7b5e3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_source_type_aae7b5e3 ON public.file USING btree (source_type);


--
-- Name: file_source_type_aae7b5e3_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_source_type_aae7b5e3_like ON public.file USING btree (source_type varchar_pattern_ops);


--
-- Name: file_update_time_e55a692a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX file_update_time_e55a692a ON public.file USING btree (update_time);


--
-- Name: knowledge_action_create_time_e8782fff; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_action_create_time_e8782fff ON public.knowledge_action USING btree (create_time);


--
-- Name: knowledge_action_knowledge_id_8c71df84; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_action_knowledge_id_8c71df84 ON public.knowledge_action USING btree (knowledge_id);


--
-- Name: knowledge_action_update_time_b7da00ac; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_action_update_time_b7da00ac ON public.knowledge_action USING btree (update_time);


--
-- Name: knowledge_create_time_73058bbd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_create_time_73058bbd ON public.knowledge USING btree (create_time);


--
-- Name: knowledge_embedding_model_id_d8ebfba0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_embedding_model_id_d8ebfba0 ON public.knowledge USING btree (embedding_model_id);


--
-- Name: knowledge_folder_create_time_9f79917a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_create_time_9f79917a ON public.knowledge_folder USING btree (create_time);


--
-- Name: knowledge_folder_id_c2644e2c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_id_c2644e2c ON public.knowledge USING btree (folder_id);


--
-- Name: knowledge_folder_id_c2644e2c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_id_c2644e2c_like ON public.knowledge USING btree (folder_id varchar_pattern_ops);


--
-- Name: knowledge_folder_id_d2636e62_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_id_d2636e62_like ON public.knowledge_folder USING btree (id varchar_pattern_ops);


--
-- Name: knowledge_folder_name_ab2c51ae; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_name_ab2c51ae ON public.knowledge_folder USING btree (name);


--
-- Name: knowledge_folder_name_ab2c51ae_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_name_ab2c51ae_like ON public.knowledge_folder USING btree (name varchar_pattern_ops);


--
-- Name: knowledge_folder_parent_id_88bfda49; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_parent_id_88bfda49 ON public.knowledge_folder USING btree (parent_id);


--
-- Name: knowledge_folder_parent_id_88bfda49_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_parent_id_88bfda49_like ON public.knowledge_folder USING btree (parent_id varchar_pattern_ops);


--
-- Name: knowledge_folder_tree_id_a575de4c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_tree_id_a575de4c ON public.knowledge_folder USING btree (tree_id);


--
-- Name: knowledge_folder_update_time_14aa2e30; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_update_time_14aa2e30 ON public.knowledge_folder USING btree (update_time);


--
-- Name: knowledge_folder_user_id_48c7f505; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_user_id_48c7f505 ON public.knowledge_folder USING btree (user_id);


--
-- Name: knowledge_folder_workspace_id_23488b49; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_workspace_id_23488b49 ON public.knowledge_folder USING btree (workspace_id);


--
-- Name: knowledge_folder_workspace_id_23488b49_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_folder_workspace_id_23488b49_like ON public.knowledge_folder USING btree (workspace_id varchar_pattern_ops);


--
-- Name: knowledge_name_41f67f24; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_name_41f67f24 ON public.knowledge USING btree (name);


--
-- Name: knowledge_name_41f67f24_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_name_41f67f24_like ON public.knowledge USING btree (name varchar_pattern_ops);


--
-- Name: knowledge_scope_c8877d39; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_scope_c8877d39 ON public.knowledge USING btree (scope);


--
-- Name: knowledge_scope_c8877d39_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_scope_c8877d39_like ON public.knowledge USING btree (scope varchar_pattern_ops);


--
-- Name: knowledge_type_7a89fb9d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_type_7a89fb9d ON public.knowledge USING btree (type);


--
-- Name: knowledge_update_time_588f12b8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_update_time_588f12b8 ON public.knowledge USING btree (update_time);


--
-- Name: knowledge_user_id_18293b47; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_user_id_18293b47 ON public.knowledge USING btree (user_id);


--
-- Name: knowledge_workflow_create_time_3d79e7e6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_create_time_3d79e7e6 ON public.knowledge_workflow USING btree (create_time);


--
-- Name: knowledge_workflow_is_publish_74629d52; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_is_publish_74629d52 ON public.knowledge_workflow USING btree (is_publish);


--
-- Name: knowledge_workflow_update_time_1036d552; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_update_time_1036d552 ON public.knowledge_workflow USING btree (update_time);


--
-- Name: knowledge_workflow_version_create_time_10b25ccb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_version_create_time_10b25ccb ON public.knowledge_workflow_version USING btree (create_time);


--
-- Name: knowledge_workflow_version_knowledge_id_34bf3175; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_version_knowledge_id_34bf3175 ON public.knowledge_workflow_version USING btree (knowledge_id);


--
-- Name: knowledge_workflow_version_update_time_3f96de1d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_version_update_time_3f96de1d ON public.knowledge_workflow_version USING btree (update_time);


--
-- Name: knowledge_workflow_version_workspace_id_d4df3903; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_version_workspace_id_d4df3903 ON public.knowledge_workflow_version USING btree (workspace_id);


--
-- Name: knowledge_workflow_version_workspace_id_d4df3903_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_version_workspace_id_d4df3903_like ON public.knowledge_workflow_version USING btree (workspace_id varchar_pattern_ops);


--
-- Name: knowledge_workflow_workspace_id_79c20e29; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_workspace_id_79c20e29 ON public.knowledge_workflow USING btree (workspace_id);


--
-- Name: knowledge_workflow_workspace_id_79c20e29_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workflow_workspace_id_79c20e29_like ON public.knowledge_workflow USING btree (workspace_id varchar_pattern_ops);


--
-- Name: knowledge_workspace_id_795138c3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workspace_id_795138c3 ON public.knowledge USING btree (workspace_id);


--
-- Name: knowledge_workspace_id_795138c3_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX knowledge_workspace_id_795138c3_like ON public.knowledge USING btree (workspace_id varchar_pattern_ops);


--
-- Name: log_create_time_44520a52; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_create_time_44520a52 ON public.log USING btree (create_time);


--
-- Name: log_operate_bb4f8ada; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_operate_bb4f8ada ON public.log USING btree (operate);


--
-- Name: log_operate_bb4f8ada_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_operate_bb4f8ada_like ON public.log USING btree (operate varchar_pattern_ops);


--
-- Name: log_status_77474674; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_status_77474674 ON public.log USING btree (status);


--
-- Name: log_update_time_a65e7f1e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_update_time_a65e7f1e ON public.log USING btree (update_time);


--
-- Name: log_workspace_id_3f8e9902; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_workspace_id_3f8e9902 ON public.log USING btree (workspace_id);


--
-- Name: log_workspace_id_3f8e9902_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX log_workspace_id_3f8e9902_like ON public.log USING btree (workspace_id varchar_pattern_ops);


--
-- Name: model_create_time_c34d0337; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_create_time_c34d0337 ON public.model USING btree (create_time);


--
-- Name: model_model_name_c1d139d8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_model_name_c1d139d8 ON public.model USING btree (model_name);


--
-- Name: model_model_name_c1d139d8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_model_name_c1d139d8_like ON public.model USING btree (model_name varchar_pattern_ops);


--
-- Name: model_model_type_b693061b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_model_type_b693061b ON public.model USING btree (model_type);


--
-- Name: model_model_type_b693061b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_model_type_b693061b_like ON public.model USING btree (model_type varchar_pattern_ops);


--
-- Name: model_name_1f9cfbc9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_name_1f9cfbc9 ON public.model USING btree (name);


--
-- Name: model_name_1f9cfbc9_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_name_1f9cfbc9_like ON public.model USING btree (name varchar_pattern_ops);


--
-- Name: model_provider_cdbe3bf6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_provider_cdbe3bf6 ON public.model USING btree (provider);


--
-- Name: model_provider_cdbe3bf6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_provider_cdbe3bf6_like ON public.model USING btree (provider varchar_pattern_ops);


--
-- Name: model_status_e8e46844; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_status_e8e46844 ON public.model USING btree (status);


--
-- Name: model_status_e8e46844_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_status_e8e46844_like ON public.model USING btree (status varchar_pattern_ops);


--
-- Name: model_update_time_11b3490c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_update_time_11b3490c ON public.model USING btree (update_time);


--
-- Name: model_user_id_a841bfc8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_user_id_a841bfc8 ON public.model USING btree (user_id);


--
-- Name: model_workspace_id_1edf80e5; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_workspace_id_1edf80e5 ON public.model USING btree (workspace_id);


--
-- Name: model_workspace_id_1edf80e5_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX model_workspace_id_1edf80e5_like ON public.model USING btree (workspace_id varchar_pattern_ops);


--
-- Name: paragraph_create_time_521ed7f0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_create_time_521ed7f0 ON public.paragraph USING btree (create_time);


--
-- Name: paragraph_document_id_2e0722cc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_document_id_2e0722cc ON public.paragraph USING btree (document_id);


--
-- Name: paragraph_is_active_d6ea683a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_is_active_d6ea683a ON public.paragraph USING btree (is_active);


--
-- Name: paragraph_knowledge_id_4adce37e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_knowledge_id_4adce37e ON public.paragraph USING btree (knowledge_id);


--
-- Name: paragraph_position_00aa9a2f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_position_00aa9a2f ON public.paragraph USING btree ("position");


--
-- Name: paragraph_status_ebef6bfe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_status_ebef6bfe ON public.paragraph USING btree (status);


--
-- Name: paragraph_status_ebef6bfe_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_status_ebef6bfe_like ON public.paragraph USING btree (status varchar_pattern_ops);


--
-- Name: paragraph_title_57663bca; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_title_57663bca ON public.paragraph USING btree (title);


--
-- Name: paragraph_title_57663bca_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_title_57663bca_like ON public.paragraph USING btree (title varchar_pattern_ops);


--
-- Name: paragraph_update_time_0e8da622; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX paragraph_update_time_0e8da622 ON public.paragraph USING btree (update_time);


--
-- Name: platform_display_setting_create_time_73008bbc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX platform_display_setting_create_time_73008bbc ON public.platform_display_setting USING btree (create_time);


--
-- Name: platform_display_setting_id_15c39485_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX platform_display_setting_id_15c39485_like ON public.platform_display_setting USING btree (id varchar_pattern_ops);


--
-- Name: problem_content_93727706; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_content_93727706 ON public.problem USING btree (content);


--
-- Name: problem_content_93727706_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_content_93727706_like ON public.problem USING btree (content varchar_pattern_ops);


--
-- Name: problem_create_time_3a2d1421; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_create_time_3a2d1421 ON public.problem USING btree (create_time);


--
-- Name: problem_knowledge_id_656d8e09; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_knowledge_id_656d8e09 ON public.problem USING btree (knowledge_id);


--
-- Name: problem_paragraph_mapping_create_time_30dae711; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_paragraph_mapping_create_time_30dae711 ON public.problem_paragraph_mapping USING btree (create_time);


--
-- Name: problem_paragraph_mapping_document_id_74b9f617; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_paragraph_mapping_document_id_74b9f617 ON public.problem_paragraph_mapping USING btree (document_id);


--
-- Name: problem_paragraph_mapping_knowledge_id_84e4e42a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_paragraph_mapping_knowledge_id_84e4e42a ON public.problem_paragraph_mapping USING btree (knowledge_id);


--
-- Name: problem_paragraph_mapping_paragraph_id_f0be2e98; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_paragraph_mapping_paragraph_id_f0be2e98 ON public.problem_paragraph_mapping USING btree (paragraph_id);


--
-- Name: problem_paragraph_mapping_problem_id_937b9858; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_paragraph_mapping_problem_id_937b9858 ON public.problem_paragraph_mapping USING btree (problem_id);


--
-- Name: problem_paragraph_mapping_update_time_677e4106; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_paragraph_mapping_update_time_677e4106 ON public.problem_paragraph_mapping USING btree (update_time);


--
-- Name: problem_update_time_16392c6e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX problem_update_time_16392c6e ON public.problem USING btree (update_time);


--
-- Name: public_file_access_create_time_c322ec98; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_access_create_time_c322ec98 ON public.public_file_access USING btree (create_time);


--
-- Name: public_file_access_source_id_6d3fa282; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_access_source_id_6d3fa282 ON public.public_file_access USING btree (source_id);


--
-- Name: public_file_access_source_id_6d3fa282_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_access_source_id_6d3fa282_like ON public.public_file_access USING btree (source_id varchar_pattern_ops);


--
-- Name: public_file_access_source_type_a345336c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_access_source_type_a345336c ON public.public_file_access USING btree (source_type);


--
-- Name: public_file_access_source_type_a345336c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_access_source_type_a345336c_like ON public.public_file_access USING btree (source_type varchar_pattern_ops);


--
-- Name: public_file_access_update_time_a5dd6071; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_access_update_time_a5dd6071 ON public.public_file_access USING btree (update_time);


--
-- Name: public_file_source__a961f4_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX public_file_source__a961f4_idx ON public.public_file_access USING btree (source_type, source_id);


--
-- Name: resource_chat_user_authorize_resource_id_efef323e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_resource_id_efef323e ON public.resource_chat_user_authorize USING btree (resource_id);


--
-- Name: resource_chat_user_authorize_resource_type_dfd85ed2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_resource_type_dfd85ed2 ON public.resource_chat_user_authorize USING btree (resource_type);


--
-- Name: resource_chat_user_authorize_resource_type_dfd85ed2_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_resource_type_dfd85ed2_like ON public.resource_chat_user_authorize USING btree (resource_type varchar_pattern_ops);


--
-- Name: resource_chat_user_authorize_user_group_id_5f3021d3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_user_group_id_5f3021d3 ON public.resource_chat_user_authorize USING btree (user_group_id);


--
-- Name: resource_chat_user_authorize_user_group_id_5f3021d3_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_user_group_id_5f3021d3_like ON public.resource_chat_user_authorize USING btree (user_group_id varchar_pattern_ops);


--
-- Name: resource_chat_user_authorize_user_id_326419b7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_user_id_326419b7 ON public.resource_chat_user_authorize USING btree (user_id);


--
-- Name: resource_chat_user_authorize_workspace_id_515407f9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_workspace_id_515407f9 ON public.resource_chat_user_authorize USING btree (workspace_id);


--
-- Name: resource_chat_user_authorize_workspace_id_515407f9_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_authorize_workspace_id_515407f9_like ON public.resource_chat_user_authorize USING btree (workspace_id varchar_pattern_ops);


--
-- Name: resource_chat_user_group_authorize_resource_id_25ffb4f9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_resource_id_25ffb4f9 ON public.resource_chat_user_group_authorize USING btree (resource_id);


--
-- Name: resource_chat_user_group_authorize_resource_type_91c5cda5; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_resource_type_91c5cda5 ON public.resource_chat_user_group_authorize USING btree (resource_type);


--
-- Name: resource_chat_user_group_authorize_resource_type_91c5cda5_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_resource_type_91c5cda5_like ON public.resource_chat_user_group_authorize USING btree (resource_type varchar_pattern_ops);


--
-- Name: resource_chat_user_group_authorize_user_group_id_3798efb8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_user_group_id_3798efb8 ON public.resource_chat_user_group_authorize USING btree (user_group_id);


--
-- Name: resource_chat_user_group_authorize_user_group_id_3798efb8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_user_group_id_3798efb8_like ON public.resource_chat_user_group_authorize USING btree (user_group_id varchar_pattern_ops);


--
-- Name: resource_chat_user_group_authorize_workspace_id_b75c61b5; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_workspace_id_b75c61b5 ON public.resource_chat_user_group_authorize USING btree (workspace_id);


--
-- Name: resource_chat_user_group_authorize_workspace_id_b75c61b5_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_chat_user_group_authorize_workspace_id_b75c61b5_like ON public.resource_chat_user_group_authorize USING btree (workspace_id varchar_pattern_ops);


--
-- Name: resource_mapping_create_time_bda4e392; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_create_time_bda4e392 ON public.resource_mapping USING btree (create_time);


--
-- Name: resource_mapping_source_id_4ea1216b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_source_id_4ea1216b ON public.resource_mapping USING btree (source_id);


--
-- Name: resource_mapping_source_id_4ea1216b_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_source_id_4ea1216b_like ON public.resource_mapping USING btree (source_id varchar_pattern_ops);


--
-- Name: resource_mapping_source_type_65569047; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_source_type_65569047 ON public.resource_mapping USING btree (source_type);


--
-- Name: resource_mapping_source_type_65569047_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_source_type_65569047_like ON public.resource_mapping USING btree (source_type varchar_pattern_ops);


--
-- Name: resource_mapping_target_id_6e1f2685; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_target_id_6e1f2685 ON public.resource_mapping USING btree (target_id);


--
-- Name: resource_mapping_target_id_6e1f2685_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_target_id_6e1f2685_like ON public.resource_mapping USING btree (target_id varchar_pattern_ops);


--
-- Name: resource_mapping_target_type_85c62bbb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_target_type_85c62bbb ON public.resource_mapping USING btree (target_type);


--
-- Name: resource_mapping_target_type_85c62bbb_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_target_type_85c62bbb_like ON public.resource_mapping USING btree (target_type varchar_pattern_ops);


--
-- Name: resource_mapping_update_time_1c3672d3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX resource_mapping_update_time_1c3672d3 ON public.resource_mapping USING btree (update_time);


--
-- Name: role_permission_permission_id_ee9c5982; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_permission_permission_id_ee9c5982 ON public.role_permission USING btree (permission_id);


--
-- Name: role_permission_permission_id_ee9c5982_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_permission_permission_id_ee9c5982_like ON public.role_permission USING btree (permission_id varchar_pattern_ops);


--
-- Name: role_permission_role_id_877a80a4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_permission_role_id_877a80a4 ON public.role_permission USING btree (role_id);


--
-- Name: role_permission_role_id_877a80a4_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_permission_role_id_877a80a4_like ON public.role_permission USING btree (role_id varchar_pattern_ops);


--
-- Name: role_setting_create_time_c94535ed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_create_time_c94535ed ON public.role_setting USING btree (create_time);


--
-- Name: role_setting_create_user_id_6b445527; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_create_user_id_6b445527 ON public.role_setting USING btree (create_user_id);


--
-- Name: role_setting_id_77e4dc9c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_id_77e4dc9c_like ON public.role_setting USING btree (id varchar_pattern_ops);


--
-- Name: role_setting_internal_efb75f8b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_internal_efb75f8b ON public.role_setting USING btree (internal);


--
-- Name: role_setting_role_name_d08bc838; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_role_name_d08bc838 ON public.role_setting USING btree (role_name);


--
-- Name: role_setting_role_name_d08bc838_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_role_name_d08bc838_like ON public.role_setting USING btree (role_name varchar_pattern_ops);


--
-- Name: role_setting_type_96416659; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_type_96416659 ON public.role_setting USING btree (type);


--
-- Name: role_setting_type_96416659_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX role_setting_type_96416659_like ON public.role_setting USING btree (type varchar_pattern_ops);


--
-- Name: shared_resource_workspac_resource_type_7c2189b7_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX shared_resource_workspac_resource_type_7c2189b7_like ON public.shared_resource_workspace_authorization USING btree (resource_type varchar_pattern_ops);


--
-- Name: shared_resource_workspace_authorization_create_time_1911b445; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX shared_resource_workspace_authorization_create_time_1911b445 ON public.shared_resource_workspace_authorization USING btree (create_time);


--
-- Name: shared_resource_workspace_authorization_id_782f59e4_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX shared_resource_workspace_authorization_id_782f59e4_like ON public.shared_resource_workspace_authorization USING btree (id varchar_pattern_ops);


--
-- Name: shared_resource_workspace_authorization_resource_type_7c2189b7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX shared_resource_workspace_authorization_resource_type_7c2189b7 ON public.shared_resource_workspace_authorization USING btree (resource_type);


--
-- Name: system_api_key_create_time_7ca80d97; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX system_api_key_create_time_7ca80d97 ON public.system_api_key USING btree (create_time);


--
-- Name: system_api_key_is_active_69a5ddbb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX system_api_key_is_active_69a5ddbb ON public.system_api_key USING btree (is_active);


--
-- Name: system_api_key_secret_key_cc2faff6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX system_api_key_secret_key_cc2faff6_like ON public.system_api_key USING btree (secret_key varchar_pattern_ops);


--
-- Name: system_api_key_user_id_cd4d9463; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX system_api_key_user_id_cd4d9463 ON public.system_api_key USING btree (user_id);


--
-- Name: system_setting_create_time_7c21ded3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX system_setting_create_time_7c21ded3 ON public.system_setting USING btree (create_time);


--
-- Name: system_setting_update_time_a3d325d1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX system_setting_update_time_a3d325d1 ON public.system_setting USING btree (update_time);


--
-- Name: tag_create_time_36d78b7c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_create_time_36d78b7c ON public.tag USING btree (create_time);


--
-- Name: tag_key_08a35336; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_key_08a35336 ON public.tag USING btree (key);


--
-- Name: tag_key_08a35336_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_key_08a35336_like ON public.tag USING btree (key varchar_pattern_ops);


--
-- Name: tag_knowled_cba590_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_knowled_cba590_idx ON public.tag USING btree (knowledge_id, key);


--
-- Name: tag_knowledge_id_5816b5de; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_knowledge_id_5816b5de ON public.tag USING btree (knowledge_id);


--
-- Name: tag_update_time_928c2700; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_update_time_928c2700 ON public.tag USING btree (update_time);


--
-- Name: tag_value_0d236690; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_value_0d236690 ON public.tag USING btree (value);


--
-- Name: tag_value_0d236690_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tag_value_0d236690_like ON public.tag USING btree (value varchar_pattern_ops);


--
-- Name: termbase_content_5cb3da68; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX termbase_content_5cb3da68 ON public.termbase USING btree (content);


--
-- Name: termbase_content_5cb3da68_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX termbase_content_5cb3da68_like ON public.termbase USING btree (content varchar_pattern_ops);


--
-- Name: termbase_create_time_c46bd6cc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX termbase_create_time_c46bd6cc ON public.termbase USING btree (create_time);


--
-- Name: termbase_knowledge_id_fe5e8d87; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX termbase_knowledge_id_fe5e8d87 ON public.termbase USING btree (knowledge_id);


--
-- Name: termbase_update_time_68470b36; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX termbase_update_time_68470b36 ON public.termbase USING btree (update_time);


--
-- Name: tool_create_time_e0880b81; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_create_time_e0880b81 ON public.tool USING btree (create_time);


--
-- Name: tool_folder_create_time_2a019328; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_create_time_2a019328 ON public.tool_folder USING btree (create_time);


--
-- Name: tool_folder_id_940ad233_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_id_940ad233_like ON public.tool_folder USING btree (id varchar_pattern_ops);


--
-- Name: tool_folder_id_ecc041f8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_id_ecc041f8 ON public.tool USING btree (folder_id);


--
-- Name: tool_folder_id_ecc041f8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_id_ecc041f8_like ON public.tool USING btree (folder_id varchar_pattern_ops);


--
-- Name: tool_folder_name_d6438754; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_name_d6438754 ON public.tool_folder USING btree (name);


--
-- Name: tool_folder_name_d6438754_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_name_d6438754_like ON public.tool_folder USING btree (name varchar_pattern_ops);


--
-- Name: tool_folder_parent_id_cbcf6a00; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_parent_id_cbcf6a00 ON public.tool_folder USING btree (parent_id);


--
-- Name: tool_folder_parent_id_cbcf6a00_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_parent_id_cbcf6a00_like ON public.tool_folder USING btree (parent_id varchar_pattern_ops);


--
-- Name: tool_folder_tree_id_60fc41dd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_tree_id_60fc41dd ON public.tool_folder USING btree (tree_id);


--
-- Name: tool_folder_update_time_ba9be14e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_update_time_ba9be14e ON public.tool_folder USING btree (update_time);


--
-- Name: tool_folder_user_id_be38331b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_user_id_be38331b ON public.tool_folder USING btree (user_id);


--
-- Name: tool_folder_workspace_id_20b66b15; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_workspace_id_20b66b15 ON public.tool_folder USING btree (workspace_id);


--
-- Name: tool_folder_workspace_id_20b66b15_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_folder_workspace_id_20b66b15_like ON public.tool_folder USING btree (workspace_id varchar_pattern_ops);


--
-- Name: tool_is_active_f3d326d1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_is_active_f3d326d1 ON public.tool USING btree (is_active);


--
-- Name: tool_label_66e517a8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_label_66e517a8 ON public.tool USING btree (label);


--
-- Name: tool_label_66e517a8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_label_66e517a8_like ON public.tool USING btree (label varchar_pattern_ops);


--
-- Name: tool_name_ec029465; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_name_ec029465 ON public.tool USING btree (name);


--
-- Name: tool_name_ec029465_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_name_ec029465_like ON public.tool USING btree (name varchar_pattern_ops);


--
-- Name: tool_record_create_time_0e96de5e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_record_create_time_0e96de5e ON public.tool_record USING btree (create_time);


--
-- Name: tool_record_tool_id_32995d93; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_record_tool_id_32995d93 ON public.tool_record USING btree (tool_id);


--
-- Name: tool_record_update_time_3ef56090; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_record_update_time_3ef56090 ON public.tool_record USING btree (update_time);


--
-- Name: tool_record_workspace_id_88320155; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_record_workspace_id_88320155 ON public.tool_record USING btree (workspace_id);


--
-- Name: tool_record_workspace_id_88320155_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_record_workspace_id_88320155_like ON public.tool_record USING btree (workspace_id varchar_pattern_ops);


--
-- Name: tool_scope_6387be58; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_scope_6387be58 ON public.tool USING btree (scope);


--
-- Name: tool_scope_6387be58_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_scope_6387be58_like ON public.tool USING btree (scope varchar_pattern_ops);


--
-- Name: tool_template_id_717d147f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_template_id_717d147f ON public.tool USING btree (template_id);


--
-- Name: tool_tool_type_204cdc98; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_tool_type_204cdc98 ON public.tool USING btree (tool_type);


--
-- Name: tool_tool_type_204cdc98_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_tool_type_204cdc98_like ON public.tool USING btree (tool_type varchar_pattern_ops);


--
-- Name: tool_update_time_2e4efd57; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_update_time_2e4efd57 ON public.tool USING btree (update_time);


--
-- Name: tool_user_id_fd36dfa4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_user_id_fd36dfa4 ON public.tool USING btree (user_id);


--
-- Name: tool_workflow_create_time_cb25a2c6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_create_time_cb25a2c6 ON public.tool_workflow USING btree (create_time);


--
-- Name: tool_workflow_is_publish_d8c55450; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_is_publish_d8c55450 ON public.tool_workflow USING btree (is_publish);


--
-- Name: tool_workflow_update_time_afd5559b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_update_time_afd5559b ON public.tool_workflow USING btree (update_time);


--
-- Name: tool_workflow_version_create_time_8a513673; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_version_create_time_8a513673 ON public.tool_workflow_version USING btree (create_time);


--
-- Name: tool_workflow_version_tool_id_b4671e40; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_version_tool_id_b4671e40 ON public.tool_workflow_version USING btree (tool_id);


--
-- Name: tool_workflow_version_update_time_6daf9080; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_version_update_time_6daf9080 ON public.tool_workflow_version USING btree (update_time);


--
-- Name: tool_workflow_version_workspace_id_e99217f6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_version_workspace_id_e99217f6 ON public.tool_workflow_version USING btree (workspace_id);


--
-- Name: tool_workflow_version_workspace_id_e99217f6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_version_workspace_id_e99217f6_like ON public.tool_workflow_version USING btree (workspace_id varchar_pattern_ops);


--
-- Name: tool_workflow_workspace_id_6700c059; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_workspace_id_6700c059 ON public.tool_workflow USING btree (workspace_id);


--
-- Name: tool_workflow_workspace_id_6700c059_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workflow_workspace_id_6700c059_like ON public.tool_workflow USING btree (workspace_id varchar_pattern_ops);


--
-- Name: tool_workspace_id_bf0fd790; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workspace_id_bf0fd790 ON public.tool USING btree (workspace_id);


--
-- Name: tool_workspace_id_bf0fd790_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tool_workspace_id_bf0fd790_like ON public.tool USING btree (workspace_id varchar_pattern_ops);


--
-- Name: user_create_time_d69e5f54; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_create_time_d69e5f54 ON public."user" USING btree (create_time);


--
-- Name: user_email_54dc62b2_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_email_54dc62b2_like ON public."user" USING btree (email varchar_pattern_ops);


--
-- Name: user_group_id_9e420a50_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_group_id_9e420a50_like ON public.user_group USING btree (id varchar_pattern_ops);


--
-- Name: user_group_name_d36097b4_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_group_name_d36097b4_like ON public.user_group USING btree (name varchar_pattern_ops);


--
-- Name: user_group_relation_group_id_8ee53fb6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_group_relation_group_id_8ee53fb6 ON public.user_group_relation USING btree (group_id);


--
-- Name: user_group_relation_group_id_8ee53fb6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_group_relation_group_id_8ee53fb6_like ON public.user_group_relation USING btree (group_id varchar_pattern_ops);


--
-- Name: user_group_relation_user_id_0a38580e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_group_relation_user_id_0a38580e ON public.user_group_relation USING btree (user_id);


--
-- Name: user_is_active_74579245; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_is_active_74579245 ON public."user" USING btree (is_active);


--
-- Name: user_nick_name_580ea5e6_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_nick_name_580ea5e6_like ON public."user" USING btree (nick_name varchar_pattern_ops);


--
-- Name: user_phone_fcd7f7da; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_phone_fcd7f7da ON public."user" USING btree (phone);


--
-- Name: user_phone_fcd7f7da_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_phone_fcd7f7da_like ON public."user" USING btree (phone varchar_pattern_ops);


--
-- Name: user_role_relation_role_id_e55c1c54; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_role_relation_role_id_e55c1c54 ON public.user_role_relation USING btree (role_id);


--
-- Name: user_role_relation_role_id_e55c1c54_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_role_relation_role_id_e55c1c54_like ON public.user_role_relation USING btree (role_id varchar_pattern_ops);


--
-- Name: user_role_relation_user_id_0df4472b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_role_relation_user_id_0df4472b ON public.user_role_relation USING btree (user_id);


--
-- Name: user_role_relation_workspace_id_d2bebed7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_role_relation_workspace_id_d2bebed7 ON public.user_role_relation USING btree (workspace_id);


--
-- Name: user_role_relation_workspace_id_d2bebed7_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_role_relation_workspace_id_d2bebed7_like ON public.user_role_relation USING btree (workspace_id varchar_pattern_ops);


--
-- Name: user_source_51744f77; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_source_51744f77 ON public."user" USING btree (source);


--
-- Name: user_source_51744f77_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_source_51744f77_like ON public."user" USING btree (source varchar_pattern_ops);


--
-- Name: user_update_time_ccf08206; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_update_time_ccf08206 ON public."user" USING btree (update_time);


--
-- Name: user_username_cf016618_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_username_cf016618_like ON public."user" USING btree (username varchar_pattern_ops);


--
-- Name: workspace_create_time_1d030cbe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_create_time_1d030cbe ON public.workspace USING btree (create_time);


--
-- Name: workspace_create_user_id_3ef6501e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_create_user_id_3ef6501e ON public.workspace USING btree (create_user_id);


--
-- Name: workspace_id_76599053_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_id_76599053_like ON public.workspace USING btree (id varchar_pattern_ops);


--
-- Name: workspace_name_cff03e24_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_name_cff03e24_like ON public.workspace USING btree (name varchar_pattern_ops);


--
-- Name: workspace_user_resource__auth_target_type_33deef7a_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource__auth_target_type_33deef7a_like ON public.workspace_user_resource_permission USING btree (auth_target_type varchar_pattern_ops);


--
-- Name: workspace_user_resource_permission_auth_target_type_33deef7a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_auth_target_type_33deef7a ON public.workspace_user_resource_permission USING btree (auth_target_type);


--
-- Name: workspace_user_resource_permission_auth_type_43a49931; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_auth_type_43a49931 ON public.workspace_user_resource_permission USING btree (auth_type);


--
-- Name: workspace_user_resource_permission_auth_type_43a49931_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_auth_type_43a49931_like ON public.workspace_user_resource_permission USING btree (auth_type varchar_pattern_ops);


--
-- Name: workspace_user_resource_permission_create_time_d3397f88; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_create_time_d3397f88 ON public.workspace_user_resource_permission USING btree (create_time);


--
-- Name: workspace_user_resource_permission_target_d0c6532f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_target_d0c6532f ON public.workspace_user_resource_permission USING btree (target);


--
-- Name: workspace_user_resource_permission_update_time_f944478e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_update_time_f944478e ON public.workspace_user_resource_permission USING btree (update_time);


--
-- Name: workspace_user_resource_permission_user_id_623d7674; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_user_id_623d7674 ON public.workspace_user_resource_permission USING btree (user_id);


--
-- Name: workspace_user_resource_permission_workspace_id_6d34f020; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_workspace_id_6d34f020 ON public.workspace_user_resource_permission USING btree (workspace_id);


--
-- Name: workspace_user_resource_permission_workspace_id_6d34f020_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX workspace_user_resource_permission_workspace_id_6d34f020_like ON public.workspace_user_resource_permission USING btree (workspace_id varchar_pattern_ops);


--
-- Name: application_access_token application_access_t_application_id_d90b8cec_fk_applicati; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_access_token
    ADD CONSTRAINT application_access_t_application_id_d90b8cec_fk_applicati FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_api_key application_api_key_application_id_376d9a01_fk_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_api_key
    ADD CONSTRAINT application_api_key_application_id_376d9a01_fk_application_id FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_chat application_chat_application_id_0c9f6b90_fk_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat
    ADD CONSTRAINT application_chat_application_id_0c9f6b90_fk_application_id FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_chat_record application_chat_record_chat_id_21aeb7ef_fk_application_chat_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_record
    ADD CONSTRAINT application_chat_record_chat_id_21aeb7ef_fk_application_chat_id FOREIGN KEY (chat_id) REFERENCES public.application_chat(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_chat_share_link application_chat_sha_application_id_49c6403d_fk_applicati; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_share_link
    ADD CONSTRAINT application_chat_sha_application_id_49c6403d_fk_applicati FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_chat_share_link application_chat_sha_chat_id_8d8b6456_fk_applicati; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_share_link
    ADD CONSTRAINT application_chat_sha_chat_id_8d8b6456_fk_applicati FOREIGN KEY (chat_id) REFERENCES public.application_chat(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_chat_user_stats application_chat_use_application_id_2080bbf7_fk_applicati; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_chat_user_stats
    ADD CONSTRAINT application_chat_use_application_id_2080bbf7_fk_applicati FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application application_folder_id_0d598f52_fk_application_folder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application
    ADD CONSTRAINT application_folder_id_0d598f52_fk_application_folder_id FOREIGN KEY (folder_id) REFERENCES public.application_folder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_folder application_folder_parent_id_b82d1c52_fk_application_folder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_folder
    ADD CONSTRAINT application_folder_parent_id_b82d1c52_fk_application_folder_id FOREIGN KEY (parent_id) REFERENCES public.application_folder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_knowledge_mapping application_knowledg_application_id_784ccbaf_fk_applicati; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_knowledge_mapping
    ADD CONSTRAINT application_knowledg_application_id_784ccbaf_fk_applicati FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_knowledge_mapping application_knowledg_knowledge_id_767ec6f1_fk_knowledge; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_knowledge_mapping
    ADD CONSTRAINT application_knowledg_knowledge_id_767ec6f1_fk_knowledge FOREIGN KEY (knowledge_id) REFERENCES public.knowledge(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_setting application_setting_application_id_50f30183_fk_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_setting
    ADD CONSTRAINT application_setting_application_id_50f30183_fk_application_id FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: application_version application_version_application_id_ee35744a_fk_application_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_version
    ADD CONSTRAINT application_version_application_id_ee35744a_fk_application_id FOREIGN KEY (application_id) REFERENCES public.application(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_apscheduler_djangojobexecution django_apscheduler_djangojobexecution_job_id_daf5090a_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_apscheduler_djangojobexecution
    ADD CONSTRAINT django_apscheduler_djangojobexecution_job_id_daf5090a_fk FOREIGN KEY (job_id) REFERENCES public.django_apscheduler_djangojob(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_clocked_id_47a69f82_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_clocked_id_47a69f82_fk_django_ce FOREIGN KEY (clocked_id) REFERENCES public.django_celery_beat_clockedschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_crontab_id_d3cba168_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_crontab_id_d3cba168_fk_django_ce FOREIGN KEY (crontab_id) REFERENCES public.django_celery_beat_crontabschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_interval_id_a8ca27da_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_interval_id_a8ca27da_fk_django_ce FOREIGN KEY (interval_id) REFERENCES public.django_celery_beat_intervalschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_solar_id_a87ce72c_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_solar_id_a87ce72c_fk_django_ce FOREIGN KEY (solar_id) REFERENCES public.django_celery_beat_solarschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: document document_knowledge_id_419c566f_fk_knowledge_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document
    ADD CONSTRAINT document_knowledge_id_419c566f_fk_knowledge_id FOREIGN KEY (knowledge_id) REFERENCES public.knowledge(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: event_trigger_task_record event_trigger_task_r_trigger_id_e2820298_fk_event_tri; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_trigger_task_record
    ADD CONSTRAINT event_trigger_task_r_trigger_id_e2820298_fk_event_tri FOREIGN KEY (trigger_id) REFERENCES public.event_trigger(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: event_trigger_task event_trigger_task_trigger_id_fe513725_fk_event_trigger_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_trigger_task
    ADD CONSTRAINT event_trigger_task_trigger_id_fe513725_fk_event_trigger_id FOREIGN KEY (trigger_id) REFERENCES public.event_trigger(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: knowledge knowledge_folder_id_c2644e2c_fk_knowledge_folder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge
    ADD CONSTRAINT knowledge_folder_id_c2644e2c_fk_knowledge_folder_id FOREIGN KEY (folder_id) REFERENCES public.knowledge_folder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: knowledge_folder knowledge_folder_parent_id_88bfda49_fk_knowledge_folder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_folder
    ADD CONSTRAINT knowledge_folder_parent_id_88bfda49_fk_knowledge_folder_id FOREIGN KEY (parent_id) REFERENCES public.knowledge_folder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: paragraph paragraph_knowledge_id_4adce37e_fk_knowledge_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paragraph
    ADD CONSTRAINT paragraph_knowledge_id_4adce37e_fk_knowledge_id FOREIGN KEY (knowledge_id) REFERENCES public.knowledge(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: resource_chat_user_authorize resource_chat_user_a_user_group_id_5f3021d3_fk_user_grou; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_authorize
    ADD CONSTRAINT resource_chat_user_a_user_group_id_5f3021d3_fk_user_grou FOREIGN KEY (user_group_id) REFERENCES public.user_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: resource_chat_user_authorize resource_chat_user_authorize_user_id_326419b7_fk_chat_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_authorize
    ADD CONSTRAINT resource_chat_user_authorize_user_id_326419b7_fk_chat_user_id FOREIGN KEY (user_id) REFERENCES public.chat_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: resource_chat_user_group_authorize resource_chat_user_g_user_group_id_3798efb8_fk_user_grou; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_chat_user_group_authorize
    ADD CONSTRAINT resource_chat_user_g_user_group_id_3798efb8_fk_user_grou FOREIGN KEY (user_group_id) REFERENCES public.user_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: role_permission role_permission_role_id_877a80a4_fk_role_setting_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permission
    ADD CONSTRAINT role_permission_role_id_877a80a4_fk_role_setting_id FOREIGN KEY (role_id) REFERENCES public.role_setting(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: role_setting role_setting_create_user_id_6b445527_fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_setting
    ADD CONSTRAINT role_setting_create_user_id_6b445527_fk_user_id FOREIGN KEY (create_user_id) REFERENCES public."user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: system_api_key system_api_key_user_id_cd4d9463_fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_api_key
    ADD CONSTRAINT system_api_key_user_id_cd4d9463_fk_user_id FOREIGN KEY (user_id) REFERENCES public."user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tool tool_folder_id_ecc041f8_fk_tool_folder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool
    ADD CONSTRAINT tool_folder_id_ecc041f8_fk_tool_folder_id FOREIGN KEY (folder_id) REFERENCES public.tool_folder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tool_folder tool_folder_parent_id_cbcf6a00_fk_tool_folder_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_folder
    ADD CONSTRAINT tool_folder_parent_id_cbcf6a00_fk_tool_folder_id FOREIGN KEY (parent_id) REFERENCES public.tool_folder(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tool_record tool_record_tool_id_32995d93_fk_tool_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_record
    ADD CONSTRAINT tool_record_tool_id_32995d93_fk_tool_id FOREIGN KEY (tool_id) REFERENCES public.tool(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_group_relation user_group_relation_group_id_8ee53fb6_fk_user_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_group_relation
    ADD CONSTRAINT user_group_relation_group_id_8ee53fb6_fk_user_group_id FOREIGN KEY (group_id) REFERENCES public.user_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_group_relation user_group_relation_user_id_0a38580e_fk_chat_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_group_relation
    ADD CONSTRAINT user_group_relation_user_id_0a38580e_fk_chat_user_id FOREIGN KEY (user_id) REFERENCES public.chat_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_role_relation user_role_relation_role_id_e55c1c54_fk_role_setting_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role_relation
    ADD CONSTRAINT user_role_relation_role_id_e55c1c54_fk_role_setting_id FOREIGN KEY (role_id) REFERENCES public.role_setting(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_role_relation user_role_relation_user_id_0df4472b_fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role_relation
    ADD CONSTRAINT user_role_relation_user_id_0df4472b_fk_user_id FOREIGN KEY (user_id) REFERENCES public."user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_role_relation user_role_relation_workspace_id_d2bebed7_fk_workspace_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role_relation
    ADD CONSTRAINT user_role_relation_workspace_id_d2bebed7_fk_workspace_id FOREIGN KEY (workspace_id) REFERENCES public.workspace(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspace workspace_create_user_id_3ef6501e_fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace
    ADD CONSTRAINT workspace_create_user_id_3ef6501e_fk_user_id FOREIGN KEY (create_user_id) REFERENCES public."user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspace_user_resource_permission workspace_user_resource_permission_user_id_623d7674_fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace_user_resource_permission
    ADD CONSTRAINT workspace_user_resource_permission_user_id_623d7674_fk_user_id FOREIGN KEY (user_id) REFERENCES public."user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict hgfa6Scol4LPZvhulSYGENjQa9lmTB6Gpm8YknXbdnb3LWUFj8s2N6AXXEzoWRU

