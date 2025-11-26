// Particle Effects System for ROOMie
// Creates stunning mood-based particle effects around the avatar
import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const PARTICLE_CONFIGS = {
    happy: {
        color: new THREE.Color(0xffd700), // Gold
        count: 1200,
        size: 0.08,
        speed: 0.8,
        spread: 4,
        direction: 'up', // Floating up like bubbles/confetti
        opacity: 0.9,
        glow: true,
        variation: 'rainbow' // New: varied colors
    },
    sad: {
        color: new THREE.Color(0x4a90e2), // Blue
        count: 1500,
        size: 0.03,
        speed: 1.5, // Faster falling
        spread: 3,
        direction: 'down', // Rain
        opacity: 0.7,
        glow: false,
        variation: 'none'
    },
    angry: {
        color: new THREE.Color(0xff4444), // Red
        count: 1500,
        size: 0.06,
        speed: 1.2,
        spread: 2.5,
        direction: 'fire', // New direction type
        opacity: 0.8,
        glow: true,
        variation: 'fire' // Orange/Red mix
    },
    neutral: {
        color: new THREE.Color(0xcccccc), // White
        count: 300,
        size: 0.02,
        speed: 0.1,
        spread: 3,
        direction: 'float',
        opacity: 0.4,
        glow: false,
        variation: 'none'
    },
    calm: {
        color: new THREE.Color(0x10b981), // Green
        count: 400,
        size: 0.04,
        speed: 0.2,
        spread: 2.5,
        direction: 'float',
        opacity: 0.6,
        glow: true,
        variation: 'none'
    },
    stressed: {
        color: new THREE.Color(0xf59e0b), // Orange
        count: 800,
        size: 0.05,
        speed: 0.9,
        spread: 3,
        direction: 'chaotic',
        opacity: 0.75,
        glow: true,
        variation: 'none'
    },
    surprise: {
        color: new THREE.Color(0xff00ff), // Magenta/Purple
        count: 1000,
        size: 0.09,
        speed: 2.0,
        spread: 5,
        direction: 'burst',
        opacity: 0.9,
        glow: true,
        variation: 'rainbow'
    }
};

