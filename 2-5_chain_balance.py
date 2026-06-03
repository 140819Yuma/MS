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

# --- 【アップデート】平均値を均等化するチェイン型グループ生成 ---
def create_balanced_chain_groups(n_users, angles, group_size):
    if n_users < group_size:
        return []
        
    # 1. 必要なグループ数(M)とリレー数(M-1)を計算
    num_groups = math.ceil((n_users - 1) / (group_size - 1))
    num_relays = num_groups - 1
    
    # 2. リレーノードの選定 (全体の平均角度に最も近いユーザーを選ぶ)
    avg_angle = np.mean(angles[:n_users])
    sorted_by_diff = sorted(range(n_users), key=lambda x: abs(angles[x] - avg_angle))
    relays = sorted_by_diff[:num_relays]
    
    # 3. 割り当て待ちのユーザー (角度が大きい/条件が悪い順にソート)
    available_users = [u for u in range(n_users) if u not in relays]
    available_users.sort(key=lambda x: angles[x], reverse=True)
    
    # 4. グループの初期化とリレーの配置 (数珠繋ぎの形成)
    groups = [[] for _ in range(num_groups)]
    for i, relay in enumerate(relays):
        groups[i].append(relay)
        groups[i+1].append(relay)
        
    # 5. Greedy法で残りのユーザーを割り当てて、各グループの合計値(平均値)を揃える
    for u in available_users:
        valid_groups = [i for i in range(num_groups) if len(groups[i]) < group_size]
        if not valid_groups:
            break # 全グループが定員に達した場合
            
        # 現在の「角度の合計値」が一番小さいグループにユーザーを追加
        best_group = min(valid_groups, key=lambda i: sum(angles[member] for member in groups[i]))
        groups[best_group].append(u)
        
    # 6. 端数調整 (グループの人数が group_size に満たない場合、条件の良い人を重複させて定員を満たす)
    for i in range(num_groups):
        while len(groups[i]) < group_size:
            for u in sorted(range(n_users), key=lambda x: angles[x]):
                if u not in groups[i]:
                    groups[i].append(u)
                    break
                    
    # 7. 【重要】各グループ内でゼニスアングルが一番小さいユーザーをアリス(index 0)にする
    for i in range(num_groups):
        groups[i] = sorted(groups[i], key=lambda x: angles[x])
        
    return groups

def main():
    print("=== Scalability Full Qiskit Simulation (Balanced Chain Topology) ===")
    user_counts = list(range(5, 26, 1))
    ghz_sizes = [2, 3, 4, 5]
    results = {size: {} for size in ghz_sizes}
    num_timeslots = 1000 
    
    for n_users in user_counts:
        print(f"\n--- Simulating NUM_USERS = {n_users} ---")
        angles = np.linspace(0, 60, n_users).tolist()
        #angles = [(i % 3) * 15 for i in range(n_users)]
        eta_matrix = generate_realistic_eta(n_users, num_timeslots, angles)
        
        for size in ghz_sizes:
            if n_users < size:
                results[size][n_users] = 0.0; continue
            
            # 平均値均等化チェイン関数を呼び出し
            groups = create_balanced_chain_groups(n_users, angles, size)
            num_links = len(groups)
            group_skrs = []
            
            # デバッグ用：各グループのメンバーと平均角度を出力して均等化を確認
            if size == 3 and n_users == 7: # 例として7ユーザー/3-GHZの時だけ出力
                print(f"  [Debug] 3-GHZ Grouping for 7 Users:")
                for i, g in enumerate(groups):
                    g_angles = [angles[u] for u in g]
                    print(f"    G{i}: {g} -> Angles: {g_angles}, Avg: {np.mean(g_angles):.1f}")
            
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

            final_rate = (min(group_skrs) / num_links) / 1e6 if group_skrs else 0.0
            results[size][n_users] = final_rate
            print(f"  {size}-GHZ Balanced Chain (Links:{num_links}): {final_rate:.4f} Mbps")

    print("\n\n" + "="*75)
    print(" SUMMARY: Balanced Chain Topology End-to-End Throughput (Mbps)")
    print("="*75)
    print(f"{'Users':>6} | {'2-GHZ Chain':>13} | {'3-GHZ Chain':>13} | {'4-GHZ Chain':>13} | {'5-GHZ Chain':>13}")
    print("-" * 75)
    for n in user_counts:
        row_str = f"{n:6} |"
        for size in ghz_sizes:
            val = results[size].get(n, 0.0)
            row_str += f"{'N/A':>13} |" if val == 0.0 and n < size else f"{val:13.4f} |"
        print(row_str)
    print("="*75)

if __name__ == '__main__': main()