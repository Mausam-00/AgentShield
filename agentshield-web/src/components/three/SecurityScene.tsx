"use client";

import { Component, useEffect, useMemo, useRef, type ReactNode } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Edges } from "@react-three/drei";
import { Group, Mesh, Shape } from "three";
import type { SceneVariant } from "./SecurityVisual";

type Palette = { cyan: string; blue: string; violet: string; surface: string };
const CONTROL_NODES: [number, number, number][] = [
  [1.7, 0, 0], [-1.7, 0, 0], [0, 1.7, 0],
  [0, -1.7, 0], [0, 0, 1.7], [0, 0, -1.7],
];

function ControlNetwork({ palette, activeIndex }: { palette: Palette; activeIndex: number }) {
  const ref = useRef<Group>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += Math.min(delta, .05) * .18;
  });
  return (
    <group ref={ref} rotation={[.35, .6, .2]}>
      <mesh>
        <icosahedronGeometry args={[.72, 0]} />
        <meshStandardMaterial color={palette.surface} metalness={.55} roughness={.25} />
        <Edges color={palette.cyan} />
      </mesh>
      {CONTROL_NODES.map((position, i) => (
        <group key={i}>
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute attach="attributes-position" count={2} array={new Float32Array([0, 0, 0, ...position])} itemSize={3} />
            </bufferGeometry>
            <lineBasicMaterial color={palette.cyan} transparent opacity={i === activeIndex ? .9 : .25} />
          </lineSegments>
          <mesh position={position} scale={i === activeIndex ? 1.35 : 1}>
            <octahedronGeometry args={[.19, 0]} />
            <meshStandardMaterial color={i === activeIndex ? palette.violet : palette.cyan} emissive={i === activeIndex ? palette.violet : palette.blue} emissiveIntensity={.5} metalness={.4} roughness={.3} />
          </mesh>
        </group>
      ))}
      <Orbit radius={2} tilt={[.4, .3, 0]} color={palette.blue} speed={.35} />
    </group>
  );
}

function GateCorridor({ palette, activeIndex }: { palette: Palette; activeIndex: number }) {
  const ref = useRef<Group>(null);
  const packet = useRef<Mesh>(null);
  const elapsed = useRef(0);
  useFrame((_, delta) => {
    elapsed.current += Math.min(delta, .05);
    if (ref.current) ref.current.rotation.y = -.65 + Math.sin(elapsed.current * .3) * .08;
    // Decorative circulation, not progress or authorization for a real action.
    if (packet.current) packet.current.position.z = 1.8 - (elapsed.current * .45 % 3.6);
  });
  return (
    <group ref={ref} rotation={[.16, -.65, .08]}>
      {Array.from({ length: 8 }, (_, i) => {
        const selected = i === activeIndex;
        return (
          <group key={i} position={[0, 0, 1.75 - i * .5]}>
            {[[-.78, 0], [.78, 0], [0, .9], [0, -.9]].map(([x, y], j) => (
              <mesh key={j} position={[x, y, 0]}>
                <boxGeometry args={j < 2 ? [.045, 1.8, .055] : [1.6, .045, .055]} />
                <meshBasicMaterial color={selected ? palette.cyan : i === 4 ? palette.violet : palette.blue} transparent opacity={selected ? 1 : .32} />
              </mesh>
            ))}
            {selected && (
              <mesh>
                <planeGeometry args={[1.56, 1.8]} />
                <meshBasicMaterial color={palette.cyan} transparent opacity={.07} depthWrite={false} />
              </mesh>
            )}
          </group>
        );
      })}
      <mesh ref={packet} position={[0, 0, 1.8]}>
        <octahedronGeometry args={[.1, 0]} />
        <meshBasicMaterial color={palette.cyan} />
      </mesh>
    </group>
  );
}

