import React, { useEffect, useRef, useState } from 'react';
import { 
  Send, 
  Square, 
  ThumbsUp, 
  ThumbsDown, 
  Mic, 
  ExternalLink, 
  Sparkles, 
  Loader2, 
  MessageSquare, 
  Plus 
} from 'lucide-react';
import { apiGet, apiPost } from '../api/client';
import { FeedbackModal } from '../components/common/FeedbackModal';

interface Message {
  id: string;
  role: string;
  content: string;
  tools_used?: string[];
  sources?: Array<{ name: string; url: string; last_verified?: string }>;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvoId, setActiveConvoId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [currentToolStatus, setCurrentToolStatus] = useState<string | null>(null);

  // Feedback Modal State
  const [feedbackTarget, setFeedbackTarget] = useState<{ messageId: string; rating: number } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentToolStatus]);

  // Load conversations
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const res = await apiGet<{ conversations: Conversation[] }>('/conversations');
        if (res.conversations && res.conversations.length > 0) {
          setConversations(res.conversations);
          setActiveConvoId(res.conversations[0].id);
        } else {
          // Create initial conversation
          const newConvo = await apiPost<Conversation>('/conversations', { title: 'Trip Planning' });
          setConversations([newConvo]);
          setActiveConvoId(newConvo.id);
        }
      } catch {
        // Ignore
      }
    };
    loadConversations();
  }, []);

  // Load messages for active conversation
  useEffect(() => {
    if (!activeConvoId) return;

    const loadMessages = async () => {
      try {
        const res = await apiGet<{ messages: Message[] }>(`/conversations/${activeConvoId}/messages`);
        setMessages(res.messages || []);
      } catch {
        // Ignore
      }
    };
    loadMessages();
  }, [activeConvoId]);

  const handleNewConversation = async () => {
    try {
      const newConvo = await apiPost<Conversation>('/conversations', { title: 'New chat' });
      setConversations((prev) => [newConvo, ...prev]);
      setActiveConvoId(newConvo.id);
      setMessages([]);
    } catch {
      // Ignore
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || streaming || !activeConvoId) return;

    const userText = input.trim();
    setInput('');
    setCurrentToolStatus(null);

    // Optimistic user message
    const tempUserMsg: Message = {
      id: `temp_${Date.now()}`,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    setStreaming(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: activeConvoId,
          message: userText,
        }),
        credentials: 'include',
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Chat error: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMsgId = `asst_${Date.now()}`;
      let accumulatedText = '';
      let accumulatedSources: Array<{ name: string; url: string }> = [];
      let accumulatedTools: string[] = [];

      // Add temporary placeholder for assistant
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: '',
          created_at: new Date().toISOString(),
        },
      ]);

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6));
                if (event.event === 'token') {
                  accumulatedText += event.data.token || '';
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId ? { ...m, content: accumulatedText } : m
                    )
                  );
                } else if (event.event === 'status') {
                  setCurrentToolStatus(event.data.message || 'Consulting travel knowledge base...');
                } else if (event.event === 'sources') {
                  accumulatedSources = event.data.sources || [];
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId ? { ...m, sources: accumulatedSources } : m
                    )
                  );
                } else if (event.event === 'done') {
                  if (event.data.message_id) assistantMsgId = event.data.message_id;
                  setCurrentToolStatus(null);
                }
              } catch {
                // Ignore parse errors on stream tokens
              }
            }
          }
        }
      }
    } catch {
      // Stream aborted or network error
    } finally {
      setStreaming(false);
      setCurrentToolStatus(null);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setStreaming(false);
      setCurrentToolStatus(null);
    }
  };

  return (
    <div className="h-[80vh] flex flex-col rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
      {/* Thread Header */}
      <div className="h-12 px-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-brand-400" />
          <span className="font-semibold text-xs text-white">SafarSathi Live Assistant</span>
        </div>

        <button
          onClick={handleNewConversation}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
            <div className="w-12 h-12 rounded-md bg-brand-950 border border-brand-800 text-brand-400 flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-sm font-semibold text-white">How can SafarSathi assist your travel today?</h2>
            <p className="text-xs text-slate-400 max-w-sm">
              Ask about verified itinerary planning, regional scam alerts, train/bus connectivity, entry fees, or food guides.
            </p>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] rounded-lg p-3.5 text-xs leading-relaxed space-y-2 ${
                    isUser
                      ? 'bg-brand-600 text-white rounded-br-xs'
                      : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Sources citation list */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 text-[10px] space-y-1">
                      <span className="text-slate-400 font-semibold block">Verified Sources:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((s, sIdx) => (
                          <a
                            key={sIdx}
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-brand-300 hover:underline"
                          >
                            <span>{s.name}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Assistant Feedback Toolbar */}
                  {!isUser && msg.content && (
                    <div className="pt-1 flex items-center justify-end gap-1.5 text-slate-500">
                      <button
                        onClick={() => setFeedbackTarget({ messageId: msg.id, rating: 1 })}
                        className="p-1 hover:text-emerald-400 hover:bg-slate-900 rounded transition-colors"
                        title="Helpful"
                      >
                        <ThumbsUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => setFeedbackTarget({ messageId: msg.id, rating: -1 })}
                        className="p-1 hover:text-red-400 hover:bg-slate-900 rounded transition-colors"
                        title="Not helpful"
                      >
                        <ThumbsDown className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {/* Live tool status indicator */}
        {currentToolStatus && (
          <div className="flex items-center gap-2 text-xs text-brand-400 bg-brand-950/30 border border-brand-900/40 p-2.5 rounded-md max-w-sm">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>{currentToolStatus}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask travel questions e.g. 'Plan 3 days in Jaipur with entry fees'..."
          disabled={streaming}
          className="flex-1 px-3 py-2 rounded-md bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:border-brand-500 disabled:opacity-50"
        />

        {streaming ? (
          <button
            type="button"
            onClick={handleStop}
            className="p-2 rounded-md bg-red-950 border border-red-800 text-red-300 hover:bg-red-900 transition-colors"
            title="Stop generation"
          >
            <Square className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="p-2 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white transition-colors cursor-pointer"
            title="Send"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </form>

      {/* Feedback Modal */}
      {feedbackTarget && (
        <FeedbackModal
          messageId={feedbackTarget.messageId}
          conversationId={activeConvoId || undefined}
          initialRating={feedbackTarget.rating}
          onClose={() => setFeedbackTarget(null)}
        />
      )}
    </div>
  );
};
