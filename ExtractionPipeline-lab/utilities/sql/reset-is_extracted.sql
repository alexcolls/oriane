with cte as (
  select id
  from public.insta_content
  where is_extracted = true
  limit 100000
)
update public.insta_content
set is_extracted = false
where id in (select id from cte);
