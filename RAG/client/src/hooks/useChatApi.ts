import { useState, useCallback, useEffect } from 'react';
import { 
  useGetChatsQuery,
  useGetChatQuery,
  useCreateChatMutation, 
  useDeleteChatMutation
//   useSendMessageMutation
} from '@/lib/redux/api/chatApis';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';

interface UseChatApiOptions {
  initialChatId?: number;
}

interface StreamMessageOptions {
  chatId: number;
  message: string;
  scrapeIds?: number[];
  onToken?: (token: string) => void;
  onError?: (error: string) => void;
  onComplete?: (messageId: number) => void;
}

const API_BASE_URL = import.meta.env.VITE_BASE_URL || '';


export function useChatApi(options: UseChatApiOptions = {}) {
  const [currentChatId, setCurrentChatId] = useState<number | undefined>(options.initialChatId);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const selectedFileIds = useSelector((state: RootState) => state.selection.selectedFileIds);
  const selectedUrlIds = useSelector((state: RootState) => state.selection.selectedUrlIds);

  // RTK Query hooks
  const { data: chats, isLoading: isChatsLoading, refetch: refetchChats } = useGetChatsQuery();
  const { data: currentChat, isLoading: isChatLoading , refetch: refetchChat } = useGetChatQuery(currentChatId ?? 0, {
    skip: !currentChatId,
  });
  const [createChat] = useCreateChatMutation();
  const [deleteChat] = useDeleteChatMutation();
//   const [sendMessage, { isLoading: isSending }] = useSendMessageMutation();

  // Clean up any ongoing streams when component unmounts
  useEffect(() => {
    return () => {
      if (abortController) {
        abortController.abort();
      }
    };
  }, [abortController]);

  // Select a chat
  const selectChat = useCallback((chatId: number) => {
    setCurrentChatId(chatId);
  }, []);

  // Create a new chat
  const handleCreateChat = useCallback(async (title: string) => {
    try {
      const newChat = await createChat({ title }).unwrap();
      setCurrentChatId(newChat.id);
      return newChat;
    } catch (error) {
      console.error('Failed to create chat:', error);
      throw error;
    }
  }, [createChat]);

  // Delete a chat
  const handleDeleteChat = useCallback(async (chatId: number) => {
    try {
      await deleteChat(chatId).unwrap();
      if (currentChatId === chatId) {
        setCurrentChatId(undefined);
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      throw error;
    }
  }, [deleteChat, currentChatId]);

  // Send a message with streaming response
  const streamMessage = useCallback(
    async ({ chatId, message, scrapeIds, onToken, onError, onComplete }: StreamMessageOptions) => {
      // First, abort any existing stream
      if (abortController) {
        abortController.abort();
      }

      // Create a new abort controller for this request
      const controller = new AbortController();
      setAbortController(controller);
      setIsStreaming(true);
      setStreamingContent('');

      const allScrapeIds = [
        ...(scrapeIds || []),
        ...selectedFileIds.map(file => file.id),
        ...selectedUrlIds.map(url => url.id)
      ];

      
      console.log(selectedUrlIds, selectedFileIds, 'Sending message with scrape IDs:', allScrapeIds);
      
      try {
        const response = await fetch(`${API_BASE_URL}/api-chat/chats/${chatId}/messages/stream/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}` // Adjust to your auth implementation
            },
            body: JSON.stringify({
              message,
              scrape_ids: allScrapeIds.length > 0 ? allScrapeIds : undefined
            }),
            signal: controller.signal
          });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Create a reader for the response
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let partialChunk = '';

        // Process the stream
        let done = false;
        while (!done) {
          const { value, done: readDone } = await reader.read();
          done = readDone;
          if (done) break;

          // Decode and add any partial chunk from previous iteration
          const chunk = partialChunk + decoder.decode(value, { stream: true });
          
          // Process line by line (SSE format has data: prefix)
          const lines = chunk.split('\n\n');
          
          // Last line might be incomplete, save it for next iteration
          partialChunk = lines.pop() || '';
          
          // Process complete lines
          for (const line of lines) {
            if (line.trim() === '') continue;
            
            // Extract the data part (removing "data: " prefix)
            const dataMatch = line.match(/^data: (.+)$/);
            if (!dataMatch) continue;
            
            try {
              const eventData = JSON.parse(dataMatch[1]);
              
              // Handle different event types
              if (eventData.token) {
                // Handle token
                setStreamingContent(prev => prev + eventData.token);
                if (onToken) onToken(eventData.token);
              } else if (eventData.error) {
                // Handle error
                if (onError) onError(eventData.error);
              } else if (eventData.done && eventData.messageId) {
                // Handle completion
                if (onComplete) onComplete(eventData.messageId);
              }
            } catch (err) {
              console.error('Error parsing SSE data:', err);
            }
          }
        }
      } catch (error) {
        // Only report errors if not aborted
        if (controller.signal.aborted) {
          console.log('Stream was aborted');
        } else {
          console.error('Error streaming message:', error);
          if (onError) onError((error as Error).message);
        }
      } finally {
        setIsStreaming(false);
        setAbortController(null);
      }
    },
    [abortController]
  );

  // Stop any ongoing streaming
  const stopStreaming = useCallback(() => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsStreaming(false);
    }
  }, [abortController]);

  return {
    // State
    currentChatId,
    isStreaming,
    streamingContent,
    
    // Chat data
    chats,
    currentChat,
    isChatsLoading,
    isChatLoading,
    // isSending,
    
    // Actions
    selectChat,
    createChat: handleCreateChat,
    deleteChat: handleDeleteChat,
    // sendMessage: handleSendMessage,
    streamMessage,
    stopStreaming,
    refetchChats,
    refetchChat
  };
}

export default useChatApi;