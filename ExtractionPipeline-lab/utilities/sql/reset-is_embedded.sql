with cte as (
  select id
  from public.insta_content
  where is_embedded = true
  limit 100000
)
update public.insta_content
set is_embedded = false
where id in (select id from cte);