function Shield({ palette }: { palette: Palette }) {
  const ref = useRef<Group>(null);
  const elapsed = useRef(0);
  const shape = useMemo(() => {
    const outline = new Shape();
    outline.moveTo(0, 1.4);
    outline.lineTo(1.03, .98);
    outline.lineTo(1.03, -.1);
    outline.bezierCurveTo(1.03, -.75, .45, -1.18, 0, -1.4);
    outline.bezierCurveTo(-.45, -1.18, -1.03, -.75, -1.03, -.1);
    outline.lineTo(-1.03, .98);
    outline.closePath();
    return outline;
  }, []);
  useFrame(({ pointer }, delta) => {
    if (!ref.current) return;
    elapsed.current += Math.min(delta, .05);
    const t = elapsed.current;
    const blend = 1 - Math.exp(-Math.min(delta, .05) * 3);
    ref.current.rotation.y += (Math.sin(t * .35) * .3 + pointer.x * .15 - ref.current.rotation.y) * blend;
    ref.current.rotation.x += (Math.sin(t * .25) * .07 - pointer.y * .1 - ref.current.rotation.x) * blend;
    ref.current.position.y = Math.sin(t * .7) * .07;
  });
  return (
    <group ref={ref} rotation={[.06, -.2, 0]}>
      <mesh>
        <extrudeGeometry args={[shape, { depth: .22, bevelEnabled: true, bevelSegments: 3, steps: 1, bevelSize: .035, bevelThickness: .035, curveSegments: 16 }]} />
        <meshStandardMaterial color={palette.surface} metalness={.65} roughness={.3} />
        <Edges color={palette.cyan} threshold={24} />
      </mesh>
      <group position={[0, 0, .3]}>
        <mesh position={[-.24, .05, 0]} rotation={[0, 0, -.32]}>
          <boxGeometry args={[.1, 1.35, .07]} />
          <meshStandardMaterial color={palette.cyan} emissive={palette.cyan} emissiveIntensity={.6} />
        </mesh>
        <mesh position={[.24, .05, 0]} rotation={[0, 0, .32]}>
          <boxGeometry args={[.1, 1.35, .07]} />
          <meshStandardMaterial color={palette.violet} emissive={palette.violet} emissiveIntensity={.45} />
        </mesh>
        <mesh position={[0, -.13, .07]}>
          <sphereGeometry args={[.115, 16, 12]} />
          <meshStandardMaterial color={palette.cyan} emissive={palette.cyan} emissiveIntensity={.5} />
        </mesh>
        <mesh position={[0, -.34, .07]}>
          <boxGeometry args={[.075, .26, .07]} />
          <meshStandardMaterial color={palette.cyan} />
        </mesh>
      </group>
    </group>
  );
}

function Orbit({ radius, tilt, color, speed }: {
  radius: number; tilt: [number, number, number]; color: string; speed: number;
}) {
  const ref = useRef<Mesh>(null);
  const elapsed = useRef(0);
  useFrame((_, delta) => {
    elapsed.current += Math.min(delta, .05) * speed;
    ref.current?.position.set(Math.cos(elapsed.current) * radius, Math.sin(elapsed.current) * radius, 0);
  });
  return (
    <group rotation={tilt}>
      <mesh>
        <torusGeometry args={[radius, .009, 6, 100]} />
        <meshBasicMaterial color={color} transparent opacity={.4} />
      </mesh>
      <mesh ref={ref} position={[radius, 0, 0]}>
        <sphereGeometry args={[.055, 12, 8]} />
        <meshBasicMaterial color={color} />
      </mesh>
    </group>
  );
}

function ContextLifecycle({ onReady, onFailure }: { onReady: () => void; onFailure: () => void }) {
  const gl = useThree(state => state.gl);
  useEffect(() => {
    const canvas = gl.domElement;
    const lost = (event: Event) => {
      event.preventDefault();
      console.warn("AgentShield: WebGL context lost; switching to the SVG illustration.");
      onFailure();
    };
    canvas.addEventListener("webglcontextlost", lost);
    onReady();
    return () => canvas.removeEventListener("webglcontextlost", lost);
  }, [gl, onReady, onFailure]);
  return null;
}

class SceneBoundary extends Component<{ children: ReactNode; onFailure: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error) {
    console.warn("AgentShield: 3D illustration unavailable; retaining SVG.", error.message);
    this.props.onFailure();
  }
  render() { return this.state.failed ? null : this.props.children; }
}

export default function SecurityScene({ active, variant, activeIndex, onReady, onFailure }: {
  active: boolean; variant: SceneVariant; activeIndex: number; onReady: () => void; onFailure: () => void;
}) {
  const palette = useMemo(() => {
    const styles = getComputedStyle(document.documentElement);
    const color = (name: string) => styles.getPropertyValue(name).trim();
    return { cyan: color("--neon-cyan"), blue: color("--neon-blue"), violet: color("--neon-violet"), surface: color("--surface") };
  }, []);

  return (
    <div className="shield-webgl absolute inset-0" aria-hidden="true" data-active={active}>
      <SceneBoundary onFailure={onFailure}>
        <Canvas
          camera={{ position: [0, 0, 6.7], fov: 43 }}
          dpr={[1, 1.5]}
          frameloop={active ? "always" : "never"}
          gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
        >
          <ambientLight intensity={1.1} />
          <directionalLight position={[3, 3, 5]} intensity={3} color={palette.cyan} />
          <pointLight position={[-3, 0, 3]} intensity={18} color={palette.violet} />
          {variant === "shield" && <>
            <Shield palette={palette} />
            <Orbit radius={1.9} tilt={[.9, .2, -.4]} color={palette.cyan} speed={.4} />
            <Orbit radius={2.3} tilt={[-.7, .7, .6]} color={palette.blue} speed={-.28} />
          </>}
          {variant === "capabilities" && <ControlNetwork palette={palette} activeIndex={activeIndex} />}
          {variant === "gates" && <GateCorridor palette={palette} activeIndex={activeIndex} />}
          <ContextLifecycle onReady={onReady} onFailure={onFailure} />
        </Canvas>
      </SceneBoundary>
    </div>
  );
}
