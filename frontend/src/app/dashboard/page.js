'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import NoteUpload from '@/components/NoteUpload';
import ChatInterface from '@/components/ChatInterface';
import ProtectedRoute from '@/components/ProtectedRoute';
import auth from '@/utils/auth';

export default function Dashboard() {
    const [notes, setNotes] = useState([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        // Fetch user's notes
        fetchNotes();
    }, []);

    const fetchNotes = async () => {
        try {
            setLoading(true);
            const response = await auth.api.get('/notes');
            setNotes(response.data);
        } catch (error) {
            console.error('Error fetching notes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleUploadSuccess = (newNote) => {
        setNotes([newNote, ...notes]);
    };

    const handleDeleteNote = (deletedNoteId) => {
        setNotes(notes.filter(note => note.id !== deletedNoteId));
    };

    const handleLogout = () => {
        auth.logout();
    };

    return (
        <ProtectedRoute>
            <div className="min-h-screen bg-gray-50">
                <header className="bg-gradient-to-r from-indigo-600 to-purple-600 shadow-md">
                    <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-white flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 mr-2" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                            </svg>
                            AI Learning Buddy
                        </h1>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 border border-white/20 text-sm font-medium rounded-md text-white bg-white/10 hover:bg-white/20 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </header>

                <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="md:col-span-1">
                            <NoteUpload
                                onUploadSuccess={handleUploadSuccess}
                                notes={notes}
                                onDeleteSuccess={handleDeleteNote}
                            />
                        </div>

                        <div className="md:col-span-2">
                            <ChatInterface />
                        </div>
                    </div>
                </main>

                <footer className="bg-white border-t border-gray-200 mt-10">
                    <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
                        <p className="text-center text-gray-500 text-sm">
                            &copy; {new Date().getFullYear()} AI Learning Buddy. All rights reserved.
                        </p>
                    </div>
                </footer>
            </div>
        </ProtectedRoute>
    );
} 