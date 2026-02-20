import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

interface ApprovalActionsProps {
  canApprove: boolean
  approving: boolean
  onApprove: () => void
  onReset: () => void
}

export default function ApprovalActions({
  canApprove,
  approving,
  onApprove,
  onReset,
}: ApprovalActionsProps) {
  return (
    <div className="flex gap-3 justify-end">
      <Button variant="outline" onClick={onReset} disabled={approving}>
        Upload Another
      </Button>
      <Button onClick={onApprove} disabled={!canApprove || approving}>
        {approving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        Approve Product
      </Button>
    </div>
  )
}
