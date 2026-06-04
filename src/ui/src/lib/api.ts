const BASE = '/api'

export interface DocumentItem {
  filename: string
  chunks: number
}

export interface StatusResponse {
  total_chunks: number
  documents: DocumentItem[]
}

export interface ModelItem {
  name: string
  current: boolean
}

export interface ModelsResponse {
  models: ModelItem[]
  current: string
}

export interface QueryResponse {
  answer: string
  sources: { source: string; chunk_index: number }[]
  session_id: string
}

export interface DocumentIngestResponse {
  filename: string
  chunks_created: number
  total_chunks: number
}

async function handleResponse<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(body.detail || body.errors?.[0] || resp.statusText)
  }
  return resp.json()
}

export async function getStatus(): Promise<StatusResponse> {
  const resp = await fetch(`${BASE}/status`)
  return handleResponse<StatusResponse>(resp)
}

export async function getModels(): Promise<ModelsResponse> {
  const resp = await fetch(`${BASE}/models`)
  return handleResponse<ModelsResponse>(resp)
}

export async function getDocuments(): Promise<DocumentItem[]> {
  const resp = await fetch(`${BASE}/documents`)
  return handleResponse<DocumentItem[]>(resp)
}

export async function uploadDocument(file: File): Promise<DocumentIngestResponse> {
  const form = new FormData()
  form.append('file', file)
  const resp = await fetch(`${BASE}/documents/upload`, { method: 'POST', body: form })
  return handleResponse<DocumentIngestResponse>(resp)
}

export async function deleteDocument(filename: string): Promise<{ filename: string; chunks_removed: number }> {
  const resp = await fetch(`${BASE}/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' })
  return handleResponse(resp)
}

export async function clearDocuments(): Promise<{ message: string }> {
  const resp = await fetch(`${BASE}/documents`, { method: 'DELETE' })
  return handleResponse(resp)
}

export async function sendQuery(question: string, sessionId?: string, topK?: number): Promise<QueryResponse> {
  const resp = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId, top_k: topK }),
  })
  return handleResponse<QueryResponse>(resp)
}
