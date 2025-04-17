import React from "react";
import { Menu, X, PanelRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface MobileHeaderProps {
  showConversations: boolean;
  showFilesPanel: boolean;
  onToggleConversations: () => void;
  onToggleFilesPanel: () => void;
}

const MobileHeader: React.FC<MobileHeaderProps> = ({
  showConversations,
  showFilesPanel,
  onToggleConversations,
  onToggleFilesPanel
}) => {
  return (
    <div className="flex items-center justify-between p-4 border-b">
      <Button
        variant="ghost"
        size="icon"
        onClick={onToggleConversations}
      >
        {showConversations ? (
          <X className="h-5 w-5" />
        ) : (
          <Menu className="h-5 w-5" />
        )}
      </Button>
      <h1 className="font-semibold text-lg">Chat</h1>
      <Button
        variant="ghost"
        size="icon"
        onClick={onToggleFilesPanel}
      >
        {showFilesPanel ? (
          <X className="h-5 w-5" />
        ) : (
          <PanelRight className="h-5 w-5" />
        )}
      </Button>
    </div>
  );
};

export default MobileHeader;
