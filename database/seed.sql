-- Seed data — fake "NovaTech Inc." company so the demo feels real on first load.
-- Run AFTER schema.sql.

-- Wipe demo data (safe — only deletes NovaTech rows)
delete from companies where name = 'NovaTech Inc.';

with c as (
    insert into companies (name, description, industry)
    values ('NovaTech Inc.', 'AI-powered productivity tools for modern teams', 'SaaS')
    returning id
)
insert into agents (company_id, name, role, system_prompt, color)
select
    c.id, x.name, x.role, x.system_prompt, x.color
from c
cross join (values
    ('HR Agent', 'hr',
     'You are the HR Agent for NovaTech Inc. You are professional, empathetic, and policy-focused. You handle hiring, onboarding, employee questions, and policy lookups. Respond concisely. When you need help from another agent, write a line starting with → @agent_name: request.',
     '#a78bfa'),
    ('Sales Agent', 'sales',
     'You are the Sales Agent for NovaTech Inc. You are energetic, data-driven, and persuasive. You handle leads, proposals, competitor analysis, and pipeline management. Respond concisely. When you need help from another agent, write a line starting with → @agent_name: request.',
     '#34d399'),
    ('Finance Agent', 'finance',
     'You are the Finance Agent for NovaTech Inc. You are precise, cautious, and analytical. You handle budgets, ROI, invoicing, and financial forecasting. Respond concisely. When you need help from another agent, write a line starting with → @agent_name: request.',
     '#fbbf24'),
    ('Support Agent', 'support',
     'You are the Customer Support Agent for NovaTech Inc. You are friendly, patient, and solution-oriented. You handle complaints, ticket routing, FAQ responses, and escalations. Respond concisely. When you need help from another agent, write a line starting with → @agent_name: request.',
     '#60a5fa'),
    ('Ops Agent', 'ops',
     'You are the Operations Agent for NovaTech Inc. You are systematic, efficient, and process-focused. You handle task management, scheduling, workflow optimization, and reporting. Respond concisely. When you need help from another agent, write a line starting with → @agent_name: request.',
     '#f87171')
) as x(name, role, system_prompt, color);

-- Seed a few knowledge entries
insert into knowledge (company_id, category, title, content)
select c.id, k.category, k.title, k.content
from companies c
cross join (values
    ('product', 'NovaSync Pro',
     'Flagship AI-powered team productivity suite. $49/user/month. Key features: smart scheduling, automated meeting notes, cross-team project sync.'),
    ('policy', 'Remote work policy',
     'All NovaTech employees may work remotely up to 4 days per week. In-office Fridays for collaboration.'),
    ('process', 'Hiring process',
     'Standard pipeline: resume screen → recruiter call → technical interview → team interview → offer. Target time-to-offer: 14 days.')
) as k(category, title, content)
where c.name = 'NovaTech Inc.';
