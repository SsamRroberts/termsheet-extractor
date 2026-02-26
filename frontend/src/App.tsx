import { useState, useCallback } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import ProductList from '@/components/ProductList'
import ProductDetail from '@/components/ProductDetail'
import TermsheetPipeline from '@/components/TermsheetPipeline'

type View = 'empty' | 'upload' | 'product'

function App() {
  const [view, setView] = useState<View>('empty')
  const [selectedIsin, setSelectedIsin] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleSelectProduct = useCallback((isin: string) => {
    setSelectedIsin(isin)
    setView('product')
  }, [])

  const handleNewUpload = useCallback(() => {
    setSelectedIsin(null)
    setView('upload')
  }, [])

  const handleExtractionComplete = useCallback(() => {
    setRefreshKey((k) => k + 1)
  }, [])

  const handleApproved = useCallback(() => {
    setRefreshKey((k) => k + 1)
  }, [])

  return (
    <DashboardLayout
      sidebar={
        <ProductList
          selectedIsin={selectedIsin}
          onSelectProduct={handleSelectProduct}
          onNewUpload={handleNewUpload}
          refreshKey={refreshKey}
        />
      }
    >
      {view === 'empty' && <EmptyState onUpload={handleNewUpload} />}

      {view === 'upload' && (
        <TermsheetPipeline onComplete={handleExtractionComplete} />
      )}

      {view === 'product' && selectedIsin && (
        <ProductDetail isin={selectedIsin} onApproved={handleApproved} />
      )}
    </DashboardLayout>
  )
}

function EmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-32 text-center">
      <div className="rounded-2xl border border-border bg-card p-10 max-w-md">
        <h2 className="text-lg font-semibold mb-2">Welcome to BlueBridge</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Select a product from the sidebar or upload a new termsheet to get started.
        </p>
        <button
          onClick={onUpload}
          className="text-sm font-medium text-teal hover:text-teal/80 transition-colors"
        >
          Upload a termsheet &rarr;
        </button>
      </div>
    </div>
  )
}

export default App
