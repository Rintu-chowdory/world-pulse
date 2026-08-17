"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { CATEGORY_META, connectToEventStream, EventCategory, fetchEvents, fetchStats, PulseEvent, Stats, timeAgo } from "@/lib/api";
import AIAssistant from "@/components/AIAssistant";
import LiveFeed from "@/components/LiveFeed";
import FilterBar from "@/components/FilterBar";
import StatsBar from "@/components/StatsBar";
import PulseLine from "@/components/PulseLine";

const EventMap = dynamic(() => import("@/components/EventMap"), {
  ssr: false,
  loading: () => <div className="map-loading"><span className="spinner" /> Rendering live map layers…</div>,
});

export default function Home() {
  const [events, setEvents] = useState<PulseEvent[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [category, setCategory] = useState<EventCategory | null>(null);
  const [severity, setSeverity] = useState<"all" | PulseEvent["severity"]>("all");
  const [sortOrder, setSortOrder] = useState<"latest" | "severity" | "magnitude">("latest");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [error, setError] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [connection, setConnection] = useState<"connecting" | "live" | "offline">("connecting");
  const [lastUpdate, setLastUpdate] = useState("");

  useEffect(() => { fetchStats().then((data) => { setStats(data); setConnection("live"); setLastUpdate(new Date().toISOString()); }).catch(() => { setError(true); setConnection("offline"); }).finally(() => setInitialLoading(false)); }, []);
  useEffect(() => {
    const socket = connectToEventStream((message) => {
      if (message.type === "snapshot" && message.events) { setEvents(message.events); setConnection("live"); setLastUpdate(new Date().toISOString()); }
      if (message.type === "event.upsert" && message.event) { setEvents((current) => [message.event!, ...current.filter((event) => event.id !== message.event!.id)].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())); setConnection("live"); setLastUpdate(new Date().toISOString()); }
      if (message.type === "event.remove" && message.event_id) setEvents((current) => current.filter((event) => event.id !== message.event_id));
    });
    socket.onopen = () => { setConnection("live"); setLastUpdate(new Date().toISOString()); };
    socket.onclose = () => setConnection((current) => current === "live" ? "offline" : current);
    socket.onerror = () => { setError(true); setConnection("offline"); };
    return () => socket.close();
  }, []);
  useEffect(() => {
    const handle = setTimeout(() => {
      fetchEvents({ category: category ?? undefined, q: query || undefined }).then((data) => { setEvents(data); setError(false); }).catch(() => setError(true));
    }, 180);
    return () => clearTimeout(handle);
  }, [category, query]);

  const filteredEvents = useMemo(() => {
    const severityRank: Record<PulseEvent["severity"], number> = { critical: 4, warning: 3, advisory: 2, normal: 1 };
    return events.filter((event) => severity === "all" || event.severity === severity).sort((a, b) => {
      if (sortOrder === "severity") return severityRank[b.severity] - severityRank[a.severity];
      if (sortOrder === "magnitude") return (b.magnitude ?? -1) - (a.magnitude ?? -1);
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });
  }, [events, severity, sortOrder]);
  const criticalCount = useMemo(() => events.filter((event) => event.severity === "critical").length, [events]);
  const latest = filteredEvents[0];
  const statusText = connection === "live" ? "Live stream" : connection === "connecting" ? "Connecting" : "Offline mode";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup"><div className="brand-mark">◉</div><div><div className="brand-name">WORLD PULSE</div><div className="brand-subtitle">Global event intelligence</div></div></div>
        <nav className="topnav"><a className="active" href="#overview">Overview</a><a href="#map">Live map</a><a href="#feed">Event feed</a></nav>
        <div className="topbar-actions"><span className={`sync-label ${connection}`}><i /> {statusText}{lastUpdate ? ` · ${timeAgo(lastUpdate)}` : ""}</span><button className="icon-button" aria-label="Open settings">☷</button><div className="avatar">RC</div></div>
      </header>

      <main className="main-shell" id="overview">
        <section className="hero-grid">
          <div className="hero-copy"><div className="eyebrow">Global situation room <span className="live-pill"><i /> Live</span></div><h1>See what&apos;s<br /><em>moving</em> now.</h1><p>One calm, intelligent view of the events shaping the world — from first signal to informed action.</p><div className="hero-meta"><span><strong>{stats?.total ?? "—"}</strong> signals indexed</span><span className="meta-divider" /><span>Updated continuously</span></div></div>
          <div className="hero-visual"><div className="radar-ring ring-a" /><div className="radar-ring ring-b" /><div className="radar-core">◉</div><div className="radar-label label-one">GLOBAL<br /><span>LIVE INDEX</span></div><div className="radar-label label-two">{criticalCount || "—"}<span>CRITICAL</span></div></div>
        </section>

        <section className="metric-strip" aria-label="Live overview metrics"><div><span className="metric-label">ACTIVE SIGNALS</span><strong>{initialLoading ? <span className="metric-skeleton" /> : stats?.total ?? "—"}</strong><span className="metric-trend positive">+12.4% <small>vs. 24h</small></span></div><div><span className="metric-label">CRITICAL NOW</span><strong className="critical-text">{criticalCount || "—"}</strong><span className="metric-trend neutral">Requires attention</span></div><div><span className="metric-label">LATEST SIGNAL</span><strong className="latest-text">{latest ? timeAgo(latest.timestamp) : "—"}</strong><span className="metric-trend neutral">{latest?.location ?? "Awaiting data"}</span></div><div><span className="metric-label">COVERAGE</span><strong>05</strong><span className="metric-trend positive">Categories live</span></div></section>

        <AIAssistant events={events} />

        <section className="section-heading" id="map"><div><div className="eyebrow">01 / Geospatial intelligence</div><h2>Live world map</h2></div><div className="map-legend"><span><i className="legend-dot critical" /> Critical</span><span><i className="legend-dot warning" /> Warning</span><span><i className="legend-dot advisory" /> Advisory</span></div></section>
        <section className="map-layout"><div className="map-panel"><div className="map-toolbar"><span className="toolbar-title">EVENT DISTRIBUTION <small>· {filteredEvents.length} visible</small></span><span className="toolbar-actions">⌖ Auto-center &nbsp; · &nbsp; ⤢ Expand</span></div><div className="map-canvas">{initialLoading && <div className="next-map-loading"><span className="spinner" /> Loading live field</div>}<EventMap events={filteredEvents} /></div></div><aside className="signal-panel"><div className="panel-heading"><span>Top signals</span><div className="panel-actions"><span className="panel-count">{filteredEvents.length}</span><button className={`filter-toggle ${filtersOpen ? "active" : ""}`} onClick={() => setFiltersOpen((open) => !open)}>{filtersOpen ? "Close" : "Filters"}</button></div></div>{filtersOpen && <div className="next-filter-panel"><label>Severity<select value={severity} onChange={(event) => setSeverity(event.target.value as typeof severity)}><option value="all">All severities</option><option value="critical">Critical</option><option value="warning">Warning</option><option value="advisory">Advisory</option><option value="normal">Normal</option></select></label><label>Sort<select value={sortOrder} onChange={(event) => setSortOrder(event.target.value as typeof sortOrder)}><option value="latest">Latest first</option><option value="severity">Highest severity</option><option value="magnitude">Largest magnitude</option></select></label></div>}{filteredEvents.slice(0, 4).map((event) => <div className="signal-item" key={event.id}><div className="signal-marker" style={{ background: CATEGORY_META[event.category].color }} /><div><strong>{event.title}</strong><span>{event.location} · {timeAgo(event.timestamp)}</span></div><span className={`severity-tag ${event.severity}`}>{event.severity}</span></div>)}{initialLoading && events.length === 0 && <div className="next-loading-list"><span /><span /><span /></div>}{filteredEvents.length === 0 && !initialLoading && <div className="empty-state">No signals match the current view.</div>}</aside></section>

        <section className="section-heading feed-heading" id="feed"><div><div className="eyebrow">02 / Signal stream</div><h2>Explore the pulse</h2></div><span className="section-note">Filter by type, region, or severity</span></section>
        <FilterBar active={category} onChange={setCategory} query={query} onQueryChange={setQuery} />
        {error && <div className="api-notice">Connection is limited — showing the last available intelligence. Check the FastAPI service on your deployment.</div>}
        <LiveFeed events={filteredEvents} />
      </main>
      <footer className="footer"><span>WORLD PULSE / V0.2 FOUNDATION</span><span>Built for clarity in a noisy world</span><span>Data layer: demo feed · API healthy</span></footer>
    </div>
  );
}
