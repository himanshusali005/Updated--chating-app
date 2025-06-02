import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, Calendar, Globe, Heart } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const ProfileSetup = ({ onUserCreated, isLoading, setIsLoading }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    age: '',
    interests: [],
    language: 'en'
  });

  const availableInterests = [
    'travel', 'photography', 'food', 'art', 'music', 'fitness', 'technology',
    'fashion', 'gaming', 'movies', 'books', 'cooking', 'sports', 'nature',
    'culture', 'science', 'business', 'creativity', 'adventure', 'spirituality'
  ];

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const toggleInterest = (interest) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username.trim()) {
      toast.error('Please enter a username');
      return;
    }

    if (!formData.age || formData.age < 13 || formData.age > 100) {
      toast.error('Please enter a valid age (13-100)');
      return;
    }

    if (formData.interests.length === 0) {
      toast.error('Please select at least one interest');
      return;
    }

    setIsLoading(true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await axios.post(`${backendUrl}/api/users/create`, {
        username: formData.username.trim(),
        age: parseInt(formData.age),
        interests: formData.interests,
        language: formData.language
      });

      const userData = {
        user_id: response.data.user_id,
        username: formData.username.trim(),
        age: parseInt(formData.age),
        interests: formData.interests,
        language: formData.language
      };

      onUserCreated(userData);
      toast.success('Profile created! Let\'s find you a perfect chat buddy');
      navigate('/select-bot');

    } catch (error) {
      console.error('Error creating user:', error);
      toast.error('Failed to create profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-700">
      {/* Header */}
      <div className="flex items-center justify-between p-4 text-white">
        <button 
          onClick={() => navigate('/')}
          className="p-2 hover:bg-white/10 rounded-full transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-lg font-semibold">Create Profile</h1>
        <div className="w-10"></div>
      </div>

      {/* Form */}
      <div className="px-6 pb-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 glass-effect">
            <div className="flex items-center space-x-3 mb-4">
              <User size={20} className="text-white" />
              <h2 className="text-white font-semibold">What should we call you?</h2>
            </div>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Enter your username"
              className="w-full bg-white/20 border border-white/30 rounded-xl px-4 py-3 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white/50"
              maxLength={20}
            />
          </div>

          {/* Age */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 glass-effect">
            <div className="flex items-center space-x-3 mb-4">
              <Calendar size={20} className="text-white" />
              <h2 className="text-white font-semibold">How old are you?</h2>
            </div>
            <input
              type="number"
              name="age"
              value={formData.age}
              onChange={handleInputChange}
              placeholder="Enter your age"
              min="13"
              max="100"
              className="w-full bg-white/20 border border-white/30 rounded-xl px-4 py-3 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white/50"
            />
          </div>

          {/* Language */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 glass-effect">
            <div className="flex items-center space-x-3 mb-4">
              <Globe size={20} className="text-white" />
              <h2 className="text-white font-semibold">Preferred language</h2>
            </div>
            <select
              name="language"
              value={formData.language}
              onChange={handleInputChange}
              className="w-full bg-white/20 border border-white/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code} className="bg-purple-700">
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          {/* Interests */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 glass-effect">
            <div className="flex items-center space-x-3 mb-4">
              <Heart size={20} className="text-white" />
              <h2 className="text-white font-semibold">What are you into?</h2>
            </div>
            <p className="text-white/80 text-sm mb-4">Select your interests to find compatible chat partners</p>
            
            <div className="grid grid-cols-2 gap-2">
              {availableInterests.map(interest => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className={`p-3 rounded-xl text-sm font-medium transition-all ${
                    formData.interests.includes(interest)
                      ? 'bg-white text-purple-600 shadow-lg'
                      : 'bg-white/20 text-white hover:bg-white/30'
                  }`}
                >
                  {interest.charAt(0).toUpperCase() + interest.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-white text-purple-600 font-semibold py-4 px-6 rounded-2xl transition-all duration-300 hover:bg-gray-50 hover:scale-105 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="spinner"></div>
                <span>Creating Profile...</span>
              </div>
            ) : (
              'Find My Perfect Chat Buddy'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ProfileSetup;