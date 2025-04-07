'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import auth from '@/utils/auth';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // If user is already authenticated, redirect to dashboard
    if (auth.isAuthenticated()) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-indigo-50">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="text-2xl font-bold text-indigo-600">AI Study Buddy</div>
          <div className="space-x-4 hidden md:flex">
            <Link href="/login" className="text-gray-600 hover:text-indigo-600">Sign In</Link>
            <Link
              href="/register"
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition"
            >
              Register
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-12 md:py-24 flex flex-col md:flex-row items-center">
        <div className="md:w-1/2 md:pr-10">
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-800 leading-tight mb-6">
            Study Smarter, <span className="text-indigo-600">Not Harder</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Transform your notes into an interactive AI study companion that helps you understand concepts, prepare for exams, and master your coursework.
          </p>
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
            <Link
              href="/register"
              className="bg-indigo-600 text-white text-center px-8 py-3 rounded-md hover:bg-indigo-700 transition shadow-lg"
            >
              Get Started Free
            </Link>
            <Link
              href="#how-it-works"
              className="border border-indigo-600 text-indigo-600 text-center px-8 py-3 rounded-md hover:bg-indigo-50 transition"
            >
              How It Works
            </Link>
          </div>
        </div>
        <div className="md:w-1/2 mt-12 md:mt-0">
          <div className="bg-white p-4 rounded-lg shadow-xl transform rotate-2">
            <div className="bg-indigo-600 rounded-md p-6 text-white">
              <div className="flex justify-between items-center mb-6">
                <div className="font-bold">AI Study Buddy</div>
                <div className="text-xs bg-indigo-500 px-2 py-1 rounded">Online</div>
              </div>
              <div className="space-y-4">
                <div className="bg-indigo-500 p-3 rounded-lg rounded-tl-none max-w-xs">
                  How do photosynthesis and cellular respiration relate to each other?
                </div>
                <div className="bg-white text-gray-800 p-3 rounded-lg rounded-tr-none ml-auto max-w-sm">
                  Photosynthesis and cellular respiration are complementary processes. Photosynthesis converts light energy, CO₂ and water into glucose and oxygen, while cellular respiration uses glucose and oxygen to produce energy (ATP), CO₂ and water.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-12">Why Students Love AI Study Buddy</h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 bg-indigo-50 rounded-lg">
              <div className="w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Upload Any Document</h3>
              <p className="text-gray-600">Easily upload your PDF, DOCX, or TXT study materials and transform them into interactive knowledge.</p>
            </div>

            <div className="p-6 bg-indigo-50 rounded-lg">
              <div className="w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Smart Conversations</h3>
              <p className="text-gray-600">Ask questions in natural language and get accurate, contextual answers based on your notes.</p>
            </div>

            <div className="p-6 bg-indigo-50 rounded-lg">
              <div className="w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Study Insights</h3>
              <p className="text-gray-600">Get helpful explanations, summaries, and connections between concepts that enhance your understanding.</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-16">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-12">How AI Study Buddy Works</h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">1</div>
              <h3 className="text-xl font-semibold mb-2">Upload Your Notes</h3>
              <p className="text-gray-600">Upload your study materials in PDF, DOCX, or TXT format to your personal dashboard.</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">2</div>
              <h3 className="text-xl font-semibold mb-2">AI Processing</h3>
              <p className="text-gray-600">Our AI analyzes your notes, extracting key concepts and creating connections between ideas.</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">3</div>
              <h3 className="text-xl font-semibold mb-2">Start Learning</h3>
              <p className="text-gray-600">Ask questions, get explanations, and deepen your understanding through interactive conversation.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="bg-indigo-600 text-white py-16">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">What Students Are Saying</h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-indigo-700 p-6 rounded-lg">
              <p className="mb-4 italic">AI Study Buddy helped me understand complex concepts in my biochemistry class that I was struggling with for weeks!</p>
              <div className="font-semibold">- Emily S., Biology Major</div>
            </div>

            <div className="bg-indigo-700 p-6 rounded-lg">
              <p className="mb-4 italic">Being able to ask questions about my own lecture notes saved me hours of searching through textbooks and online resources.</p>
              <div className="font-semibold">- Jason T., Computer Science Student</div>
            </div>

            <div className="bg-indigo-700 p-6 rounded-lg">
              <p className="mb-4 italic">The way AI Study Buddy connects different topics together helped me see the bigger picture in my psychology course.</p>
              <div className="font-semibold">- Maria L., Psychology Student</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Ready to Transform Your Study Experience?</h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">Join thousands of students who are studying smarter with AI Study Buddy.</p>
          <Link
            href="/register"
            className="bg-indigo-600 text-white px-8 py-3 rounded-md hover:bg-indigo-700 transition shadow-lg text-lg"
          >
            Get Started Free
          </Link>
          <p className="mt-4 text-gray-500">No credit card required • Free 14-day trial</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-12">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-6 md:mb-0">
              <div className="text-2xl font-bold">AI Study Buddy</div>
              <div className="text-gray-400 mt-2">© {new Date().getFullYear()} All Rights Reserved</div>
            </div>
            <div className="flex space-x-6">
              <Link href="/about" className="hover:text-indigo-300">About</Link>
              <Link href="/privacy" className="hover:text-indigo-300">Privacy</Link>
              <Link href="/terms" className="hover:text-indigo-300">Terms</Link>
              <Link href="/contact" className="hover:text-indigo-300">Contact</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
} 