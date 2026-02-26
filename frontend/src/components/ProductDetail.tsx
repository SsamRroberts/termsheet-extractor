import { useQuery } from '@tanstack/react-query'
import { fetchProduct, approveProduct } from '@/lib/api'
import { useState } from 'react'
import ProductSummaryCard from '@/components/ProductSummaryCard'
import UnderlyingsTable from '@/components/UnderlyingsTable'
import EventsTable from '@/components/EventsTable'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Loader2, CheckCircle } from 'lucide-react'
import type { Product } from '@/types/extraction'

interface ProductDetailProps {
  isin: string
  onApproved: () => void
}

export default function ProductDetail({ isin, onApproved }: ProductDetailProps) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['product', isin],
    queryFn: () => fetchProduct(isin),
  })
  const [approving, setApproving] = useState(false)

  const handleApprove = async () => {
    setApproving(true)
    try {
      await approveProduct(isin)
      await refetch()
      onApproved()
    } catch {
      // Error handling could be improved
    } finally {
      setApproving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="text-center py-20">
        <p className="text-destructive text-sm">Failed to load product details</p>
      </div>
    )
  }

  // Adapt ProductDetail data to the Product interface used by ProductSummaryCard
  const product: Product = {
    product_isin: data.product_isin,
    sedol: data.sedol,
    short_description: data.short_description,
    issuer: data.issuer,
    issue_date: data.issue_date,
    currency: data.currency,
    maturity: data.maturity,
    product_type: data.product_type,
    word_description: data.word_description,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{data.product_isin}</h2>
          <p className="text-sm text-muted-foreground">
            {data.issuer ?? 'Unknown issuer'}
          </p>
        </div>
        {data.approved ? (
          <Badge className="bg-teal/15 text-teal border-teal/20 gap-1.5">
            <CheckCircle className="h-3.5 w-3.5" />
            Approved
          </Badge>
        ) : (
          <Button onClick={handleApprove} disabled={approving} size="sm">
            {approving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Approve Product
          </Button>
        )}
      </div>

      <Separator className="opacity-50" />

      <ProductSummaryCard product={product} />
      <UnderlyingsTable underlyings={data.underlyings} />
      <EventsTable events={data.events} />
    </div>
  )
}
