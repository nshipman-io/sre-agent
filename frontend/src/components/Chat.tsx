import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { chatAPI } from '../services/api';
import type { ChatMessage as ChatMessageType } from '../types/api';

interface ChatProps {
  namespace: string;
}

export const Chat: React.FC<ChatProps> = ({ namespace }) => {
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      role: 'assistant',
      content: `Hello! I'm your SRE AI Assistant. I can help you with:

- **Investigating pod issues** - "Why is my pod crashing?"
- **Checking cluster health** - "Show me pods in ${namespace}"
- **Analyzing deployments** - "List all deployments"
- **Reviewing events** - "Show recent events"
- **Searching runbooks** - "How do I fix CrashLoopBackOff?"

What would you like to know about your cluster?`,
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      // Build conversation history
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      return chatAPI.sendMessage({
        message,
        namespace,
        conversation_history: history,
      });
    },
    onMutate: (message) => {
      // Optimistically add user message
      setMessages((prev) => [...prev, { role: 'user', content: message }]);
    },
    onSuccess: (data) => {
      // Add assistant response
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
        },
      ]);
    },
    onError: (error) => {
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        },
      ]);
    },
  });

  const handleSendMessage = (message: string) => {
    chatMutation.mutate(message);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <h2 className="text-lg font-semibold">Chat</h2>
        <p className="text-sm text-gray-600">
          Asking about namespace: <span className="font-medium">{namespace}</span>
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
          {chatMutation.isPending && (
            <div className="flex gap-3 p-4 bg-white">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-green-500">
                <Loader2 className="w-5 h-5 text-white animate-spin" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-sm mb-1">SRE Agent</div>
                <div className="text-gray-600 text-sm">Thinking...</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white">
        <div className="max-w-4xl mx-auto">
          <ChatInput onSend={handleSendMessage} disabled={chatMutation.isPending} />
        </div>
      </div>
    </div>
  );
};
