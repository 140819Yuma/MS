import numpy as np
import pandas as pd
from scipy.integrate import quad, quad_vec
from scipy.special import i0e, i1e, erf
import warnings

# 提供された物理モジュールのインポート
import cn2
import smf_coupling as smf
import transmittance as tr_mod

RE = 6371  # 地球半径 [km]
d_p = 0.85

# Zernike インデックスの初期化 (smf_coupling.py に依存)
MAX_N_WFS = 150 
array_of_zernike_index = smf.get_zernikes_index_range(MAX_N_WFS)
lut_zernike_index_pd = pd.DataFrame(array_of_zernike_index[1:], columns=["n", "m", "j"])
lut_zernike_index_pd["j_Noll"] = smf.calculate_j_Noll(lut_zernike_index_pd["n"], lut_zernike_index_pd["m"])

class HAPDownlinkChannel:
    def __init__(self, W0, rx_aperture, obs_ratio, n_max, Cn0, wind_speed, wavelength, 
                 ground_station_alt, aerial_platform_alt, zenith_angle, pointing_error=0, 
                 tracking_efficiency=0, Tatm=None, integral_gain=1, control_delay=13.32e-4, integration_time=6.66e-4):
        
        self.W0 = W0
        self.rx_aperture = rx_aperture
        self.obs_ratio = obs_ratio
        self.n_max = n_max
        self.Cn0 = Cn0
        self.wind_speed = wind_speed
        self.wavelength = wavelength
        self.ground_station_alt = ground_station_alt
        self.aerial_platform_alt = aerial_platform_alt
        self.zenith_angle = zenith_angle
        self.pointing_error = pointing_error
        self.tracking_efficiency = tracking_efficiency
        self.integral_gain = integral_gain
        self.control_delay = control_delay
        self.integration_time = integration_time
        
        # 大気透過率の決定 (transmittance.py の slant 関数を使用)
        if Tatm is None:
            # wavelength は nm 単位で渡す必要があるため 1e9 倍
            self.Tatm = tr_mod.slant(self.ground_station_alt, self.aerial_platform_alt, 
                                     self.wavelength * 1e9, self.zenith_angle)
        else:
            self.Tatm = Tatm

    def _compute_Cn2(self, h):
        return cn2.hufnagel_valley(h, self.wind_speed, self.Cn0)
    
    def sec(self, theta):
        return 1/np.cos(np.deg2rad(theta))

    def _compute_rytov_variance_spherical(self):
        gs_alt_m = self.ground_station_alt * 1e3
        ap_alt_m = self.aerial_platform_alt * 1e3
        k = 2 * np.pi / self.wavelength
        integrand = lambda h : self._compute_Cn2(h) * (h - gs_alt_m)**(5/6) * \
                               ((ap_alt_m - h) / (ap_alt_m - gs_alt_m))**(5/6)
        val, _ = quad(integrand, gs_alt_m, ap_alt_m)
        return 2.25 * k**(7/6) * self.sec(self.zenith_angle)**(11/6) * val
    
    def _compute_channel_length(self):
        zenith_rad = np.deg2rad(self.zenith_angle)
        RA = RE + self.aerial_platform_alt
        RG = RE + self.ground_station_alt
        return np.sqrt(RA**2 + RG**2 * (np.cos(zenith_rad)**2 - 1)) - RG * np.cos(zenith_rad)

    def _compute_coherence_width_gaussian(self, length_km):
        gs_alt_m = self.ground_station_alt * 1e3
        ap_alt_m = self.aerial_platform_alt * 1e3
        k = 2 * np.pi / self.wavelength
        z = length_km * 1e3
        
        Lambda_0 = 2 * z / (k * self.W0**2)
        Lambda = Lambda_0 / (1 + Lambda_0**2)
        Theta = 1 / (1 + Lambda_0**2)
        Theta_bar = 1 - Theta
        
        integrand_1 = lambda h : self._compute_Cn2(h) * \
                                 (Theta + Theta_bar * (ap_alt_m - h) / (ap_alt_m - gs_alt_m))**(5/3)
        mu_1d, _ = quad(integrand_1, gs_alt_m, ap_alt_m)
        
        integrand_2 = lambda h : self._compute_Cn2(h) * \
                                 ((h - gs_alt_m) / (ap_alt_m - gs_alt_m))**(5/3)
        mu_2d, _ = quad(integrand_2, gs_alt_m, ap_alt_m)
        
        return (np.cos(np.deg2rad(self.zenith_angle)) / \
               (0.423 * k**2 * (mu_1d + 0.622 * mu_2d * Lambda**(11/6))))**(3/5)

    def _compute_wandering_variance(self):
        gs_alt_m = self.ground_station_alt * 1e3
        ap_alt_m = self.aerial_platform_alt * 1e3
        k = 2 * np.pi / self.wavelength
        length = self._compute_channel_length() * 1e3
        
        Lambda_0 = 2 * length / (k * self.W0**2)
        Theta_0 = 1
        rytov_var = self._compute_rytov_variance_spherical()
        
        f = lambda h: (Theta_0 + (1 - Theta_0) * (h - gs_alt_m) / (ap_alt_m - gs_alt_m))**2 + \
                      1.63 * (rytov_var)**(6/5) * Lambda_0 * \
                      ((ap_alt_m - h) / (ap_alt_m - gs_alt_m))**(16/5)
        
        integrand = lambda h: self._compute_Cn2(h) * (h - gs_alt_m)**2 / f(h)**(1/6)
        val, _ = quad(integrand, gs_alt_m, ap_alt_m)
        
        return 7.25 * self.sec(self.zenith_angle)**3 * self.W0**(-1/3) * val

    def _compute_scintillation_index_spherical(self, rytov_var, length_m):
        k = 2 * np.pi / self.wavelength
        d = np.sqrt(k * self.rx_aperture**2 / (4 * length_m))
        beta_0_sq = 0.4065 * rytov_var
        first_term = 0.49 * beta_0_sq / (1 + 0.65 * d**2 + 1.11 * beta_0_sq**(6/5))**(7/6)
        second_term = 0.51 * beta_0_sq * (1 + 0.69 * beta_0_sq**(6/5))**(-5/6) / \
                      (1 + 0.9 * d**2 + 0.62 * d**2 * beta_0_sq**(6/5))
        return np.exp(first_term + second_term) - 1

    def _compute_pdt_parameters(self, length_km):
        z = length_km * 1e3
        rx_radius = self.rx_aperture / 2
        pointing_var = (self.pointing_error * z)**2
        rytov_var = self._compute_rytov_variance_spherical()
        scint_index = self._compute_scintillation_index_spherical(rytov_var, z)
        
        W_LT = self.W0 * np.sqrt(1 + (self.wavelength * z / (np.pi * self.W0**2))**2 + \
                                 1.63 * rytov_var**(6/5) * 2 * z / (k := 2*np.pi/self.wavelength * self.W0**2))
        
        wandering_var = (self._compute_wandering_variance() + pointing_var) * (1 - self.tracking_efficiency)
        W_ST = np.sqrt(np.maximum(W_LT**2 - wandering_var, 1e-9))

        X = (rx_radius / W_ST)**2
        T0 = np.sqrt(1 - np.exp(-2 * X))
        
        # Weibull パラメータ計算
        l = 8 * X * i1e(4*X) / (i0e(0) - i0e(4*X)) / np.log(2*T0**2 / (1e-10 + 1 - i0e(4*X))) # 簡易化
        R = rx_radius * np.abs(np.log(2*T0**2 / (1e-10 + 1 - i0e(4*X))))**(-1./l)

        def lognormal_params(r):
            eta_mean = T0 * np.exp(-(r/R)**l)
            eta_var = (1 + scint_index) * eta_mean**2
            mu = -np.log(eta_mean**2 / np.sqrt(eta_var))
            sigma = np.sqrt(np.log(eta_var / eta_mean**2))
            return mu, sigma

        return lognormal_params, wandering_var, W_LT

    def _compute_pdt(self, eta, length_km):
        log_params, wand_var, W_LT = self._compute_pdt_parameters(length_km)
        pdt = np.zeros_like(eta)
        for i, e in enumerate(eta):
            if e <= 0 or e > 1: continue
            integrand = lambda r: r * (np.exp(-(np.log(e) + log_params(r)[0])**2 / (2 * log_params(r)[1]**2)) / \
                                  (e * log_params(r)[1] * np.sqrt(2 * np.pi))) * \
                                  np.exp(-r**2 / (2 * wand_var)) / wand_var
            val, _ = quad(integrand, 0, self.rx_aperture/2 + W_LT)
            pdt[i] = val
        return pdt

    def _compute_attenuation_factors(self):
        n = np.array(lut_zernike_index_pd["n"].values)
        n_corrected = n[n <= self.n_max]
        # AO 伝達関数
        e_err = lambda v: 1 / (1 + self.integral_gain * np.exp(-self.control_delay * v) * \
                              (1 - np.exp(-self.integration_time * v)) / (self.integration_time * v)**2)
        gamma_j = np.ones_like(n, dtype=float)
        for i in range(len(n_corrected)):
            cutoff = 0.3 * (n_corrected[i] + 1) * self.wind_speed / self.rx_aperture
            psd = lambda v: v**(-2/3) if v <= cutoff else v**(-17/3)
            num, _ = quad(lambda v: e_err(v)**2 * psd(v), 1e-2, 1000)
            den, _ = quad(psd, 1e-2, 1000)
            gamma_j[i] = num / den if den != 0 else 1
        return gamma_j

    def sample_transmittance(self, n_samples):
        length_km = self._compute_channel_length()
        eta_grid = np.linspace(1e-4, 1, 500)
        
        # PDT サンプリング
        pdt_dist = self._compute_pdt(eta_grid, length_km)
        # 負の値を 0 に置換し、数値的な安定性を確保
        pdt_dist = np.maximum(pdt_dist, 0)
        pdt_sum = np.sum(pdt_dist)
        if pdt_sum > 0:
            pdt_dist /= pdt_sum
        else:
            # 万が一透過率が 0 の場合は、最小値に確率を割り当てる
            pdt_dist[0] = 1.0
            
        pdt_s = np.random.choice(eta_grid, n_samples, p=pdt_dist)
        
        # SMF サンプリング
        r0 = self._compute_coherence_width_gaussian(length_km)
        n = np.array(lut_zernike_index_pd["n"].values)
        bj2 = smf.bn2(self.rx_aperture, r0, n, self.obs_ratio) * self._compute_attenuation_factors()
        
        rytov = self._compute_rytov_variance_spherical()
        si = self._compute_scintillation_index_spherical(rytov, length_km * 1e3)
        eta_max = smf.eta_s(si) * smf.eta_0(self.obs_ratio, smf.beta_opt(self.obs_ratio))
        
        smf_pdf = smf.compute_eta_smf_probability_distribution(eta_grid, eta_max, bj2)
        
        # ここが修正ポイント：負の値を排除し、正規化を厳密に行う
        smf_pdf = np.nan_to_num(smf_pdf) # NaN を 0 に置換
        smf_pdf = np.maximum(smf_pdf, 0)  # 負の値を 0 に置換
        smf_sum = np.sum(smf_pdf)
        
        if smf_sum > 0:
            smf_pdf /= smf_sum
        else:
            smf_pdf[0] = 1.0
            
        smf_s = np.random.choice(eta_grid, n_samples, p=smf_pdf)
        
        # 大気透過率（LOWTRANによる算出値）を乗じて最終結果を出す
        return self.Tatm * pdt_s * smf_s * d_p
    
    def _compute_mean_channel_efficiency(self, eta_ch, length, detector_efficiency = 1):
        """Compute mean channel efficiency, including losses at the detector.

        ## Parameters
        `eta_ch` : np.ndarray
            Input random variable values to calculate pdf for.
        `length` : float 
            Length of the channel [km].
        `detector_efficiency` : float
            Efficiency of detector at receiver (default 1).
        ## Returns
        `ch_pdf` : np.ndarray
            Channel PDF for input eta.
        """
        eta_ch = np.arange(1e-7, 1, 0.001)
        pdt = self._compute_pdt(eta_ch, length)
        pdt = pdt/np.sum(pdt)
        
        z = length*1e3
        n = np.array(lut_zernike_index_pd["n"].values)
        j_Noll_as_index = np.array(lut_zernike_index_pd["j_Noll"].values) - 2

        rytov_var = self._compute_rytov_variance_spherical()

        #Check of the condition for aperture averaging
        if rytov_var <1:
                check = np.sqrt(self.wavelength*length*1e3)
        else:
                check = 0.36*np.sqrt(self.wavelength*length*1e3)* (rytov_var**(-3/5))
        if self.rx_aperture < check:
            print("Warning ! The aperture averaging hypothesis is not valid for this set of parameters. Use bigger values of receiving aperture size")

        scint_index = self._compute_scintillation_index_spherical(rytov_var, z)
        r0 = self._compute_coherence_width_gaussian(z)
        eta_s = np.exp(-np.log(1 + scint_index))
        bj2 = smf.bn2(self.rx_aperture, r0, n,self.obs_ratio)

        gamma_j = self._compute_attenuation_factors()
        bj2 = bj2*gamma_j

        # Check if we are below the Rayleigh criterion
        bj_wvln = np.sqrt(bj2)/(2*np.pi)
        bj_wlvn_max = np.max(bj_wvln)
        if bj_wlvn_max > 0.05:
            print(f" Warning ! The maximum Zernike coefficient std in wavelenghts is {bj_wlvn_max}. The SMF PDF is accurate below the Rayleigh criterion (0.05). You may need to use higher order of correction or smaller integration time of the AO system.")

        beta_opt = smf.beta_opt(self.obs_ratio)
        eta_smf_max = smf.eta_0(self.obs_ratio, beta_opt)

        mean_transmittance = np.sum(eta_ch*pdt)*self.Tatm*eta_s*eta_smf_max*detector_efficiency *smf.eta_ao(bj2)
        return mean_transmittance * d_p
    
