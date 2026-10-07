{{
  config(
    materialized='external',
    location="s3://silver/delta/arxiv_papers",
    options={"format": "delta"}
  )
}}

with raw as (
    select
        paper_id,
        trim(title) as title,
        regexp_replace(
            regexp_replace(trim(abstract), '\$[^$]*\$', '', 'g'),
            '\\\\[a-zA-Z]+\{[^}]*\}', '', 'g'
        ) as abstract,
        category,
        published_date::date as published_date
    from delta_scan('s3://bronze/delta/arxiv_raw')
    where paper_id is not null
      and title is not null
      and abstract is not null
),

deduped as (
    select *,
           row_number() over (partition by paper_id order by published_date desc) as rn
    from raw
)

select
    paper_id,
    title,
    abstract,
    category,
    published_date
from deduped
where rn = 1
