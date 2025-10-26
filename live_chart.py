# ------------------------------------------------------------------ #
# 6. ENHANCED LIVE MODULE – Radar (Polar-Area) + Full Sensitivity
# ------------------------------------------------------------------ #
def _live_module(
    title: str,
    inputs: dict,
    compute,
    extra_outputs: list = None,
    default_chart: str = "radar",
    dynamic_components: bool = False,
):
    """
    Live sensitivity analyzer with radar (polar-area) chart showing:
      • All input parameters
      • Primary result
      • Optional extra outputs (e.g., intermediate variables)
    """
    st.markdown(f"### {title} – Live Sensitivity")

    # --- 1. Input sliders ---
    vals = {}
    for key, cfg in inputs.items():
        vals[key] = st.slider(
            f"**{key}** ({cfg.get('unit', '')})",
            min_value=cfg["min"],
            max_value=cfg["max"],
            value=cfg["value"],
            step=cfg["step"],
            format=cfg.get("format", None),
            key=f"live_{title}_{key}",
        )

    # --- 2. Dynamic components (for mixture density) ---
    if dynamic_components:
        C = int(vals.get("C", 1))
        for i in range(1, C + 1):
            mass = st.slider(
                f"Mass comp {i} (lbm)", 0.1, 1000.0, 10.0, 0.1,
                key=f"mass_{i}"
            )
            dens = st.slider(
                f"Density comp {i} (lbm/ft³)", 10.0, 100.0, 50.0, 0.1,
                key=f"dens_{i}"
            )
            st.session_state[f"mass_{i}"] = mass
            st.session_state[f"dens_{i}"] = dens

    # --- 3. Compute current values ---
    result_dict = compute(vals)
    main_result = result_dict.get("result")
    unit = result_dict.get("unit", "")
    extra_vals = {k: result_dict.get(k) for k in (extra_outputs or []) if k in result_dict}

    # Show main result
    if main_result is not None:
        st.success(f"**Result:** {main_result:.5f} {unit}")

    # Show extra outputs
    if extra_vals:
        cols = st.columns(len(extra_vals))
        for (name, val), col in zip(extra_vals.items(), cols):
            col.metric(name, f"{val:.5f}")

    # --- 4. Sweep setup ---
    sweep_key = st.selectbox(
        "Sweep variable for sensitivity",
        options=list(inputs.keys()),
        key=f"sweep_{title}"
    )

    n_points = 50
    sweep_range = np.linspace(
        inputs[sweep_key]["min"],
        inputs[sweep_key]["max"],
        n_points
    )

    # Prepare containers
    sweep_data = {k: [] for k in inputs}
    sweep_data["Result"] = []
    for k in extra_outputs or []:
        sweep_data[k] = []

    fixed_inputs = {k: v for k, v in vals.items() if k != sweep_key}

    # --- 5. Run sweep ---
    for sweep_val in sweep_range:
        fixed_inputs[sweep_key] = sweep_val
        res = compute(fixed_inputs)
        for k in inputs:
            sweep_data[k].append(fixed_inputs[k])
        sweep_data["Result"].append(res.get("result", 0))
        for k in extra_outputs or []:
            sweep_data[k].append(res.get(k, 0))

    df_sweep = pd.DataFrame(sweep_data, index=sweep_range)
    df_sweep.index.name = sweep_key

    # --- 6. Chart type selector ---
    chart_type = st.radio(
        "Chart type",
        ["radar", "line", "bar", "scatter"],
        index=["radar", "line", "bar", "scatter"].index(default_chart),
        horizontal=True,
        key=f"ctype_{title}",
    )

    # --- 7. Build Plotly figure ---
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#7f7f7f", "#bcbd22", "#17becf"]

    # Determine global min/max for scaling
    all_vals = pd.concat([pd.Series(vals.values()), pd.Series([main_result] + list(extra_vals.values()))])
    if not df_sweep.empty:
        all_vals = pd.concat([all_vals, df_sweep.stack()])
    vmin, vmax = all_vals.min(), all_vals.max()
    if pd.isna(vmin) or pd.isna(vmax):
        vmin, vmax = 0, 1
    buffer = (vmax - vmin) * 0.1 or 0.1
    vmin, vmax = vmin - buffer, vmax + buffer
    if vmin >= 0:
        vmin = 0  # radar looks better starting at 0 for positive data

    # Labels for radar
    radar_labels = list(inputs.keys()) + (extra_outputs or []) + ["Result"]

    if chart_type == "radar":
        # Sensitivity polygons (semi-transparent)
        for i in range(0, len(df_sweep), max(1, len(df_sweep) // 10)):  # sample for performance
            row = df_sweep.iloc[i]
            values = [row.get(k, 0) for k in inputs.keys()]
            if extra_outputs:
                values += [row.get(k, 0) for k in extra_outputs]
            values += [row["Result"]]
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=radar_labels + [radar_labels[0]],
                fill="toself",
                fillcolor=colors[i % len(colors)],
                line=dict(color=colors[i % len(colors)], width=0.5),
                opacity=0.15,
                name=f"{sweep_key}={df_sweep.index[i]:.3f}",
                showlegend=False,
            ))

        # Current point (bold red)
        current_vals = [vals[k] for k in inputs.keys()]
        if extra_outputs:
            current_vals += [extra_vals.get(k, 0) for k in extra_outputs]
        current_vals += [main_result or 0]
        fig.add_trace(go.Scatterpolar(
            r=current_vals + [current_vals[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            name="Current",
            line=dict(color="red", width=4),
            fillcolor="rgba(255,0,0,0.1)",
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[vmin, vmax],
                    tickfont=dict(size=10),
                ),
                angularaxis=dict(
                    rotation=90,
                    direction="clockwise",
                    tickfont=dict(size=11),
                ),
            ),
            showlegend=False,
            height=600,
            margin=dict(l=60, r=60, t=40, b=40),
        )

    elif chart_type == "line":
        for i, col in enumerate(df_sweep.columns):
            fig.add_trace(go.Scatter(
                x=df_sweep.index,
                y=df_sweep[col],
                mode="lines+markers",
                name=col,
                line=dict(color=colors[i % len(colors)]),
                marker=dict(size=5),
            ))

    elif chart_type == "bar":
        for i, col in enumerate(df_sweep.columns):
            fig.add_trace(go.Bar(
                x=df_sweep.index,
                y=df_sweep[col],
                name=col,
                marker_color=colors[i % len(colors)],
            ))
        fig.update_layout(barmode="group")

    elif chart_type == "scatter":
        for i, col in enumerate(df_sweep.columns):
            fig.add_trace(go.Scatter(
                x=df_sweep.index,
                y=df_sweep[col],
                mode="markers",
                name=col,
                marker=dict(color=colors[i % len(colors)], size=8, opacity=0.8),
            ))

    # Theme & layout
    fig.update_layout(
        template="plotly_dark" if st.get_option("theme.backgroundColor") == "#0e1117" else "plotly",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 8. Raw data ---
    with st.expander("Raw sensitivity data"):
        st.dataframe(df_sweep.style.format("{:.5f}"))
