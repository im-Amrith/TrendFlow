-- 1. Enable UUID extension if not enabled
create extension if not exists "uuid-ossp";

-- 2. Create users table if it doesn't exist
create table if not exists public.users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  full_name text,
  avatar_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Insert the user if they don't exist
insert into public.users (email, full_name)
values ('amrithesh23@gmail.com', 'Amrithesh')
on conflict (email) do nothing;

-- 4. Add user_id column to posts if it doesn't exist
do $$
begin
    if not exists (select 1 from information_schema.columns where table_name = 'posts' and column_name = 'user_id') then
        alter table public.posts add column user_id uuid references public.users(id);
    end if;
end $$;

-- 5. Update existing posts to belong to this user
update public.posts
set user_id = (select id from public.users where email = 'amrithesh23@gmail.com')
where user_id is null;
