import streamlit as st
import math
import json

# Set Streamlit configuration as the first command
st.set_page_config(layout="wide")

# Initialize session state
if "inputs" not in st.session_state:
    st.session_state.inputs = {}
if "selected_unit_system" not in st.session_state:
    st.session_state.selected_unit_system = "Imperial"
if "selected_formula" not in st.session_state:
    st.session_state.selected_formula = "oil_density_1"

# Conversion factors
PSIA_TO_BAR = 0.0689476
BAR_TO_PSIA = 1 / PSIA_TO_BAR
F_TO_C = lambda f: (f - 32) * 5 / 9
C_TO_F = lambda c: c * 9 / 5 + 32

def get_valid_float(value, min_val=None, max_val=None, error_message=None):
    """Validate float input within specified range."""
    try:
        value = float(value)
        if min_val is not None and value < min_val:
            st.error(error_message or f"Value must be at least {min_val}.")
            return None
        if max_val is not None and value > max_val:
            st.error(error_message or f"Value must be at most {max_val}.")
            return None
        return value
    except (ValueError, TypeError):
        st.error(error_message or "Please enter a valid numeric value.")
        return None

@st.cache_data
def oil_density_1(Yo, Yg, Rs, Bo, unit_system="Imperial"):
    ρo = (350 * Yo + 0.0764 * Yg * Rs) / (5.615 * Bo)
    unit = "lbm/cu ft" if unit_system == "Imperial" else "kg/m³"
    if unit_system == "Metric":
        ρo *= 16.0185  # Convert lbm/cu ft to kg/m³
    return ρo, unit

@st.cache_data
def oil_density_2(ρob, Co, Pb, P, unit_system="Imperial"):
    if P < Pb:
        return None, "Pressure must be higher than bubble point pressure."
    ρo = ρob * math.exp(Co * (P - Pb))
    unit = "lbm/cu ft" if unit_system == "Imperial" else "kg/m³"
    if unit_system == "Metric":
        ρob *= 16.0185
        ρo *= 16.0185
    return ρo, unit

@st.cache_data
def specific_gravity_3(Yapi):
    return 141.5 / (131.5 + Yapi)

@st.cache_data
def composition_known_density_4(masses, densities, unit_system="Imperial"):
    total_mass = sum(masses)
    total_volume = sum(m / ρ for m, ρ in zip(masses, densities))
    if total_volume == 0:
        return None, "Total volume cannot be zero."
    ρt = total_mass / total_volume
    unit = "lbm/ft³" if unit_system == "Imperial" else "kg/m³"
    if unit_system == "Metric":
        ρt *= 16.0185
    return ρt, unit

@st.cache_data
def standing_bubble_point_5(Rsb, Yg, Tr, Yapi, unit_system="Imperial"):
    yg = 0.00091 * Tr - 0.0125 * Yapi
    Pb = 18 * ((Rsb / Yg) ** 0.83) * 10 ** yg
    unit = "psia" if unit_system == "Imperial" else "bar"
    if unit_system == "Metric":
        Pb *= PSIA_TO_BAR
    return Pb, unit

@st.cache_data
def lasater_correlation(Yapi, Rsb, Tr, unit_system="Imperial"):
    if Yapi <= 40:
        Mo = 630 - 10 * Yapi
    else:
        Mo = 73.110 * (Yapi ** -1.562)
    Yo = 141.5 / (131.5 + Yapi)
    Yg = (Rsb / 379.3) / ((Rsb / 379.3) + (350 * Yo / Mo))
    if not (0.574 <= Yg <= 1.223):
        return None, None, None, f"Gas specific gravity (Yg = {Yg:.5f}) is out of valid range (0.574 – 1.223)."
    if Yg <= 0.6:
        Pb = (0.679 * math.exp(2.786 * Yg) - 0.323) * Tr / Yg
    else:
        Pb = ((8.26 * Yg ** 3.56) + 1.95) * Tr / Yg
    if not (48 <= Pb <= 5780):
        return None, None, None, f"Bubble point pressure (Pb = {Pb:.2f}) is out of valid range (48 – 5780)."
    unit = "psia" if unit_system == "Imperial" else "bar"
    if unit_system == "Metric":
        Pb *= PSIA_TO_BAR
    return Mo, Yg, Pb, unit

