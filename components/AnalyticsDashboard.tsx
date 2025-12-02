import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Eye, Heart, MessageCircle, TrendingUp, ExternalLink } from 'lucide-react';

interface ArticleStats {
  title: string;
  url: string;
  views: number;
  reactions: number;
  comments: number;
  published_at: string;
}

interface AnalyticsData {
  devto: ArticleStats[];
  hashnode: ArticleStats[];
  totals: {
    views: number;
    reactions: number;
    comments: number;
  };
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black/80 backdrop-blur-md border border-gray-700 p-4 rounded-xl shadow-2xl">
        <p className="text-gray-300 font-medium mb-3 text-sm border-b border-gray-700 pb-2">{label}</p>
        <div className="space-y-2">
            {payload.map((entry: any, index: number) => (
                <div key={index} className="flex items-center justify-between gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></div>
                        <span className="text-gray-400 capitalize">{entry.name}</span>
                    </div>
                    <span className="text-white font-bold font-mono">{entry.value}</span>
                </div>
            ))}
        </div>
      </div>
    );
  }
  return null;
};

export const AnalyticsDashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const result = await api.getAnalytics();
      setData(result);
    } catch (error) {
      console.error("Failed to load analytics", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!data) return <div className="text-center text-gray-500">No data available</div>;

  // Prepare data for charts
  const devtoChartData = data.devto.map(a => ({
    name: a.title.length > 20 ? a.title.substring(0, 20) + '...' : a.title,
    views: a.views,
    reactions: a.reactions,
    fullTitle: a.title
  }));

  const hashnodeChartData = data.hashnode.map(a => ({
    name: a.title.length > 20 ? a.title.substring(0, 20) + '...' : a.title,
    views: a.views,
    reactions: a.reactions,
    fullTitle: a.title
  }));

  return (
    <div className="space-y-10 animate-fade-in pb-20">
      
      <div className="flex items-center justify-between mb-2">
        <div>
            <h1 className="text-4xl font-extrabold text-white mb-2 tracking-tight">Analytics Overview</h1>
            <p className="text-gray-400 text-lg">Track the performance of your content across all platforms.</p>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-6 rounded-2xl flex items-center gap-4 hover:border-purple-500/30 transition-colors group">
          <div className="p-4 bg-purple-500/10 rounded-xl text-purple-400 group-hover:bg-purple-500/20 transition-colors">
            <Eye size={24} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-medium">Total Views</p>
            <h3 className="text-3xl font-bold text-white tracking-tight">{data.totals.views.toLocaleString()}</h3>
          </div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-6 rounded-2xl flex items-center gap-4 hover:border-pink-500/30 transition-colors group">
          <div className="p-4 bg-pink-500/10 rounded-xl text-pink-400 group-hover:bg-pink-500/20 transition-colors">
            <Heart size={24} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-medium">Total Reactions</p>
            <h3 className="text-3xl font-bold text-white tracking-tight">{data.totals.reactions.toLocaleString()}</h3>
          </div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-6 rounded-2xl flex items-center gap-4 hover:border-blue-500/30 transition-colors group">
          <div className="p-4 bg-blue-500/10 rounded-xl text-blue-400 group-hover:bg-blue-500/20 transition-colors">
            <MessageCircle size={24} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-medium">Total Comments</p>
            <h3 className="text-3xl font-bold text-white tracking-tight">{data.totals.comments.toLocaleString()}</h3>
          </div>
        </div>
      </div>

      {/* Dev.to Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-black border border-gray-700 flex items-center justify-center">
                    <img src="https://dev.to/favicon.ico" className="w-5 h-5" alt="Dev.to" />
                </div>
                Dev.to Performance
            </h2>
        </div>
        
        {data.devto.length > 0 ? (
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-3xl p-8 shadow-xl">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-semibold text-gray-300">Engagement Metrics</h3>
                    <div className="flex gap-2">
                        <span className="flex items-center gap-1 text-xs text-gray-500"><div className="w-2 h-2 rounded-full bg-purple-500"></div> Views</span>
                        <span className="flex items-center gap-1 text-xs text-gray-500"><div className="w-2 h-2 rounded-full bg-pink-500"></div> Reactions</span>
                    </div>
                </div>
                <div className="h-96 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={devtoChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }} barGap={8}>
                            <defs>
                                <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={1}/>
                                    <stop offset="100%" stopColor="#7c3aed" stopOpacity={0.8}/>
                                </linearGradient>
                                <linearGradient id="colorReactions" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#ec4899" stopOpacity={1}/>
                                    <stop offset="100%" stopColor="#db2777" stopOpacity={0.8}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} opacity={0.2} />
                            <XAxis 
                                dataKey="name" 
                                stroke="#6B7280" 
                                tick={{fontSize: 12, fill: '#9CA3AF'}} 
                                tickLine={false}
                                axisLine={false}
                                dy={10}
                            />
                            <YAxis 
                                stroke="#6B7280" 
                                tick={{fontSize: 12, fill: '#9CA3AF'}} 
                                tickLine={false}
                                axisLine={false}
                                dx={-10}
                            />
                            <Tooltip content={<CustomTooltip />} cursor={{fill: '#374151', opacity: 0.1}} />
                            <Bar dataKey="views" name="Views" fill="url(#colorViews)" radius={[6, 6, 6, 6]} barSize={32} />
                            <Bar dataKey="reactions" name="Reactions" fill="url(#colorReactions)" radius={[6, 6, 6, 6]} barSize={32} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        ) : (
            <div className="p-12 text-center border border-dashed border-gray-800 rounded-3xl bg-gray-900/30">
                <p className="text-gray-500">No published articles on Dev.to yet.</p>
            </div>
        )}
      </div>

      {/* Hashnode Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                    <img src="https://hashnode.com/favicon.ico" className="w-5 h-5 brightness-0 invert" alt="Hashnode" />
                </div>
                Hashnode Performance
            </h2>
        </div>

        {data.hashnode.length > 0 ? (
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-3xl p-8 shadow-xl">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-semibold text-gray-300">Engagement Metrics</h3>
                    <div className="flex gap-2">
                        <span className="flex items-center gap-1 text-xs text-gray-500"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Views</span>
                        <span className="flex items-center gap-1 text-xs text-gray-500"><div className="w-2 h-2 rounded-full bg-cyan-500"></div> Reactions</span>
                    </div>
                </div>
                <div className="h-96 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={hashnodeChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }} barGap={8}>
                            <defs>
                                <linearGradient id="colorViewsHash" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={1}/>
                                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0.8}/>
                                </linearGradient>
                                <linearGradient id="colorReactionsHash" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#06b6d4" stopOpacity={1}/>
                                    <stop offset="100%" stopColor="#0891b2" stopOpacity={0.8}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} opacity={0.2} />
                            <XAxis 
                                dataKey="name" 
                                stroke="#6B7280" 
                                tick={{fontSize: 12, fill: '#9CA3AF'}} 
                                tickLine={false}
                                axisLine={false}
                                dy={10}
                            />
                            <YAxis 
                                stroke="#6B7280" 
                                tick={{fontSize: 12, fill: '#9CA3AF'}} 
                                tickLine={false}
                                axisLine={false}
                                dx={-10}
                            />
                            <Tooltip content={<CustomTooltip />} cursor={{fill: '#374151', opacity: 0.1}} />
                            <Bar dataKey="views" name="Views" fill="url(#colorViewsHash)" radius={[6, 6, 6, 6]} barSize={32} />
                            <Bar dataKey="reactions" name="Reactions" fill="url(#colorReactionsHash)" radius={[6, 6, 6, 6]} barSize={32} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        ) : (
            <div className="p-12 text-center border border-dashed border-gray-800 rounded-3xl bg-gray-900/30">
                <p className="text-gray-500">No published articles on Hashnode yet.</p>
            </div>
        )}
      </div>

    </div>
  );
};
