"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { EventCategory, fetchEvents, fetchStats, PulseEvent, Stats } from "@/lib/api";
import StatsBar from "@/components/StatsBar";
import LiveFeed from "@/components/LiveFeed";
import FilterBar from "@/components/FilterBar";
import PulseLine from "@/components/PulseLine";

const EventMap = dynamic(() => import("@/components/EventMap"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full rounded-xl border border-border bg-panel flex items-center justify-center text-muted text-sm">
      Loading map…
    </div>
  ),
});

export default function Home() {
  const [events, setEvents] = useState<PulseEvent[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [category, setCategory] = useState<EventCategory | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => setError("api-offline"));
  }, []);

  useEffect(() => {
    const handle = setTimeout(() => {
      fetchEvents({ category: category ?? undefined, q: query || undefined })
        .then((data) => {
          setEvents(data);
          setError(null);
        })
        .catch(() => setError("api-offline"));
    }, 200);
    return () => clearTimeout(handle);
  }, [category, query]);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border px-6 py-4 flex items-center gap-6">
        <span className="font-mono text-sm tracking-widest uppercase">
          ◉ World Pulse
        </span>
        <nav className="hidden sm:flex gap-5 text-sm text-muted">
          <span className="text-text">Explore</span>
          <span>Live</span>
          <span>Analytics</span>
        </nav>
      </header>

      <main className="flex-1 px-6 py-10 max-w-6xl mx-auto w-full flex flex-col gap-8">
        <section className="text-center flex flex-col items-center gap-3">
          <h1 className="font-mono text-xs uppercase tracking-[0.3em] text-muted">
            Global Event Intelligence
          </h1>
          <div className="flex items-center gap-3">
            <span className="font-mono text-4xl">
              {stats?.total ?? "—"}
            </span>
            <span className="text-muted text-sm">events tracked</span>
            <span className="flex items-center gap-1.5 text-live text-xs font-mono uppercase ml-2">
              <span className="w-2 h-2 rounded-full bg-live live-dot" />
              Live
            </span>
          </div>
          <PulseLine />
        </section>

        {error && (
          <div className="text-center text-sm text-warning font-mono">
            API not reachable — start the FastAPI backend on :8000
          </div>
        )}

        <section className="h-[420px]">
          <EventMap events={events} />
        </section>

        {stats && <StatsBar stats={stats} />}

        <FilterBar
          active={category}
          onChange={setCategory}
          query={query}
          onQueryChange={setQuery}
        />

        <LiveFeed events={events} />
      </main>

      <footer className="border-t border-border px-6 py-4 text-center text-xs text-muted font-mono">
        World Pulse V0.1 — demo data — see what&apos;s happening around the world
      </footer>
    </div>
  );
}
