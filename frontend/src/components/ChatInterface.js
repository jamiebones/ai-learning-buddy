'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { PlusIcon, TrashIcon, ArrowSmallRightIcon } from '@heroicons/react/24/outline';
import auth from '@/utils/auth';

export default function ChatInterface() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessions, setSessions] = useState([]);
    const [currentSession, setCurrentSession] = useState(null);
    const messagesEndRef = useRef(null);
    const [showSessionList, setShowSessionList] = useState(false);

    // Load chat sessions on component mount
    useEffect(() => {
        fetchChatSessions();
    }, []);

    // Load chat messages when session changes
    useEffect(() => {
        if (currentSession) {
            fetchChatHistory(currentSession.id);
        } else {
            setMessages([]);
        }
    }, [currentSession]);

    // Scroll to bottom whenever messages change
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchChatSessions = async () => {
        try {
            const response = await auth.api.get('/chat/sessions');
            setSessions(response.data);

            // Set current session to most recent if available
            if (response.data.length > 0) {
                setCurrentSession(response.data[0]);
            }
        } catch (err) {
            console.error('Failed to fetch chat sessions:', err);
        }
    };

    const fetchChatHistory = async (sessionId) => {
        try {
            setLoading(true);
            const response = await auth.api.get('/chat/history', {
                params: { session_id: sessionId }
            });

            // Process chat history - for each message in the backend, create a user message and AI response pair
            const processedMessages = [];
            response.data.forEach(msg => {
                // Add user message
                processedMessages.push({
                    id: msg.id + "-user",
                    message: msg.message,
                    isUser: true,
                    timestamp: msg.timestamp
                });

                // Process AI response to extract thinking
                const { mainResponse, thinking } = formatMessageContent(msg.response);

                // Add AI response with thinking extracted
                processedMessages.push({
                    id: msg.id,
                    message: mainResponse,
                    response: msg.response,
                    thinking: thinking,
                    isUser: false,
                    timestamp: msg.timestamp,
                    sources: msg.source_documents
                });
            });

            setMessages(processedMessages);
        } catch (err) {
            console.error('Failed to fetch chat history:', err);
        } finally {
            setLoading(false);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Format message content to separate thinking process (<think> tags)
    const formatMessageContent = (content) => {
        if (!content) {
            return { mainResponse: "No response received", thinking: "" };
        }

        // Extract thinking part from <think> tags
        const thinkMatch = content && typeof content === 'string' ? content.match(/<think>([\s\S]*?)<\/think>/i) : null;

        if (thinkMatch) {
            // Extract thinking process
            const thinking = thinkMatch[1].trim();

            // Remove thinking part from the main response
            const mainResponse = content.replace(/<think>[\s\S]*?<\/think>/i, '').trim();

            return { mainResponse, thinking };
        }

        // No think tags found, just return the content as is
        return { mainResponse: content, thinking: '' };
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        // Store the user message text
        const userMessageText = input;

        // Add user message to chat
        const userMessage = { message: userMessageText, isUser: true };
        setMessages(prevMessages => [...prevMessages, userMessage]);
        setInput('');
        setLoading(true);

        try {
            // Send the message to the API
            const response = await auth.api.post('/chat/send', {
                message: userMessageText,
                session_id: currentSession?.id
            });

            // If this was a new session, refresh sessions list
            if (!currentSession) {
                await fetchChatSessions();
                setCurrentSession({
                    id: response.data.session_id
                });
            }

            // Safely process the response data
            if (!response.data) {
                throw new Error("Empty response from server");
            }

            // Create message objects - do this outside of setState for clarity
            const userMessageFormatted = {
                id: `${Date.now()}-user`,
                message: userMessageText,
                isUser: true
            };

            // Process the response to extract thinking and main response
            const { mainResponse, thinking } = formatMessageContent(response.data.response);

            const aiMessageFormatted = {
                id: `${Date.now()}-ai`,
                message: mainResponse, // Store formatted main response
                response: response.data.response, // Store original response with think tags
                thinking: thinking, // Store extracted thinking
                isUser: false,
                sources: response.data.source_documents || []
            };

            // Use a functional update to ensure we're working with the latest state
            setMessages(prevMessages => {
                // Filter out the temporary user message
                const filteredMessages = prevMessages.filter(msg =>
                    !(msg.isUser && msg.message === userMessageText && !msg.id)
                );

                // Add the formatted messages
                return [...filteredMessages, userMessageFormatted, aiMessageFormatted];
            });

        } catch (error) {
            console.error("Error sending message:", error);

            // Show error message but keep user message
            setMessages(prevMessages => {
                // Keep all previous messages except the temporary one
                const filteredMessages = prevMessages.filter(msg =>
                    !(msg.isUser && msg.message === userMessageText && !msg.id)
                );

                // Add back user message with an ID and the error message
                return [
                    ...filteredMessages,
                    {
                        id: `${Date.now()}-user`,
                        message: userMessageText,
                        isUser: true
                    },
                    {
                        id: `${Date.now()}-error`,
                        message: "Sorry, there was an error processing your request. Please try again.",
                        isUser: false
                    }
                ];
            });
        } finally {
            setLoading(false);
        }
    };

    const createNewSession = async () => {
        try {
            const response = await auth.api.post('/chat/session', {
                name: `Chat ${new Date().toLocaleString()}`
            });
            // Refresh sessions and set current to new one
            await fetchChatSessions();
            setCurrentSession(response.data);
            setMessages([]);
        } catch (err) {
            console.error('Failed to create new session:', err);
        }
    };

    const deleteSession = async (sessionId) => {
        try {
            await auth.api.delete(`/chat/session/${sessionId}`);

            // Refresh sessions
            await fetchChatSessions();

            // If we deleted the current session, clear messages
            if (currentSession?.id === sessionId) {
                setCurrentSession(null);
                setMessages([]);
            }
        } catch (err) {
            console.error('Failed to delete session:', err);
        }
    };

    // MessageItem component to display user messages and AI responses with thinking
    const MessageItem = ({ msg }) => {
        return (
            <div className={`mb-4 ${msg.isUser ? 'text-right' : 'text-left'}`}>
                {msg.isUser ? (
                    <div className="inline-block p-3 rounded-lg max-w-[80%] shadow-sm bg-indigo-600 text-white rounded-br-none">
                        {msg.message}
                    </div>
                ) : (
                    <>
                        {/* Model thinking process shown first */}
                        {msg.thinking && (
                            <div className="mb-2 bg-yellow-50 border-l-4 border-yellow-400 p-2 rounded-r text-left text-sm text-gray-700 font-mono">
                                <div className="font-medium text-yellow-600 mb-1">Model Thinking:</div>
                                <div className="whitespace-pre-wrap">{msg.thinking}</div>
                            </div>
                        )}

                        {/* Model response shown after thinking */}
                        <div className="inline-block p-3 rounded-lg max-w-[80%] shadow-sm bg-white text-gray-800 rounded-bl-none">
                            {msg.message}
                        </div>
                    </>
                )}

                {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 text-xs text-left">
                        <details className="ml-2 text-gray-600 bg-gray-100 rounded p-2">
                            <summary className="cursor-pointer font-medium">
                                Source Documents ({msg.sources.length})
                            </summary>
                            <ul className="mt-2 space-y-2">
                                {msg.sources.map((src, i) => (
                                    <li key={i} className="bg-white p-2 rounded border border-gray-200">
                                        <div className="line-clamp-3">
                                            {src.content.substring(0, 150)}...
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </details>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col h-[700px] bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
            {/* Header with session control */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-semibold">
                        {currentSession ? (currentSession.name || 'Chat Session') : 'New Chat'}
                    </h2>
                    <button
                        onClick={() => setShowSessionList(!showSessionList)}
                        className="p-1 rounded hover:bg-white/20 transition-colors"
                        aria-label="Toggle session list"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                    </button>
                </div>
                <button
                    onClick={createNewSession}
                    className="flex items-center space-x-1 bg-white/10 hover:bg-white/20 text-white px-3 py-1 rounded-full text-sm transition-colors"
                >
                    <PlusIcon className="h-4 w-4" />
                    <span>New Chat</span>
                </button>
            </div>

            {/* Session dropdown */}
            {showSessionList && (
                <div className="bg-white border-b border-gray-200 max-h-60 overflow-y-auto">
                    <ul className="divide-y divide-gray-100">
                        {sessions.length === 0 ? (
                            <li className="p-4 text-gray-500 text-center">No previous chat sessions</li>
                        ) : (
                            sessions.map(session => (
                                <li
                                    key={session.id}
                                    className={`flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 transition-colors
                                        ${currentSession?.id === session.id ? 'bg-indigo-50' : ''}`}
                                    onClick={() => {
                                        setCurrentSession(session);
                                        setShowSessionList(false);
                                    }}
                                >
                                    <span className="text-gray-800 truncate flex-1">
                                        {session.name || `Chat ${new Date(session.created_at).toLocaleString()}`}
                                    </span>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteSession(session.id);
                                        }}
                                        className="text-red-500 hover:text-red-700 p-1"
                                        aria-label="Delete session"
                                    >
                                        <TrashIcon className="h-4 w-4" />
                                    </button>
                                </li>
                            ))
                        )}
                    </ul>
                </div>
            )}

            {/* Chat messages */}
            <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                        <p className="text-lg">Start a new conversation</p>
                        <p className="text-sm mt-2">Ask about your notes or any other questions</p>
                    </div>
                ) : (
                    messages.map((msg, index) => {
                        // Generate a stable unique key for each message
                        const messageKey = msg.id || `msg-${index}-${msg.isUser ? 'user' : 'ai'}`;

                        return (
                            <MessageItem
                                key={messageKey}
                                msg={msg}
                            />
                        );
                    })
                )}

                {loading && (
                    <div className="text-left mb-4">
                        <div className="inline-block bg-white text-gray-800 p-3 rounded-lg rounded-bl-none shadow-sm">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></div>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Message input */}
            <form onSubmit={handleSendMessage} className="border-t p-4 bg-white">
                <div className="flex items-center rounded-full border border-gray-300 bg-gray-50 focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-indigo-500 overflow-hidden">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={currentSession ? "Ask a question..." : "Start a new conversation..."}
                        className="flex-1 border-none bg-transparent px-4 py-3 focus:outline-none text-gray-800"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className={`p-3 rounded-full ${loading || !input.trim()
                            ? 'text-gray-400 cursor-not-allowed'
                            : 'text-white bg-indigo-600 hover:bg-indigo-700'
                            } transition-colors mr-1`}
                        aria-label="Send message"
                    >
                        <ArrowSmallRightIcon className="h-5 w-5" />
                    </button>
                </div>
            </form>
        </div>
    );
} 