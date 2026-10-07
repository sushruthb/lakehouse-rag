{{
  config(
    materialized='external',
    location="s3://gold/delta/arxiv_chunks",
    options={"format": "delta"}
  )
}}

with silver as (
    select paper_id, title, category, abstract
    from delta_scan('s3://silver/delta/arxiv_papers')
),

words as (
    select
        paper_id,
        title,
        category,
        abstract,
        string_split(abstract, ' ') as word_arr,
        len(string_split(abstract, ' ')) as word_count
    from silver
),

chunks as (
    select
        paper_id,
        title,
        category,
        generate_subscripts(
            range(0, greatest(1, cast(ceil(word_count / 200.0) as int)))
        ) - 1 as chunk_index,
        word_arr,
        word_count
    from words,
         lateral (select range(0, greatest(1, cast(ceil(word_count / 200.0) as int)))) t(r)
),

final as (
    select
        paper_id,
        title,
        category,
        chunk_index,
        array_to_string(
            word_arr[chunk_index * 200 + 1 : least((chunk_index + 1) * 200, word_count)],
            ' '
        ) as chunk_text,
        title || ' ' || array_to_string(
            word_arr[chunk_index * 200 + 1 : least((chunk_index + 1) * 200, word_count)],
            ' '
        ) as embed_text
    from chunks
)

select * from final
where length(trim(chunk_text)) > 10
