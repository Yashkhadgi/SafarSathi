import React, { useEffect, useRef, useState } from 'react';
import { 
  Send, 
  Square, 
  ThumbsUp, 
  ThumbsDown, 
  ExternalLink, 
  Sparkles, 
  Loader2, 
  MessageSquare, 
  Plus, 
  Calendar, 
  DollarSign, 
  Navigation, 
  ShieldAlert, 
  Luggage, 
  FileDown, 
  Check, 
  X, 
  RotateCcw, 
  Volume2, 
  Copy, 
  Download 
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

  // Right Side Panel / Inspector State
  const [sidePanelContent, setSidePanelContent] = useState<{
    title: string;
    type: 'itinerary' | 'budget' | 'checklist' | 'export';
    data: any;
  } | null>(null);

  // Packing Checklist Interactive State
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

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
          const newConvo = await apiPost<Conversation>('/conversations', { title: 'Trip Planning' });
          setConversations([newConvo]);
          setActiveConvoId(newConvo.id);
        }
      } catch {
        // Soft error
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
        // Soft error
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
      setSidePanelContent(null);
    } catch {
      // Soft error
    }
  };

  const handleSendMessage = async (customText?: string) => {
    const userText = (customText || input).trim();
    if (!userText || streaming || !activeConvoId) return;

    if (!customText) setInput('');
    setCurrentToolStatus(null);

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
                  setCurrentToolStatus(event.data.message || 'Consulting verified travel sources...');
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

  const speakText = (text: string, lang = 'hi-IN') => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleToggleCheck = (item: string) => {
    setCheckedItems((prev) => ({ ...prev, [item]: !prev[item] }));
  };

  return (
    <div className="flex h-[84vh] gap-4">
      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col rounded-lg bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        {/* Thread Header */}
        <div className="h-12 px-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-brand-400" />
            <span className="font-semibold text-xs text-white">SafarSathi Travel Assistant</span>
          </div>

          <div className="flex items-center gap-2">
            {sidePanelContent && (
              <button
                onClick={() => setSidePanelContent(null)}
                className="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 hover:text-white"
              >
                Hide Inspector
              </button>
            )}
            <button
              onClick={handleNewConversation}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Chat</span>
            </button>
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
              <div className="w-12 h-12 rounded-md bg-brand-950 border border-brand-800 text-brand-400 flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-white">Ask anything about India travel</h2>
                <p className="text-xs text-slate-400 max-w-md">
                  Itineraries, transport routes, budget comparison, weather forecasts, fair auto fares, emergency phrases, and cultural etiquette.
                </p>
              </div>

              {/* Quick Prompt Starters */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg text-left pt-2">
                {[
                  { title: 'Plan 3 days in Jaipur', subtitle: 'Heritage forts, opening hours & budget' },
                  { title: 'Nagpur to Mumbai on 3rd Nov', subtitle: 'Compare road, rail & flight travel times' },
                  { title: 'Scams to watch out for in Delhi', subtitle: 'Verified tourist alerts & safety notes' },
                  { title: 'Packing list for Goa in winter', subtitle: 'Clothing, essentials & pre-trip items' },
                ].map((starter, sIdx) => (
                  <button
                    key={sIdx}
                    onClick={() => handleSendMessage(starter.title)}
                    className="p-2.5 rounded-md bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors cursor-pointer group"
                  >
                    <span className="text-xs font-medium text-slate-200 group-hover:text-brand-400 block">
                      {starter.title}
                    </span>
                    <span className="text-[10px] text-slate-500 block">{starter.subtitle}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] rounded-lg p-4 text-xs leading-relaxed space-y-3 ${
                      isUser
                        ? 'bg-brand-600 text-white rounded-br-xs'
                        : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-xs'
                    }`}
                  >
                    <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>

                    {/* Sources Citation List */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="pt-2 border-t border-slate-800/80 text-[10px] space-y-1">
                        <span className="text-slate-400 font-semibold block">Verified Grounding Sources:</span>
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

                    {/* Assistant Action Bar & Feedback */}
                    {!isUser && msg.content && (
                      <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => speakText(msg.content)}
                            className="flex items-center gap-1 hover:text-slate-200 transition-colors"
                            title="Speak message"
                          >
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>Read aloud</span>
                          </button>
                          <button
                            onClick={() => navigator.clipboard.writeText(msg.content)}
                            className="flex items-center gap-1 hover:text-slate-200 transition-colors"
                            title="Copy text"
                          >
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </button>
                        </div>

                        <div className="flex items-center gap-1.5 text-slate-500">
                          <button
                            onClick={() => setFeedbackTarget({ messageId: msg.id, rating: 1 })}
                            className="p-1 hover:text-emerald-400 hover:bg-slate-900 rounded transition-colors"
                            title="Helpful response"
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
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Tool status indicator */}
          {currentToolStatus && (
            <div className="flex items-center gap-2 text-xs text-brand-400 bg-brand-950/30 border border-brand-900/40 p-2.5 rounded-md max-w-sm">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>{currentToolStatus}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or request a plan (e.g. 'Compare budget tiers for Goa')..."
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
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>

      {/* Collapsible Right-Side Panel / Inspector for Structured Results */}
      {sidePanelContent && (
        <aside className="w-96 rounded-lg bg-slate-900 border border-slate-800 flex flex-col overflow-hidden shadow-xl">
          <div className="h-12 px-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-bold text-white truncate">{sidePanelContent.title}</span>
            <button
              onClick={() => setSidePanelContent(null)}
              className="text-slate-400 hover:text-white p-1 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {sidePanelContent.type === 'checklist' && (
              <div className="space-y-2">
                <span className="text-slate-400 font-semibold block">Interactive Packing Items:</span>
                {Array.isArray(sidePanelContent.data) &&
                  sidePanelContent.data.map((item: string, idx: number) => {
                    const isChecked = Boolean(checkedItems[item]);
                    return (
                      <div
                        key={idx}
                        onClick={() => handleToggleCheck(item)}
                        className={`p-2 rounded border flex items-center gap-2 cursor-pointer transition-colors ${
                          isChecked
                            ? 'bg-slate-950 border-slate-800 text-slate-500 line-through'
                            : 'bg-slate-950 border-slate-800 text-slate-200'
                        }`}
                      >
                        <div
                          className={`w-4 h-4 rounded flex items-center justify-center border ${
                            isChecked ? 'bg-brand-600 border-brand-500 text-white' : 'border-slate-700'
                          }`}
                        >
                          {isChecked && <Check className="w-3 h-3" />}
                        </div>
                        <span className="text-xs">{item}</span>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        </aside>
      )}

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