def reset_inputs(formula_key):
    """Reset inputs for a specific formula."""
    if formula_key in st.session_state.inputs:
        del st.session_state.inputs[formula_key]
    st.rerun()

def display_result(value, unit, label):
    """Display calculation result in a styled container."""
    st.markdown(
        f"""
        <div style='background-color: #e6f3ff; padding: 10px; border-radius: 5px; margin: 10px 0;'>
            <strong>{label}:</strong> {value:.5f} {unit}
        </div>
        """,
        unsafe_allow_html=True
    )

def oil_density_1_ui():
    st.subheader("Oil Density (Basic)")
    formula_key = "oil_density_1"
    if formula_key not in st.session_state.inputs:
        st.session_state.inputs[formula_key] = {"Yo": 0.6, "Yg": 0.55, "Rs": 0.0, "Bo": 1.0}
    
    Yo = st.number_input("Oil specific gravity (0.6 to 1.0)", min_value=0.6, max_value=1.0, value=st.session_state.inputs[formula_key]["Yo"], step=0.01, key=f"{formula_key}_Yo", help="Ratio of oil density to water density at standard conditions.")
    Yg = st.number_input("Gas specific gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=st.session_state.inputs[formula_key]["Yg"], step=0.01, key=f"{formula_key}_Yg", help="Ratio of gas density to air density at standard conditions.")
    Rs = st.number_input("Solution or dissolved gas (0 to 3000 scf/STB)", min_value=0.0, max_value=3000.0, value=st.session_state.inputs[formula_key]["Rs"], step=1.0, key=f"{formula_key}_Rs", help="Volume of gas dissolved in oil at standard conditions.")
    Bo = st.number_input("Oil formation volume factor (1.0 to 2.0 bbl/STB)", min_value=1.0, max_value=2.0, value=st.session_state.inputs[formula_key]["Bo"], step=0.01, key=f"{formula_key}_Bo", help="Ratio of oil volume at reservoir conditions to stock tank conditions.")
    
    st.session_state.inputs[formula_key] = {"Yo": Yo, "Yg": Yg, "Rs": Rs, "Bo": Bo}
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Calculate Oil Density (Basic)", key=f"{formula_key}_calc"):
            ρo, unit = oil_density_1(Yo, Yg, Rs, Bo, st.session_state.selected_unit_system)
            display_result(ρo, unit, "Oil density")
    with col2:
        if st.button("Reset Inputs", key=f"{formula_key}_reset"):
            reset_inputs(formula_key)

def oil_density_2_ui():
    st.subheader("Oil Density (At Pressure)")
    formula_key = "oil_density_2"
    if formula_key not in st.session_state.inputs:
        st.session_state.inputs[formula_key] = {"ρob": 30.0, "Co": 1e-7, "Pb": 50.0, "P": 50.0}
    
    ρob = st.number_input(
        f"Oil density at bubble point (30 to 60 {'lbm/ft³' if st.session_state.selected_unit_system == 'Imperial' else 'kg/m³'})",
        min_value=30.0 if st.session_state.selected_unit_system == "Imperial" else 30.0 * 16.0185,
        max_value=60.0 if st.session_state.selected_unit_system == "Imperial" else 60.0 * 16.0185,
        value=st.session_state.inputs[formula_key]["ρob"],
        step=0.1,
        key=f"{formula_key}_ρob",
        help="Density of oil at bubble point pressure."
    )
    Co = st.number_input(
        f"Oil isothermal compressibility (1e-7 to 1e-3 {'psi^-1' if st.session_state.selected_unit_system == 'Imperial' else 'bar^-1'})",
        min_value=1e-7,
        max_value=1e-3,
        value=st.session_state.inputs[formula_key]["Co"],
        step=1e-7,
        format="%.7f",
        key=f"{formula_key}_Co",
        help="Measure of oil volume change with pressure."
    )
    Pb = st.number_input(
        f"Bubble point pressure (50 to 6000 {'psia' if st.session_state.selected_unit_system == 'Imperial' else 'bar'})",
        min_value=50.0 if st.session_state.selected_unit_system == "Imperial" else 50.0 * PSIA_TO_BAR,
        max_value=6000.0 if st.session_state.selected_unit_system == "Imperial" else 6000.0 * PSIA_TO_BAR,
        value=st.session_state.inputs[formula_key]["Pb"],
        step=1.0,
        key=f"{formula_key}_Pb",
        help="Pressure at which gas begins to come out of solution."
    )
    P = st.number_input(
        f"Pressure (50 to 10000 {'psia' if st.session_state.selected_unit_system == 'Imperial' else 'bar'})",
        min_value=50.0 if st.session_state.selected_unit_system == "Imperial" else 50.0 * PSIA_TO_BAR,
        max_value=10000.0 if st.session_state.selected_unit_system == "Imperial" else 10000.0 * PSIA_TO_BAR,
        value=st.session_state.inputs[formula_key]["P"],
        step=1.0,
        key=f"{formula_key}_P",
        help="Reservoir pressure of interest."
    )
    
    # Convert inputs to Imperial for calculation
    ρob_calc = ρob / 16.0185 if st.session_state.selected_unit_system == "Metric" else ρob
    Pb_calc = Pb / PSIA_TO_BAR if st.session_state.selected_unit_system == "Metric" else Pb
    P_calc = P / PSIA_TO_BAR if st.session_state.selected_unit_system == "Metric" else P
    
    st.session_state.inputs[formula_key] = {"ρob": ρob, "Co": Co, "Pb": Pb, "P": P}
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Calculate Oil Density (At Pressure)", key=f"{formula_key}_calc"):
            ρo, result = oil_density_2(ρob_calc, Co, Pb_calc, P_calc, st.session_state.selected_unit_system)
            if ρo is None:
                st.error(result)
            else:
                display_result(ρo, result, "Oil density")
                # Generate plot
                pressures = list(range(int(Pb_calc), int(min(P_calc + 1000, 10000)), 100))
                densities = [ρob_calc * math.exp(Co * (p - Pb_calc)) for p in pressures]
                if st.session_state.selected_unit_system == "Metric":
                    pressures = [p * PSIA_TO_BAR for p in pressures]
                    densities = [d * 16.0185 for d in densities]
                    p_unit = "bar"
                    d_unit = "kg/m³"
                else:
                    p_unit = "psia"
                    d_unit = "lbm/ft³"
                st.write("Oil Density vs. Pressure")
                st.markdown(
                    f"""
                    ```chartjs
                    {{
                        "type": "line",
                        "data": {{
                            "labels": {json.dumps(pressures)},
                            "datasets": [{{
                                "label": "Oil Density ({d_unit})",
                                "data": {json.dumps(densities)},
                                "borderColor": "#1f77b4",
                                "backgroundColor": "rgba(31, 119, 180, 0.2)",
                                "fill": true
                            }}]
                        }},
                        "options": {{
                            "scales": {{
                                "x": {{"title": {{"display": true, "text": "Pressure ({p_unit})"}}}},
                                "y": {{"title": {{"display": true, "text": "Density ({d_unit})"}}}}
                            }}
                        }}
                    }}
                    ```
                    """
                )
    with col2:
        if st.button("Reset Inputs", key=f"{formula_key}_reset"):
            reset_inputs(formula_key)

def specific_gravity_3_ui():
    st.subheader("Oil Specific Gravity from API")
    formula_key = "specific_gravity_3"
    if formula_key not in st.session_state.inputs:
        st.session_state.inputs[formula_key] = {"Yapi": 10.0}
    
    Yapi = st.number_input("Oil gravity (10 to 60 API)", min_value=10.0, max_value=60.0, value=st.session_state.inputs[formula_key]["Yapi"], step=0.1, key=f"{formula_key}_Yapi", help="API gravity of oil at standard conditions.")
    
    st.session_state.inputs[formula_key] = {"Yapi": Yapi}
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Calculate Oil Specific Gravity", key=f"{formula_key}_calc"):
            Yo = specific_gravity_3(Yapi)
            display_result(Yo, "", "Oil specific gravity")
    with col2:
        if st.button("Reset Inputs", key=f"{formula_key}_reset"):
            reset_inputs(formula_key)

def help_section():
    st.subheader("Help & Documentation")
    st.markdown("""
    This app calculates oil and gas properties using industry-standard correlations. Below are the formulas used:

    - **Oil Density (Basic)**: Calculates oil density using the formula `ρo = (350 * Yo + 0.0764 * Yg * Rs) / (5.615 * Bo)`.
    - **Oil Density (At Pressure)**: Computes density with compressibility: `ρo = ρob * exp(Co * (P - Pb))`.
    - **Oil Specific Gravity from API**: Converts API gravity to specific gravity: `Yo = 141.5 / (131.5 + Yapi)`.
    - **Mixture Density from Components**: Sums mass and volume: `ρt = Σmi / ΣVi`.
    - **Standing Bubble Point Correlation**: Uses `Pb = 18 * ((Rsb / Yg)^0.83) * 10^(0.00091*Tr - 0.0125*Yapi)`.

    For more details, refer to petroleum engineering references like Standing (1977), Lasater (1958), or Vasquez and Beggs (1980).
    """)

def main():
    st.title("Oil Properties Calculator")
    st.markdown("Select a formula from the **Formulas Menu** in the sidebar to compute oil and gas properties.")
    
    # Sidebar styling for permanent visibility and touch-friendliness
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            min-width: 400px;
            max-width: 500px;
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            overflow-y: auto;
            z-index: 9999;
        }
        [data-testid="stSidebarNav"] {
            position: sticky;
            top: 0;
        }
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        @media (max-width: 640px) {
            [data-testid="stSidebar"] {
                display: block !important;
                width: 300px !important;
                transform: translateX(0) !important;
            }
            [data-testid="stAppViewContainer"] {
                margin-left: 300px !important;
            }
        }
        .stNumberInput input {
            font-size: 16px;
            padding: 8px;
        }
        .stButton button {
            font-size: 16px;
            padding: 10px 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.header("Formulas Menu")
    unit_system = st.sidebar.selectbox("Unit System", ["Imperial", "Metric"], key="unit_system_select")
    if unit_system != st.session_state.selected_unit_system:
        st.session_state.selected_unit_system = unit_system
    
    with st.sidebar.expander("Density Calculations"):
        if st.button("Oil Density (Basic)", key="sidebar_oil_density_1"):
            st.session_state.selected_formula = "oil_density_1"
        if st.button("Oil Density (At Pressure)", key="sidebar_oil_density_2"):
            st.session_state.selected_formula = "oil_density_2"
        if st.button("Oil Specific Gravity from API", key="sidebar_specific_gravity_3"):
            st.session_state.selected_formula = "specific_gravity_3"
        if st.button("Mixture Density from Components", key="sidebar_composition_known_density_4"):
            st.session_state.selected_formula = "composition_known_density_4"
    
    with st.sidebar.expander("Bubble Point Correlations"):
        if st.button("Standing Bubble Point Correlation", key="sidebar_standing_bubble_point_5"):
            st.session_state.selected_formula = "standing_bubble_point_5"
        if st.button("Lasater Bubble Point Correlation", key="sidebar_lasater_correlation"):
            st.session_state.selected_formula = "lasater_correlation"
        if st.button("Vasquez and Beggs Bubble Point Correlation", key="sidebar_vasquez_beggs_bubble_point"):
            st.session_state.selected_formula = "vasquez_beggs_bubble_point"
    
    with st.sidebar.expander("Help"):
        if st.button("View Documentation", key="sidebar_help"):
            st.session_state.selected_formula = "help"
    
    # Formula options
    formula_options = {
        "oil_density_1": oil_density_1_ui,
        "oil_density_2": oil_density_2_ui,
        "specific_gravity_3": specific_gravity_3_ui,
        "help": help_section
        # Add other formula UI functions here
    }
    
    selected_formula = st.session_state.get("selected_formula", "oil_density_1")
    formula_options.get(selected_formula, oil_density_1_ui)()

if __name__ == "__main__":
    main()
