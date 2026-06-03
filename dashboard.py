import streamlit as st
import duckdb
import plotly.express as px

st.set_page_config(page_title="Olist Analytics", layout="wide")

@st.cache_data
def load(query):
    con = duckdb.connect("olist.duckdb")
    df = con.execute(query).fetchdf()
    con.close()
    return df

st.title("Olist E-Commerce Analytics")
st.markdown("How late delivery affects customer satisfaction")

# --- KPIs ---
kpis = load("""
    select
        count(*) as total_orders,
        round(avg(review_score), 2) as avg_score,
        round(100.0 * sum(case when is_delayed then 1 else 0 end) / count(*), 1) as pct_delayed
    from fct_orders
""")

c1, c2, c3 = st.columns(3)
c1.metric("Total orders", f"{int(kpis.total_orders[0]):,}")
c2.metric("Avg. review score", kpis.avg_score[0])
c3.metric("% delayed", f"{kpis.pct_delayed[0]}%")

st.divider()

# --- Delay vs satisfaction ---
st.subheader("Review score by delay bucket")
delay = load("""
    select
        case
            when delay_days <= 0 then '1. On time or early'
            when delay_days between 1 and 5 then '2. 1-5 days late'
            when delay_days between 6 and 15 then '3. 6-15 days late'
            else '4. 15+ days late'
        end as delay_bucket,
        round(avg(review_score), 2) as avg_score,
        count(*) as orders
    from fct_orders
    where review_score is not null and delay_days is not null
    group by delay_bucket
    order by delay_bucket
""")

fig = px.bar(delay, x="delay_bucket", y="avg_score", text="avg_score",
             labels={"delay_bucket": "Delivery outcome", "avg_score": "Avg. review score"},
             color="avg_score", color_continuous_scale="RdYlGn")
fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Score distribution ---
st.subheader("Distribution of review scores")
dist = load("""
    select review_score, count(*) as orders
    from fct_orders
    where review_score is not null
    group by review_score
    order by review_score
""")
fig2 = px.bar(dist, x="review_score", y="orders",
              labels={"review_score": "Review score", "orders": "Number of orders"})
st.plotly_chart(fig2, use_container_width=True)