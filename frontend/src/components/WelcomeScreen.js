import React from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Users, Sparkles, Shield } from 'lucide-react';

const WelcomeScreen = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-700 flex flex-col">
      {/* Header */}
      <div className="flex-1 flex flex-col justify-center items-center px-6 py-12">
        <div className="text-center space-y-8 max-w-sm">
          {/* Logo/Icon */}
          <div className="relative">
            <div className="w-24 h-24 bg-white/20 backdrop-blur-lg rounded-full flex items-center justify-center mx-auto mb-6 glass-effect">
              <MessageCircle size={40} className="text-white" />
              <div className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center">
                <Sparkles size={16} className="text-yellow-800" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-4">
            <h1 className="text-4xl font-bold text-white leading-tight">
              AI Chat
              <span className="block text-yellow-300">Revolution</span>
            </h1>
            <p className="text-blue-100 text-lg leading-relaxed">
              Connect with ultra-realistic AI companions who understand you like real friends
            </p>
          </div>

          {/* Features */}
          <div className="space-y-4 text-left">
            <div className="flex items-center space-x-3 text-white/90">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Users size={16} />
              </div>
              <span className="text-sm">Smart personality matching</span>
            </div>
            <div className="flex items-center space-x-3 text-white/90">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Sparkles size={16} />
              </div>
              <span className="text-sm">Human-like conversations</span>
            </div>
            <div className="flex items-center space-x-3 text-white/90">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Shield size={16} />
              </div>
              <span className="text-sm">Safe & moderated chats</span>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="px-6 pb-12">
        <div className="space-y-4">
          <Link 
            to="/setup"
            className="w-full bg-white text-purple-600 font-semibold py-4 px-6 rounded-2xl text-center block transition-all duration-300 hover:bg-gray-50 hover:scale-105 shadow-lg"
          >
            Start Chatting Now
          </Link>
          
          <p className="text-center text-blue-100 text-sm">
            Join thousands having amazing conversations
          </p>
        </div>
      </div>

      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
      </div>
    </div>
  );
};

export default WelcomeScreen;