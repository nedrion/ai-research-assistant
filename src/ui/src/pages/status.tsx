import { useQuery } from "@tanstack/react-query"
import { Database, Cpu, FileText, Layers } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { getStatus, getModels } from "@/lib/api"

export function StatusPage() {
  const { data: status, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
    refetchInterval: 10000,
  })

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ["models"],
    queryFn: getModels,
  })

  if (statusLoading || modelsLoading) {
    return <div className="text-sm text-muted-foreground">Loading status...</div>
  }

  if (statusError) {
    return <div className="text-sm text-destructive">Error: {(statusError as Error).message}</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Status</h1>
          <p className="text-sm text-muted-foreground mt-1">Vector store and model overview</p>
        </div>
      </div>

      <Separator />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Chunks</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status?.total_chunks ?? 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status?.documents.length ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      {models && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Cpu className="h-4 w-4" />
              LLM Models
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {models.models.map((m) => (
                <Badge key={m.name} variant={m.current ? "default" : "secondary"}>
                  {m.name}
                </Badge>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Current model: <span className="font-medium">{models.current}</span>
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <Database className="h-4 w-4" />
            Document Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!status?.documents || status.documents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents stored</p>
          ) : (
            <div className="divide-y">
              {status.documents.map((doc) => (
                <div key={doc.filename} className="flex items-center justify-between py-2 text-sm">
                  <span>{doc.filename}</span>
                  <Badge variant="secondary">{doc.chunks} chunks</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
