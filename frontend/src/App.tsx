import { useState, useRef, useEffect } from 'react'
import { analyze } from './api'
import type { InferResponse, ProgressEvent } from './types'
import ResultPanel from './components/ResultPanel'
import ProgressBox from './components/ProgressBox'
import { Activity, Loader2, AlertCircle, Sun, Moon } from 'lucide-react'

const SAMPLE_NOTE = `Patient, 34F, presents with severe depressive episode lasting 8 weeks.
PHQ-9 score of 22. GAF score 35. Reports active suicidal ideation with plan.
History of Bipolar I Disorder. Currently prescribed Quetiapine 400mg and Lithium 900mg.
Recent psychotic symptoms including auditory hallucinations. Last hospitalization 3 months ago.`

export default function App() {
  const [note, setNote]         = useState('')
  const [result, setResult]     = useState<InferResponse | null>(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [override, setOverride] = useState<'fast' | 'full' | null>(null)
  const [dark, setDark]         = useState(false)
  const [events, setEvents]     = useState<ProgressEvent[]>([])
  const [streaming, setStreaming] = useState(false)

  const resultRef = useRef<HTMLDivElement>(null)
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  async function handleSubmit() {
    if (!note.trim()) return
    setLoading(true)
    setStreaming(true)
    setError(null)
    setResult(null)
    setEvents([])

    try {
      const res = await fetch('/infer/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note, mode_override: override }),
      })

      const reader = res.body!.getReader()
      readerRef.current = reader
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          const event: ProgressEvent = JSON.parse(line.slice(6))

          if (event.type === 'done' && event.result) {
            setResult(event.result)
            setStreaming(false)
            setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
          } else if (event.type === 'error') {
            setError(event.msg ?? 'Unknown error')
            setStreaming(false)
          } else {
            setEvents(prev => [...prev, event])
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function handleStop() {
    readerRef.current?.cancel()
    readerRef.current = null
    setStreaming(false)
    setLoading(false)
    setEvents(prev => [...prev, { type: 'progress', step: 'error', msg: 'Stopped by user.' }])
  }

  const bg       = dark ? 'bg-[#0f1117]'     : 'bg-[#f5ede4]'
  const panel    = dark ? 'bg-[#1a1d27]'     : 'bg-[#ede4da]'
  const border   = dark ? 'border-[#2a2d3a]' : 'border-[#d4c4b5]'
  const text     = dark ? 'text-slate-100'   : 'text-[#3d2b1f]'
  const subtext  = dark ? 'text-slate-500'   : 'text-[#8c7468]'
  const inputBg  = dark
    ? 'bg-[#1a1d27] text-slate-200 placeholder-slate-600'
    : 'bg-[#f0e6db] text-[#3d2b1f] placeholder-[#b8a498]'
  const btnClass = dark
    ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
    : 'bg-[#3d2b1f] hover:bg-[#5c3d2e] text-[#f5ede4]'
  const accentText = dark ? 'text-indigo-400' : 'text-[#a85a4a]'

  return (
    <div className={`min-h-screen transition-colors duration-300 ${bg}`}>

      {/* Header */}
      <header className={`border-b ${border} ${dark ? 'bg-[#0f1117]/80' : 'bg-[#f5ede4]/80'} backdrop-blur-sm sticky top-0 z-10`}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg ${dark ? 'bg-indigo-500/20 border-indigo-500/30' : 'bg-[#a85a4a]/10 border-[#a85a4a]/30'} border flex items-center justify-center`}>
              <Activity size={16} className={accentText} />
            </div>
            <div>
              <h1 className={`text-sm font-semibold tracking-tight font-serif ${text}`}>Init-Diagnose</h1>
              <p className={`text-xs ${subtext}`}>Clinical Triage Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className={`text-xs ${subtext}`}>Pipeline Ready</span>
            </div>
            <button
              onClick={() => setDark(d => !d)}
              className={`w-8 h-8 rounded-lg border ${border} ${panel} flex items-center justify-center transition-all`}
            >
              {dark
                ? <Sun size={14} className="text-amber-400" />
                : <Moon size={14} className="text-[#8c7468]" />
              }
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">

          {/* Left panel */}
          <div className="flex flex-col gap-5">
            <div>
              <p className={`text-xs uppercase tracking-widest ${subtext} mb-1`}>Patient Record</p>
              <h2 className={`text-2xl font-serif ${text}`}>Clinical Note</h2>
              <p className={`text-sm ${subtext} mt-1`}>
                Pipeline auto-selects analysis mode based on note quality
              </p>
            </div>

            <textarea
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Patient presents with..."
              rows={12}
              className={`w-full rounded-xl border ${border} ${inputBg}
                         px-4 py-3 resize-none focus:outline-none focus:ring-1
                         ${dark ? 'focus:ring-indigo-500/50 focus:border-indigo-500/50' : 'focus:ring-[#a85a4a]/40 focus:border-[#a85a4a]/40'}
                         transition-all font-mono text-sm leading-relaxed`}
            />

            {/* Mode */}
            <div className="flex items-center gap-2">
              <span className={`text-xs ${subtext}`}>Mode:</span>
              {(['auto', 'fast', 'full'] as const).map(m => (
                <button
                  key={m}
                  onClick={() => setOverride(m === 'auto' ? null : m)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all
                    ${(m === 'auto' && override === null) || m === override
                      ? dark
                        ? 'border-indigo-500/50 bg-indigo-500/10 text-indigo-400'
                        : 'border-[#a85a4a]/50 bg-[#a85a4a]/10 text-[#a85a4a]'
                      : `${border} ${panel} ${subtext}`
                    }`}
                >
                  {m}
                </button>
              ))}
            </div>

            <button
              onClick={() => setNote(SAMPLE_NOTE)}
              className={`text-xs ${subtext} hover:${accentText} transition-colors text-left`}
            >
              ↗ Load sample high-risk note
            </button>

            {/* Submit + Stop */}
            <div className="flex gap-2">
              <button
                onClick={handleSubmit}
                disabled={loading || !note.trim()}
                className={`flex items-center justify-center gap-2 flex-1 py-3 rounded-xl
                           ${btnClass} disabled:opacity-40 disabled:cursor-not-allowed
                           text-sm font-semibold transition-all active:scale-95`}
              >
                {loading
                  ? <><Loader2 size={16} className="animate-spin" /> Analyzing...</>
                  : 'Analyze Patient →'
                }
              </button>
              {streaming && (
                <button
                  onClick={handleStop}
                  className="px-4 py-3 rounded-xl border border-red-500/40 bg-red-500/10 text-red-400 text-sm font-semibold hover:bg-red-500/20 transition-all"
                >
                  Stop
                </button>
              )}
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
                <AlertCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
                <p className="text-xs text-red-400">{error}</p>
              </div>
            )}

            {(streaming || events.length > 0) && (
              <ProgressBox events={events} dark={dark} done={!streaming} />
            )}
          </div>

          {/* Right panel */}
          <div ref={resultRef}>
            {result
              ? <ResultPanel result={result} dark={dark} />
              : (
                <div className={`flex flex-col items-center justify-center h-96 rounded-xl border border-dashed ${border} gap-3`}>
                  <Activity size={32} className={`${subtext} opacity-20`} />
                  <p className={`text-sm font-serif ${subtext}`}>Results appear here</p>
                </div>
              )
            }
          </div>

        </div>
      </main>
    </div>
  )
}