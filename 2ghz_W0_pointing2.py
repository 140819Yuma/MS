import numpy as np
import time
import math
import warnings

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# new_tool.py から大元のチャネルクラスをインポート
from new_tool import HAPDownlinkChannel

np.seterr(over='ignore')
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==========================================
# 定数・量子パラメータ
# ==========================================
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 100000
FIXED_Q_X = 0.02
P_Z_2GHZ = 0.5

# ==========================================
# システムパラメータ（遅延計算用）
# ==========================================
DELTA_T = 1.0     
D_POST  = 0.1     
T_ENC   = 0.005   
D_PROP  = 0.0001  

# 今回の指定条件
M_USERS = 16
NUM_TIMESLOTS = 500

# 変更するパラメータのリスト（高度、PE、W0、ゼニスアングルの総当たり）
alt_list   = [20, 35]                                    # HAPの高度 (km)
pe_list    = [2e-6]                                      # ポインティングエラー
w0_list    = [0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2] # ビームウェスト
angle_list = [0, 10, 20, 30, 40, 50, 60]                 # ゼニスアングル (度)

# Qiskitシミュレータの使い回し（高速化）
GLOBAL_BACKEND = AerSimulator()

# ==========================================
# W0, PE, Altitude を動的に変更できる透過率生成関数
# ==========================================
def custom_generate_realistic_eta(n_users, n_timeslots, zenith_angle_list, current_w0, current_pe, current_alt):
    params = {
        "W0": current_w0,           
        "pointing_error": current_pe, 
        "Cn0": 1e-14,           
        "rx_aperture": 0.4,    
        "obs_ratio": 0.3,   
        "n_max": 6,            
        "wind_speed": 10,      
        "wavelength": 1550e-9, 
        "ground_station_alt": 0.02, 
        "aerial_platform_alt": current_alt, # 高度を動的に変更
        "tracking_efficiency": 0.99  
    }
    
    eta_matrix = []
    for angle in zenith_angle_list:
        channel = HAPDownlinkChannel(zenith_angle=angle, **params)
        samples = channel.sample_transmittance(n_timeslots)
        eta_matrix.append(samples)
        
    return eta_matrix

def calculate_yield_theoretical(etas):
    y_N = 1.0
    for eta in etas: y_N *= 1 - (1 - Y0) * (1 - eta)
    return y_N

def calculate_pairwise_qbers(eta_alice, etas_bobs, y_N):
    if y_N <= 0: return [0.5] * len(etas_bobs)
    qbers = []
    y_A = 1 - (1 - Y0) * (1 - eta_alice)
    for eta_bob in etas_bobs:
        y_B = 1 - (1 - Y0) * (1 - eta_bob)
        y_AB_i = eta_alice * eta_bob * y_N / (y_A * y_B)
        qbers.append((E0 * (y_N - y_AB_i) + ED * y_AB_i) / y_N)
    return qbers

