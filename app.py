import streamlit as st
import math
import json

# Set Streamlit configuration as the first command
st.set_page_config(layout="wide")

# Initialize session state
if "inputs" not in st.session_state:
    st.session_state.inputs = {}
if "selected_formula" not in st.session_state:
    st.session_state.selected_formula = "oil_density_1"

# Conversion factors (main unit is Imperial for all formulas)
pressure_conversions = {
    "psia": 1.0,
    "bar": 14.5038,  # bar to psia
    "atm": 14.6959,  # atm to psia
    "kPa": 0.145038,  # kPa to psia
}
density_conversions = {
    "lbm/ft³": 1.0,
    "kg/m³": 0.06242796,  # kg/m³ to lbm/ft³
    "g/cm³": 62.42796,  # g/cm³ to lbm/ft³
}
temperature_conversions = {
    "°F": 1.0,
    "°C": lambda c: c * 9 / 5 + 32,  # °C to °F
    "K": lambda k: (k - 273.15) * 9 / 5 + 32,  # K to °F
}

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
def oil_density_1(Yo, Yg, Rs, Bo):
    ρo = (350 * Yo + 0.0764 * Yg * Rs) / (5.615 * Bo)
    return ρo

@st.cache_data
def oil_density_2(ρob, Co, Pb, P):
    if P < Pb:
        return None, "Pressure must be higher than bubble point pressure."
    ρo = ρob * math.exp(Co * (P - Pb))
    return ρo

@st.cache_data
def specific_gravity_3(Yapi):
    return 141.5 / (131.5 + Yapi)

# ... (other cached functions remain the same)

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

def number_input_with_conversion(label, min_val, max_val, value, step, help, main_unit, conversion_dict, formula_key, input_key):
    """Custom number input with alternative unit conversion."""
    main_value = st.number_input(f"{label} ({main_unit})", min_value=min_val, max_value=max_val, value=value, step=step, help=help, key=f"{formula_key}_{input_key}_main")
    
    # Alternative input
    st.markdown("**Alternative Unit Input (optional):**")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        alt_value = st.number_input("Value", value=0.0, key=f"{formula_key}_{input_key}_alt_value")
    with col2:
        alt_unit = st.selectbox("Unit", list(conversion_dict.keys())[1:], key=f"{formula_key}_{input_key}_alt_unit")  # Skip main unit
    with col3:
        if st.button("Convert", key=f"{formula_key}_{input_key}_convert"):
            if alt_value != 0.0:
                if isinstance(conversion_dict[alt_unit], (int, float)):
                    converted = alt_value * conversion_dict[alt_unit]
                else:
                    converted = conversion_dict[alt_unit](alt_value)
                st.session_state[f"{formula_key}_{input_key}_main"] = converted
                st.rerun()
    
    return main_value

def oil_density_1_ui():
    st.subheader("Oil Density (Basic)")
    formula_key = "oil_density_1"
    if formula_key not in st.session_state.inputs:
        st.session_state.inputs[formula_key] = {"Yo": 0.6, "Yg": 0.55, "Rs": 0.0, "Bo": 1.0}
    
    Yo = number_input_with_conversion(
        "Oil specific gravity", 0.6, 1.0, st.session_state.inputs[formula_key]["Yo"], 0.01, 
        "Ratio of oil density to water density at standard conditions.", "", {"": 1.0},  # No conversion for gravity
        formula_key, "Yo"
    )
    Yg = number_input_with_conversion(
        "Gas specific gravity", 0.55, 1.5, st.session_state.inputs[formula_key]["Yg"], 0.01, 
        "Ratio of gas density to air density at standard conditions.", "", {"": 1.0},  # No conversion
        formula_key, "Yg"
    )
    Rs = number_input_with_conversion(
        "Solution or dissolved gas", 0.0, 3000.0, st.session_state.inputs[formula_key]["Rs"], 1.0, 
        "Volume of gas dissolved in oil at standard conditions.", "scf/STB", {"scf/STB": 1.0},  # Add more if needed
        formula_key, "Rs"
    )
    Bo = number_input_with_conversion(
        "Oil formation volume factor", 1.0, 2.0, st.session_state.inputs[formula_key]["Bo"], 0.01, 
        "Ratio of oil volume at reservoir conditions to stock tank conditions.", "bbl/STB", {"bbl/STB": 1.0},
        formula_key, "Bo"
    )
    
    st.session_state.inputs[formula_key] = {"Yo": Yo, "Yg": Yg, "Rs": Rs, "Bo": Bo}
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Calculate Oil Density (Basic)", key=f"{formula_key}_calc"):
            ρo = oil_density_1(Yo, Yg, Rs, Bo)
            display_result(ρo, "lbm/cu ft", "Oil density")
    with col2:
        if st.button("Reset Inputs", key=f"{formula_key}_reset"):
            reset_inputs(formula_key)

