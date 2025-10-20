import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Plus, User, LogOut, Sparkles } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

interface Profile {
  id: number;
  name: string;
  dob: string;
  place: string;
  created_at: string;
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("astro_token");
    if (!token) {
      navigate("/auth");
      return;
    }
    fetchProfiles();
  }, [navigate]);

  const fetchProfiles = async () => {
    try {
      const token = localStorage.getItem("astro_token");
      const response = await fetch(`${API_BASE_URL}/profiles/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch profiles");
      }

      const data = await response.json();
      setProfiles(data.profiles || []);
    } catch (error: any) {
      toast.error(error.message || "Failed to load profiles");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("astro_token");
    toast.success("Logged out successfully");
    navigate("/auth");
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 animate-fade-in">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg glow-primary">
              <Sparkles className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gradient">Your Profiles</h1>
              <p className="text-muted-foreground">Manage your astrological charts</p>
            </div>
          </div>
          <Button variant="outline" size="icon" onClick={handleLogout}>
            <LogOut className="w-4 h-4" />
          </Button>
        </div>

        {/* Create Profile Button */}
        <Button
          onClick={() => navigate("/profiles/new")}
          className="w-full md:w-auto mb-6 glow-primary"
          size="lg"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create New Profile
        </Button>

        {/* Profiles Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="card-glass animate-pulse">
                <CardHeader>
                  <div className="h-6 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2 mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-full mb-2" />
                  <div className="h-4 bg-muted rounded w-2/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : profiles.length === 0 ? (
          <Card className="card-glass border-dashed border-2 border-primary/30">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="p-4 bg-primary/10 rounded-full mb-4">
                <User className="w-12 h-12 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">No profiles yet</h3>
              <p className="text-muted-foreground text-center mb-6">
                Create your first astrological profile to get started with predictions
              </p>
              <Button onClick={() => navigate("/profiles/new")} className="glow-primary">
                <Plus className="w-4 h-4 mr-2" />
                Create Profile
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profiles.map((profile) => (
              <Card
                key={profile.id}
                className="card-glass cursor-pointer hover:border-primary/50 transition-all hover:glow-primary"
                onClick={() => navigate(`/profiles/${profile.id}`)}
              >
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5 text-primary" />
                    {profile.name}
                  </CardTitle>
                  <CardDescription>Born {new Date(profile.dob).toLocaleDateString()}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{profile.place}</p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Created {new Date(profile.created_at).toLocaleDateString()}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
