import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
from utils.data_utils import get_all_data

st.title("Geopolitical shocks: country-level collapses and post-COVID movers")

def render_geopolitical_page():
pax_by_country, pax_by_airport, us_airport_map, new_data = get_all_data()

# --- DEBUG ONCE: show what columns exist ---
st.write("pax_by_country columns:", list(pax_by_country.columns))
st.write("pax_by_country head:", pax_by_country.head())

# --- Normalize column names (safe) ---
df = pax_by_country.copy()
df.columns = [c.strip() for c in df.columns]

# Candidate mappings: pick the first column that exists
year_col_candidates = ["YEAR", "Year", "year"]
country_col_candidates = ["foreign_country", "FOREIGN_COUNTRY", "COUNTRY", "DEST_COUNTRY_NAME", "ORIGIN_COUNTRY_NAME"]
pax_col_candidates = ["PASSENGERS", "passengers", "PAX", "TOTAL_PASSENGERS"]

def first_existing(cands):
    for c in cands:
        if c in df.columns:
            return c
    return None

YEAR_COL = first_existing(year_col_candidates)
COUNTRY_COL = first_existing(country_col_candidates)
PAX_COL = first_existing(pax_col_candidates)

if YEAR_COL is None or COUNTRY_COL is None or PAX_COL is None:
    st.error(f"Missing expected columns. Found YEAR={YEAR_COL}, COUNTRY={COUNTRY_COL}, PAX={PAX_COL}")
    st.stop()

# Standardize names to what the rest of the page expects
df = df.rename(columns={YEAR_COL: "YEAR", COUNTRY_COL: "foreign_country", PAX_COL: "PASSENGERS"})

