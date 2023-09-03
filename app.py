"""Monte Carlo simulation of the Dunning-Kruger experiment."""

from __future__ import annotations

from typing import TYPE_CHECKING

import altair as alt
import numpy as np
import polars as pl
import streamlit as st


if TYPE_CHECKING:
    from typing import Any


QUARTILES = ("Bottom", "2nd", "3rd", "Top")


def generate_data(
    corr_coef: float,
    n_participants: int,
    random_seed: int,
) -> pl.DataFrame:
    rng = np.random.default_rng(random_seed)
    test_score = rng.normal(size=n_participants)
    perceived_ability = (
        corr_coef * test_score +
        np.sqrt(1 - corr_coef * corr_coef) * rng.normal(size=n_participants)
    )

    return (
        pl.DataFrame({
            "test_score_percentile": (
                test_score.argsort().argsort() * 100 // n_participants),
            "perceived_ability_percentile": (
                perceived_ability.argsort().argsort() * 100 // n_participants),
        })
        .with_columns(
            pl.col("test_score_percentile").qcut(4, labels=QUARTILES)
                .alias("test_score_quartile"),
            pl.col("perceived_ability_percentile").qcut(4, labels=QUARTILES)
                .alias("perceived_ability_quartile"),
        )
    )


def create_percentile_chart(data: pl.DataFrame) -> alt.Chart:
    return alt.Chart(data).mark_point().encode(
        alt.X("test_score_percentile:Q"),
        alt.Y("perceived_ability_percentile:Q"),
    )


def create_quartile_chart(data: pl.DataFrame, quartile_col: str) -> alt.Chart:
    return (
        data.select(
            quartile_col,
            pl.col("test_score_percentile").alias("test_score"),
            pl.col("perceived_ability_percentile").alias("perceived_ability"),
        )
        .group_by(quartile_col)
        .mean()
        .melt(id_vars=quartile_col, value_name="average")
        .pipe(alt.Chart)
        .mark_line(point=True)
        .encode(
            alt.Color("variable:N").title(None)
                .sort(("test_score", "perceived_ability"))
                .legend(orient="bottom-right"),
            alt.X(f"{quartile_col}:N").sort(QUARTILES).axis(labelAngle=0),
            alt.Y("average:Q").title("average_percentile").scale(domain=(0, 100)),
        )
    )


def custom_theme() -> dict[str, Any]:
    return {
        "config": {
            "axis": {
                "grid": False,
                "labelColor": "#7F7F7F",
                "labelFontSize": 14,
                "tickColor": "#7F7F7F",
                "titleColor": "#7F7F7F",
                "titleFontSize": 16,
                "titleFontWeight": "normal",
            },
            "legend": {
                "labelColor": "#7F7F7F",
                "labelFontSize": 14,
            },
            "view": {
                "height": 320,
                "width": 480,
                "stroke": False,
            },
        },
    }


if __name__ == "__main__":
    alt.themes.register("custom_theme", custom_theme)
    alt.themes.enable("custom_theme")

    with st.sidebar:
        st.title("Monte Carlo simulation of the Dunning-Kruger experiment")

        n_participants = st.slider(
            label="Number of participants",
            min_value=50,
            max_value=150,
            value=100,
            step=10,
        )

        corr_coef = st.slider(
            label="Correlation",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
        )

        random_seed = st.number_input(label="Random seed", value=42)

    data = generate_data(
        corr_coef=corr_coef,
        n_participants=n_participants,
        random_seed=random_seed,  # type: ignore
    )

    st.header("Test score vs. perceived ability")
    st.altair_chart(create_percentile_chart(data), theme=None)

    st.header("Average percentiles by test score quartiles")
    st.altair_chart(create_quartile_chart(data, "test_score_quartile"), theme=None)

    st.header("Average percentiles by perceived ability quartiles")
    st.altair_chart(
        create_quartile_chart(data, "perceived_ability_quartile"),
        theme=None,
    )
