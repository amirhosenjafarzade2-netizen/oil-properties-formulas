# live_chart.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Callable, Dict, List, Any

def live_module(
    title: str,
    inputs: Dict[str, Dict],
    compute: Callable[[Dict[str, float]], Dict[str, float]],
    extra_vars: List[str] = None,
    default_chart: str = "polar",
):
    """
    Generic “live” calculator with sliders + interactive chart.

    Parameters
    ----------
    title : str
        Section title (shown as sub-header).
    inputs : dict
        { "label": {"min": float, "max": float, "step": float, "value": float, "unit": str}, … }
    compute : callable
        Takes a dict of current values → returns a dict {var_name: value}
        Must always return the *main* result under the key "result".
    extra_vars : list[str], optional
        Additional output keys that should be plotted (besides "result").
    default_chart : str
        One of "polar", "line", "bar", "radar", "scatter"
    """
    st.subheader(title)

    # ------------------------------------------------------------------ #
    # 1. Sliders
    # ------------------------------------------------------------------ #
    values = {}
    for label, cfg in inputs.items():
        values[label] = st.slider(
            f"{label} ({cfg.get('unit','')})",
            min_value=cfg["min"],
            max_value=cfg["max"],
            value=cfg["value"],
            step=cfg["step"],
            key=f"slider_{title}_{label}",
        )

    # ------------------------------------------------------------------ #
    # 2. Compute all variables (including intermediate ones)
    # ------------------------------------------------------------------ #
    out = compute(values)

    # Always show the primary result
    st.success(f"**Result:** {out['result']:.5f} {out.get('unit','')}")

    # ------------------------------------------------------------------ #
    # 3. Prepare data for live chart
    # ------------------------------------------------------------------ #
    # We will sweep ONE input (the one the user selects) while keeping the others fixed.
    sweep_key = st.selectbox(
        "Sweep variable for chart",
        options=list(inputs.keys()),
        key=f"sweep_{title}",
    )

    n_points = 50
    sweep_vals = pd.np.linspace(
        inputs[sweep_key]["min"], inputs[sweep_key]["max"], n_points
    )

    # Container for each output series
    series = {k: [] for k in (["result"] + (extra_vars or []))}

    fixed = {k: v for k, v in values.items() if k != sweep_key}
    for val in sweep_vals:
        fixed[sweep_key] = val
        res = compute(fixed)
        for k in series:
            series[k].append(res.get(k, res["result"] if k == "result" else None))

    df = pd.DataFrame(series, index=sweep_vals)
    df.index.name = sweep_key

    # ------------------------------------------------------------------ #
    # 4. Chart type selector
    # ------------------------------------------------------------------ #
    chart_type = st.radio(
        "Chart type",
        ["polar", "line", "bar", "radar", "scatter"],
        index=["polar", "line", "bar", "radar", "scatter"].index(default_chart),
        horizontal=True,
        key=f"charttype_{title}",
    )

    # ------------------------------------------------------------------ #
    # 5. Build Plotly figure
    # ------------------------------------------------------------------ #
    fig = go.Figure()

    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    ]

    if chart_type == "polar":
        # Polar-area needs positive radius → shift if any negative
        shift = abs(df.min().min()) + 1 if (df < 0).any().any() else 0
        for i, col in enumerate(df.columns):
            fig.add_trace(
                go.Scatterpolar(
                    r=df[col] + shift,
                    theta=df.index,
                    mode="lines",
                    name=col,
                    line=dict(color=colors[i % len(colors)]),
                )
            )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[shift, df.max().max() + shift])),
            showlegend=True,
        )

    elif chart_type == "line":
        for i, col in enumerate(df.columns):
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="lines+markers",
                    name=col,
                    line=dict(color=colors[i % len(colors)]),
                )
            )

    elif chart_type == "bar":
        for i, col in enumerate(df.columns):
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df[col],
                    name=col,
                    marker_color=colors[i % len(colors)],
                )
            )
        fig.update_layout(barmode="group")

    elif chart_type == "radar":
        for i, col in enumerate(df.columns):
            fig.add_trace(
                go.Scatterpolar(
                    r=df[col].tolist() + [df[col].iloc[0]],
                    theta=list(df.index) + [df.index[0]],
                    fill="toself",
                    name=col,
                    line=dict(color=colors[i % len(colors)]),
                )
            )
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)

    elif chart_type == "scatter":
        for i, col in enumerate(df.columns):
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="markers",
                    name=col,
                    marker=dict(color=colors[i % len(colors)], size=8),
                )
            )

    fig.update_layout(
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark" if st.get_option("theme.backgroundColor") == "#0e1117" else "plotly",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------ #
    # 6. Optional: show raw table
    # ------------------------------------------------------------------ #
    with st.expander("Raw sweep data"):
        st.dataframe(df.style.format("{:.5f}"))
