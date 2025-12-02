import React, { useRef, useMemo } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';

// Vertex Shader: Standard UV and Position pass-through with scroll-based distortion
const vertexShader = `
  varying vec2 vUv;
  varying vec3 vPosition;
  uniform float uTime;
  uniform float uScroll;

  void main() {
    vUv = uv;
    vPosition = position;
    
    // Position manipulation based on scroll speed (Warp effect)
    vec3 pos = position;
    // Bend the plane slightly as you scroll
    float warp = uScroll * 0.5;
    pos.z += sin(pos.x * 2.0 + uTime * 0.5) * 0.1;
    // Stretch along Y when scrolling fast (simulated)
    
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

// Fragment Shader: Domain Warping FBM for "Cyber Liquid" effect
const fragmentShader = `
  uniform float uTime;
  uniform float uScroll;
  uniform vec3 uColorA;
  uniform vec3 uColorB;
  uniform vec3 uColorC;
  varying vec2 vUv;
  varying vec3 vPosition;

  // Simplex 2D noise
  vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

  float snoise(vec2 v){
    const vec4 C = vec4(0.211324865405187, 0.366025403784439,
             -0.577350269189626, 0.024390243902439);
    vec2 i  = floor(v + dot(v, C.yy) );
    vec2 x0 = v -   i + dot(i, C.xx);
    vec2 i1;
    i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod(i, 289.0);
    vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
    + i.x + vec3(0.0, i1.x, 1.0 ));
    vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
    m = m*m ;
    m = m*m ;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
    vec3 g;
    g.x  = a0.x  * x0.x  + h.x  * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
  }

  void main() {
    vec2 st = vUv * 3.0;
    
    // Acceleration based on scroll
    float time = uTime * 0.05 + (uScroll * 2.0); 

    // Domain Warping
    vec2 q = vec2(0.);
    q.x = snoise(st + vec2(0.0, time));
    q.y = snoise(st + vec2(5.2, 1.3));

    vec2 r = vec2(0.);
    r.x = snoise(st + 1.0*q + vec2(1.7, 9.2) + 0.15*time);
    r.y = snoise(st + 1.0*q + vec2(8.3, 2.8) + 0.126*time);

    float f = snoise(st + r);

    // Color Mixing based on noise value 'f'
    // Map -1..1 to 0..1
    float mixVal = f * 0.5 + 0.5;

    // Shift colors slightly based on scroll
    vec3 colorA = mix(uColorA, vec3(0.0), uScroll * 0.5); // Darken base on scroll
    vec3 colorB = mix(uColorB, uColorC, uScroll * 0.3);   // Shift primary to accent

    // Deep fluid colors
    vec3 color = mix(colorA, colorB, smoothstep(0.0, 0.6, mixVal));
    color = mix(color, uColorC, smoothstep(0.4, 1.0, mixVal));

    // Add a tech-grid overlay effect (subtle lines)
    float gridStrength = 0.1 + (uScroll * 0.2); // Grid gets stronger when scrolling
    float grid = step(0.98, fract(vUv.x * 40.0)) * gridStrength + step(0.98, fract(vUv.y * 40.0)) * gridStrength;
    color += vec3(grid * 0.3); // Faint grid lines

    // Vignette
    float dist = distance(vUv, vec2(0.5));
    color *= 1.0 - dist * 0.9; // Stronger vignette for depth

    gl_FragColor = vec4(color, 1.0);
  }
`;

const FluidShader: React.FC = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uScroll: { value: 0 },
      // Dark Purple base
      uColorA: { value: new THREE.Color('#000000') }, 
      // Deep Indigo
      uColorB: { value: new THREE.Color('#1a0b2e') }, 
      // Dark Violet Accent
      uColorC: { value: new THREE.Color('#4c1d95') }, 
    }),
    []
  );

  useFrame((state) => {
    if (materialRef.current) {
      // Time accumulation
      materialRef.current.uniforms.uTime.value = state.clock.getElapsedTime();
      
      // Read scroll directly for performance
      const scrollY = window.scrollY;
      const height = window.innerHeight;
      // Normalized scroll 0..1 (capped for visual consistency)
      const scrollProgress = Math.min(scrollY / height, 1.5);
      
      // Interpolate for smoothness
      materialRef.current.uniforms.uScroll.value = THREE.MathUtils.lerp(
        materialRef.current.uniforms.uScroll.value,
        scrollProgress,
        0.1
      );
    }
  });

  return (
    <mesh ref={meshRef} position={[0, 0, 0]} scale={[2, 2, 1]}>
      <planeGeometry args={[10, 10, 32, 32]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
};

export default FluidShader;
