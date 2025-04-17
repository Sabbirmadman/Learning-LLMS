import React, { useState, useEffect, useRef } from "react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Message } from "@/types/chat";
import MobileHeader from "@/components/chat/MobileHeader";
import ConversationList from "@/components/chat/ConversationList";
import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import FilesPanel from "@/components/chat/FilesPanel";
import useChatApi from "@/hooks/useChatApi";
import { Chat  } from "@/lib/redux/api/chatApis";
import { Loader2 } from "lucide-react";
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle 
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { debounce } from "@/components/utils/chatUtils";

// Define the interface for conversation objects to fix type issues
interface Conversation {
  id: string;
  title: string;
  updatedAt: Date;
  messages: Message[];
}

// Helper function to convert API chat to frontend Conversation format
const mapChatToConversation = (chat: Chat): Conversation => {
  return {
    id: chat.id.toString(),
    title: chat.title,
    updatedAt: new Date(chat.updated_at),
    messages: chat.messages.map(msg => ({
      id: msg.id.toString(),
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.timestamp)
    }))
  };
};

const ChatPage: React.FC = () => {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const windowRef = useRef<HTMLDivElement>(null);

  // State for panel visibility
  const [showConversations, setShowConversations] = useState(!isMobile);
  const [showFilesPanel, setShowFilesPanel] = useState(!isMobile);
  
  // State for panel collapse (separate from visibility)
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

  // Alert dialog for delete confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<number | null>(null);

  // Panel widths (percentages)
  const [leftPanelWidth, setLeftPanelWidth] = useState(20);
  const [rightPanelWidth, setRightPanelWidth] = useState(25);
  
  // Width of collapsed panels (px)
  const collapsedWidth = 50;

  // Use chat API hook
  const {
    chats,
    currentChat,
    currentChatId,
    isChatsLoading,
    isChatLoading,
    isStreaming,
    streamingContent,
    createChat,
    deleteChat,
    selectChat,
    streamMessage,
    stopStreaming,
    refetchChat
  } = useChatApi();

  // State to store converted conversations for UI
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);

  useEffect(() => {
    if (currentChat) {
      const conversation = mapChatToConversation(currentChat);
      setActiveConversation(conversation);
    } else {
      setActiveConversation(null);
    }
  }, [currentChat]);

  // Add streaming message to UI when streaming
  useEffect(() => {
    if (isStreaming && streamingContent && currentChatId && activeConversation) {
      // Create a temporary streaming message for display
      const tempStreamingMessage: Message = {
        id: 'streaming-message',
        role: 'assistant',
        content: streamingContent,
        timestamp: new Date(),
        isStreaming: true
      };
      
      // Filter out any previous streaming message
      const filteredMessages = activeConversation.messages.filter(
        (msg: Message) => msg.id !== 'streaming-message'
      );
      
      // Set the updated conversation with streaming content
      setActiveConversation({
        ...activeConversation,
        messages: [...filteredMessages, tempStreamingMessage]
      });
    }
  }, [isStreaming, streamingContent, currentChatId, activeConversation]);

  // Scroll to bottom when messages change
  const debouncedScroll = useRef(
    debounce(() => {
      if (windowRef.current) {
        const scrollElement = windowRef.current.querySelector('.scroll-area-viewport');
        if (scrollElement) {
          scrollElement.scrollTop = scrollElement.scrollHeight;
        }
      }
    }, 150)
  ).current;
  
  // Use the debounced function in your effect
  useEffect(() => {
    if (activeConversation?.messages) {
      requestAnimationFrame(() => {
        debouncedScroll();
      });
    }
  }, [activeConversation?.messages, debouncedScroll]);


  // Adjust panel visibility based on screen size
  useEffect(() => {
    if (isMobile) {
      setShowConversations(false);
      setShowFilesPanel(false);
      setLeftPanelCollapsed(false);
      setRightPanelCollapsed(false);
    } else {
      setShowConversations(true);
      setShowFilesPanel(true);
    }
  }, [isMobile]);

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;
    
    if (!currentChatId) {
      // If no chat exists, create one first
      try {
        const newChat = await createChat("New Conversation");
        
        // Add a slight delay to ensure chat is created before sending message
        setTimeout(() => {
          handleStreamMessage(newChat.id, messageText);
        }, 100);
      } catch (error) {
        toast.error("Failed to create new chat");
      }
      return;
    }

    handleStreamMessage(currentChatId, messageText);
  };

  const handleStreamMessage = (chatId: number, message: string) => {
    // Add user message to UI immediately
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    
    if (activeConversation) {
      setActiveConversation({
        ...activeConversation,
        messages: [...activeConversation.messages, userMessage]
      });
    }

    // Stream the response
    streamMessage({
      chatId,
      message,
      onError: (error) => {
        toast.error(error);
      },
      onComplete: () => {
        refetchChat();      }
    });
  };

  const startNewConversation = async () => {
    try {
      await createChat("New Conversation");
      if (isMobile) {
        setShowConversations(false);
      }
    } catch (error) {
      toast.error("Failed to create new chat");
    }
  };

  const handleDeleteChat = (chatId: number) => {
    setChatToDelete(chatId);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteChat = async () => {
    if (chatToDelete !== null) {
      try {
        await deleteChat(chatToDelete);
        setDeleteDialogOpen(false);
        setChatToDelete(null);
        toast.success("Chat deleted successfully");
      } catch (error) {
        toast.error("Failed to delete chat");
      }
    }
  };

  const handleSelectConversation = (conversation: Conversation) => {
    selectChat(parseInt(conversation.id));
    if (isMobile) setShowConversations(false);
  };

  const handleResize = (e: React.MouseEvent, direction: "left" | "right") => {
    if (isMobile) return;

    const startX = e.clientX;
    const startLeftWidth = leftPanelWidth;
    const startRightWidth = rightPanelWidth;
    const containerWidth =
      document.getElementById("chat-container")?.offsetWidth || 100;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (direction === "left") {
        const newLeftWidth =
          startLeftWidth +
          ((moveEvent.clientX - startX) / containerWidth) * 100;
        // Ensure width stays within reasonable bounds (5% to 40%)
        if (newLeftWidth >= 5 && newLeftWidth <= 40) {
          setLeftPanelWidth(newLeftWidth);
        }
      } else {
        const newRightWidth =
          startRightWidth -
          ((moveEvent.clientX - startX) / containerWidth) * 100;
        // Ensure width stays within reasonable bounds (5% to 40%)
        if (newRightWidth >= 5 && newRightWidth <= 40) {
          setRightPanelWidth(newRightWidth);
        }
      }
    };

    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  // Convert API chats to UI conversation format
  const conversations: Conversation[] = chats ? chats.map(chat => ({
    id: chat.id.toString(),
    title: chat.title,
    updatedAt: new Date(chat.updated_at),
    messages: [] // We don't need full messages list in the sidebar
  })) : [];

  return (
    <div className="flex flex-col h-[calc(100vh-65px)]">
      {/* Mobile Header */}
      {isMobile && (
        <MobileHeader
          showConversations={showConversations}
          showFilesPanel={showFilesPanel}
          onToggleConversations={() => setShowConversations(!showConversations)}
          onToggleFilesPanel={() => setShowFilesPanel(!showFilesPanel)}
        />
      )}

      {/* Loading overlay */}
      {isChatsLoading && (
        <div className="absolute inset-0 bg-background/50 flex items-center justify-center z-50">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      )}

      {/* Main Container */}
      <div id="chat-container" className="flex flex-1 overflow-hidden relative">
        
        {/* Conversations Panel - Left */}
        {showConversations && (
          <div
            className={`bg-card h-full flex flex-col border-r transition-all duration-300 ${
              isMobile ? "absolute z-10 w-4/5 left-0 top-0 h-full" : ""
            } ${!isMobile && leftPanelCollapsed ? "shadow-md" : ""}`}
            style={isMobile 
              ? {} 
              : leftPanelCollapsed 
                ? { width: `${collapsedWidth}px` } 
                : { width: `${leftPanelWidth}%` }
            }
          >
            <ConversationList
              conversations={conversations}
              activeConversation={activeConversation}
              onSelectConversation={handleSelectConversation}
              onNewConversation={startNewConversation}
              onDeleteConversation={(conv) => handleDeleteChat(parseInt(conv.id))}
              collapsed={leftPanelCollapsed}
              onToggleCollapse={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
              isMobile={isMobile}
            />
          </div>
        )}

        {!isMobile && showConversations && !leftPanelCollapsed && (
          <div
            className="w-1 hover:bg-primary/50 cursor-col-resize"
            onMouseDown={(e) => handleResize(e, "left")}
          ></div>
        )}

        {/* Chat Area - Middle part that stretches */}
        <div 
          ref={windowRef}
          className={`flex-1 flex flex-col ${
            isMobile && (showConversations || showFilesPanel) ? "hidden" : ""
          }`}
     
        >
          {isChatLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <ChatWindow activeConversation={activeConversation} />
          )}
          <ChatInput 
            onSendMessage={handleSendMessage} 
            disabled={isStreaming}
            isStreaming={isStreaming}
            onStopStreaming={stopStreaming}
          />
        </div>
        
        {!isMobile && showFilesPanel && !rightPanelCollapsed && (
          <div 
            className="w-1 hover:bg-primary/50 cursor-col-resize" 
            onMouseDown={(e) => handleResize(e, 'right')}
          ></div>
        )}

        {/* Files Panel - Right */}
        {showFilesPanel && (
          <div
            className={`bg-card h-full flex flex-col border-l transition-all duration-300 ${
              isMobile ? "absolute z-10 w-full right-0 top-0 h-full" : ""
            } ${!isMobile && rightPanelCollapsed ? "shadow-md" : ""}`}
            style={isMobile 
              ? {} 
              : rightPanelCollapsed 
                ? { width: `${collapsedWidth}px` } 
                : { width: `${rightPanelWidth}%` }
            }
          >
            <FilesPanel 
              onClose={() => setShowFilesPanel(false)}
              collapsed={rightPanelCollapsed}
              onToggleCollapse={() => setRightPanelCollapsed(!rightPanelCollapsed)}
              isMobile={isMobile}
            />
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chat</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this chat? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteChat}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default ChatPage;