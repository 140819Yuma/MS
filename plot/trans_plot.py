import matplotlib.pyplot as plt
import numpy as np
np.seterr(over='ignore') # NumPyのオーバーフロー警告を無視

# 新しいチャネルモデルをインポート
from new_tool import generate_realistic_eta

# --- 設定 ---
# 評価する天頂角のリスト
angles = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]

# 平均値を算出するためのサンプル数 (多いほど滑らかになります)
NUM_SAMPLES = 10**6

def main():
    print("Calculating average transmittance for each angle using HAP channel model...")
    
    calculated_transmittance = []
    
    # 各角度についてシミュレーションを実行
    for angle in angles:
        # 1ユーザー分、指定した角度でチャネルデータを生成
        # eta_matrix shape: [user_index][timeslot] -> [0][:]
        eta_matrix = generate_realistic_eta(
            n_users=1, 
            n_timeslots=NUM_SAMPLES, 
            zenith_angle_list=[angle]
        )
        
        # 透過率の平均値を計算
        mean_eta = np.mean(eta_matrix[0])
        
        # パーセント表記に変換して格納
        calculated_transmittance.append(mean_eta * 100)
        
        print(f"Angle: {angle:>4.1f} deg | Transmittance: {mean_eta*100:.4f}%")

    # --- グラフの作成 ---
    plt.figure(figsize=(10, 6)) # グラフのサイズ指定
    
    # プロット
    plt.plot(angles, calculated_transmittance, marker='o', linestyle='-', color='#1f77b4', label='Transmittance')

    # ラベルとタイトルの設定
    plt.xlabel('Zenith Angle (deg)', fontsize=12)
    plt.ylabel('Transmittance (%)', fontsize=12)

    # グリッド（目盛り線）の表示
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 軸の範囲設定
    plt.xlim(min(angles)-2, max(angles)+2)
    plt.ylim(0, max(calculated_transmittance) * 1.1) # 上部に少し余裕を持たせる

    # 凡例の表示
    plt.legend()

    # グラフの表示
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()