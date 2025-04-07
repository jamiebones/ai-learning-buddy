'use client';

import { useState } from 'react';
import axios from 'axios';
import { DocumentPlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import auth from '@/utils/auth';

export default function NoteUpload({ onUploadSuccess, notes = [], onDeleteSuccess }) {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [deleteInProgress, setDeleteInProgress] = useState(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        // Check file type
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        if (selectedFile && validTypes.includes(selectedFile.type)) {
            setFile(selectedFile);
            setError('');
        } else {
            setFile(null);
            setError('Please select a PDF, DOCX, or TXT file');
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Create a custom axios instance for form data
            const response = await axios.post(
                `${process.env.NEXT_PUBLIC_API_URL}/notes/upload`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'Authorization': `Bearer ${auth.getToken()}`
                    }
                }
            );

            setUploading(false);
            setFile(null);
            // Reset the file input element
            const fileInput = document.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.value = '';
            }
            if (onUploadSuccess) {
                onUploadSuccess(response.data);
            }
        } catch (err) {
            setUploading(false);
            // Get a more specific error message if available
            const errorMessage = err.response?.data?.message ||
                err.response?.data?.error ||
                err.message ||
                'Failed to upload file';
            setError(errorMessage);
            console.error('Upload error:', err);
        }
    };

    const handleDeleteNote = async (noteId) => {
        try {
            setDeleteInProgress(noteId);
            await auth.api.delete(`/notes/${noteId}`);
            if (onDeleteSuccess) {
                onDeleteSuccess(noteId);
            }
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Failed to delete note';
            setError(errorMessage);
            console.error('Delete error:', err);
        } finally {
            setDeleteInProgress(null);
        }
    };

    return (
        <div className="space-y-6">
            {/* Upload section */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4">
                    <h2 className="text-lg font-semibold flex items-center">
                        <DocumentPlusIcon className="h-5 w-5 mr-2" />
                        Upload Study Notes
                    </h2>
                </div>

                <div className="p-4">
                    {error && (
                        <div className="mb-4 bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded">
                            <p className="font-medium">Error</p>
                            <p className="text-sm">{error}</p>
                        </div>
                    )}

                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2">
                            Select a file (PDF, DOCX, or TXT)
                        </label>
                        <input
                            type="file"
                            onChange={handleFileChange}
                            className="w-full text-gray-700 p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                        />
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className={`w-full py-2 px-4 rounded flex items-center justify-center ${!file || uploading
                            ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                            : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                            }`}
                    >
                        {uploading ? (
                            <>
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Uploading...
                            </>
                        ) : (
                            'Upload Note'
                        )}
                    </button>
                </div>
            </div>

            {/* Notes list section */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="bg-gray-100 p-4 border-b">
                    <h2 className="text-lg font-semibold text-gray-800">Your Notes</h2>
                </div>

                <div className="divide-y divide-gray-200">
                    {notes.length === 0 ? (
                        <p className="text-gray-500 p-4 text-center">You haven&apos;t uploaded any notes yet.</p>
                    ) : (
                        notes.map((note) => (
                            <div key={note.id} className="p-4 flex justify-between items-center hover:bg-gray-50">
                                <div>
                                    <h3 className="font-medium text-gray-800">{note.file_name}</h3>
                                    <p className="text-sm text-gray-500">
                                        {new Date(note.upload_date).toLocaleDateString()} • {(note.note_text.length / 1000).toFixed(1)}K characters
                                    </p>
                                </div>
                                <button
                                    onClick={() => handleDeleteNote(note.id)}
                                    disabled={deleteInProgress === note.id}
                                    className="text-red-500 hover:text-red-700 p-2 rounded-full hover:bg-red-50 transition-colors"
                                    aria-label="Delete note"
                                >
                                    {deleteInProgress === note.id ? (
                                        <svg className="animate-spin h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                    ) : (
                                        <TrashIcon className="h-5 w-5" />
                                    )}
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
} 