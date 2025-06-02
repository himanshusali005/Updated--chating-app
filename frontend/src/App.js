import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import WelcomeScreen from './components/WelcomeScreen';
import ProfileSetup from './components/ProfileSetup';
import BotSelection from './components/BotSelection';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Check for existing user session
  useEffect(() => {
    const savedUser = localStorage.getItem('chatapp_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('chatapp_user');
      }
    }
  }, []);

  const handleUserCreated = (userData) => {
    setUser(userData);
    localStorage.setItem('chatapp_user', JSON.stringify(userData));
  };

  const handleSessionStarted = (sessionData) => {
    setCurrentSession(sessionData);
  };

  const handleLogout = () => {
    setUser(null);
    setCurrentSession(null);
    localStorage.removeItem('chatapp_user');
  };

  return (
    <div className="mobile-container">
      <Router>
        <Routes>
          {/* Welcome Screen */}
          <Route 
            path="/" 
            element={
              !user ? (
                <WelcomeScreen />
              ) : (
                <Navigate to="/select-bot" replace />
              )
            } 
          />
          
          {/* Profile Setup */}
          <Route 
            path="/setup" 
            element={
              !user ? (
                <ProfileSetup 
                  onUserCreated={handleUserCreated}
                  isLoading={isLoading}
                  setIsLoading={setIsLoading}
                />
              ) : (
                <Navigate to="/select-bot" replace />
              )
            } 
          />
          
          {/* Bot Selection */}
          <Route 
            path="/select-bot" 
            element={
              user ? (
                <BotSelection 
                  user={user}
                  onSessionStarted={handleSessionStarted}
                  onLogout={handleLogout}
                />
              ) : (
                <Navigate to="/" replace />
              )
            } 
          />
          
          {/* Chat Interface */}
          <Route 
            path="/chat/:sessionId" 
            element={
              user && currentSession ? (
                <ChatInterface 
                  user={user}
                  session={currentSession}
                  onBackToSelection={() => setCurrentSession(null)}
                />
              ) : (
                <Navigate to="/select-bot" replace />
              )
            } 
          />
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
      
      <Toaster 
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#1f2937',
            color: '#f9fafb',
            borderRadius: '12px',
            padding: '12px 16px',
          },
        }}
      />
    </div>
  );
}

export default App;