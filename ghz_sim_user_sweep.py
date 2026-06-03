import numpy as np
import math
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from new_tool import generate_realistic_eta

# --- Constants (from 3ghz_auto_trans.py) ---
MU_OPTIMAL = 0.125   # 平均光子対数
LAMBDA_VAL = MU_OPTIMAL / 2.0 
Y0 = 1e-5            # ダークカウント率
ED = 0.01            # アライメント誤差 1%
E0 = 0.5             # 背景ノイズ
FREQ = 1e9           # 1GHz

# シミュレーション設定
BATCH_SIZE = 1000
NUM_TIMESLOTS = 1000
ARRAY_SIZE = 10**6     # 1スロットあたりのパルス数 (3ghz_auto_trans.pyに合わせ10^6に増加)
X_BASIS_RATIO = 0.1    # パラメータ推定用 (スイープ用に0.1程度に設定)

FIXED_ANGLE = 5.0
GROUP_SIZE = 2 

# Alice (HAP) は理想的なリンクを持つ
ETA_ALICE_FIXED = 1.0 

# --- Helper Functions ---

def P(n, lam):
    """ポアソン分布"""
    if n < 0: return 0.0
    numerator = (n + 1) * (lam ** n)
    denominator = (1 + lam) ** (n + 2)
    return numerator / denominator

def binary_entropy(x):
    """2値エントロピー関数 h(x)"""
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

def calculate_link_qber_ma2007(eta):
    """
    Ma et al. (2007) Eq. A6 に基づき、単一リンクの理論的QBERを計算する。
    """
    total_yield = 0.0
    total_error_prob = 0.0
    
    # ノード側のetaと、HAP内部(eta=1.0)のペアとして計算
    eta_alice = 1.0 
    eta_bob = eta   
    
    for n in range(17):
        prob_n = P(n, LAMBDA_VAL)
        
        # 受信確率 Y_n (Pair)
        term_a = 1 - (1 - Y0) * ((1 - eta_alice) ** n)
        term_b = 1 - (1 - Y0) * ((1 - eta_bob) ** n)
        y_n = term_a * term_b
        
        # エラー率 e_n [Eq. A6]
        if y_n == 0:
            e_n = 0.5
        else:
            denom_diff = eta_bob - eta_alice
            if abs(denom_diff) < 1e-15:
                term_limit = (n + 1) * ((1 - eta_alice) ** n)
            else:
                term_limit = ((1 - eta_alice)**(n + 1) - (1 - eta_bob)**(n + 1)) / denom_diff

            term_bracket = (
                (1 - ((1 - eta_alice)**(n + 1)) * ((1 - eta_bob)**(n + 1))) / 
                (1 - (1 - eta_alice) * (1 - eta_bob)) 
                - term_limit
            )
            # ED (e_pol) はアライメント誤差
            e_n = E0 - (2 * (E0 - ED) / ((n + 1) * y_n)) * term_bracket
        
        q_n = prob_n * y_n
        total_yield += q_n
        total_error_prob += q_n * e_n

    avg_qber = total_error_prob / total_yield if total_yield > 0 else 0.5
    return avg_qber

def calculate_yield_theoretical(etas):
    """
    N者 (HAP + Users) の同時受信確率 (Yield) を計算
    3ghz_auto_trans.py のロジックをN者間に一般化
    """
    total_yield = 0.0
    for n in range(17):
        prob_n = P(n, LAMBDA_VAL)
        
        # 全員が受信する確率
        p_detect_all = 1.0
        for eta in etas:
            p_detect_i = 1 - (1 - Y0) * ((1 - eta) ** n)
            p_detect_all *= p_detect_i
            
        total_yield += prob_n * p_detect_all
        
    return total_yield

