import { useQuery } from '@tanstack/react-query'
import { fetchProducts } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Loader2 } from 'lucide-react'
import type { ProductSummary } from '@/types/extraction'

interface ProductListProps {
  selectedIsin: string | null
  onSelectProduct: (isin: string) => void
  onNewUpload: () => void
  refreshKey: number
}

export default function ProductList({
  selectedIsin,
  onSelectProduct,
  onNewUpload,
  refreshKey,
}: ProductListProps) {
  const { data: products, isLoading, error } = useQuery({
    queryKey: ['products', refreshKey],
    queryFn: fetchProducts,
    refetchInterval: 30_000,
  })

  return (
    <div className="flex flex-col h-full">
      {/* Header + New Upload */}
      <div className="p-4 pb-3">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-3">
          Products
        </p>
        <Button
          onClick={onNewUpload}
          className="w-full justify-center gap-2"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          New Upload
        </Button>
      </div>

      {/* Product list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <p className="text-xs text-destructive text-center py-4">
            Failed to load products
          </p>
        )}

        {products?.map((product) => (
          <ProductCard
            key={product.product_isin}
            product={product}
            selected={product.product_isin === selectedIsin}
            onClick={() => onSelectProduct(product.product_isin)}
          />
        ))}

        {products && products.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-8">
            No products yet
          </p>
        )}
      </div>
    </div>
  )
}

function ProductCard({
  product,
  selected,
  onClick,
}: {
  product: ProductSummary
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg p-3 transition-colors ${
        selected
          ? 'bg-primary/15 border border-primary/30'
          : 'hover:bg-white/5 border border-transparent'
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-mono font-medium truncate">
          {product.product_isin}
        </span>
        {product.approved ? (
          <Badge variant="secondary" className="text-[10px] bg-teal/15 text-teal border-teal/20 shrink-0 ml-2">
            Approved
          </Badge>
        ) : (
          <Badge variant="secondary" className="text-[10px] bg-amber/15 text-amber border-amber/20 shrink-0 ml-2">
            Pending
          </Badge>
        )}
      </div>
      <p className="text-xs text-muted-foreground truncate">
        {product.issuer ?? 'Unknown issuer'}
      </p>
      <p className="text-xs text-muted-foreground/60 mt-0.5">
        {product.maturity}
      </p>
    </button>
  )
}
