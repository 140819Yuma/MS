import numpy as np
import math
import warnings
import sys
import datetime
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from new_tool import generate_realistic_eta
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==========================================
# ターミナル＆ファイル同時出力用のロガークラス
# ==========================================
class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_file = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()

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

def run_full_qkd_protocol_qiskit(n_qubits, num_shots, max_qber, p_z):
    if num_shots == 0: return 0, 0
    
    # ここで2-GHZも3-GHZも指定された確率(今回は0.5)で基底を選択します
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
# ネットワーク層（トポロジー）のグループ生成関数
# ==========================================
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
                
                # 【変更点】フェアな比較のため、2-GHZも3-GHZもZ基底確率は0.5で固定
                batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, batch, max_qber, 0.5)
                
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

def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"sim_results_{timestamp}.txt"
    logger = DualLogger(log_filename)
    sys.stdout = logger

    print(f"=== Scalability Full Qiskit Simulation (Fair Baseline: Z-basis 50%) ===")
    print(f"Log file created: {log_filename}")
    
    ghz_sizes = [2, 3]
    num_timeslots = 1000 
    
    user_counts = list(range(3, 101, 2))
    final_summary = {2: {}, 3: {}}
    
    for n_users in user_counts:
        print("\n" + "="*80)
        print(f" SIMULATING: NUM_USERS = {n_users}")
        print("="*80)
        
        #angles = np.random.uniform(0, 60, n_users).tolist()
        angles=np.linspace(0, 60, n_users).tolist()  # 均等に分布させる場合はこちらを使用
        angles_formatted = [round(a, 2) for a in angles]
        print(f"  * Generated Zenith Angles (degrees): {angles_formatted}\n")
        
        eta_matrix = generate_realistic_eta(n_users, num_timeslots, angles)
        results_star = {}

        for size in ghz_sizes:
            if n_users < size:
                continue

            print(f"  Evaluating {size}-GHZ topology...")
            groups_star = create_balanced_star_groups(n_users, angles, size)
            uni_rate, opt_rate, time_allocs, links = run_topology_simulation(groups_star, eta_matrix, num_timeslots)
            
            results_star[size] = {
                'uni_rate': uni_rate,
                'opt_rate': opt_rate,
                'time_allocs': time_allocs,
                'links': links
            }
            
            final_summary[size][n_users] = {
                'uni': uni_rate,
                'opt': opt_rate,
                'links': links
            }

        print("\n" + "-"*80)
        print(f" RESULTS for {n_users} Users")
        print("-"*80)
        for size in ghz_sizes:
            data = results_star.get(size)
            if not data: continue
            
            print(f"【{size}-GHZ】 Total Groups: {data['links']}")
            print(f"  - Uniform Rate (従来)  : {data['uni_rate']:.4f} Mbps")
            print(f"  - Optimal Rate (提案)  : {data['opt_rate']:.4f} Mbps")
            
            if len(data['time_allocs']) > 10000000000:
                alloc_str = ", ".join([f"{p*100:.1f}%" for p in data['time_allocs'][:5]]) + f", ... (Total {len(data['time_allocs'])} groups)"
            else:
                alloc_str = ", ".join([f"{p*100:.1f}%" for p in data['time_allocs']])
            print(f"  - Optimal Time Ratios: [{alloc_str}]")
            
            if data['uni_rate'] > 0:
                boost = (data['opt_rate'] / data['uni_rate'] - 1) * 100
                print(f"  => Performance Boost : +{boost:.1f} %")
            else:
                print("  => Performance Boost : N/A (Rate is 0)")
            print(" ")

    print("\n" + "#"*80)
    print(" FINAL SCALABILITY SUMMARY (Mbps)")
    print("#"*80)
    print(f"{'Users':<6} | {'2-GHZ Uniform':<15} | {'2-GHZ Optimal':<15} | {'3-GHZ Uniform':<15} | {'3-GHZ Optimal':<15}")
    print("-" * 75)
    for n_users in user_counts:
        r2_uni = final_summary[2].get(n_users, {}).get('uni', 0.0)
        r2_opt = final_summary[2].get(n_users, {}).get('opt', 0.0)
        r3_uni = final_summary[3].get(n_users, {}).get('uni', 0.0)
        r3_opt = final_summary[3].get(n_users, {}).get('opt', 0.0)
        print(f"{n_users:<6} | {r2_uni:<15.4f} | {r2_opt:<15.4f} | {r3_uni:<15.4f} | {r3_opt:<15.4f}")
    print("#"*80 + "\n")

    sys.stdout = sys.__stdout__
    logger.close()
    print(f"Simulation completed. Results saved to {log_filename}")

if __name__ == '__main__': 
    main()