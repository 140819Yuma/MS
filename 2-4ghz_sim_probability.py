import numpy as np
import time
import math
import warnings

# Qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
# ★ depolarizing_error を pauli_error に変更
from qiskit_aer.noise import NoiseModel, pauli_error

# 物理モデルツール (クラスをインポート)
from new_tool import HAPDownlinkChannel

np.seterr(over='ignore')
warnings.filterwarnings('ignore')

# ==========================================
# 定数とQKDパラメータ
# ==========================================
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**5; BATCH_SIZE = 10**5
FIXED_Q_X = 0.02

# ==========================================
# システムオーバーヘッドのパラメータ
# ==========================================
DELTA_T = 3600.0     # 量子フェーズの時間 (t) [秒]
D_POST  = 2          # 後処理の遅延 (dpost) [秒]
T_ENC   = 0.000002   # 暗号化時間 (tenc) [秒]
D_PROP  = 0.000060   # 伝搬遅延 (dprop) [秒]

# ==========================================
# 今回の指定条件
# ==========================================
pz_list = [0.9]
w0_list = [0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]
pe_list = [1e-6] 
angle_list = [0, 15, 30, 45, 60] 
user_counts = [6]
ghz_list = [3]  # ★追加: 使用するGHZ状態のリスト

NUM_TIMESLOTS = 500

# Qiskitシミュレータの使い回し（高速化）
GLOBAL_BACKEND = AerSimulator()

# ==========================================
# W0, PE を動的に変更できる透過率生成関数
# ==========================================
def custom_generate_realistic_eta(n_users, n_timeslots, zenith_angle_list, current_w0, current_pe):
    params = {
        "W0": current_w0,           
        "pointing_error": current_pe,  
        "Cn0": 9.6e-14,                
        "rx_aperture": 0.4,    
        "obs_ratio": 0.3,   
        "n_max": 6,            
        "wind_speed": 10,      
        "wavelength": 1550e-9, 
        "ground_station_alt": 0.02, 
        "aerial_platform_alt": 20,   
        "tracking_efficiency": 0.8  
    }
    
    eta_matrix = []
    for angle in zenith_angle_list:
        channel = HAPDownlinkChannel(zenith_angle=angle, **params)
        samples = channel.sample_transmittance(n_timeslots)
        eta_matrix.append(samples)
        
    return eta_matrix

# ==========================================
# 算出用関数
# ==========================================
def calculate_yield_theoretical(etas):
    y_N = 1.0
    for eta in etas: 
        y_N *= 1 - (1 - Y0) * (1 - eta)
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
    
    # ★パウリエラーモデルの適用
    p_err_x = min(1.0, max_qber)
    p_err_z = FIXED_Q_X 
    
    p_x = p_err_x * (1.0 - p_err_z)         
    p_z_pauli = p_err_z * (1.0 - p_err_x)   
    p_y = p_err_x * p_err_z                 
    p_i = (1.0 - p_err_x) * (1.0 - p_err_z) 
    
    total_p = p_x + p_z_pauli + p_y + p_i
    if total_p > 0:
        p_x, p_z_pauli, p_y, p_i = p_x/total_p, p_z_pauli/total_p, p_y/total_p, p_i/total_p

    p_error = pauli_error([('X', p_x), ('Y', p_y), ('Z', p_z_pauli), ('I', p_i)])

    if (1.0 - p_i) > 0:
        noise_model.add_quantum_error(p_error, 'measure', [0])
        
    bases = np.random.choice([0, 1], size=(num_shots, n_qubits), p=[p_z, 1.0 - p_z])
    unique_bases, counts = np.unique(bases, axis=0, return_counts=True)
    
    sifted_events = 0
    sifted_errors = np.zeros(n_qubits - 1)  # ユーザーごとにエラーを格納する配列に変更
    
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
                # 各ユーザー(i)ごとに個別にカウント
                for i in range(1, n_qubits):
                    if bits[0] != bits[i]: sifted_errors[i-1] += cnt
        elif n_qubits == 2 and np.all(basis_combo == 1):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                bits = out.replace(" ", "")[::-1]
                if bits[0] != bits[1]: sifted_errors[0] += cnt
                
    return sifted_events, sifted_errors

