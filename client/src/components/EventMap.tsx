// Meridian Command: reliable in-app cartographic field with plotted signal marks, coordinate texture, and no external worker dependency.
import { CATEGORY_META, PulseEvent, SEVERITY_COLOR } from "@/lib/api";

export default function EventMap({ events }: { events: PulseEvent[] }) {
  return (
    <div className="signal-map" role="img" aria-label={`World map showing ${events.length} live signals`}>
      <div className="map-longitude longitude-a" /><div className="map-longitude longitude-b" /><div className="map-latitude latitude-a" /><div className="map-latitude latitude-b" />
      <div className="map-compass">N<span>↑</span></div>
      {events.map((event) => {
        const left = `${Math.min(96, Math.max(4, ((event.lon + 180) / 360) * 100))}%`;
        const top = `${Math.min(92, Math.max(8, ((90 - event.lat) / 180) * 100))}%`;
        return <button key={event.id} className="map-signal" style={{ left, top, background: SEVERITY_COLOR[event.severity], color: SEVERITY_COLOR[event.severity] }} title={`${CATEGORY_META[event.category].label}: ${event.title} — ${event.location}`} aria-label={`${event.title}, ${event.location}`}><span /></button>;
      })}
      <div className="map-readout">LIVE FIELD<br /><strong>{String(events.length).padStart(2, "0")}</strong> PLOTTED</div>
    </div>
  );
}
