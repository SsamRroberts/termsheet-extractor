import TermsheetPipeline from '@/components/TermsheetPipeline'

function App() {
  return (
    <div className="flex min-h-svh items-start justify-center p-4 pt-12">
      <div className="w-full max-w-4xl space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight">
            Termsheet Upload
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Upload a PDF termsheet for extraction and validation
          </p>
        </div>
        <TermsheetPipeline />
      </div>
    </div>
  )
}

export default App
