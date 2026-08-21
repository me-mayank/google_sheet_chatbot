import React from 'react';

export default function Message({ message }) {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`flex w-full ${isAssistant ? 'justify-start' : 'justify-end'} mb-6`}>
      <div 
        className={`max-w-[85%] rounded-xl px-5 py-3 ${
          isAssistant 
            ? 'bg-white shadow-sm border border-gray-100 text-gray-800' 
            : 'bg-blue-600 text-white shadow-sm'
        }`}
      >
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
        </div>
        
        {isAssistant && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-2 border-t border-gray-100 flex flex-wrap gap-2">
            {message.sources.map((src, idx) => (
              <span 
                key={idx} 
                className="inline-flex items-center text-xs bg-gray-50 border border-gray-200 text-gray-500 px-2 py-1 rounded"
              >
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {src.date} - {src.section}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
