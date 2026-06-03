import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from new_tool import generate_realistic_eta
warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- Constants ---
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 1000000
FIXED_Q_X = 0.02  

# ==========================================
# 物理層の計算関数
# ==========================================
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


# ==========================================
# ネットワーク層（トポロジー）のグループ生成関数
# ==========================================

# 1. 中央集権型（Balanced Star）
def create_balanced_star_groups(n_users, angles, group_size):
    sorted_users = sorted(range(n_users), key=lambda x: angles[x])
    center_node = sorted_users[0]
    remaining = sorted_users[1:]
    
    mixed_remaining = []
    left, right = 0, len(remaining) - 1
    while left <= right:
        mixed_remaining.append(remaining[left])
        left += 1
        if left <= right:
            mixed_remaining.append(remaining[right])
            right -= 1
            
    groups = []
    k_others = group_size - 1
    num_groups = math.ceil(len(mixed_remaining) / k_others)
    
    for i in range(num_groups):
        chunk = mixed_remaining[i*k_others : (i+1)*k_others]
        while len(chunk) < k_others:
            for u in sorted_users:
                if u not in chunk and u != center_node:
                    chunk.append(u)
                    break
        g = [center_node] + chunk
        g = sorted(g, key=lambda x: angles[x])
        if g not in groups: groups.append(g)
    return groups

# 2. チェイン型（Balanced Chain）
def create_balanced_chain_groups(n_users, angles, group_size):
    sorted_users = sorted(range(n_users), key=lambda x: angles[x])
    
    mixed_users = []
    left, right = 0, len(sorted_users) - 1
    while left <= right:
        mixed_users.append(sorted_users[left])
        left += 1
        if left <= right:
            mixed_users.append(sorted_users[right])
            right -= 1
            
    groups = []
    step = group_size - 1
    for i in range(0, len(mixed_users) - 1, step):
        chunk = mixed_users[i : i + group_size]
        while len(chunk) < group_size:
            for u in sorted_users:
                if u not in chunk:
                    chunk.append(u)
                    break
        g = sorted(chunk, key=lambda x: angles[x])
        if g not in groups: groups.append(g)
    return groups

# 3. クラスター階層型（Balanced Cluster-Tree）
def create_balanced_cluster_groups(n_users, angles, group_size):
    sorted_users = sorted(range(n_users), key=lambda x: angles[x])
    groups = []
    current_level_nodes = sorted_users.copy()
    
    while len(current_level_nodes) > 1:
        if len(current_level_nodes) <= group_size:
            chunk = current_level_nodes.copy()
            for u in sorted_users:
                if len(chunk) == group_size: break
                if u not in chunk: chunk.append(u)
            chunk = sorted(chunk, key=lambda x: angles[x])
            if chunk not in groups: groups.append(chunk)
            break

        num_groups = math.ceil(len(current_level_nodes) / group_size)
        temp_groups = [[] for _ in range(num_groups)]
        
        for i in range(num_groups):
            temp_groups[i].append(current_level_nodes[i])
            
        remaining_users = current_level_nodes[num_groups:]
        remaining_users.sort(key=lambda x: angles[x], reverse=True)
        
        for u in remaining_users:
            valid_groups = [i for i in range(num_groups) if len(temp_groups[i]) < group_size]
            if not valid_groups: break
            best_group = min(valid_groups, key=lambda i: sum(angles[member] for member in temp_groups[i]))
            temp_groups[best_group].append(u)
            
        for i in range(num_groups):
            while len(temp_groups[i]) < group_size:
                for u in sorted_users:
                    if u not in temp_groups[i]:
                        temp_groups[i].append(u)
                        break
                        
        next_level_nodes = []
        for g in temp_groups:
            g = sorted(g, key=lambda x: angles[x])
            if g not in groups: groups.append(g)
            if g[0] not in next_level_nodes:
                next_level_nodes.append(g[0])
                
        current_level_nodes = next_level_nodes
        
    return groups

