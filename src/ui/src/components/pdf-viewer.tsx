import { useState, useEffect } from "react"
import { Document, Page, pdfjs } from "react-pdf"
import { X, ChevronLeft, ChevronRight } from "lucide-react"
import { getPdfUrl } from "@/lib/api"
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url"

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

interface PdfViewerProps {
  filename: string
  page?: number | null
  open: boolean
  onClose: () => void
}

export function PdfViewer({ filename, page, open, onClose }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    setCurrentPage(page ?? 1)
    setNumPages(null)
    setLoadError(null)
  }, [page, filename])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
      if (!numPages) return
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        setCurrentPage((p) => Math.min(numPages, p + 1))
      }
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        setCurrentPage((p) => Math.max(1, p - 1))
      }
    }
    if (open) document.addEventListener("keydown", handleKey)
    return () => document.removeEventListener("keydown", handleKey)
  }, [open, numPages, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-5xl h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-3 border-b">
          <span className="font-medium truncate">{filename}</span>
          <div className="flex items-center gap-3">
            {numPages && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  className="p-1 hover:bg-muted rounded disabled:opacity-30 transition-opacity"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  {currentPage} / {numPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
                  disabled={currentPage >= numPages}
                  className="p-1 hover:bg-muted rounded disabled:opacity-30 transition-opacity"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
            <button onClick={onClose} className="p-1 hover:bg-muted rounded-md transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        <div className="flex-1 min-h-0 overflow-auto bg-muted/30 flex flex-col items-center p-4">
          {loadError && (
            <div className="text-sm text-destructive py-8">{loadError}</div>
          )}
          <Document
            file={getPdfUrl(filename)}
            onLoadSuccess={({ numPages: n }) => setNumPages(n)}
            onLoadError={(err) => setLoadError(`Failed to load PDF: ${err.message}`)}
            loading={<div className="text-sm text-muted-foreground py-8">Loading PDF...</div>}
            error={<div className="text-sm text-destructive py-8">Failed to load PDF</div>}
          >
            <Page
              pageNumber={currentPage}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              className="shadow-md"
            />
          </Document>
        </div>
      </div>
    </div>
  )
}
