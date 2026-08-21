import React from 'react';

export default function SyncStatus({ statusObj, onRefresh }) {
  if (!statusObj) return null;

  let color = "bg-gray-300";
  let text = "Unknown sync status";

  if (statusObj.status === "synced") {
    color = "bg-green-500";
    if (statusObj.last_synced_at) {
      const date = new Date(statusObj.last_synced_at);
      text = `Synced: ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      text = "Synced";
    }
    if (statusObj.document_too_large) {
      text += " (Doc is large, filters apply)";
      color = "bg-yellow-500";
    }
  } else if (statusObj.status === "syncing") {
    color = "bg-yellow-400 animate-pulse";
    text = "Syncing...";
  } else if (statusObj.status === "sync_failed") {
    color = "bg-red-500";
    text = "Sync failed";
  } else if (statusObj.status === "never_synced") {
    color = "bg-gray-400";
    text = "Not synced yet";
  }

  return (
    <div className="flex items-center space-x-2 text-xs text-gray-500 bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      <span>{text}</span>
      
      <button 
        onClick={onRefresh} 
        disabled={statusObj.status === "syncing"}
        className="ml-2 text-blue-600 hover:text-blue-800 disabled:opacity-50"
        title="Force Refresh"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>
  );
}
