import type {
  AdminAlertItem,
  AdminAuditLogItem,
  AdminSystemHealth,
  AdminUserItem,
  AlertDetail,
  AlertItem,
  AvatarResponse,
  ChildProfile,
  ComfortMode,
  ConversationMessageResponse,
  ConversationStartResponse,
  ConversationSummary,
  HelperProfile,
  LiveAvatarConfigureResponse,
  LiveAvatarSession,
  LiveAvatarSpeakResponse,
  MeResponse,
  ParentProfile,
  TokenResponse,
  VoiceResponse
} from "@/lib/types";

export type ApiErrorPayload = {
  detail?: string;
  message?: string;
};

export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload | unknown;

  constructor(status: number, payload: ApiErrorPayload | unknown) {
    const message =
      typeof payload === "object" && payload && "detail" in payload
        ? String((payload as ApiErrorPayload).detail)
        : `Request failed with status ${status}`;
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let tokenGetter: (() => string | null) | null = null;
let unauthorizedHandler: (() => void) | null = null;

export function setAuthTokenGetter(getter: () => string | null) {
  tokenGetter = getter;
}

export function setUnauthorizedHandler(handler: () => void) {
  unauthorizedHandler = handler;
}

export type ApiRequestOptions = RequestInit & {
  authRedirect?: boolean;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  const token = tokenGetter?.();
  const { authRedirect = true, ...requestOptions } = options;

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const hasBody = options.body !== undefined;
  if (hasBody && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers
  });

  if (!response.ok) {
    const payload = await parseResponse(response);
    if ((response.status === 401 || response.status === 403) && authRedirect) {
      unauthorizedHandler?.();
    }
    throw new ApiError(response.status, payload);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await parseResponse(response)) as T;
}

export function apiGet<T>(path: string) {
  return apiRequest<T>(path);
}

export function apiPost<T>(path: string, body?: unknown, options: ApiRequestOptions = {}) {
  return apiRequest<T>(path, {
    ...options,
    method: "POST",
    body: body instanceof FormData ? body : JSON.stringify(body ?? {})
  });
}

export function apiPut<T>(path: string, body: unknown, options: ApiRequestOptions = {}) {
  return apiRequest<T>(path, {
    ...options,
    method: "PUT",
    body: JSON.stringify(body)
  });
}

export function apiDelete<T>(path: string, options: ApiRequestOptions = {}) {
  return apiRequest<T>(path, {
    ...options,
    method: "DELETE"
  });
}

