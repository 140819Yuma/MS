import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from new_tool import generate_realistic_eta
warnings.filterwarnings('ignore', category=RuntimeWarning)

Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 1000000
FIXED_Q_X = 0.02  

def calculate_yield_theoretical(etas):
    y_N = 1.0
    for eta in etas: y_N *= 1 - (1 - Y0) * (1 - eta)
    return y_N

def calculate_pairwise_qbers(eta_alice, etas_bobs, y_N):
    if y_N == 0: return [0.5] * len(etas_bobs)
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

def run_full_qkd_protocol_qiskit(n_qubits, num_shots, max_qber):
    if num_shots == 0: return 0, 0
    bases = np.random.randint(2, size=(num_shots, n_qubits))
    unique_bases, counts = np.unique(bases, axis=0, return_counts=True)
    backend = AerSimulator()
    noise_model = NoiseModel()
    depol_param = min(1.0, 2.0 * max_qber)
    if depol_param > 0:
        noise_model.add_quantum_error(depolarizing_error(depol_param, 1), 'measure', [0])
    sifted_events = 0; sifted_errors = 0
    for basis_combo, count in zip(unique_bases, counts):
        qc = QuantumCircuit(n_qubits)
        qc.h(0)
        for i in range(1, n_qubits): qc.cx(0, i)
        for i, b in enumerate(basis_combo):
            if b == 1: qc.h(i)
        qc.measure_all()
        job = backend.run(qc, noise_model=noise_model, shots=count)
        result_counts = job.result().get_counts()
        if np.all(basis_combo == 0):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                out_bits = out.replace(" ", "")[::-1]
                if any(out_bits[0] != out_bits[i] for i in range(1, n_qubits)): sifted_errors += cnt
        elif n_qubits == 2 and np.all(basis_combo == 1):
            for out, cnt in result_counts.items():
                sifted_events += cnt
                out_bits = out.replace(" ", "")[::-1]
                if out_bits[0] != out_bits[1]: sifted_errors += cnt
    return sifted_events, sifted_errors

# --- 【変更箇所】チェイン型（数珠繋ぎ）のグループ生成関数 ---
def create_chain_groups(n_users, angles, group_size):
    """
    ユーザーをゼニスアングルの小さい順（物理的に近い順）に並べ、
    中継ノードを1つ重ねながら数珠繋ぎ（Chain）のグループを構築する。
    各グループ内で一番ゼニスアングルが小さいユーザーを必ずアリス（index 0）に設定する。
    """
    sorted_users = sorted(range(n_users), key=lambda x: angles[x])
    groups = []
    if n_users < group_size:
        return []
    
    step = group_size - 1 
    for i in range(0, n_users - 1, step):
        group = sorted_users[i : i + group_size]
        # 端数が出た場合、後ろから group_size 分だけ確保
        if len(group) < group_size:
            group = sorted_users[n_users - group_size : n_users]
            
        # グループ内でゼニスアングルが一番小さいユーザーをアリスにする
        group = sorted(group, key=lambda x: angles[x])
        if group not in groups:
            groups.append(group)
            
        # 最後のユーザーに到達したらチェイン完成
        if group[-1] == sorted_users[-1]:
            break
            
    return groups

def main():
    print("=== Scalability Full Qiskit Simulation (Chain Topology): Users 5 to 25 ===")
    user_counts = list(range(5, 26, 1))
    ghz_sizes = [2, 3, 4, 5]
    results = {size: {} for size in ghz_sizes}
    num_timeslots = 1000 
    
    for n_users in user_counts:
        print(f"\n--- Simulating NUM_USERS = {n_users} ---")
        #angles = np.linspace(0, 60, n_users).tolist()
        angles = [(i % 3) * 15 for i in range(n_users)]
        eta_matrix = generate_realistic_eta(n_users, num_timeslots, angles)
        
        for size in ghz_sizes:
            if n_users < size:
                results[size][n_users] = 0.0; continue
            
            # スター型ではなくチェイン型でグループを生成
            groups = create_chain_groups(n_users, angles, size)
            num_links = len(groups)
            group_skrs = []
            
            for members in groups:
                grp_z_events = 0; grp_z_errors = 0
                n_qubits = len(members) 
                for ts in range(num_timeslots):
                    current_etas = [eta_matrix[uid][ts] for uid in members]
                    current_yield = calculate_yield_theoretical(current_etas)
                    n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
                    
                    if n_events > 0:
                        max_qber = max(calculate_pairwise_qbers(current_etas[0], current_etas[1:], current_yield))
                        batch = min(n_events, BATCH_SIZE)
                        batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, batch, max_qber)
                        grp_z_events += batch_events * (n_events / batch)
                        grp_z_errors += batch_errors * (n_events / batch)

                if grp_z_events > 0:
                    skr = calculate_ghz_skr_new(grp_z_events / ((num_timeslots * PULSES_PER_SLOT) / FREQ), grp_z_errors / grp_z_events)
                else: skr = 0.0
                group_skrs.append(skr)

            # チェインのボトルネック(最小値)を取り、時分割ペナルティ(num_linksで割る)を課す
            final_rate = (min(group_skrs) / num_links) / 1e6 if group_skrs else 0.0
            results[size][n_users] = final_rate
            print(f"  {size}-GHZ Chain (Links:{num_links}): {final_rate:.4f} Mbps")

    print("\n\n" + "="*70)
    print(" SUMMARY: Chain Topology End-to-End Throughput (Mbps)")
    print("="*70)
    print(f"{'Users':>6} | {'2-GHZ Chain':>12} | {'3-GHZ Chain':>12} | {'4-GHZ Chain':>12} | {'5-GHZ Chain':>12}")
    print("-" * 70)
    for n in user_counts:
        row_str = f"{n:6} |"
        for size in ghz_sizes:
            val = results[size].get(n, 0.0)
            row_str += f"{'N/A':>12} |" if val == 0.0 and n < size else f"{val:12.4f} |"
        print(row_str)
    print("="*70)

if __name__ == '__main__': main()