import './globals.css';

export const metadata = {
    title: 'AI Study Buddy',
    description: 'Upload notes, chat with AI, and improve your study experience',
};

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
} 