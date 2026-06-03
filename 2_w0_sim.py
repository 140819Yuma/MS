import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# 【変更点】generate_realistic_eta ではなく、大元のクラスをインポート
from new_tool import HAPDownlinkChannel

warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- Constants ---
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**5; BATCH_SIZE = 100000
FIXED_Q_X = 0.02  

# シミュレータの使い回し（高速化）
GLOBAL_BACKEND = AerSimulator()

# ==========================================
# W0を動的に変更できるカスタム透過率生成関数
# ==========================================
def custom_generate_realistic_eta(n_users, n_timeslots, zenith_angle_list, current_w0):
    """new_tool.py を変更せずに、メインコード側で W0 を指定して透過率を生成する"""
    params = {
        "W0": current_w0,           # ループから渡された W0 を適用
        "rx_aperture": 0.4,    
        "obs_ratio": 0.3,   
        "n_max": 6,            
        "Cn0": 9.6e-14,        
        "wind_speed": 10,      
        "wavelength": 1550e-9, 
        "ground_station_alt": 0.02, 
        "aerial_platform_alt": 20,  
        "pointing_error": 1e-6,     
        "tracking_efficiency": 0.8  
    }
    
    eta_matrix = []
    if zenith_angle_list is None: 
        zenith_angle_list = [0] * n_users
    
    for i in range(n_users):
        angle = zenith_angle_list[i]
        # 直接クラスを呼び出してパラメータを渡す
        channel = HAPDownlinkChannel(zenith_angle=angle, **params)
        samples = channel.sample_transmittance(n_timeslots)
        eta_matrix.append(samples)
        
    return eta_matrix

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
    p_z = 0.5 # 2-GHZ固定
    bases = np.random.choice([0, 1], size=(num_shots, n_qubits), p=[p_z, 1.0 - p_z])
    unique_bases, counts = np.unique(bases, axis=0, return_counts=True)
    
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
        
        job = GLOBAL_BACKEND.run(qc, noise_model=noise_model, shots=count)
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
# トポロジーのグループ生成関数 (Opt Starのみ)
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

# ==========================================
# シミュレーション実行関数
# ==========================================
def run_topology_simulation(groups, eta_matrix, num_timeslots):
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
        else:
            skr = 0.0
        group_skrs.append(skr)

    optimal_rate_bps, _ = calculate_optimal_time_allocation(group_skrs)
    return optimal_rate_bps / 1e6


def main():
    print("=== Beam Waist (W0) & Scalability Optimization Test (Opt Star Only) ===")
    
    num_timeslots = 1000 
    
    # 4つの W0 の値
    w0_values = [0.05, 0.10, 0.15, 0.20]
    # 5から25まで2ずつ増加
    user_counts = list(range(5, 26, 2)) 
    
    final_results = {w0: {} for w0 in w0_values}
    
    for w0 in w0_values:
        print("\n" + "="*80)
        print(f" EXPERIMENT PHASE: Beam Waist W0 = {w0} m")
        print("="*80)
        
        for n_users in user_counts:
            print(f"  -> Simulating for {n_users} Users...", end=" ", flush=True)
            
            # 【変更点】0〜60度で均等配置 (Equally Spaced)
            angles = np.linspace(0, 60, n_users).tolist()
            
            # カスタム関数で、指定した W0 の透過率マトリクスを生成
            eta_matrix = custom_generate_realistic_eta(n_users, num_timeslots, zenith_angle_list=angles, current_w0=w0)
            
            # トポロジーの実行 (Opt Star のみ)
            groups_star = create_balanced_star_groups(n_users, angles)
            rate_star = run_topology_simulation(groups_star, eta_matrix, num_timeslots)
            
            # 結果の保存
            final_results[w0][n_users] = {
                'Star': rate_star
            }
            print("Done.")

    # ==========================================
    # 最終サマリーの出力
    # ==========================================
    print("\n\n" + "#"*80)
    print(" FINAL SCALABILITY SUMMARY (Optimal Time Allocation Rate [Mbps])")
    print("#"*80)
    
    for w0 in w0_values:
        print(f"\n[ Beam Waist W0 = {w0} m ]")
        print("-" * 30)
        print(f"{'Users':<8} | {'Opt Star':<15}")
        print("-" * 30)
        
        for n_users in user_counts:
            res = final_results[w0][n_users]
            r_star = res['Star']
            
            print(f"{n_users:<8} | {r_star:<15.4f}")
    
    print("\n" + "="*80)

if __name__ == '__main__': 
    main()