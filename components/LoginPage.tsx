import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Canvas } from '@react-three/fiber';
import FluidShader from '../FluidShader';
import { Sparkles } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();

  const handleLogin = async () => {
    try {
      await login();
    } catch (error) {
      console.error('Login Error:', error);
      alert('Login failed. Please try again.');
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-black overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 z-0 opacity-50">
        <Canvas camera={{ position: [0, 0, 1] }}>
            <FluidShader />
        </Canvas>
      </div>

      <div className="relative z-10 w-full max-w-md p-8">
        <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-purple-500/30">
                <span className="text-3xl font-bold text-white">T</span>
            </div>
            
            <h1 className="text-4xl font-black text-white mb-2 tracking-tight">TrendFlow</h1>
            <p className="text-gray-400 mb-8 text-lg">Your AI-Powered Content Engine</p>

            <div className="space-y-6">
                <div className="flex justify-center">
                    <button
                        onClick={handleLogin}
                        className="flex items-center gap-3 bg-white text-black px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition-colors"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        Sign in with Google
                    </button>
                </div>
                
                <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                    <Sparkles size={14} />
                    <span>Join creators automating their growth</span>
                </div>
            </div>
        </div>
        
        <p className="text-center text-gray-600 text-xs mt-8">
            By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
};
