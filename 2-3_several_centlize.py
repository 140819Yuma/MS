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

# ==========================================
# 時間割り当て最適化の計算
# ==========================================
def calculate_optimal_time_allocation(group_skrs):
    """
    提案された数式に基づき、最適化されたSKRと各グループの時間の割合を計算する
    """
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
                batch = min(n_events, BATCH_SIZE)
                batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, batch, max_qber)
                grp_z_events += batch_events * (n_events / batch)
                grp_z_errors += batch_errors * (n_events / batch)

        if grp_z_events > 0:
            skr = calculate_ghz_skr_new(grp_z_events / ((num_timeslots * PULSES_PER_SLOT) / FREQ), grp_z_errors / grp_z_events)
        else:
            skr = 0.0
        group_skrs.append(skr)

    # 1. 均等割り当て（従来）のレート
    uniform_rate = (min(group_skrs) / num_links) / 1e6 if group_skrs else 0.0
    
    # 2. 最適化割り当て（提案手法）の計算
    optimal_rate_bps, time_allocs = calculate_optimal_time_allocation(group_skrs)
    optimal_rate_mbps = optimal_rate_bps / 1e6

    return uniform_rate, optimal_rate_mbps, time_allocs, len(groups)


def main():
    print("=== Scalability Full Qiskit Simulation (Centralized Star with Time Optimization) ===")
    
    n_users = 11
    ghz_sizes = [2, 3]
    num_timeslots = 1000 
    num_trials = 5 
    
    for trial in range(1, num_trials + 1):
        print(f"\n" + "#"*80)
        print(f"--- Simulating Trial {trial} / {num_trials} (NUM_USERS = {n_users}) ---")
        print("#"*80)
        
        # ---------------------------------------------------------
        # シナリオ選択（検証したい配置のコメントアウトを外してください）
        # ---------------------------------------------------------
        
        # 0〜60度で全員がランダムに配置
        angles = np.random.uniform(0, 60, n_users).tolist()

        # 0〜15度で全員がランダムに配置（超密集）
        # angles = np.random.uniform(0, 15, n_users).tolist()

        # 0〜30度で全員がランダムに配置（やや密集）
        # angles = np.random.uniform(0, 30, n_users).tolist()

        # 0〜20度に8人、20〜60度に3人を配置（中央密集）
        # angles = np.random.uniform(0, 20, 8).tolist() + np.random.uniform(20, 60, 3).tolist()
        # np.random.shuffle(angles) 

        # 0〜20度に2人、40〜60度に9人を配置（端密集）
        # angles = np.random.uniform(0, 20, 2).tolist() + np.random.uniform(40, 60, 9).tolist()
        # np.random.shuffle(angles)

        # 5〜15度に5人、45〜55度に6人を配置（中間の20〜40度には誰もいない分断配置）
        # angles = np.random.uniform(5, 15, 5).tolist() + np.random.uniform(45, 55, 6).tolist()
        # np.random.shuffle(angles)

        # 0度から60度まで等間隔に11人を配置
        # angles = np.linspace(0, 60, n_users).tolist()

        # ---------------------------------------------------------
        
        angles_formatted = [round(a, 2) for a in angles]
        print(f"  * Generated Zenith Angles (degrees): {angles_formatted}\n")
        
        eta_matrix = generate_realistic_eta(n_users, num_timeslots, angles)
        
        results_star = {}

        for size in ghz_sizes:
            print(f"  Evaluating {size}-GHZ topology...")
            
            groups_star = create_balanced_star_groups(n_users, angles, size)
            uni_rate, opt_rate, time_allocs, links = run_topology_simulation(groups_star, eta_matrix, num_timeslots)
            
            results_star[size] = {
                'uni_rate': uni_rate,
                'opt_rate': opt_rate,
                'time_allocs': time_allocs,
                'links': links
            }

        # 最終比較サマリーの出力
        print("\n" + "="*80)
        print(f" SUMMARY: Time Optimization Results (Mbps) - Trial {trial}")
        print("="*80)
        
        for size in ghz_sizes:
            data = results_star[size]
            print(f"【{size}-GHZ】 Total Groups: {data['links']}")
            print(f"  - Uniform Rate (従来)  : {data['uni_rate']:.4f} Mbps")
            print(f"  - Optimal Rate (提案)  : {data['opt_rate']:.4f} Mbps")
            
            alloc_str = ", ".join([f"{p*100:.1f}%" for p in data['time_allocs']])
            print(f"  - Optimal Time Ratios: [{alloc_str}]")
            
            if data['uni_rate'] > 0:
                boost = (data['opt_rate'] / data['uni_rate'] - 1) * 100
                print(f"  => Performance Boost : +{boost:.1f} %")
            else:
                print("  => Performance Boost : N/A (Rate is 0)")
            print("-" * 80)

if __name__ == '__main__': 
    main()