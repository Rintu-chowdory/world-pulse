export type EventCategory =
  | "earthquake"
  | "wildfire"
  | "flood"
  | "storm"
  | "volcano";

export type EventSeverity = "critical" | "warning" | "advisory" | "normal";

export interface PulseEvent {
  id: string;
  category: EventCategory;
  severity: EventSeverity;
  title: string;
  location: string;
  lat: number;
  lon: number;
  magnitude: number | null;
  timestamp: string;
  source: string;
}

export interface Stats {
  total: number;
  by_category: Record<string, number>;
  live: boolean;
}

export interface AskResponse {
  answer: string;
  mode: "ai" | "fallback";
  sources: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchEvents(params?: {
  category?: EventCategory;
  q?: string;
}): Promise<PulseEvent[]> {
  const url = new URL("/api/v1/events", API_BASE);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.q) url.searchParams.set("q", params.q);
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch events");
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(new URL("/api/v1/stats", API_BASE), {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function askPulse(question: string, events: PulseEvent[]): Promise<AskResponse> {
  const res = await fetch(new URL("/api/v1/ask", API_BASE), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, events }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to ask Pulse AI");
  return res.json();
}

export function connectToEventStream(onMessage: (message: { type: string; events?: PulseEvent[]; event?: PulseEvent; event_id?: string }) => void) {
  const httpUrl = new URL(API_BASE);
  const protocol = httpUrl.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${protocol}//${httpUrl.host}/ws/events`);
  socket.onmessage = (message) => {
    try { onMessage(JSON.parse(message.data)); } catch { /* ignore malformed provider messages */ }
  };
  return socket;
}

export const CATEGORY_META: Record<
  EventCategory,
  { label: string; icon: string; color: string }
> = {
  earthquake: { label: "Quakes", icon: "\u{1F30B}", color: "#ff9f40" },
  wildfire: { label: "Fires", icon: "\u{1F525}", color: "#ff4557" },
  flood: { label: "Floods", icon: "\u{1F30A}", color: "#3e9bff" },
  storm: { label: "Storms", icon: "\u{1F32A}\uFE0F", color: "#ffd23f" },
  volcano: { label: "Volcanoes", icon: "\u{1F30B}", color: "#ff6b3d" },
};

export const SEVERITY_COLOR: Record<EventSeverity, string> = {
  critical: "#ff4557",
  warning: "#ff9f40",
  advisory: "#ffd23f",
  normal: "#7c8798",
};

export function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.round(diffMs / 60000));
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.round(hrs / 24)}d`;
}
