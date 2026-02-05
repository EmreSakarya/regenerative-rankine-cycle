from pyXSteam.XSteam import XSteam
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Create docs folder if not exists
os.makedirs("docs", exist_ok=True)

# Initialize IAPWS-97 Steam Tables (MKS Units: bar, °C, kJ/kg)
steam = XSteam(XSteam.UNIT_SYSTEM_MKS)

# ==========================================
# SYSTEM PARAMETERS
# ==========================================
P_boiler = 70.0   # 70 bar
P_ofwh   = 8.0    # 8 bar
P_cond   = 0.1    # 0.1 bar

eta_turb = 0.90   # Turbine Efficiency
eta_pump = 0.90   # Pump Efficiency

print(">>> RANKINE CYCLE ANALYSIS RESULTS <<<\n")

# ==========================================
# PART A: EFFECT OF TURBINE INLET TEMPERATURE
# ==========================================
temps_a = list(range(300, 625, 25))
eff_a = []
quality_a = []

for T_inlet in temps_a:
    # 1. Condenser Exit
    h1 = steam.hL_p(P_cond)
    v1 = steam.vL_p(P_cond)
    w_pump1 = (v1 * (P_ofwh - P_cond) * 100) / eta_pump
    h2 = h1 + w_pump1
    
    # 3. OFWH Exit
    h3 = steam.hL_p(P_ofwh)
    v3 = steam.vL_p(P_ofwh)
    w_pump2 = (v3 * (P_boiler - P_ofwh) * 100) / eta_pump
    h4 = h3 + w_pump2
    
    # 5. Turbine Inlet
    h5 = steam.h_pt(P_boiler, T_inlet)
    s5 = steam.s_pt(P_boiler, T_inlet)
    
    # 6. Extraction
    h6s = steam.h_ps(P_ofwh, s5)
    h6 = h5 - eta_turb * (h5 - h6s)
    
    # 7. Turbine Exit
    h7s = steam.h_ps(P_cond, s5)
    h7 = h5 - eta_turb * (h5 - h7s)
    
    y = (h3 - h2) / (h6 - h2) # Mass fraction
    
    # Quality
    h_f = steam.hL_p(P_cond)
    h_fg = steam.hV_p(P_cond) - h_f
    x_exit = (h7 - h_f) / h_fg
    
    w_t1 = h5 - h6
    w_t2 = (h6 - h7) * (1 - y)
    w_p1 = w_pump1
    w_p2 = w_pump2 * (1 - y)
    
    q_in = h5 - h4
    w_net = w_t1 + w_t2 - w_p1 - w_p2
    eta = (w_net / q_in) * 100
    
    eff_a.append(eta)
    quality_a.append(x_exit)

df_a = pd.DataFrame({"T_inlet": temps_a, "Efficiency": np.round(eff_a, 2), "Quality": np.round(quality_a, 4)})
print("--- PART A RESULTS ---")
print(df_a.to_string(index=False))
print("\n")


# ==========================================
# PART B: EFFECT OF REHEAT TEMPERATURE
# ==========================================
T_inlet_fixed = 500.0
temps_b = list(range(300, 425, 25))
eff_b = []
quality_b = []

for T_reheat in temps_b:
    # Pumps (Same as Part A)
    h1 = steam.hL_p(P_cond); v1 = steam.vL_p(P_cond)
    w_pump1 = (v1 * (P_ofwh - P_cond) * 100) / eta_pump
    h2 = h1 + w_pump1
    
    h3 = steam.hL_p(P_ofwh); v3 = steam.vL_p(P_ofwh)
    w_pump2 = (v3 * (P_boiler - P_ofwh) * 100) / eta_pump
    h4 = h3 + w_pump2
    
    # HP Turbine
    h5 = steam.h_pt(P_boiler, T_inlet_fixed)
    s5 = steam.s_pt(P_boiler, T_inlet_fixed)
    h6s = steam.h_ps(P_ofwh, s5)
    h6 = h5 - eta_turb * (h5 - h6s)
    
    y = (h3 - h2) / (h6 - h2)
    
    # Reheat & LP Turbine
    h7 = steam.h_pt(P_ofwh, T_reheat)
    s7 = steam.s_pt(P_ofwh, T_reheat)
    h8s = steam.h_ps(P_cond, s7)
    h8 = h7 - eta_turb * (h7 - h8s)
    
    h_f = steam.hL_p(P_cond)
    h_fg = steam.hV_p(P_cond) - h_f
    x_exit = (h8 - h_f) / h_fg
    
    w_hp = h5 - h6
    w_lp = (1 - y) * (h7 - h8)
    w_p1 = (1 - y) * w_pump1
    w_p2 = w_pump2
    
    q_main = h5 - h4
    q_reheat = (1 - y) * (h7 - h6)
    w_net = w_hp + w_lp - w_p1 - w_p2
    eta = (w_net / (q_main + q_reheat)) * 100
    
    eff_b.append(eta)
    quality_b.append(x_exit)

df_b = pd.DataFrame({"T_reheat": temps_b, "Efficiency": np.round(eff_b, 2), "Quality": np.round(quality_b, 4)})
print("--- PART B RESULTS ---")
print(df_b.to_string(index=False))

# ==========================================
# PLOTTING
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot Part A
ax1.plot(temps_a, eff_a, 'b-o', label='Efficiency')
ax1.set_xlabel('Turbine Inlet Temperature (°C)')
ax1.set_ylabel('Thermal Efficiency (%)')
ax1.set_title('Part A: Efficiency vs Inlet Temp')
ax1.grid(True)
ax1_twin = ax1.twinx()
ax1_twin.plot(temps_a, quality_a, 'r--s', label='Exit Quality')
ax1_twin.set_ylabel('Steam Quality (x)')
ax1.legend(loc='upper left')
ax1_twin.legend(loc='lower right')

# Plot Part B
ax2.plot(temps_b, eff_b, 'g-o', label='Efficiency')
ax2.set_xlabel('Reheat Temperature (°C)')
ax2.set_ylabel('Thermal Efficiency (%)')
ax2.set_title('Part B: Efficiency vs Reheat Temp')
ax2.grid(True)
ax2_twin = ax2.twinx()
ax2_twin.plot(temps_b, quality_b, 'm--s', label='Exit Quality')
ax2_twin.set_ylabel('Steam Quality (x)')
ax2.legend(loc='upper left')
ax2_twin.legend(loc='lower right')

plt.tight_layout()
plt.savefig('docs/rankine_results.png')
print("\nGraph saved as 'docs/rankine_results.png'")
