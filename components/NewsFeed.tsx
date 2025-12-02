import React, { useEffect, useState } from 'react';
import { api, NewsItem } from '../services/api';
import { ExternalLink, Clock, Newspaper, Plus } from 'lucide-react';

export const NewsFeed: React.FC = () => {
  const [allNews, setAllNews] = useState<NewsItem[]>([]);
  const [visibleCount, setVisibleCount] = useState(9);
  const [loading, setLoading] = useState(true);
  const [topic, setTopic] = useState('Technology');

  // Initial fetch of a large batch
  useEffect(() => {
    loadNews();
  }, [topic]);

  const loadNews = async () => {
    setLoading(true);
    try {
      // Fetch a large batch (e.g., 50) to allow instant "Load More"
      const data = await api.getNews(topic, 50);
      setAllNews(data);
      setVisibleCount(9); // Reset visible count on new topic
    } catch (error) {
      console.error("Failed to load news", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    setVisibleCount(prev => prev + 9);
  };

  const handleTopicChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTopic(e.target.value);
  };

  const visibleNews = allNews.slice(0, visibleCount);
  const hasMore = visibleCount < allNews.length;

  return (
    <div className="animate-fade-in pb-10">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Newspaper className="text-purple-500" /> Global Tech News
        </h2>
        <select 
          value={topic} 
          onChange={handleTopicChange}
          className="bg-gray-900 border border-gray-700 text-white text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block p-2.5"
        >
          <option value="Technology">Technology</option>
          <option value="AI">Artificial Intelligence</option>
          <option value="Crypto">Crypto & Finance</option>
          <option value="Startup">Startups</option>
        </select>
      </div>

      {loading && allNews.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-64 bg-gray-900 rounded-xl animate-pulse border border-gray-800"></div>
          ))}
        </div>
      ) : (
        <>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {visibleNews.map((item, index) => (
            <a 
              key={index} 
              href={item.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="group bg-gray-900 border border-gray-800 rounded-xl overflow-hidden hover:border-purple-500/50 transition-all hover:shadow-lg hover:shadow-purple-900/20 flex flex-col"
            >
              {item.image_url && (
                <div className="h-40 overflow-hidden">
                  <img 
                    src={item.image_url} 
                    alt={item.title} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    onError={(e) => (e.currentTarget.style.display = 'none')} 
                  />
                </div>
              )}
              <div className="p-5 flex-1 flex flex-col">
                <div className="flex items-center justify-between mb-2 text-xs text-gray-400">
                  <span className="font-semibold text-purple-400">{item.source}</span>
                  <span className="flex items-center gap-1">
                    <Clock size={12} />
                    {new Date(item.published_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2 line-clamp-2 group-hover:text-purple-300 transition-colors">
                  {item.title}
                </h3>
                <p className="text-gray-400 text-sm line-clamp-3 mb-4 flex-1">
                  {item.summary}
                </p>
                <div className="flex items-center text-purple-400 text-xs font-bold uppercase tracking-wider mt-auto">
                  Read Article <ExternalLink size={12} className="ml-1" />
                </div>
              </div>
            </a>
          ))}
        </div>

        {hasMore && (
            <div className="flex justify-center">
                <button 
                    onClick={handleLoadMore}
                    className="group relative flex items-center justify-center w-12 h-12 rounded-full bg-gray-800 hover:bg-purple-600 border border-gray-700 hover:border-purple-500 transition-all duration-300 shadow-lg hover:shadow-purple-500/40"
                >
                    <Plus size={24} className="text-white group-hover:scale-110 transition-transform" />
                </button>
            </div>
        )}
        </>
      )}
    </div>
  );
};
