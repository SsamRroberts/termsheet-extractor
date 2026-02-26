import { useExtractionPipeline } from '@/hooks/useExtractionPipeline'
import FileUploader from '@/components/FileUploader'
import ProcessingStages from '@/components/ProcessingStages'
import ExtractionReview from '@/components/ExtractionReview'
import ApprovalConfirmation from '@/components/ApprovalConfirmation'
import ErrorDisplay from '@/components/ErrorDisplay'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useEffect, useRef } from 'react'

interface TermsheetPipelineProps {
  onComplete?: () => void
}

export default function TermsheetPipeline({ onComplete }: TermsheetPipelineProps) {
  const { state, handleFile, handleApprove, handleReset } = useExtractionPipeline()
  const notifiedRef = useRef(false)

  // Notify parent when extraction reaches review or approved state (product saved to DB)
  useEffect(() => {
    if ((state.phase === 'review' || state.phase === 'approved') && !notifiedRef.current) {
      notifiedRef.current = true
      onComplete?.()
    }
    if (state.phase === 'idle') {
      notifiedRef.current = false
    }
  }, [state.phase, onComplete])

  switch (state.phase) {
    case 'idle':
      return <FileUploader onFile={handleFile} />

    case 'uploading':
      return (
        <Card className="w-full">
          <CardContent className="space-y-4 py-8">
            <div className="text-center">
              <p className="text-sm font-medium">Uploading {state.filename}</p>
            </div>
            <Progress value={state.uploadProgress} />
            <p className="text-sm text-muted-foreground text-center">
              {state.uploadProgress}%
            </p>
          </CardContent>
        </Card>
      )

    case 'processing':
      return (
        <ProcessingStages
          currentStage={state.stage}
          progress={state.progress}
          filename={state.filename}
        />
      )

    case 'review':
      return (
        <ExtractionReview
          extraction={state.extraction}
          approving={state.approving}
          onApprove={() => handleApprove(state.extraction.product_isin)}
          onReset={handleReset}
        />
      )

    case 'approved':
      return (
        <ApprovalConfirmation
          extraction={state.extraction}
          onReset={handleReset}
        />
      )

    case 'error':
      return <ErrorDisplay message={state.message} onReset={handleReset} />
  }
}
