import React, { useState, useEffect } from 'react';
import { BlogPost } from '../types';
import { Save, X, ArrowLeft, Wand2, Target, MessageSquare, BrainCircuit, Search, Image as ImageIcon } from 'lucide-react';

interface PostEditorProps {
  post: BlogPost;
  onSave: (updatedPost: BlogPost) => void;
  onCancel: () => void;
}

export const PostEditor: React.FC<PostEditorProps> = ({ post, onSave, onCancel }) => {
  const [editedPost, setEditedPost] = useState<BlogPost>(post);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'content' | 'seo' | 'critique'>('content');

  // Reset state when post changes
  useEffect(() => {
    setEditedPost(post);
  }, [post]);

  const handleChange = (field: keyof BlogPost, value: any) => {
    setEditedPost(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
        await onSave(editedPost);
    } catch (error) {
        console.error("Failed to save post", error);
    } finally {
        setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col animate-fade-in">
        {/* Editor Header */}
        <div className="h-16 border-b border-gray-800 flex items-center justify-between px-6 bg-gray-900/50 backdrop-blur-md">
            <div className="flex items-center gap-4">
                <button 
                    onClick={onCancel}
                    className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors"
                >
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        Edit Draft 
                        {editedPost.sentiment && (
                            <span className={`text-[10px] px-2 py-0.5 rounded border ${editedPost.sentiment === 'Positive' ? 'border-green-800 text-green-400' : 'border-gray-700 text-gray-400'}`}>
                                {editedPost.sentiment} Sentiment
                            </span>
                        )}
                    </h2>
                </div>
            </div>
            
            <div className="flex items-center gap-3">
                 <div className="flex bg-gray-800 rounded-lg p-1 mr-4">
                    <button 
                        onClick={() => setActiveTab('content')}
                        className={`px-3 py-1 text-xs font-medium rounded ${activeTab === 'content' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        Content
                    </button>
                    <button 
                        onClick={() => setActiveTab('seo')}
                        className={`px-3 py-1 text-xs font-medium rounded ${activeTab === 'seo' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        SEO & Metadata
                    </button>
                    <button 
                        onClick={() => setActiveTab('critique')}
                        className={`px-3 py-1 text-xs font-medium rounded ${activeTab === 'critique' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        Agent Feedback
                    </button>
                 </div>

                <button 
                    onClick={onCancel}
                    className="px-4 py-2 text-sm text-gray-400 hover:text-white font-medium"
                >
                    Cancel
                </button>
                <button 
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex items-center gap-2 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-full text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSaving ? 'Saving...' : <><Save size={16} /> Save & Close</>}
                </button>
            </div>
        </div>

        {/* Editor Layout */}
        <div className="flex-1 flex overflow-hidden">
            
            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full">
                
                {activeTab === 'content' && (
                    <div className="space-y-6">
                        {/* Cover Image Preview */}
                        <div className="relative h-64 w-full rounded-2xl overflow-hidden group border border-gray-800">
                            <img 
                                src={editedPost.imageUrl} 
                                alt="Cover" 
                                className="w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity"
                            />
                            <div className="absolute top-4 left-4 bg-black/70 backdrop-blur px-3 py-2 rounded-lg max-w-md">
                                <span className="text-xs text-gray-400 block mb-1 uppercase tracking-wider flex items-center gap-1"><ImageIcon size={10}/> Image Prompt</span>
                                <p className="text-xs text-white line-clamp-2 italic">{editedPost.imagePrompt || "No prompt available"}</p>
                            </div>
                        </div>

                        {/* Title Input */}
                        <input 
                            type="text" 
                            value={editedPost.title}
                            onChange={(e) => handleChange('title', e.target.value)}
                            className="w-full bg-transparent text-4xl font-extrabold text-white placeholder-gray-600 border-none outline-none focus:ring-0 px-0"
                            placeholder="Article Title..."
                        />

                        {/* Excerpt */}
                        <div>
                            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Excerpt</label>
                            <textarea 
                                value={editedPost.excerpt}
                                onChange={(e) => handleChange('excerpt', e.target.value)}
                                rows={3}
                                className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-gray-300 focus:border-purple-500 focus:outline-none transition-colors resize-none"
                            />
                        </div>

                        {/* Main Content Body */}
                        <div className="pt-4 border-t border-gray-800">
                            <label className="block text-xs font-semibold text-purple-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <Wand2 size={14}/> AI Generated Content (Markdown)
                            </label>
                            <textarea 
                                value={editedPost.content}
                                onChange={(e) => handleChange('content', e.target.value)}
                                className="w-full h-[600px] bg-transparent text-lg text-gray-300 leading-relaxed border-none outline-none focus:ring-0 resize-none p-0 font-serif"
                                placeholder="Start writing..."
                            />
                        </div>
                    </div>
                )}

                {activeTab === 'seo' && (
                    <div className="space-y-8 animate-fade-in">
                        <h3 className="text-2xl font-bold text-white mb-6">SEO & Metadata</h3>
                        
                        <div className="grid grid-cols-2 gap-6">
                            <div className="bg-gray-900 p-5 rounded-xl border border-gray-800">
                                <label className="flex items-center gap-2 text-sm font-bold text-gray-400 mb-3">
                                    <Target size={16} className="text-purple-500"/> Target Audience
                                </label>
                                <input 
                                    type="text"
                                    value={editedPost.targetAudience || ''}
                                    onChange={(e) => handleChange('targetAudience', e.target.value)}
                                    className="w-full bg-black/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                                />
                            </div>
                            <div className="bg-gray-900 p-5 rounded-xl border border-gray-800">
                                <label className="flex items-center gap-2 text-sm font-bold text-gray-400 mb-3">
                                    <Search size={16} className="text-blue-500"/> SEO Keywords
                                </label>
                                <input 
                                    type="text"
                                    value={editedPost.seoKeywords?.join(', ') || ''}
                                    onChange={(e) => handleChange('seoKeywords', e.target.value.split(',').map(s => s.trim()))}
                                    className="w-full bg-black/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                                    placeholder="AI, Tech, Future..."
                                />
                            </div>
                        </div>

                        <div className="bg-gray-900 p-5 rounded-xl border border-gray-800">
                            <label className="block text-sm font-bold text-gray-400 mb-3">Meta Description (Google Snippet)</label>
                            <textarea 
                                value={editedPost.metaDescription || ''}
                                onChange={(e) => handleChange('metaDescription', e.target.value)}
                                rows={3}
                                className="w-full bg-black/50 border border-gray-700 rounded-lg px-3 py-2 text-gray-300 focus:outline-none focus:border-purple-500"
                            />
                            <p className="text-xs text-gray-500 mt-2 text-right">{editedPost.metaDescription?.length || 0} / 160 characters</p>
                        </div>
                    </div>
                )}

                {activeTab === 'critique' && (
                     <div className="space-y-6 animate-fade-in">
                        <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 p-6 rounded-xl border border-purple-500/20">
                            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                <BrainCircuit className="text-purple-400" /> Agent Critique & Logic
                            </h3>
                            <div className="prose prose-invert prose-sm max-w-none">
                                <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                                    {editedPost.critiqueNotes || "No critique available for this draft."}
                                </p>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-gray-900 p-4 rounded-lg border border-gray-800 text-center">
                                <div className="text-gray-500 text-xs uppercase font-bold mb-1">Revisions</div>
                                <div className="text-2xl font-bold text-white">2</div>
                            </div>
                             <div className="bg-gray-900 p-4 rounded-lg border border-gray-800 text-center">
                                <div className="text-gray-500 text-xs uppercase font-bold mb-1">Fact Check</div>
                                <div className="text-2xl font-bold text-green-400">Pass</div>
                            </div>
                             <div className="bg-gray-900 p-4 rounded-lg border border-gray-800 text-center">
                                <div className="text-gray-500 text-xs uppercase font-bold mb-1">Tone</div>
                                <div className="text-lg font-bold text-white truncate">{editedPost.sentiment}</div>
                            </div>
                        </div>
                     </div>
                )}
            </div>

            {/* Right Sidebar - Analytics/Settings */}
            <div className="w-80 border-l border-gray-800 bg-gray-900/30 p-6 hidden xl:block">
                <h3 className="text-sm font-bold text-white mb-6 uppercase tracking-wider">Live Analytics</h3>
                
                <div className="space-y-6">
                    <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
                        <div className="flex justify-between items-end mb-2">
                            <span className="text-gray-400 text-sm">Viral Prediction</span>
                            <span className={`text-2xl font-bold ${editedPost.viralScore > 80 ? 'text-green-400' : 'text-yellow-400'}`}>
                                {editedPost.viralScore}
                            </span>
                        </div>
                        <div className="w-full bg-gray-800 rounded-full h-1.5">
                            <div 
                                className={`h-1.5 rounded-full ${editedPost.viralScore > 80 ? 'bg-green-400' : 'bg-yellow-400'}`} 
                                style={{ width: `${editedPost.viralScore}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
                        <div className="flex justify-between items-center mb-4">
                            <span className="text-gray-400 text-sm">Readability</span>
                            <span className="text-xs font-bold bg-gray-800 px-2 py-1 rounded text-white">
                                {editedPost.readingTimeMin ? `${editedPost.readingTimeMin} min read` : 'N/A'}
                            </span>
                        </div>
                         <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">SEO Score</span>
                            <span className="text-xs font-bold bg-green-900/30 text-green-400 px-2 py-1 rounded border border-green-900">Good</span>
                        </div>
                    </div>

                     <div className="p-4 rounded-xl border border-dashed border-gray-700 text-center">
                        <p className="text-xs text-gray-500 mb-2">Targeting</p>
                        <p className="text-sm font-medium text-purple-300">
                            {editedPost.targetAudience || "General Tech"}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
  );
};