"use client";

import React, { useEffect, useRef, useState } from "react";
import { MapPin, Navigation, Info } from "lucide-react";
import "maplibre-gl/dist/maplibre-gl.css";

interface GeographicFindingMapProps {
  projectCoords: [number, number]; // [lat, lon]
  evidenceGeometry?: {
    type: string;
    coordinates: any;
  } | null;
  evidenceTitle: string;
  calculatedDistanceMeters?: number | null;
  methodology?: string;
  difference?: string | number | null;
}

export function GeographicFindingMap({
  projectCoords,
  evidenceGeometry,
  evidenceTitle,
  calculatedDistanceMeters,
  methodology,
  difference,
}: GeographicFindingMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  const [pLat, pLon] = projectCoords;

  useEffect(() => {
    let isMounted = true;
    if (!mapContainerRef.current) return;

    // Dynamically load maplibre-gl to ensure clean SSR compatibility
    import("maplibre-gl")
      .then((maplibre) => {
        if (!isMounted || !mapContainerRef.current) return;

        try {
          const map = new maplibre.Map({
            container: mapContainerRef.current,
            style: {
              version: 8,
              sources: {
                osm: {
                  type: "raster",
                  tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                  tileSize: 256,
                  attribution: "&copy; OpenStreetMap contributors",
                },
              },
              layers: [
                {
                  id: "osm-tiles",
                  type: "raster",
                  source: "osm",
                  minzoom: 0,
                  maxzoom: 19,
                },
              ],
            },
            center: [pLon, pLat],
            zoom: 14,
          });

          map.addControl(new maplibre.NavigationControl({ showCompass: true }), "top-right");

          map.on("load", () => {
            if (!isMounted) return;
            setMapLoaded(true);

            // 1. Add Project Marker (Emerald / Indigo)
            const projectEl = document.createElement("div");
            projectEl.className = "flex items-center justify-center w-8 h-8 rounded-full bg-emerald-600 border-2 border-white shadow-lg text-white font-bold text-xs cursor-pointer";
            projectEl.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`;

            new maplibre.Marker({ element: projectEl })
              .setLngLat([pLon, pLat])
              .setPopup(
                new maplibre.Popup({ offset: 25 }).setHTML(`
                  <div class="p-2 text-xs">
                    <div class="font-bold text-emerald-800">Project Reference Origin</div>
                    <div class="text-slate-600 font-mono mt-0.5">${pLat.toFixed(5)}° N, ${pLon.toFixed(5)}° W</div>
                    <div class="text-[10px] text-slate-500 mt-1">GroundCheck Project Location</div>
                  </div>
                `)
              )
              .addTo(map);

            // 2. Add Evidence Geometry if present
            if (evidenceGeometry && evidenceGeometry.coordinates) {
              const geomType = evidenceGeometry.type;
              const coords = evidenceGeometry.coordinates;

              // GeoJSON feature collection
              const featureCollection = {
                type: "FeatureCollection",
                features: [
                  {
                    type: "Feature",
                    geometry: evidenceGeometry,
                    properties: {
                      title: evidenceTitle,
                    },
                  },
                ],
              };

              map.addSource("evidence-source", {
                type: "geojson",
                data: featureCollection as any,
              });

              if (geomType === "LineString") {
                map.addLayer({
                  id: "evidence-line",
                  type: "line",
                  source: "evidence-source",
                  paint: {
                    "line-color": "#2563eb", // vibrant blue
                    "line-width": 4,
                    "line-opacity": 0.85,
                  },
                });

                // Find closest coordinate to draw distance line
                let minD = Infinity;
                let closestPt = coords[0];
                for (const pt of coords) {
                  const d = Math.hypot(pt[0] - pLon, pt[1] - pLat);
                  if (d < minD) {
                    minD = d;
                    closestPt = pt;
                  }
                }

                // Distance line
                map.addSource("distance-line", {
                  type: "geojson",
                  data: {
                    type: "Feature",
                    geometry: {
                      type: "LineString",
                      coordinates: [
                        [pLon, pLat],
                        [closestPt[0], closestPt[1]],
                      ],
                    },
                    properties: {},
                  },
                });

                map.addLayer({
                  id: "distance-line-layer",
                  type: "line",
                  source: "distance-line",
                  paint: {
                    "line-color": "#e11d48", // rose / red measurement
                    "line-width": 2.5,
                    "line-dasharray": [2, 2],
                  },
                });
              } else if (geomType === "Polygon" || geomType === "MultiPolygon") {
                map.addLayer({
                  id: "evidence-fill",
                  type: "fill",
                  source: "evidence-source",
                  paint: {
                    "fill-color": "#0284c7",
                    "fill-opacity": 0.25,
                  },
                });
                map.addLayer({
                  id: "evidence-outline",
                  type: "line",
                  source: "evidence-source",
                  paint: {
                    "line-color": "#0284c7",
                    "line-width": 2.5,
                  },
                });
              } else if (geomType === "Point") {
                const evMarker = document.createElement("div");
                evMarker.className = "flex items-center justify-center w-7 h-7 rounded-full bg-blue-600 border-2 border-white shadow-md text-white font-bold text-xs";
                evMarker.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>`;

                new maplibre.Marker({ element: evMarker })
                  .setLngLat([coords[0], coords[1]])
                  .setPopup(
                    new maplibre.Popup({ offset: 20 }).setHTML(`
                      <div class="p-1.5 text-xs">
                        <div class="font-bold text-blue-900">${evidenceTitle}</div>
                        <div class="text-[10px] text-slate-500 font-mono mt-0.5">${coords[1].toFixed(5)}° N, ${coords[0].toFixed(5)}° W</div>
                      </div>
                    `)
                  )
                  .addTo(map);

                // Add measurement line
                map.addSource("distance-line", {
                  type: "geojson",
                  data: {
                    type: "Feature",
                    geometry: {
                      type: "LineString",
                      coordinates: [
                        [pLon, pLat],
                        [coords[0], coords[1]],
                      ],
                    },
                    properties: {},
                  },
                });

                map.addLayer({
                  id: "distance-line-layer",
                  type: "line",
                  source: "distance-line",
                  paint: {
                    "line-color": "#e11d48",
                    "line-width": 2.5,
                    "line-dasharray": [2, 2],
                  },
                });
              }

              // Fit bounds to show both project and evidence
              const bounds = new maplibre.LngLatBounds();
              bounds.extend([pLon, pLat]);

              if (geomType === "Point") {
                bounds.extend([coords[0], coords[1]]);
              } else if (geomType === "LineString") {
                for (const c of coords) bounds.extend([c[0], c[1]]);
              } else if (geomType === "Polygon") {
                for (const c of coords[0]) bounds.extend([c[0], c[1]]);
              }

              map.fitBounds(bounds, { padding: 60, maxZoom: 16 });
            }
          });

          mapInstanceRef.current = map;
        } catch (e: any) {
          logger_error(e);
          setMapError(e.message || "Failed to initialize MapLibre GL.");
        }
      })
      .catch((err) => {
        setMapError("Failed to load map libraries.");
      });

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [pLat, pLon, evidenceGeometry, evidenceTitle]);

  function logger_error(e: any) {
    if (typeof window !== "undefined") {
      console.warn("MapLibre init error:", e);
    }
  }

  return (
    <div className="relative w-full rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 shadow-sm">
      {/* Map Container */}
      <div ref={mapContainerRef} className="w-full h-80 sm:h-96" />

      {/* Floating Measurement Overlay Badge */}
      {calculatedDistanceMeters !== undefined && calculatedDistanceMeters !== null && (
        <div className="absolute bottom-3 left-3 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md px-3.5 py-2.5 rounded-lg border border-slate-200/80 dark:border-slate-700/80 shadow-md flex items-center gap-3 text-xs z-10">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
          <div>
            <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
              <span>Geodesic Distance:</span>
              <span className="font-mono text-rose-600 dark:text-rose-400 font-bold">
                {calculatedDistanceMeters >= 1000
                  ? `${(calculatedDistanceMeters / 1000).toFixed(2)} km`
                  : `${calculatedDistanceMeters.toFixed(1)} m`}
              </span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <span>Origin to {evidenceTitle}</span>
            </div>
          </div>
        </div>
      )}

      {/* Map Legend */}
      <div className="absolute top-3 left-3 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-200/80 dark:border-slate-700/80 shadow-sm text-[11px] text-slate-700 dark:text-slate-300 flex flex-col gap-1.5 z-10">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-emerald-600 border border-white" />
          <span className="font-medium">Project Site Coordinates</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-blue-600 border border-white" />
          <span className="font-medium">Independent OSM Geometry</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-0.5 bg-rose-500 border-t border-dashed border-rose-500" />
          <span className="font-medium">WGS84 Geodesic Trajectory</span>
        </div>
      </div>

      {mapError && (
        <div className="absolute inset-0 bg-slate-50/90 dark:bg-slate-900/90 flex flex-col items-center justify-center p-4 text-center z-20">
          <Info className="w-8 h-8 text-slate-400 mb-2" />
          <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">Map visualization fallback</p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
            Project coordinate: ({pLat.toFixed(5)}° N, {pLon.toFixed(5)}° W) | Calculated distance: {calculatedDistanceMeters?.toFixed(1)}m.
          </p>
        </div>
      )}
    </div>
  );
}

