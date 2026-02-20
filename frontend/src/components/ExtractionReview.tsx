import { Separator } from '@/components/ui/separator'
import ProductSummaryCard from '@/components/ProductSummaryCard'
import UnderlyingsTable from '@/components/UnderlyingsTable'
import EventsTable from '@/components/EventsTable'
import ValidationResults from '@/components/ValidationResults'
import ApprovalActions from '@/components/ApprovalActions'
import type { ExtractionResponse } from '@/types/extraction'

interface ExtractionReviewProps {
  extraction: ExtractionResponse
  approving: boolean
  onApprove: () => void
  onReset: () => void
}

export default function ExtractionReview({
  extraction,
  approving,
  onApprove,
  onReset,
}: ExtractionReviewProps) {
  const { data, validation } = extraction

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Extraction Review</h2>
        <p className="text-sm text-muted-foreground">
          {extraction.filename} ({Math.round(extraction.size_bytes / 1024)} KB)
        </p>
      </div>

      <ValidationResults validation={validation} />

      <Separator />

      <ProductSummaryCard product={data.product} />
      <UnderlyingsTable underlyings={data.underlyings} />
      <EventsTable events={data.events} />

      <Separator />

      <ApprovalActions
        canApprove={validation.is_valid}
        approving={approving}
        onApprove={onApprove}
        onReset={onReset}
      />
    </div>
  )
}
