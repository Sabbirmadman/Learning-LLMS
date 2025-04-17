import React from "react";
import { Eye, Trash2, Globe, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useNavigate } from "react-router-dom";
import { ScrapeJob } from "@/types/files";
import { ScrapeStatus } from "@/lib/redux/api/scrapeApi";

interface ScrapeJobCardProps {
  url: ScrapeJob;
  isSelected: boolean;
  toggleSelection: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
}

export const ScrapeJobCard: React.FC<ScrapeJobCardProps> = ({
  url,
  isSelected,
  toggleSelection,
  onDelete,
}) => {
  const navigate = useNavigate();

  const getStatusColor = (status: ScrapeStatus) => {
    switch (status) {
      case "COMPLETED":
        return "bg-green-100 text-green-800";
      case "FAILED":
        return "bg-red-100 text-red-800";
      case "IN_PROGRESS":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md relative ${
        isSelected ? "border-primary bg-primary/5" : ""
      }`}
      onClick={() => toggleSelection(url.id)}
    >
      {isSelected && (
        <div className="absolute top-3 right-3 bg-primary text-primary-foreground rounded-full p-1">
          <Check className="w-4 h-4" />
        </div>
      )}
      <div className="p-4 flex flex-col h-full">
        <div className="flex items-center gap-2 mb-3">
          <Globe className="w-5 h-5 text-blue-500" />
          <div className="font-medium truncate" title={url.url}>
            {url.url}
          </div>
        </div>
        <Badge
          variant="outline"
          className={`${getStatusColor(url.status)} mb-4`}
        >
          {url.status}
        </Badge>
        <div className="mt-auto flex justify-between">
          <div className="text-xs text-gray-500">
            {new Date(url.created_at).toLocaleDateString()}
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
                      navigate(`/content/scrape/${url.id}`);
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
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(url.id);
                    }}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Delete Content</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </Card>
  );
};