def calculate_ghz_skr_epping(raw_rate, Q_Z, N):
    """Epping et al. (2017) Eq. (36) SKR"""
    # 3ghz_auto_trans.py と同じ関数
    if Q_Z >= 0.5: return 0.0
    
    denom = 2**N - 2
    c1 = (2**N - 1) / denom
    c2 = (2**(N-1)) / denom
    
    # N=2 の場合ゼロ除算になる可能性があるため保護 (念のため)
    if denom == 0: 
        # N=2 の場合は通常のBB84に近い形など別の極限だが、
        # Eppingの式36は N>=3 を想定していることが多い。
        # ここでは式通り計算し、発散する場合は0を返すか、N=2用の処理を入れる。
        # 今回はGHZ(3者以上)メインだが、UserSweepでN=2(Total=3)ならOK。
        # User=2(Total=3) -> denom=6. User=1(Total=2) -> denom=2.
        pass

    val_term_lin = (math.log2(2**(N-1) - 1) - c1 * math.log2(2**N - 1)) * Q_Z

    h_q = binary_entropy(Q_Z)
    h_c1q = binary_entropy(c1 * Q_Z)
    h_c2q = binary_entropy(c2 * Q_Z)
    
    r_inf = 1 + h_q - h_c1q - h_c2q + val_term_lin
    if r_inf < 0: r_inf = 0
    
    return raw_rate * r_inf

def create_ghz_circuit(n_qubits, basis='Z'):
    qc = QuantumCircuit(n_qubits)
    qc.h(0) 
    for i in range(1, n_qubits):
        qc.cx(0, i)
    if basis == 'X':
        for i in range(n_qubits):
            qc.h(i)
    qc.measure_all()
    return qc

def run_ghz_batch_simulation(n_users, num_events, qbers, basis='Z'):
    if num_events == 0: return {}
    
    qc = create_ghz_circuit(n_users, basis=basis)
    noise_model = NoiseModel()
    
    for i, qber in enumerate(qbers):
        depol_param = min(1.0, 2.0 * qber)
        error = depolarizing_error(depol_param, 1)
        noise_model.add_quantum_error(error, 'measure', [i])
        
    backend = AerSimulator()
    job = backend.run(qc, noise_model=noise_model, shots=num_events)
    return job.result().get_counts()

# --- Main Simulation ---

