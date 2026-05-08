import type { InferRequest, InferResponse } from './types'

export async function analyze(request: InferRequest): Promise<InferResponse> {
  const res = await fetch('/infer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API error ${res.status}: ${err}`)
  }

  return res.json()
}