import duckdb

con = duckdb.connect("olist.duckdb")

print("=== Nota média: pedidos no prazo vs atrasados ===\n")
resultado = con.execute("""
    select
        is_delayed,
        count(*) as pedidos,
        round(avg(review_score), 2) as nota_media
    from fct_orders
    where review_score is not null
      and delay_days is not null
    group by is_delayed
    order by is_delayed
""").fetchdf()
print(resultado)

print("\n=== Nota média por faixa de atraso ===\n")
faixas = con.execute("""
    select
        case
            when delay_days <= 0 then 'No prazo ou adiantado'
            when delay_days between 1 and 5 then 'Atraso 1-5 dias'
            when delay_days between 6 and 15 then 'Atraso 6-15 dias'
            else 'Atraso 15+ dias'
        end as faixa_atraso,
        count(*) as pedidos,
        round(avg(review_score), 2) as nota_media
    from fct_orders
    where review_score is not null
      and delay_days is not null
    group by faixa_atraso
    order by nota_media desc
""").fetchdf()
print(faixas)

con.close()