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
FREQ = 1e9; PULSES_PER_SLOT = 10**5; BATCH_SIZE = 100000
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
    
    p_z = 0.5
    bases = np.random.choice([0, 1], size=(num_shots, n_qubits), p=[p_z, 1.0 - p_z])
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
# 時間割り当て最適化の計算
# ==========================================
def calculate_optimal_time_allocation(group_skrs):
    if not group_skrs or any(skr == 0.0 for skr in group_skrs):
        n = len(group_skrs)
        return 0.0, [1.0 / n] * n if n > 0 else []

    max_skr = max(group_skrs)
    t_ratios = [max_skr / skr for skr in group_skrs]
    
    total_t = sum(t_ratios)
    time_allocations = [t / total_t for t in t_ratios]
    
    optimal_rate = 1.0 / sum(1.0 / skr for skr in group_skrs)
    return optimal_rate, time_allocations

# ==========================================
# ネットワーク層（トポロジー）のグループ生成関数
# ==========================================
def create_balanced_star_groups(n_users, angles, group_size=2):
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
    for i in range(math.ceil(len(mixed_remaining) / k_others)):
        chunk = mixed_remaining[i*k_others : (i+1)*k_others]
        g = sorted([center_node] + chunk, key=lambda x: angles[x])
        groups.append(g)
    return groups

def create_balanced_chain_groups(n_users, angles, group_size=2):
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
        g = sorted(chunk, key=lambda x: angles[x])
        if g not in groups: groups.append(g)
    return groups

def create_random_star_groups(n_users, angles, group_size=2):
    sorted_users = sorted(range(n_users), key=lambda x: angles[x])
    center_node = int(np.random.choice(range(n_users)))
    remaining = [u for u in sorted_users if u != center_node]
    
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
    for i in range(math.ceil(len(mixed_remaining) / k_others)):
        chunk = mixed_remaining[i*k_others : (i+1)*k_others]
        g = sorted([center_node] + chunk, key=lambda x: angles[x])
        groups.append(g)
    return groups, center_node

# ==========================================
# メインシミュレーション実行関数
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
                batch = min(n_events, BATCH_SIZE)
                
                batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, batch, max_qber)
                grp_z_events += batch_events * (n_events / batch)
                grp_z_errors += batch_errors * (n_events / batch)

        if grp_z_events > 0:
            skr = calculate_ghz_skr_new(grp_z_events / ((num_timeslots * PULSES_PER_SLOT) / FREQ), grp_z_errors / grp_z_events)
        else:
            skr = 0.0
        group_skrs.append(skr)

    uniform_rate = (min(group_skrs) / num_links) / 1e6 if group_skrs else 0.0
    optimal_rate_bps, time_allocs = calculate_optimal_time_allocation(group_skrs)
    optimal_rate_mbps = optimal_rate_bps / 1e6

    return uniform_rate, optimal_rate_mbps, time_allocs, len(groups)

# シナリオ配列生成用ヘルパー
def get_mixed_angles(n_near, near_range, n_far, far_range):
    a = np.random.uniform(near_range[0], near_range[1], n_near).tolist() + \
        np.random.uniform(far_range[0], far_range[1], n_far).tolist()
    np.random.shuffle(a)
    return a

def main():
    print("=== 2-GHZ Topology Optimization Comparison (11 Users) ===")
    
    n_users = 11
    num_timeslots = 1000 
    
    # 5つのシナリオを定義（n_usersが変わっても自動で対応するように修正）
    
    # シナリオ4用の人数計算（例：およそ3割が近く、7割が遠く）
    s4_near = max(1, int(n_users * 3 / 11))
    s4_far = n_users - s4_near

    # シナリオ5用の人数計算（例：およそ7割が近く、3割が遠く）
    s5_near = n_users - max(1, int(n_users * 3 / 11))
    s5_far = n_users - s5_near

    scenarios = [
        {"id": 1, "name": "Random (0 - 60 degrees)", 
         "angles": np.random.uniform(0, 60, n_users).tolist()},
        {"id": 2, "name": "Dense Near (0 - 15 degrees)", 
         "angles": np.random.uniform(0, 15, n_users).tolist()},
        {"id": 3, "name": "Dense Far (45 - 60 degrees)", 
         "angles": np.random.uniform(45, 60, n_users).tolist()},
        {"id": 4, "name": f"{s4_near} Near (0-20), {s4_far} Far (40-60)", 
         "angles": get_mixed_angles(s4_near, (0, 20), s4_far, (40, 60))},
        {"id": 5, "name": f"{s5_near} Near (0-20), {s5_far} Far (40-60)", 
         "angles": get_mixed_angles(s5_near, (0, 20), s5_far, (40, 60))}
    ]
    
    for scenario in scenarios:
        print("\n" + "="*80)
        print(f" SCENARIO {scenario['id']}: {scenario['name']}")
        print("="*80)
        
        angles = scenario['angles']
        angles_formatted = [round(a, 2) for a in angles]
        print(f"  * Generated Zenith Angles (degrees): {angles_formatted}\n")
        
        eta_matrix = generate_realistic_eta(n_users, num_timeslots, angles)
        
        # 1. 中央集権型 (Balanced Star)
        print("  Evaluating [1] Centralized Star (Best Node Alice)...")
        groups_star = create_balanced_star_groups(n_users, angles, group_size=2)
        star_uni, star_opt, star_allocs, star_links = run_topology_simulation(groups_star, eta_matrix, num_timeslots)
        
        # 2. チェイン型 (Balanced Chain)
        print("  Evaluating [2] Balanced Chain...")
        groups_chain = create_balanced_chain_groups(n_users, angles, group_size=2)
        chain_uni, chain_opt, chain_allocs, chain_links = run_topology_simulation(groups_chain, eta_matrix, num_timeslots)
        
        # 3. ランダム中央集権型 (Random Star)
        print("  Evaluating [3] Random Centralized Star...")
        groups_rnd_star, rnd_alice_id = create_random_star_groups(n_users, angles, group_size=2)
        print(f"    -> Randomly Selected Alice Node ID: {rnd_alice_id} (Angle: {round(angles[rnd_alice_id], 2)} deg)")
        rnd_uni, rnd_opt, rnd_allocs, rnd_links = run_topology_simulation(groups_rnd_star, eta_matrix, num_timeslots)
        
        # --- 結果の出力 ---
        print("\n" + "-"*80)
        print(f" RESULTS for Scenario {scenario['id']}")
        print("-"*80)
        
        results = [
            ("Centralized Star", star_uni, star_opt, star_allocs, star_links),
            ("Balanced Chain", chain_uni, chain_opt, chain_allocs, chain_links),
            ("Random Star", rnd_uni, rnd_opt, rnd_allocs, rnd_links)
        ]
        
        for name, uni, opt, allocs, links in results:
            print(f"【{name}】 Total Links: {links}")
            print(f"  - Uniform Rate  : {uni:.4f} Mbps")
            print(f"  - Optimal Rate  : {opt:.4f} Mbps")
            
            if uni > 0:
                boost = (opt / uni - 1) * 100
                print(f"  => Perf Boost   : +{boost:.1f} %")
            else:
                print("  => Perf Boost   : N/A (Rate is 0)")
            print(" ")

if __name__ == '__main__': 
    main()