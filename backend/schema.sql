-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Create the status enum type
do $$ begin
    create type post_status as enum ('draft', 'needs_review', 'approved', 'published');
exception
    when duplicate_object then null;
end $$;

-- Create the posts table
create table if not exists posts (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id), -- References the custom users table
  title text not null,
  content_markdown text,
  status post_status default 'draft',
  viral_score integer check (viral_score >= 0 and viral_score <= 100),
  sentiment text check (sentiment in ('Positive', 'Neutral', 'Negative')),
  target_audience text,
  reading_time_min integer,
  seo_keywords text[],
  meta_description text,
  critique_notes text,
  image_prompt text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create users table for custom auth (if not using Supabase Auth directly)
create table if not exists users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  full_name text,
  avatar_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table posts enable row level security;

-- Create a policy that allows all operations for now (can be restricted later)
create policy "Allow all operations for anon" on posts for all using (true) with check (true);
