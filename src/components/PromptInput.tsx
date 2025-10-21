import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

const EXAMPLE_PROMPTS = [
  "Portfolio website with about, projects, and contact sections",
  "Todo list app with add, delete, and mark complete features",
  "Landing page for a SaaS product with pricing tiers",
  "Weather dashboard with city search and 5-day forecast",
];

const PLACEHOLDER = `Example: Create a modern calculator app with all mathematical operations (addition, subtraction, multiplication, division). Style it with a dark theme using CSS and implement full functionality with JavaScript. Include a display screen, number buttons 0-9, operation buttons, equals button, and a clear button.`;

export default function PromptInput({ onSubmit, isLoading }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");
  const maxLength = 2000;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim().length < 10) {
      toast.error("Please provide a more detailed description (at least 10 characters)");
      return;
    }
    onSubmit(prompt);
  };

  const handleExampleClick = (example: string) => {
    setPrompt(example);
    toast.success("Example prompt loaded - edit it or generate directly!");
  };

  const charCount = prompt.length;
  const isValid = charCount > 0 && charCount <= maxLength;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-fade-in-up">
      {/* Example Prompts */}
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">Try these examples:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_PROMPTS.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="px-4 py-2 text-sm rounded-lg glass-card hover:bg-primary/10 hover:border-primary/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={PLACEHOLDER}
            disabled={isLoading}
            maxLength={maxLength}
            className="min-h-[200px] resize-none glass-card text-base focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300"
          />
          <div
            className={`absolute bottom-3 right-3 text-xs ${
              charCount > maxLength * 0.9 ? "text-destructive" : "text-muted-foreground"
            }`}
          >
            {charCount} / {maxLength}
          </div>
        </div>

        <Button
          type="submit"
          variant="hero"
          size="xl"
          disabled={!isValid || isLoading}
          className="w-full sm:w-auto"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" />
              Building your website...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Generate Website
            </>
          )}
        </Button>
      </form>
    </div>
  );
}
