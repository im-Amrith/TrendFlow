-- Add API key columns to users table
do $$
begin
    if not exists (select 1 from information_schema.columns where table_name = 'users' and column_name = 'devto_api_key') then
        alter table public.users add column devto_api_key text;
    end if;

    if not exists (select 1 from information_schema.columns where table_name = 'users' and column_name = 'hashnode_token') then
        alter table public.users add column hashnode_token text;
    end if;

    if not exists (select 1 from information_schema.columns where table_name = 'users' and column_name = 'hashnode_pub_id') then
        alter table public.users add column hashnode_pub_id text;
    end if;
end $$;
