export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: Date;
}

// Mock conversation data
export const mockConversations: Conversation[] = [
  {
    id: "conv-1",
    title: "Understanding React Hooks",
    messages: [
      {
        id: "msg-1",
        role: "user",
        content: "Can you explain React hooks to me?",
        timestamp: new Date("2023-03-01T12:30:00"),
      },
      {
        id: "msg-2",
        role: "assistant",
        content:
          "React Hooks are functions that let you use state and other React features in functional components...",
        timestamp: new Date("2023-03-01T12:31:00"),
      },
    ],
    updatedAt: new Date("2023-03-01T12:31:00"),
  },
  {
    id: "conv-2",
    title: "CSS Grid Layout Help",
    messages: [
      {
        id: "msg-3",
        role: "user",
        content: "What's the best way to create a responsive grid layout?",
        timestamp: new Date("2023-03-02T14:20:00"),
      },
      {
        id: "msg-4",
        role: "assistant",
        content:
          "CSS Grid is a powerful tool for creating responsive layouts...",
        timestamp: new Date("2023-03-02T14:22:00"),
      },
    ],
    updatedAt: new Date("2023-03-02T14:22:00"),
  },
];
