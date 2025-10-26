# app.py
import streamlit as st
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ------------------------------------------------------------------ #
# 1. Streamlit page config (must be first)
# ------------------------------------------------------------------ #
st.set_page_config(layout="wide")

# ------------------------------------------------------------------ #
# 2. Helper – safe float conversion (unchanged)
# ------------------------------------------------------------------ #
def get_valid_float(value, min_val=None, max_val=None, error_message=None):
    try:
        value = float(value)
        if min_val is not None and value < min_val:
            if error_message:
                st.error(error_message)
            return None
        if max_val is not None and value > max_val:
            if error_message:
                st.error(error_message)
            return None
        return value
    except (ValueError, TypeError):
        if error_message:
            st.error("Invalid input. Please enter a numeric value.")
        return None

# ------------------------------------------------------------------ #
# 3. ORIGINAL CALCULATORS (unchanged)
# ------------------------------------------------------------------ #
def oil_density_1():
    st.subheader("Oil Density (Basic)")
    Yo = st.number_input("Oil specific gravity (0.6 to 1.0)", min_value=0.6, max_value=1.0, value=0.6, step=0.01)
    Yg = st.number_input("Gas specific gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    Rs = st.number_input("Solution or dissolved gas (0 to 3000 scf/STB)", min_value=0.0, max_value=3000.0, value=0.0, step=1.0)
    Bo = st.number_input("Oil formation volume factor (1.0 to 2.0 bbl/STB)", min_value=1.0, max_value=2.0, value=1.0, step=0.01)
    if st.button("Calculate Oil Density (Basic)"):
        ρo = (350 * Yo + 0.0764 * Yg * Rs) / (5.615 * Bo)
        st.success(f"Oil density: {ρo:.5f} lbm/cu ft")

def oil_density_2():
    st.subheader("Oil Density (At Pressure)")
    ρob = st.number_input("Oil density at bubble point (30 to 60 lbm/ft³)", min_value=30.0, max_value=60.0, value=30.0, step=0.1)
    Co = st.number_input("Oil isothermal compressibility (1e-7 to 1e-3 psi^-1)", min_value=1e-7, max_value=1e-3, value=1e-7, step=1e-7, format="%.7f")
    Pb = st.number_input("Bubble point pressure (50 to 6000 psia)", min_value=50.0, max_value=6000.0, value=50.0, step=1.0)
    P = st.number_input("Pressure (50 to 10000 psia)", min_value=50.0, max_value=10000.0, value=50.0, step=1.0)
    if st.button("Calculate Oil Density (At Pressure)"):
        if P < Pb:
            st.error("Pressure must be higher than bubble point pressure.")
            return
        ρo = ρob * math.exp(Co * (P - Pb))
        st.success(f"Oil density: {ρo:.5f} lbm/cu ft")

def specific_gravity_3():
    st.subheader("Oil Specific Gravity from API")
    Yapi = st.number_input("Oil gravity (10 to 60 API)", min_value=10.0, max_value=60.0, value=10.0, step=0.1)
    if st.button("Calculate Oil Specific Gravity"):
        Yo = 141.5 / (131.5 + Yapi)
        st.success(f"Oil specific gravity: {Yo:.5f}")

def composition_known_density_4():
    st.subheader("Mixture Density from Components")
    C = st.number_input("Number of components (1 to 100)", min_value=1, max_value=100, value=1, step=1, format="%d")
    total_mass = 0.0
    total_volume = 0.0
    if C > 0:
        for i in range(1, C + 1):
            st.write(f"Component {i}:")
            m_i = st.number_input(f"Mass (0.1 to 1000 lbm) - Component {i}", min_value=0.1, max_value=1000.0, value=0.1, step=0.1, key=f"mass_{i}")
            ρ_i = st.number_input(f"Density at standard conditions (10 to 100 lbm/ft³) - Component {i}", min_value=10.0, max_value=100.0, value=10.0, step=0.1, key=f"density_{i}")
            V_i = m_i / ρ_i
            total_mass += m_i
            total_volume += V_i
    if st.button("Calculate Mixture Density"):
        if total_volume == 0:
            st.error("Total volume cannot be zero.")
            return
        ρt = total_mass / total_volume
        st.success(f"Mixture density: {ρt:.5f} lbm/ft³")

def standing_bubble_point_5():
    st.subheader("Standing Bubble Point Correlation")
    Rsb = st.number_input("Solution GOR at P > Pb (20 to 2000 scf/STB)", min_value=20.0, max_value=2000.0, value=20.0, step=1.0)
    Yg = st.number_input("Gas gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    Tr = st.number_input("Reservoir temperature (70 to 300 °F)", min_value=70.0, max_value=300.0, value=70.0, step=1.0)
    Yapi = st.number_input("Stock-tank oil gravity (10 to 60 API)", min_value=10.0, max_value=60.0, value=10.0, step=0.1)
    if st.button("Calculate Standing Bubble Point"):
        yg = 0.00091 * Tr - 0.0125 * Yapi
        Pb = 18 * ((Rsb / Yg) ** 0.83) * 10 ** yg
        st.success(f"Bubble point pressure: {Pb:.5f} psia")

def lasater_correlation():
    st.subheader("Lasater Bubble Point Correlation")
    Yapi = st.number_input("Oil gravity (17.9 to 51.1 API)", min_value=17.9, max_value=51.1, value=17.9, step=0.1)
    Rsb = st.number_input("Solution GOR (3 to 2905 scf/STB)", min_value=3.0, max_value=2905.0, value=3.0, step=1.0)
    Tr = st.number_input("Reservoir temperature (82 to 272 °F)", min_value=82.0, max_value=272.0, value=82.0, step=1.0)
    if st.button("Calculate Lasater Bubble Point"):
        if Yapi <= 40:
            Mo = 630 - 10 * Yapi
        else:
            Mo = 73.110 * (Yapi ** -1.562)
        Yo = 141.5 / (131.5 + Yapi)
        Yg = (Rsb / 379.3) / ((Rsb / 379.3) + (350 * Yo / Mo))
        if not (0.574 <= Yg <= 1.223):
            st.error(f"Gas specific gravity (Yg = {Yg:.5f}) is out of valid range (0.574 – 1.223).")
            return
        if Yg <= 0.6:
            Pb = (0.679 * math.exp(2.786 * Yg) - 0.323) * Tr / Yg
        else:
            Pb = ((8.26 * Yg ** 3.56) + 1.95) * Tr / Yg
        if not (48 <= Pb <= 5780):
            st.error(f"Bubble point pressure (Pb = {Pb:.2f}) is out of valid range (48 – 5780).")
            return
        st.success(f"Molecular weight: {Mo:.5f} g/mol")
        st.success(f"Gas specific gravity (Yg): {Yg:.5f}")
        st.success(f"Bubble point pressure (Pb): {Pb:.2f} psia")

def vasquez_beggs_bubble_point():
    st.subheader("Vasquez and Beggs Bubble Point Correlation")
    Yg = st.number_input("Gas specific gravity at Ps and Ts (0.56 to 1.18)", min_value=0.56, max_value=1.18, value=0.56, step=0.01)
    Ts = st.number_input("Separator temperature (70 to 295 °F)", min_value=70.0, max_value=295.0, value=70.0, step=1.0)
    Ps = st.number_input("Separator pressure (15 to 1000 psi)", min_value=15.0, max_value=1000.0, value=15.0, step=1.0)
    Yapi = st.number_input("Oil gravity (16 to 58 API)", min_value=16.0, max_value=58.0, value=16.0, step=0.1)
    Rsb = st.number_input("Solution GOR (20 to 2070 scf/STB)", min_value=20.0, max_value=2070.0, value=20.0, step=1.0)
    Tr = st.number_input("Reservoir temperature (70 to 295 °F)", min_value=70.0, max_value=295.0, value=70.0, step=1.0)
    if st.button("Calculate Vasquez and Beggs Bubble Point"):
        try:
            Ygc = Yg * (1 + 5.912e-5 * Yapi * Ts * math.log(Ps / 114.7))
        except ValueError:
            st.error("Invalid log value — make sure Ps > 0.")
            return
        if Yapi <= 30:
            C1 = 0.0362
            C2 = 1.0937
            C3 = 25.72
        else:
            C1 = 0.0178
            C2 = 1.187
            C3 = 23.931
        try:
            Pb = (Rsb / (C1 * Yg * math.exp(C3 * Yapi / (Tr + 460)))) ** (1 / C2)
        except (ValueError, ZeroDivisionError, OverflowError):
            st.error("Error calculating Pb. Check input values.")
            return
        if not (50 <= Pb <= 5250):
            st.error(f"Bubble point pressure (Pb = {Pb:.2f}) is out of valid range (50 – 5250).")
            return
        st.success(f"Corrected gas gravity (Ygc): {Ygc:.5f}")
        st.success(f"Bubble point pressure (Pb): {Pb:.5f} psia")

def standing_rs_correlation():
    st.subheader("Standing Rs Correlation")
    p = st.number_input("Pressure (50 to 10000 psia)", min_value=50.0, max_value=10000.0, value=50.0, step=1.0)
    Tr = st.number_input("Reservoir temperature (70 to 300 °F)", min_value=70.0, max_value=300.0, value=70.0, step=1.0)
    Yapi = st.number_input("Oil gravity (10 to 60 API)", min_value=10.0, max_value=60.0, value=10.0, step=0.1)
    if st.button("Calculate Standing Rs"):
        Yg = 0.00091 * Tr - 0.0125 * Yapi
        Rs = Yg * (p / (18 * 10 ** Yg)) ** 1.204
        st.success(f"Solution GOR: {Rs:.5f} scf/STB")

def lasater_rs_correlation():
    st.subheader("Lasater Rs Correlation")
    Yo = st.number_input("Oil specific gravity (0.6 to 1.0)", min_value=0.6, max_value=1.0, value=0.6, step=0.01)
    Yg = st.number_input("Gas specific gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    Mo = st.number_input("Molecular weight of oil (100 to 600 g/mol)", min_value=100.0, max_value=600.0, value=100.0, step=1.0)
    if st.button("Calculate Lasater Rs"):
        Rs = (132755 * Yo * Yg) / (Mo * (1 - Yg))
        st.success(f"Solution GOR: {Rs:.5f} scf/STB")

def vasquez_beggs_rs_correlation():
    st.subheader("Vasquez and Beggs Rs Correlation")
    Yg = st.number_input("Gas specific gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    p = st.number_input("Pressure (50 to 10000 psia)", min_value=50.0, max_value=10000.0, value=50.0, step=1.0)
    Yapi = st.number_input("Oil gravity (10 to 60 API)", min_value=10.0, max_value=60.0, value=10.0, step=0.1)
    T = st.number_input("Reservoir temperature (70 to 300 °F)", min_value=70.0, max_value=300.0, value=70.0, step=1.0)
    if st.button("Calculate Vasquez and Beggs Rs"):
        if Yapi <= 30:
            C1 = 0.0362
            C2 = 1.0937
            C3 = 25.72
        else:
            C1 = 0.0178
            C2 = 1.187
            C3 = 23.931
        Rs = C1 * Yg * (p ** C2) * math.exp((C3 * Yapi) / (T + 460))
        st.success(f"Solution GOR: {Rs:.5f} scf/STB")

def standing_fvf():
    st.subheader("Standing Oil Formation Volume Factor")
    Rs = st.number_input("Solution GOR (0 to 3000 scf/STB)", min_value=0.0, max_value=3000.0, value=0.0, step=1.0)
    Yg = st.number_input("Gas specific gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    Yo = st.number_input("Oil specific gravity (0.6 to 1.0)", min_value=0.6, max_value=1.0, value=0.6, step=0.01)
    T = st.number_input("Reservoir temperature (70 to 300 °F)", min_value=70.0, max_value=300.0, value=70.0, step=1.0)
    if st.button("Calculate Standing FVF"):
        F = Rs * ((Yg / Yo) ** 0.5) + 1.25 * T
        Bo = 0.972 + 0.000147 * (F ** 1.175)
        st.success(f"Oil formation volume factor: {Bo:.5f} bbl/STB")

def vasquez_beggs_fvf():
    st.subheader("Vasquez and Beggs Oil Formation Volume Factor")
    Rs = st.number_input("Solution GOR (20 to 2070 scf/STB)", min_value=20.0, max_value=2070.0, value=20.0, step=1.0)
    T = st.number_input("Temperature (70 to 295 °F)", min_value=70.0, max_value=295.0, value=70.0, step=1.0)
    Yapi = st.number_input("Stock tank oil gravity (16 to 58 API)", min_value=16.0, max_value=58.0, value=16.0, step=0.1)
    Ygc = st.number_input("Corrected gas gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    if st.button("Calculate Vasquez and Beggs FVF"):
        if Yapi <= 30:
            C1 = 0.0004677
            C2 = 0.00001751
            C3 = -0.00000001811
        else:
            C1 = 0.000467
            C2 = 0.000011
            C3 = 0.000000001337
        Bo = 1 + C1 * Rs + C2 * (T - 60) * (Yapi / Ygc) + C3 * Rs * (T - 60) * (Yapi / Ygc)
        st.success(f"Oil formation volume factor (Bo): {Bo:.5f} bbl/STB")

def oil_fvf():
    st.subheader("Oil Formation Volume Factor (General)")
    Bob = st.number_input("Bo at bubble point pressure (1.0 to 2.0 bbl/STB)", min_value=1.0, max_value=2.0, value=1.0, step=0.01)
    Pb = st.number_input("Bubble point pressure (50 to 6000 psia)", min_value=50.0, max_value=6000.0, value=50.0, step=1.0)
    p = st.number_input("Current pressure (50 to 10000 psia)", min_value=50.0, max_value=10000.0, value=50.0, step=1.0)
    co = st.number_input("Oil compressibility (1e-7 to 1e-3 1/psi)", min_value=1e-7, max_value=1e-3, value=1e-7, step=1e-7, format="%.7f")
    if st.button("Calculate Oil FVF"):
        exponent = co * (Pb - p)
        if abs(exponent) > 700:
            st.error("Exponent in calculation is too large, likely to cause overflow. Please check input values.")
            return
        Bo = Bob * math.exp(exponent)
        st.success(f"Oil formation volume factor at pressure {p} psia: {Bo:.5f} bbl/STB")

def vasquez_beggs_oil_compressibility():
    st.subheader("Vasquez and Beggs Oil Isothermal Compressibility")
    Rsb = st.number_input("Solution GOR (20 to 2070 scf/STB)", min_value=20.0, max_value=2070.0, value=20.0, step=1.0)
    T = st.number_input("Temperature (70 to 295 °F)", min_value=70.0, max_value=295.0, value=70.0, step=1.0)
    Yg = st.number_input("Gas gravity (0.55 to 1.5)", min_value=0.55, max_value=1.5, value=0.55, step=0.01)
    Yapi = st.number_input("Oil gravity (16 to 58 API)", min_value=16.0, max_value=58.0, value=16.0, step=0.1)
    p = st.number_input("Pressure of interest (50 to 10000 psia)", min_value=50.0, max_value=10000.0, value=50.0, step=1.0)
    if st.button("Calculate Oil Compressibility"):
        co = (5 * Rsb + 17.2 * T - 1180 * Yg + 12.61 * Yapi - 1433) / (p * 1e5)
        st.success(f"Oil isothermal compressibility (co): {co:.8f} 1/psi")

def beggs_robinson_viscosity():
    st.subheader("Beggs and Robinson Oil Viscosity")
    Rsb = st.number_input("Solution GOR (20 to 2070 scf/STB)", min_value=20.0, max_value=2070.0, value=20.0, step=1.0)
    T = st.number_input("Temperature (70 to 295 °F)", min_value=70.0, max_value=295.0, value=70.0, step=1.0)
    Yapi = st.number_input("Oil gravity (16 to 58 API)", min_value=16.0, max_value=58.0, value=16.0, step=0.1)
    if st.button("Calculate Beggs and Robinson Viscosity"):
        x = T ** (-1.163) * math.exp(6.9824 - 0.04658 * Yapi)
        mu_od = 10 ** x - 1.0
        A = 10.715 * (Rsb + 100) ** (-0.515)
        B = 5.44 * (Rsb + 150) ** (-0.338)
        mu_os = A * mu_od ** B
        st.success(f"Dead-oil viscosity (μod): {mu_od:.4f} cP")
        st.success(f"Saturated-oil viscosity (μos): {mu_os:.4f} cP")

def vasquez_beggs_undersaturated_viscosity():
    st.subheader("Vasquez and Beggs Undersaturated Oil Viscosity")
    mu_ob = st.number_input("Saturated oil viscosity at bubble point (0.1 to 100 cP)", min_value=0.1, max_value=100.0, value=0.1, step=0.1)
    p = st.number_input("Pressure of interest (50 to 10000 psia)", min_value=50.0, max_value=10000.0, value=50.0, step=1.0)
    pb = st.number_input("Bubble point pressure (50 to 6000 psia)", min_value=50.0, max_value=6000.0, value=50.0, step=1.0)
    if st.button("Calculate Undersaturated Viscosity"):
        C1 = 2.6
        C2 = 1.187
        C3 = -11.513
        C4 = -8.98e-5
        m = C1 * p ** C2 * math.exp(C3 + C4 * p)
        mu_o = mu_ob * (p / pb) ** m
        st.success(f"Undersaturated oil viscosity (μo): {mu_o:.4f} cP")

# ------------------------------------------------------------------ #
# 4. LIVE SENSITIVITY ANALYZER
# ------------------------------------------------------------------ #
def live_sensitivity_analyzer():
    st.subheader("Live Sensitivity Analyzer")
    formula_options = {
        "Oil Density (Basic)": oil_density_1_live,
        "Oil Density (At Pressure)": oil_density_2_live,
        "Oil Specific Gravity from API": specific_gravity_3_live,
        "Mixture Density from Components": composition_known_density_4_live,
        "Standing Bubble Point": standing_bubble_point_5_live,
        "Lasater Bubble Point": lasater_correlation_live,
        "Vasquez & Beggs Bubble Point": vasquez_beggs_bubble_point_live,
        "Standing Rs": standing_rs_correlation_live,
        "Lasater Rs": lasater_rs_correlation_live,
        "Vasquez & Beggs Rs": vasquez_beggs_rs_correlation_live,
        "Standing FVF": standing_fvf_live,
        "Vasquez & Beggs FVF": vasquez_beggs_fvf_live,
        "Oil FVF (General)": oil_fvf_live,
        "Vasquez & Beggs Compressibility": vasquez_beggs_oil_compressibility_live,
        "Beggs & Robinson Viscosity": beggs_robinson_viscosity_live,
        "Vasquez & Beggs Undersaturated Viscosity": vasquez_beggs_undersaturated_viscosity_live,
    }
    selected = st.selectbox("Select formula to analyze", options=list(formula_options.keys()))
    formula_options[selected]()

# ------------------------------------------------------------------ #
# 5. LIVE WRAPPERS (all fixed)
# ------------------------------------------------------------------ #
def oil_density_1_live():
    inputs = {
        "Yo": {"min":0.6,"max":1.0,"step":0.01,"value":0.8,"unit":""},
        "Yg": {"min":0.55,"max":1.5,"step":0.01,"value":0.7,"unit":""},
        "Rs": {"min":0.0,"max":3000.0,"step":10.0,"value":200.0,"unit":"scf/STB"},
        "Bo": {"min":1.0,"max":2.0,"step":0.01,"value":1.2,"unit":"bbl/STB"},
    }
    def calc(v):
        ρo = (350*v["Yo"] + 0.0764*v["Yg"]*v["Rs"]) / (5.615*v["Bo"])
        return {"result":ρo,"unit":"lbm/ft³"}
    _live_module("Oil Density (Basic)", inputs, calc)

def oil_density_2_live():
    inputs = {
        "ρob": {"min":30.0,"max":60.0,"step":0.1,"value":45.0,"unit":"lbm/ft³"},
        "Co": {"min":1e-7,"max":1e-3,"step":1e-7,"value":1e-6,"unit":"1/psi"},
        "Pb": {"min":50.0,"max":6000.0,"step":10.0,"value":2000.0,"unit":"psia"},
        "P": {"min":50.0,"max":10000.0,"step":10.0,"value":3000.0,"unit":"psia"},
    }
    def calc(v):
        if v["P"] < v["Pb"]: return {"result":None,"unit":""}
        ρo = v["ρob"] * math.exp(v["Co"]*(v["P"]-v["Pb"]))
        return {"result":ρo,"unit":"lbm/ft³"}
    _live_module("Oil Density (At Pressure)", inputs, calc)

def specific_gravity_3_live():
    inputs = {"Yapi": {"min":10.0,"max":60.0,"step":0.1,"value":30.0,"unit":"API"}}
    def calc(v):
        Yo = 141.5 / (131.5 + v["Yapi"])
        return {"result":Yo,"unit":""}
    _live_module("Oil Specific Gravity from API", inputs, calc)

def composition_known_density_4_live():
    inputs = {"C": {"min":1,"max":5,"step":1,"value":2,"unit":"components"}}
    def calc(v):
        C = int(v["C"])
        total_mass = total_vol = 0.0
        for i in range(1, C+1):
            m = st.session_state.get(f"mass_{i}", 10.0)
            ρ = st.session_state.get(f"dens_{i}", 50.0)
            total_mass += m
            total_vol += m / ρ
        return {"result": total_mass/total_vol if total_vol > 0 else None, "unit": "lbm/ft³"}
    _live_module("Mixture Density from Components", inputs, calc, dynamic_components=True)

def standing_bubble_point_5_live():
    inputs = {
        "Rsb": {"min":20.0,"max":2000.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "Yg": {"min":0.55,"max":1.5,"step":0.01,"value":0.7,"unit":""},
        "Tr": {"min":70.0,"max":300.0,"step":1.0,"value":180.0,"unit":"°F"},
        "Yapi": {"min":10.0,"max":60.0,"step":0.1,"value":30.0,"unit":"API"},
    }
    def calc(v):
        yg = 0.00091 * v["Tr"] - 0.0125 * v["Yapi"]
        Pb = 18 * ((v["Rsb"] / v["Yg"]) ** 0.83) * 10 ** yg
        return {"result": Pb, "unit": "psia"}
    _live_module("Standing Bubble Point", inputs, calc)

def lasater_correlation_live():
    inputs = {
        "Yapi": {"min":17.9,"max":51.1,"step":0.1,"value":30.0,"unit":"API"},
        "Rsb": {"min":3.0,"max":2905.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "Tr": {"min":82.0,"max":272.0,"step":1.0,"value":150.0,"unit":"°F"},
    }
    def calc(v):
        if v["Yapi"] <= 40:
            Mo = 630 - 10 * v["Yapi"]
        else:
            Mo = 73.110 * (v["Yapi"] ** -1.562)
        Yo = 141.5 / (131.5 + v["Yapi"])
        Yg = (v["Rsb"] / 379.3) / ((v["Rsb"] / 379.3) + (350 * Yo / Mo))
        if Yg <= 0.6:
            Pb = (0.679 * math.exp(2.786 * Yg) - 0.323) * v["Tr"] / Yg
        else:
            Pb = ((8.26 * Yg ** 3.56) + 1.95) * v["Tr"] / Yg
        return {"result": Pb, "unit": "psia"}
    _live_module("Lasater Bubble Point", inputs, calc)

def vasquez_beggs_bubble_point_live():
    inputs = {
        "Yg": {"min":0.56,"max":1.18,"step":0.01,"value":0.8,"unit":""},
        "Ts": {"min":70.0,"max":295.0,"step":1.0,"value":120.0,"unit":"°F"},
        "Ps": {"min":15.0,"max":1000.0,"step":1.0,"value":100.0,"unit":"psi"},
        "Yapi": {"min":16.0,"max":58.0,"step":0.1,"value":30.0,"unit":"API"},
        "Rsb": {"min":20.0,"max":2070.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "Tr": {"min":70.0,"max":295.0,"step":1.0,"value":180.0,"unit":"°F"},
    }
    def calc(v):
        Ygc = v["Yg"] * (1 + 5.912e-5 * v["Yapi"] * v["Ts"] * math.log(v["Ps"] / 114.7))
        if v["Yapi"] <= 30:
            C1, C2, C3 = 0.0362, 1.0937, 25.72
        else:
            C1, C2, C3 = 0.0178, 1.187, 23.931
        Pb = (v["Rsb"] / (C1 * v["Yg"] * math.exp(C3 * v["Yapi"] / (v["Tr"] + 460)))) ** (1 / C2)
        return {"result": Pb, "unit": "psia"}
    _live_module("Vasquez & Beggs Bubble Point", inputs, calc)

def standing_rs_correlation_live():
    inputs = {
        "p": {"min":50.0,"max":10000.0,"step":10.0,"value":2000.0,"unit":"psia"},
        "Tr": {"min":70.0,"max":300.0,"step":1.0,"value":180.0,"unit":"°F"},
        "Yapi": {"min":10.0,"max":60.0,"step":0.1,"value":30.0,"unit":"API"},
    }
    def calc(v):
        Yg = 0.00091 * v["Tr"] - 0.0125 * v["Yapi"]
        Rs = Yg * (v["p"] / (18 * 10 ** Yg)) ** 1.204
        return {"result": Rs, "unit": "scf/STB"}
    _live_module("Standing Rs", inputs, calc)

def lasater_rs_correlation_live():
    inputs = {
        "Yo": {"min":0.6,"max":1.0,"step":0.01,"value":0.85,"unit":""},
        "Yg": {"min":0.55,"max":1.5,"step":0.01,"value":0.7,"unit":""},
        "Mo": {"min":100.0,"max":600.0,"step":1.0,"value":200.0,"unit":"g/mol"},
    }
    def calc(v):
        Rs = (132755 * v["Yo"] * v["Yg"]) / (v["Mo"] * (1 - v["Yg"]))
        return {"result": Rs, "unit": "scf/STB"}
    _live_module("Lasater Rs", inputs, calc)

def vasquez_beggs_rs_correlation_live():
    inputs = {
        "Yg": {"min":0.55,"max":1.5,"step":0.01,"value":0.7,"unit":""},
        "p": {"min":50.0,"max":10000.0,"step":10.0,"value":2000.0,"unit":"psia"},
        "Yapi": {"min":10.0,"max":60.0,"step":0.1,"value":30.0,"unit":"API"},
        "T": {"min":70.0,"max":300.0,"step":1.0,"value":180.0,"unit":"°F"},
    }
    def calc(v):
        C1 = 0.0362 if v["Yapi"] <= 30 else 0.0178
        C2 = 1.0937 if v["Yapi"] <= 30 else 1.187
        C3  = 25.72 if v["Yapi"] <= 30 else 23.931
        Rs = C1 * v["Yg"] * (v["p"] ** C2) * math.exp((C3 * v["Yapi"]) / (v["T"] + 460))
        return {"result": Rs, "unit": "scf/STB"}
    _live_module("Vasquez & Beggs Rs", inputs, calc)

def standing_fvf_live():
    inputs = {
        "Rs": {"min":0.0,"max":3000.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "Yg": {"min":0.55,"max":1.5,"step":0.01,"value":0.7,"unit":""},
        "Yo": {"min":0.6,"max":1.0,"step":0.01,"value":0.85,"unit":""},
        "T": {"min":70.0,"max":300.0,"step":1.0,"value":180.0,"unit":"°F"},
    }
    def calc(v):
        F = v["Rs"] * ((v["Yg"] / v["Yo"]) ** 0.5) + 1.25 * v["T"]
        Bo = 0.972 + 0.000147 * (F ** 1.175)
        return {"result": Bo, "unit": "bbl/STB"}
    _live_module("Standing FVF", inputs, calc)

def vasquez_beggs_fvf_live():
    inputs = {
        "Rs": {"min":20.0,"max":2070.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "T": {"min":70.0,"max":295.0,"step":1.0,"value":180.0,"unit":"°F"},
        "Yapi": {"min":16.0,"max":58.0,"step":0.1,"value":30.0,"unit":"API"},
        "Ygc": {"min":0.55,"max":1.5,"step":0.01,"value":0.8,"unit":""},
    }
    def calc(v):
        C1 = 0.0004677 if v["Yapi"] <= 30 else 0.000467
        C2 = 0.00001751 if v["Yapi"] <= 30 else 0.000011
        C3 = -0.00000001811 if v["Yapi"] <= 30 else 0.000000001337
        Bo = 1 + C1 * v["Rs"] + C2 * (v["T"] - 60) * (v["Yapi"] / v["Ygc"]) + C3 * v["Rs"] * (v["T"] - 60) * (v["Yapi"] / v["Ygc"])
        return {"result": Bo, "unit": "bbl/STB"}
    _live_module("Vasquez & Beggs FVF", inputs, calc)

def oil_fvf_live():
    inputs = {
        "Bob": {"min":1.0,"max":2.0,"step":0.01,"value":1.2,"unit":"bbl/STB"},
        "Pb": {"min":50.0,"max":6000.0,"step":10.0,"value":2000.0,"unit":"psia"},
        "p": {"min":50.0,"max":10000.0,"step":10.0,"value":3000.0,"unit":"psia"},
        "co": {"min":1e-7,"max":1e-3,"step":1e-7,"value":1e-6,"unit":"1/psi"},
    }
    def calc(v):
        exp = v["co"] * (v["Pb"] - v["p"])
        if abs(exp) > 700: return {"result": None, "unit": ""}
        Bo = v["Bob"] * math.exp(exp)
        return {"result": Bo, "unit": "bbl/STB"}
    _live_module("Oil FVF (General)", inputs, calc)

def vasquez_beggs_oil_compressibility_live():
    inputs = {
        "Rsb": {"min":20.0,"max":2070.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "T": {"min":70.0,"max":295.0,"step":1.0,"value":180.0,"unit":"°F"},
        "Yg": {"min":0.55,"max":1.5,"step":0.01,"value":0.7,"unit":""},
        "Yapi": {"min":16.0,"max":58.0,"step":0.1,"value":30.0,"unit":"API"},
        "p": {"min":50.0,"max":10000.0,"step":10.0,"value":2000.0,"unit":"psia"},
    }
    def calc(v):
        co = (5 * v["Rsb"] + 17.2 * v["T"] - 1180 * v["Yg"] + 12.61 * v["Yapi"] - 1433) / (v["p"] * 1e5)
        return {"result": co, "unit": "1/psi"}
    _live_module("Vasquez & Beggs Compressibility", inputs, calc)

def beggs_robinson_viscosity_live():
    inputs = {
        "Rsb": {"min":20.0,"max":2070.0,"step":10.0,"value":500.0,"unit":"scf/STB"},
        "T": {"min":70.0,"max":295.0,"step":1.0,"value":180.0,"unit":"°F"},
        "Yapi": {"min":16.0,"max":58.0,"step":0.1,"value":30.0,"unit":"API"},
    }
    def calc(v):
        x = v["T"] ** (-1.163) * math.exp(6.9824 - 0.04658 * v["Yapi"])
        mu_od = 10 ** x - 1.0
        A = 10.715 * (v["Rsb"] + 100) ** (-0.515)
        B = 5.44 * (v["Rsb"] + 150) ** (-0.338)
        mu_os = A * mu_od ** B
        return {"result": mu_os, "unit": "cP"}
    _live_module("Beggs & Robinson Viscosity", inputs, calc)

def vasquez_beggs_undersaturated_viscosity_live():
    inputs = {
        "mu_ob": {"min":0.1,"max":100.0,"step":0.1,"value":1.0,"unit":"cP"},
        "p": {"min":50.0,"max":10000.0,"step":10.0,"value":3000.0,"unit":"psia"},
        "pb": {"min":50.0,"max":6000.0,"step":10.0,"value":2000.0,"unit":"psia"},
    }
    def calc(v):
        m = 2.6 * v["p"] ** 1.187 * math.exp(-11.513 - 8.98e-5 * v["p"])
        mu_o = v["mu_ob"] * (v["p"] / v["pb"]) ** m
        return {"result": mu_o, "unit": "cP"}
    _live_module("Vasquez & Beggs Undersaturated Viscosity", inputs, calc)

# ------------------------------------------------------------------ #
# 6. GENERIC LIVE MODULE
# ------------------------------------------------------------------ #
def _live_module(title, inputs, compute, default_chart="polar", dynamic_components=False):
    st.markdown(f"### {title} – Live Sensitivity")
    vals = {}
    for k, cfg in inputs.items():
        vals[k] = st.slider(
            f"{k} ({cfg.get('unit','')})",
            min_value=cfg["min"], max_value=cfg["max"],
            value=cfg["value"], step=cfg["step"],
            key=f"live_{title}_{k}"
        )
    if dynamic_components:
        C = int(vals.get("C", 1))
        for i in range(1, C+1):
            st.session_state[f"mass_{i}"] = st.slider(f"Mass comp {i}", 0.1, 1000.0, 10.0, 0.1, key=f"mass_{i}")
            st.session_state[f"dens_{i}"] = st.slider(f"Density comp {i}", 10.0, 100.0, 50.0, 0.1, key=f"dens_{i}")

    out = compute(vals)
    result = out.get("result")
    if result is not None:
        st.success(f"**Result:** {result:.5f} {out.get('unit','')}")

    sweep_key = st.selectbox("Sweep variable", options=list(inputs.keys()), key=f"sweep_{title}")
    npts = 50
    sweep_vals = np.linspace(inputs[sweep_key]["min"], inputs[sweep_key]["max"], npts)
    series = {"Result": []}
    fixed = {k: v for k, v in vals.items() if k != sweep_key}
    for sv in sweep_vals:
        fixed[sweep_key] = sv
        res = compute(fixed)
        series["Result"].append(res.get("result") or 0)
    df = pd.DataFrame(series, index=sweep_vals)
    df.index.name = sweep_key

    chart_type = st.radio("Chart type", ["polar", "line", "bar", "radar", "scatter"],
                          index=["polar","line","bar","radar","scatter"].index(default_chart),
                          horizontal=True, key=f"ctype_{title}")

    fig = go.Figure()
    colors = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd"]
    if chart_type == "polar":
        shift = abs(df.min().min()) + 1 if (df<0).any().any() else 0
        fig.add_trace(go.Scatterpolar(r=df["Result"]+shift, theta=df.index, mode="lines", name="Result", line=dict(color=colors[0])))
        fig.update_layout(polar=dict(radialaxis=dict(range=[shift, df.max().max()+shift])))
    elif chart_type == "line":
        fig.add_trace(go.Scatter(x=df.index, y=df["Result"], mode="lines+markers", name="Result"))
    elif chart_type == "bar":
        fig.add_trace(go.Bar(x=df.index, y=df["Result"], name="Result", marker_color=colors[0]))
        fig.update_layout(barmode="group")
    elif chart_type == "radar":
        fig.add_trace(go.Scatterpolar(r=df["Result"].tolist()+[df["Result"].iloc[0]], theta=df.index.tolist()+[df.index[0]], fill="toself", name="Result"))
    elif chart_type == "scatter":
        fig.add_trace(go.Scatter(x=df.index, y=df["Result"], mode="markers", name="Result"))

    fig.update_layout(height=500, template="plotly_dark" if st.get_option("theme.backgroundColor")=="#0e1117" else "plotly")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Raw data"):
        st.dataframe(df.style.format("{:.5f}"))

# ------------------------------------------------------------------ #
# 7. MAIN
# ------------------------------------------------------------------ #
def main():
    st.title("Oil Properties Calculator")
    st.markdown("Select a formula from the sidebar to compute oil and gas properties.")

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {min-width:400px; max-width:500px; position:fixed; top:0; left:0; height:100vh; overflow-y:auto; z-index:9999;}
        [data-testid="stSidebarNav"] {position:sticky; top:0;}
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {display:none !important;}
        @media (max-width: 640px) {
            [data-testid="stSidebar"] {display:block !important; width:400px !important; transform:translateX(0)!important;}
            [data-testid="stAppViewContainer"] {margin-left:400px !important;}
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.header("Formulas Menu")
    menu_options = {
        "Oil Density (Basic)": oil_density_1,
        "Oil Density (At Pressure)": oil_density_2,
        "Oil Specific Gravity from API": specific_gravity_3,
        "Mixture Density from Components": composition_known_density_4,
        "Standing Bubble Point Correlation": standing_bubble_point_5,
        "Lasater Bubble Point Correlation": lasater_correlation,
        "Vasquez and Beggs Bubble Point Correlation": vasquez_beggs_bubble_point,
        "Standing Rs Correlation": standing_rs_correlation,
        "Lasater Rs Correlation": lasater_rs_correlation,
        "Vasquez and Beggs Rs Correlation": vasquez_beggs_rs_correlation,
        "Standing Oil Formation Volume Factor": standing_fvf,
        "Vasquez and Beggs Oil Formation Volume Factor": vasquez_beggs_fvf,
        "Oil Formation Volume Factor (General)": oil_fvf,
        "Vasquez and Beggs Oil Isothermal Compressibility": vasquez_beggs_oil_compressibility,
        "Beggs and Robinson Oil Viscosity": beggs_robinson_viscosity,
        "Vasquez and Beggs Undersaturated Oil Viscosity": vasquez_beggs_undersaturated_viscosity,
        "Live Sensitivity Analyzer": live_sensitivity_analyzer,
    }

    choice = st.sidebar.selectbox("Select Formula", list(menu_options.keys()))
    menu_options[choice]()

if __name__ == "__main__":
    main()
