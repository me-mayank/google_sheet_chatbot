import React from 'react';

const SUGGESTIONS = [
  "What happened this week?",
  "Give me the current ICPC status.",
  "How are the teams performing?",
  "What are the major problems right now?",
  "What is planned next?",
  "Summarize the preparation so far."
];

export default function SuggestedQuestions({ onSelect }) {
  return (
    <div className="text-center text-gray-500 mt-10">
      <p className="mb-6">Ask anything about ICPC preparation...</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
        {SUGGESTIONS.map((q, idx) => (
          <button 
            key={idx}
            onClick={() => onSelect(q)}
            className="border border-gray-200 rounded-lg p-3 text-sm hover:bg-white hover:shadow-sm hover:border-gray-300 text-left transition-all duration-200 text-gray-700"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
