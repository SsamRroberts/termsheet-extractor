import { useCallback, useReducer, useRef } from 'react'
import type { ExtractionResponse, SseEvent } from '@/types/extraction'
import { approveProduct, connectExtractionStream, uploadTermsheetAsync } from '@/lib/api'

// ── State ──────────────────────────────────────────────

type Stage =
  | 'extracting_pdf'
  | 'saving_blob'
  | 'llm_extraction'
  | 'validation'
  | 'persisting'

interface IdleState {
  phase: 'idle'
}

interface UploadingState {
  phase: 'uploading'
  filename: string
  uploadProgress: number
}

interface ProcessingState {
  phase: 'processing'
  filename: string
  stage: Stage
  progress: number
}

interface ReviewState {
  phase: 'review'
  extraction: ExtractionResponse
  approving: boolean
}

interface ApprovedState {
  phase: 'approved'
  extraction: ExtractionResponse
}

interface ErrorState {
  phase: 'error'
  message: string
}

export type PipelineState =
  | IdleState
  | UploadingState
  | ProcessingState
  | ReviewState
  | ApprovedState
  | ErrorState

// ── Actions ────────────────────────────────────────────

type Action =
  | { type: 'START_UPLOAD'; filename: string }
  | { type: 'UPLOAD_PROGRESS'; percent: number }
  | { type: 'UPLOAD_DONE' }
  | { type: 'SSE_PROGRESS'; stage: Stage; progress: number }
  | { type: 'SSE_COMPLETE'; data: ExtractionResponse }
  | { type: 'SSE_VALIDATION_FAILED'; data: ExtractionResponse }
  | { type: 'APPROVE_START' }
  | { type: 'APPROVE_DONE' }
  | { type: 'ERROR'; message: string }
  | { type: 'RESET' }

// ── Reducer ────────────────────────────────────────────

function reducer(_state: PipelineState, action: Action): PipelineState {
  switch (action.type) {
    case 'START_UPLOAD':
      return { phase: 'uploading', filename: action.filename, uploadProgress: 0 }
    case 'UPLOAD_PROGRESS':
      if (_state.phase !== 'uploading') return _state
      return { ..._state, uploadProgress: action.percent }
    case 'UPLOAD_DONE':
      if (_state.phase !== 'uploading') return _state
      return { phase: 'processing', filename: _state.filename, stage: 'extracting_pdf', progress: 0 }
    case 'SSE_PROGRESS':
      if (_state.phase !== 'processing') return _state
      return { ..._state, stage: action.stage, progress: action.progress }
    case 'SSE_COMPLETE':
      return { phase: 'review', extraction: action.data, approving: false }
    case 'SSE_VALIDATION_FAILED':
      return { phase: 'review', extraction: action.data, approving: false }
    case 'APPROVE_START':
      if (_state.phase !== 'review') return _state
      return { ..._state, approving: true }
    case 'APPROVE_DONE':
      if (_state.phase !== 'review') return _state
      return { phase: 'approved', extraction: _state.extraction }
    case 'ERROR':
      return { phase: 'error', message: action.message }
    case 'RESET':
      return { phase: 'idle' }
  }
}

// ── Hook ───────────────────────────────────────────────

export function useExtractionPipeline() {
  const [state, dispatch] = useReducer(reducer, { phase: 'idle' })
  const abortRef = useRef<(() => void) | null>(null)

  const handleFile = useCallback((file: File) => {
    dispatch({ type: 'START_UPLOAD', filename: file.name })

    uploadTermsheetAsync(file, (percent) => {
      dispatch({ type: 'UPLOAD_PROGRESS', percent })
    })
      .then((job) => {
        dispatch({ type: 'UPLOAD_DONE' })

        // Connect to SSE stream
        const abort = connectExtractionStream(
          job.job_id,
          (event: SseEvent) => {
            switch (event.stage) {
              case 'extracting_pdf':
              case 'saving_blob':
              case 'llm_extraction':
              case 'validation':
              case 'persisting':
                dispatch({ type: 'SSE_PROGRESS', stage: event.stage, progress: event.progress })
                break
              case 'complete':
                dispatch({ type: 'SSE_COMPLETE', data: event.data })
                break
              case 'validation_failed':
                dispatch({ type: 'SSE_VALIDATION_FAILED', data: event.data })
                break
              case 'error':
                dispatch({ type: 'ERROR', message: event.message })
                break
            }
          },
          (error) => {
            dispatch({ type: 'ERROR', message: error.message })
          },
        )
        abortRef.current = abort
      })
      .catch((err: unknown) => {
        dispatch({ type: 'ERROR', message: err instanceof Error ? err.message : 'Upload failed' })
      })
  }, [])

  const handleApprove = useCallback(async (productIsin: string) => {
    dispatch({ type: 'APPROVE_START' })
    try {
      await approveProduct(productIsin)
      dispatch({ type: 'APPROVE_DONE' })
    } catch (err: unknown) {
      dispatch({ type: 'ERROR', message: err instanceof Error ? err.message : 'Approval failed' })
    }
  }, [])

  const handleReset = useCallback(() => {
    abortRef.current?.()
    abortRef.current = null
    dispatch({ type: 'RESET' })
  }, [])

  return { state, handleFile, handleApprove, handleReset }
}
