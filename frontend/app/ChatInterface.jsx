"use client"

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import QueryVisualization from './QueryVisualization';

const ChatInput = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query);
      setQuery('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  return (
    <form onSubmit={handleSubmit} className="relative flex items-end space-x-2">
      <textarea
        ref={textareaRef}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question..."
        className="flex-1 min-h-[44px] max-h-[200px] p-2 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={1}
      />
      <Button 
        type="submit" 
        disabled={isLoading || !query.trim()}
        className="h-11 px-4"
      >
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </Button>
    </form>
  );
};

const ChatMessage = ({ message, isError }) => {
  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{message}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <p className="text-sm text-gray-700">{message}</p>
    </div>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contextId, setContextId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleQuery = async (queryText) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/query/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: queryText,
          tenant_id: 'tenant1',
          metadata: {},
          ...(contextId && { context_id: contextId }),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch response');
      }

      const data = await response.json();
      
      // Store context_id for future requests
      if (data.context_id) {
        setContextId(data.context_id);
      }

      // Add user message and response to chat
      setMessages(prev => [
        ...prev,
        { type: 'user', content: queryText },
        { 
          type: 'assistant',
          content: data.sql_query,
          results: data.results,
          visualization: data.visualization
        }
      ]);

    } catch (err) {
      setError(err.message);
      setMessages(prev => [
        ...prev,
        { type: 'user', content: queryText },
        { type: 'error', content: err.message }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-gray-50">
      <div className="flex-none p-4 border-b bg-white">
        <h1 className="text-xl font-semibold">AI Query Assistant</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`${
              message.type === 'user' ? 'ml-auto max-w-[80%]' : 'mr-auto max-w-[80%]'
            }`}
          >
            {message.type === 'user' ? (
              <div className="bg-blue-100 p-3 rounded-lg">
                <p className="text-sm">{message.content}</p>
              </div>
            ) : message.type === 'error' ? (
              <ChatMessage message={message.content} isError />
            ) : (
              <div className="space-y-4">
                <div className="bg-white p-3 rounded-lg shadow">
                  <p className="text-xs text-gray-500 mb-2">Generated SQL:</p>
                  <pre className="text-sm bg-gray-50 p-2 rounded">
                    {message.content}
                  </pre>
                </div>
                {message.results && message.visualization && (
                  <QueryVisualization
                    data={message.results}
                    visualization={message.visualization}
                    title="Query Results"
                  />
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex-none p-4 bg-white border-t">
        <ChatInput onSubmit={handleQuery} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default ChatInterface;