export default function ParticleSystem({ mood = 'neutral', intensity = 1.0 }) {
    const particlesRef = useRef();
    const velocitiesRef = useRef([]);
    const config = PARTICLE_CONFIGS[mood] || PARTICLE_CONFIGS.neutral;

    // Create particles
    const particles = useMemo(() => {
        const count = Math.floor(config.count * intensity);
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const sizes = new Float32Array(count);
        const velocities = [];

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;

            // Random position in sphere
            const radius = Math.random() * config.spread;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;

            positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i3 + 2] = radius * Math.cos(phi);

            // Color logic
            if (config.variation === 'rainbow') {
                const hue = Math.random();
                const color = new THREE.Color().setHSL(hue, 1, 0.6);
                colors[i3] = color.r;
                colors[i3 + 1] = color.g;
                colors[i3 + 2] = color.b;
            } else if (config.variation === 'fire') {
                const hue = 0.0 + Math.random() * 0.1; // Red to Orange
                const color = new THREE.Color().setHSL(hue, 1, 0.5);
                colors[i3] = color.r;
                colors[i3 + 1] = color.g;
                colors[i3 + 2] = color.b;
            } else {
                const colorVariation = 0.1;
                colors[i3] = config.color.r + (Math.random() - 0.5) * colorVariation;
                colors[i3 + 1] = config.color.g + (Math.random() - 0.5) * colorVariation;
                colors[i3 + 2] = config.color.b + (Math.random() - 0.5) * colorVariation;
            }

            // Size with variation
            sizes[i] = config.size * (0.5 + Math.random() * 0.5);

            // Velocity based on direction
            velocities.push({
                x: (Math.random() - 0.5) * 0.02,
                y: (Math.random() - 0.5) * 0.02,
                z: (Math.random() - 0.5) * 0.02,
                angle: Math.random() * Math.PI * 2,
                radius: radius,
                speedOffset: Math.random() * 0.5 // Varied speed
            });
        }

        velocitiesRef.current = velocities;

        return { positions, colors, sizes, count };
    }, [mood, intensity]);

    // Animate particles
    useFrame((state, delta) => {
        if (!particlesRef.current) return;

        const positions = particlesRef.current.geometry.attributes.position.array;
        const count = particles.count;
        const time = state.clock.elapsedTime;

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            const velocity = velocitiesRef.current[i];

            switch (config.direction) {
                case 'up':
                    // Float upward (Bubbles/Confetti)
                    positions[i3 + 1] += (config.speed + velocity.speedOffset) * delta * 0.5;
                    positions[i3] += Math.sin(time + i) * 0.005; // Gentle sway
                    positions[i3 + 2] += Math.cos(time + i) * 0.005;

                    // Reset if too high
                    if (positions[i3 + 1] > config.spread) {
                        positions[i3 + 1] = -config.spread;
                        positions[i3] = (Math.random() - 0.5) * config.spread; // Randomize X on reset
                        positions[i3 + 2] = (Math.random() - 0.5) * config.spread; // Randomize Z on reset
                    }
                    break;

                case 'down':
                    // Fall downward (Rain)
                    positions[i3 + 1] -= (config.speed + velocity.speedOffset) * delta;
                    // No sway for rain, straight down looks better

                    // Reset if too low
                    if (positions[i3 + 1] < -config.spread) {
                        positions[i3 + 1] = config.spread;
                        positions[i3] = (Math.random() - 0.5) * config.spread;
                        positions[i3 + 2] = (Math.random() - 0.5) * config.spread;
                    }
                    break;

                case 'fire':
                    // Rising fire
                    positions[i3 + 1] += (config.speed + velocity.speedOffset) * delta;
                    positions[i3] += (Math.random() - 0.5) * 0.05; // Jitter
                    positions[i3 + 2] += (Math.random() - 0.5) * 0.05;

                    // Reset if too high
                    if (positions[i3 + 1] > config.spread * 0.5) { // Fire dies out faster
                        positions[i3 + 1] = -config.spread * 0.2;
                        positions[i3] = (Math.random() - 0.5) * config.spread * 0.5; // Cone shape
                        positions[i3 + 2] = (Math.random() - 0.5) * config.spread * 0.5;
                    }
                    break;

                case 'chaotic':
                    // Aggressive random movement
                    positions[i3] += velocity.x * config.speed * 5;
                    positions[i3 + 1] += velocity.y * config.speed * 5;
                    positions[i3 + 2] += velocity.z * config.speed * 5;

                    // Bounce off boundaries
                    if (Math.abs(positions[i3]) > config.spread) velocity.x *= -1;
                    if (Math.abs(positions[i3 + 1]) > config.spread) velocity.y *= -1;
                    if (Math.abs(positions[i3 + 2]) > config.spread) velocity.z *= -1;
                    break;

                case 'orbit':
                    // Circular orbit
                    velocity.angle += config.speed * delta;
                    positions[i3] = Math.cos(velocity.angle) * velocity.radius;
                    positions[i3 + 2] = Math.sin(velocity.angle) * velocity.radius;
                    positions[i3 + 1] += Math.sin(time * 2 + i) * 0.01;
                    break;

                case 'float':
                    // Gentle floating
                    positions[i3] += Math.sin(time + i) * 0.01 * config.speed;
                    positions[i3 + 1] += Math.cos(time * 0.5 + i) * 0.01 * config.speed;
                    positions[i3 + 2] += Math.sin(time * 0.3 + i) * 0.01 * config.speed;
                    break;

                case 'spiral':
                    // Spiral motion
                    velocity.angle += config.speed * delta * 2;
                    velocity.radius += Math.sin(time + i) * 0.01;
                    positions[i3] = Math.cos(velocity.angle) * velocity.radius;
                    positions[i3 + 1] += config.speed * delta * 0.3;
                    positions[i3 + 2] = Math.sin(velocity.angle) * velocity.radius;

                    if (positions[i3 + 1] > config.spread) {
                        positions[i3 + 1] = -config.spread;
                        velocity.radius = Math.random() * config.spread;
                    }
                    break;

                case 'burst':
                    // Explosive burst
                    const distance = Math.sqrt(
                        positions[i3] ** 2 +
                        positions[i3 + 1] ** 2 +
                        positions[i3 + 2] ** 2
                    );

                    if (distance < config.spread) {
                        positions[i3] += velocity.x * config.speed * 3;
                        positions[i3 + 1] += velocity.y * config.speed * 3;
                        positions[i3 + 2] += velocity.z * config.speed * 3;
                    } else {
                        // Reset to center
                        positions[i3] *= 0.1;
                        positions[i3 + 1] *= 0.1;
                        positions[i3 + 2] *= 0.1;
                    }
                    break;
            }
        }

        particlesRef.current.geometry.attributes.position.needsUpdate = true;
    });

    return (
        <points ref={particlesRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={particles.count}
                    array={particles.positions}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-color"
                    count={particles.count}
                    array={particles.colors}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-size"
                    count={particles.count}
                    array={particles.sizes}
                    itemSize={1}
                />
            </bufferGeometry>
            <pointsMaterial
                size={config.size}
                vertexColors
                transparent
                opacity={config.opacity}
                sizeAttenuation
                blending={THREE.AdditiveBlending}
                depthWrite={false}
            />
        </points>
    );
}
