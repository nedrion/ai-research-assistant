import { useState, useRef, useEffect } from "react"
import { useMutation } from "@tanstack/react-query"
import { Send, Bot, User, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { toast } from "@/hooks/use-toast"
import { sendQuery } from "@/lib/api"

type Message = {
  role: "user" | "assistant"
  content: string
  sources?: { source: string; chunk_index: number }[]
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sessionId, setSessionId] = useState<string | undefined>()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const queryMut = useMutation({
    mutationFn: (question: string) => sendQuery(question, sessionId),
    onSuccess: (result) => {
      setSessionId(result.session_id)
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

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Chat</h1>
      <Separator />

      <Card className="h-[60vh] flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              Ask a question about your documents
            </div>
          )}
          {messages.map((msg, i) => (
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
                      <Badge key={j} variant="outline" className="text-[10px]">
                        {s.source}#{s.chunk_index}
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
          ))}
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

        <div className="border-t p-4">
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
    </div>
  )
}
