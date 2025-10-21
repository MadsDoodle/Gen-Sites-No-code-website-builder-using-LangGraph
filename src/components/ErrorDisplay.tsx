import { AlertCircle, RefreshCw, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorDisplayProps {
  error: string;
  onRetry: () => void;
}

export default function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  return (
    <div className="w-full max-w-2xl mx-auto animate-fade-in-up">
      <div className="glass-card rounded-lg p-8 border-destructive/50">
        {/* Error Icon */}
        <div className="flex items-center justify-center w-16 h-16 rounded-full bg-destructive/20 mx-auto mb-4">
          <AlertCircle className="w-10 h-10 text-destructive" />
        </div>

        {/* Error Message */}
        <div className="text-center space-y-4">
          <h3 className="text-2xl font-bold text-destructive">Build Failed</h3>
          <p className="text-foreground/80">
            {error || "An unexpected error occurred while building your website."}
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <Button variant="hero" size="lg" onClick={onRetry}>
              <RefreshCw />
              Try Again
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() =>
                window.open("mailto:support@example.com?subject=Build Error", "_blank")
              }
            >
              <Mail />
              Contact Support
            </Button>
          </div>
        </div>

        {/* Error Details */}
        <div className="mt-6 p-4 rounded-md bg-destructive/10 border border-destructive/20">
          <p className="text-xs font-mono text-destructive/80 break-words">
            Error: {error}
          </p>
        </div>
      </div>
    </div>
  );
}