# Now your original logic will work
country_year = (
    df.groupby(["YEAR", "foreign_country"], as_index=False)
      .agg(passengers=("PASSENGERS", "sum"))
)

    global_year = (
        country_year.groupby("YEAR", as_index=False)
        .agg(total_passengers=("passengers", "sum"))
    )

    # ---- Timeline ----
    events = pd.DataFrame({"YEAR": [2001, 2020], "event": ["9/11", "COVID"]})

    timeline = alt.Chart(global_year).mark_line().encode(
        x=alt.X("YEAR:Q", title="Year", axis=alt.Axis(format="d")),
        y=alt.Y("total_passengers:Q", title="Total international passengers"),
        tooltip=["YEAR:Q", alt.Tooltip("total_passengers:Q", format=",.0f")]
    ).properties(width=850, height=260, title="International passengers to/from the U.S. (1990–2025)")

    markers = alt.Chart(events).mark_rule(strokeDash=[6, 4]).encode(
        x="YEAR:Q",
        tooltip=["event:N", "YEAR:Q"]
    )

    st.altair_chart(timeline + markers, use_container_width=True)

    # ---- Shocks (collapse-only bars) ----
    event_windows = [
        {"event": "9/11", "pre": 2000, "post": 2002},
        {"event": "COVID", "pre": 2019, "post": 2020},
    ]

    shocks_list = []
    for e in event_windows:
        pre = (
            country_year[country_year["YEAR"] == e["pre"]][["foreign_country", "passengers"]]
            .rename(columns={"passengers": "passengers_pre"})
        )
        post = (
            country_year[country_year["YEAR"] == e["post"]][["foreign_country", "passengers"]]
            .rename(columns={"passengers": "passengers_post"})
        )
        merged = pre.merge(post, on="foreign_country", how="outer").fillna(0)
        merged["event"] = e["event"]
        merged["pre_year"] = e["pre"]
        merged["post_year"] = e["post"]
        merged["abs_change"] = merged["passengers_post"] - merged["passengers_pre"]
        merged["pct_change"] = np.where(
            merged["passengers_pre"] > 0, merged["abs_change"] / merged["passengers_pre"], np.nan
        )
        shocks_list.append(merged)

    shocks = pd.concat(shocks_list, ignore_index=True)

    shock_events = sorted([e for e in shocks["event"].unique() if "recovery" not in e.lower()])
    event_param = alt.param(
        name="Event",
        value="COVID",
        bind=alt.binding_select(options=shock_events, name="Shock event: ")
    )

    BASELINE_MIN = 50_000

    bars_down = (
        alt.Chart(shocks)
        .add_params(event_param)
        .transform_filter("datum.event == Event")
        .transform_filter(f"datum.passengers_pre >= {BASELINE_MIN}")
        .transform_calculate(
            pct_change_pct="datum.pct_change * 100",
            loss_mag="(-1) * (datum.pct_change * 100)"
        )
        .transform_filter("datum.pct_change_pct < 0")
        .transform_window(
            rank="rank(datum.loss_mag)",
            sort=[alt.SortField("loss_mag", order="descending")]
        )
        .transform_filter("datum.rank <= 25")
        .mark_bar(color="#ac3333c9")
        .encode(
            x=alt.X(
                "foreign_country:N",
                sort=alt.SortField("loss_mag", order="descending"),
                title=None,
                axis=alt.Axis(labelAngle=90)
            ),
            y=alt.Y(
                "loss_mag:Q",
                title="Percent decline (pre → post)",
                scale=alt.Scale(domain=[0, 105], reverse=True)
            ),
            tooltip=[
                "foreign_country:N",
                "pre_year:Q",
                "post_year:Q",
                alt.Tooltip("passengers_pre:Q", format=",.0f"),
                alt.Tooltip("passengers_post:Q", format=",.0f"),
                alt.Tooltip("pct_change_pct:Q", format=".1f")
            ],
        )
        .properties(width=950, height=450, title="Largest country-level collapses during major shocks")
    )

    st.altair_chart(bars_down, use_container_width=True)

    # ---- Post-COVID movers (2019 -> 2024), countries on X ----
    PRE_YEAR, POST_YEAR = 2019, 2024

    cy_19_24 = (
        country_year[country_year["YEAR"].isin([PRE_YEAR, POST_YEAR])]
        .pivot_table(index="foreign_country", columns="YEAR", values="passengers", aggfunc="sum")
        .reset_index()
        .rename(columns={PRE_YEAR: "passengers_pre", POST_YEAR: "passengers_post"})
        .fillna(0)
    )

    BASELINE_MIN_POSTCOVID = 50_000
    cy_19_24 = cy_19_24[cy_19_24["passengers_pre"] >= BASELINE_MIN_POSTCOVID].copy()

    cy_19_24["abs_change"] = cy_19_24["passengers_post"] - cy_19_24["passengers_pre"]
    cy_19_24["pct_change"] = np.where(
        cy_19_24["passengers_pre"] > 0, cy_19_24["abs_change"] / cy_19_24["passengers_pre"], np.nan
    )
    cy_19_24["pct_change_pct"] = 100 * cy_19_24["pct_change"]

    top_inc_pct = cy_19_24.nlargest(5, "pct_change")
    top_dec_pct = cy_19_24.nsmallest(5, "pct_change")
    top10_pct = pd.concat([top_dec_pct, top_inc_pct], ignore_index=True)

    pct_chart = (
        alt.Chart(top10_pct)
        .mark_bar()
        .encode(
            x=alt.X(
                "foreign_country:N",
                sort=alt.SortField("pct_change_pct", order="ascending"),
                title=None,
                axis=alt.Axis(labelAngle=45)
            ),
            y=alt.Y("pct_change_pct:Q", title="Percent change (2019 → 2024)"),
            tooltip=[
                "foreign_country:N",
                alt.Tooltip("passengers_pre:Q", title="2019 passengers", format=",.0f"),
                alt.Tooltip("passengers_post:Q", title="2024 passengers", format=",.0f"),
                alt.Tooltip("abs_change:Q", title="Abs change", format=",.0f"),
                alt.Tooltip("pct_change_pct:Q", title="% change", format=".1f"),
            ]
        )
        .properties(width=950, height=450, title="Top post-COVID movers by percent change (2019 → 2024)")
    )

    pct_zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q")
    st.altair_chart(pct_chart + pct_zero, use_container_width=True)

render_geopolitical_page()
