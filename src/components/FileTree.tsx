import { useState } from "react";
import { File, Folder, ChevronRight, ChevronDown } from "lucide-react";

interface FileTreeProps {
  files: string[];
  selectedFile: string | null;
  onFileSelect: (file: string) => void;
}

interface TreeNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children: TreeNode[];
}

function buildTree(files: string[]): TreeNode {
  const root: TreeNode = {
    name: "project",
    path: "",
    type: "folder",
    children: [],
  };

  files.forEach((filePath) => {
    const parts = filePath.split("/").filter(Boolean);
    let currentNode = root;

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      const path = parts.slice(0, index + 1).join("/");

      let childNode = currentNode.children.find((child) => child.name === part);

      if (!childNode) {
        childNode = {
          name: part,
          path,
          type: isFile ? "file" : "folder",
          children: [],
        };
        currentNode.children.push(childNode);
      }

      currentNode = childNode;
    });
  });

  return root;
}

function TreeNodeComponent({
  node,
  level = 0,
  selectedFile,
  onFileSelect,
}: {
  node: TreeNode;
  level?: number;
  selectedFile: string | null;
  onFileSelect: (file: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(level < 2);

  const handleClick = () => {
    if (node.type === "folder") {
      setIsOpen(!isOpen);
    } else {
      onFileSelect(node.path);
    }
  };

  const isSelected = selectedFile === node.path;

  return (
    <div>
      <button
        onClick={handleClick}
        className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-all duration-200 hover:bg-accent/50 ${
          isSelected ? "bg-primary/20 text-primary" : "text-foreground"
        }`}
        style={{ paddingLeft: `${level * 1 + 0.75}rem` }}
      >
        {node.type === "folder" ? (
          <>
            {isOpen ? (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            )}
            <Folder className="w-4 h-4 text-primary" />
          </>
        ) : (
          <>
            <span className="w-4" />
            <File className="w-4 h-4 text-secondary" />
          </>
        )}
        <span className="truncate">{node.name}</span>
      </button>

      {node.type === "folder" && isOpen && (
        <div className="animate-accordion-down">
          {node.children.map((child) => (
            <TreeNodeComponent
              key={child.path}
              node={child}
              level={level + 1}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FileTree({ files, selectedFile, onFileSelect }: FileTreeProps) {
  const tree = buildTree(files);

  return (
    <div className="glass-card p-4 rounded-lg space-y-2 max-h-[500px] overflow-y-auto">
      <h3 className="text-sm font-semibold text-muted-foreground px-3 mb-2">FILES</h3>
      <TreeNodeComponent
        node={tree}
        selectedFile={selectedFile}
        onFileSelect={onFileSelect}
      />
    </div>
  );
}
