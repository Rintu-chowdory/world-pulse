(globalThis["TURBOPACK"] || (globalThis["TURBOPACK"] = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/world-pulse/apps/web/src/components/EventMap.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>EventMap
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/world-pulse/apps/web/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/world-pulse/apps/web/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$maplibre$2d$gl$2f$dist$2f$maplibre$2d$gl$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/world-pulse/apps/web/node_modules/maplibre-gl/dist/maplibre-gl.mjs [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/world-pulse/apps/web/src/lib/api.ts [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-nolabels/style.json";
function EventMap({ events }) {
    _s();
    const containerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const mapRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const markersRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])([]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "EventMap.useEffect": ()=>{
            if (!containerRef.current || mapRef.current) return;
            mapRef.current = new __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$maplibre$2d$gl$2f$dist$2f$maplibre$2d$gl$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["Map"]({
                container: containerRef.current,
                style: DARK_STYLE,
                center: [
                    10,
                    25
                ],
                zoom: 1.6,
                attributionControl: {
                    compact: true
                }
            });
            mapRef.current.addControl(new __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$maplibre$2d$gl$2f$dist$2f$maplibre$2d$gl$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["NavigationControl"]({
                showCompass: false
            }), "top-right");
            return ({
                "EventMap.useEffect": ()=>{
                    mapRef.current?.remove();
                    mapRef.current = null;
                }
            })["EventMap.useEffect"];
        }
    }["EventMap.useEffect"], []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "EventMap.useEffect": ()=>{
            const map = mapRef.current;
            if (!map) return;
            const place = {
                "EventMap.useEffect.place": ()=>{
                    markersRef.current.forEach({
                        "EventMap.useEffect.place": (m)=>m.remove()
                    }["EventMap.useEffect.place"]);
                    markersRef.current = [];
                    events.forEach({
                        "EventMap.useEffect.place": (ev)=>{
                            const el = document.createElement("div");
                            el.style.width = "14px";
                            el.style.height = "14px";
                            el.style.borderRadius = "50%";
                            el.style.background = __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["SEVERITY_COLOR"][ev.severity];
                            el.style.boxShadow = `0 0 0 4px ${__TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["SEVERITY_COLOR"][ev.severity]}33`;
                            el.style.border = "1px solid rgba(255,255,255,0.4)";
                            el.style.cursor = "pointer";
                            const meta = __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CATEGORY_META"][ev.category];
                            const popup = new __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$maplibre$2d$gl$2f$dist$2f$maplibre$2d$gl$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["Popup"]({
                                offset: 12
                            }).setHTML(`<div style="font-family:var(--font-sans, sans-serif); min-width:180px">
             <div style="font-size:11px; letter-spacing:.05em; color:#7c8798; text-transform:uppercase">${meta.label}</div>
             <div style="font-weight:600; margin:2px 0">${ev.title}</div>
             <div style="font-size:13px; color:#a9b3c1">${ev.location}</div>
             ${ev.magnitude ? `<div style="font-size:12px; color:#7c8798; margin-top:4px">Magnitude ${ev.magnitude}</div>` : ""}
           </div>`);
                            const marker = new __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$maplibre$2d$gl$2f$dist$2f$maplibre$2d$gl$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["Marker"]({
                                element: el
                            }).setLngLat([
                                ev.lon,
                                ev.lat
                            ]).setPopup(popup).addTo(map);
                            markersRef.current.push(marker);
                        }
                    }["EventMap.useEffect.place"]);
                }
            }["EventMap.useEffect.place"];
            if (map.isStyleLoaded()) place();
            else map.once("load", place);
        }
    }["EventMap.useEffect"], [
        events
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$world$2d$pulse$2f$apps$2f$web$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: containerRef,
        className: "h-full w-full rounded-xl overflow-hidden border border-border"
    }, void 0, false, {
        fileName: "[project]/world-pulse/apps/web/src/components/EventMap.tsx",
        lineNumber: 75,
        columnNumber: 5
    }, this);
}
_s(EventMap, "9R8gSUWivkfrTpmOtb0Np8SDyuw=");
_c = EventMap;
var _c;
__turbopack_context__.k.register(_c, "EventMap");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/world-pulse/apps/web/src/components/EventMap.tsx [app-client] (ecmascript, next/dynamic entry)", (function(__turbopack_context__){

__turbopack_context__.n(__turbopack_context__.i("[project]/world-pulse/apps/web/src/components/EventMap.tsx [app-client] (ecmascript)"));
}),
]);

//# sourceMappingURL=world-pulse_apps_web_src_components_EventMap_tsx_0_gu1qe._.js.map