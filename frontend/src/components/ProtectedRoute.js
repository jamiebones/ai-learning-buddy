'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import auth from '@/utils/auth';

export default function ProtectedRoute({ children }) {
    const router = useRouter();
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Check authentication status
        const checkAuth = () => {
            if (auth.isAuthenticated()) {
                setIsAuthenticated(true);
            } else {
                router.push('/login');
            }
            setIsLoading(false);
        };

        checkAuth();
    }, [router]);

    // Show loading state while checking authentication
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-50">
                <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    // Render children only if authenticated
    return isAuthenticated ? children : null;
} 