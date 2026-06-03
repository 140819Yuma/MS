import matplotlib.pyplot as plt
import numpy as np
import sys

# 必要なクラスをnew_toolからインポート
try:
    from new_tool import HAPDownlinkChannel
except ImportError:
    print("Error: new_tool.py not found.")
    sys.exit(1)

# --- パラメータ設定 (new_tool.pyのgenerate_realistic_etaと同じ設定) ---
PARAMS = {
    "W0": 0.10,            # 送信ビームウェスト [m]
    "rx_aperture": 0.4,    # 受信開口径 [m]
    "obs_ratio": 0.4195,   # 副鏡による遮蔽率
    "n_max": 6,            # 補償光学(AO)の次数
    "Cn0": 9.6e-14,        # 地上の乱流強度
    "wind_speed": 10,      # 風速 [m/s]
    "wavelength": 1550e-9, # 波長 [m]
    "ground_station_alt": 0.02, # 地上局高度 [km]
    "aerial_platform_alt": 20,  # HAP高度 [km]
    "pointing_error": 1e-6,     # ポインティング誤差 [rad]
    "Tatm": None,               # 大気透過率 (Noneなら自動計算)
    "tracking_efficiency": 0.0  # トラッキング効率パラメータ
}

# --- シミュレーション設定 ---
# 評価する天頂角のリスト
ANGLES = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]
# 平均化のサンプル数
NUM_SAMPLES = 10**5 

def get_channel_components(angle, n_samples):
    """
    指定された角度における、各要因ごとの平均透過率/効率を計算して返す
    """
    # チャネルクラスのインスタンス化
    channel = HAPDownlinkChannel(zenith_angle=angle, **PARAMS)
    
    # 内部メソッドを使って分布などを計算 (new_tool.pyのロジックを再現)
    length_km = channel._compute_channel_length()
    eta_grid = np.linspace(1e-4, 1, 500)
    
    # 1. Pointing & Tracking (PDT) 要因
    # ビームワンダリングやポインティング誤差による幾何学的ロス
    pdt_dist = channel._compute_pdt(eta_grid, length_km)
    pdt_dist = np.abs(pdt_dist)
    if np.sum(pdt_dist) > 0:
        pdt_dist /= np.sum(pdt_dist)
    else:
        return 0.0, 0.0, 0.0, 0.0
        
    # 2. SMF Coupling (Turbulence/AO) 要因
    # 大気乱流による波面歪みとファイバー結合ロス
    smf_pdf = channel._compute_smf_coupling_pdf(eta_grid, 1.0, length_km)
    smf_pdf = np.abs(smf_pdf)
    if np.sum(smf_pdf) > 0:
        smf_pdf /= np.sum(smf_pdf)
    else:
        return 0.0, 0.0, 0.0, 0.0
    
    # ランダムサンプリング (独立事象として生成)
    pdt_samples = np.random.choice(eta_grid, n_samples, p=pdt_dist)
    smf_samples = np.random.choice(eta_grid, n_samples, p=smf_pdf)
    
    # 3. Atmospheric Transmittance (Atm) 要因
    # 距離と大気による吸収 (定数または角度依存の固定値)
    atm_val = channel.Tatm
    
    # 全体 (Total) = Atm * PDT * SMF
    total_samples = atm_val * pdt_samples * smf_samples
    
    # それぞれの平均値を返す
    return np.mean(total_samples), atm_val, np.mean(pdt_samples), np.mean(smf_samples)

def main():
    print("Calculating breakdown of transmittance factors...")
    
    results = {
        'total': [],
        'atm': [],
        'pdt': [],
        'smf': []
    }
    
    for angle in ANGLES:
        print(f"Processing Angle: {angle:>4.1f} deg ... ", end="")
        avg_total, avg_atm, avg_pdt, avg_smf = get_channel_components(angle, NUM_SAMPLES)
        
        results['total'].append(avg_total)
        results['atm'].append(avg_atm)
        results['pdt'].append(avg_pdt)
        results['smf'].append(avg_smf)
        
        print(f"Total: {avg_total*100:.2f}% (Atm: {avg_atm*100:.2f}%, PDT: {avg_pdt*100:.2f}%, SMF: {avg_smf*100:.2f}%)")

    # --- グラフ描画 (2x2 のサブプロット) ---
    print("\nGenerating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"HAP Downlink Channel Transmittance Breakdown", fontsize=16)
    
    # 共通の設定関数
    def setup_ax(ax, title, data, color, marker):
        ax.plot(ANGLES, np.array(data) * 100, marker=marker, linestyle='-', color=color, linewidth=2)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylabel("Efficiency / Transmittance (%)")
        ax.set_xlabel("Zenith Angle (deg)")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_ylim(bottom=0) # 0からスタート

    # 1. Total (全体)
    setup_ax(axes[0, 0], "1. Total System Transmittance (Combined)", results['total'], 'black', 'o')

    # 2. Atmospheric (大気)
    setup_ax(axes[0, 1], "2. Atmospheric Transmission (Loss due to Air)", results['atm'], 'blue', 's')

    # 3. Pointing (幾何学ロス)
    setup_ax(axes[1, 0], "3. Pointing & Tracking Efficiency (Geometric)", results['pdt'], 'green', '^')

    # 4. SMF Coupling (結合ロス)
    setup_ax(axes[1, 1], "4. SMF Coupling Efficiency (Turbulence & AO)", results['smf'], 'red', 'd')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # タイトル分のスペースを空ける
    
    # 保存と表示
    save_name = "transmittance_factors_breakdown.png"
    plt.savefig(save_name)
    print(f"Plot saved as '{save_name}'")
    plt.show()

if __name__ == "__main__":
    main()