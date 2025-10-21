import { useState, useEffect } from "react";
import { Sparkles } from "lucide-react";
import AnimatedBackground from "@/components/AnimatedBackground";
import PromptInput from "@/components/PromptInput";
import ProgressTracker from "@/components/ProgressTracker";
import ResultsDisplay from "@/components/ResultsDisplay";
import ErrorDisplay from "@/components/ErrorDisplay";
import { toast } from "sonner";
import heroImage from "@/assets/hero-bg.jpg";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type BuildStatus = "idle" | "building" | "completed" | "failed";
type Progress = "pending" | "planner" | "architect" | "coder" | "done";

export default function Index() {
  const [status, setStatus] = useState<BuildStatus>("idle");
  const [progress, setProgress] = useState<Progress>("pending");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (taskId && status === "building") {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/status/${taskId}`);
          if (!response.ok) throw new Error("Failed to fetch status");
          
          const data = await response.json();
          setProgress(data.progress || "pending");

          if (data.status === "completed") {
            setStatus("completed");
            clearInterval(interval);
            await fetchBuildResult(taskId);
            toast.success("Website built successfully! 🎉");
          } else if (data.status === "failed") {
            setStatus("failed");
            setError(data.error || "Build failed");
            clearInterval(interval);
            toast.error("Build failed");
          }
        } catch (err) {
          console.error("Polling error:", err);
          // Continue polling unless we get a critical error
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [taskId, status]);

  const fetchBuildResult = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/result/${id}`);
      if (!response.ok) throw new Error("Failed to fetch result");
      
      const data = await response.json();
      setFiles(data.files || []);
    } catch (err) {
      console.error("Error fetching result:", err);
      toast.error("Failed to load build results");
    }
  };

  const handleSubmit = async (prompt: string) => {
    setStatus("building");
    setProgress("pending");
    setError(null);
    setFiles([]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/build-website`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_prompt: prompt }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to start build");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      toast.success("Build started! 🚀");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to start build";
      setStatus("failed");
      setError(errorMessage);
      toast.error(errorMessage);
    }
  };

  const handleReset = () => {
    setStatus("idle");
    setProgress("pending");
    setTaskId(null);
    setFiles([]);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleRetry = () => {
    setStatus("idle");
    setError(null);
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-secondary/5" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[800px] h-[800px] bg-secondary/10 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 py-8 sm:py-12">
        {/* Hero Section */}
        {status === "idle" && (
          <section className="text-center space-y-8 mb-16 animate-fade-in">
            {/* Hero Image */}
            <div className="relative w-full max-w-4xl mx-auto h-[300px] sm:h-[400px] rounded-2xl overflow-hidden mb-8 glass-card">
              <img
                src={heroImage}
                alt="AI coding a website"
                className="w-full h-full object-cover opacity-80"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/50 to-transparent" />
            </div>

            {/* Logo/Brand */}
            <div className="inline-flex items-center justify-center gap-3 px-6 py-3 glass-card rounded-full">
              <Sparkles className="w-6 h-6 text-primary animate-pulse-glow" />
              <span className="text-lg font-bold">AI Website Builder</span>
            </div>

            {/* Main Headline */}
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight">
                Build Websites with{" "}
                <span className="gradient-text">AI in Seconds</span>
              </h1>
              <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto">
                Describe your idea and watch our AI agents design, architect, and code your
                website automatically
              </p>
            </div>

            {/* How It Works */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto pt-8">
              {[
                { step: "1", title: "Describe", desc: "Tell us what you want to build" },
                { step: "2", title: "Generate", desc: "AI creates your website" },
                { step: "3", title: "Download", desc: "Get production-ready code" },
              ].map((item) => (
                <div
                  key={item.step}
                  className="glass-card p-6 rounded-xl text-center space-y-2 hover:scale-105 transition-transform duration-300"
                >
                  <div className="w-12 h-12 rounded-full bg-gradient-primary mx-auto flex items-center justify-center text-xl font-bold mb-2">
                    {item.step}
                  </div>
                  <h3 className="font-semibold text-lg">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Main Content */}
        <main className="space-y-12">
          {status === "idle" && (
            <PromptInput onSubmit={handleSubmit} isLoading={false} />
          )}

          {status === "building" && <ProgressTracker currentProgress={progress} />}

          {status === "completed" && taskId && (
            <ResultsDisplay
              taskId={taskId}
              files={files}
              onReset={handleReset}
              apiBaseUrl={API_BASE_URL}
            />
          )}

          {status === "failed" && error && (
            <ErrorDisplay error={error} onRetry={handleRetry} />
          )}
        </main>

        {/* Footer */}
        <footer className="mt-24 text-center text-sm text-muted-foreground">
          <p>Powered by AI • Built with React & TypeScript</p>
        </footer>
      </div>
    </div>
  );
}
