import React, { useState, useEffect } from 'react';
import { Search, Bell, LayoutGrid, List, Sparkles, Plus, BarChart2, Settings, Newspaper, ChevronDown, LogOut } from 'lucide-react';
import { Canvas } from '@react-three/fiber';
import FluidShader from './FluidShader';
import { PostCard } from './components/PostCard';
import { PostEditor } from './components/PostEditor';
import { NavBar } from './components/NavBar';
import { NewsFeed } from './components/NewsFeed';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { SettingsPage } from './components/SettingsPage';
import { LoginPage } from './components/LoginPage';
import { BlogPost } from './types';
import { api } from './services/api';
import { useAuth } from './context/AuthContext';

const AppContent: React.FC = () => {
  const { user, logout } = useAuth();
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [editingPost, setEditingPost] = useState<BlogPost | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'published' | 'news' | 'analytics' | 'settings'>('dashboard');
  const [topicInput, setTopicInput] = useState('');
  const [showTopicInput, setShowTopicInput] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  // Fetch posts on mount
  useEffect(() => {
    loadPosts();
    
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const loadPosts = async () => {
    try {
      const fetchedPosts = await api.getPosts();
      setPosts(fetchedPosts);
    } catch (error) {
      console.error("Failed to load posts:", error);
    }
  };

  // --- Handlers ---
  const handleEdit = (post: BlogPost) => {
    setEditingPost(post);
  };

  const handleSavePost = async (updatedPost: BlogPost) => {
    try {
      await api.updatePost(updatedPost.id, updatedPost);
      setPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p));
      setEditingPost(null);
    } catch (error) {
      console.error("Failed to save post:", error);
      alert("Failed to save changes.");
    }
  };

  const handleCancelEdit = () => {
    setEditingPost(null);
  };

  const handleApprove = async (id: string, platform: 'devto' | 'hashnode') => {
    try {
      let result;
      if (platform === 'devto') {
          result = await api.publishToDevTo(id);
          alert(`Post published to Dev.to! View it here: ${result.url}`);
      } else {
          result = await api.publishToHashnode(id);
          alert(`Post published to Hashnode! View it here: ${result.url}`);
      }
      
      // 2. Update Local State
      setPosts(prev => prev.map(p => p.id === id ? { ...p, status: 'published' } : p));
      
    } catch (error) {
      console.error(`Failed to publish post to ${platform}:`, error);
      alert(`Failed to publish to ${platform}. Check console for details.`);
    }
  };

  const handleReject = async (id: string) => {
    if (!confirm("Are you sure you want to reject and delete this draft?")) return;
    try {
      await api.deletePost(id);
      setPosts(prev => prev.filter(p => p.id !== id));
    } catch (error) {
      console.error("Failed to reject post:", error);
      alert("Failed to reject post.");
    }
  };

  const handleGenerate = async () => {
    if (!topicInput.trim()) return;
    
    setIsGenerating(true);
    setShowTopicInput(false);
    try {
        const newPost = await api.generatePost(topicInput);
        setPosts(prev => [newPost, ...prev]);
        setTopicInput('');
    } catch (e) {
        console.error(e);
        alert("Failed to generate content. Ensure backend is running.");
    } finally {
        setIsGenerating(false);
    }
  };

  // Filter posts based on active tab
  const displayPosts = posts.filter(p => 
    activeTab === 'dashboard' ? (p.status === 'draft' || p.status === 'needs_review') : p.status === 'published'
  );

  return (
    <div className="relative min-h-screen text-gray-100 font-sans selection:bg-purple-500 selection:text-white">
      
      {/* 3D Background - Fixed */}
      <div className="fixed inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 1] }}>
            <FluidShader />
        </Canvas>
      </div>

      {/* Landing Page Section */}
      <div className="relative z-10 h-screen flex flex-col items-center justify-center pointer-events-none">
        <div 
            id="landing-hero-text" 
            className="text-center will-change-transform flex flex-col items-center justify-center transition-transform duration-75 ease-out"
            style={{
                transform: `scale(${1 + scrollY * 0.002})`,
                opacity: Math.max(0, 1 - scrollY * 0.002)
            }}
        >
           <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-primary text-xs font-semibold uppercase tracking-widest mb-8 backdrop-blur-md animate-pulse">
             <span className="w-1.5 h-1.5 rounded-full font-white bg-primary shadow-[0_0_10px_#6135c8]"></span>
             Future of Content
           </div>
           <h1 className="text-7xl md:text-9xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40 drop-shadow-2xl">
             TrendFlow
           </h1>
           <p className="mt-6 text-lg md:text-xl text-gray-400 max-w-lg mx-auto leading-relaxed font-light tracking-wide">
             Scroll to Enter the Engine
           </p>
           <div className="mt-12 animate-bounce text-white/30">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
               <path d="M7 13l5 5 5-5M7 6l5 5 5-5"/>
             </svg>
           </div>
        </div>
      </div>

      {/* Main App Content - Starts after 100vh */}
      <div className="relative z-20 bg-black min-h-screen shadow-[0_-20px_50px_rgba(0,0,0,0.8)]">
        
        {/* Navigation */}
        <nav className="  bg-black/80 backdrop-blur-md sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center font-bold text-white">
                        T
                    </div>
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        TrendFlow
                    </span>
                </div>
                <div className="hidden md:flex items-center justify-center flex-1 px-8">
                    <NavBar 
                        items={[
                            { name: 'Dashboard', value: 'dashboard', icon: LayoutGrid },
                            { name: 'News Feed', value: 'news', icon: Newspaper },
                            { name: 'Published', value: 'published', icon: List },
                            { name: 'Analytics', value: 'analytics', icon: BarChart2 },
                            { name: 'Settings', value: 'settings', icon: Settings },
                        ]}
                        activeTab={activeTab}
                        onTabChange={(tab: any) => setActiveTab(tab)}
                    />
                </div>

                <div className="flex items-center gap-4">
                    <button className="p-2 text-gray-400 hover:text-white transition-colors">
                        <Search size={20} />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-white transition-colors relative">
                        <Bell size={20} />
                        <span className="absolute top-2 right-2 w-2 h-2 bg-purple-500 rounded-full"></span>
                    </button>
                    <div className="h-8 w-px bg-gray-800 mx-2"></div>
                    <div className="flex items-center gap-3">
                        <img src={user?.picture} alt={user?.name} className="w-8 h-8 rounded-full border border-gray-700" />
                        <button onClick={logout} className="p-2 text-gray-400 hover:text-red-400 transition-colors" title="Logout">
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-10">
            
            {/* Header Action Bar */}
            {activeTab !== 'news' && activeTab !== 'analytics' && activeTab !== 'settings' && (
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                <div>
                    <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-2 tracking-tight">
                        {activeTab === 'dashboard' ? 'Content Dashboard' : 'Published Archives'}
                    </h1>
                    <p className="text-gray-400 text-lg">
                        {activeTab === 'dashboard' 
                            ? 'Manage your AI-generated drafts and trending topics.' 
                            : 'Review performance of live articles.'}
                    </p>
                </div>

                {activeTab === 'dashboard' && (
                    <div className="relative">
                        {showTopicInput ? (
                            <div className="flex items-center gap-2 animate-fade-in">
                                <input 
                                    type="text" 
                                    value={topicInput}
                                    onChange={(e) => setTopicInput(e.target.value)}
                                    placeholder="Enter a topic..."
                                    className="h-12 px-4 rounded-full bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-purple-500 w-64"
                                    onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                                />
                                <button 
                                    onClick={handleGenerate}
                                    disabled={isGenerating}
                                    className="h-12 px-6 rounded-full font-bold text-white bg-purple-600 hover:bg-purple-500 transition-colors disabled:opacity-50"
                                >
                                    {isGenerating ? 'Generating...' : 'Go'}
                                </button>
                                <button 
                                    onClick={() => setShowTopicInput(false)}
                                    className="p-3 text-gray-400 hover:text-white"
                                >
                                    ✕
                                </button>
                            </div>
                        ) : (
                            <button 
                                onClick={() => setShowTopicInput(true)}
                                disabled={isGenerating}
                                className={`
                                    h-12 px-6 rounded-full font-bold text-white shadow-lg shadow-purple-900/40 
                                    flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95
                                    ${isGenerating ? 'bg-gray-800 cursor-wait' : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500'}
                                `}
                            >
                                {isGenerating ? (
                                    <>
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        <span>Generating Agent...</span>
                                    </>
                                ) : (
                                    <>
                                        <Plus size={20} />
                                        <span>New AI Draft</span>
                                    </>
                                )}
                            </button>
                        )}
                    </div>
                )}
            </div>
            )}

            {/* Content Grid */}
            {activeTab === 'news' ? (
                <NewsFeed />
            ) : activeTab === 'analytics' ? (
                <AnalyticsDashboard />
            ) : activeTab === 'settings' ? (
                <SettingsPage />
            ) : (
            <>
            {/* Filters / View Toggle (Visual Only) */}
            <div className="flex items-center justify-between mb-8 border-b border-gray-800 pb-4">
                <div className="flex items-center gap-4">
                    <span className="text-sm font-semibold text-white">{displayPosts.length} Articles</span>
                    <div className="h-4 w-px bg-gray-800"></div>
                    <select className="bg-transparent text-sm text-gray-400 focus:outline-none cursor-pointer hover:text-white">
                        <option>All Categories</option>
                        <option>Tech</option>
                        <option>Finance</option>
                    </select>
                    <select className="bg-transparent text-sm text-gray-400 focus:outline-none cursor-pointer hover:text-white">
                        <option>Newest First</option>
                        <option>Viral Score</option>
                    </select>
                </div>
                <div className="flex items-center gap-2 bg-gray-900 rounded-lg p-1">
                    <button className="p-1.5 rounded bg-gray-800 text-white shadow-sm"><LayoutGrid size={16}/></button>
                    <button className="p-1.5 rounded text-gray-500 hover:text-white"><List size={16}/></button>
                </div>
            </div>

            {/* Grid */}
            {displayPosts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center border-2 border-dashed border-gray-800 rounded-3xl">
                    <div className="w-16 h-16 bg-gray-900 rounded-full flex items-center justify-center mb-4">
                        <Sparkles className="text-gray-600" size={24} />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">No drafts found</h3>
                    <p className="text-gray-500 max-w-sm">
                        {activeTab === 'dashboard' 
                            ? "Ready to create? Click 'New AI Draft' to let the agents work their magic." 
                            : "No published articles yet. Approve a draft to see it here."}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {displayPosts.map(post => (
                        <PostCard 
                            key={post.id} 
                            post={post} 
                            onEdit={handleEdit}
                            onApprove={handleApprove}
                            onReject={handleReject}
                        />
                    ))}
                </div>
            )}
            </>
            )}

        </main>

        {/* Editor Modal */}
        {editingPost && (
            <PostEditor 
                post={editingPost} 
                onSave={handleSavePost}
                onCancel={handleCancelEdit} 
            />
        )}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <AppContent />
  );
};

export default App;