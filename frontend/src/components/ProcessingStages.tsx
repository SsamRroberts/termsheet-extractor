import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CheckCircle, Circle, Loader2 } from 'lucide-react'

type Stage =
  | 'extracting_pdf'
  | 'saving_blob'
  | 'llm_extraction'
  | 'validation'
  | 'persisting'

const STAGES: { key: Stage; label: string }[] = [
  { key: 'extracting_pdf', label: 'Extracting PDF' },
  { key: 'saving_blob', label: 'Saving document' },
  { key: 'llm_extraction', label: 'LLM extraction' },
  { key: 'validation', label: 'Validating data' },
  { key: 'persisting', label: 'Saving to database' },
]

interface ProcessingStagesProps {
  currentStage: Stage
  progress: number
  filename: string
}

export default function ProcessingStages({
  currentStage,
  progress,
  filename,
}: ProcessingStagesProps) {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage)

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg">Processing {filename}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <Progress value={progress} />

        <div className="space-y-3">
          {STAGES.map((stage, i) => {
            const isDone = i < currentIndex
            const isCurrent = i === currentIndex
            return (
              <div key={stage.key} className="flex items-center gap-3">
                {isDone ? (
                  <CheckCircle className="h-5 w-5 text-green-600 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 className="h-5 w-5 text-primary animate-spin shrink-0" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground/40 shrink-0" />
                )}
                <span
                  className={
                    isDone
                      ? 'text-sm text-muted-foreground'
                      : isCurrent
                        ? 'text-sm font-medium'
                        : 'text-sm text-muted-foreground/60'
                  }
                >
                  {stage.label}
                </span>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