def main():
    print(f"--- GHZ-QKD (HAP+Ground Group) TDMA Sweep ---")
    print(f"Logic: Ma et al. (2007) QBER/Yield + Epping et al. (2017) Eq.36 SKR")
    print(f"Condition: User count sweep (2->12), Fixed Angle {FIXED_ANGLE} deg")
    print(f"Config: HAP(Eta=1.0) + Ground Group({GROUP_SIZE})")
    print(f"Array Size: {ARRAY_SIZE} pulses")
    print("-" * 115)
    
    user_counts_list = [ 6, 8, 10]
    
    print(f"{'GndUsers':<8} | {'System SKR (Mb/s)':<18} | {'Avg Q_Z':<8} | {'Avg Q_X':<8} | {'Group SKRs (Mbit/s) ...'}")
    print("-" * 115)

    for num_users in user_counts_list:
        
        # 1. チャネル生成
        angles = [FIXED_ANGLE] * num_users
        eta_matrix = generate_realistic_eta(num_users, NUM_TIMESLOTS, angles)
        
        # グループ定義
        groups = []
        for i in range(0, num_users, GROUP_SIZE):
            groups.append(list(range(i, min(i + GROUP_SIZE, num_users))))
        num_groups = len(groups)
        
        group_stats = {}
        for gid in range(num_groups):
            group_stats[gid] = {
                'total_z_events': 0, 'global_z_errors': 0,
                'total_x_events': 0, 'global_x_errors': 0,
            }
            
        for ts in range(NUM_TIMESLOTS):
            current_gid = ts % num_groups
            current_members = groups[current_gid]
            n_ground = len(current_members)
            n_total = n_ground + 1 # HAP + Ground Users
            
            # 現在の透過率リスト取得 (HAP + 地上)
            current_etas = [ETA_ALICE_FIXED] 
            for uid in current_members:
                current_etas.append(eta_matrix[uid][ts])
            
            # --- 物理モデルに基づく Yield 計算 ---
            current_yield = calculate_yield_theoretical(current_etas)
            
            # イベント数生成
            n_events = np.random.binomial(ARRAY_SIZE, current_yield)
            
            if n_events > 0:
                # --- 物理モデルに基づく QBER 計算 ---
                current_link_qbers = []
                for eta in current_etas:
                    # Ma et al. 2007 モデルで計算
                    q = calculate_link_qber_ma2007(eta)
                    current_link_qbers.append(q)
                
                # Sifting (Z:X 配分)
                n_x = np.random.binomial(n_events, X_BASIS_RATIO)
                n_z = n_events - n_x
                
                # Z基底シミュレーション
                if n_z > 0:
                    batch = min(n_z, BATCH_SIZE)
                    counts = run_ghz_batch_simulation(n_total, batch, current_link_qbers, basis='Z')
                    scale = n_z / batch
                    
                    for out_str, cnt in counts.items():
                        # スペース除去
                        out = out_str.replace(" ", "")
                        # GHZ Z基底エラー: 全員0 or 全員1 以外
                        is_error = (out != '0'*n_total and out != '1'*n_total)
                        
                        group_stats[current_gid]['total_z_events'] += cnt * scale
                        if is_error:
                            group_stats[current_gid]['global_z_errors'] += cnt * scale
                            
                # X基底シミュレーション
                if n_x > 0:
                    batch = min(n_x, BATCH_SIZE)
                    counts = run_ghz_batch_simulation(n_total, batch, current_link_qbers, basis='X')
                    scale = n_x / batch
                    
                    for out_str, cnt in counts.items():
                        out = out_str.replace(" ", "")
                        # GHZ X基底エラー: パリティが奇数
                        parity = out.count('1') % 2
                        is_error = (parity != 0)
                        
                        group_stats[current_gid]['total_x_events'] += cnt * scale
                        if is_error:
                            group_stats[current_gid]['global_x_errors'] += cnt * scale

        # --- 集計とSKR計算 ---
        group_skrs_bps = []
        total_qz_accum = 0.0
        total_qx_accum = 0.0
        active_groups_count = 0
        
        sim_duration = (NUM_TIMESLOTS * ARRAY_SIZE) / FREQ
        
        for gid in range(num_groups):
            st = group_stats[gid]
            n_ground = len(groups[gid])
            n_total = n_ground + 1
            
            if st['total_z_events'] > 0:
                Q_Z = st['global_z_errors'] / st['total_z_events']
                
                if st['total_x_events'] > 0:
                    Q_X = st['global_x_errors'] / st['total_x_events']
                else:
                    Q_X = 0.5
                
                # Raw Rate (bps)
                raw_rate = st['total_z_events'] / sim_duration
                
                # SKR計算 (Epping et al. Eq 36)
                skr_bps = calculate_ghz_skr_epping(raw_rate, Q_Z, n_total)
                
                group_skrs_bps.append(skr_bps)
                total_qz_accum += Q_Z
                total_qx_accum += Q_X
                active_groups_count += 1
            else:
                group_skrs_bps.append(0.0)
        
        # System SKR (1 / sum(1/SKR))
        if len(group_skrs_bps) > 0:
            if any(r <= 1e-12 for r in group_skrs_bps):
                system_skr_bps = 0.0
            else:
                sum_inverse = sum(1.0 / r for r in group_skrs_bps)
                system_skr_bps = 1.0 / sum_inverse
        else:
            system_skr_bps = 0.0
            
        avg_qz = total_qz_accum / active_groups_count if active_groups_count > 0 else 0.0
        avg_qx = total_qx_accum / active_groups_count if active_groups_count > 0 else 0.0
        
        skr_str = " | ".join([f"{val/1e6:.5f}" for val in group_skrs_bps])
        
        print(f"{num_users:<8} | {system_skr_bps/1e6:<18.5f} | {avg_qz:<8.4f} | {avg_qx:<8.4f} | {skr_str}")

    print("-" * 115)
    print("Simulation Complete")

if __name__ == '__main__':
    main()