import React, { useState, useRef, useEffect } from "react";
import { Send, PaperclipIcon, StopCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onStopStreaming?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onStopStreaming,
  disabled = false,
  isStreaming = false,
}) => {
  const [messageInput, setMessageInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-resize the textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = "60px";
    
    // Calculate the new height (with a maximum of 200px)
    const maxHeight = 200;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
    
    // Maintain scrolling functionality but with hidden scrollbar
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "scroll" : "hidden";
  }, [messageInput]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || disabled) return;

    onSendMessage(messageInput);
    setMessageInput("");
  };

  return (
    <div className="px-4 pb-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto ">
        <Card className="shadow-sm border-none overflow-hidden ">
          <Textarea
            ref={textareaRef}
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            placeholder="Type your message here..."
            disabled={disabled}
            className="min-h-[60px] resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0 rounded-none bg-muted/30 scrollbar-hide"
            style={{
              scrollbarWidth: 'none', /* Firefox */
              msOverflowStyle: 'none', /* IE and Edge */
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div className="flex items-center justify-between px-3 py-2 bg-muted/30">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="rounded-full h-8 w-8"
              title="Attach files"
            >
              <PaperclipIcon className="h-4 w-4" />
            </Button>

            {isStreaming ? (
              <Button
                type="button"
                variant="ghost"
                onClick={onStopStreaming}
                className="rounded-full px-2"
              >
                <StopCircle className="h-4 w-4 " />
              </Button>
            ) : (
              <Button
                type="submit"
                variant="ghost"
                size="icon"
                className="rounded-full h-8 w-8"
                title="Send"
                disabled={!messageInput.trim() || disabled}
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>
        </Card>
      </form>
    </div>
  );
};

export default ChatInput;
