import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";

/*
  Landing page hero sequence.
  - Minimal DOM / SVG approach for performance.
  - Lazy-loads GSAP + ScrollTrigger only on this route.
  - Respects prefers-reduced-motion: instant reveal.
*/

export default function HomePage() {
  const heroRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let ctx: any = null;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    async function init() {
      if (!heroRef.current || !svgRef.current) return;

      if (prefersReduced) {
        // reduced motion: reveal state without animation
        heroRef.current.classList.add('revealed');
        setReady(true);
        return;
      }

      const gsap = await import('gsap');
      const ScrollTrigger = (await import('gsap/ScrollTrigger')).default;
      gsap.default.registerPlugin(ScrollTrigger);

      const tl = gsap.default.timeline({
        scrollTrigger: {
          trigger: heroRef.current,
          start: 'top top',
          end: '+=800',
          scrub: true,
          pin: true,
        },
      });

      // single pulsing dot -> multiplicative spread
      const dot = svgRef.current.querySelector('#hero-dot');
      const dotsGroup = svgRef.current.querySelector('#dots');

      tl.to(dot, { attr: { r: 6 }, duration: 0.6, ease: 'power1.out' })
        .to(dot, { attr: { r: 2 }, duration: 0.4 })
        .addLabel('spread')
        .to(dotsGroup, { opacity: 1, duration: 0.8, stagger: 0.02 }, 'spread')
        .to(
          svgRef.current,
          { transform: 'scale(1.04)', duration: 0.8, ease: 'power2.out' },
          'spread'
        );

      setReady(true);
      ctx = tl;
    }

    init();

    return () => {
      try {
        if (ctx && ctx.kill) ctx.kill();
      } catch (e) {
        // ignore
      }
    };
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper-bg)', color: 'var(--ink)' }}>
      <div style={{ display: 'flex', gap: 24, padding: '48px', alignItems: 'flex-start' }}>
        <div style={{ flex: '0 0 520px', maxWidth: 520 }}>
          <h2 style={{ fontFamily: 'Fraunces', fontSize: 48, lineHeight: 1.02, margin: 0 }}>
            Early signal, early action —
            <br />
            <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 48, color: 'var(--ink)' }}>1,284 cases</span>
            <br />
            tracked this month in Gujarat
          </h2>

          <p style={{ marginTop: 16, color: 'rgba(26,29,27,0.8)', fontFamily: 'Plus Jakarta Sans' }}>
            Medical Draft surfaces emerging patterns from scattered clinical reports so hospitals can prepare before
            escalation. The signal-to-noise is subtle — this product shows what matters.
          </p>

          <div style={{ marginTop: 24 }}>
            <Link to="/dashboard" style={{ marginRight: 12, padding: '10px 14px', background: '#171B18', color: 'var(--paper-bg)', borderRadius: 6, textDecoration: 'none', fontFamily: 'Plus Jakarta Sans' }}>
              View Dashboard
            </Link>
            <Link to="/alerts" style={{ padding: '10px 14px', borderRadius: 6, border: '1px solid rgba(0,0,0,0.06)', textDecoration: 'none', fontFamily: 'Plus Jakarta Sans', color: 'var(--ink)' }}>
              Learn more
            </Link>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div ref={heroRef} className="hero-sequence" style={{ width: '100%', height: 420, borderRadius: 8, background: '#0F1210', overflow: 'hidden', border: '1px solid rgba(0,0,0,0.06)' }}>
            <svg ref={svgRef} width="100%" height="100%" viewBox="0 0 800 420" preserveAspectRatio="xMidYMid meet">
              <rect width="100%" height="100%" fill="#0F1210" />
              <g id="map" transform="translate(0,0)">
                <g id="dots" opacity="0">
                  {/* generate a grid of subtle dots to simulate heatmap */}
                  {Array.from({ length: 120 }).map((_, i) => {
                    const x = 80 + ((i * 37) % 640);
                    const y = 60 + (Math.floor(i / 16) * 18) + ((i * 13) % 6);
                    const r = (i % 7 === 0) ? 3.5 : 2.0;
                    return <circle key={i} cx={x} cy={y} r={r} fill="rgba(192,57,43,0.85)" opacity={0.9} />;
                  })}
                </g>
                <g id="focus">
                  <circle id="hero-dot" cx="120" cy="160" r="2" fill="#C0392B" />
                </g>
              </g>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
