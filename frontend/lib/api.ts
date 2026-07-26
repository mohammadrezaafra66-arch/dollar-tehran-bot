const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  health: () => get<{ status: string }>("/health"),

  divar: {
    stats: () => get<DivarStats>("/divar/stats"),
    leads: (p?: { limit?: number; offset?: number; status?: string; city?: string; message_sent?: string }) => {
      const q = new URLSearchParams();
      if (p?.limit) q.set("limit", String(p.limit));
      if (p?.offset) q.set("offset", String(p.offset));
      if (p?.status) q.set("status", p.status);
      if (p?.city) q.set("city", p.city);
      if (p?.message_sent) q.set("message_sent", p.message_sent);
      return get<DivarLeadsResponse>(`/divar/leads?${q}`);
    },
    logs: (lines?: number) => get<{ lines: string[] }>(`/divar/logs?lines=${lines ?? 100}`),
    run: (body: DivarRunRequest) => post<RunResponse>("/divar/run", body),
    runStatus: () => get<RunStatus>("/divar/run/status"),
    runStop: () => post<{ stopped: boolean }>("/divar/run/stop", {}),
    sendLog: (limit?: number) => get<{ items: DivarSendLog[] }>(`/divar/send-log?limit=${limit ?? 50}`),
    accounts: () => get<{ items: DivarAccount[] }>("/divar/accounts"),
    loginStart: (profileId: string, phone: string) =>
      post<{ started: boolean; process_key: string }>(`/divar/accounts/${profileId}/login/start`, { phone }),
    loginOtp: (profileId: string, otp: string) =>
      post<{ sent: boolean }>(`/divar/accounts/${profileId}/login/otp`, { otp }),
    loginStatus: (profileId: string) =>
      get<LoginStatus>(`/divar/accounts/${profileId}/login/status`),
    checkLogin: (profileId: string) =>
      get<{ likely_logged_in: boolean; phone: string; cookies_size: number }>(`/divar/accounts/${profileId}/check-login`),
    savePhone: (profileId: string, phone: string) =>
      post<{ saved: boolean }>(`/divar/accounts/${profileId}/save-phone`, { phone }),
    deleteAccount: (profileId: string) =>
      del<{ deleted: boolean }>(`/divar/accounts/${profileId}`),
    config: () => get<DivarConfig>("/divar/config"),
    saveConfig: (body: Partial<DivarConfig>) => post<{ saved: boolean }>("/divar/config", body),
    template: () => get<{ template: string }>("/divar/template"),
    saveTemplate: (template: string) => post<{ saved: boolean }>("/divar/template", { template }),
    aiStats: () => get<DivarAIStats>("/divar/ai/stats"),
    aiRun: () => post<{ started: boolean }>("/divar/ai/run", {}),
    exports: () => get<{ items: ExportItem[] }>("/divar/exports"),
    export: () => get<{ file: string }>("/divar/export"),
  },

  torob: {
    stats: () => get<TorobStats>("/torob/stats"),
    sellers: (p?: { limit?: number; offset?: number; crawl_status?: string }) => {
      const q = new URLSearchParams();
      if (p?.limit) q.set("limit", String(p.limit));
      if (p?.offset) q.set("offset", String(p.offset));
      if (p?.crawl_status) q.set("crawl_status", p.crawl_status);
      return get<TorobSellersResponse>(`/torob/sellers?${q}`);
    },
    sellerDetail: (id: number) => get<TorobSeller>(`/torob/sellers/${id}`),
    reports: (p?: { limit?: number; offset?: number }) => {
      const q = new URLSearchParams();
      if (p?.limit) q.set("limit", String(p.limit));
      if (p?.offset) q.set("offset", String(p.offset));
      return get<TorobReportsResponse>(`/torob/reports?${q}`);
    },
    logs: (lines?: number) => get<{ lines: string[] }>(`/torob/logs?lines=${lines ?? 100}`),
    run: (body: TorobRunRequest) => post<RunResponse>("/torob/run", body),
    runStatus: () => get<RunStatus>("/torob/run/status"),
    runStop: () => post<{ stopped: boolean }>("/torob/run/stop", {}),
    config: () => get<TorobConfig>("/torob/config"),
    saveConfig: (body: Partial<TorobConfig>) => post<{ saved: boolean }>("/torob/config", body),
    exports: () => get<{ items: ExportItem[] }>("/torob/exports"),
    export: () => get<{ file: string }>("/torob/export"),
  },
};

// ─── Shared types ────────────────────────────────────────────
export interface RunResponse { started: boolean; pid: number; cmd: string; }
export interface RunStatus { running: boolean; pid: number | null; output: string[]; }
export interface ExportItem { name: string; path: string; size: number; modified: string; }

// ─── Divar types ─────────────────────────────────────────────
export interface DivarStats {
  total_leads: number; synced: number; messages_sent: number; pending: number; failed: number;
}
export interface DivarLead {
  id: number; title: string; seller_name: string; phone: string; city: string;
  district: string; price_text: string; extraction_status: string; message_sent: number;
  message_status: string; sync_status: string; source_url: string; ai_analysis: string;
  created_at: string;
  profile_id: string;
}
export interface DivarLeadsResponse { items: DivarLead[]; total: number; }
export interface DivarRunRequest { url: string; send_messages?: boolean; no_ai?: boolean; profile_id?: string; }
export interface DivarSendLog {
  id: number; lead_id: number; phone: string; message_text: string;
  status: string; error_msg: string; sent_at: string;
}
export interface DivarAccount {
  profile_id: string; reputation_score: number; success_count: number;
  failure_count: number; available: boolean; cooldown_until: number;
  last_used_at: number; has_session_files: boolean;
}
export interface LoginStatus { running: boolean; output: string[]; success: boolean; }
export interface DivarConfig {
  DIVAR_MAX_ADS_PER_RUN: string; DIVAR_DAILY_MESSAGE_LIMIT: string;
  DIVAR_MIN_DELAY_SECONDS: string; DIVAR_MAX_DELAY_SECONDS: string;
  DIVAR_PROFILE_DIR: string; DIVAR_PROFILE_COUNT: string;
  HTTP_PROXY: string; DEEPSEEK_API_KEY: string; AFRA_API_URL: string;
}
export interface DivarAIStats { total: number; analyzed: number; pending: number; failed: number; }

// ─── Torob types ─────────────────────────────────────────────
export interface TorobStats { total_sellers: number; synced: number; total_reports: number; total_history: number; }
export interface TorobSeller {
  id: number; store_name: string; phone: string; email: string; store_url: string;
  torob_url: string; price_on_torob: number; instagram: string; telegram: string;
  whatsapp: string; crawl_status: string; sync_status: string; created_at: string;
}
export interface TorobSellersResponse { items: TorobSeller[]; total: number; }
export interface TorobReport {
  id: number; product_code: string; product_name: string; afrakala_price: number;
  lowest_rival: number; avg_rival: number; afrakala_rank: number; rival_count: number;
  diff_percent: number; sync_status: string; created_at: string;
}
export interface TorobReportsResponse { items: TorobReport[]; total: number; }
export interface TorobRunRequest { query: string; }
export interface TorobConfig {
  AFRA_API_URL: string; AFRA_API_KEY: string; TOROB_MIN_DELAY_SECONDS: string;
  TOROB_MAX_DELAY_SECONDS: string; TOROB_MAX_SELLERS_PER_URL: string;
  SELLER_CRAWL_TIMEOUT_SECONDS: string; CRAWL_SELLER_SITES: string;
}
