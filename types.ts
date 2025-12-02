export type PostStatus = 'draft' | 'needs_review' | 'approved' | 'published' | 'archived';

export interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  author: string;
  category: string;
  imageUrl: string;
  
  // Advanced Analytics
  viralScore: number; // 0-100
  sentiment: 'Positive' | 'Neutral' | 'Negative';
  targetAudience: string;
  readingTimeMin: number;
  
  // SEO & Packaging
  seoKeywords: string[];
  metaDescription: string;
  imagePrompt: string;
  
  // Agent Feedback
  critiqueNotes: string;
  
  status: PostStatus;
  createdAt: string;
  tags: string[]; // Keeping for backward compatibility (maps to seoKeywords usually)
}

export interface NavItem {
  label: string;
  href: string;
  active?: boolean;
}