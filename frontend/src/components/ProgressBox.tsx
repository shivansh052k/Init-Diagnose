import type { ProgressEvent } from '../types'
import { CheckCircle, XCircle, Loader2, Info } from 'lucide-react'

interface Props {
  events: ProgressEvent[]
  dark: boolean
  done: boolean
}

const icon = (e: ProgressEvent) => {
  if (e.step === 'success') return <CheckCircle size={12} className="text-emerald-400 shrink-0 mt-0.5" />
  if (e.step === 'error')   return <XCircle     size={12} className="text-red-400 shrink-0 mt-0.5" />
  if (e.step === 'query')   return <Loader2     size={12} className="text-indigo-400 shrink-0 mt-0.5 animate-spin" />
  return                           <Info        size={12} className="text-slate-500 shrink-0 mt-0.5" />
}

export default function ProgressBox({ events, dark, done }: Props) {
  const panel  = dark ? 'bg-[#1a1d27]'     : 'bg-[#ede4da]'
  const border = dark ? 'border-[#2a2d3a]' : 'border-[#d4c4b5]'
  const text   = dark ? 'text-slate-300'   : 'text-[#5c3d2e]'
  const sub    = dark ? 'text-slate-600'   : 'text-[#8c7468]'

  return (
    <div className={`rounded-xl border ${border} ${panel} overflow-hidden`}>
      <div className={`px-4 py-2.5 border-b ${border} flex items-center justify-between`}>
        <span className={`text-xs uppercase tracking-widest ${sub}`}>Pipeline Progress</span>
        {!done && <Loader2 size={12} className="text-indigo-400 animate-spin" />}
        {done  && <CheckCircle size={12} className="text-emerald-400" />}
      </div>
      <div className="px-4 py-3 flex flex-col gap-1.5 max-h-56 overflow-y-auto font-mono">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-2">
            {icon(e)}
            <span className={`text-xs leading-relaxed ${
              e.step === 'success' ? 'text-emerald-400' :
              e.step === 'error'   ? 'text-red-400'     :
              e.step === 'query'   ? 'text-indigo-400'  :
              text
            }`}>
              {e.msg}
            </span>
          </div>
        ))}
        {!done && events.length === 0 && (
          <span className={`text-xs ${sub}`}>Initializing...</span>
        )}
      </div>
    </div>
  )
}