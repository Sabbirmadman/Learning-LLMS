/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";
import { Message } from "@/types/chat";
import { Loader2, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import { preprocessLatex, getMarkdownComponents } from "./markdownHandlers";

interface ChatMessageItemProps {
  message: Message;
}

// Format the AI response to remove question and prefixes
function formatAIResponse(content: string, role: string): string {
  if (role === "assistant") {
    // Remove __end__ suffix
    content = content.replace(/__end__$/g, "");

    // Check for the ANSWER: prefix pattern
    const answerPrefixPattern = /^ANSWER:\s*([\s\S]*)$/;
    const answerMatch = content.match(answerPrefixPattern);

    if (answerMatch) {
      return answerMatch[1].trim();
    }

    // Pattern 1: Remove question that ends with ? followed by heading
    const questionHeadingPattern = /^(.*?\?)(?:\s*)(#.*)/;
    const headingMatch = content.match(questionHeadingPattern);

    if (headingMatch) {
      return headingMatch[2].trim();
    }

    // Pattern 2: When the heading is part of the question or no clear separation
    const directHeadingPattern = /^([^#]*?)(#.*)$/;
    const directMatch = content.match(directHeadingPattern);

    if (directMatch) {
      return directMatch[2].trim();
    }

    // Check for __end__ prefixes (sometimes these might be in the middle)
    if (content.includes("__end__")) {
      return content.split("__end__")[1].trim();
    }
  }

  return content;
}

const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  // Format the content to remove question and prefixes
  const formattedContent = formatAIResponse(message.content, message.role);

  const { processedMarkdown, blockMathExpressions, blockMathPlaceholder } =
    message.role === "assistant"
      ? preprocessLatex(formattedContent)
      : {
          processedMarkdown: formattedContent,
          blockMathExpressions: [],
          blockMathPlaceholder: "",
        };

  return (
    <div
      className={`flex w-full ${
        message.role === "user" ? "justify-end" : "justify-start"
      }`}
    >
      {message.role === "assistant" && (
        <div className="flex-shrink-0 mr-2 mt-4 hidden sm:block">
          <Bot className="h-6 w-6 text-primary" />
        </div>
      )}

      <div
        className={`rounded-lg p-3 sm:p-4 mt-4 overflow-hidden max-w-full ${
          message.role === "assistant"
            ? "border border-secondary w-full sm:w-auto"
            : "border border-primary"
        }`}
      >
        {message.role === "assistant" ? (
          <div className="markdown-content prose prose-invert max-w-none break-words w-full">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={getMarkdownComponents(
                blockMathExpressions,
                blockMathPlaceholder
              )}
            >
              {processedMarkdown}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="whitespace-pre-wrap break-words">{formattedContent}</p>
        )}
        <div className="flex items-center justify-between text-xs mt-2 opacity-70">
          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          {message?.isStreaming && (
            <Loader2 className="animate-spin h-3 w-3 ml-2" />
          )}
        </div>
      </div>

      {message.role === "user" && (
        <div className="flex-shrink-0 ml-2 mt-4 hidden sm:block">
          <User className="h-6 w-6 text-primary" />
        </div>
      )}
    </div>
  );
};

export default ChatMessageItem;