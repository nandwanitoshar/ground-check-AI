"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

interface ThreeTerrainVisualizerProps {
  interactive?: boolean;
  highlightBoundary?: boolean;
  highlightRoute?: boolean;
  activeNode?: string | null;
  className?: string;
}

export default function ThreeTerrainVisualizer({
  interactive = true,
  highlightBoundary = false,
  highlightRoute = false,
  activeNode = null,
  className = "",
}: ThreeTerrainVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [webglSupported, setWebglSupported] = useState<boolean>(true);
  const mouseRef = useRef<{ x: number; y: number; targetX: number; targetY: number }>({
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check WebGL availability
    try {
      const testCanvas = document.createElement("canvas");
      const gl = testCanvas.getContext("webgl") || testCanvas.getContext("experimental-webgl");
      if (!gl) {
        setWebglSupported(false);
        return;
      }
    } catch {
      setWebglSupported(false);
      return;
    }

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x080c0e, 0.025);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 14, 22);
    camera.lookAt(0, 1, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x080c0e, 0);
    container.appendChild(renderer.domElement);

    // 1. Topographic Plane Geometry
    const gridSegments = 48;
    const planeGeo = new THREE.PlaneGeometry(32, 24, gridSegments, gridSegments);
    planeGeo.rotateX(-Math.PI / 2);

    // Sculpt natural topographic contours using layered sine/cosine elevation
    const posAttr = planeGeo.attributes.position;
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);
      // Topographic elevation function with quarry pit indentation
      const distFromCenter = Math.sqrt(x * x + z * z);
      let y =
        Math.sin(x * 0.35) * Math.cos(z * 0.35) * 1.8 +
        Math.sin(x * 0.7 + z * 0.5) * 0.6 +
        Math.cos(x * 0.2 - z * 0.4) * 0.8;

      // Excavation quarry pit dip in the center-left
      const pitDist = Math.sqrt((x + 2) * (x + 2) + (z - 1) * (z - 1));
      if (pitDist < 5.5) {
        y -= Math.cos((pitDist / 5.5) * Math.PI * 0.5) * 2.2;
      }
      posAttr.setY(i, y);
    }
    planeGeo.computeVertexNormals();

    // Wireframe Topographic Material with Phosphor Environmental Accent
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x0e3a2b,
      wireframe: true,
      transparent: true,
      opacity: 0.55,
    });
    const terrainWireMesh = new THREE.Mesh(planeGeo, wireMat);
    scene.add(terrainWireMesh);

    // Solid darker base for depth occlusion
    const baseMat = new THREE.MeshBasicMaterial({
      color: 0x080c0e,
      transparent: true,
      opacity: 0.92,
      depthWrite: true,
    });
    const terrainBaseMesh = new THREE.Mesh(planeGeo, baseMat);
    terrainBaseMesh.position.y = -0.05;
    scene.add(terrainBaseMesh);

    // 2. Excavation Boundary Polygon (12.5 ha representation)
    const boundaryPoints = [
      new THREE.Vector3(-4.5, -0.6, -2.5),
      new THREE.Vector3(-1.0, -0.8, -3.2),
      new THREE.Vector3(1.2, -0.4, -1.0),
      new THREE.Vector3(0.5, -0.2, 2.2),
      new THREE.Vector3(-3.2, -0.4, 2.8),
      new THREE.Vector3(-4.5, -0.6, -2.5), // closed loop
    ];
    const boundaryGeo = new THREE.BufferGeometry().setFromPoints(boundaryPoints);
    const boundaryMat = new THREE.LineBasicMaterial({
      color: highlightBoundary ? 0x00f5a0 : 0x10b981,
      linewidth: 2,
      transparent: true,
      opacity: highlightBoundary ? 0.95 : 0.65,
    });
    const boundaryLine = new THREE.Line(boundaryGeo, boundaryMat);
    scene.add(boundaryLine);

    // 3. Haul Road Alignment Route (5km transport corridor)
    const routePoints = [
      new THREE.Vector3(0.5, -0.2, 2.2),
      new THREE.Vector3(3.0, 0.4, 3.5),
      new THREE.Vector3(6.5, 0.9, 2.0),
      new THREE.Vector3(9.2, 1.4, -1.5),
      new THREE.Vector3(12.0, 1.8, -4.0),
    ];
    const routeGeo = new THREE.BufferGeometry().setFromPoints(routePoints);
    const routeMat = new THREE.LineDashedMaterial({
      color: highlightRoute ? 0x38bdf8 : 0x64748b,
      dashSize: 0.8,
      gapSize: 0.4,
      transparent: true,
      opacity: highlightRoute ? 0.95 : 0.5,
    });
    const routeLine = new THREE.Line(routeGeo, routeMat);
    routeLine.computeLineDistances();
    scene.add(routeLine);

    // 4. Evidence Verification Nodes
    const nodeData = [
      { id: "coords", pos: new THREE.Vector3(-2.2, -0.5, 0.5), label: "GPS Center 40.7128°N", color: 0x00f5a0 },
      { id: "boundary", pos: new THREE.Vector3(-1.0, -0.8, -3.2), label: "Excavation 12.5ha", color: 0x38bdf8 },
      { id: "borehole", pos: new THREE.Vector3(-3.5, -0.3, 1.2), label: "Borehole GW-18m", color: 0xf59e0b },
      { id: "corridor", pos: new THREE.Vector3(9.2, 1.4, -1.5), label: "Corridor Check 5km", color: 0x10b981 },
      { id: "buffer", pos: new THREE.Vector3(5.0, 0.2, -1.0), label: "500m Setback", color: 0xa855f7 },
    ];

    const nodesGroup = new THREE.Group();
    const nodeSpheres: THREE.Mesh[] = [];

    nodeData.forEach((item) => {
      const isSelected = activeNode === item.id;
      const sphereGeo = new THREE.SphereGeometry(isSelected ? 0.35 : 0.22, 16, 16);
      const sphereMat = new THREE.MeshBasicMaterial({
        color: isSelected ? 0x00f5a0 : item.color,
      });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.position.copy(item.pos);
      nodesGroup.add(sphere);
      nodeSpheres.push(sphere);

      // Vertical radar beacon stem connecting to terrain
      const stemGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(item.pos.x, -2, item.pos.z),
        item.pos,
      ]);
      const stemMat = new THREE.LineBasicMaterial({
        color: item.color,
        transparent: true,
        opacity: isSelected ? 0.7 : 0.25,
      });
      const stem = new THREE.Line(stemGeo, stemMat);
      nodesGroup.add(stem);
    });
    scene.add(nodesGroup);

    // 5. Environmental Ambient & Grid Reference
    const gridHelper = new THREE.GridHelper(36, 18, 0x132a21, 0x0b1813);
    gridHelper.position.y = -2.1;
    scene.add(gridHelper);

    // Mouse parallax tracking
    const handleMouseMove = (e: MouseEvent) => {
      if (!interactive) return;
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseRef.current.targetX = x * 1.5;
      mouseRef.current.targetY = y * 1.2;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // Resize listener
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth camera interpolation for cinematic feel
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

      camera.position.x = mouseRef.current.x * 3.5;
      camera.position.y = 14 + mouseRef.current.y * 2.0;
      camera.lookAt(0, 0.5, 0);

      // Subtle pulse on nodes
      nodeSpheres.forEach((sphere, idx) => {
        const pulse = 1 + Math.sin(elapsedTime * 3 + idx * 1.5) * 0.12;
        sphere.scale.set(pulse, pulse, pulse);
      });

      // Slow topographic drift
      terrainWireMesh.rotation.y = Math.sin(elapsedTime * 0.08) * 0.03;
      terrainBaseMesh.rotation.y = terrainWireMesh.rotation.y;

      renderer.render(scene, camera);
    };

    animate();

    // Clean up WebGL resources
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);

      planeGeo.dispose();
      wireMat.dispose();
      baseMat.dispose();
      boundaryGeo.dispose();
      boundaryMat.dispose();
      routeGeo.dispose();
      routeMat.dispose();
      gridHelper.dispose();

      renderer.dispose();
      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [interactive, highlightBoundary, highlightRoute, activeNode]);

  if (!webglSupported) {
    return (
      <div className={`relative flex items-center justify-center bg-[#080C0E] border border-emerald-950 rounded-xl p-8 ${className}`}>
        <div className="text-center font-mono text-xs text-emerald-400/80 space-y-2">
          <div className="w-12 h-12 rounded-full border border-emerald-500/30 mx-auto flex items-center justify-center text-emerald-400">
            ▲
          </div>
          <p className="font-bold uppercase tracking-widest">TOPOGRAPHIC CADASTRE VIEWPORT</p>
          <p className="text-slate-400 text-[11px]">WGS84 40.7128°N, 74.0060°W · 12.5ha Quarry Cadastre</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden select-none pointer-events-auto ${className}`}>
      {/* HUD Telemetry Overlay */}
      <div className="absolute top-3 left-4 z-10 pointer-events-none font-mono text-[10px] text-emerald-400/70 tracking-widest uppercase flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          SPATIAL CADASTRE RADAR
        </span>
        <span className="text-slate-600">|</span>
        <span className="text-slate-400">EPSG:4326 · 48-GRID TOPOGRAPHY</span>
      </div>

      <div className="absolute bottom-3 right-4 z-10 pointer-events-none font-mono text-[9px] text-slate-500 flex items-center gap-2">
        <span className="text-emerald-500/80">NODE 01: GPS ANCHOR</span>
        <span>•</span>
        <span className="text-sky-400/80">NODE 02: BOUNDARY 12.5ha</span>
        <span>•</span>
        <span className="text-amber-400/80">NODE 03: 18m BOREHOLE</span>
      </div>

      <div ref={containerRef} className="w-full h-full min-h-[380px]" />
    </div>
  );
}

