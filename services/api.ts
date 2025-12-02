import { BlogPost, PostStatus } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

// Helper to map Backend snake_case to Frontend camelCase
const mapPostFromBackend = (data: any): BlogPost => ({
  id: data.id,
  title: data.title,
  excerpt: data.meta_description || '', // Use meta description as excerpt if not available
  content: data.content_markdown || '',
  author: 'AI Agent', // Default
  category: 'Tech', // Default or derive
  imageUrl: data.image_prompt ? `https://picsum.photos/seed/${data.id}/800/600` : 'https://picsum.photos/800/600', // Placeholder based on ID
  viralScore: data.viral_score || 0,
  sentiment: data.sentiment as 'Positive' | 'Neutral' | 'Negative',
  targetAudience: data.target_audience || '',
  readingTimeMin: data.reading_time_min || 0,
  seoKeywords: data.seo_keywords || [],
  metaDescription: data.meta_description || '',
  imagePrompt: data.image_prompt || '',
  critiqueNotes: data.critique_notes || '',
  status: data.status as PostStatus,
  createdAt: data.created_at,
  tags: data.seo_keywords || []
});

// Helper to map Frontend camelCase to Backend snake_case for updates
const mapPostToBackend = (post: Partial<BlogPost>) => {
  const mapped: any = {};
  if (post.title) mapped.title = post.title;
  if (post.content) mapped.content_markdown = post.content;
  if (post.status) mapped.status = post.status;
  if (post.viralScore) mapped.viral_score = post.viralScore;
  if (post.sentiment) mapped.sentiment = post.sentiment;
  if (post.targetAudience) mapped.target_audience = post.targetAudience;
  if (post.readingTimeMin) mapped.reading_time_min = post.readingTimeMin;
  if (post.seoKeywords) mapped.seo_keywords = post.seoKeywords;
  if (post.metaDescription) mapped.meta_description = post.metaDescription;
  if (post.critiqueNotes) mapped.critique_notes = post.critiqueNotes;
  if (post.imagePrompt) mapped.image_prompt = post.imagePrompt;
  return mapped;
};

export interface NewsItem {
  title: string;
  url: string;
  source: string;
  summary: string;
  published_at: string;
  image_url?: string;
}

export const api = {
  getNews: async (topic: string = "Technology", limit: number = 5): Promise<NewsItem[]> => {
    const response = await fetch(`${API_URL}/news?topic=${encodeURIComponent(topic)}&limit=${limit}`, {
      headers: getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch news');
    return await response.json();
  },

  getPosts: async (): Promise<BlogPost[]> => {
    const response = await fetch(`${API_URL}/posts`, {
      headers: getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch posts');
    const data = await response.json();
    return data.map(mapPostFromBackend);
  },

  generatePost: async (topic: string): Promise<BlogPost> => {
    const response = await fetch(`${API_URL}/generate-pro-blog`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ topic }),
    });
    if (!response.ok) throw new Error('Failed to generate post');
    const result = await response.json();
    
    // The backend returns { status: "success", data: { ...post ... }, state: ... }
    // We modified backend to return the object directly, not an array
    const newPostData = Array.isArray(result.data) ? result.data[0] : result.data;
    return mapPostFromBackend(newPostData);
  },

  updatePost: async (id: string, updates: Partial<BlogPost>): Promise<void> => {
    const backendUpdates = mapPostToBackend(updates);
    const response = await fetch(`${API_URL}/posts/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(backendUpdates),
    });
    if (!response.ok) throw new Error('Failed to update post');
  },

  deletePost: async (id: string): Promise<void> => {
    const response = await fetch(`${API_URL}/posts/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete post');
  },

  publishToDevTo: async (id: string): Promise<{ url: string }> => {
    const response = await fetch(`${API_URL}/posts/${id}/publish`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to publish to Dev.to');
    return await response.json();
  },

  publishToHashnode: async (id: string): Promise<{ url: string }> => {
    const response = await fetch(`${API_URL}/posts/${id}/publish/hashnode`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to publish to Hashnode');
    return await response.json();
  },

  getAnalytics: async (): Promise<any> => {
    const response = await fetch(`${API_URL}/analytics`, {
      headers: getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch analytics');
    return await response.json();
  },

  getSettings: async (): Promise<any> => {
    const response = await fetch(`${API_URL}/user/settings`, {
      headers: getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch settings');
    return await response.json();
  },

  updateSettings: async (settings: any): Promise<void> => {
    const response = await fetch(`${API_URL}/user/settings`, {
      method: 'PUT',
      headers: {
        ...getHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    });
    if (!response.ok) throw new Error('Failed to update settings');
  }
};