# ==========================================
# メインシミュレーション実行
# ==========================================
def run_topology_simulation(groups, eta_matrix, num_timeslots):
    group_skrs = []
    num_links = len(groups)
    
    for members in groups:
        grp_z_events = 0; grp_z_errors = 0
        n_qubits = len(members) 
        for ts in range(num_timeslots):
            current_etas = [eta_matrix[uid][ts] for uid in members]
            current_yield = calculate_yield_theoretical(current_etas)
            n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
            
            if n_events > 0:
                max_qber = max(calculate_pairwise_qbers(current_etas[0], current_etas[1:], current_yield))
                # シミュレーション時間短縮のため、バッチサイズでスケール
                batch = min(n_events, BATCH_SIZE)
                batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, batch, max_qber)
                grp_z_events += batch_events * (n_events / batch)
                grp_z_errors += batch_errors * (n_events / batch)

        if grp_z_events > 0:
            skr = calculate_ghz_skr_new(grp_z_events / ((num_timeslots * PULSES_PER_SLOT) / FREQ), grp_z_errors / grp_z_events)
        else:
            skr = 0.0
        group_skrs.append(skr)

    # ボトルネックレートをリンク数で割る（TDMペナルティ）
    final_rate = (min(group_skrs) / num_links) / 1e6 if group_skrs else 0.0
    return final_rate, num_links


def main():
    print("=== Scalability Full Qiskit Simulation (Integrated Topology Comparison) ===")
    
    n_users = 11
    ghz_sizes = [2, 3]
    num_timeslots = 1000 
    num_trials = 5  # 実行回数を指定
    
    for trial in range(1, num_trials + 1):
        print(f"\n" + "#"*80)
        print(f"--- Simulating Trial {trial} / {num_trials} (NUM_USERS = {n_users}) ---")
        print("#"*80)
        
        # 【重要】角度とeta_matrixを1度だけ生成し、すべてのトポロジーで使い回す
        angles = np.random.uniform(0, 60, n_users).tolist()
        angles_formatted = [round(a, 2) for a in angles]
        print(f"  * Generated Zenith Angles (degrees): {angles_formatted}\n")
        
        eta_matrix = generate_realistic_eta(n_users, num_timeslots, angles)
        
        results_star = {}
        results_chain = {}
        results_tree = {}

        for size in ghz_sizes:
            print(f"  Evaluating {size}-GHZ topologies...")
            
            # 1. 中央集権型 (Star)
            groups_star = create_balanced_star_groups(n_users, angles, size)
            rate_star, links_star = run_topology_simulation(groups_star, eta_matrix, num_timeslots)
            results_star[size] = (rate_star, links_star)
            
            # 2. チェイン型 (Chain)
            groups_chain = create_balanced_chain_groups(n_users, angles, size)
            rate_chain, links_chain = run_topology_simulation(groups_chain, eta_matrix, num_timeslots)
            results_chain[size] = (rate_chain, links_chain)
            
            # 3. 階層型 (Cluster-Tree)
            groups_tree = create_balanced_cluster_groups(n_users, angles, size)
            rate_tree, links_tree = run_topology_simulation(groups_tree, eta_matrix, num_timeslots)
            results_tree[size] = (rate_tree, links_tree)

        # 最終比較サマリーの出力
        print("\n" + "="*80)
        print(f" SUMMARY: Topology Performance Comparison (Mbps) - Trial {trial}")
        print("="*80)
        print(f"{'Topology':<15} | {'2-GHZ Rate':<15} | {'2-GHZ Links':<11} | {'3-GHZ Rate':<15} | {'3-GHZ Links':<11}")
        print("-" * 80)
        
        # Star
        print(f"{'Balanced Star':<15} | {results_star[2][0]:<15.4f} | {results_star[2][1]:<11} | {results_star[3][0]:<15.4f} | {results_star[3][1]:<11}")
        # Chain
        print(f"{'Balanced Chain':<15} | {results_chain[2][0]:<15.4f} | {results_chain[2][1]:<11} | {results_chain[3][0]:<15.4f} | {results_chain[3][1]:<11}")
        # Tree
        print(f"{'Balanced Tree':<15} | {results_tree[2][0]:<15.4f} | {results_tree[2][1]:<11} | {results_tree[3][0]:<15.4f} | {results_tree[3][1]:<11}")
        print("="*80 + "\n")

if __name__ == '__main__': 
    main()