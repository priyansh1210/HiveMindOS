-- Autonomous Enterprise AI Workforce — Database Schema
-- Run this in your Supabase SQL editor to provision the project.

create extension if not exists "pgcrypto";
create extension if not exists "vector";

-- ============================================================
-- companies
-- ============================================================
create table if not exists companies (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text,
    industry text,
    created_at timestamptz default now()
);

-- ============================================================
-- agents
-- ============================================================
create table if not exists agents (
    id uuid primary key default gen_random_uuid(),
    company_id uuid references companies(id) on delete cascade,
    name text not null,
    role text not null check (role in ('hr','sales','finance','support','ops','orchestrator')),
    system_prompt text not null,
    status text default 'idle' check (status in ('idle','working','waiting','collaborating','paused')),
    avatar_url text,
    color text,
    created_at timestamptz default now()
);

create index if not exists idx_agents_company on agents(company_id);
create index if not exists idx_agents_status on agents(status);

-- ============================================================
-- tasks
-- ============================================================
create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    company_id uuid references companies(id) on delete cascade,
    title text not null,
    description text,
    status text default 'pending' check (status in ('pending','planning','in_progress','completed','failed')),
    created_by text default 'user',
    assigned_agents text[] default '{}',
    plan jsonb,
    result jsonb,
    created_at timestamptz default now(),
    completed_at timestamptz
);

create index if not exists idx_tasks_company on tasks(company_id);
create index if not exists idx_tasks_status on tasks(status);
create index if not exists idx_tasks_created_at on tasks(created_at desc);

-- ============================================================
-- messages (agent-to-agent communication log)
-- ============================================================
create table if not exists messages (
    id uuid primary key default gen_random_uuid(),
    task_id uuid references tasks(id) on delete cascade,
    from_agent text not null,
    to_agent text not null,
    message_type text not null check (message_type in ('request','response','info','escalation','broadcast','user','system')),
    content text not null,
    data jsonb,
    priority text default 'medium' check (priority in ('low','medium','high','urgent')),
    created_at timestamptz default now()
);

create index if not exists idx_messages_task on messages(task_id);
create index if not exists idx_messages_created_at on messages(created_at desc);

-- ============================================================
-- knowledge (company knowledge base, with optional embeddings)
-- ============================================================
create table if not exists knowledge (
    id uuid primary key default gen_random_uuid(),
    company_id uuid references companies(id) on delete cascade,
    category text,
    title text not null,
    content text not null,
    embedding vector(1536),
    created_at timestamptz default now()
);

create index if not exists idx_knowledge_company on knowledge(company_id);
create index if not exists idx_knowledge_category on knowledge(category);

-- ============================================================
-- activity_log (per-agent action audit for analytics)
-- ============================================================
create table if not exists activity_log (
    id uuid primary key default gen_random_uuid(),
    agent_id uuid references agents(id) on delete cascade,
    task_id uuid references tasks(id) on delete cascade,
    action text not null,
    details jsonb,
    tokens_used integer default 0,
    duration_ms integer default 0,
    created_at timestamptz default now()
);

create index if not exists idx_activity_agent on activity_log(agent_id);
create index if not exists idx_activity_task on activity_log(task_id);
create index if not exists idx_activity_created_at on activity_log(created_at desc);

-- ============================================================
-- Enable realtime on dashboard-facing tables
-- ============================================================
alter publication supabase_realtime add table tasks;
alter publication supabase_realtime add table messages;
alter publication supabase_realtime add table agents;
alter publication supabase_realtime add table activity_log;
