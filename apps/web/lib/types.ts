export type AlertItem = {
  id: string;
  child_name: string;
  severity: "HIGH" | "MEDIUM" | string;
  created_at: string;
  mode?: string | null;
  trigger_summary?: string | null;
  parent_viewed: boolean;
};

export type AlertDetail = AlertItem & {
  child_id: string;
  conversation_id?: string | null;
  category: string;
  status: string;
  details?: string | null;
  parent_notified: boolean;
  conversation_status?: string | null;
};

export type ChildProfile = {
  id: string;
  name: string;
  nickname?: string | null;
  pronouns?: string | null;
  comfort_notes?: string | null;
  is_active: boolean;
};

export type ConversationStartResponse = {
  conversation_id: string;
  status: string;
};

export type ConversationMessageResponse = {
  conversation_id: string;
  response_text: string;
  audio_url?: string | null;
  audio_content_type?: string | null;
  liveavatar_enabled: boolean;
  liveavatar_session_required: boolean;
  liveavatar_audio_stream_url?: string | null;
  risk_level: string;
  risk_reason: string;
  trigger_parent_alert: boolean;
  use_emergency_flow: boolean;
};

export type ConversationSummary = {
  id: string;
  child_id: string;
  helper_profile_id?: string | null;
  status: string;
  highest_risk_level?: string | null;
  messages: Array<{
    sender_role: string;
    content: string;
    safety_level?: string | null;
    created_at: string;
  }>;
};

export type ComfortMode = {
  id: string;
  child_id: string;
  mode_name: string;
  name: string;
  script?: string | null;
  routine_prompt?: string | null;
  active: boolean;
  safety_status: "pending" | "approved" | "failed" | string;
  parent_approval_status: "pending" | "approved" | string;
};

export type ParentProfile = {
  id: string;
  display_name: string;
  phone?: string | null;
  timezone: string;
  consent_given: boolean;
};

export type User = {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
};

export type MeResponse = {
  user: User;
  parent_id?: string | null;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type HelperProfile = {
  id: string;
  parent_id: string;
  child_id: string;
  label: string;
  description?: string | null;
  status: string;
  approved_at?: string | null;
  paused_at?: string | null;
};

export type AvatarResponse = {
  id: string;
  status: string;
  original_image_key?: string | null;
  approved_for_child_use?: boolean;
  liveavatar_avatar_id?: string | null;
  liveavatar_status?: string;
};

export type VoiceResponse = {
  id: string;
  status: string;
  provider_voice_id?: string | null;
  approved_for_child_use?: boolean;
  signed_url?: string;
};

export type AdminAlertItem = {
  id: string;
  child_id: string;
  child_label: string;
  severity: "HIGH" | "MEDIUM" | string;
  created_at: string;
  trigger_summary?: string | null;
  mode?: string | null;
  parent_viewed: boolean;
};

export type AdminAuditLogItem = {
  id: string;
  created_at: string;
  actor_user_id?: string | null;
  actor_email?: string | null;
  action: string;
  metadata_summary?: string | null;
  ip_address?: string | null;
};

export type AdminUserItem = {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export type AdminSystemHealth = {
  status: string;
  uptime_seconds: number;
  database: string;
};

export type LiveAvatarSession = {
  session_id: string;
  embed_url?: string | null;
  sdk_token?: string | null;
  expires_at?: string | null;
  mock: boolean;
};

export type LiveAvatarConfigureResponse = {
  avatar_id: string;
  status: string;
};

export type LiveAvatarSpeakResponse = {
  accepted: boolean;
  mode: string;
  message: string;
};
