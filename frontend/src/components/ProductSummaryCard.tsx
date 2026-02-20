import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Product } from '@/types/extraction'

interface ProductSummaryCardProps {
  product: Product
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium">{value ?? '-'}</dd>
    </div>
  )
}

export default function ProductSummaryCard({ product }: ProductSummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Product Details</CardTitle>
          {product.product_type && (
            <Badge variant="secondary">{product.product_type}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-8 gap-y-3">
          <Field label="ISIN" value={product.product_isin} />
          <Field label="SEDOL" value={product.sedol} />
          <Field label="Issuer" value={product.issuer} />
          <Field label="Currency" value={product.currency} />
          <Field label="Issue Date" value={product.issue_date} />
          <Field label="Maturity" value={product.maturity} />
          <Field label="Description" value={product.short_description} />
        </dl>
      </CardContent>
    </Card>
  )
}
