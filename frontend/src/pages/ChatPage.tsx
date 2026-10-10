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
  MapPin, 
  FileDown, 
  X, 
  Volume2, 
  VolumeX,
  Copy, 
  Mic, 
  MicOff,
  Map, 
  Search, 
  Camera, 
  Globe, 
  Trash2,
  ArrowRight,
  Navigation,
  Hotel,
  CheckSquare,
  ShieldAlert,
  CloudSun,
  Utensils
} from 'lucide-react';
import { apiGet, apiPost, apiDelete } from '../api/client';
import { FeedbackModal } from '../components/common/FeedbackModal';
import { CardRenderer, UICardPayload } from '../components/cards/CardRegistry';
import { ItineraryData } from '../components/cards/ItineraryCard';

interface Message {
  id: string;
  role: string;
  content: string;
  tools_used?: string[];
  sources?: Array<{ name: string; url: string; last_verified?: string }>;
  cards?: UICardPayload[];
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

interface NextStepChip {
  label: string;
  query: string;
}

const INDIC_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml', label: 'മലയാളം (Malayalam)' },
];

function getNextStepSuggestions(msg: Message): NextStepChip[] {
  const cards = msg.cards || [];
  const contentLower = (msg.content || '').toLowerCase();
  const cardTypes = cards.map((c) => (c.type || '').toLowerCase());

  if (
    cardTypes.includes('route_options') ||
    contentLower.includes('train') ||
    contentLower.includes('route') ||
    contentLower.includes('how to reach')
  ) {
    return [
      { label: 'Check nearby hotel stays', query: 'Show recommended hotel and stay areas near the destination' },
      { label: 'Explore local food and sights', query: 'What are the top local foods and places to visit?' },
      { label: 'Check return travel options', query: 'What are the return train and bus options?' },
    ];
  }

  if (
    cardTypes.includes('itinerary') ||
    contentLower.includes('itinerary') ||
    contentLower.includes('day 1')
  ) {
    return [
      { label: 'Calculate budget breakdown', query: 'Compare budget tiers and estimated cost for this trip' },
      { label: 'Smart packing checklist', query: 'Generate a smart packing list for this itinerary' },
      { label: 'Check weather and advisory', query: 'Check current weather and travel advisory for the destination' },
    ];
  }

  if (
    cardTypes.includes('budget') ||
    contentLower.includes('budget') ||
    contentLower.includes('cost')
  ) {
    return [
      { label: 'Build 3-day itinerary', query: 'Plan a 3-day grounded itinerary with monument timings' },
      { label: 'Where to stay', query: 'Where to stay: safe and convenient neighborhoods' },
      { label: 'Monument entry fees', query: 'What are the entry ticket fees and timings for top monuments?' },
    ];
  }

  if (
    cardTypes.includes('weather') ||
    contentLower.includes('weather') ||
    contentLower.includes('temperature')
  ) {
    return [
      { label: 'What should I pack?', query: 'Smart packing checklist based on current weather' },
      { label: 'Plan sightseeing route', query: 'Plan a sightseeing itinerary suited for this weather' },
      { label: 'Check travel routes', query: 'How to reach this city by train, road, or flight?' },
    ];
  }

  if (
    cardTypes.includes('sos') ||
    contentLower.includes('emergency') ||
    contentLower.includes('safety') ||
    contentLower.includes('police')
  ) {
    return [
      { label: 'Locate nearest hospital', query: 'Where is the nearest hospital and 108 emergency service?' },
      { label: 'Locate nearest police station', query: 'Where is the nearest police station?' },
      { label: 'Emergency phrases in local language', query: 'Show emergency phrases in the local language' },
    ];
  }

  if (
    cardTypes.includes('phrasebook') ||
    contentLower.includes('phrase') ||
    contentLower.includes('language')
  ) {
    return [
      { label: 'Food ordering phrases', query: 'Phrases for ordering food and dietary restrictions' },
      { label: 'Auto and Taxi phrases', query: 'Phrases for talking to taxi and auto drivers' },
      { label: 'Check travel safety', query: 'Safety tips and emergency numbers for this area' },
    ];
  }

  return [
    { label: 'Check stay options', query: 'What are the best neighborhoods and stay options?' },
    { label: 'Check travel routes', query: 'How to reach by train, road, or flight?' },
    { label: 'Estimate trip budget', query: 'What is the estimated budget breakdown for this trip?' },
  ];
}

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvoId, setActiveConvoId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedLang, setSelectedLang] = useState('en');
  const [streaming, setStreaming] = useState(false);
  const [currentToolStatus, setCurrentToolStatus] = useState<string | null>(null);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);

  // Audio Recording & Voice State
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<any>(null);

  // Audio Playback / TTS State
  const [playingMsgId, setPlayingMsgId] = useState<string | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Right Side Panel / Inspector State
  const [inspectorData, setInspectorData] = useState<ItineraryData | null>(null);
  const [inspectorTab, setInspectorTab] = useState<'plan' | 'budget' | 'map'>('plan');

  // Feedback Modal State
  const [feedbackTarget, setFeedbackTarget] = useState<{ messageId: string; rating: number } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentToolStatus]);

  // Load conversations list
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const res = await apiGet<Conversation[]>('/chat/conversations');
        if (Array.isArray(res) && res.length > 0) {
          setConversations(res);
          setActiveConvoId(res[0].id);
        } else {
          const newConvo = await apiPost<Conversation>('/chat/conversations', { title: 'Trip Planning' });
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
        const res = await apiGet<{ messages: Message[] }>(`/chat/conversations/${activeConvoId}/messages`);
        if (res && Array.isArray(res.messages)) {
          setMessages(res.messages);
        }
      } catch {
        try {
          const res = await apiGet<{ messages: Message[] }>(`/chat/conversations/${activeConvoId}`);
          if (res && Array.isArray(res.messages)) {
            setMessages(res.messages);
          }
        } catch {
          // Soft error
        }
      }
    };
    loadMessages();
  }, [activeConvoId]);

  // Fallback SpeechRecognition initialization
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognizer = new SpeechRecognition();
      recognizer.continuous = false;
      recognizer.interimResults = false;
      recognizer.lang = selectedLang === 'hi' ? 'hi-IN' : 'en-IN';

      recognizer.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsRecordingAudio(false);
      };

      recognizer.onerror = () => {
        setIsRecordingAudio(false);
      };

      recognizer.onend = () => {
        setIsRecordingAudio(false);
      };

      recognitionRef.current = recognizer;
    }
  }, [selectedLang]);

  const toggleVoiceInput = async () => {
    if (isRecordingAudio) {
      stopAudioRecording();
      return;
    }

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];

        let mimeType = 'audio/webm';
        if (typeof MediaRecorder !== 'undefined' && typeof MediaRecorder.isTypeSupported === 'function') {
          if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            mimeType = 'audio/webm;codecs=opus';
          } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
          }
        }

        const recorder = new MediaRecorder(stream, { mimeType });
        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        recorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          clearInterval(recordingTimerRef.current);
          setRecordingSeconds(0);
          setIsRecordingAudio(false);

          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
          if (audioBlob.size < 400) {
            return;
          }

          setTranscribing(true);
          try {
            const formData = new FormData();
            const ext = mimeType.includes('mp4') ? 'm4a' : 'webm';
            formData.append('file', audioBlob, `speech.${ext}`);
            formData.append('language_code', selectedLang === 'hi' ? 'hi-IN' : 'en-IN');

            const res = await fetch('/api/v1/voice/transcribe', {
              method: 'POST',
              body: formData,
              credentials: 'include',
            });

            if (res.ok) {
              const data = await res.json();
              if (data && data.transcript && data.transcript.trim()) {
                setInput((prev) => (prev ? `${prev} ${data.transcript.trim()}` : data.transcript.trim()));
              }
            }
          } catch {
            // Soft error
          } finally {
            setTranscribing(false);
          }
        };

        mediaRecorderRef.current = recorder;
        recorder.start(250);
        setIsRecordingAudio(true);
        setRecordingSeconds(0);
        recordingTimerRef.current = setInterval(() => {
          setRecordingSeconds((prev) => prev + 1);
        }, 1000);
      } else if (recognitionRef.current) {
        setIsRecordingAudio(true);
        recognitionRef.current.start();
      }
    } catch {
      if (recognitionRef.current) {
        setIsRecordingAudio(true);
        recognitionRef.current.start();
      }
    }
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    } else if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecordingAudio(false);
    }
  };

  const cleanMarkdownForSpeech = (text: string) => {
    return text
      .replace(/\[\d+\]/g, '')
      .replace(/\*\*|__/g, '')
      .replace(/\*|_/g, '')
      .replace(/^#+\s+/gm, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\n+/g, '. ')
      .trim();
  };

  const handleSpeak = async (msgId: string, text: string) => {
    if (playingMsgId === msgId) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setPlayingMsgId(null);
      return;
    }

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    const cleanText = cleanMarkdownForSpeech(text);
    if (!cleanText) return;

    setPlayingMsgId(msgId);

    try {
      const res = await apiPost<{ audio_url?: string; success?: boolean }>(
        '/voice/speak',
        {
          text: cleanText.slice(0, 450),
          target_language_code: selectedLang === 'hi' ? 'hi-IN' : 'en-IN',
        }
      );

      if (res && res.audio_url && res.success) {
        const audio = new Audio(res.audio_url);
        currentAudioRef.current = audio;
        audio.onended = () => setPlayingMsgId(null);
        audio.onerror = () => {
          fallbackBrowserTTS(cleanText, () => setPlayingMsgId(null));
        };
        await audio.play();
        return;
      }
    } catch {
      // Fallback
    }

    fallbackBrowserTTS(cleanText, () => setPlayingMsgId(null));
  };

  const fallbackBrowserTTS = (text: string, onEnd: () => void) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = selectedLang === 'hi' ? 'hi-IN' : 'en-IN';
      utterance.rate = 1.0;
      utterance.onend = onEnd;
      utterance.onerror = onEnd;
      window.speechSynthesis.speak(utterance);
    } else {
      onEnd();
    }
  };

  const handleAttachLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocation not supported');
      return;
    }
    setLocationStatus('Locating...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude.toFixed(4);
        const lng = pos.coords.longitude.toFixed(4);
        setInput((prev) => {
          const locText = `[My location: lat ${lat}, lng ${lng}]`;
          return prev ? `${prev} ${locText}` : `Near me ${locText}: `;
        });
        setLocationStatus('Attached');
        setTimeout(() => setLocationStatus(null), 3000);
      },
      () => {
        setLocationStatus('Location access denied');
        setTimeout(() => setLocationStatus(null), 3000);
      }
    );
  };

  const handleNewConversation = async () => {
    try {
      const newConvo = await apiPost<Conversation>('/chat/conversations', { title: 'New chat' });
      setConversations((prev) => [newConvo, ...prev]);
      setActiveConvoId(newConvo.id);
      setMessages([]);
      setInspectorData(null);
    } catch {
      // Soft error
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await apiDelete(`/chat/conversations/${id}`);
      const filtered = conversations.filter((c) => c.id !== id);
      setConversations(filtered);
      if (activeConvoId === id) {
        if (filtered.length > 0) {
          setActiveConvoId(filtered[0].id);
        } else {
          handleNewConversation();
        }
      }
    } catch {
      // Soft error
    }
  };

  const handleSendMessage = async (customText?: string) => {

    const userText = (customText || input).trim();
    if (!userText || streaming) return;

    if (!customText) setInput('');
    setCurrentToolStatus(null);

    // Resolve or fallback activeConvoId
    let convoId = activeConvoId;
    if (!convoId) {
      try {
        const newConvo = await apiPost<Conversation>('/chat/conversations', { title: userText.slice(0, 30) });
        if (newConvo && newConvo.id) {
          convoId = newConvo.id;
          setConversations((prev) => [newConvo, ...prev]);
          setActiveConvoId(newConvo.id);
        }
      } catch {
        // Fallback without explicit conversation ID
      }
    }

    const tempUserMsg: Message = {
      id: `temp_${Date.now()}`,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    setStreaming(true);
    abortControllerRef.current = new AbortController();

    const assistantMsgId = `asst_${Date.now()}`;
    let accumulatedText = '';
    let accumulatedSources: Array<{ name: string; url: string }> = [];
    let accumulatedCards: UICardPayload[] = [];

    // Mount assistant message bubble
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        cards: [],
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: convoId,
          message: userText,
          language: selectedLang,
        }),
        credentials: 'include',
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

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
                
                // Stream token delta
                if (event.delta || event.token) {
                  accumulatedText += event.delta || event.token || '';
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId ? { ...m, content: accumulatedText } : m
                    )
                  );
                } 
                // Tool status
                else if (event.message && event.step) {
                  setCurrentToolStatus(event.message);
                } 
                // UI Card payload
                else if (event.card && event.card.type) {
                  accumulatedCards.push(event.card);
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId ? { ...m, cards: [...accumulatedCards] } : m
                    )
                  );
                  if (event.card.type.toLowerCase() === 'itinerary') {
                    setInspectorData(event.card.data as ItineraryData);
                  }
                } 
                // Grounding sources
                else if (event.sources && Array.isArray(event.sources)) {
                  accumulatedSources = event.sources;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId ? { ...m, sources: accumulatedSources } : m
                    )
                  );
                } 
                // Done event
                else if (event.content !== undefined) {
                  const finalContent = accumulatedText || event.content || '';
                  if (event.cards && Array.isArray(event.cards)) {
                    accumulatedCards = event.cards;
                  }
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId
                        ? { ...m, content: finalContent, cards: accumulatedCards, sources: accumulatedSources }
                        : m
                    )
                  );
                  setCurrentToolStatus(null);
                }
              } catch {
                // Ignore parse error on partial chunks
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const fallbackText = accumulatedText || 'Unable to connect to the travel assistant. Please check your connection and retry.';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: fallbackText,
                }
              : m
          )
        );
      }
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

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = selectedLang === 'hi' ? 'hi-IN' : 'en-IN';
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    }
  };

  const filteredConversations = conversations.filter((c) =>
    (c.title || 'Untitled chat').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-[84vh] gap-4">
      {/* Threads Sidebar Drawer */}
      <div className="w-60 rounded-lg bg-slate-900 border border-slate-800 flex flex-col overflow-hidden shrink-0 shadow-lg">
        {/* New Chat Header */}
        <div className="p-3 border-b border-slate-800 space-y-2">
          <button
            data-testid="new-chat-button"
            onClick={handleNewConversation}
            className="w-full py-2 px-3 rounded-md bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>


          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full pl-8 pr-2.5 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-[11px] text-slate-200 placeholder:text-slate-500 focus:border-brand-500"
            />
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredConversations.map((c) => {
            const active = c.id === activeConvoId;
            return (
              <div
                key={c.id}
                onClick={() => setActiveConvoId(c.id)}
                className={`group flex items-center justify-between px-2.5 py-2 rounded-md text-xs cursor-pointer transition-colors ${
                  active
                    ? 'bg-slate-800 text-brand-300 font-medium border border-slate-700'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{c.title || 'Untitled conversation'}</span>
                </div>
                {conversations.length > 1 && (
                  <button
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 rounded transition-opacity"
                    title="Delete chat"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })}

          {filteredConversations.length === 0 && (
            <div className="py-6 text-center text-[11px] text-slate-500">
              No conversations found.
            </div>
          )}
        </div>
      </div>

      {/* Primary Chat View */}
      <div className="flex-1 flex flex-col rounded-lg bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        {/* Header */}
        <div className="h-12 px-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-brand-400" />
            <span className="font-semibold text-xs text-white">SafarSathi Travel Assistant</span>
          </div>

          <div className="flex items-center gap-2">
            {inspectorData && (
              <button
                onClick={() => setInspectorData(null)}
                className="text-[11px] px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:text-white transition-colors"
              >
                Close Inspector
              </button>
            )}
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
              <div className="w-12 h-12 rounded-md bg-brand-950 border border-brand-800 text-brand-400 flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-white">How can SafarSathi assist your trip?</h2>
                <p className="text-xs text-slate-400 max-w-md">
                  Grounded travel assistance with verified monuments, live weather, budget tiers, and emergency safety.
                </p>
              </div>

              {/* 6 Empty-State Suggestion Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-w-2xl text-left pt-2">
                {[
                  { title: 'Plan 3 days in Jaipur for 2', subtitle: 'Monuments, entry hours & budget breakdown' },
                  { title: 'Compare budget tiers for Goa', subtitle: 'Budget vs Moderate vs Luxury breakdown' },
                  { title: 'How to reach Manali from Delhi', subtitle: 'Compare road, bus & flight travel times' },
                  { title: 'Live weather and AQI in Varanasi', subtitle: 'Temperature, air index & advisory' },
                  { title: 'Smart packing checklist for Kerala', subtitle: '5-day essentials & climate checklist' },
                  { title: 'Emergency numbers in Mumbai', subtitle: '112/108 hotlines & safety advisory' },
                ].map((chip, cIdx) => (
                  <button
                    key={cIdx}
                    onClick={() => handleSendMessage(chip.title)}
                    className="p-3 rounded-md bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors cursor-pointer group"
                  >
                    <span className="text-xs font-medium text-slate-200 group-hover:text-brand-400 block">
                      {chip.title}
                    </span>
                    <span className="text-[10px] text-slate-500 block line-clamp-1">{chip.subtitle}</span>
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
                    data-testid={isUser ? "user-message" : "assistant-message"}
                    className={`max-w-[88%] rounded-lg p-4 text-xs leading-relaxed space-y-3 ${
                      isUser
                        ? 'bg-brand-600 text-white rounded-br-xs'
                        : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-xs'
                    }`}
                  >
                    {msg.content && <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>}

                    {/* Render Embedded UI Cards */}
                    {msg.cards && msg.cards.length > 0 && (
                      <div className="space-y-3 pt-1">
                        {msg.cards.map((card, cIdx) => (
                          <CardRenderer
                            key={cIdx}
                            card={card}
                            onSendChatMessage={handleSendMessage}
                            onOpenInspector={(itineraryData) => setInspectorData(itineraryData)}
                          />
                        ))}
                      </div>
                    )}

                    {/* Verified Sources Citations */}
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

                    {/* Interactive Next-Step Decision Chips */}
                    {!isUser && !streaming && msg.content && (
                      <div className="pt-2 border-t border-slate-800/70 space-y-1.5">
                        <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-brand-400" />
                          <span>Suggested next steps:</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {getNextStepSuggestions(msg).map((chip, idx) => (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => handleSendMessage(chip.query)}
                              className="px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                            >
                              <span>{chip.label}</span>
                              <ArrowRight className="w-3 h-3 text-brand-400" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Assistant Feedback Toolbar */}
                    {!isUser && msg.content && (
                      <div className="pt-1 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleSpeak(msg.id, msg.content)}
                            className={`flex items-center gap-1 transition-colors ${
                              playingMsgId === msg.id ? 'text-brand-400 font-medium' : 'hover:text-slate-200'
                            }`}
                            title={playingMsgId === msg.id ? 'Stop audio playback' : 'Read aloud with voice'}
                          >
                            {playingMsgId === msg.id ? (
                              <>
                                <VolumeX className="w-3.5 h-3.5 text-brand-400 animate-pulse" />
                                <span>Stop</span>
                              </>
                            ) : (
                              <>
                                <Volume2 className="w-3.5 h-3.5" />
                                <span>Listen</span>
                              </>
                            )}
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

                        <div className="flex items-center gap-1 text-slate-500">
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

        {/* Enhanced Composer Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="p-3 bg-slate-950 border-t border-slate-800 space-y-2"
        >
          {/* Action Row */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5">
              {/* Voice Mic Button */}
              <button
                type="button"
                onClick={toggleVoiceInput}
                className={`p-1.5 rounded-md border transition-colors flex items-center gap-1.5 ${
                  isRecordingAudio
                    ? 'bg-red-950 text-red-300 border-red-700 animate-pulse'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
                title={isRecordingAudio ? 'Stop recording and transcribe' : 'Voice input (Speak)'}
              >
                {isRecordingAudio ? (
                  <>
                    <MicOff className="w-3.5 h-3.5 text-red-400" />
                    <span className="text-[10px] font-mono text-red-300">
                      0:0{recordingSeconds}
                    </span>
                  </>
                ) : (
                  <Mic className="w-3.5 h-3.5" />
                )}
              </button>

              {transcribing && (
                <span className="inline-flex items-center gap-1 text-[11px] text-brand-400">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Transcribing...</span>
                </span>
              )}

              {/* Location Pin Button */}
              <button
                type="button"
                onClick={handleAttachLocation}
                className="p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                title="Attach current location"
              >
                <MapPin className="w-3.5 h-3.5" />
              </button>

              {/* Image Attachment (Placeholder) */}
              <div className="relative group">
                <button
                  type="button"
                  disabled
                  className="p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-600 cursor-not-allowed"
                  title="Visual Monument Recognition (Coming soon)"
                >
                  <Camera className="w-3.5 h-3.5" />
                </button>
              </div>

              {locationStatus && (
                <span className="text-[10px] text-brand-400 font-mono pl-1">{locationStatus}</span>
              )}
            </div>

            {/* Language Selector */}
            <div className="flex items-center gap-1">
              <Globe className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-slate-300 focus:border-brand-500"
              >
                {INDIC_LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Textarea Input */}
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              data-testid="message-input"
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask a question, plan a trip, or check route options (Enter to send, Shift+Enter for newline)..."
              disabled={streaming}
              className="flex-1 px-3 py-2 rounded-md bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:border-brand-500 disabled:opacity-50 resize-none"
            />

            {streaming ? (
              <button
                type="button"
                onClick={handleStop}
                className="p-2.5 rounded-md bg-red-950 border border-red-800 text-red-300 hover:bg-red-900 transition-colors shrink-0"
                title="Stop generation"
              >
                <Square className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                data-testid="send-button"
                disabled={!input.trim()}
                className="p-2.5 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white transition-colors cursor-pointer shrink-0"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

      </div>

      {/* Right Side Panel / Inspector for Itinerary & Expansive Views */}
      {inspectorData && (
        <aside className="w-[420px] rounded-lg bg-slate-900 border border-slate-800 flex flex-col overflow-hidden shadow-2xl shrink-0">
          {/* Inspector Header & Tabs */}
          <div className="h-12 px-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-1">
              {[
                { id: 'plan', label: 'Plan', icon: Calendar },
                { id: 'budget', label: 'Budget', icon: DollarSign },
                { id: 'map', label: 'Map', icon: Map },
              ].map((tab) => {
                const Icon = tab.icon;
                const active = inspectorTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setInspectorTab(tab.id as any)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      active ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => setInspectorData(null)}
              className="text-slate-400 hover:text-white p-1 rounded"
              title="Close inspector"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Inspector Tab Views */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {inspectorTab === 'plan' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">
                    {inspectorData.destination} Itinerary (v{inspectorData.version || 1})
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-brand-950 text-brand-300 font-mono">
                    {inspectorData.days?.length || 0} Days
                  </span>
                </div>

                <div className="space-y-2">
                  {inspectorData.days?.map((day) => (
                    <div key={day.day} className="p-3 rounded-md bg-slate-950 border border-slate-800 space-y-2">
                      <div className="text-xs font-semibold text-brand-400">
                        Day {day.day}: {day.theme}
                      </div>
                      <div className="space-y-1.5">
                        {day.slots?.map((slot, sIdx) => (
                          <div key={sIdx} className="text-xs flex items-start justify-between border-b border-slate-900 pb-1">
                            <div>
                              <span className="font-mono text-slate-400 text-[10px] block">{slot.time}</span>
                              <span className="text-slate-200 font-medium">{slot.place}</span>
                            </div>
                            {slot.opening_hours && slot.opening_hours !== 'verify' && (
                              <span className="text-[10px] text-emerald-400 font-mono">{slot.opening_hours}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {inspectorTab === 'budget' && (
              <div className="space-y-3 text-xs">
                <h3 className="text-sm font-semibold text-white">Cost Breakdown</h3>
                <p className="text-slate-400">
                  Itemized estimation for {inspectorData.destination} ({inspectorData.days?.length || 3} Days).
                </p>
                <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex justify-between py-1 border-b border-slate-900">
                    <span className="text-slate-400">Estimated Total</span>
                    <span className="font-mono text-emerald-400 font-semibold">
                      ₹{((inspectorData.days?.length || 3) * 2 * 2200).toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-900">
                    <span className="text-slate-400">Hotel / Stay</span>
                    <span className="font-mono text-slate-300">
                      ₹{((inspectorData.days?.length || 3) * 1800).toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Food & Monument Fees</span>
                    <span className="font-mono text-slate-300">
                      ₹{((inspectorData.days?.length || 3) * 2 * 1300).toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {inspectorTab === 'map' && (
              <div className="h-64 flex flex-col items-center justify-center text-center p-6 space-y-2 bg-slate-950 rounded-md border border-slate-800">
                <Map className="w-8 h-8 text-slate-600" />
                <div className="text-xs font-semibold text-slate-300">Interactive Map View</div>
                <p className="text-[11px] text-slate-500 max-w-xs">
                  Google Maps route polyline and pinned monument markers are arriving in Phase 2 Step F7.
                </p>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* User Feedback Modal */}
      {feedbackTarget && (
        <FeedbackModal
          onClose={() => setFeedbackTarget(null)}
          messageId={feedbackTarget.messageId}
          initialRating={feedbackTarget.rating}
        />
      )}
    </div>
  );
};

