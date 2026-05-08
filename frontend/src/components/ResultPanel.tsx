import { useState } from 'react'
import type { InferResponse, GraphData } from '../types'
import RiskGauge from './RiskGauge'
import { ChevronDown, ChevronUp, Zap, Network, Clock } from 'lucide-react'
import GraphView from './GraphView'

interface Props {
  result: InferResponse
  dark: boolean
}

const FEATURE_LABELS: Record<string, string> = {
  has_bipolar_disorder:       'Bipolar Disorder',
  has_psychotic_disorder:     'Psychotic Disorder',
  has_mood_disorder:          'Mood Disorder',
  has_anxiety_disorder:       'Anxiety Disorder',
  has_personality_disorder:   'Personality Disorder',
  suicidal_ideation_severity: 'Suicidal Ideation',
  has_severe_episode:         'Severe Episode',
  phq9_norm:                  'PHQ-9 Score',
  gaf_risk:                   'GAF Risk',
  has_antipsychotic:          'Antipsychotic Prescribed',
  age_norm:                   'Patient Age',
  num_medications:            'Medication Count',
  num_diagnoses:              'Diagnosis Count',
  episode_count_norm:         'Episode Count',
  gender_female:              'Female Gender',
  gender_nonbinary:           'Non-binary Gender',
}

export default function ResultPanel({ result, dark }: Props) {
  const [contextOpen, setContextOpen] = useState(false)

  const panel   = dark ? 'bg-[#1a1d27]'     : 'bg-white'
  const border  = dark ? 'border-[#2a2d3a]' : 'border-slate-200'
  const subtext = dark ? 'text-slate-500'   : 'text-slate-400'
  const text    = dark ? 'text-slate-200'   : 'text-slate-700'

  const maxImportance = Math.max(...result.top_factors.map(f => f.importance))

  return (
    <div className="flex flex-col gap-6 animate-slide-up">

      {/* Gauge */}
      <div className="flex justify-center">
        <RiskGauge score={result.risk_score} level={result.triage_level} />
      </div>

      {/* Recommendation */}
      <div className={`rounded-xl border ${border} ${panel} px-5 py-4`}>
        <p className={`text-xs ${subtext} uppercase tracking-widest mb-1`}>Recommendation</p>
        <p className={`text-sm ${text} leading-relaxed`}>{result.recommendation}</p>
      </div>

      {/* Top factors */}
      <div className={`rounded-xl border ${border} ${panel} px-5 py-4`}>
        <p className={`text-xs ${subtext} uppercase tracking-widest mb-4`}>Top Risk Factors</p>
        <div className="flex flex-col gap-3">
          {result.top_factors.map((f, i) => (
            <div key={i}>
              <div className="flex justify-between text-xs mb-1">
                <span className={text}>
                  {FEATURE_LABELS[f.feature] ?? f.feature}
                </span>
                <span className={`${subtext} font-mono`}>
                  {(f.importance * 100).toFixed(1)}%
                </span>
              </div>
              <div className={`h-1.5 rounded-full ${dark ? 'bg-[#2a2d3a]' : 'bg-slate-100'} overflow-hidden`}>
                <div
                  className="h-full rounded-full bg-indigo-500"
                  style={{
                    width: `${(f.importance / maxImportance) * 100}%`,
                    transition: `width ${0.4 + i * 0.1}s cubic-bezier(0.34, 1.56, 0.64, 1)`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap gap-3">
        <div className={`flex items-center gap-1.5 text-xs ${subtext} ${panel} border ${border} rounded-lg px-3 py-2`}>
          {result.mode_used === 'fast'
            ? <Zap size={12} className="text-amber-400" />
            : <Network size={12} className="text-indigo-400" />
          }
          <span className="capitalize">{result.mode_used} mode</span>
        </div>
        <div className={`flex items-center gap-1.5 text-xs ${subtext} ${panel} border ${border} rounded-lg px-3 py-2`}>
          <Clock size={12} />
          <span>
            {result.latency_ms < 1000
              ? `${result.latency_ms.toFixed(0)}ms`
              : `${(result.latency_ms / 1000).toFixed(1)}s`
            }
          </span>
        </div>
        <div className={`flex-1 text-xs ${subtext} ${panel} border ${border} rounded-lg px-3 py-2 min-w-0`}>
          <span className="truncate block">{result.mode_reason}</span>
        </div>
      </div>

      {/* Graph context collapsible */}
      {result.graphrag_context && (
        <div className={`rounded-xl border ${border} ${panel} overflow-hidden`}>
          <button
            onClick={() => setContextOpen(o => !o)}
            className={`w-full flex items-center justify-between px-5 py-3 text-xs ${subtext} hover:text-indigo-400 transition-colors`}
          >
            <span className="uppercase tracking-widest">Graph Context</span>
            {contextOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {contextOpen && (
            <div className="px-5 pb-4">
              <pre className={`text-xs ${subtext} whitespace-pre-wrap leading-relaxed font-mono max-h-48 overflow-y-auto`}>
                {result.graphrag_context}
              </pre>
            </div>
          )}
        </div>
      )}
      {/* Knowledge Graph */}
      {result.graph_data && result.graph_data.nodes.length > 1 && (
        <div className={`rounded-xl border ${border} ${panel} overflow-hidden`}>
          <div className={`px-5 py-3 border-b ${border}`}>
            <p className={`text-xs ${subtext} uppercase tracking-widest`}>Knowledge Graph</p>
          </div>
          <div className="p-4">
            <GraphView data={result.graph_data} dark={dark} />
          </div>
        </div>
      )}
    </div>
  )
}