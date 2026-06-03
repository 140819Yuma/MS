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

# 位相エラーを 2% (0.02) に設定
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

# --- 【アップデート】各グループの平均値を均等化するクラスター階層型 ---
def create_balanced_cluster_groups(n_users, angles, group_size):
    """
    ゼニスアングルの平均が各クラスター間で均等になるように(High-Low Mixing)振り分け、
    各クラスター内の最良ノードを上位バックボーンに引き上げる階層型アルゴリズム。
    """
    sorted_users = sorted(range(n_users), key=lambda x: angles[x])
    groups = []
    current_level_nodes = sorted_users.copy()
    
    while len(current_level_nodes) > 1:
        # 1. 全員が1つのグループに収まる場合（最上位バックボーン層）
        if len(current_level_nodes) <= group_size:
            chunk = current_level_nodes.copy()
            # 定員に満たない場合は、システム全体から最も条件の良いユーザーを助っ人として補充
            for u in sorted_users:
                if len(chunk) == group_size: break
                if u not in chunk: chunk.append(u)
            chunk = sorted(chunk, key=lambda x: angles[x])
            if chunk not in groups: groups.append(chunk)
            break

        # 2. 必要なグループ数(M)を計算
        num_groups = math.ceil(len(current_level_nodes) / group_size)
        temp_groups = [[] for _ in range(num_groups)]
        
        # 3. 現在の階層で最も条件の良いユーザーたちを、各グループの「親（リーダー）」として1人ずつ配置
        for i in range(num_groups):
            temp_groups[i].append(current_level_nodes[i])
            
        # 4. 残りのユーザーを「条件が悪い（アングルが大きい）」順にソートする
        remaining_users = current_level_nodes[num_groups:]
        remaining_users.sort(key=lambda x: angles[x], reverse=True)
        
        # 5. 貪欲法（Greedy Allocation）：現在の「角度の合計」が一番小さいグループに重いユーザーを入れていく
        for u in remaining_users:
            valid_groups = [i for i in range(num_groups) if len(temp_groups[i]) < group_size]
            if not valid_groups: break
            # 合計値が一番小さいグループを探す
            best_group = min(valid_groups, key=lambda i: sum(angles[member] for member in temp_groups[i]))
            temp_groups[best_group].append(u)
            
        # 6. 端数調整：グループの人数が足りない場合、システム全体から条件の良い人を補充
        for i in range(num_groups):
            while len(temp_groups[i]) < group_size:
                for u in sorted_users:
                    if u not in temp_groups[i]:
                        temp_groups[i].append(u)
                        break
                        
        # 7. リーダーを抽出して次の上位階層へ
        next_level_nodes = []
        for g in temp_groups:
            # グループ内で一番ゼニスアングルが小さいユーザーをアリス（インデックス0）に設定
            g = sorted(g, key=lambda x: angles[x])
            if g not in groups:
                groups.append(g)
            # 各グループの最良ノード（アリス）を次の親として登録
            if g[0] not in next_level_nodes:
                next_level_nodes.append(g[0])
                
        current_level_nodes = next_level_nodes
        
    return groups

def main():
    print("=== Scalability Full Qiskit Simulation (Balanced Cluster-Tree) ===")
    print(f"    * Phase Error (FIXED_Q_X) = {FIXED_Q_X*100}%\n")
    
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
                
            # ここで「平均値均等化」のクラスター階層型関数を呼び出し
            groups = create_balanced_cluster_groups(n_users, angles, size)
            num_links = len(groups)
            group_skrs = []
            
            # --- デバッグ表示：グループが綺麗に平均化されているか確認 ---
            if size == 3 and n_users == 9: 
                print(f"  [Debug] 3-GHZ Balanced Cluster for 9 Users:")
                for i, g in enumerate(groups):
                    g_angles = [angles[u] for u in g]
                    print(f"    Group {i+1}: {g} (Leader: {g[0]}) -> Avg Angle: {np.mean(g_angles):.1f}")

            for members in groups:
                grp_z_events = 0; grp_z_errors = 0
                n_qubits = len(members) 
                for ts in range(num_timeslots):
                    current_etas = [eta_matrix[uid][ts] for uid in members]
                    current_yield = calculate_yield_theoretical(current_etas)
                    n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
                    
                    if n_events > 0:
                        max_qber = max(calculate_pairwise_qbers(current_etas[0], current_etas[1:], current_yield))
                        # 妥協なしの全弾Qiskit投入
                        batch_events, batch_errors = run_full_qkd_protocol_qiskit(n_qubits, n_events, max_qber)
                        grp_z_events += batch_events
                        grp_z_errors += batch_errors

                if grp_z_events > 0:
                    skr = calculate_ghz_skr_new(grp_z_events / ((num_timeslots * PULSES_PER_SLOT) / FREQ), grp_z_errors / grp_z_events)
                else: skr = 0.0
                group_skrs.append(skr)

            # End-to-End スループット (最小レートをリンク数 M で時分割)
            final_rate = (min(group_skrs) / num_links) / 1e6 if group_skrs else 0.0
            results[size][n_users] = final_rate
            print(f"  {size}-GHZ Bal-Clst (Links:{num_links}): {final_rate:.4f} Mbps")

    print("\n\n" + "="*70)
    print(" SUMMARY: Balanced Cluster-Tree End-to-End Throughput (Mbps)")
    print("="*70)
    print(f"{'Users':>6} | {'2-GHZ Bal':>11} | {'3-GHZ Bal':>11} | {'4-GHZ Bal':>11} | {'5-GHZ Bal':>11}")
    print("-" * 70)
    for n in user_counts:
        row_str = f"{n:6} |"
        for size in ghz_sizes:
            val = results[size].get(n, 0.0)
            row_str += f"{'N/A':>11} |" if val == 0.0 and n < size else f"{val:11.4f} |"
        print(row_str)
    print("="*70)

if __name__ == '__main__': main()