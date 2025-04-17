import React from "react";
import { Plus, MessageSquare, PanelLeftClose, PanelRightClose, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Conversation } from "@/types/chat";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  onSelectConversation: (conversation: Conversation) => void;
  onNewConversation: () => void;
  onDeleteConversation: (conversation: Conversation) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  isMobile: boolean;
}

// Helper function to format dates
const formatDate = (date: Date): string => {
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  
  // Check if date is today
  if (date.toDateString() === today.toDateString()) {
    return "Today";
  }
  
  // Check if date is yesterday
  if (date.toDateString() === yesterday.toDateString()) {
    return "Yesterday";
  }
  
  // Return formatted date
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
  });
};

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  activeConversation,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  collapsed,
  onToggleCollapse,
  isMobile
}) => {
  if (collapsed) {
    return (
      <Button 
        variant="ghost" 
        size="sm" 
        className="flex justify-center items-center py-1 border-t"
        onClick={onToggleCollapse}
      >
        <PanelRightClose className="h-4 w-4" />
      </Button>
    );
  }
  
  // Sort conversations by updatedAt (newest first)
  const sortedConversations = [...conversations].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );
  
  // Group conversations by date
  const groupedConversations: Record<string, Conversation[]> = {};
  
  sortedConversations.forEach(conversation => {
    const dateKey = formatDate(new Date(conversation.updatedAt));
    if (!groupedConversations[dateKey]) {
      groupedConversations[dateKey] = [];
    }
    groupedConversations[dateKey].push(conversation);
  });
  
  // Get group dates in order
  const dateGroups = Object.keys(groupedConversations);

  return (
    <>
      <div className="p-3 border-b">
        <Button
          className="w-full flex items-center gap-2"
          onClick={onNewConversation}
        >
          <Plus size={16} /> New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1 p-2">
        {sortedConversations.length === 0 ? (
          <div className="text-center p-4 text-muted-foreground">
            No conversations yet
          </div>
        ) : (
          <div className="space-y-4 pr-2">
            {dateGroups.map((dateGroup) => (
              <div key={dateGroup} className="space-y-2">
                <h3 className="text-sm text-muted-foreground font-medium px-2 pt-1">
                  {dateGroup}
                </h3>
                {groupedConversations[dateGroup].map((conversation) => (
                  <Card
                    key={conversation.id}
                    className={`p-3 cursor-pointer hover:bg-accent transition-colors ${
                      activeConversation?.id === conversation.id
                        ? "bg-accent"
                        : ""
                    }`}
                  >
                    <div 
                      className="flex gap-2 items-start"
                      onClick={() => onSelectConversation(conversation)}
                    >
                      <MessageSquare className="w-4 h-4 mt-1 flex-shrink-0" />
                      <div className="overflow-hidden space-y-1 flex-1">
                        <p className="font-medium truncate">
                          {conversation.title}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {new Date(conversation.updatedAt).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit"
                          })}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 opacity-50 hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conversation);
                        }}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {!isMobile && (
        <Button 
          variant="ghost" 
          size="sm" 
          className="flex justify-center items-center py-1 border-t"
          onClick={onToggleCollapse}
        >
          <PanelLeftClose className="h-4 w-4" />
        </Button>
      )}
    </>
  );
};

export default ConversationList;