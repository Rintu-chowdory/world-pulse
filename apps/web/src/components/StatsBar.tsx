import { CATEGORY_META, EventCategory, Stats } from "@/lib/api";

export default function StatsBar({ stats }: { stats: Stats }) {
  const categories = Object.keys(CATEGORY_META) as EventCategory[];
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-px bg-border border border-border rounded-xl overflow-hidden">
      {categories.map((cat) => {
        const meta = CATEGORY_META[cat];
        const count = stats.by_category[cat] ?? 0;
        return (
          <div key={cat} className="bg-panel px-4 py-3 flex flex-col gap-1">
            <span className="text-lg leading-none">{meta.icon}</span>
            <span className="font-mono text-xl" style={{ color: meta.color }}>
              {count}
            </span>
            <span className="text-xs uppercase tracking-wide text-muted">
              {meta.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
