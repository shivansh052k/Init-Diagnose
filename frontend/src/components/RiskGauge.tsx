import { useEffect, useState } from 'react'

interface Props {
  score: number
  level: 'Low' | 'Medium' | 'High'
}

const LEVEL = {
  Low:    { color: '#10b981', glow: '0 0 40px rgba(16,185,129,0.5)',  ring: 'rgba(16,185,129,0.15)',  label: 'text-emerald-500' },
  Medium: { color: '#f59e0b', glow: '0 0 40px rgba(245,158,11,0.5)', ring: 'rgba(245,158,11,0.15)', label: 'text-amber-500'   },
  High:   { color: '#ef4444', glow: '0 0 60px rgba(239,68,68,0.6)',  ring: 'rgba(239,68,68,0.15)',  label: 'text-red-500'     },
}

export default function RiskGauge({ score, level }: Props) {
  const [displayed, setDisplayed] = useState(0)
  const [mounted, setMounted]     = useState(false)
  const cfg = LEVEL[level]

  // Count-up animation
  useEffect(() => {
    setDisplayed(0)
    setMounted(false)
    const t = setTimeout(() => {
      setMounted(true)
      const target = Math.round(score * 100)
      const duration = 1000
      const steps = 40
      const increment = target / steps
      let current = 0
      let step = 0
      const interval = setInterval(() => {
        step++
        current = Math.min(Math.round(increment * step), target)
        setDisplayed(current)
        if (step >= steps) clearInterval(interval)
      }, duration / steps)
      return () => clearInterval(interval)
    }, 80)
    return () => clearTimeout(t)
  }, [score, level])

  const size = 200
  const orb = mounted ? size : size * 0.85

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        className="relative flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        {/* Outer pulse ring */}
        <div
          className="absolute rounded-full"
          style={{
            width: orb + 32,
            height: orb + 32,
            background: cfg.ring,
            transition: 'all 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
            animation: level === 'High' ? 'pulse 2s ease-in-out infinite' : undefined,
          }}
        />

        {/* Mid ring */}
        <div
          className="absolute rounded-full"
          style={{
            width: orb + 12,
            height: orb + 12,
            background: cfg.ring,
            opacity: 0.6,
            transition: 'all 1s cubic-bezier(0.34, 1.56, 0.64, 1)',
          }}
        />

        {/* Core orb */}
        <div
          className="absolute rounded-full flex flex-col items-center justify-center"
          style={{
            width: orb,
            height: orb,
            background: `radial-gradient(circle at 35% 35%, ${cfg.color}33, ${cfg.color}11)`,
            border: `2px solid ${cfg.color}55`,
            boxShadow: mounted ? cfg.glow : 'none',
            transition: 'all 1s cubic-bezier(0.34, 1.56, 0.64, 1)',
          }}
        >
          {/* Score number */}
          <span
            className={`text-5xl font-bold font-mono tabular-nums ${cfg.label}`}
            style={{ transition: 'color 0.6s ease', lineHeight: 1 }}
          >
            {displayed}
          </span>
          <span className="text-xs text-slate-500 uppercase tracking-widest mt-1">
            risk score
          </span>
        </div>
      </div>

      {/* Triage badge */}
      <div
        className={`px-6 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest border
          ${level === 'High'   ? 'border-red-500/40 text-red-400 bg-red-500/10'         : ''}
          ${level === 'Medium' ? 'border-amber-500/40 text-amber-400 bg-amber-500/10'   : ''}
          ${level === 'Low'    ? 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10' : ''}
          ${level === 'High'   ? 'animate-pulse' : ''}
        `}
      >
        {level} Risk
      </div>
    </div>
  )
}