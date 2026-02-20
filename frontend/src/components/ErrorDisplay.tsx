import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { XCircle } from 'lucide-react'

interface ErrorDisplayProps {
  message: string
  onReset: () => void
}

export default function ErrorDisplay({ message, onReset }: ErrorDisplayProps) {
  return (
    <div className="space-y-4">
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertTitle>Something went wrong</AlertTitle>
        <AlertDescription>{message}</AlertDescription>
      </Alert>
      <div className="flex justify-center">
        <Button variant="outline" onClick={onReset}>
          Try Again
        </Button>
      </div>
    </div>
  )
}
