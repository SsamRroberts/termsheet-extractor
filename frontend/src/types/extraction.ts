/** Mirrors backend schemas for the extraction pipeline. */

export interface ProductSummary {
  product_isin: string
  sedol: string | null
  short_description: string | null
  issuer: string | null
  issue_date: string
  currency: string
  maturity: string
  product_type: string | null
  approved: boolean
  underlying_count: number
  event_count: number
}

export interface ProductDetail {
  product_isin: string
  sedol: string | null
  short_description: string | null
  issuer: string | null
  issue_date: string
  currency: string
  maturity: string
  product_type: string | null
  word_description: string | null
  approved: boolean
  underlyings: Underlying[]
  events: Event[]
}

export interface Underlying {
  bbg_code: string
  weight: number | null
  initial_price: number
}

export interface Event {
  event_type: 'strike' | 'coupon' | 'auto_early_redemption' | 'knock_in' | 'final_redemption'
  event_level_pct: number | null
  event_strike_pct: number | null
  event_date: string
  event_amount: number | null
  event_payment_date: string | null
}

export interface Product {
  product_isin: string
  sedol: string | null
  short_description: string | null
  issuer: string | null
  issue_date: string
  currency: string
  maturity: string
  product_type: string | null
  word_description: string | null
}

export interface TermsheetData {
  product: Product
  underlyings: Underlying[]
  events: Event[]
}

export interface ValidationIssue {
  field: string
  rule: string
  message: string
  severity: 'error' | 'warning'
}

export interface ValidationResult {
  is_valid: boolean
  issues: ValidationIssue[]
}

export interface ExtractionResponse {
  filename: string
  size_bytes: number
  status: string
  product_isin: string
  approved: boolean
  data: TermsheetData
  validation: ValidationResult
}

export interface JobCreatedResponse {
  job_id: string
  filename: string
  size_bytes: number
}

/** SSE event shapes */
export type SseProgressEvent = {
  stage: 'extracting_pdf' | 'saving_blob' | 'llm_extraction' | 'validation' | 'persisting'
  progress: number
}

export type SseCompleteEvent = {
  stage: 'complete'
  progress: 100
  data: ExtractionResponse
}

export type SseValidationFailedEvent = {
  stage: 'validation_failed'
  progress: 100
  data: ExtractionResponse
}

export type SseErrorEvent = {
  stage: 'error'
  message: string
}

export type SseEvent =
  | SseProgressEvent
  | SseCompleteEvent
  | SseValidationFailedEvent
  | SseErrorEvent
