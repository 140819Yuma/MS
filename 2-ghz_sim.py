import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from new_tool import generate_realistic_eta

warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- Configuration ---
NUM_USERS = 15
ZENITH_ANGLES = np.linspace(0, 60, NUM_USERS).tolist()
GROUP_SIZE = 2  # 2-GHZ

# --- Constants ---
Y0 = 1e-5; ED = 0.01; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 1000
FIXED_Q_X = 0.03  

def calculate_yield_theoretical(etas):
    y_N = 1.0
    for eta in etas:
        y_N *= 1 - (1 - Y0) * (1 - eta)
    return y_N

def calculate_pairwise_qbers(eta_alice, etas_bobs, y_N):
    if y_N == 0: return [0.5] * len(etas_bobs)
    qbers = []
    y_A = 1 - (1 - Y0) * (1 - eta_alice)
    for eta_bob in etas_bobs:
        y_B = 1 - (1 - Y0) * (1 - eta_bob)
        y_AB_i = eta_alice * eta_bob * y_N / (y_A * y_B)
        q_AB_i = (E0 * (y_N - y_AB_i) + ED * y_AB_i) / y_N
        qbers.append(q_AB_i)
    return qbers

def binary_entropy(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

def calculate_ghz_skr_new(sifted_rate, Q_Z_max):
    if FIXED_Q_X >= 0.5 or Q_Z_max >= 0.5: return 0.0
    r_inf = 1 - binary_entropy(FIXED_Q_X) - binary_entropy(Q_Z_max)
    if r_inf < 0: return 0.0
    return sifted_rate * r_inf

# --- 【完全版】Qiskitプロトコルシミュレーション ---
def run_full_qkd_protocol_qiskit(n_qubits, num_shots, max_qber):
    if num_shots == 0: return 0, 0
    
    # 1. ユーザーごとに独立してランダムに基底を選択 (Z=0, X=1)
    bases = np.random.randint(2, size=(num_shots, n_qubits))
    unique_bases, counts = np.unique(bases, axis=0, return_counts=True)
    
    backend = AerSimulator()
    noise_model = NoiseModel()
    depol_param = min(1.0, 2.0 * max_qber)
    if depol_param > 0:
        error = depolarizing_error(depol_param, 1)
        noise_model.add_quantum_error(error, 'measure', [0])
        
    sifted_events = 0
    sifted_errors = 0
    
    # 2. 選択された基底のパターンごとに回路を構築・測定
    for basis_combo, count in zip(unique_bases, counts):
        qc = QuantumCircuit(n_qubits)
        qc.h(0)
        for i in range(1, n_qubits): qc.cx(0, i)
            
        # 測定基底を適用 (X基底ならHゲートを追加)
        for i, b in enumerate(basis_combo):
            if b == 1: qc.h(i)
        qc.measure_all()
        
        job = backend.run(qc, noise_model=noise_model, shots=count)
        result_counts = job.result().get_counts()
        
        # 3. 古典通信によるSifting (ふるい分け)
        is_all_z = np.all(basis_combo == 0)
        is_all_x = np.all(basis_combo == 1)
        
        if is_all_z:
            for out, cnt in result_counts.items():
                sifted_events += cnt
                out_bits = out.replace(" ", "")[::-1]
                alice_bit = out_bits[0]
                if any(alice_bit != out_bits[i] for i in range(1, n_qubits)):
                    sifted_errors += cnt
        elif n_qubits == 2 and is_all_x:
            for out, cnt in result_counts.items():
                sifted_events += cnt
                out_bits = out.replace(" ", "")[::-1]
                if out_bits[0] != out_bits[1]:
                    sifted_errors += cnt
        # 基底が不一致のものは破棄（何もしない）
        
    return sifted_events, sifted_errors

def create_balanced_star_groups(n_users, angles, group_size):
    groups = []; leader = 0; others = [(i, angles[i]) for i in range(1, n_users)]
    others.sort(key=lambda x: x[1])
    while len(others) > 0:
        if len(others) >= group_size - 1:
            members = [leader]
            for i in range(group_size - 1):
                members.append(others.pop(0)[0] if i % 2 == 0 else others.pop(-1)[0])
            groups.append(sorted(members))
        else:
            members = [leader]
            leftover = [x[0] for x in others]
            members.extend(leftover); others.clear()
            candidates = [(i, angles[i]) for i in range(1, n_users) if i not in leftover]
            candidates.sort(key=lambda x: x[1])
            for i in range(min(group_size - len(members), len(candidates))): members.append(candidates[i][0])
            groups.append(sorted(members))
    return groups

def main():
    print(f"=== {GROUP_SIZE}-GHZ Full Qiskit Simulation ===")
    angles = ZENITH_ANGLES[:NUM_USERS] if len(ZENITH_ANGLES) >= NUM_USERS else ZENITH_ANGLES + [0]*(NUM_USERS - len(ZENITH_ANGLES))
    groups = create_balanced_star_groups(NUM_USERS, angles, GROUP_SIZE)
    eta_matrix = generate_realistic_eta(NUM_USERS, 1000, angles)
    group_skrs = []
    
    for g_idx, members in enumerate(groups):
        grp_z_events = 0; grp_z_errors = 0
        n_qubits = len(members) 
        for ts in range(1000):
            current_etas = [eta_matrix[uid][ts] for uid in members]
            current_yield = calculate_yield_theoretical(current_etas)
            n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
            
            if n_events > 0:
                pairwise_qbers = calculate_pairwise_qbers(current_etas[0], current_etas[1:], current_yield)
                max_qber = max(pairwise_qbers)
                batch = min(n_events, BATCH_SIZE)
                scale = n_events / batch
                
                # Qiskit完全シミュレーションを実行
                batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, batch, max_qber)
                grp_z_events += batch_events * scale
                grp_z_errors += batch_errors * scale

        if grp_z_events > 0:
            Q_Z_max = grp_z_errors / grp_z_events
            sifted_rate = grp_z_events / ((1000 * PULSES_PER_SLOT) / FREQ)
            skr = calculate_ghz_skr_new(sifted_rate, Q_Z_max)
        else: skr = 0.0
        
        group_skrs.append(skr)
        print(f"  Group {g_idx} SKR: {skr/1e6:.4f} Mbps")

    print(f"System Throughput: {(min(group_skrs)/len(groups))/1e6:.4f} Mbps")

if __name__ == '__main__':
    main()