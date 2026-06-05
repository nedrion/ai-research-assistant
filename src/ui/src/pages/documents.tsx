import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Upload, Trash2, FileText, RefreshCw, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { PdfViewer } from "@/components/pdf-viewer"
import { toast } from "@/hooks/use-toast"
import { getDocuments, uploadDocument, deleteDocument, clearDocuments, getStatus } from "@/lib/api"

export function DocumentsPage() {
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState(false)
  const [previewFile, setPreviewFile] = useState<string | null>(null)

  const { data: documents, isLoading, error } = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  })

  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
  })

  const uploadMut = useMutation({
    mutationFn: uploadDocument,
    onSuccess: (result) => {
      toast({ title: "Uploaded", description: `${result.filename}: ${result.chunks_created} chunks created` })
      queryClient.invalidateQueries({ queryKey: ["documents"] })
      queryClient.invalidateQueries({ queryKey: ["status"] })
    },
    onError: (err: Error) => toast({ title: "Upload failed", description: err.message, variant: "destructive" }),
  })

  const deleteMut = useMutation({
    mutationFn: deleteDocument,
    onSuccess: (result) => {
      toast({ title: "Deleted", description: `${result.filename}: ${result.chunks_removed} chunks removed` })
      queryClient.invalidateQueries({ queryKey: ["documents"] })
      queryClient.invalidateQueries({ queryKey: ["status"] })
    },
    onError: (err: Error) => toast({ title: "Delete failed", description: err.message, variant: "destructive" }),
  })

  const clearMut = useMutation({
    mutationFn: clearDocuments,
    onSuccess: () => {
      toast({ title: "Cleared", description: "All documents removed" })
      queryClient.invalidateQueries({ queryKey: ["documents"] })
      queryClient.invalidateQueries({ queryKey: ["status"] })
    },
    onError: (err: Error) => toast({ title: "Clear failed", description: err.message, variant: "destructive" }),
  })

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.endsWith(".pdf")) {
      toast({ title: "Invalid file", description: "Only PDF files are supported", variant: "destructive" })
      return
    }
    setUploading(true)
    uploadMut.mutate(file, { onSettled: () => setUploading(false) })
    e.target.value = ""
  }

  if (isLoading) return <div className="text-sm text-muted-foreground">Loading documents...</div>
  if (error) return <div className="text-sm text-destructive">Error: {error.message}</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          {status && (
            <p className="text-sm text-muted-foreground mt-1">
              {status.total_chunks} total chunks across {status.documents.length} documents
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <label className="cursor-pointer">
              <Upload className="h-4 w-4 mr-1" />
              {uploading ? "Uploading..." : "Upload PDF"}
              <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
            </label>
          </Button>
          <Button variant="outline" size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ["documents"] })}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          {documents && documents.length > 0 && (
            <Button variant="destructive" size="sm" onClick={() => clearMut.mutate()}>
              Clear All
            </Button>
          )}
        </div>
      </div>

      <Separator />

      {!documents || documents.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No documents ingested yet</p>
          <p className="text-sm">Upload a PDF to get started</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {documents.map((doc) => (
            <Card key={doc.filename}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <span className="font-medium">{doc.filename}</span>
                    <Badge variant="secondary" className="ml-2">{doc.chunks} chunks</Badge>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" onClick={() => setPreviewFile(doc.filename)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => deleteMut.mutate(doc.filename)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <PdfViewer
        filename={previewFile ?? ""}
        open={previewFile !== null}
        onClose={() => setPreviewFile(null)}
      />
    </div>
  )
}
