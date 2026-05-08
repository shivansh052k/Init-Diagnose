import { useRef, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { GraphData } from '../types'

interface Props {
  data: GraphData
  dark: boolean
}

const NODE_COLORS = {
  patient:    '#6366f1',
  diagnosis:  '#ef4444',
  medication: '#10b981',
  symptom:    '#f59e0b',
  assessment: '#8b5cf6',
}

const NODE_LABELS = {
  patient:    'Patient',
  diagnosis:  'Diagnosis',
  medication: 'Medication',
  symptom:    'Symptom',
  assessment: 'Assessment',
}

export default function GraphView({ data, dark }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const width = containerRef.current?.offsetWidth ?? 500

  const bg     = dark ? '#1a1d27' : '#ede4da'
  const linkColor = dark ? '#2a2d3a' : '#c4b5a8'
  const textColor = dark ? '#e2e8f0' : '#3d2b1f'

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={containerRef}
        className={`rounded-xl overflow-hidden border ${dark ? 'border-[#2a2d3a]' : 'border-[#d4c4b5]'}`}
        style={{ height: 340 }}
      >
        <ForceGraph2D
          graphData={data}
          width={width}
          height={340}
          backgroundColor={bg}
          nodeVal="val"
          nodeLabel="name"
          nodeColor={(n: any) => NODE_COLORS[n.type as keyof typeof NODE_COLORS] ?? '#64748b'}
          linkColor={() => linkColor}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkLabel="label"
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.name as string
            const fontSize = Math.max(10 / globalScale, 4)
            const r = Math.sqrt(node.val ?? 10) * 2

            ctx.beginPath()
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
            ctx.fillStyle = NODE_COLORS[node.type as keyof typeof NODE_COLORS] ?? '#64748b'
            ctx.fill()

            if (globalScale > 0.8) {
              ctx.font = `${fontSize}px Inter, sans-serif`
              ctx.fillStyle = textColor
              ctx.textAlign = 'center'
              ctx.textBaseline = 'top'
              ctx.fillText(label.length > 18 ? label.slice(0, 16) + '…' : label, node.x, node.y + r + 2)
            }
          }}
          cooldownTicks={80}
        />
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 px-1">
        {Object.entries(NODE_LABELS).map(([type, label]) => (
          <div key={type} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: NODE_COLORS[type as keyof typeof NODE_COLORS] }} />
            <span className={`text-xs ${dark ? 'text-slate-500' : 'text-[#8c7468]'}`}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}