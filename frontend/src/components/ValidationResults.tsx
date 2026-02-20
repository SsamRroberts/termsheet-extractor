import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import type { ValidationResult } from '@/types/extraction'

interface ValidationResultsProps {
  validation: ValidationResult
}

export default function ValidationResults({ validation }: ValidationResultsProps) {
  const errors = validation.issues.filter((i) => i.severity === 'error')
  const warnings = validation.issues.filter((i) => i.severity === 'warning')

  if (validation.is_valid && warnings.length === 0) {
    return (
      <Alert className="border-green-200 bg-green-50 text-green-800">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <AlertTitle>Validation passed</AlertTitle>
        <AlertDescription>All business rules passed successfully.</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-3">
      {errors.length > 0 && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Validation errors ({errors.length})</AlertTitle>
          <AlertDescription>
            <ul className="mt-1 list-disc pl-4 space-y-1">
              {errors.map((issue, i) => (
                <li key={i}>{issue.message}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {warnings.length > 0 && (
        <Alert className="border-yellow-200 bg-yellow-50 text-yellow-800">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertTitle>Warnings ({warnings.length})</AlertTitle>
          <AlertDescription>
            <ul className="mt-1 list-disc pl-4 space-y-1">
              {warnings.map((issue, i) => (
                <li key={i}>{issue.message}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {validation.is_valid && errors.length === 0 && (
        <Alert className="border-green-200 bg-green-50 text-green-800">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertTitle>Validation passed</AlertTitle>
          <AlertDescription>All business rules passed (with warnings above).</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
