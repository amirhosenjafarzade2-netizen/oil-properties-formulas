import streamlit as st
import math

# Set Streamlit configuration as the first Streamlit command
st.set_page_config(layout="wide", sidebar_state="expanded")

def get_valid_float(value, min_val=None, max_val=None, error_message=None):
    """Validate float input within specified range."""
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

def main():
    st.title("Oil Properties Calculator")
    st.markdown("Select a formula from the sidebar to compute oil and gas properties.")
    
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
    }
    
    # Customize sidebar width using CSS
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            min-width: 400px;
            max-width: 500px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.header("Formulas Menu")
    choice = st.sidebar.selectbox("Select Formula", list(menu_options.keys()))
    
    menu_options[choice]()

if __name__ == "__main__":
    main()
