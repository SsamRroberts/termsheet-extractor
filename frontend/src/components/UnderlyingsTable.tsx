import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { Underlying } from '@/types/extraction'

interface UnderlyingsTableProps {
  underlyings: Underlying[]
}

export default function UnderlyingsTable({ underlyings }: UnderlyingsTableProps) {
  if (underlyings.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Underlyings</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>BBG Code</TableHead>
              <TableHead className="text-right">Weight</TableHead>
              <TableHead className="text-right">Initial Price</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {underlyings.map((u, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono">{u.bbg_code}</TableCell>
                <TableCell className="text-right">
                  {u.weight != null ? `${u.weight}%` : '-'}
                </TableCell>
                <TableCell className="text-right">
                  {u.initial_price.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
