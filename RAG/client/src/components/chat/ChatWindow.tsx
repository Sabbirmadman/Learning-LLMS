import React, { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Conversation } from "@/types/chat";
import ChatMessageItem from "./ChatMessageItem";

interface ChatWindowProps {
  activeConversation: Conversation | null;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ activeConversation }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (messagesEndRef.current && activeConversation?.messages?.length) {
      // Use requestAnimationFrame for smoother scrolling
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ 
          behavior: "smooth",
          block: "end" 
        });
      });
    }
  }, [activeConversation?.messages]);
  
  if (!activeConversation) {
    return (
      <ScrollArea className="flex-1 p-4">
        <div className="flex h-full items-center justify-center">
          <p>Select a conversation or start a new one</p>
        </div>
      </ScrollArea>
    );
  }

  if (activeConversation.messages.length === 0) {
    return (
      <ScrollArea className="flex-1 p-4">
        <div className="flex h-full items-center justify-center text-center p-4">
          <div>
            <h2 className="text-xl font-semibold mb-2">Start a new conversation</h2>
            <p className="text-muted-foreground">
              Send a message to begin chatting with the AI assistant
            </p>
          </div>
        </div>
      </ScrollArea>
    );
  }

  return (
    <ScrollArea className="flex-1  px-4 ">
      <div className="max-w-4xl mx-auto space-y-4 pb-4 ">
        {activeConversation.messages.map((message) => (
          <ChatMessageItem key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  );
};

export default ChatWindow;