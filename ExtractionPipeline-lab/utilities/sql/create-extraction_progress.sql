drop function if exists extraction_progress();

create function extraction_progress()
returns json
language sql
as $$
  select json_build_object(
    'total', count(*),
    'downloaded', sum(case when is_downloaded = true then 1 else 0 end),
    'extracted', sum(case when is_extracted = true then 1 else 0 end),
    'progress', case
      when count(*) = 0 then 0
      else round(100.0 * sum(case when is_extracted = true then 1 else 0 end) / count(*), 2)
    end
  )
  from public.insta_content;
$$;
