import { useState, useRef, useEffect } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useSearchParams } from "react-router-dom"
import { Send, Bot, User, Loader2, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { PdfViewer } from "@/components/pdf-viewer"
import { toast } from "@/hooks/use-toast"
import { sendQuery, getModels, getSessionHistory, type Source } from "@/lib/api"

const STORAGE_KEY = "ara_session_id"

type Message = {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
}

export function ChatPage() {
  const [searchParams] = useSearchParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sessionId, setSessionId] = useState<string | undefined>(
    () => searchParams.get("session") || localStorage.getItem(STORAGE_KEY) || undefined,
  )
  const [selectedModel, setSelectedModel] = useState(searchParams.get("model") ?? "")
  const [preview, setPreview] = useState<{ filename: string; page?: number | null } | null>(null)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: modelsData } = useQuery({
    queryKey: ["models"],
    queryFn: getModels,
  })

  useEffect(() => {
    if (!modelsData) return
    if (!selectedModel || !modelsData.models.some((m) => m.name === selectedModel)) {
      setSelectedModel(modelsData.current)
    }
  }, [modelsData, selectedModel])

  useEffect(() => {
    if (sessionId && !historyLoaded) {
      getSessionHistory(sessionId)
        .then((data) => {
          setMessages(data.messages.map((m) => ({ role: m.role, content: m.content })))
          setHistoryLoaded(true)
        })
        .catch(() => {
          localStorage.removeItem(STORAGE_KEY)
          setSessionId(undefined)
          setHistoryLoaded(true)
        })
    } else if (!sessionId) {
      setHistoryLoaded(true)
    }
  }, [sessionId, historyLoaded])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const queryMut = useMutation({
    mutationFn: (question: string) =>
      sendQuery(question, sessionId, undefined, selectedModel || undefined),
    onSuccess: (result) => {
      setSessionId(result.session_id)
      localStorage.setItem(STORAGE_KEY, result.session_id)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, sources: result.sources },
      ])
    },
    onError: (err: Error) => {
      toast({ title: "Query failed", description: err.message, variant: "destructive" })
      setMessages((prev) => prev.slice(0, -1))
    },
  })

  const handleSend = () => {
    const q = input.trim()
    if (!q || queryMut.isPending) return
    setMessages((prev) => [...prev, { role: "user", content: q }])
    setInput("")
    queryMut.mutate(q)
  }

  const handleNewChat = () => {
    localStorage.removeItem(STORAGE_KEY)
    setSessionId(undefined)
    setMessages([])
    setHistoryLoaded(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Chat</h1>
        {messages.length > 0 && (
          <Button variant="outline" size="sm" onClick={handleNewChat}>
            <Plus className="h-4 w-4 mr-1" />
            New chat
          </Button>
        )}
      </div>
      <Separator />

      <Card className="h-[60vh] flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {!historyLoaded ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              Loading history...
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              Ask a question about your documents
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                {msg.role === "assistant" && (
                  <div className="flex-shrink-0 mt-1">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                )}
                <div className={`max-w-[80%] ${msg.role === "user" ? "order-first" : ""}`}>
                  <div
                    className={`rounded-lg px-4 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    {msg.content}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {msg.sources.map((s, j) => (
                        <Badge
                          key={j}
                          variant="outline"
                          className="text-[10px] cursor-pointer hover:bg-accent transition-colors"
                          onClick={() => setPreview({ filename: s.source, page: s.page })}
                        >
                          {s.source}#{s.chunk_index}{s.page ? ` (p.${s.page})` : ""}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="flex-shrink-0 mt-1">
                    <User className="h-5 w-5 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))
          )}
          {queryMut.isPending && (
            <div className="flex gap-3">
              <Bot className="h-5 w-5 text-primary flex-shrink-0 mt-1" />
              <div className="rounded-lg px-4 py-2 text-sm bg-muted flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>

        <div className="border-t p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <label htmlFor="model-select">Model:</label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="flex h-8 w-48 rounded-md border border-input bg-transparent px-2 py-1 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {modelsData?.models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend() }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              disabled={queryMut.isPending}
            />
            <Button type="submit" size="icon" disabled={queryMut.isPending || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>

      <PdfViewer
        filename={preview?.filename ?? ""}
        page={preview?.page}
        open={preview !== null}
        onClose={() => setPreview(null)}
      />
    </div>
  )
}
