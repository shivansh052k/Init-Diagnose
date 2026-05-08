import { useEffect, useState } from 'react'

interface Props {
  score: number
  level: 'Low' | 'Medium' | 'High'
}

const LEVEL_COLORS = {
  Low:    { stroke: '#10b981', glow: 'rgba(16,185,129,0.3)',  text: 'text-emerald-400' },
  Medium: { stroke: '#f59e0b', glow: 'rgba(245,158,11,0.3)',  text: 'text-amber-400'   },
  High:   { stroke: '#ef4444', glow: 'rgba(239,68,68,0.3)',   text: 'text-red-400'     },
}

const SIZE        = 220
const STROKE      = 14
const RADIUS      = (SIZE - STROKE) / 2
const CENTER      = SIZE / 2
const ARC_DEGREES = 240
const ARC_RAD     = (ARC_DEGREES * Math.PI) / 180
const CIRCUMFERENCE = RADIUS * ARC_RAD

function polarToCart(cx: number, cy: number, r: number, deg: number) {
  const rad = (deg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const s = polarToCart(cx, cy, r, startDeg)
  const e = polarToCart(cx, cy, r, endDeg)
  const large = endDeg - startDeg > 180 ? 1 : 0
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`
}

const START_DEG = 150
const END_DEG   = 390

export default function RiskGauge({ score, level }: Props) {
  const [animated, setAnimated] = useState(0)
  const colors = LEVEL_COLORS[level]

  useEffect(() => {
    setAnimated(0)
    const raf = requestAnimationFrame(() => {
      setTimeout(() => setAnimated(score), 50)
    })
    return () => cancelAnimationFrame(raf)
  }, [score, level])

  const trackPath = arcPath(CENTER, CENTER, RADIUS, START_DEG, END_DEG)
  const fillDeg   = START_DEG + ARC_DEGREES * animated
  const fillPath  = arcPath(CENTER, CENTER, RADIUS, START_DEG, fillDeg)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE}>
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Track */}
          <path
            d={trackPath}
            fill="none"
            stroke="#1e2028"
            strokeWidth={STROKE}
            strokeLinecap="round"
          />

          {/* Fill */}
          <path
            d={fillPath}
            fill="none"
            stroke={colors.stroke}
            strokeWidth={STROKE}
            strokeLinecap="round"
            filter="url(#glow)"
            style={{ transition: 'all 1s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={`text-5xl font-bold font-mono tracking-tight ${colors.text}`}
            style={{ transition: 'color 0.6s ease' }}
          >
            {(animated * 100).toFixed(0)}
          </span>
          <span className="text-xs text-slate-500 uppercase tracking-widest mt-1">
            risk score
          </span>
        </div>
      </div>

      {/* Triage badge */}
      <div
        className={`
          px-5 py-1.5 rounded-full text-sm font-semibold uppercase tracking-widest border
          ${level === 'High'   ? 'border-red-500/40 text-red-400 bg-red-500/10 animate-pulse' : ''}
          ${level === 'Medium' ? 'border-amber-500/40 text-amber-400 bg-amber-500/10' : ''}
          ${level === 'Low'    ? 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10' : ''}
        `}
      >
        {level} Risk
      </div>
    </div>
  )
}