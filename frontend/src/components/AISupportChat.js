import { useState, useRef, useEffect } from 'react';
import { 
  Bot, User, Send, Loader2, ArrowRight, MessageSquare,
  Sparkles, X, ChevronDown
} from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AISupportChat = ({ 
  token, 
  devices = [], 
  onEscalate, 
  onSkip,
  onResolved 
}) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [showDeviceSelect, setShowDeviceSelect] = useState(false);
  const [canEscalate, setCanEscalate] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial greeting
  useEffect(() => {
    const greeting = {
      role: 'assistant',
      content: "Hi! I'm your AI Support Assistant. I can help troubleshoot common IT issues before creating a ticket.\n\nWhat issue are you experiencing today?"
    };
    setMessages([greeting]);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/company/ai-support/chat`, {
        message: userMessage.content,
        session_id: sessionId,
        message_history: messages.filter(m => m.role !== 'assistant' || messages.indexOf(m) > 0),
        device_id: selectedDevice?.id || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Enable escalation after AI suggests it or after 3 user messages
      const userMsgCount = messages.filter(m => m.role === 'user').length + 1;
      if (response.data.should_escalate || userMsgCount >= 3) {
        setCanEscalate(true);
      }

    } catch (error) {
      toast.error('Failed to get AI response');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble connecting. Would you like to create a support ticket instead?"
      }]);
      setCanEscalate(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleEscalate = async () => {
    try {
      // Generate summary from conversation
      const response = await axios.post(`${API}/company/ai-support/generate-summary`, {
        messages: messages
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      onEscalate({
        subject: response.data.subject,
        description: response.data.description,
        device_id: selectedDevice?.id,
        ai_session_id: sessionId
      });
    } catch (error) {
      // Fallback if summary generation fails
      onEscalate({
        subject: messages.find(m => m.role === 'user')?.content?.slice(0, 100) || 'Support Request',
        description: messages.map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`).join('\n\n'),
        device_id: selectedDevice?.id,
        ai_session_id: sessionId
      });
    }
  };

  const handleResolved = () => {
    toast.success('Glad we could help!');
    onResolved?.();
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden" data-testid="ai-support-chat">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-white font-semibold">AI Support Assistant</h3>
              <p className="text-violet-200 text-sm">Let's try to solve this together</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onSkip}
            className="text-white/80 hover:text-white hover:bg-white/10"
          >
            Skip to ticket <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Device Selection */}
      {devices.length > 0 && (
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
          <div className="relative">
            <button
              onClick={() => setShowDeviceSelect(!showDeviceSelect)}
              className="w-full flex items-center justify-between px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm hover:border-violet-300 transition-colors"
            >
              <span className={selectedDevice ? 'text-slate-900' : 'text-slate-500'}>
                {selectedDevice 
                  ? `${selectedDevice.brand} ${selectedDevice.model} (${selectedDevice.serial_number})`
                  : 'Select a device (optional)'
                }
              </span>
              <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${showDeviceSelect ? 'rotate-180' : ''}`} />
            </button>
            
            {showDeviceSelect && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
                <button
                  onClick={() => { setSelectedDevice(null); setShowDeviceSelect(false); }}
                  className="w-full px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"
                >
                  No specific device
                </button>
                {devices.map(device => (
                  <button
                    key={device.id}
                    onClick={() => { setSelectedDevice(device); setShowDeviceSelect(false); }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-violet-50 border-t border-slate-100"
                  >
                    <span className="font-medium">{device.brand} {device.model}</span>
                    <span className="text-slate-500 ml-2">({device.serial_number})</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="h-80 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' 
                ? 'bg-emerald-100 text-emerald-600' 
                : 'bg-violet-100 text-violet-600'
            }`}>
              {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
              msg.role === 'user'
                ? 'bg-emerald-600 text-white rounded-tr-md'
                : 'bg-slate-100 text-slate-800 rounded-tl-md'
            }`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-slate-100 rounded-2xl rounded-tl-md px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-200 bg-slate-50">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your issue..."
            className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-sm"
            disabled={isLoading}
            data-testid="ai-chat-input"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="bg-violet-600 hover:bg-violet-700 rounded-xl px-4"
            data-testid="ai-chat-send"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>

        {/* Action Buttons */}
        {canEscalate && (
          <div className="flex gap-2 mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleResolved}
              className="flex-1 border-emerald-200 text-emerald-700 hover:bg-emerald-50"
              data-testid="ai-resolved-btn"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Issue Resolved
            </Button>
            <Button
              size="sm"
              onClick={handleEscalate}
              className="flex-1 bg-slate-800 hover:bg-slate-900"
              data-testid="ai-escalate-btn"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Create Ticket
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AISupportChat;
