"use client";

import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapGeometry, GeographicCoordinates } from "@/types/audit";
import { MapPin, Navigation, Layers, ZoomIn, ZoomOut } from "lucide-react";

interface AuditMapProps {
  center?: { lat: number; lon: number } | null;
  zoom?: number | null;
  features?: MapGeometry[] | null;
  projectCoords?: GeographicCoordinates | null;
  height?: string;
  interactive?: boolean;
}

export function AuditMap({
  center = { lat: 39.7547, lon: -105.2211 },
  zoom = 13,
  features = [],
  projectCoords,
  height = "420px",
  interactive = true,
}: AuditMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const defaultCenter = center || { lat: 39.7547, lon: -105.2211 };
  const defaultZoom = zoom || 13;

  useEffect(() => {
    if (!mapContainer.current) return;

    // Destroy existing instance if any
    if (mapInstance.current) {
      mapInstance.current.remove();
      mapInstance.current = null;
    }

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors"
          }
        },
        layers: [
          {
            id: "osm-tiles",
            type: "raster",
            source: "osm",
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [defaultCenter.lon, defaultCenter.lat],
      zoom: defaultZoom,
      interactive: interactive
    });

    if (interactive) {
      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");
    }

    map.on("load", () => {
      setMapLoaded(true);

      // Add features
      if (features && features.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        let hasPoints = false;

        // Separate points and lines/polygons
        features.forEach((feat, idx) => {
          if (feat.type === "Point") {
            const [lon, lat] = feat.coordinates;
            bounds.extend([lon, lat]);
            hasPoints = true;

            const isOrigin = feat.properties?.role === "origin";
            const isEvidence = feat.properties?.role === "evidence";

            // Custom HTML Marker element
            const el = document.createElement("div");
            el.className = "flex items-center justify-center cursor-pointer";
            
            if (isOrigin) {
              el.innerHTML = `
                <div class="relative flex items-center justify-center">
                  <div class="absolute w-8 h-8 rounded-full bg-emerald-500/20 animate-ping"></div>
                  <div class="w-6 h-6 rounded-full bg-emerald-600 border-2 border-white shadow-lg flex items-center justify-center text-white font-bold text-[10px]">
                    ★
                  </div>
                </div>
              `;
            } else if (isEvidence) {
              const color = feat.properties?.category === "water" ? "bg-cyan-600" : "bg-rose-600";
              el.innerHTML = `
                <div class="relative flex items-center justify-center">
                  <div class="w-6 h-6 rounded-full ${color} border-2 border-white shadow-lg flex items-center justify-center text-white text-[11px] font-bold">
                    ●
                  </div>
                </div>
              `;
            } else {
              el.innerHTML = `
                <div class="w-5 h-5 rounded-full bg-slate-700 border-2 border-white shadow-md flex items-center justify-center text-white text-[10px]">
                  •
                </div>
              `;
            }

            const popupHtml = `
              <div class="p-2 text-slate-900 text-xs">
                <p class="font-bold text-sm">${feat.properties?.title || "Feature"}</p>
                <p class="text-slate-600">${feat.properties?.role === "origin" ? "Project Reference Site" : "Independently Verified Feature"}</p>
                <p class="text-[10px] text-slate-500 font-mono mt-1">Lat: ${lat.toFixed(5)}°, Lon: ${lon.toFixed(5)}°</p>
              </div>
            `;

            new maplibregl.Marker({ element: el })
              .setLngLat([lon, lat])
              .setPopup(new maplibregl.Popup({ offset: 12 }).setHTML(popupHtml))
              .addTo(map);
          }
        });

        // Add LineStrings (Distance lines)
        const lineFeatures = features.filter(f => f.type === "LineString");
        if (lineFeatures.length > 0) {
          map.addSource("distance-lines", {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: lineFeatures.map(lf => ({
                type: "Feature",
                geometry: {
                  type: "LineString",
                  coordinates: lf.coordinates
                },
                properties: lf.properties
              }))
            }
          });

          // Dashed geodesic line
          map.addLayer({
            id: "distance-line-layer",
            type: "line",
            source: "distance-lines",
            layout: {
              "line-join": "round",
              "line-cap": "round"
            },
            paint: {
              "line-color": "#e11d48",
              "line-width": 3,
              "line-dasharray": [2, 2]
            }
          });
        }

        // Add Circle / Radius buffers
        const circleFeatures = features.filter(f => f.type === "Circle");
        if (circleFeatures.length > 0) {
          // Generate a polygon circle from coordinates and radius_km
          const polygonFeatures = circleFeatures.map(cf => {
            const [centerLon, centerLat] = cf.coordinates;
            const radiusKm = cf.properties?.radius_km || 1.0;
            const points = 64;
            const coords = [];
            const earthRadiusKm = 6371.0;

            const latRad = (centerLat * Math.PI) / 180;
            const lonRad = (centerLon * Math.PI) / 180;
            const dByR = radiusKm / earthRadiusKm;

            for (let i = 0; i <= points; i++) {
              const bearing = (i * 2 * Math.PI) / points;
              const pLatRad = Math.asin(
                Math.sin(latRad) * Math.cos(dByR) +
                  Math.cos(latRad) * Math.sin(dByR) * Math.cos(bearing)
              );
              const pLonRad =
                lonRad +
                Math.atan2(
                  Math.sin(bearing) * Math.sin(dByR) * Math.cos(latRad),
                  Math.cos(dByR) - Math.sin(latRad) * Math.sin(pLatRad)
                );
              coords.push([(pLonRad * 180) / Math.PI, (pLatRad * 180) / Math.PI]);
            }

            return {
              type: "Feature",
              geometry: {
                type: "Polygon",
                coordinates: [coords]
              },
              properties: cf.properties
            };
          });

          map.addSource("buffer-circles", {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: polygonFeatures as any
            }
          });

          map.addLayer({
            id: "buffer-circle-fill",
            type: "fill",
            source: "buffer-circles",
            paint: {
              "fill-color": "#ef4444",
              "fill-opacity": 0.08
            }
          });

          map.addLayer({
            id: "buffer-circle-stroke",
            type: "line",
            source: "buffer-circles",
            paint: {
              "line-color": ["get", "stroke"],
              "line-width": 2,
              "line-dasharray": [3, 2]
            }
          });
        }

        // Fit map bounds to view all elements
        if (hasPoints && !bounds.isEmpty()) {
          map.fitBounds(bounds, { padding: 60, maxZoom: 15, duration: 1000 });
        }
      }
    });

    mapInstance.current = map;

    return () => {
      map.remove();
    };
  }, [center, zoom, features, interactive]);

  return (
    <div className="relative w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-900 shadow-md">
      <div ref={mapContainer} style={{ width: "100%", height }} />

      {/* Map Legend Overlay */}
      <div className="absolute bottom-3 left-3 z-10 rounded-lg bg-slate-950/85 backdrop-blur-md px-3 py-2 text-xs border border-slate-800 text-slate-300 shadow-lg">
        <p className="font-semibold text-slate-100 text-[11px] mb-1.5 flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5 text-emerald-400" />
          <span>Independent Geospatial Ground Truth</span>
        </p>
        <div className="flex flex-col gap-1 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-white"></span>
            <span>Project Site Coordinates (WGS-84)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 border border-white"></span>
            <span>Independently Surveyed OSM Feature</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 border-t-2 border-dashed border-rose-500"></span>
            <span>Deterministic Geodesic Line</span>
          </div>
        </div>
      </div>
    </div>
  );
}
