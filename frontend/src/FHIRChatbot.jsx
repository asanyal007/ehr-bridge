import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * FHIR Data Chatbot Component
 * Natural language interface for querying FHIR data
 */
const FHIRChatbot = ({ token }) => {
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive (but not when user is typing)
  useEffect(() => {
    if (chatMessages.length > 0 && !chatLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages.length, chatLoading]);

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!chatInput.trim() || chatLoading) return;

    const userQuestion = chatInput.trim();
    
    // Add user message immediately
    const userMessage = { role: 'user', content: userQuestion };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};
      const resp = await axios.post(
        `${API_BASE_URL}/api/v1/chat/query`,
        {
          question: userQuestion,
          conversation_id: conversationId
        },
        { headers: authHeaders }
      );

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: resp.data.answer,
        results_count: resp.data.results_count,
        query_used: resp.data.query_used,
        response_time: resp.data.response_time,
        translation_error: resp.data.translation_error,
        did_fallback: resp.data.did_fallback
      };
      setChatMessages(prev => [...prev, assistantMessage]);
      setConversationId(resp.data.conversation_id);
    } catch (err) {
      console.error('Chat query error:', err);
      const backendAnswer = err.response?.data?.answer;
      const translationError = err.response?.data?.translation_error || err.response?.data?.error;
      const errorMessage = {
        role: 'assistant',
        content: backendAnswer || 'Sorry, I encountered an error processing your question. Please try again.',
        error: true,
        translation_error: translationError
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  const resetChat = async () => {
    if (conversationId) {
      try {
        const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};
        await axios.post(
          `${API_BASE_URL}/api/v1/chat/reset`,
          { conversation_id: conversationId },
          { headers: authHeaders }
        );
      } catch (err) {
        console.error('Failed to reset conversation:', err);
      }
    }
    setChatMessages([]);
    setConversationId(null);
    setChatInput('');
  };

  const ChatMessage = ({ message }) => {
    const isUser = message.role === 'user';
    const isError = message.error;
    const isWarning = !isUser && !isError && (message.did_fallback || message.translation_error);
    
    return (
      <div className={`mb-4 flex ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[75%] rounded-lg p-4 shadow-md ${
          isUser 
            ? 'bg-amber-600 text-white' 
            : isError
            ? 'bg-red-100 border border-red-300 text-red-800'
            : isWarning
            ? 'bg-amber-50 border border-amber-200 text-amber-800'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}>
          {/* Plain text content - preserve line breaks */}
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          
          {/* Response time indicator */}
          {message.response_time && (
            <div className="mt-2 text-xs opacity-60">
              ⚡ {message.response_time}s
            </div>
          )}
          
          {message.results_count !== undefined && !isError && !message.did_fallback && (
            <div className="mt-2 pt-2 border-t border-gray-300 opacity-75">
              <p className="text-xs">
                📊 Found {message.results_count} record{message.results_count !== 1 ? 's' : ''}
              </p>
            </div>
          )}
          
          {message.translation_error && (
            <div className="mt-3 text-xs bg-white/60 border border-amber-200 text-amber-800 rounded p-2">
              ⚠️ Translation detail: {message.translation_error}
            </div>
          )}

          {message.did_fallback && (
            <div className="mt-3 text-xs bg-white/40 text-amber-700">
              <p className="font-semibold mb-1">Try a clearer question:</p>
              <div className="flex flex-wrap gap-2">
                {['How many patients do we have?', 'Show me female patients', 'Show me observations for patient 123'].map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setChatInput(suggestion)}
                    className="px-2 py-1 rounded bg-amber-100 hover:bg-amber-200 text-amber-800 transition-colors"
                    type="button"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {message.query_used && Object.keys(message.query_used).length > 0 && (
            <details className="mt-2">
              <summary className="text-xs cursor-pointer opacity-75 hover:opacity-100">
                View Query Details
              </summary>
              <pre className="text-xs mt-1 bg-gray-800 text-white p-2 rounded overflow-x-auto">
                {JSON.stringify(message.query_used, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    );
  };

  const exampleQueries = [
    "How many patients do we have?",
    "Show me male patients",
    "List patients from Boston",
    "What observations do we have?",
    "Show me patients born after 1990"
  ];

  const getSuggestedFollowups = (lastMessage) => {
    if (!lastMessage || lastMessage.role !== 'assistant') return [];
    
    const query = lastMessage.query_used;
    if (!query || !query.resourceType) return [];
    
    const suggestions = [];
    
    if (query.resourceType === 'Patient') {
      suggestions.push("How many of these patients are female?");
      suggestions.push("Show me patients from a different city");
      suggestions.push("What observations do we have for these patients?");
    } else if (query.resourceType === 'Observation') {
      suggestions.push("Show me the patients for these observations");
      suggestions.push("What are the most common observation types?");
    } else if (query.resourceType === 'Condition') {
      suggestions.push("How many patients have this condition?");
      suggestions.push("Show me related observations");
    }
    
    return suggestions.slice(0, 3);
  };

  return (
    <div className="bg-white rounded-lg shadow-md h-[calc(100vh-14rem)] flex flex-col">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-t-lg p-4 border-b">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-xl font-semibold">💬 FHIR Data Assistant</h3>
            <p className="text-sm opacity-90 mt-1">
              Ask questions about patient data, observations, and clinical records
            </p>
          </div>
          {conversationId && (
            <button
              onClick={resetChat}
              className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg text-sm transition-colors"
              title="Clear conversation"
            >
              🗑️ Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
        {chatMessages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-6xl mb-4">💬</div>
            <h4 className="text-lg font-semibold mb-2">Start a conversation</h4>
            <p className="text-sm mb-4">Ask me anything about your FHIR data</p>
            
            <div className="mt-6">
              <p className="text-xs font-semibold text-gray-600 mb-2">Try these examples:</p>
              <div className="space-y-2">
                {exampleQueries.map((query, idx) => (
                  <button
                    key={idx}
                    onClick={() => setChatInput(query)}
                    className="block w-full max-w-md mx-auto text-left px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:bg-amber-50 hover:border-amber-300 transition-colors"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {chatMessages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}
            {chatLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-md">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600"></div>
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Suggested follow-up questions */}
            {chatMessages.length > 0 && !chatLoading && getSuggestedFollowups(chatMessages[chatMessages.length - 1]).length > 0 && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-semibold text-blue-800 mb-2">💡 Try asking:</p>
                <div className="space-y-1">
                  {getSuggestedFollowups(chatMessages[chatMessages.length - 1]).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setChatInput(suggestion)}
                      className="block w-full text-left px-2 py-1 text-xs text-blue-700 hover:bg-blue-100 rounded"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white rounded-b-lg p-4 border-t border-gray-200">
        <form onSubmit={handleChatSubmit}>
          <div className="flex space-x-2">
            <textarea
              ref={textareaRef}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleChatSubmit(e);
                }
              }}
              placeholder="Ask a question... (Press Enter to send, Shift+Enter for new line)"
              className="flex-1 border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200 min-h-[2.5rem] max-h-32"
              rows={2}
              disabled={chatLoading}
              style={{ resize: 'vertical' }}
              maxLength={1000}
            />
            <button
              type="submit"
              disabled={chatLoading || !chatInput.trim()}
              className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
                chatLoading || !chatInput.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-amber-600 hover:bg-amber-700 text-white'
              }`}
            >
              {chatLoading ? '⏳' : '📤'} Send
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            💡 Tip: Ask about patient counts, filter by demographics, or search for specific observations
          </p>
        </form>
      </div>
    </div>
  );
};

export default FHIRChatbot;