def oil_density_2_ui():
    st.subheader("Oil Density (At Pressure)")
    formula_key = "oil_density_2"
    if formula_key not in st.session_state.inputs:
        st.session_state.inputs[formula_key] = {"ρob": 30.0, "Co": 1e-7, "Pb": 50.0, "P": 50.0}
    
    ρob = number_input_with_conversion(
        "Oil density at bubble point", 30.0, 60.0, st.session_state.inputs[formula_key]["ρob"], 0.1, 
        "Density of oil at bubble point pressure.", "lbm/ft³", density_conversions, 
        formula_key, "ρob"
    )
    Co = number_input_with_conversion(
        "Oil isothermal compressibility", 1e-7, 1e-3, st.session_state.inputs[formula_key]["Co"], 1e-7, 
        "Measure of oil volume change with pressure.", "psi^-1", {"psi^-1": 1.0, "bar^-1": 0.0689476},  # bar^-1 to psi^-1
        formula_key, "Co"
    )
    Pb = number_input_with_conversion(
        "Bubble point pressure", 50.0, 6000.0, st.session_state.inputs[formula_key]["Pb"], 1.0, 
        "Pressure at which gas begins to come out of solution.", "psia", pressure_conversions,
        formula_key, "Pb"
    )
    P = number_input_with_conversion(
        "Pressure", 50.0, 10000.0, st.session_state.inputs[formula_key]["P"], 1.0, 
        "Reservoir pressure of interest.", "psia", pressure_conversions,
        formula_key, "P"
    )
    
    st.session_state.inputs[formula_key] = {"ρob": ρob, "Co": Co, "Pb": Pb, "P": P}
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Calculate Oil Density (At Pressure)", key=f"{formula_key}_calc"):
            ρo, result = oil_density_2(ρob, Co, Pb, P)
            if ρo is None:
                st.error(result)
            else:
                display_result(ρo, "lbm/cu ft", "Oil density")
                # Generate plot (in main unit psia, lbm/ft³)
                pressures = list(range(int(Pb), int(min(P + 1000, 10000)), 100))
                densities = [ρob * math.exp(Co * (p - Pb)) for p in pressures]
                st.write("Oil Density vs. Pressure")
                st.markdown(
                    f"""
                    ```chartjs
                    {{
                        "type": "line",
                        "data": {{
                            "labels": {json.dumps(pressures)},
                            "datasets": [{{
                                "label": "Oil Density (lbm/ft³)",
                                "data": {json.dumps(densities)},
                                "borderColor": "#1f77b4",
                                "backgroundColor": "rgba(31, 119, 180, 0.2)",
                                "fill": true
                            }}]
                        }},
                        "options": {{
                            "scales": {{
                                "x": {{"title": {{"display": true, "text": "Pressure (psia)"}}}},
                                "y": {{"title": {{"display": true, "text": "Density (lbm/ft³)"}}}}
                            }}
                        }}
                    }}
                    ```
                    """
                )
    with col2:
        if st.button("Reset Inputs", key=f"{formula_key}_reset"):
            reset_inputs(formula_key)

# Similar updates for other UI functions, using number_input_with_conversion for each input

def help_section():
    # Unchanged
    pass

def main():
    st.title("Oil Properties Calculator")
    st.markdown("Select a formula from the **Formulas Menu** in the sidebar to compute oil and gas properties.")
    
    # Sidebar styling (unchanged)
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
    
    with st.sidebar.expander("Density Calculations", expanded=True):
        if st.button("Oil Density (Basic)", key="sidebar_oil_density_1"):
            st.session_state.selected_formula = "oil_density_1"
        if st.button("Oil Density (At Pressure)", key="sidebar_oil_density_2"):
            st.session_state.selected_formula = "oil_density_2"
        if st.button("Oil Specific Gravity from API", key="sidebar_specific_gravity_3"):
            st.session_state.selected_formula = "specific_gravity_3"
        if st.button("Mixture Density from Components", key="sidebar_composition_known_density_4"):
            st.session_state.selected_formula = "composition_known_density_4"
    
    with st.sidebar.expander("Bubble Point Correlations", expanded=True):
        if st.button("Standing Bubble Point Correlation", key="sidebar_standing_bubble_point_5"):
            st.session_state.selected_formula = "standing_bubble_point_5"
        if st.button("Lasater Bubble Point Correlation", key="sidebar_lasater_correlation"):
            st.session_state.selected_formula = "lasater_correlation"
        if st.button("Vasquez and Beggs Bubble Point Correlation", key="sidebar_vasquez_beggs_bubble_point"):
            st.session_state.selected_formula = "vasquez_beggs_bubble_point"
    
    with st.sidebar.expander("Help", expanded=True):
        if st.button("View Documentation", key="sidebar_help"):
            st.session_state.selected_formula = "help"
    
    # Formula options (add all)
    formula_options = {
        "oil_density_1": oil_density_1_ui,
        "oil_density_2": oil_density_2_ui,
        "specific_gravity_3": specific_gravity_3_ui,
        "help": help_section,
        # Add other formula UI functions
    }
    
    selected_formula = st.session_state.get("selected_formula", "oil_density_1")
    formula_options.get(selected_formula, oil_density_1_ui)()

if __name__ == "__main__":
    main()
