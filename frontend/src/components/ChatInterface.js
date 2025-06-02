import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Send, MoreVertical, Phone, Video } from 'lucide-react';
import toast from 'react-hot-toast';
import { v4 as uuidv4 } from 'uuid';

const ChatInterface = ({ user, session, onBackToSelection }) => {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    loadChatHistory();
    
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    try {
      const wsUrl = (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001').replace('http', 'ws');
      const ws = new WebSocket(`${wsUrl}/ws/${sessionId}/${user.user_id}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setSocket(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message') {
          setIsTyping(false);
          setMessages(prev => [...prev, {
            id: uuidv4(),
            type: 'bot',
            content: data.content,
            timestamp: new Date(data.timestamp),
            sender: data.bot_name
          }]);
        } else if (data.type === 'moderation_warning') {
          toast.error(data.message);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setSocket(null);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        toast.error('Connection error. Please refresh the page.');
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      toast.error('Failed to connect to chat');
    }
  };

  const loadChatHistory = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/chat/messages/${sessionId}`);
      
      if (response.ok) {
        const data = await response.json();
        const formattedMessages = [];
        
        data.messages.forEach(msg => {
          // Add user message
          formattedMessages.push({
            id: uuidv4(),
            type: 'user',
            content: msg.user_message,
            timestamp: new Date(msg.timestamp),
            sender: user.username
          });
          
          // Add bot response
          formattedMessages.push({
            id: uuidv4(),
            type: 'bot',
            content: msg.bot_response,
            timestamp: new Date(msg.timestamp),
            sender: session.bot_profile.name
          });
        });
        
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !socket || !isConnected) return;

    const messageId = uuidv4();
    const newMessage = {
      id: messageId,
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
      sender: user.username
    };

    // Add user message to UI immediately
    setMessages(prev => [...prev, newMessage]);

    // Send message via WebSocket
    socket.send(JSON.stringify({
      content: inputMessage.trim(),
      session_id: sessionId
    }));

    // Show typing indicator
    setIsTyping(true);

    // Clear input
    setInputMessage('');
    
    // Hide typing indicator after 5 seconds if no response
    setTimeout(() => setIsTyping(false), 5000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const TypingIndicator = () => (
    <div className="flex items-center space-x-2 p-4">
      <img
        src={`data:image/jpeg;base64,${session.bot_profile.profile_picture}`}
        alt={session.bot_profile.name}
        className="w-8 h-8 rounded-full"
        onError={(e) => {
          e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(session.bot_profile.name)}&size=32&background=667eea&color=white`;
        }}
      />
      <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-200">
        <div className="typing-indicator">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="chat-container bg-gray-50">
      {/* Header */}
      <div className="chat-header">
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => {
              onBackToSelection();
              navigate('/select-bot');
            }}
            className="p-1 hover:bg-white/10 rounded-full transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          
          <img
            src={`data:image/jpeg;base64,${session.bot_profile.profile_picture}`}
            alt={session.bot_profile.name}
            className="w-10 h-10 rounded-full border-2 border-white/20"
            onError={(e) => {
              e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(session.bot_profile.name)}&size=40&background=white&color=667eea`;
            }}
          />
          
          <div className="flex-1">
            <h2 className="font-semibold text-lg">{session.bot_profile.name}</h2>
            <div className="flex items-center space-x-2 text-sm text-white/80">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span>{isConnected ? 'Online' : 'Reconnecting...'}</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
            <Phone size={20} />
          </button>
          <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
            <Video size={20} />
          </button>
          <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
            <MoreVertical size={20} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">👋</span>
            </div>
            <p className="text-gray-600 mb-2">Start chatting with {session.bot_profile.name}!</p>
            <p className="text-sm text-gray-500">{session.welcome_message}</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
          >
            {message.type === 'bot' && (
              <img
                src={`data:image/jpeg;base64,${session.bot_profile.profile_picture}`}
                alt={session.bot_profile.name}
                className="w-8 h-8 rounded-full mr-2 mt-1"
                onError={(e) => {
                  e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(session.bot_profile.name)}&size=32&background=667eea&color=white`;
                }}
              />
            )}
            
            <div className={`message-bubble ${message.type === 'user' ? 'message-user chat-bubble-user' : 'message-bot chat-bubble-bot'}`}>
              <p className="text-sm leading-relaxed">{message.content}</p>
              <div className={`message-timestamp ${message.type === 'user' ? 'text-white/70' : 'text-gray-500'}`}>
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-container">
        <textarea
          ref={inputRef}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={`Message ${session.bot_profile.name}...`}
          className="chat-input"
          rows="1"
          disabled={!isConnected}
          style={{
            minHeight: '44px',
            maxHeight: '120px',
            height: 'auto',
            resize: 'none'
          }}
          onInput={(e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
          }}
        />
        
        <button
          onClick={sendMessage}
          disabled={!inputMessage.trim() || !isConnected}
          className="send-button"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;