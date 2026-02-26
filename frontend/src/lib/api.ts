import type { JobCreatedResponse, ProductDetail, ProductSummary, SseEvent } from '@/types/extraction'

const API_URL = import.meta.env.VITE_API_URL ?? '/api'

/**
 * Upload a PDF via XHR (preserves upload progress tracking).
 * Returns a job_id for the SSE extraction stream.
 */
export function uploadTermsheetAsync(
  file: File,
  onProgress: (percent: number) => void,
): Promise<JobCreatedResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as JobCreatedResponse)
      } else {
        try {
          const body = JSON.parse(xhr.responseText)
          reject(new Error(body.detail ?? `Upload failed (${xhr.status})`))
        } catch {
          reject(new Error(`Upload failed (${xhr.status})`))
        }
      }
    })

    xhr.addEventListener('error', () => reject(new Error('Network error')))

    xhr.open('POST', `${API_URL}/upload-termsheet-async`)
    xhr.send(formData)
  })
}

/**
 * Connect to the SSE extraction stream.
 * Calls onEvent for each SSE message. Returns an abort function.
 */
export function connectExtractionStream(
  jobId: string,
  onEvent: (event: SseEvent) => void,
  onError: (error: Error) => void,
): () => void {
  const controller = new AbortController()

  fetch(`${API_URL}/extraction-stream/${jobId}`, {
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `Stream failed (${response.status})`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE lines: "data: {...}\n\n"
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          const line = part.trim()
          if (line.startsWith('data: ')) {
            const json = line.slice(6)
            try {
              onEvent(JSON.parse(json) as SseEvent)
            } catch {
              // skip malformed events
            }
          }
        }
      }
    })
    .catch((err: unknown) => {
      if (err instanceof Error && err.name === 'AbortError') return
      onError(err instanceof Error ? err : new Error(String(err)))
    })

  return () => controller.abort()
}

/**
 * Fetch all products.
 */
export async function fetchProducts(): Promise<ProductSummary[]> {
  const response = await fetch(`${API_URL}/products`)
  if (!response.ok) {
    throw new Error(`Failed to fetch products (${response.status})`)
  }
  return response.json()
}

/**
 * Fetch a single product by ISIN.
 */
export async function fetchProduct(isin: string): Promise<ProductDetail> {
  const response = await fetch(`${API_URL}/products/${isin}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Failed to fetch product (${response.status})`)
  }
  return response.json()
}

/**
 * Approve a product by ISIN.
 */
export async function approveProduct(
  productIsin: string,
): Promise<{ product_isin: string; approved: boolean }> {
  const response = await fetch(`${API_URL}/products/${productIsin}/approve`, {
    method: 'PATCH',
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Approval failed (${response.status})`)
  }
  return response.json()
}
