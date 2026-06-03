import numpy as np
import time
import math
import warnings

# Qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# 物理モデルツール（W0やCn2等はモジュール側で手動設定済みとする）
from new_tool import generate_realistic_eta

np.seterr(over='ignore')
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==========================================
# 定数・量子パラメータ
# ==========================================
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 1000000
FIXED_Q_X = 0.02
P_Z_3GHZ = 0.5

# ==========================================
# システムパラメータ & 複雑性計算用パラメータ
# ==========================================
DELTA_T = 1.0     
D_POST  = 0.1     
T_ENC   = 0.005   
D_PROP  = 0.0001  

FIXED_ANGLE = 10
NUM_TIMESLOTS = 500
M_list = [6, 12, 18, 24, 30]

# --- 表示・メモ用の変数（new_tool.pyの手動設定値と必ず合わせる） ---
W0_DISPLAY  = 0.10    # ビームウェスト
CN2_DISPLAY = 1e-13 # 大気乱流パラメータ(Cn^2)のメモ用

# --- 追加：複雑性（Complexity）計算用の仮定 ---
BYTES_PER_PACKET = 100.0  # 1回のダウンリンクで送信するデータ量(Bytes)
ENERGY_UNIT_ENC  = 1.0    # 1回の暗号化にかかる相対エネルギー
ENERGY_UNIT_TX   = 2.0    # 1回のパケット送信にかかる相対エネルギー

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

def run_full_qkd_protocol_qiskit(n_qubits, num_shots, max_qber, p_z):
    if num_shots == 0: return 0, 0
    backend = AerSimulator()
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
        elif n_qubits == 2 and np.all(basis_combo == 1):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                bits = out.replace(" ", "")[::-1]
                if bits[0] != bits[1]: sifted_errors += cnt
    return sifted_events, sifted_errors

def main():
    print("\n" + "="*60)
    print("   Multi-partite QKD: Advanced Trade-off Analyzer")
    print("="*60)
    print("[ Simulation Settings ]")
    print(f" - Cn2 (Turbulence)    : {CN2_DISPLAY}")
    print(f" - W0 (Beam Waist)     : {W0_DISPLAY} m")
    print(f" - Zenith Angle        : {FIXED_ANGLE} deg")
    print(f" - M (Users)           : {M_list}")
    print("="*60 + "\n")

    start_time = time.time()

    for M in M_list:
        print(f"[{'='*20} Number of Terrestrial Nodes: M = {M} {'='*20}]")
        eta_matrix = generate_realistic_eta(M, NUM_TIMESLOTS, [FIXED_ANGLE] * M)
        eta_alice = 1.0

        for n_ghz in [2, 3, 4]:
            bobs_per_grp = n_ghz - 1
            num_groups = math.ceil(M / bobs_per_grp)
            group_skrs = []
            
            for g in range(num_groups):
                bob_ids = list(range(g * bobs_per_grp, min((g + 1) * bobs_per_grp, M)))
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

            skr_min = min(group_skrs) if group_skrs else 0.0
            
            # --- 1. System SKR と 実行時間 (T_total) ---
            t_total = num_groups * (DELTA_T + D_POST + T_ENC + D_PROP)
            skr_sys_uni = (skr_min * DELTA_T) / t_total if t_total > 0 else 0.0
            
            # --- 2. 複雑性指標の計算 (代替案 A, B, C) ---
            G = num_groups
            # [A] 通信オーバーヘッド (Bytes)
            total_payload = G * BYTES_PER_PACKET
            # [B] 古典処理時間の総和 (sec)
            classical_time = G * (D_POST + T_ENC + D_PROP)
            # [C] HAPの消費エネルギー (Units)
            total_energy = G * (ENERGY_UNIT_ENC + ENERGY_UNIT_TX)

            # ターミナルへの詳細出力
            print(f" * {n_ghz}-GHZ (Groups G = {G})")
            print(f"    ├─ [Core] System SKR       : {skr_sys_uni:10.5f} bps")
            print(f"    ├─ [Core] Total Exec Time  : {t_total:10.4f} sec")
            print(f"    │")
            print(f"    ├─ [Opt A] Comm. Payload   : {total_payload:10.1f} Bytes")
            print(f"    ├─ [Opt B] Classical Delay : {classical_time:10.4f} sec")
            print(f"    └─ [Opt C] Est. Energy     : {total_energy:10.1f} Units")
        print() 

    print(f"Simulation completed in {time.time() - start_time:.2f} seconds.\n")

if __name__ == '__main__':
    main()