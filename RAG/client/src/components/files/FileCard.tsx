import React from "react";
import { Eye, Download, Trash2, FileText, File, FileImage, FileCode } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Check } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useNavigate } from "react-router-dom";
import { FileItem } from "@/types/files";

interface FileCardProps {
  file: FileItem;
  isSelected: boolean;
  toggleSelection: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
}

export const FileCard: React.FC<FileCardProps> = ({
  file,
  isSelected,
  toggleSelection,
  onDelete,
}) => {
  const navigate = useNavigate();

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith("image/")) {
      return <FileImage className="w-8 h-8 text-blue-500" />;
    } else if (contentType === "application/pdf") {
      return <FileText className="w-8 h-8 text-red-500" />;
    } else if (
      contentType.includes("javascript") ||
      contentType.includes("json") ||
      contentType.includes("html") ||
      contentType.includes("css")
    ) {
      return <FileCode className="w-8 h-8 text-yellow-500" />;
    } else if (contentType.includes("text")) {
      return <FileText className="w-8 h-8 text-gray-500" />;
    } else {
      return <File className="w-8 h-8 text-gray-400" />;
    }
  };

  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md relative ${
        isSelected ? "border-primary bg-primary/5" : ""
      }`}
      onClick={() => toggleSelection(file.id)}
    >
      {isSelected && (
        <div className="absolute top-3 right-3 bg-primary text-primary-foreground rounded-full p-1">
          <Check className="w-4 h-4" />
        </div>
      )}
      <div className="p-4 flex flex-col h-full">
        <div className="flex items-center gap-3 mb-3">
          {getFileIcon(file.content_type)}
          <div className="font-medium truncate" title={file.filename}>
            {file.filename}
          </div>
        </div>
        <div className="text-sm text-gray-500 mb-1">{file.content_type}</div>
        <div className="text-sm text-gray-500 mb-4">
          {(file.file_size / 1024).toFixed(1)} KB
        </div>
        <div className="mt-auto flex justify-between">
          <div className="text-xs text-gray-500">
            {new Date(file.upload_date).toLocaleDateString()}
          </div>
          <div className="flex space-x-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/content/file/${file.id}`);
                    }}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Preview content</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => e.stopPropagation()}
                    asChild
                  >
                    <a
                      href={file.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center"
                    >
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Download file</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(file.id);
                    }}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Delete file</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </Card>
  );
};
