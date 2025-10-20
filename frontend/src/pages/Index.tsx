import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sparkles, Star, Moon, Sun } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-accent/20 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-secondary/10 rounded-full blur-3xl animate-pulse-slow" />
      </div>

      <div className="relative z-10 text-center max-w-4xl mx-auto animate-fade-in">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            <div className="absolute inset-0 animate-pulse-slow glow-primary rounded-full" />
            <div className="relative p-6 bg-primary/10 rounded-full backdrop-blur-xl border border-primary/30">
              <Sparkles className="w-16 h-16 text-primary" />
            </div>
          </div>
        </div>

        {/* Hero Text */}
        <h1 className="text-5xl md:text-7xl font-bold mb-6">
          <span className="text-gradient">Discover Your</span>
          <br />
          <span className="text-gradient">Cosmic Path</span>
        </h1>

        <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl mx-auto">
          Unlock the wisdom of Vedic astrology with AI-powered predictions and personalized insights
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button
            size="lg"
            onClick={() => navigate("/auth")}
            className="text-lg px-8 py-6 glow-primary"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            Get Started
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={() => navigate("/auth")}
            className="text-lg px-8 py-6 border-primary/30"
          >
            Learn More
          </Button>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
          <div className="p-6 card-glass rounded-xl hover:glow-primary transition-all">
            <div className="p-3 bg-primary/10 rounded-lg w-fit mx-auto mb-4">
              <Star className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Precise Calculations</h3>
            <p className="text-muted-foreground">
              Advanced Vedic astrology calculations with Swiss Ephemeris accuracy
            </p>
          </div>

          <div className="p-6 card-glass rounded-xl hover:glow-primary transition-all">
            <div className="p-3 bg-accent/10 rounded-lg w-fit mx-auto mb-4">
              <Moon className="w-8 h-8 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-2">AI Predictions</h3>
            <p className="text-muted-foreground">
              Get personalized predictions powered by advanced AI models
            </p>
          </div>

          <div className="p-6 card-glass rounded-xl hover:glow-primary transition-all">
            <div className="p-3 bg-secondary/10 rounded-lg w-fit mx-auto mb-4">
              <Sun className="w-8 h-8 text-secondary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Deep Insights</h3>
            <p className="text-muted-foreground">
              Comprehensive analysis of yogas, dashas, and planetary transits
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
