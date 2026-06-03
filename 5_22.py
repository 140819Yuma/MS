import numpy as np
import warnings

# 物理モデルツール (new_tool.py からインポート)
from new_tool import HAPDownlinkChannel

np.seterr(over='ignore')
warnings.filterwarnings('ignore')

def main():
    # ==========================================
    # 2-4ghz_sim_probability.py から抽出した最新設定
    # ==========================================
    W0 = 0.1
    PE = 1e-6
    NUM_TIMESLOTS = 500
    angle_list = [0, 15, 30, 45, 60] 

    params = {
        "W0": W0,           
        "pointing_error": PE,  
        "Cn0": 9.6e-14,                
        "rx_aperture": 0.4,    
        "obs_ratio": 0.3,   
        "n_max": 6,            
        "wind_speed": 10,      
        "wavelength": 1550e-9, 
        "ground_station_alt": 0.02, 
        "aerial_platform_alt": 20,   
        "tracking_efficiency": 0.8  
    }

    print("=========================================================")
    print(" HAP Downlink Channel Transmittance (Eta) Test")
    print("=========================================================")
    print(f" Parameters:")
    print(f"  Cn0 = {params['Cn0']}")
    print(f"  Rx Aperture = {params['rx_aperture']} m")
    print(f"  Obs Ratio = {params['obs_ratio']}")
    print(f"  n_max = {params['n_max']}")
    print(f"  Tracking Efficiency = {params['tracking_efficiency']}")
    print("=========================================================\n")

    for angle in angle_list:
        print(f"[ Zenith Angle: {angle} deg ]")
        
        # 1. チャネルインスタンスの作成 (Tatm は指定せず内部算出に任せる)
        channel = HAPDownlinkChannel(zenith_angle=angle, **params)
        
        # 2. 理論的な厳密平均透過率の算出 (Theoritical.py で使用している式)
        slant_range_km = (channel.aerial_platform_alt - channel.ground_station_alt) / np.cos(np.deg2rad(channel.zenith_angle))
        mean_eta_theoretical = channel._compute_mean_channel_efficiency(eta_ch=None, length=slant_range_km)
        
        # 3. シミュレーション用の瞬時透過率のサンプリング
        samples = channel.sample_transmittance(NUM_TIMESLOTS)
        
        # 結果の出力
        print(f"  - Theoretical Mean Eta : {mean_eta_theoretical:.6e}")
        print(f"  - Sampled Mean Eta     : {np.mean(samples):.6e}")
        print(f"  - Sampled Max Eta      : {np.max(samples):.6e}")
        print(f"  - Sampled Min Eta      : {np.min(samples):.6e}")
        print("-" * 57)

if __name__ == '__main__':
    main()