def binary_entropy(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

def calculate_ghz_skr_new(sifted_rate, Q_Z_max):
    if FIXED_Q_X >= 0.5 or Q_Z_max >= 0.5: return 0.0
    r_inf = 1 - binary_entropy(FIXED_Q_X) - binary_entropy(Q_Z_max)
    return sifted_rate * r_inf if r_inf > 0 else 0.0

def run_full_qkd_protocol_qiskit(n_qubits, num_shots, max_qber, p_z, backend):
    if num_shots == 0: return 0, 0
    noise_model = NoiseModel()
    depol_param = min(1.0, 2.0 * max_qber)
    if depol_param > 0:
        noise_model.add_quantum_error(depolarizing_error(depol_param, 1), 'measure', [0])
        
    bases = np.random.choice([0, 1], size=(num_shots, n_qubits), p=[p_z, 1.0 - p_z])
    unique_bases, counts = np.unique(bases, axis=0, return_counts=True)
    
    sifted_events, sifted_errors = 0, 0
    for basis_combo, count in zip(unique_bases, counts):
        qc = QuantumCircuit(n_qubits)
        qc.h(0)
        for i in range(1, n_qubits): qc.cx(0, i)
        for i, b in enumerate(basis_combo):
            if b == 1: qc.h(i)
        qc.measure_all()
        result = backend.run(qc, noise_model=noise_model, shots=count).result()
        result_counts = result.get_counts()
        
        if np.all(basis_combo == 0):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                bits = out.replace(" ", "")[::-1]
                if any(bits[0] != bits[i] for i in range(1, n_qubits)): sifted_errors += cnt
        elif np.all(basis_combo == 1):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                bits = out.replace(" ", "")[::-1]
                if bits[0] != bits[1]: sifted_errors += cnt
    return sifted_events, sifted_errors

def main():
    print("\n" + "="*75)
    print("   2-GHZ QKD Specific Simulation: Altitude, PE, W0 & Angle Sweep")
    print("="*75)
    print(f"[ Fixed Parameters ]")
    print(f" - Protocol       : 2-GHZ (BBM92)")
    print(f" - Users (M)      : {M_USERS}")
    print("="*75 + "\n")

    start_time = time.time()
    
    n_ghz = 2
    bobs_per_grp = n_ghz - 1 
    num_groups = math.ceil(M_USERS / bobs_per_grp) 

    for alt in alt_list:
        print(f"\n[{'='*25} HAP Altitude: {alt} km {'='*25}]")
        
        for pe in pe_list:
            print(f"  [{'*'*20} Pointing Error: {pe} {'*'*20}]")
            
            for w0 in w0_list:
                print(f"\n    --- Beam Waist W0 = {w0:.3f} m ---")
                
                for angle in angle_list:
                    # 全員が現在の角度(angle)になるリストを生成
                    angles = [angle] * M_USERS
                    
                    # FSOチャネルの計算（クラスから動的に生成）
                    eta_matrix = custom_generate_realistic_eta(M_USERS, NUM_TIMESLOTS, angles, current_w0=w0, current_pe=pe, current_alt=alt)
                    eta_alice = 1.0
                    group_skrs = []
                    
                    for g in range(num_groups):
                        bob_ids = list(range(g * bobs_per_grp, min((g + 1) * bobs_per_grp, M_USERS)))
                        z_ev, z_er = 0, 0
                        
                        for ts in range(NUM_TIMESLOTS):
                            cur_etas = [eta_alice] + [eta_matrix[uid][ts] for uid in bob_ids]
                            y_n = calculate_yield_theoretical(cur_etas)
                            n_ev = np.random.binomial(PULSES_PER_SLOT, y_n)
                            
                            if n_ev > 0:
                                max_q = max(calculate_pairwise_qbers(eta_alice, cur_etas[1:], y_n))
                                batch = min(n_ev, BATCH_SIZE)
                                ev, er = run_full_qkd_protocol_qiskit(n_ghz, batch, max_q, P_Z_2GHZ, GLOBAL_BACKEND)
                                z_ev += ev * (n_ev / batch)
                                z_er += er * (n_ev / batch)

                        raw_skr = calculate_ghz_skr_new(z_ev / ((NUM_TIMESLOTS * PULSES_PER_SLOT) / FREQ), z_er / z_ev if z_ev > 0 else 0)
                        group_skrs.append(raw_skr)

                    skr_min = min(group_skrs) if group_skrs else 0.0
                    
                    # System SKR と 実行時間の計算
                    t_total = num_groups * (DELTA_T + D_POST + T_ENC + D_PROP)
                    skr_sys_uni = (skr_min * DELTA_T) / t_total if t_total > 0 else 0.0
                    
                    # 1行でスッキリと結果を出力
                    print(f"      [Angle: {angle:2d} deg] System SKR: {skr_sys_uni:10.5f} bps | Total Exec Time: {t_total:6.4f} s | Steps: {num_groups * 4}")

    print(f"\nSimulation completed in {time.time() - start_time:.2f} seconds.\n")

if __name__ == '__main__':
    main()