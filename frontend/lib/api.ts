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

export const api = {
  health: () => get<{ status: string }>("/health"),
  divar: {
    stats: () => get<DivarStats>("/divar/stats"),
    sessionStatus: () => get<{
      logged_in: boolean;
      profile_path: string;
      session_files_found: number;
      numbered_profiles: {
        profile_id: string;
        reputation_score: number;
        success_count: number;
        failure_count: number;
        available: boolean;
      }[];
      login_instructions: string[];
    }>('/divar/session-status'),
    login: (phone: string) => post<{started: boolean; message: string}>('/divar/login', { phone }),
    leads: (params?: { limit?: number; offset?: number; status?: string }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      if (params?.status) q.set("status", params.status);
      return get<DivarLeadsResponse>(`/divar/leads?${q}`);
    },
    logs: (lines?: number) => get<{ lines: string[] }>(`/divar/logs?lines=${lines ?? 100}`),
    run: (body: DivarRunRequest) => post<RunResponse>("/divar/run", body),
    sendLog: (limit?: number) => get<{ items: DivarSendLog[] }>(`/divar/send-log?limit=${limit ?? 50}`),
  },
  torob: {
    stats: () => get<TorobStats>("/torob/stats"),
    sellers: (params?: { limit?: number; offset?: number; crawl_status?: string }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      if (params?.crawl_status) q.set("crawl_status", params.crawl_status);
      return get<TorobSellersResponse>(`/torob/sellers?${q}`);
    },
    reports: (params?: { limit?: number; offset?: number }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      return get<TorobReportsResponse>(`/torob/reports?${q}`);
    },
    logs: (lines?: number) => get<{ lines: string[] }>(`/torob/logs?lines=${lines ?? 100}`),
    run: (body: TorobRunRequest) => post<RunResponse>("/torob/run", body),
  },
};

// Divar types
export interface DivarStats { total_leads: number; synced: number; messages_sent: number; pending: number; failed: number; }
export interface DivarLead { id: number; title: string; seller_name: string; phone: string; city: string; district: string; price_text: string; extraction_status: string; message_sent: number; message_status: string; sync_status: string; source_url: string; created_at: string; }
export interface DivarLeadsResponse { items: DivarLead[]; total: number; }
export interface DivarRunRequest { url: string; send_messages?: boolean; no_ai?: boolean; }
export interface DivarSendLog { id: number; lead_id: number; phone: string; message_text: string; status: string; error_msg: string; sent_at: string; }

// Torob types
export interface TorobStats { total_sellers: number; synced: number; total_reports: number; total_history: number; }
export interface TorobSeller { id: number; store_name: string; phone: string; email: string; store_url: string; torob_url: string; price_on_torob: number; instagram: string; telegram: string; whatsapp: string; crawl_status: string; sync_status: string; created_at: string; }
export interface TorobSellersResponse { items: TorobSeller[]; total: number; }
export interface TorobReport { id: number; product_code: string; product_name: string; afrakala_price: number; lowest_rival: number; avg_rival: number; afrakala_rank: number; rival_count: number; diff_percent: number; sync_status: string; created_at: string; }
export interface TorobReportsResponse { items: TorobReport[]; total: number; }
export interface TorobRunRequest { query: string; }
export interface RunResponse { started: boolean; pid: number; cmd: string; }
