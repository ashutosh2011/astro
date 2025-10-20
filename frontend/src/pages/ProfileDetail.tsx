import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ArrowLeft, Sparkles, Brain, Calculator, Clock, Star, Zap, Shield, Target, Activity, MessageSquare } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

interface Profile {
  id: number;
  name: string;
  gender: string;
  dob: string;
  tob: string;
  place: string;
  lat: number;
  lon: number;
}

const ProfileDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [calcSnapshot, setCalcSnapshot] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("astro_token");
    if (!token) {
      navigate("/auth");
      return;
    }
    fetchProfile();
  }, [id, navigate]);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem("astro_token");
      const response = await fetch(`${API_BASE_URL}/profiles/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Failed to fetch profile");

      const data = await response.json();
      setProfile(data);
      
      // Also try to fetch existing calculation data
      await fetchExistingCalculation();
    } catch (error: any) {
      toast.error(error.message || "Failed to load profile");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchExistingCalculation = async () => {
    try {
      const token = localStorage.getItem("astro_token");
      // Get the latest calculation for this profile
      const response = await fetch(`${API_BASE_URL}/profiles/${id}/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.history && data.history.length > 0) {
          // Find the most recent calc_snapshot
          const latestCalcSnapshot = data.history.find((item: any) => item.type === "calc_snapshot");
          if (latestCalcSnapshot) {
            const snapshotResponse = await fetch(
              `${API_BASE_URL}/compute/${latestCalcSnapshot.id}`,
              {
                headers: { Authorization: `Bearer ${token}` },
              }
            );

            if (snapshotResponse.ok) {
              const snapshotData = await snapshotResponse.json();
              setCalcSnapshot(snapshotData);
            }
          }
        }
      }
    } catch (error) {
      // Silently fail - it's okay if there's no existing calculation
      console.log("No existing calculation found");
    }
  };

  const handleCalculate = async () => {
    setIsCalculating(true);
    try {
      const token = localStorage.getItem("astro_token");
      const response = await fetch(`${API_BASE_URL}/compute/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ profile_id: parseInt(id!) }),
      });

      if (!response.ok) throw new Error("Calculation failed");

      const data = await response.json();
      
      // Fetch the detailed calculation
      const snapshotResponse = await fetch(
        `${API_BASE_URL}/compute/${data.calc_snapshot_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!snapshotResponse.ok) throw new Error("Failed to fetch calculation details");

      const snapshotData = await snapshotResponse.json();
      setCalcSnapshot(snapshotData);
      toast.success("Calculation completed!");
    } catch (error: any) {
      toast.error(error.message || "Calculation failed");
    } finally {
      setIsCalculating(false);
    }
  };

  if (isLoading || !profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse">
          <Sparkles className="w-12 h-12 text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto animate-fade-in">
        <Button variant="ghost" onClick={() => navigate("/dashboard")} className="mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>

        {/* Profile Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary/10 rounded-lg glow-primary">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gradient">{profile.name}</h1>
              <p className="text-muted-foreground">
                Born {new Date(profile.dob).toLocaleDateString()} at {profile.tob}
              </p>
              <p className="text-sm text-muted-foreground">{profile.place}</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={handleCalculate} disabled={isCalculating} className="glow-primary">
              <Calculator className="w-4 h-4 mr-2" />
              {isCalculating ? "Calculating..." : "Calculate Chart"}
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(`/profiles/${id}/predict`)}
              className="border-accent/50"
            >
              <Brain className="w-4 h-4 mr-2" />
              Ask Question
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(`/profiles/${id}/chat`)}
              className="border-accent/50"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              Chat
            </Button>
          </div>
        </div>

        {/* Content */}
        {!calcSnapshot ? (
          <Card className="card-glass">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="p-4 bg-primary/10 rounded-full mb-4">
                <Calculator className="w-12 h-12 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">No calculations yet</h3>
              <p className="text-muted-foreground text-center mb-6">
                Calculate the astrological chart to view detailed information
              </p>
              <Button onClick={handleCalculate} disabled={isCalculating} className="glow-primary">
                <Calculator className="w-4 h-4 mr-2" />
                {isCalculating ? "Calculating..." : "Calculate Now"}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-6 lg:grid-cols-8">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="planets">Planets</TabsTrigger>
              <TabsTrigger value="houses">Houses</TabsTrigger>
              <TabsTrigger value="aspects">Aspects</TabsTrigger>
              <TabsTrigger value="dignities">Dignities</TabsTrigger>
              <TabsTrigger value="timing">Timing</TabsTrigger>
              <TabsTrigger value="yogas">Yogas</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              {/* Meta Information */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="w-5 h-5" />
                    Calculation Info
                  </CardTitle>
                  <CardDescription>Meta information about the calculation</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {calcSnapshot.data?.meta && (
                    <>
                      <div>
                        <p className="text-sm text-muted-foreground">Ayanamsa</p>
                        <p className="font-semibold">{calcSnapshot.data.meta.ayanamsa}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">House System</p>
                        <p className="font-semibold">{calcSnapshot.data.meta.house_system}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Ephemeris</p>
                        <p className="font-semibold">{calcSnapshot.data.meta.ephemeris}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Ruleset</p>
                        <p className="font-semibold">{calcSnapshot.data.meta.ruleset_version}</p>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Panchanga */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Panchanga
                  </CardTitle>
                  <CardDescription>Daily celestial information</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {calcSnapshot.data?.panchanga && (
                    <>
                      <div>
                        <p className="text-sm text-muted-foreground">Weekday</p>
                        <p className="font-semibold">{calcSnapshot.data.panchanga.weekday}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Tithi</p>
                        <p className="font-semibold">{calcSnapshot.data.panchanga.tithi}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Nakshatra</p>
                        <p className="font-semibold">{calcSnapshot.data.panchanga.nakshatra}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Yoga</p>
                        <p className="font-semibold">{calcSnapshot.data.panchanga.yoga}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Karana</p>
                        <p className="font-semibold">{calcSnapshot.data.panchanga.karana}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Pada</p>
                        <p className="font-semibold">{calcSnapshot.data.panchanga.pada}</p>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Ascendant */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Ascendant
                  </CardTitle>
                  <CardDescription>Rising sign information</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.d1?.ascendant && (
                    <div className="space-y-2">
                      <p className="text-2xl font-bold text-primary">
                        {calcSnapshot.data.d1.ascendant.sign}
                      </p>
                      <p className="text-muted-foreground">
                        {calcSnapshot.data.d1.ascendant.degree.toFixed(2)}° in{" "}
                        {calcSnapshot.data.d1.ascendant.nakshatra} (Pada {calcSnapshot.data.d1.ascendant.pada})
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="planets" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {calcSnapshot.data?.d1?.planets?.map((planet: any) => (
                  <Card key={planet.name} className="card-glass">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center justify-between">
                        {planet.name}
                        {planet.retrograde && (
                          <Badge variant="outline" className="text-orange-500">
                            R
                          </Badge>
                        )}
                      </CardTitle>
                      <CardDescription>
                        House {planet.house} • {planet.sign}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Degree</span>
                        <span className="font-semibold">{planet.degree.toFixed(2)}°</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Nakshatra</span>
                        <span className="font-semibold">
                          {planet.nakshatra} ({planet.pada})
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Speed</span>
                        <span className="font-semibold">
                          {planet.speed ? planet.speed.toFixed(2) : 'N/A'}°/day
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="houses" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {calcSnapshot.data?.d1?.houses?.map((house: any) => (
                  <Card key={house.num} className="card-glass">
                    <CardHeader>
                      <CardTitle className="text-lg">House {house.num}</CardTitle>
                      <CardDescription>{house.sign}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Sign</span>
                          <span className="font-semibold">{house.sign}</span>
                        </div>
                        {house.cusp_degree && (
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Cusp Degree</span>
                            <span className="font-semibold">{house.cusp_degree.toFixed(2)}°</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="aspects" className="space-y-4">
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    Planetary Aspects
                  </CardTitle>
                  <CardDescription>All aspects between planets</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.aspects?.length > 0 ? (
                    <div className="space-y-3">
                      {calcSnapshot.data.aspects.map((aspect: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-primary/5 border border-primary/20">
                          <div className="flex items-center gap-3">
                            <span className="font-semibold text-primary">{aspect.from}</span>
                            <span className="text-muted-foreground">→</span>
                            <span className="font-semibold">{aspect.to}</span>
                            <Badge variant="outline">{aspect.type}</Badge>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-muted-foreground">
                              Orb: {aspect.orb_deg?.toFixed(1)}°
                            </div>
                            <div className="text-sm font-semibold">
                              Strength: {(aspect.strength * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No aspects data available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="dignities" className="space-y-4">
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Planetary Dignities
                  </CardTitle>
                  <CardDescription>Planetary strengths and states</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.dignities ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(calcSnapshot.data.dignities).map(([planet, dignity]: [string, any]) => (
                        <div key={planet} className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{planet}</span>
                            <Badge 
                              variant={dignity.dignity === 'Exalted' ? 'default' : 
                                      dignity.dignity === 'Debilitated' ? 'destructive' : 'outline'}
                              className={dignity.dignity === 'Exalted' ? 'bg-green-500' : 
                                        dignity.dignity === 'Debilitated' ? 'bg-red-500' : ''}
                            >
                              {dignity.dignity}
                            </Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Tier: {dignity.tier || 'N/A'}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No dignities data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Combustion */}
              {calcSnapshot.data?.combustion && (
                <Card className="card-glass">
                  <CardHeader>
                    <CardTitle>Combustion</CardTitle>
                    <CardDescription>Planets too close to the Sun</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(calcSnapshot.data.combustion).map(([planet, combust]: [string, any]) => (
                        combust && (
                          <div key={planet} className="flex items-center gap-2 p-2 rounded bg-orange-100 dark:bg-orange-900/20">
                            <span className="text-orange-600 dark:text-orange-400">⚠</span>
                            <span className="font-semibold">{planet}</span>
                            <span className="text-sm text-muted-foreground">is combust</span>
                          </div>
                        )
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="timing" className="space-y-4">
              {/* Dasha Information */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Dasha System
                  </CardTitle>
                  <CardDescription>Current planetary periods</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.dasha ? (
                    <div className="space-y-6">
                      {/* Complete Dasha Sequence */}
                      {calcSnapshot.data.dasha.complete_sequence && (
                        <div className="space-y-4">
                          <h4 className="font-semibold text-lg">Complete Dasha Sequence</h4>
                          
                          {/* Maha Dasha */}
                          {calcSnapshot.data.dasha.complete_sequence.maha_dasha && (
                            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                              <div className="flex items-center justify-between mb-2">
                                <div className="text-sm text-muted-foreground">Maha Dasha</div>
                                <div className="text-xs text-muted-foreground">
                                  {calcSnapshot.data.dasha.complete_sequence.maha_dasha.remaining_years?.toFixed(1) || '0.0'} years remaining
                                </div>
                              </div>
                              <div className="text-xl font-bold text-primary mb-2">
                                {calcSnapshot.data.dasha.complete_sequence.maha_dasha.planet || 'Unknown'}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {calcSnapshot.data.dasha.complete_sequence.maha_dasha.start_date || 'N/A'} - {calcSnapshot.data.dasha.complete_sequence.maha_dasha.end_date || 'N/A'}
                              </div>
                              <div className="mt-2">
                                <div className="w-full bg-muted rounded-full h-2">
                                  <div 
                                    className="bg-primary h-2 rounded-full transition-all duration-300" 
                                    style={{ 
                                      width: `${calcSnapshot.data.dasha.complete_sequence.maha_dasha.total_years && calcSnapshot.data.dasha.complete_sequence.maha_dasha.remaining_years ? 
                                        ((calcSnapshot.data.dasha.complete_sequence.maha_dasha.total_years - calcSnapshot.data.dasha.complete_sequence.maha_dasha.remaining_years) / calcSnapshot.data.dasha.complete_sequence.maha_dasha.total_years) * 100 : 0}%` 
                                    }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Antar Dasha */}
                          {calcSnapshot.data.dasha.complete_sequence.antar_dasha && (
                            <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                              <div className="flex items-center justify-between mb-2">
                                <div className="text-sm text-muted-foreground">Antar Dasha</div>
                                <div className="text-xs text-muted-foreground">
                                  {calcSnapshot.data.dasha.complete_sequence.antar_dasha.remaining_years?.toFixed(2) || '0.00'} years remaining
                                </div>
                              </div>
                              <div className="text-xl font-bold text-secondary mb-2">
                                {calcSnapshot.data.dasha.complete_sequence.antar_dasha.planet || 'Unknown'}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {calcSnapshot.data.dasha.complete_sequence.antar_dasha.start_date || 'N/A'} - {calcSnapshot.data.dasha.complete_sequence.antar_dasha.end_date || 'N/A'}
                              </div>
                              <div className="mt-2">
                                <div className="w-full bg-muted rounded-full h-2">
                                  <div 
                                    className="bg-secondary h-2 rounded-full transition-all duration-300" 
                                    style={{ 
                                      width: `${calcSnapshot.data.dasha.complete_sequence.antar_dasha.total_years && calcSnapshot.data.dasha.complete_sequence.antar_dasha.remaining_years ? 
                                        ((calcSnapshot.data.dasha.complete_sequence.antar_dasha.total_years - calcSnapshot.data.dasha.complete_sequence.antar_dasha.remaining_years) / calcSnapshot.data.dasha.complete_sequence.antar_dasha.total_years) * 100 : 0}%` 
                                    }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Paryantar Dasha */}
                          {calcSnapshot.data.dasha.complete_sequence.paryantar_dasha && (
                            <div className="p-4 rounded-lg bg-accent/5 border border-accent/20">
                              <div className="flex items-center justify-between mb-2">
                                <div className="text-sm text-muted-foreground">Paryantar Dasha</div>
                                <div className="text-xs text-muted-foreground">
                                  {calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.remaining_years?.toFixed(3) || '0.000'} years remaining
                                </div>
                              </div>
                              <div className="text-xl font-bold text-accent-foreground mb-2">
                                {calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.planet || 'Unknown'}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.start_date || 'N/A'} - {calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.end_date || 'N/A'}
                              </div>
                              <div className="mt-2">
                                <div className="w-full bg-muted rounded-full h-2">
                                  <div 
                                    className="bg-accent h-2 rounded-full transition-all duration-300" 
                                    style={{ 
                                      width: `${calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.total_years && calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.remaining_years ? 
                                        ((calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.total_years - calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.remaining_years) / calcSnapshot.data.dasha.complete_sequence.paryantar_dasha.total_years) * 100 : 0}%` 
                                    }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Fallback: Basic Dasha Info */}
                      {!calcSnapshot.data.dasha.complete_sequence && (
                        <div className="space-y-4">
                          <h4 className="font-semibold text-lg">Current Dasha Information</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                              <div className="text-sm text-muted-foreground">Current Mahadasha</div>
                              <div className="text-xl font-bold text-primary">{calcSnapshot.data.dasha.current_md || 'Unknown'}</div>
                            </div>
                            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                              <div className="text-sm text-muted-foreground">Current Antardasha</div>
                              <div className="text-xl font-bold text-primary">{calcSnapshot.data.dasha.current_ad || 'Unknown'}</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Next 12 Months */}
                      {calcSnapshot.data.dasha.next_12m_ads && calcSnapshot.data.dasha.next_12m_ads.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-3">Next 12 Months - Antar Dasha Changes</h4>
                          <div className="space-y-2">
                            {calcSnapshot.data.dasha.next_12m_ads.map((ad: any, index: number) => (
                              <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border">
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
                                    {(ad.ad || ad.planet)?.charAt(0) || '?'}
                                  </div>
                                  <div>
                                    <span className="font-medium">{ad.ad || ad.planet || 'Unknown'}</span>
                                    <div className="text-xs text-muted-foreground">Antar Dasha</div>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-sm font-medium">
                                    {ad.start || ad.start_date || 'N/A'} - {ad.end || ad.end_date || 'N/A'}
                                  </div>
                                  <div className="text-xs text-muted-foreground">
                                    {(ad.start || ad.start_date) && (ad.end || ad.end_date) ? 
                                      Math.ceil((new Date(ad.end || ad.end_date).getTime() - new Date(ad.start || ad.start_date).getTime()) / (1000 * 60 * 60 * 24)) + ' days' : 
                                      'Duration unknown'
                                    }
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No dasha data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Transits */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Current Transits
                  </CardTitle>
                  <CardDescription>Major planetary transits</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.transits ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                          <div className="text-sm text-muted-foreground">Saturn House</div>
                          <div className="text-lg font-bold text-primary">{calcSnapshot.data.transits.saturn_house_from_lagna}</div>
                        </div>
                        <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                          <div className="text-sm text-muted-foreground">Jupiter House</div>
                          <div className="text-lg font-bold text-primary">{calcSnapshot.data.transits.jupiter_house_from_lagna}</div>
                        </div>
                      </div>
                      
                      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                        <div className="text-sm text-muted-foreground">Rahu-Ketu Axis</div>
                        <div className="text-lg font-bold text-primary">
                          Houses {calcSnapshot.data.transits.rahu_ketu_axis_from_lagna?.join(', ')}
                        </div>
                      </div>
                      
                      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                        <div className="text-sm text-muted-foreground">Sade Sati Phase</div>
                        <div className="text-lg font-bold text-primary capitalize">{calcSnapshot.data.transits.sade_sati_phase}</div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No transit data available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="yogas" className="space-y-4">
              {calcSnapshot.data?.yogas?.length > 0 ? (
                <div className="grid grid-cols-1 gap-4">
                  {calcSnapshot.data.yogas.map((yoga: any, index: number) => (
                    <Card key={index} className="card-glass">
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          {yoga.name}
                          <Badge 
                            variant={yoga.present ? "default" : "outline"} 
                            className={yoga.present ? "bg-green-500" : ""}
                          >
                            {yoga.present ? "Present" : "Not Present"}
                          </Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          {yoga.reason}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="card-glass">
                  <CardContent className="py-12 text-center">
                    <p className="text-muted-foreground">No yogas detected in this chart</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="advanced" className="space-y-4">
              {/* D9 Chart */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="w-5 h-5" />
                    D9 Chart (Navamsha)
                  </CardTitle>
                  <CardDescription>Spiritual and deeper analysis chart</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.d9 ? (
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                        <div className="text-sm text-muted-foreground">D9 Ascendant</div>
                        <div className="text-lg font-bold">
                          {typeof calcSnapshot.data.d9.asc_sign === 'string' 
                            ? calcSnapshot.data.d9.asc_sign 
                            : calcSnapshot.data.d9.asc_sign?.sign || 'Unknown'}
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold mb-3">Planet Signs in D9</h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {Object.entries(calcSnapshot.data.d9.planet_signs || {}).map(([planet, signData]: [string, any]) => {
                            // Handle both string and object formats
                            const sign = typeof signData === 'string' ? signData : signData?.sign || 'Unknown';
                            return (
                              <div key={planet} className="p-3 rounded bg-muted">
                                <div className="text-sm text-muted-foreground">{planet}</div>
                                <div className="font-semibold">{sign}</div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No D9 data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Ashtakavarga */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Ashtakavarga (SAV)
                  </CardTitle>
                  <CardDescription>Strength points for each house</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.sav?.sav_values ? (
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                      {calcSnapshot.data.sav.sav_values.map((value: number, index: number) => (
                        <div key={index} className="p-3 rounded-lg bg-primary/5 border border-primary/20 text-center">
                          <div className="text-sm text-muted-foreground">House {index + 1}</div>
                          <div className="text-lg font-bold text-primary">{value}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No SAV data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Bhava Bala */}
              <Card className="card-glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Bhava Bala
                  </CardTitle>
                  <CardDescription>House strength calculations</CardDescription>
                </CardHeader>
                <CardContent>
                  {calcSnapshot.data?.bhava_bala ? (
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                      {Object.entries(calcSnapshot.data.bhava_bala).map(([house, strength]: [string, any]) => (
                        <div key={house} className="p-3 rounded-lg bg-primary/5 border border-primary/20 text-center">
                          <div className="text-sm text-muted-foreground">House {house}</div>
                          <div className="text-lg font-bold text-primary">
                            {(strength * 100).toFixed(0)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No Bhava Bala data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Sensitivity Analysis */}
              {calcSnapshot.data?.sensitivity && (
                <Card className="card-glass">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="w-5 h-5" />
                      Sensitivity Analysis
                    </CardTitle>
                    <CardDescription>Impact of birth time uncertainty</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-primary/5 border border-primary/20">
                        <span className="font-semibold text-primary">Lagna Flips</span>
                        <Badge variant={calcSnapshot.data.sensitivity.lagna_flip ? "destructive" : "outline"}>
                          {calcSnapshot.data.sensitivity.lagna_flip ? "Risky" : "Safe"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-primary/5 border border-primary/20">
                        <span className="font-semibold text-primary">Moon Sign Flips</span>
                        <Badge variant={calcSnapshot.data.sensitivity.moon_flip ? "destructive" : "outline"}>
                          {calcSnapshot.data.sensitivity.moon_flip ? "Risky" : "Safe"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-primary/5 border border-primary/20">
                        <span className="font-semibold text-primary">Dasha Boundary</span>
                        <Badge variant={calcSnapshot.data.sensitivity.dasha_boundary_risky ? "destructive" : "outline"}>
                          {calcSnapshot.data.sensitivity.dasha_boundary_risky ? "Risky" : "Safe"}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
};

export default ProfileDetail;