# ==========================================
# メインシミュレーション
# ==========================================
def main():
    print("="*70)
    print(" === HAP-Alice: Scalability Simulation (2 to 4-GHZ) ===")
    print(" === Sweep Parameters: P_Z, W0, PE, Zenith Angle, Users ===")
    print("="*70)
    print(f"System Overheads: dt={DELTA_T}s, d_post={D_POST}s, t_enc={T_ENC}s, d_prop={D_PROP}s\n")
    
    start_time = time.time()

    for p_z in pz_list:
        print(f"\n######################################################################")
        print(f"### Sweep P_Z = {p_z:.1f} ###")
        print(f"######################################################################")
        
        for w0 in w0_list:
            
            for pe in pe_list:
            
                for current_angle in angle_list:
                    print(f"\n[====== Angle: {current_angle} deg | W0: {w0:.3f}m | PE: {pe:.1e} ======]")
                    
                    for N_USERS in user_counts:
                        print(f"  [********** Number of Users: {N_USERS:2d} **********]")
                        
                        angles = [current_angle] * N_USERS
                        
                        eta_matrix = custom_generate_realistic_eta(N_USERS, NUM_TIMESLOTS, angles, current_w0=w0, current_pe=pe)
                        eta_alice = 1.0

                        for n_ghz in ghz_list: # ★修正: ghz_list を使用
                            bobs_per_grp = n_ghz - 1
                            num_groups = math.ceil(N_USERS / bobs_per_grp)
                            group_skrs = []
                            
                            for g in range(num_groups):
                                bob_ids = list(range(g * bobs_per_grp, min((g + 1) * bobs_per_grp, N_USERS)))
                                z_ev = 0
                                z_er = np.zeros(n_ghz - 1)  # ユーザーごとのエラー集計配列
                                
                                for ts in range(NUM_TIMESLOTS):
                                    cur_etas = [eta_alice] + [eta_matrix[uid][ts] for uid in bob_ids]
                                    y_n = calculate_yield_theoretical(cur_etas)
                                    n_ev = np.random.binomial(PULSES_PER_SLOT, y_n)
                                    
                                    if n_ev > 0:
                                        max_q = max(calculate_pairwise_qbers(eta_alice, cur_etas[1:], y_n))
                                        batch = min(n_ev, BATCH_SIZE)
                                        
                                        ev, er = run_full_qkd_protocol_qiskit(n_ghz, batch, max_q, p_z, GLOBAL_BACKEND)
                                        z_ev += ev * (n_ev / batch)
                                        z_er += er * (n_ev / batch)  # 配列として加算

                                if z_ev > 0:
                                    q_z_max = np.max(z_er / z_ev)  # 最大のQBERを選択
                                else:
                                    q_z_max = 0.0

                                raw_skr = calculate_ghz_skr_new(z_ev / ((NUM_TIMESLOTS * PULSES_PER_SLOT) / FREQ), q_z_max)
                                group_skrs.append(raw_skr)

                            skr_min = min(group_skrs) if group_skrs else 0.0
                            skr_raw_uni = skr_min / num_groups if num_groups > 0 else 0.0
                            
                            t_total = num_groups * (DELTA_T + D_POST + T_ENC + D_PROP)
                            skr_sys_uni = (skr_min * DELTA_T) / t_total if t_total > 0 else 0.0
                            
                            if any(s <= 0 for s in group_skrs) or not group_skrs:
                                skr_optimal = 0.0
                            else:
                                skr_optimal = 1.0 / sum(1.0 / s for s in group_skrs)
                                
                            print(f"   * {n_ghz}-GHZ (Groups: {num_groups})")
                            print(f"      1. Raw Uniform SKR : {skr_raw_uni/1e6:8.5f} Mbps")
                            print(f"      2. System Uniform  : {skr_sys_uni/1e6:8.5f} Mbps")
                            print(f"      3. Optimal SKR     : {skr_optimal/1e6:8.5f} Mbps")
                        print("-" * 65)

    print(f"\nSimulation completed in {time.time() - start_time:.2f} seconds.")

if __name__ == '__main__':
    main()