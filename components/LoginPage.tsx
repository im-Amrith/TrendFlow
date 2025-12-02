import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import { Canvas } from '@react-three/fiber';
import FluidShader from '../FluidShader';
import { Sparkles } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();

  const handleSuccess = async (credentialResponse: any) => {
    try {
      const res = await fetch('http://localhost:8000/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });

      if (!res.ok) throw new Error('Login failed');

      const data = await res.json();
      login(data.access_token, data.user);
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
                    <GoogleLogin
                        onSuccess={handleSuccess}
                        onError={() => {
                            console.log('Login Failed');
                        }}
                        theme="filled_black"
                        shape="pill"
                        size="large"
                        width="300"
                    />
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