def generate_realistic_eta(n_users, n_timeslots, zenith_angle_list=None):
    # パラメータ設定 (HAPDownlinkChannel の __init__ に渡す値)
    params = {
        "W0": 0.10,            # ビームウエスト 10cm
        "rx_aperture": 0.9,    # 受信口径 40cm
        "obs_ratio": 0.1,   # 遮蔽率
        "n_max": 10,            # AO 補正次数
        "Cn0": 1e-15,        # 地表の Cn2 基準値
        "wind_speed": 10,      # 風速 10m/s
        "wavelength": 1550e-9, # 波長
        "ground_station_alt": 0.02, # 地上局高度 (km)
        "aerial_platform_alt": 20,  # 気球高度 (km)gf
        "pointing_error": 1e-6,     # ポインティング誤差
        "tracking_efficiency": 0.99  # トラッキング効率
    }
    
    eta_matrix = []
    # 天頂角のリストが指定されていない場合は、全員 0 度（真上）とする
    if zenith_angle_list is None: 
        zenith_angle_list = [0] * n_users
    
    for i in range(n_users):
        angle = zenith_angle_list[i]
        # チャネルインスタンスの作成
        channel = HAPDownlinkChannel(zenith_angle=angle, Tatm=0.9, **params)
        # 瞬時透過率のサンプリングを実行
        samples = channel.sample_transmittance(n_timeslots)
        eta_matrix.append(samples)
        
    return eta_matrix


