import numpy as np
import time
import math
import warnings

# Qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# 物理モデルツール
from new_tool import generate_realistic_eta

np.seterr(over='ignore')
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==========================================
# 定数とQKDパラメータ
# ==========================================
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 10000000
FIXED_Q_X = 0.02
P_Z_3GHZ = 0.5

# ==========================================
# システムオーバーヘッドのパラメータ (自由に変更してください)
# ==========================================
DELTA_T = 1.0     # 量子フェーズの時間 (t) [秒]
D_POST  = 0.1     # 後処理の遅延 (dpost) [秒]
T_ENC   = 0.0005   # 暗号化時間 (tenc) [秒]
D_PROP  = 0.001  # 伝搬遅延 (dprop) [秒]

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

def run_full_qkd_protocol_qiskit(n_qubits, num_shots, max_qber, p_z):
    if num_shots == 0: return 0, 0
    backend = AerSimulator()
    noise_model = NoiseModel()
    depol_param = min(1.0, 2.0 * max_qber)
    if depol_param > 0:
        noise_model.add_quantum_error(depolarizing_error(depol_param, 1), 'measure', [0])
        
    bases = np.random.choice([0, 1], size=(num_shots, n_qubits), p=[p_z, 1.0 - p_z])
    unique_bases, counts = np.unique(bases, axis=0, return_counts=True)
    
    sifted_events = 0; sifted_errors = 0
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
        elif n_qubits == 2 and np.all(basis_combo == 1):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                bits = out.replace(" ", "")[::-1]
                if bits[0] != bits[1]: sifted_errors += cnt
                
    return sifted_events, sifted_errors

# ==========================================
# メインシミュレーション
# ==========================================
def main():
    print("=== HAP-Alice: Advanced SKR Output Simulation ===")
    print(f"System Overheads: dt={DELTA_T}s, d_post={D_POST}s, t_enc={T_ENC}s, d_prop={D_PROP}s")
    
    N_USERS = 6
    NUM_TIMESLOTS = 500 # テスト時は小さく、本番は1000等に増やしてください
    zenith_angles = np.linspace(0, 60, 7)

    start_time = time.time()

    for angle in zenith_angles:
        print(f"\n[{'='*10} Zenith Angle = {angle:.0f} deg {'='*10}]")
        eta_matrix = generate_realistic_eta(N_USERS, NUM_TIMESLOTS, [angle] * N_USERS)
        eta_alice = 1.0

        for n_ghz in [2, 3, 4]:
            bobs_per_grp = n_ghz - 1
            num_groups = math.ceil(N_USERS / bobs_per_grp)
            group_skrs = []
            
            for g in range(num_groups):
                bob_ids = list(range(g * bobs_per_grp, min((g + 1) * bobs_per_grp, N_USERS)))
                z_ev, z_er = 0, 0
                
                for ts in range(NUM_TIMESLOTS):
                    cur_etas = [eta_alice] + [eta_matrix[uid][ts] for uid in bob_ids]
                    y_n = calculate_yield_theoretical(cur_etas)
                    n_ev = np.random.binomial(PULSES_PER_SLOT, y_n)
                    
                    if n_ev > 0:
                        max_q = max(calculate_pairwise_qbers(eta_alice, cur_etas[1:], y_n))
                        batch = min(n_ev, BATCH_SIZE)
                        ev, er = run_full_qkd_protocol_qiskit(n_ghz, batch, max_q, 0.5 if n_ghz==2 else P_Z_3GHZ)
                        z_ev += ev * (n_ev / batch)
                        z_er += er * (n_ev / batch)

                raw_skr = calculate_ghz_skr_new(z_ev / ((NUM_TIMESLOTS * PULSES_PER_SLOT) / FREQ), z_er / z_ev if z_ev > 0 else 0)
                group_skrs.append(raw_skr)

            # --- ボトルネック(最小)のSKRを取得 ---
            skr_min = min(group_skrs) if group_skrs else 0.0

            # [1] Raw Uniform SKR (オーバーヘッドなし均等)
            skr_raw_uni = skr_min / num_groups if num_groups > 0 else 0.0
            
            # =========================================================
            # [2] System SKR (あなたのノートの数式を完全に反映！)
            # 分子 = 最小SKR * (Delta_t + d_post)
            # 分母 = G * (Delta_t + d_post + t_enc + d_prop)
            # =========================================================
            t_total = num_groups * (DELTA_T + D_POST + T_ENC + D_PROP)
            skr_sys_uni = (skr_min * DELTA_T) / t_total if t_total > 0 else 0.0
            
            # [3] Optimal SKR (非均等最適化 1 / sum(1/SKR))
            if any(s <= 0 for s in group_skrs) or not group_skrs:
                skr_optimal = 0.0
            else:
                skr_optimal = 1.0 / sum(1.0 / s for s in group_skrs)
                
            # コンソールへの結果出力
            print(f" * {n_ghz}-GHZ (Groups: {num_groups})")
            
            for i, g_skr in enumerate(group_skrs):
                print(f"    - Group {i+1} Base SKR: {g_skr/1e6:8.5f} Mbps")
            print("    --------------------------------")
            
            print(f"    1. Raw Uniform SKR : {skr_raw_uni/1e6:8.5f} Mbps")
            print(f"    2. System Uniform  : {skr_sys_uni/1e6:8.5f} Mbps")
            print(f"    3. Optimal SKR     : {skr_optimal/1e6:8.5f} Mbps\n")

    print(f"\nSimulation completed in {time.time() - start_time:.2f} seconds.")

if __name__ == '__main__':
    main()