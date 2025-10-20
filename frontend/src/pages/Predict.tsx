import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toast } from "sonner";
import { ArrowLeft, Brain, Sparkles, AlertTriangle } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

const Predict = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [question, setQuestion] = useState("");
  const [timeHorizon, setTimeHorizon] = useState("12");
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<any>(null);
  const [typedSummary, setTypedSummary] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [openReasoning, setOpenReasoning] = useState(false);
  const [openSources, setOpenSources] = useState(false);
  const [isMockMode, setIsMockMode] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("astro_token");
    if (!token) {
      navigate("/auth");
    }
  }, [navigate]);

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const token = localStorage.getItem("astro_token");
      const response = await fetch(`${API_BASE_URL}/predict/question`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          profile_id: parseInt(id!),
          question,
          time_horizon_months: parseInt(timeHorizon),
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Prediction failed");
      }

      const data = await response.json();
      
      // Check if response is in mock mode
      if (data.is_mock_response || data.mock_warning) {
        setIsMockMode(true);
      }
      
      setPrediction(data);
      // typewriter effect for summary
      const summary: string = data?.answer?.summary || "";
      setTypedSummary("");
      setIsTyping(true);
      let i = 0;
      const speed = 12; // ms per character
      const interval = setInterval(() => {
        i += 1;
        setTypedSummary(summary.slice(0, i));
        if (i >= summary.length) {
          clearInterval(interval);
          setIsTyping(false);
        }
      }, speed);
      toast.success("Prediction received!");
    } catch (error: any) {
      toast.error(error.message || "Failed to get prediction");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-4xl mx-auto animate-fade-in">
        <Button
          variant="ghost"
          onClick={() => navigate(`/profiles/${id}`)}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Profile
        </Button>

        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 bg-primary/10 rounded-lg glow-primary">
            <Brain className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gradient">Ask a Question</h1>
            <p className="text-muted-foreground">Get AI-powered astrological insights</p>
          </div>
        </div>

        {isMockMode && (
          <Alert variant="destructive" className="mb-6 border-yellow-500 bg-yellow-500/10">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            <AlertTitle className="text-yellow-500">Mock Mode Active</AlertTitle>
            <AlertDescription className="text-yellow-600">
              You are receiving MOCK predictions for testing only. This is NOT real AI analysis. Configure the OpenAI API key in the backend to enable real predictions.
            </AlertDescription>
          </Alert>
        )}

        {!prediction ? (
          <Card className="card-glass">
            <CardHeader>
              <CardTitle>Your Question</CardTitle>
              <CardDescription>
                Ask about career, relationships, health, or any life aspect
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAskQuestion} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="question">Question</Label>
                  <Input
                    id="question"
                    placeholder="e.g., Will I get a new job soon?"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    required
                    maxLength={500}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="time-horizon">Time Horizon (months)</Label>
                  <Input
                    id="time-horizon"
                    type="number"
                    min="1"
                    max="120"
                    value={timeHorizon}
                    onChange={(e) => setTimeHorizon(e.target.value)}
                    required
                  />
                  <p className="text-sm text-muted-foreground">
                    Maximum 120 months (10 years) for long-term predictions
                  </p>
                </div>

                <Button type="submit" className="w-full glow-primary" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                      Getting insights...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      Get Prediction
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Question & Confidence */}
            <Card className="card-glass">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Your Question</span>
                  <Badge variant="outline" className="text-primary">
                    Confidence: {(prediction.confidence_overall * 100).toFixed(0)}%
                  </Badge>
                </CardTitle>
                <CardDescription>{question}</CardDescription>
              </CardHeader>
            </Card>

            {/* Summary */}
            <Card className="card-glass border-primary/30">
              <CardHeader>
                <CardTitle>Prediction</CardTitle>
                <Badge className="w-fit">{prediction.topic}</Badge>
              </CardHeader>
              <CardContent>
                <p className="text-foreground leading-relaxed min-h-[2.5rem]">
                  {typedSummary}
                  {isTyping && <span className="animate-pulse">▍</span>}
                </p>
              </CardContent>
            </Card>

            {/* Time Windows */}
            {prediction.answer.time_windows?.length > 0 && (
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle>Favorable Periods</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {prediction.answer.time_windows.map((window: any, index: number) => (
                    <div
                      key={index}
                      className="p-4 rounded-lg bg-primary/5 border border-primary/20"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <p className="font-semibold text-primary">{window.focus}</p>
                        <Badge variant="outline">
                          {(window.confidence * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {new Date(window.start).toLocaleDateString()} -{" "}
                        {new Date(window.end).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            {prediction.answer.actions?.length > 0 && (
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle>Recommended Actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {prediction.answer.actions.map((action: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Risks */}
            {prediction.answer.risks?.length > 0 && (
              <Card className="card-glass border-destructive/30">
                <CardHeader>
                  <CardTitle className="text-destructive">Cautions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {prediction.answer.risks.map((risk: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-destructive mt-1">⚠</span>
                        <span>{risk}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Reasoning / Evidence */}
            {(prediction.answer.rationale || (prediction.answer.evidence?.length ?? 0) > 0) && (
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle>Why this answer?</CardTitle>
                  <CardDescription>See the reasoning and supporting astrology</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {prediction.answer.rationale && (
                    <Collapsible open={openReasoning} onOpenChange={setOpenReasoning}>
                      <CollapsibleTrigger asChild>
                        <Button variant="outline" className="mb-2 w-full justify-between">
                          Reasoning
                          <span>{openReasoning ? "▲" : "▼"}</span>
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">{prediction.answer.rationale}</p>
                      </CollapsibleContent>
                    </Collapsible>
                  )}

                  {(prediction.answer.evidence?.length ?? 0) > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">Evidence</h3>
                      <ul className="space-y-2 text-sm">
                        {prediction.answer.evidence.map((ev: any, idx: number) => (
                          <li key={idx} className="p-3 rounded-lg bg-muted/50 border border-border">
                            <div className="text-xs text-muted-foreground">{ev.calc_field}</div>
                            <div className="font-medium">{String(ev.value)}</div>
                            <div className="text-sm text-muted-foreground">{ev.interpretation}</div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {(prediction.answer.sources?.length ?? 0) > 0 && (
                    <Collapsible open={openSources} onOpenChange={setOpenSources}>
                      <CollapsibleTrigger asChild>
                        <Button variant="outline" className="mt-2 w-full justify-between">
                          Sources
                          <span>{openSources ? "▲" : "▼"}</span>
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <ul className="list-disc pl-6 space-y-1 text-sm">
                          {prediction.answer.sources.map((s: any, idx: number) => (
                            <li key={idx}>
                              {s.url ? (
                                <a className="text-primary underline" href={s.url} target="_blank" rel="noreferrer">
                                  {s.title || s.url}
                                </a>
                              ) : (
                                <span>{s.title}</span>
                              )}
                              {s.note && <span className="text-muted-foreground"> — {s.note}</span>}
                            </li>
                          ))}
                        </ul>
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                </CardContent>
              </Card>
            )}

            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => {
                  setPrediction(null);
                  setQuestion("");
                }}
                className="flex-1"
              >
                Ask Another Question
              </Button>
              <Button
                onClick={() => navigate(`/profiles/${id}`)}
                className="flex-1 glow-primary"
              >
                Back to Profile
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Predict;