export const api = {
  auth: {
    signup: (body: {
      email: string;
      password: string;
      display_name: string;
      phone?: string | null;
      timezone?: string;
    }) => apiPost<TokenResponse>("/auth/signup", body, { authRedirect: false }),
    login: (body: { email: string; password: string }) =>
      apiPost<TokenResponse>("/auth/login", body, { authRedirect: false }),
    logout: () => apiPost<{ detail: string }>("/auth/logout"),
    me: () => apiGet<MeResponse>("/auth/me")
  },
  parent: {
    getProfile: () => apiGet<ParentProfile>("/parent/profile"),
    updateProfile: (body: Partial<ParentProfile>) => apiPut<ParentProfile>("/parent/profile", body),
    consent: (privacy_acknowledged = true) =>
      apiPost<ParentProfile>("/parent/consent", { privacy_acknowledged })
  },
  children: {
    create: (body: Partial<ChildProfile>) => apiPost<ChildProfile>("/children", body),
    get: (id: string) => apiGet<ChildProfile>(`/children/${id}`),
    update: (id: string, body: Partial<ChildProfile>) => apiPut<ChildProfile>(`/children/${id}`, body),
    delete: (id: string) => apiDelete<void>(`/children/${id}`)
  },
  helperProfiles: {
    create: (body: { child_id: string; label: string; description?: string | null }) =>
      apiPost<HelperProfile>("/helper-profiles", body),
    get: (id: string) => apiGet<HelperProfile>(`/helper-profiles/${id}`),
    updateLabel: (id: string, label: string) =>
      apiPut<HelperProfile>(`/helper-profiles/${id}/label`, { label }),
    finalApprove: (id: string) => apiPost<HelperProfile>(`/helper-profiles/${id}/final-approve`),
    pause: (id: string) => apiPost<HelperProfile>(`/helper-profiles/${id}/pause`),
    delete: (id: string) => apiDelete<void>(`/helper-profiles/${id}`)
  },
  avatar: {
    consent: (consent_status = true) => apiPost("/avatar/consent", { consent_status }),
    upload: (image: File) => {
      const formData = new FormData();
      formData.append("image", image);
      return apiPost<AvatarResponse>("/avatar/upload", formData);
    },
    get: (id: string) => apiGet<{ id: string; signed_url: string; expires_in: number }>(`/avatar/${id}`),
    approve: (id: string) => apiPost<AvatarResponse>(`/avatar/${id}/approve`),
    delete: (id: string) => apiDelete<void>(`/avatar/${id}`)
  },
  voice: {
    uploadConsentRecording: (audio: File) => uploadVoiceFile("/voice/consent-recording", audio),
    uploadSampleRecording: (audio: File) => uploadVoiceFile("/voice/sample-recording", audio),
    createClone: () => apiPost<VoiceResponse>("/voice/create-clone"),
    preview: (id: string, text: string) =>
      apiPost<{ id: string; signed_url: string; expires_in: number }>(`/voice/${id}/preview`, { text }),
    approve: (id: string) => apiPost<VoiceResponse>(`/voice/${id}/approve`),
    delete: (id: string) => apiDelete<void>(`/voice/${id}`)
  },
  comfortModes: {
    list: (childId: string) => apiGet<ComfortMode[]>(`/children/${childId}/modes`),
    create: (childId: string, body: { mode_name: string; script?: string | null }) =>
      apiPost<{ id: string; safety_status: string; parent_approval_status: string }>(
        `/children/${childId}/modes`,
        body
      ),
    update: (id: string, body: { mode_name?: string; script?: string | null }) =>
      apiPut<ComfortMode>(`/modes/${id}`, body),
    delete: (id: string) => apiDelete<{ success: boolean }>(`/modes/${id}`),
    safetyCheck: (id: string) => apiPost<{ mode: ComfortMode; safe: boolean; reason: string }>(`/modes/${id}/safety-check`),
    approve: (id: string) => apiPost<ComfortMode>(`/modes/${id}/approve`)
  },
  alerts: {
    list: () => apiGet<AlertItem[]>("/alerts"),
    get: (id: string) => apiGet<AlertDetail>(`/alerts/${id}`),
    markViewed: (id: string) => apiPost<AlertDetail>(`/alerts/${id}/mark-viewed`)
  },
  conversation: {
    start: (body: { child_id: string; helper_profile_id?: string | null; mode: string }, authRedirect = true) =>
      apiPost<ConversationStartResponse>("/conversation/start", body, { authRedirect }),
    message: (
      body: {
        conversation_id: string;
        mode: string;
        text?: string;
        audio_base64?: string;
      },
      authRedirect = true
    ) => apiPost<ConversationMessageResponse>("/conversation/message", body, { authRedirect }),
    summary: (id: string) => apiGet<ConversationSummary>(`/conversation/${id}/summary`)
  },
  data: {
    export: () => apiGet<unknown>("/data/export"),
    requestDeletion: () => apiPost<{ detail: string }>("/data/delete-request"),
    deleteAccount: (confirmation_phrase: string) =>
      apiRequest<{ detail: string }>("/account", {
        method: "DELETE",
        body: JSON.stringify({ confirmation_phrase })
      })
  },
  liveAvatar: {
    configure: (avatar_id: string) =>
      apiPost<LiveAvatarConfigureResponse>("/liveavatar/configure", { avatar_id }),
    startSession: () => apiPost<LiveAvatarSession>("/liveavatar/session/start"),
    stopSession: (session_id?: string | null) =>
      apiPost<{ stopped: boolean }>("/liveavatar/session/stop", { session_id }),
    speak: (session_id: string, audio: Blob, contentType = "audio/wav") => {
      const formData = new FormData();
      const payload = audio.type ? audio : new Blob([audio], { type: contentType });
      formData.append("audio", payload, "response-audio.wav");
      return apiPost<LiveAvatarSpeakResponse>(
        `/liveavatar/session/speak?session_id=${encodeURIComponent(session_id)}`,
        formData
      );
    }
  },
  admin: {
    alerts: (params: {
      severity?: string;
      start_date?: string;
      end_date?: string;
      parent_viewed?: boolean;
      limit?: number;
      offset?: number;
    } = {}) => apiGet<AdminAlertItem[]>(`/admin/alerts${toQueryString(params)}`),
    auditLogs: (params: {
      user_id?: string;
      action?: string;
      start_date?: string;
      end_date?: string;
      limit?: number;
      offset?: number;
    } = {}) => apiGet<AdminAuditLogItem[]>(`/admin/audit-logs${toQueryString(params)}`),
    users: (params: {
      role?: string;
      start_date?: string;
      end_date?: string;
      limit?: number;
      offset?: number;
    } = {}) => apiGet<AdminUserItem[]>(`/admin/users${toQueryString(params)}`),
    systemHealth: () => apiGet<AdminSystemHealth>("/admin/system-health")
  }
};

function uploadVoiceFile(path: string, audio: File) {
  const formData = new FormData();
  formData.append("audio", audio);
  return apiPost<{ id: string; status: string; key: string }>(path, formData);
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function toQueryString(params: Record<string, string | number | boolean | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}
