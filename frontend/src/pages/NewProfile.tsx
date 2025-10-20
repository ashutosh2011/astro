import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { ArrowLeft, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

const NewProfile = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    gender: "male",
    dob: "",
    tob: "",
    tz: "America/New_York",
    place: "",
    lat: "",
    lon: "",
    altitude_m: "10",
    uncertainty_minutes: "5",
    ayanamsa: "Lahiri",
    house_system: "WholeSign",
  });

  // Common timezones for dropdown
  const timezones = [
    { value: "America/New_York", label: "Eastern Time (ET)" },
    { value: "America/Chicago", label: "Central Time (CT)" },
    { value: "America/Denver", label: "Mountain Time (MT)" },
    { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
    { value: "America/Phoenix", label: "Arizona Time" },
    { value: "America/Anchorage", label: "Alaska Time" },
    { value: "Pacific/Honolulu", label: "Hawaii Time" },
    { value: "Europe/London", label: "London (GMT/BST)" },
    { value: "Europe/Paris", label: "Paris (CET/CEST)" },
    { value: "Europe/Berlin", label: "Berlin (CET/CEST)" },
    { value: "Europe/Rome", label: "Rome (CET/CEST)" },
    { value: "Europe/Madrid", label: "Madrid (CET/CEST)" },
    { value: "Asia/Tokyo", label: "Tokyo (JST)" },
    { value: "Asia/Shanghai", label: "Shanghai (CST)" },
    { value: "Asia/Kolkata", label: "Mumbai/Delhi (IST)" },
    { value: "Asia/Dubai", label: "Dubai (GST)" },
    { value: "Australia/Sydney", label: "Sydney (AEST/AEDT)" },
    { value: "Australia/Melbourne", label: "Melbourne (AEST/AEDT)" },
    { value: "Pacific/Auckland", label: "Auckland (NZST/NZDT)" },
  ];

  // Geocoding function to get lat/lon from city name
  const geocodeCity = async (city: string) => {
    if (!city.trim()) return;
    
    setIsGeocoding(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(city)}&limit=1`
      );
      const data = await response.json();
      
      if (data && data.length > 0) {
        const result = data[0];
        setFormData(prev => ({
          ...prev,
          lat: parseFloat(result.lat).toFixed(6),
          lon: parseFloat(result.lon).toFixed(6),
        }));
        toast.success("Location coordinates found!");
      } else {
        toast.error("Could not find coordinates for this location");
      }
    } catch (error) {
      toast.error("Failed to get location coordinates");
    } finally {
      setIsGeocoding(false);
    }
  };

  // Debounced geocoding effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (formData.place && !formData.lat && !formData.lon) {
        geocodeCity(formData.place);
      }
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [formData.place]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const token = localStorage.getItem("astro_token");
      if (!token) {
        navigate("/auth");
        return;
      }

      // Validate required fields
      if (!formData.name.trim()) {
        toast.error("Name is required");
        return;
      }
      if (!formData.dob) {
        toast.error("Date of birth is required");
        return;
      }
      if (!formData.tob) {
        toast.error("Time of birth is required");
        return;
      }
      if (!formData.place.trim()) {
        toast.error("Birth place is required");
        return;
      }
      if (!formData.lat || !formData.lon) {
        toast.error("Please wait for coordinates to be loaded or enter them manually");
        return;
      }

      // Validate numeric fields
      const lat = parseFloat(formData.lat);
      const lon = parseFloat(formData.lon);
      const altitude = parseFloat(formData.altitude_m);
      const uncertainty = parseInt(formData.uncertainty_minutes);

      if (isNaN(lat) || lat < -90 || lat > 90) {
        toast.error("Invalid latitude. Must be between -90 and 90");
        return;
      }
      if (isNaN(lon) || lon < -180 || lon > 180) {
        toast.error("Invalid longitude. Must be between -180 and 180");
        return;
      }
      if (isNaN(altitude) || altitude < -500 || altitude > 10000) {
        toast.error("Invalid altitude. Must be between -500 and 10000 meters");
        return;
      }
      if (isNaN(uncertainty) || uncertainty < 0 || uncertainty > 10) {
        toast.error("Invalid uncertainty. Must be between 0 and 10 minutes");
        return;
      }

      const payload = {
        ...formData,
        lat,
        lon,
        altitude_m: altitude,
        uncertainty_minutes: uncertainty,
      };

      console.log("Sending payload:", payload); // Debug log

      const response = await fetch(`${API_BASE_URL}/profiles/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        console.error("API Error:", error); // Debug log
        throw new Error(error.detail || error.message || "Failed to create profile");
      }

      const data = await response.json();
      toast.success("Profile created successfully!");
      navigate(`/profiles/${data.id}`);
    } catch (error: any) {
      console.error("Submit error:", error); // Debug log
      toast.error(error.message || "Failed to create profile");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-2xl mx-auto animate-fade-in">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-primary/10 rounded-lg glow-primary">
            <Sparkles className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gradient">New Profile</h1>
            <p className="text-muted-foreground">Create a new astrological chart</p>
          </div>
        </div>

        <Card className="card-glass">
          <CardHeader>
            <CardTitle>Birth Information</CardTitle>
            <CardDescription>Enter accurate birth details for precise calculations</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gender">Gender</Label>
                  <Select value={formData.gender} onValueChange={(value) => setFormData({ ...formData, gender: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Male</SelectItem>
                      <SelectItem value="female">Female</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Birth Date & Time */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="dob">Date of Birth</Label>
                  <Input
                    id="dob"
                    type="date"
                    value={formData.dob}
                    onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tob">Time of Birth</Label>
                  <Input
                    id="tob"
                    type="time"
                    value={formData.tob}
                    onChange={(e) => setFormData({ ...formData, tob: e.target.value })}
                    required
                  />
                </div>
              </div>

              {/* Location */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="place">Birth Place</Label>
                  <div className="relative">
                    <Input
                      id="place"
                      placeholder="e.g., New York, NY"
                      value={formData.place}
                      onChange={(e) => setFormData({ ...formData, place: e.target.value })}
                      required
                    />
                    {isGeocoding && (
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Coordinates will be automatically filled when you enter a city
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="lat">Latitude</Label>
                    <Input
                      id="lat"
                      type="number"
                      step="0.0001"
                      placeholder="40.7128"
                      value={formData.lat}
                      onChange={(e) => setFormData({ ...formData, lat: e.target.value })}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="lon">Longitude</Label>
                    <Input
                      id="lon"
                      type="number"
                      step="0.0001"
                      placeholder="-74.0060"
                      value={formData.lon}
                      onChange={(e) => setFormData({ ...formData, lon: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tz">Timezone</Label>
                  <Select value={formData.tz} onValueChange={(value) => setFormData({ ...formData, tz: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select timezone" />
                    </SelectTrigger>
                    <SelectContent>
                      {timezones.map((tz) => (
                        <SelectItem key={tz.value} value={tz.value}>
                          {tz.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Advanced Settings */}
              <div className="space-y-4 pt-4 border-t border-border">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  className="flex items-center gap-2 p-0 h-auto text-sm font-semibold text-muted-foreground hover:text-foreground"
                >
                  Advanced Settings
                  {showAdvancedSettings ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </Button>
                
                {showAdvancedSettings && (
                  <div className="space-y-4 animate-in slide-in-from-top-2 duration-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="altitude_m">Altitude (meters)</Label>
                        <Input
                          id="altitude_m"
                          type="number"
                          placeholder="10"
                          value={formData.altitude_m}
                          onChange={(e) => setFormData({ ...formData, altitude_m: e.target.value })}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="uncertainty_minutes">Time Uncertainty (minutes)</Label>
                        <Input
                          id="uncertainty_minutes"
                          type="number"
                          placeholder="5"
                          value={formData.uncertainty_minutes}
                          onChange={(e) => setFormData({ ...formData, uncertainty_minutes: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="ayanamsa">Ayanamsa</Label>
                        <Select value={formData.ayanamsa} onValueChange={(value) => setFormData({ ...formData, ayanamsa: value })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Lahiri">Lahiri</SelectItem>
                            <SelectItem value="Raman">Raman</SelectItem>
                            <SelectItem value="KP">KP</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="house_system">House System</Label>
                        <Select value={formData.house_system} onValueChange={(value) => setFormData({ ...formData, house_system: value })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="WholeSign">Whole Sign</SelectItem>
                            <SelectItem value="Placidus">Placidus</SelectItem>
                            <SelectItem value="Equal">Equal</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <Button type="submit" className="w-full glow-primary" disabled={isLoading}>
                {isLoading ? "Creating..." : "Create Profile"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NewProfile;
