import axios from 'axios';

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(promise => {
        if (error) {
            promise.reject(error);
        } else {
            promise.resolve(token);
        }
    });

    failedQueue = [];
};

// Axios instance for API calls
const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    timeout: 120000, // Increase timeout to 120 seconds (2 minutes)
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor
api.interceptors.request.use(
    (config) => {
        // Get token from localStorage
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add response interceptor
api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;
        // If error is not 401 or the request already tried to refresh, reject
        if (error.response?.status !== 401 || originalRequest._retry) {
            return Promise.reject(error);
        }

        if (isRefreshing) {
            // If already refreshing, add the request to the queue
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then(token => {
                    originalRequest.headers['Authorization'] = `Bearer ${token}`;
                    return api(originalRequest);
                })
                .catch(err => {
                    return Promise.reject(err);
                });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        // Get refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
            // No refresh token, redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');

            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }

            return Promise.reject(new Error('No refresh token available'));
        }

        try {
            // Attempt to refresh the token
            const res = await axios.post(
                `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`,
                { refresh_token: refreshToken }
            );

            // Update tokens in localStorage
            const { access_token, refresh_token } = res.data;
            localStorage.setItem('token', access_token);
            localStorage.setItem('refreshToken', refresh_token);

            // Update auth header for the original request
            originalRequest.headers['Authorization'] = `Bearer ${access_token}`;

            // Process any requests that were waiting
            processQueue(null, access_token);

            return api(originalRequest);
        } catch (err) {
            // Failed to refresh token
            processQueue(err, null);

            // Clear tokens and redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');

            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }

            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);

// Auth utilities
const auth = {
    isAuthenticated() {
        if (typeof window === 'undefined') return false;
        return !!localStorage.getItem('token');
    },

    login(token, refreshToken) {
        localStorage.setItem('token', token);
        localStorage.setItem('refreshToken', refreshToken);
    },

    logout() {
        return api.post('/auth/logout')
            .finally(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('refreshToken');
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
            });
    },

    getToken() {
        return localStorage.getItem('token');
    },

    // Use this instance for API calls
    api: api
};

export default auth; 