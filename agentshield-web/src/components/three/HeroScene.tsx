"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Icosahedron, Float } from "@react-three/drei";
import { useMemo, useRef, Suspense } from "react";
import * as THREE from "three";
import type { Group, Points as ThreePoints } from "three";

/** Even point distribution on a sphere via the Fibonacci lattice. */
function fibonacciSphere(count: number, radius: number) {
  const positions = new Float32Array(count * 3);
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const theta = golden * i;
    positions[i * 3] = Math.cos(theta) * r * radius;
    positions[i * 3 + 1] = y * radius;
    positions[i * 3 + 2] = Math.sin(theta) * r * radius;
  }
  return positions;
}

/** Slowly rotating shell of neural data points around the core. */
function PointShell() {
  const ref = useRef<ThreePoints>(null);
  const positions = useMemo(() => fibonacciSphere(900, 2.35), []);

  const texture = useMemo(() => {
    const size = 64;
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    const ctx = canvas.getContext("2d")!;
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    g.addColorStop(0, "rgba(255,255,255,1)");
    g.addColorStop(0.35, "rgba(160,210,255,0.85)");
    g.addColorStop(1, "rgba(160,210,255,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
    const tex = new THREE.CanvasTexture(canvas);
    tex.needsUpdate = true;
    return tex;
  }, []);

  useFrame((_, delta) => {
    if (!ref.current) return;
    ref.current.rotation.y += delta * 0.045;
    ref.current.rotation.x += delta * 0.012;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.055}
        map={texture}
        transparent
        depthWrite={false}
        opacity={0.9}
        color="#7fb2ff"
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}

/** Crisp wireframe shield core with a soft inner glow. */
function Core() {
  const wire = useRef<Group>(null);
  useFrame((_, delta) => {
    if (wire.current) {
      wire.current.rotation.y += delta * 0.12;
      wire.current.rotation.z += delta * 0.03;
    }
  });
  return (
    <group>
      {/* inner glow sphere */}
      <Icosahedron args={[1.05, 3]}>
        <meshBasicMaterial color="#1b3aa8" transparent opacity={0.22} />
      </Icosahedron>
      {/* faceted glass shell */}
      <Icosahedron args={[1.5, 1]}>
        <meshStandardMaterial
          color="#3358ff"
          emissive="#2a1e7a"
          emissiveIntensity={0.4}
          roughness={0.25}
          metalness={0.9}
          transparent
          opacity={0.5}
        />
      </Icosahedron>
      {/* rotating wireframe cage */}
      <group ref={wire}>
        <Icosahedron args={[1.72, 1]}>
          <meshBasicMaterial color="#5fd0ff" wireframe transparent opacity={0.35} />
        </Icosahedron>
      </group>
    </group>
  );
}

/** Thin governance orbit ring on a fixed tilt. */
function OrbitRing({
  radius,
  tilt,
  color,
  speed,
  opacity,
}: {
  radius: number;
  tilt: [number, number, number];
  color: string;
  speed: number;
  opacity: number;
}) {
  const ref = useRef<Group>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.z += delta * speed;
  });
  return (
    <group rotation={tilt}>
      <group ref={ref}>
        <mesh>
          <torusGeometry args={[radius, 0.008, 16, 160]} />
          <meshBasicMaterial color={color} transparent opacity={opacity} />
        </mesh>
      </group>
    </group>
  );
}

/** Pointer-reactive parallax wrapper. */
function ParallaxRig({ children }: { children: React.ReactNode }) {
  const group = useRef<Group>(null);
  useFrame((state) => {
    if (!group.current) return;
    const targetY = state.pointer.x * 0.28;
    const targetX = -state.pointer.y * 0.2;
    group.current.rotation.y += (targetY - group.current.rotation.y) * 0.04;
    group.current.rotation.x += (targetX - group.current.rotation.x) * 0.04;
  });
  return <group ref={group}>{children}</group>;
}

export default function HeroScene() {
  return (
    <Canvas
      dpr={[1, 1.8]}
      camera={{ position: [0, 0, 6.5], fov: 42 }}
      gl={{ antialias: true, alpha: true }}
      className="!absolute inset-0"
    >
      <ambientLight intensity={0.6} />
      <pointLight position={[6, 6, 6]} intensity={110} color="#4f7cff" />
      <pointLight position={[-6, -3, 3]} intensity={80} color="#a855f7" />
      <pointLight position={[0, 4, -6]} intensity={50} color="#38e1ff" />
      <Suspense fallback={null}>
        <ParallaxRig>
          <Float speed={1.1} rotationIntensity={0.25} floatIntensity={0.6}>
            <Core />
          </Float>
          <PointShell />
          <OrbitRing radius={2.75} tilt={[Math.PI / 2.1, 0.15, 0]} color="#4f7cff" speed={0.14} opacity={0.55} />
          <OrbitRing radius={3.25} tilt={[Math.PI / 2.6, -0.4, 0.3]} color="#a855f7" speed={-0.1} opacity={0.4} />
          <OrbitRing radius={3.7} tilt={[Math.PI / 1.8, 0.5, -0.2]} color="#38e1ff" speed={0.08} opacity={0.28} />
        </ParallaxRig>
      </Suspense>
    </Canvas>
  );
}
