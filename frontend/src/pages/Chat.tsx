import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toast } from "sonner";
import { ArrowLeft, MessageSquare, Send, AlertTriangle } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

const Chat = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [messages, setMessages] = useState<Array<{ id: number; role: string; content: string; created_at: string }>>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [typingId, setTypingId] = useState<number | null>(null);
  const [typedMap, setTypedMap] = useState<Record<number, string>>({});
  const [openBlocks, setOpenBlocks] = useState<Record<number, { reasons: boolean; sources: boolean }>>({});
  const [isMockMode, setIsMockMode] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("astro_token");
    if (!token) {
      navigate("/auth");
      return;
    }
    fetchHistory();
  }, [id, navigate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem("astro_token");
      const res = await fetch(`${API_BASE_URL}/chat/history/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load chat history");
      const data = await res.json();
      setMessages(data.messages || []);
    } catch (e: any) {
      toast.error(e.message || "Failed to load chat history");
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setIsSending(true);
    try {
      const token = localStorage.getItem("astro_token");
      // Optimistic update for user message
      const tempId = Date.now();
      const optimistic = { id: tempId, role: "user", content: input, created_at: new Date().toISOString() };
      setMessages((prev) => [...prev, optimistic]);

      const res = await fetch(`${API_BASE_URL}/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ profile_id: parseInt(id!), message: input }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Failed to send message");
      }
      const data = await res.json();
      
      // Check if response contains mock mode warning
      if (data.content && data.content.includes("⚠️ **MOCK RESPONSE**")) {
        setIsMockMode(true);
      }
      
      // Append assistant message
      const assistant = { id: data.message_id, role: data.role, content: data.content, created_at: data.created_at };
      setMessages((prev) => [...prev, assistant]);
      // typewriter for assistant content
      setTypingId(assistant.id);
      const full = assistant.content || "";
      let i = 0;
      const speed = 12;
      const interval = setInterval(() => {
        i += 1;
        setTypedMap((m) => ({ ...m, [assistant.id]: full.slice(0, i) }));
        if (i >= full.length) {
          clearInterval(interval);
          setTypingId(null);
        }
      }, speed);
      setInput("");
    } catch (e: any) {
      toast.error(e.message || "Message failed");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-3xl mx-auto animate-fade-in">
        <Button variant="ghost" onClick={() => navigate(`/profiles/${id}`)} className="mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Profile
        </Button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-primary/10 rounded-lg glow-primary">
            <MessageSquare className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gradient">Astrology Chat</h1>
            <p className="text-muted-foreground">Discuss your chart, dasha and more</p>
          </div>
        </div>

        {isMockMode && (
          <Alert variant="destructive" className="mb-6 border-yellow-500 bg-yellow-500/10">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            <AlertTitle className="text-yellow-500">Mock Mode Active</AlertTitle>
            <AlertDescription className="text-yellow-600">
              You are receiving MOCK responses for testing only. Configure the OpenAI API key in the backend to enable real AI predictions.
            </AlertDescription>
          </Alert>
        )}

        <Card className="card-glass">
          <CardHeader>
            <CardTitle>Conversation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
              {messages.map((m) => {
                const isAssistant = m.role === "assistant";
                const rendered = typingId === m.id ? typedMap[m.id] || "" : m.content;
                // naive parse: split markdown sections we asked for
                let answer = rendered;
                let reasons: string[] = [];
                let sources: string[] = [];
                if (isAssistant && rendered) {
                  const parts = rendered.split(/\*\*Reasons\*\*:/i);
                  if (parts.length > 1) {
                    answer = parts[0].replace(/\*\*Answer\*\*:\\s*/i, "").trim();
                    const rest = parts[1].split(/\*\*Sources\*\*:/i);
                    const reasonsBlock = rest[0] || "";
                    reasons = reasonsBlock
                      .split(/\n|\r/)
                      .map((l) => l.replace(/^[-*]\s*/, "").trim())
                      .filter(Boolean);
                    if (rest.length > 1) {
                      sources = rest[1]
                        .split(/\n|\r/)
                        .map((l) => l.replace(/^[-*]\s*/, "").trim())
                        .filter(Boolean);
                    }
                  }
                }

                const open = openBlocks[m.id] || { reasons: false, sources: false };

                return (
                  <div key={m.id} className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}>
                    <div
                      className={`px-4 py-3 rounded-2xl shadow-sm whitespace-pre-wrap break-words max-w-[85%] ${
                        isAssistant ? "bg-primary/10 border border-primary/20" : "bg-muted border border-border"
                      }`}
                    >
                      {!isAssistant ? (
                        <>{m.content}</>
                      ) : (
                        <div className="space-y-3">
                          <div>
                            {answer}
                            {typingId === m.id && <span className="animate-pulse">▍</span>}
                          </div>
                          {reasons.length > 0 && (
                            <Collapsible
                              open={open.reasons}
                              onOpenChange={(v) => setOpenBlocks((b) => ({ ...b, [m.id]: { ...open, reasons: v } }))}
                            >
                              <CollapsibleTrigger asChild>
                                <Button variant="outline" className="w-full justify-between">
                                  Reasons
                                  <span>{open.reasons ? "▲" : "▼"}</span>
                                </Button>
                              </CollapsibleTrigger>
                              <CollapsibleContent>
                                <ul className="list-disc pl-6 text-sm mt-2 space-y-1">
                                  {reasons.map((r, idx) => (
                                    <li key={idx}>{r}</li>
                                  ))}
                                </ul>
                              </CollapsibleContent>
                            </Collapsible>
                          )}
                          {sources.length > 0 && (
                            <Collapsible
                              open={open.sources}
                              onOpenChange={(v) => setOpenBlocks((b) => ({ ...b, [m.id]: { ...open, sources: v } }))}
                            >
                              <CollapsibleTrigger asChild>
                                <Button variant="outline" className="w-full justify-between">
                                  Sources
                                  <span>{open.sources ? "▲" : "▼"}</span>
                                </Button>
                              </CollapsibleTrigger>
                              <CollapsibleContent>
                                <ul className="list-disc pl-6 text-sm mt-2 space-y-1">
                                  {sources.map((s, idx) => {
                                    const match = s.match(/https?:\/{2}[^\s)]+/);
                                    if (!match) return <li key={idx}>{s}</li>;
                                    const url = match[0];
                                    const start = match.index || 0;
                                    const before = s.slice(0, start);
                                    const after = s.slice(start + url.length);
                                    return (
                                      <li key={idx}>
                                        {before}
                                        <a className="text-primary underline" href={url} target="_blank" rel="noreferrer">
                                          {url}
                                        </a>
                                        {after}
                                      </li>
                                    );
                                  })}
                                </ul>
                              </CollapsibleContent>
                            </Collapsible>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          </CardContent>
          <CardFooter>
            <form onSubmit={sendMessage} className="w-full flex gap-2">
              <Input
                placeholder="Ask anything about your chart, dashas, transits..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                maxLength={2000}
                required
              />
              <Button type="submit" className="glow-primary" disabled={isSending}>
                <Send className="w-4 h-4 mr-1" /> Send
              </Button>
            </form>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default Chat;


