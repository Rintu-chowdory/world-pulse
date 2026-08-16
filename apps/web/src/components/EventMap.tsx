"use client";

import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import type { Map as MapLibreMap, Marker } from "maplibre-gl";
import { CATEGORY_META, PulseEvent, SEVERITY_COLOR } from "@/lib/api";

const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-nolabels/style.json";

export default function EventMap({ events }: { events: PulseEvent[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Marker[]>([]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: DARK_STYLE,
      center: [10, 25],
      zoom: 1.6,
      attributionControl: { compact: true },
    });
    mapRef.current.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      "top-right"
    );
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const place = () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      events.forEach((ev) => {
        const el = document.createElement("div");
        el.style.width = "14px";
        el.style.height = "14px";
        el.style.borderRadius = "50%";
        el.style.background = SEVERITY_COLOR[ev.severity];
        el.style.boxShadow = `0 0 0 4px ${SEVERITY_COLOR[ev.severity]}33`;
        el.style.border = "1px solid rgba(255,255,255,0.4)";
        el.style.cursor = "pointer";

        const meta = CATEGORY_META[ev.category];
        const popup = new maplibregl.Popup({ offset: 12 }).setHTML(
          `<div style="font-family:var(--font-sans, sans-serif); min-width:180px">
             <div style="font-size:11px; letter-spacing:.05em; color:#7c8798; text-transform:uppercase">${meta.label}</div>
             <div style="font-weight:600; margin:2px 0">${ev.title}</div>
             <div style="font-size:13px; color:#a9b3c1">${ev.location}</div>
             ${ev.magnitude ? `<div style="font-size:12px; color:#7c8798; margin-top:4px">Magnitude ${ev.magnitude}</div>` : ""}
           </div>`
        );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([ev.lon, ev.lat])
          .setPopup(popup)
          .addTo(map);
        markersRef.current.push(marker);
      });
    };

    if (map.isStyleLoaded()) place();
    else map.once("load", place);
  }, [events]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full rounded-xl overflow-hidden border border-border"
    />
  );
}
