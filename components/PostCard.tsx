import React from 'react';
import { BlogPost } from '../types';
import { Edit2, CheckCircle, TrendingUp, Eye, Clock, Activity, XCircle } from 'lucide-react';

interface PostCardProps {
  post: BlogPost;
  onEdit: (post: BlogPost) => void;
  onApprove: (id: string, platform: 'devto' | 'hashnode') => void;
  onReject: (id: string) => void;
}

export const PostCard: React.FC<PostCardProps> = ({ post, onEdit, onApprove, onReject }) => {
  // Determine viral score color
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-400 border-green-400';
    if (score >= 75) return 'text-purple-400 border-purple-400';
    return 'text-yellow-400 border-yellow-400';
  };

  const getSentimentColor = (sentiment: string) => {
      switch(sentiment) {
          case 'Positive': return 'text-green-400 bg-green-400/10';
          case 'Negative': return 'text-red-400 bg-red-400/10';
          default: return 'text-gray-400 bg-gray-400/10';
      }
  };

  return (
    <div className="group relative bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden hover:border-purple-500/50 transition-all duration-300 flex flex-col h-full shadow-lg hover:shadow-purple-900/20">
      {/* Image Section */}
      <div className="relative h-48 overflow-hidden">
        <img 
          src={post.imageUrl} 
          alt={post.title} 
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-80 group-hover:opacity-100"
        />
        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-gray-700 flex items-center gap-1.5">
          <TrendingUp size={14} className={getScoreColor(post.viralScore).split(' ')[0]} />
          <span className={`text-xs font-bold ${getScoreColor(post.viralScore).split(' ')[0]}`}>
            {post.viralScore} Viral Score
          </span>
        </div>
        <div className="absolute bottom-3 left-3 flex gap-2">
             <span className="px-2 py-1 text-[10px] uppercase tracking-wider font-semibold bg-purple-600 text-white rounded-md">
                {post.category}
             </span>
             {post.readingTimeMin && (
                 <span className="px-2 py-1 text-[10px] font-semibold bg-black/50 backdrop-blur text-white rounded-md flex items-center gap-1">
                    <Clock size={10}/> {post.readingTimeMin} min
                 </span>
             )}
        </div>
      </div>

      {/* Content Section */}
      <div className="p-5 flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-3">
             <div className="flex items-center gap-2 text-gray-400 text-xs">
                <span>{new Date(post.createdAt).toLocaleDateString()}</span>
                <span>•</span>
                <span className="flex items-center gap-1"><Eye size={12}/> AI Draft</span>
            </div>
            {post.sentiment && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full border border-white/5 uppercase tracking-wider font-bold ${getSentimentColor(post.sentiment)}`}>
                    {post.sentiment}
                </span>
            )}
        </div>
        
        <h3 className="text-xl font-bold text-white mb-2 leading-tight group-hover:text-purple-300 transition-colors">
          {post.title}
        </h3>
        
        <p className="text-gray-400 text-sm mb-4 line-clamp-3 flex-1">
          {post.excerpt}
        </p>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-6">
            {post.tags.slice(0, 3).map(tag => (
                <span key={tag} className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
                    #{tag}
                </span>
            ))}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-auto pt-4 border-t border-gray-800">
          <button 
            onClick={() => onReject(post.id)}
            className="p-2 rounded-lg bg-gray-800 hover:bg-red-900/50 text-gray-400 hover:text-red-400 transition-colors"
            title="Reject Draft"
          >
            <XCircle size={20} />
          </button>
          <button 
            onClick={() => onEdit(post)}
            className="flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium transition-colors"
          >
            <Edit2 size={16} /> Edit
          </button>
          <div className="flex-1 flex gap-1">
            <button 
                onClick={() => onApprove(post.id, 'devto')}
                className="flex-1 flex items-center justify-center gap-1 py-2 px-2 rounded-lg bg-white text-black hover:bg-black hover:text-white hover:border-white border border-transparent text-xs font-bold transition-all"
                title="Publish to Dev.to"
            >
                <CheckCircle size={14} /> Dev.to
            </button>
            <button 
                onClick={() => onApprove(post.id, 'hashnode')}
                className="flex-1 flex items-center justify-center gap-1 py-2 px-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 border border-transparent text-xs font-bold transition-all"
                title="Publish to Hashnode"
            >
                <CheckCircle size={14} /> Hashnode
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};