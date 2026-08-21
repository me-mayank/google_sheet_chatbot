import React, { useEffect, useRef } from 'react';
import Message from './Message';
import SuggestedQuestions from './SuggestedQuestions';

export default function ChatWindow({ messages, onSelectSuggestion }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return <SuggestedQuestions onSelect={onSelectSuggestion} />;
  }

  return (
    <div className="flex-1 overflow-y-auto py-6 px-2 scroll-smooth">
      <div className="flex flex-col space-y-2">
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
