import React, { useEffect, useRef } from 'react';
import { useAppContext } from '../context/AppContext';

interface Wave {
  y: number;
  length: number;
  amplitude: number;
  frequency: number;
  speed: number;
  color: string;
}

const WaveBackground: React.FC = () => {
  const { theme } = useAppContext();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });
  const ripplesRef = useRef<{ x: number; y: number; r: number; opacity: number }[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let time = 0;

    const waves: Wave[] = [
      {
        y: 0.5,
        length: 0.01,
        amplitude: 40,
        frequency: 0.01,
        speed: 0.02,
        color: theme === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.15)',
      },
      {
        y: 0.55,
        length: 0.008,
        amplitude: 60,
        frequency: 0.015,
        speed: -0.015,
        color: theme === 'dark' ? 'rgba(139, 92, 246, 0.08)' : 'rgba(139, 92, 246, 0.12)',
      },
      {
        y: 0.45,
        length: 0.012,
        amplitude: 30,
        frequency: 0.02,
        speed: 0.01,
        color: theme === 'dark' ? 'rgba(99, 102, 241, 0.05)' : 'rgba(99, 102, 241, 0.1)',
      },
    ];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.active = true;
    };

    const handleClick = (e: MouseEvent) => {
      ripplesRef.current.push({
        x: e.clientX,
        y: e.clientY,
        r: 0,
        opacity: 0.5,
      });
    };

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleClick);
    resize();

    const animate = () => {
      time += 0.015;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Background color based on theme
      const bgColor = theme === 'dark' ? '#0a0a0a' : '#ffffff';
      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Waves
      waves.forEach((wave) => {
        ctx.beginPath();
        ctx.moveTo(0, canvas.height);

        for (let x = 0; x <= canvas.width; x += 2) {
          let y = Math.sin(x * wave.length + time * wave.speed) * wave.amplitude;
          y += Math.sin(x * 0.005 + time * 0.8) * 15;

          if (mouseRef.current.active) {
            const dx = x - mouseRef.current.x;
            const dy = (canvas.height * wave.y + y) - mouseRef.current.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 250) {
              const force = (250 - dist) / 250;
              y += dy * force * 0.3;
            }
          }

          ctx.lineTo(x, canvas.height * wave.y + y);
        }

        ctx.lineTo(canvas.width, canvas.height);
        ctx.fillStyle = wave.color;
        ctx.fill();
      });

      // Draw Ripples
      ripplesRef.current = ripplesRef.current.filter((ripple) => ripple.opacity > 0);
      ripplesRef.current.forEach((ripple) => {
        ctx.beginPath();
        ctx.arc(ripple.x, ripple.y, ripple.r, 0, Math.PI * 2);
        ctx.strokeStyle = theme === 'dark' ? `rgba(139, 92, 246, ${ripple.opacity * 0.5})` : `rgba(139, 92, 246, ${ripple.opacity})`;
        ctx.lineWidth = 2;
        ctx.stroke();
        ripple.r += 4;
        ripple.opacity -= 0.01;
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleClick);
      cancelAnimationFrame(animationFrameId);
    };
  }, [theme]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none -z-20"
    />
  );
};

export default WaveBackground;
