import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { Event } from '@/types/extraction'

interface EventsTableProps {
  events: Event[]
}

const TYPE_LABELS: Record<string, string> = {
  coupon: 'Coupon',
  auto_early_redemption: 'Auto Early Redemption',
  knock_in: 'Knock-In',
  final_redemption: 'Final Redemption',
}

export default function EventsTable({ events }: EventsTableProps) {
  if (events.length === 0) return null

  // Group events by type
  const grouped = events.reduce<Record<string, Event[]>>((acc, event) => {
    const key = event.event_type
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {})

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Events</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {Object.entries(grouped).map(([type, typeEvents]) => (
          <div key={type}>
            <Badge variant="outline" className="mb-3">
              {TYPE_LABELS[type] ?? type}
            </Badge>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Barrier Level</TableHead>
                  <TableHead className="text-right">Strike</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Payment Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {typeEvents.map((e, i) => (
                  <TableRow key={i}>
                    <TableCell>{e.event_date}</TableCell>
                    <TableCell className="text-right">
                      {e.event_level_pct != null ? `${e.event_level_pct}%` : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {e.event_strike_pct != null ? `${e.event_strike_pct}%` : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {e.event_amount != null ? e.event_amount.toFixed(2) : '-'}
                    </TableCell>
                    <TableCell>{e.event_payment_date ?? '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
