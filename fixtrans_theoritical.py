import numpy as np
import time
import math
import warnings

np.seterr(over='ignore')
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==========================================
# 定数とQKDパラメータ
# ==========================================
Y0 = 1e-4; ED = 0.033; E0 = 0.5
FREQ = 1e9
FIXED_Q_X = 0.02

# ==========================================
# システムオーバーヘッドのパラメータ
# ==========================================
DELTA_T = 3600.0     # 量子フェーズの時間 (t) [秒]
D_POST  = 2          # 後処理の遅延 (dpost) [秒]
T_ENC   = 0.000002   # 暗号化時間 (tenc) [秒]
D_PROP  = 0.000060   # 伝搬遅延 (dprop) [秒]

# ==========================================
# 今回の指定条件
# ==========================================
pz_list = [0.9]
w0_list = [0.10]
eta_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

user_counts = [6]

# ==========================================
# 算出用関数
# ==========================================
def calculate_yield_theoretical(etas):
    y_N = 1.0
    for eta in etas: 
        y_N *= 1 - (1 - Y0) * (1 - eta)
    return y_N

def calculate_pairwise_qbers(eta_alice, etas_bobs, y_N):
    if y_N <= 0: return [0.5] * len(etas_bobs)
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

# ==========================================
# メインシミュレーション（解析解による理論計算）
# ==========================================
def main():
    print("="*70)
    print(" === Pure Theoretical SKR (Fixed Transmittance without Qiskit) ===")
    print(" === Sweep Parameters: Fixed Transmittance (eta) & Users (M) ===")
    print("="*70)
    print(f"System Overheads: dt={DELTA_T}s, d_post={D_POST}s, t_enc={T_ENC}s, d_prop={D_PROP}s\n")
    
    start_time = time.time()

    for p_z in pz_list:
        print(f"\n######################################################################")
        print(f"### Sweep P_Z = {p_z:.1f} ###")
        print(f"######################################################################")
        
        for w0 in w0_list:
            
            for fixed_eta in eta_list:
                print(f"\n[==================== Fixed Transmittance: {fixed_eta:.1f} ====================]")
                
                for N_USERS in user_counts:
                    print(f"  [********** Number of Users: {N_USERS:2d} **********]")
                    
                    eta_alice = 1.0

                    for n_ghz in [2, 3, 4]:
                        bobs_per_grp = n_ghz - 1
                        num_groups = math.ceil(N_USERS / bobs_per_grp)
                        group_skrs = []
                        
                        for g in range(num_groups):
                            bob_ids = list(range(g * bobs_per_grp, min((g + 1) * bobs_per_grp, N_USERS)))
                            
                            # 全ユーザーに固定の透過率を適用
                            cur_etas_ana = [eta_alice] + [fixed_eta for _ in bob_ids]
                            
                            # 理論YieldとQBERの計算
                            y_n_ana = calculate_yield_theoretical(cur_etas_ana)
                            
                            if y_n_ana > 0:
                                max_q_ana = max(calculate_pairwise_qbers(eta_alice, cur_etas_ana[1:], y_n_ana))
                            else:
                                max_q_ana = 0.5
                            
                            # 基底一致確率 (2-GHZはX基底も考慮、それ以上はZ基底のみ)
                            if n_ghz == 2:
                                prob_sift = (p_z ** 2) + ((1 - p_z) ** 2)
                            else:
                                prob_sift = (p_z ** n_ghz)
                            
                            # 理論的な Raw SKR の算出
                            sifted_rate_ana = y_n_ana * FREQ * prob_sift
                            raw_skr = calculate_ghz_skr_new(sifted_rate_ana, max_q_ana)
                            group_skrs.append(raw_skr)

                        # -----------------------------------------------------
                        # 最終評価
                        # -----------------------------------------------------
                        skr_min = min(group_skrs) if group_skrs else 0.0
                        skr_raw_uni = skr_min / num_groups if num_groups > 0 else 0.0
                        
                        t_total = num_groups * (DELTA_T + D_POST + T_ENC + D_PROP)
                        skr_sys_uni = (skr_min * DELTA_T) / t_total if t_total > 0 else 0.0
                        
                        if any(s <= 0 for s in group_skrs) or not group_skrs:
                            skr_optimal = 0.0
                        else:
                            skr_optimal = 1.0 / sum(1.0 / s for s in group_skrs)
                            
                        print(f"   * {n_ghz}-GHZ (Groups: {num_groups})")
                        print(f"      1. Raw Uniform SKR : {skr_raw_uni/1e6:8.5f} Mbps")
                        print(f"      2. System Uniform  : {skr_sys_uni/1e6:8.5f} Mbps")
                        print(f"      3. Optimal SKR     : {skr_optimal/1e6:8.5f} Mbps")
                    print("-" * 65)

    print(f"\nAnalytical calculation completed in {time.time() - start_time:.4f} seconds.")

if __name__ == '__main__':
    main()