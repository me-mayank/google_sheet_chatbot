import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/apiClient';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [syncStatus, setSyncStatus] = useState(null);

  // Poll sync status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await apiClient.getStatus();
        setSyncStatus(data);
      } catch (err) {
        // Ignore polling errors
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000); // 60s
    return () => clearInterval(interval);
  }, []);

  const triggerRefresh = async () => {
    try {
      await apiClient.refreshDocument();
      // Optimistically set to syncing
      setSyncStatus(prev => ({ ...prev, status: 'syncing' }));
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async (question) => {
    if (!question.trim()) return;
    
    const userMsg = { role: 'user', content: question, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.chat(question, conversationId);
      
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
      }
      
      const assistantMsg = { 
        role: 'assistant', 
        content: data.answer, 
        sources: data.sources,
        id: Date.now() + 1 
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setError(err.message || "An unexpected error occurred.");
      // We can also add an error message to chat if desired, but banner is preferred
    } finally {
      setLoading(false);
    }
  };

  return {
    messages,
    sendMessage,
    loading,
    error,
    syncStatus,
    triggerRefresh
  };
}
