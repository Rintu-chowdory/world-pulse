import { CATEGORY_META, PulseEvent, SEVERITY_COLOR, timeAgo } from "@/lib/api";

export default function LiveFeed({ events }: { events: PulseEvent[] }) {
  return (
    <div className="border border-border rounded-xl bg-panel overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <span className="w-2 h-2 rounded-full bg-live live-dot" />
        <h2 className="text-xs font-mono uppercase tracking-widest text-muted">
          Live Event Feed
        </h2>
      </div>
      <ul className="divide-y divide-border">
        {events.map((ev) => {
          const meta = CATEGORY_META[ev.category];
          return (
            <li
              key={ev.id}
              className="flex items-center gap-3 px-4 py-3 hover:bg-panel-raised transition-colors"
            >
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ background: SEVERITY_COLOR[ev.severity] }}
              />
              <span className="font-mono text-xs text-muted w-8 shrink-0">
                {timeAgo(ev.timestamp)}
              </span>
              <span className="shrink-0">{meta.icon}</span>
              <span className="text-sm font-medium truncate">{ev.title}</span>
              <span className="text-sm text-muted ml-auto shrink-0">
                {ev.location}
              </span>
              {ev.magnitude && (
                <span className="font-mono text-xs text-muted shrink-0">
                  M{ev.magnitude}
                </span>
              )}
            </li>
          );
        })}
        {events.length === 0 && (
          <li className="px-4 py-6 text-sm text-muted text-center">
            No events match the current filter.
          </li>
        )}
      </ul>
    </div>
  );
}
