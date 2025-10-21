import { Brain, Building2, Code2, CheckCircle2, Loader2 } from "lucide-react";

interface ProgressTrackerProps {
  currentProgress: "pending" | "planner" | "architect" | "coder" | "done";
}

const STEPS = [
  {
    id: "planner",
    icon: Brain,
    label: "Planning",
    description: "Analyzing requirements",
  },
  {
    id: "architect",
    icon: Building2,
    label: "Architecture",
    description: "Designing structure",
  },
  {
    id: "coder",
    icon: Code2,
    label: "Coding",
    description: "Writing code",
  },
];

export default function ProgressTracker({ currentProgress }: ProgressTrackerProps) {
  const getStepStatus = (stepId: string): "pending" | "processing" | "completed" => {
    if (currentProgress === "done") return "completed";
    if (currentProgress === "pending") return "pending";
    
    const stepIndex = STEPS.findIndex((s) => s.id === stepId);
    const currentIndex = STEPS.findIndex((s) => s.id === currentProgress);
    
    if (currentIndex > stepIndex) return "completed";
    if (currentIndex === stepIndex) return "processing";
    return "pending";
  };

  const getCurrentStepLabel = () => {
    if (currentProgress === "done") return "Build complete!";
    const step = STEPS.find((s) => s.id === currentProgress);
    return step ? `${step.label}...` : "Initializing...";
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 animate-fade-in-up">
      {/* Status Message */}
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-bold gradient-text">{getCurrentStepLabel()}</h3>
        <p className="text-muted-foreground">This usually takes 30-60 seconds</p>
      </div>

      {/* Progress Stepper */}
      <div className="relative">
        {/* Progress Line */}
        <div className="absolute top-6 left-0 right-0 h-0.5 bg-border">
          <div
            className="h-full bg-gradient-primary transition-all duration-500"
            style={{
              width: `${
                currentProgress === "pending"
                  ? 0
                  : currentProgress === "done"
                  ? 100
                  : ((STEPS.findIndex((s) => s.id === currentProgress) + 1) / STEPS.length) * 100
              }%`,
            }}
          />
        </div>

        {/* Steps */}
        <div className="relative flex justify-between">
          {STEPS.map((step, index) => {
            const status = getStepStatus(step.id);
            const Icon = step.icon;

            return (
              <div key={step.id} className="flex flex-col items-center space-y-2">
                {/* Icon Circle */}
                <div
                  className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 ${
                    status === "completed"
                      ? "bg-success text-success-foreground scale-110"
                      : status === "processing"
                      ? "bg-primary text-primary-foreground animate-pulse-glow scale-110"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {status === "completed" ? (
                    <CheckCircle2 className="w-6 h-6 animate-scale-in" />
                  ) : status === "processing" ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </div>

                {/* Label */}
                <div className="text-center">
                  <p
                    className={`font-semibold text-sm ${
                      status === "completed" || status === "processing"
                        ? "text-foreground"
                        : "text-muted-foreground"
                    }`}
                  >
                    {step.label}
                  </p>
                  <p className="text-xs text-muted-foreground hidden sm:block">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Progress Bar (optional alternative) */}
      <div className="w-full bg-border rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-gradient-primary transition-all duration-500 rounded-full"
          style={{
            width: `${
              currentProgress === "pending"
                ? 0
                : currentProgress === "done"
                ? 100
                : ((STEPS.findIndex((s) => s.id === currentProgress) + 1) / STEPS.length) * 100
            }%`,
          }}
        />
      </div>
    </div>
  );
}
