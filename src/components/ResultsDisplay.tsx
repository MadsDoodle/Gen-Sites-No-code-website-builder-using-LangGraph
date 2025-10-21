import { useState, useEffect } from "react";
import { CheckCircle2, Download, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import FileTree from "./FileTree";
import CodeViewer from "./CodeViewer";
import { toast } from "sonner";

interface ResultsDisplayProps {
  taskId: string;
  files: string[];
  onReset: () => void;
  apiBaseUrl: string;
}

export default function ResultsDisplay({
  taskId,
  files,
  onReset,
  apiBaseUrl,
}: ResultsDisplayProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [buildTime, setBuildTime] = useState<number | null>(null);

  useEffect(() => {
    if (files.length > 0 && !selectedFile) {
      // Auto-select first HTML file or first file
      const firstHtml = files.find((f) => f.endsWith(".html"));
      setSelectedFile(firstHtml || files[0]);
    }
  }, [files, selectedFile]);

  useEffect(() => {
    if (selectedFile) {
      fetchFileContent(selectedFile);
    }
  }, [selectedFile]);

  const fetchFileContent = async (filePath: string) => {
    setIsLoadingFile(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/file/${taskId}/${encodeURIComponent(filePath)}`
      );
      if (!response.ok) throw new Error("Failed to fetch file content");
      const data = await response.json();
      setFileContent(data.content);
    } catch (error) {
      toast.error("Failed to load file content");
      console.error("Error fetching file:", error);
    } finally {
      setIsLoadingFile(false);
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/download/${taskId}`);
      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `website_${taskId}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Project downloaded successfully!");
    } catch (error) {
      toast.error("Failed to download project");
      console.error("Download error:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 animate-fade-in-up">
      {/* Success Header */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-success/20 animate-scale-in">
          <CheckCircle2 className="w-12 h-12 text-success" />
        </div>
        <div>
          <h2 className="text-3xl font-bold mb-2">Your Website is Ready! ✨</h2>
          <p className="text-muted-foreground">
            Generated {files.length} file{files.length !== 1 ? "s" : ""}
            {buildTime && ` in ${buildTime} seconds`}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button
            variant="hero"
            size="lg"
            onClick={handleDownload}
            disabled={isDownloading}
          >
            {isDownloading ? (
              <>
                <Loader2 className="animate-spin" />
                Downloading...
              </>
            ) : (
              <>
                <Download />
                Download Project
              </>
            )}
          </Button>
          <Button variant="outline" size="lg" onClick={onReset}>
            <RefreshCw />
            Build Another
          </Button>
        </div>
      </div>

      {/* File Explorer and Code Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Tree */}
        <div className="lg:col-span-1">
          <FileTree
            files={files}
            selectedFile={selectedFile}
            onFileSelect={setSelectedFile}
          />
        </div>

        {/* Code Viewer */}
        <div className="lg:col-span-2">
          {isLoadingFile ? (
            <div className="glass-card rounded-lg p-12 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : selectedFile ? (
            <CodeViewer fileName={selectedFile} content={fileContent} />
          ) : (
            <div className="glass-card rounded-lg p-12 text-center text-muted-foreground">
              Select a file to view its contents
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
