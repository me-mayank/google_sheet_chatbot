import React, { useState } from 'react';
import { useChat } from '../hooks/useChat';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import SyncStatus from '../components/SyncStatus';
import ErrorBanner from '../components/ErrorBanner';

export default function ChatPage() {
  const { 
    messages, 
    sendMessage, 
    loading, 
    error, 
    syncStatus, 
    triggerRefresh 
  } = useChat();

  const [dismissedError, setDismissedError] = useState(null);

  // Allow temporary dismissal of error
  const displayError = error && error !== dismissedError ? error : null;

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 md:p-8 bg-gray-50 font-sans">
      
      {/* Header */}
      <header className="flex items-center justify-between py-4 border-b border-gray-200 mb-2">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">ICPC Coach Assistant</h1>
          <p className="text-sm text-gray-500 mt-1">Context-Driven Document Q&A</p>
        </div>
        <SyncStatus statusObj={syncStatus} onRefresh={triggerRefresh} />
      </header>

      <ErrorBanner 
        error={displayError} 
        onDismiss={() => setDismissedError(error)} 
      />

      <ChatWindow 
        messages={messages} 
        onSelectSuggestion={sendMessage} 
      />

      <InputBox 
        onSend={sendMessage} 
        loading={loading} 
      />
      
    </div>
  );
}
