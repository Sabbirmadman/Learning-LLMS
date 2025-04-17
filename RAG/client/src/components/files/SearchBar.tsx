import React from "react";
import { Search, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface SearchBarProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  hasSelections: boolean;
  onStartChat: () => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  searchQuery,
  onSearchChange,
  hasSelections,
  onStartChat,
}) => {
  return (
    <div className="flex flex-col sm:flex-row justify-between mb-4 gap-4">
      <div className="relative flex-1">
        <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <Input
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search files & URLs..."
          className="pl-10"
        />
      </div>

      {hasSelections && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="default"
                className="flex items-center gap-2"
                onClick={onStartChat}
              >
                <MessageSquare className="w-4 h-4" />
                Start Chat
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Start new chat with selected files</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
};
