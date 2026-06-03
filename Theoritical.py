import numpy as np
import time
import math
import warnings

# 物理モデルツール (new_tool.py からインポート)
from new_tool import HAPDownlinkChannel

np.seterr(over='ignore')
warnings.filterwarnings('ignore')

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
# スイープ用の指定条件
# ==========================================
pz_list = [0.9]                # Z基底を選ぶ確率
w0_list = [0.05, 0.075,0.1, 0.125, 0.15, 0.175, 0.2]                # ビームウェスト
pe_list = [1e-6]               # ポインティングエラー
angle_list = [0,15,30,45,60]               # ゼニスアングル
user_counts = [6]      # ユーザー数
ghz_list = [3]           # N-GHZ状態のサイズ

# ==========================================
# 算出用関数（正しい理論式に更新）
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

def binary_entropy(p):
    if p <= 0 or p >= 1: return 0.0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

def calculate_ghz_skr_new(sifted_rate, Q_Z_max):
    if FIXED_Q_X >= 0.5 or Q_Z_max >= 0.5:
        return 0.0
    r_inf = 1 - binary_entropy(FIXED_Q_X) - binary_entropy(Q_Z_max)
    return sifted_rate * r_inf if r_inf > 0 else 0.0

# ==========================================
# メインシミュレーション
# ==========================================
if __name__ == "__main__":
    print("=========================================================================")
    print(" Start: TDMA Multipartite QKD Theoretical Calculation (Rigorous Mean Eta)")
    print("=========================================================================\n")
    
    for p_z in pz_list:
        for w0 in w0_list:
            for pe in pe_list:
                for angle in angle_list:
                    print(f"=========================================================================")
                    print(f" Parameter Set:")
                    print(f"  P_Z={p_z}, W0={w0}m, PE={pe}rad, ZenithAngle={angle}deg")
                    print(f"=========================================================================\n")
                    
                    for m_users in user_counts:
                        print(f" >>> Total Users (M): {m_users}")
                        
                        for n_ghz in ghz_list:
                            num_groups = math.ceil(m_users / (n_ghz - 1))
                            group_skrs = []
                            
                            # 物理チャネルのインスタンス生成
                            channel = HAPDownlinkChannel(
                                W0=w0, rx_aperture=0.4, obs_ratio=0.3, n_max=6,
                                Cn0=9.6e-14, wind_speed=10, wavelength=1550e-9,
                                ground_station_alt=0.02, aerial_platform_alt=20,
                                zenith_angle=angle, pointing_error=pe, tracking_efficiency=0.8
                            )
                            
                            # 修正箇所: np.cosにはラジアンを渡す
                            slant_range_km = (channel.aerial_platform_alt - channel.ground_station_alt) / np.cos(np.deg2rad(channel.zenith_angle))
                            
                            mean_eta_theoretical = channel._compute_mean_channel_efficiency(eta_ch=None,  length=slant_range_km)
                            
                            # 透過率が正しく計算されなかった場合の安全対策
                            if np.isnan(mean_eta_theoretical) or mean_eta_theoretical <= 0:
                                mean_eta_theoretical = 1e-10

                            for g in range(num_groups):
                                # 修正箇所: アリス(HAP)の透過率は常に 1.0 にする
                                eta_alice_ana = 1.0
                                avg_etas_bobs = [mean_eta_theoretical] * (n_ghz - 1)
                                
                                # Yield と QBER の理論計算
                                y_n_ana = calculate_yield_theoretical([eta_alice_ana] + avg_etas_bobs)
                                
                                if y_n_ana > 0:
                                    # 個別のQBERから最大値を取得する (CKAの理論通り)
                                    max_q_ana = max(calculate_pairwise_qbers(eta_alice_ana, avg_etas_bobs, y_n_ana))
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
                            # 最終評価: System Uniform SKR
                            # -----------------------------------------------------
                            skr_min = min(group_skrs) if group_skrs else 0.0
                            skr_raw_uni = skr_min / num_groups if num_groups > 0 else 0.0
                            t_total = num_groups * (DELTA_T + D_POST + T_ENC + D_PROP)
                            
                            skr_sys_uni = (skr_min * DELTA_T) / t_total if t_total > 0 else 0.0
                            
                            print(f"   * {n_ghz}-GHZ (Groups: {num_groups})")
                            print(f"      1. Raw Uniform SKR : {skr_raw_uni/1e6:8.5f} Mbps")
                            print(f"      2. System Uniform  : {skr_sys_uni/1e6:8.5f} Mbps")
                        print("-" * 65)

    print("\n Theoretical Calculation Completed.")