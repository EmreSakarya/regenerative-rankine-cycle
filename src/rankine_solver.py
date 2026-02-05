from pyXSteam.XSteam import XSteam
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Initialize IAPWS-97 Steam Tables (MKS Units: bar, °C, kJ/kg)
steam = XSteam(XSteam.UNIT_SYSTEM_MKS)

# ==========================================
# SYSTEM PARAMETERS
# ==========================================
P_boiler = 70.0   # 7 MPa -> 70 bar
P_ofwh   = 8.0    # 800 kPa -> 8 bar
P_cond   = 0.1    # 10 kPa -> 0.1 bar

eta_turb = 0.90   # Turbine Isentropic Efficiency
eta_pump = 0.90   # Pump Isentropic Efficiency

print(">>> RANKINE CYCLE ANALYSIS RESULTS <<<\n")

# ==========================================
# PART A: EFFECT OF TURBINE INLET TEMPERATURE
# ==========================================
# Temperature range: 300°C to 600°C with 25°C increments
temps_a = list(range(300, 625, 25))

eff_a = []
quality_a = []

for T_inlet in temps_a:
    # 1. Condenser Exit
    h1 = steam.hL_p(P_cond)
    v1 = steam.vL_p(P_cond)
    
    # 2. Condensate Pump (Pump 1)
    # Work = v * dP (converted to kJ/kg)
    w_pump1 = (v1 * (P_ofwh - P_cond) * 100) / eta_pump
    h2 = h1 + w_pump1
    
    # 3. OFWH Exit
    h3 = steam.hL_p(P_ofwh)
    v3 = steam.vL_p(P_ofwh)
    
    # 4. Feedwater Pump (Pump 2)
    w_pump2 = (v3 * (P_boiler - P_ofwh) * 100) / eta_pump
    h4 = h3 + w_pump2
    
    # 5. Turbine Inlet
    h5 = steam.h_pt(P_boiler, T_inlet)
    s5 = steam.s_pt(P_boiler, T_inlet)
    
    # 6. Extraction to OFWH
    h6s = steam.h_ps(P_ofwh, s5)
    h6 = h5 - eta_turb * (h5 - h6s)
    
    # 7. Turbine Exit to Condenser
    # Expansion assumes single stage efficiency characteristic from inlet
    h7s = steam.h_ps(P_cond, s5)
    h7 = h5 - eta_turb * (h5 - h7s)
    
    # Mass Fraction (y)
    y = (h3 - h2) / (h6 - h2)
    
    # Steam Quality at Exit
    h_f = steam.hL_p(P_cond)
    h_fg = steam.hV_p(P_cond) - h_f
    x_exit = (h7 - h_f) / h_fg
    
    # Energy Balance
    w_t1 = h5 - h6
    w_t2 = (h6 - h7) * (1 - y)
    
    # Pump Work Allocation
    w_p1 = w_pump1
    w_p2 = w_pump2 * (1 - y)
    
    q_in = h5 - h4
    w_net = w_t1 + w_t2 - w_p1 - w_p2
    
    eta = (w_net / q_in) * 100
    
    eff_a.append(eta)
    quality_a.append(x_exit)

# Output Table Part A
df_a = pd.DataFrame({
    "T_inlet (°C)": temps_a,
    "Efficiency (%)": np.round(eff_a, 2),
    "Exit Quality": np.round(quality_a, 4)
})
print("--- PART A RESULTS ---")
print(df_a.to_string(index=False))
print("\n")


# ==========================================
# PART B: EFFECT OF REHEAT TEMPERATURE
# ==========================================
# Fixed Inlet Temperature
T_inlet_fixed = 500.0
# Reheat Temperature range: 300°C to 400°C
temps_b = list(range(300, 425, 25))

eff_b = []
quality_b = []

for T_reheat in temps_b:
    # Pumps and OFWH states (1-4) remain identical to Part A logic
    h1 = steam.hL_p(P_cond)
    v1 = steam.vL_p(P_cond)
    w_pump1 = (v1 * (P_ofwh - P_cond) * 100) / eta_pump
    h2 = h1 + w_pump1
    
    h3 = steam.hL_p(P_ofwh)
    v3 = steam.vL_p(P_ofwh)
    w_pump2 = (v3 * (P_boiler - P_ofwh) * 100) / eta_pump
    h4 = h3 + w_pump2
    
    # 5. HP Turbine Inlet
    h5 = steam.h_pt(P_boiler, T_inlet_fixed)
    s5 = steam.s_pt(P_boiler, T_inlet_fixed)
    
    # 6. HP Turbine Exit (Extraction)
    h6s = steam.h_ps(P_ofwh, s5)
    h6 = h5 - eta_turb * (h5 - h6s)
    
    # Mass Fraction (y)
    y = (h3 - h2) / (h6 - h2)
    
    # 7. Reheat Exit / LP Turbine Inlet
    h7 = steam.h_pt(P_ofwh, T_reheat)
    s7 = steam.s_pt(P_ofwh, T_reheat)
    
    # 8. LP Turbine Exit
    h8s = steam.h_ps(P_cond, s7)
    h8 = h7 - eta_turb * (h7 - h8s)
    
    # Steam Quality at LP Exit
    h_f = steam.hL_p(P_cond)
    h_fg = steam.hV_p(P_cond) - h_f
    x_exit = (h8 - h_f) / h_fg
    
    # Energy Balance
    w_hp = h5 - h6
    w_lp = (1 - y) * (h7 - h8)
    
    # Pump Work Allocation (Corrected for Reheat Cycle)
    w_p1 = (1 - y) * w_pump1
    w_p2 = w_pump2
    
    q_main = h5 - h4
    q_reheat = (1 - y) * (h7 - h6)
    q_total = q_main + q_reheat
    
    w_net = w_hp + w_lp - w_p1 - w_p2
    eta = (w_net / q_total) * 100
    
    eff_b.append(eta)
    quality_b.append(x_exit)

# Output Table Part B
df_b = pd.DataFrame({
    "T_reheat (°C)": temps_b,
    "Efficiency (%)": np.round(eff_b, 2),
    "Exit Quality": np.round(quality_b, 4)
})
print("--- PART B RESULTS ---")
print(df_b.to_string(index=False))
