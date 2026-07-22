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
    leads: (params?: { limit?: number; offset?: number; status?: string }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      if (params?.status) q.set("status", params.status);
      return get<DivarLeadsResponse>(`/divar/leads?${q}`);
    },
    logs: (lines?: number) => get<{ lines: string[] }>(`/divar/logs?lines=${lines ?? 100}`),
    run: (body: DivarRunRequest) => post<DivarRunResponse>("/divar/run", body),
    sendLog: (limit?: number) => get<{ items: DivarSendLog[] }>(`/divar/send-log?limit=${limit ?? 50}`),
  },
};

export interface DivarStats {
  total_leads: number; synced: number; messages_sent: number; pending: number; failed: number;
}
export interface DivarLead {
  id: number; title: string; seller_name: string; phone: string; city: string;
  district: string; price_text: string; extraction_status: string; message_sent: number;
  message_status: string; sync_status: string; source_url: string; created_at: string;
}
export interface DivarLeadsResponse { items: DivarLead[]; total: number; }
export interface DivarRunRequest { url: string; send_messages?: boolean; no_ai?: boolean; }
export interface DivarRunResponse { started: boolean; pid: number; cmd: string; }
export interface DivarSendLog {
  id: number; lead_id: number; phone: string; message_text: string;
  status: string; error_msg: string; sent_at: string;
}
