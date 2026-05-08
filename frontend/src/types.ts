export interface InferRequest {
  note: string
  mode_override?: 'fast' | 'full' | null
}

export interface Factor {
  feature: string
  value: number
  importance: number
}

export interface InferResponse {
  risk_score: number
  triage_level: 'Low' | 'Medium' | 'High'
  recommendation: string
  top_factors: Factor[]
  mode_used: 'fast' | 'full'
  mode_reason: string
  latency_ms: number
  graphrag_context: string | null
  graph_data: GraphData | null
}

export interface GraphNode {
  id: string
  name: string
  type: 'patient' | 'diagnosis' | 'medication' | 'symptom' | 'assessment'
  val?: number
}

export interface GraphLink {
  source: string
  target: string
  label?: string
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface ProgressEvent {
  type: 'progress' | 'done' | 'error'
  step?: 'info' | 'query' | 'success' | 'error' | 'done'
  msg?: string
  current?: number
  total?: number
  result?: InferResponse
}