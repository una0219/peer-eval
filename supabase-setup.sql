-- ============================================================
-- 综合测评评选结果确认 · 建表脚本
-- 用法：Supabase 后台 → SQL Editor → 新建查询 → 粘贴全文 → Run
-- ============================================================

create table if not exists public.eval_responses (
  id             bigserial primary key,
  student_id     text        not null unique,          -- 学号，一人一条（重复提交覆盖）
  student_name   text        not null,
  confirm_status text        not null,                 -- 'confirm' | 'dispute'
  dispute_text   text,                                 -- 异议说明，仅 dispute 时有值
  vote_seven     jsonb       not null default '[]'::jsonb,  -- 8选7 选中的学号数组
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

-- student_id 上的 unique 已自带索引，upsert 的 on_conflict=student_id 也靠它

-- ---- 行级安全 ----
-- 页面里带的是 anon key（公开可见），所以这里只能做「防君子不防小人」的限制：
-- 允许匿名读写，但结构上限定死一个人只有一条记录。
alter table public.eval_responses enable row level security;

drop policy if exists "anon_select" on public.eval_responses;
drop policy if exists "anon_insert" on public.eval_responses;
drop policy if exists "anon_update" on public.eval_responses;

create policy "anon_select" on public.eval_responses
  for select to anon using (true);

create policy "anon_insert" on public.eval_responses
  for insert to anon with check (true);

create policy "anon_update" on public.eval_responses
  for update to anon using (true) with check (true);

-- 不开放 delete：管理员在后台要删记录直接用 Supabase 面板
