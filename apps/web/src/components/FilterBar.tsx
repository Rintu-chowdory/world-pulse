"use client";

import { CATEGORY_META, EventCategory } from "@/lib/api";

export default function FilterBar({
  active,
  onChange,
  query,
  onQueryChange,
}: {
  active: EventCategory | null;
  onChange: (cat: EventCategory | null) => void;
  query: string;
  onQueryChange: (q: string) => void;
}) {
  const categories = Object.keys(CATEGORY_META) as EventCategory[];
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={() => onChange(null)}
        className={`px-3 py-1.5 rounded-full text-xs font-mono uppercase tracking-wide border transition-colors ${
          active === null
            ? "bg-live text-[#04140f] border-live"
            : "border-border text-muted hover:text-text"
        }`}
      >
        All
      </button>
      {categories.map((cat) => {
        const meta = CATEGORY_META[cat];
        const isActive = active === cat;
        return (
          <button
            key={cat}
            onClick={() => onChange(isActive ? null : cat)}
            className="px-3 py-1.5 rounded-full text-xs font-mono uppercase tracking-wide border transition-colors"
            style={{
              borderColor: isActive ? meta.color : "var(--border)",
              color: isActive ? meta.color : "var(--muted)",
              background: isActive ? `${meta.color}1a` : "transparent",
            }}
          >
            {meta.icon} {meta.label}
          </button>
        );
      })}
      <input
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="Search location or event…"
        className="ml-auto w-full sm:w-64 px-3 py-1.5 rounded-full text-sm bg-panel-raised border border-border text-text placeholder:text-muted focus:outline-none focus:border-live"
      />
    </div>
  );
}
