import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle } from 'lucide-react'
import type { ExtractionResponse } from '@/types/extraction'

interface ApprovalConfirmationProps {
  extraction: ExtractionResponse
  onReset: () => void
}

export default function ApprovalConfirmation({
  extraction,
  onReset,
}: ApprovalConfirmationProps) {
  return (
    <Card className="w-full">
      <CardContent className="flex flex-col items-center gap-4 py-8">
        <CheckCircle className="h-12 w-12 text-teal" />
        <div className="text-center space-y-1">
          <h2 className="text-lg font-semibold">Product Approved</h2>
          <p className="text-sm text-muted-foreground">
            {extraction.product_isin} has been approved and saved.
          </p>
          <p className="text-xs text-muted-foreground">
            Source: {extraction.filename} ({Math.round(extraction.size_bytes / 1024)} KB)
          </p>
        </div>
        <Button variant="outline" onClick={onReset} className="mt-2">
          Upload Another Termsheet
        </Button>
      </CardContent>
    </Card>
  )
}
