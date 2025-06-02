import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MessageCircle, Sparkles, LogOut, Users, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const BotSelection = ({ user, onSessionStarted, onLogout }) => {
  const navigate = useNavigate();
  const [botProfiles, setBotProfiles] = useState([]);
  const [matchedBot, setMatchedBot] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStartingChat, setIsStartingChat] = useState(false);

  useEffect(() => {
    fetchBotProfiles();
    fetchMatchedBot();
  }, []);

  const fetchBotProfiles = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await axios.get(`${backendUrl}/api/bots/profiles`);
      setBotProfiles(response.data.bot_profiles);
    } catch (error) {
      console.error('Error fetching bot profiles:', error);
      toast.error('Failed to load chat buddies');
    }
  };

  const fetchMatchedBot = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await axios.get(`${backendUrl}/api/bots/match/${user.user_id}`);
      setMatchedBot(response.data.matched_bot);
    } catch (error) {
      console.error('Error fetching matched bot:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startChatWithBot = async (botId) => {
    setIsStartingChat(true);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await axios.post(`${backendUrl}/api/chat/start?user_id=${user.user_id}&bot_id=${botId}`);
      
      const sessionData = response.data;
      onSessionStarted(sessionData);
      
      toast.success(`Connected with ${sessionData.bot_profile.name}!`);
      navigate(`/chat/${sessionData.session_id}`);
      
    } catch (error) {
      console.error('Error starting chat:', error);
      toast.error('Failed to start chat. Please try again.');
    } finally {
      setIsStartingChat(false);
    }
  };

  const BotCard = ({ bot, isRecommended = false }) => (
    <div 
      className={`bot-card ${isRecommended ? 'border-2 border-yellow-400 bg-gradient-to-br from-yellow-50 to-amber-50' : ''} relative`}
      onClick={() => startChatWithBot(bot.bot_id)}
    >
      {isRecommended && (
        <div className="absolute -top-2 left-4 bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-bold flex items-center space-x-1">
          <Sparkles size={12} />
          <span>Perfect Match</span>
        </div>
      )}
      
      <div className="flex items-start space-x-4">
        <div className="relative">
          <img
            src={`data:image/jpeg;base64,${bot.profile_picture}`}
            alt={bot.name}
            className="bot-profile-pic profile-picture"
            onError={(e) => {
              e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(bot.name)}&size=60&background=667eea&color=white`;
            }}
          />
          <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 border-2 border-white rounded-full status-online"></div>
        </div>
        
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="bot-name">{bot.name}</h3>
            <span className="bot-age">{bot.age}</span>
          </div>
          
          <p className="bot-bio">{bot.bio}</p>
          
          <div className="bot-interests">
            {bot.interests.slice(0, 4).map(interest => (
              <span key={interest} className="interest-tag">
                {interest}
              </span>
            ))}
            {bot.interests.length > 4 && (
              <span className="interest-tag">+{bot.interests.length - 4}</span>
            )}
          </div>
        </div>
      </div>
      
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span>Active now</span>
        </div>
        
        <button className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-full text-sm font-medium hover:shadow-lg transition-all">
          <MessageCircle size={14} className="inline mr-1" />
          Chat Now
        </button>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Finding perfect chat buddies for you...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">Hi, {user.username}!</h1>
              <p className="text-sm text-gray-600">Choose your chat buddy</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchMatchedBot}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Refresh recommendations"
            >
              <RefreshCw size={20} className="text-gray-600" />
            </button>
            <button
              onClick={onLogout}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Logout"
            >
              <LogOut size={20} className="text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Recommended Match */}
        {matchedBot && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Sparkles size={20} className="text-yellow-500" />
              <h2 className="text-lg font-semibold text-gray-900">Recommended for You</h2>
            </div>
            <BotCard bot={matchedBot} isRecommended={true} />
          </div>
        )}

        {/* All Available Bots */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Users size={20} className="text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Available Chat Buddies</h2>
          </div>
          
          {botProfiles
            .filter(bot => bot.bot_id !== matchedBot?.bot_id)
            .map(bot => (
              <BotCard key={bot.bot_id} bot={bot} />
            ))
          }
        </div>

        {/* Stats */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{botProfiles.length}</div>
              <div className="text-sm text-gray-600">Chat Buddies</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{user.interests.length}</div>
              <div className="text-sm text-gray-600">Your Interests</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">24/7</div>
              <div className="text-sm text-gray-600">Available</div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading overlay */}
      {isStartingChat && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 text-center">
            <div className="spinner mx-auto mb-4"></div>
            <p className="text-gray-700">Starting your chat...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default BotSelection;