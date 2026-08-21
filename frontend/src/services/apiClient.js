const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = {
  async getStatus() {
    const res = await fetch(`${API_BASE}/api/document/status`);
    if (!res.ok) throw new Error('Failed to fetch status');
    return res.json();
  },
  
  async refreshDocument() {
    const res = await fetch(`${API_BASE}/api/document/refresh`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger refresh');
    return res.json();
  },
  
  async chat(question, conversationId) {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        conversation_id: conversationId,
        context_id: "icpc_default"
      })
    });
    
    if (!res.ok) {
      let errorMsg = "Something went wrong. Please try again.";
      try {
        const errData = await res.json();
        if (errData.detail) errorMsg = errData.detail;
      } catch (e) {
        // Fallback
      }
      throw new Error(errorMsg);
    }
    
    return res.json();
  }
};
