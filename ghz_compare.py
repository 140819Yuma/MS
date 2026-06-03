import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# --- Constants ---
MU_OPTIMAL = 0.125
LAMBDA_VAL = MU_OPTIMAL / 2.0
Y0 = 1e-5
ED = 0.01
E0 = 0.5
FREQ = 1e9
PULSES_PER_SLOT = 10**6
BATCH_SIZE = 1000
X_BASIS_RATIO = 0.5

# --- Helper Functions ---
def P_spdc(n, lam):
    return ((n + 1) * (lam ** n)) / ((1 + lam) ** (n + 2))

def calculate_link_qber_ma2007_spdc(eta):
    total_yield = 0.0
    total_error_prob = 0.0
    eta_alice = 1.0
    eta_bob = eta
    for n in range(17): 
        prob_n = P_spdc(n, LAMBDA_VAL)
        term_a = 1 - (1 - Y0) * ((1 - eta_alice) ** n)
        term_b = 1 - (1 - Y0) * ((1 - eta_bob) ** n)
        y_n = term_a * term_b
        if y_n == 0: e_n = 0.5
        else:
            denom_diff = eta_bob - eta_alice
            if abs(denom_diff) < 1e-15:
                term_limit = (n + 1) * ((1 - eta_alice) ** n)
            else:
                term_limit = ((1 - eta_alice)**(n + 1) - (1 - eta_bob)**(n + 1)) / denom_diff
            term_bracket = ((1 - ((1 - eta_alice)**(n + 1)) * ((1 - eta_bob)**(n + 1))) / (1 - (1 - eta_alice) * (1 - eta_bob)) - term_limit)
            e_n = E0 - (2 * (E0 - ED) / ((n + 1) * y_n)) * term_bracket
        q_n = prob_n * y_n
        total_yield += q_n
        total_error_prob += q_n * e_n
    return total_error_prob / total_yield if total_yield > 0 else 0.5

def calculate_yield_theoretical_spdc(etas):
    total_yield = 0.0
    for n in range(17):
        prob_n = P_spdc(n, LAMBDA_VAL)
        p_detect_all = 1.0
        for eta in etas:
            p_detect_i = 1 - (1 - Y0) * ((1 - eta) ** n)
            p_detect_all *= p_detect_i
        total_yield += prob_n * p_detect_all
    return total_yield

def binary_entropy(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

def calculate_ghz_skr_epping(raw_rate, Q_Z, N):
    if Q_Z >= 0.5: return 0.0
    denom = 2**N - 2
    if denom == 0: return 0.0
    c1 = (2**N - 1) / denom
    c2 = (2**(N-1)) / denom
    val_term_lin = (math.log2(2**(N-1) - 1) - c1 * math.log2(2**N - 1)) * Q_Z
    arg1 = np.clip(Q_Z, 0, 1)
    arg2 = np.clip(c1 * Q_Z, 0, 1)
    arg3 = np.clip(c2 * Q_Z, 0, 1)
    r_inf = 1 + binary_entropy(arg1) - binary_entropy(arg2) - binary_entropy(arg3) + val_term_lin
    if r_inf < 0: r_inf = 0
    return raw_rate * r_inf

# --- Qiskit Simulation ---
def create_ghz_circuit(n_qubits, basis='Z'):
    qc = QuantumCircuit(n_qubits)
    qc.h(0) 
    for i in range(1, n_qubits): qc.cx(0, i)
    if basis == 'X':
        for i in range(n_qubits): qc.h(i)
    qc.measure_all()
    return qc

def run_ghz_batch_simulation(n_qubits, num_shots, qbers, basis='Z'):
    if num_shots == 0: return {}
    qc = create_ghz_circuit(n_qubits, basis=basis)
    noise_model = NoiseModel()
    for i, qber in enumerate(qbers):
        depol_param = min(1.0, 2.0 * qber)
        error = depolarizing_error(depol_param, 1)
        noise_model.add_quantum_error(error, 'measure', [i])
    backend = AerSimulator()
    job = backend.run(qc, noise_model=noise_model, shots=num_shots)
    return job.result().get_counts()

# --- Mock Eta Generator (if new_tool is missing) ---
def generate_mock_eta(n_users, n_slots, angles):
    # 簡易モデル: 角度に応じた距離減衰 + ログ正規フェージング
    H = 20.0 # HAP高度 (km)
    attenuation_coeff = 0.5 # dB/km (晴天時想定)
    sigma = 0.5 # フェージング強度
    
    eta_matrix = []
    for angle_deg in angles:
        angle_rad = np.radians(angle_deg)
        distance = H / np.cos(angle_rad)
        loss_db = attenuation_coeff * distance
        mean_eta = 10 ** (-loss_db / 10.0)
        
        # Log-normal fading
        mu_log = np.log(mean_eta) - (sigma**2)/2
        etas = np.random.lognormal(mu_log, sigma, n_slots)
        etas = np.clip(etas, 0.0, 1.0)
        eta_matrix.append(etas)
    return eta_matrix

# --- Grouping Strategies ---
def create_groups_sequential(n_users):
    """Old Strategy: Sequential Pairing with Leader"""
    groups = []
    leader = 0
    others = list(range(1, n_users))
    for i in range(0, len(others), 2):
        chunk = others[i: min(i+2, len(others))]
        if len(chunk) < 2:
             needed = 2 - len(chunk)
             extras = [k for k in others if k not in chunk]
             if len(extras) >= needed:
                 chunk.extend(extras[-needed:])
        members = [leader] + chunk
        groups.append(sorted(members))
    return groups

def create_groups_high_low(n_users, angles):
    """New Strategy: High-Low Mixing"""
    groups = []
    leader = 0
    others = []
    for i in range(1, n_users):
        others.append((i, angles[i]))
    others.sort(key=lambda x: x[1]) # 角度(条件)でソート
    
    while len(others) > 0:
        if len(others) >= 2:
            best = others.pop(0)  
            worst = others.pop(-1) 
            members = [leader, best[0], worst[0]]
            groups.append(sorted(members))
        else:
            last_one = others.pop(0)
            candidates = [(i, angles[i]) for i in range(1, n_users) if i != last_one[0]]
            candidates.sort(key=lambda x: x[1])
            best_partner = candidates[0]
            members = [leader, last_one[0], best_partner[0]]
            groups.append(sorted(members))
    return groups

# --- Main Comparison Logic ---
def run_comparison():
    # 3人から15人まで2人刻みでループ
    num_users_list = range(3, 16, 2) 
    results_old = []
    results_new = []
    
    print(f"{'Users':<6} | {'Old SKR (Mbps)':<15} | {'New SKR (Mbps)':<15}")
    print("-" * 45)
    
    for n_users in num_users_list:
        # 角度生成: 0から60度までを人数分で等分割
        angles = np.linspace(0, 60, n_users).tolist()
        
        # 大気透過率生成 (簡易版を使用)
        num_timeslots = 1000
        eta_matrix = generate_mock_eta(n_users, num_timeslots, angles)
        
        # --- OLD STRATEGY (Sequential, Trusted HAP) ---
        groups_old = create_groups_sequential(n_users)
        group_skrs_old = []
        for members in groups_old:
            # ghz_oldmulti.pyのロジック: n_total_qubits = len(members) + 1 (HAP含む)
            n_total_qubits = len(members) + 1
            grp_z_events = 0; grp_z_errors = 0; grp_x_events = 0; grp_x_errors = 0
            
            for ts in range(num_timeslots):
                current_etas = [eta_matrix[uid][ts] for uid in members]
                current_yield = calculate_yield_theoretical_spdc(current_etas)
                n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
                
                if n_events > 0:
                    link_qbers = [calculate_link_qber_ma2007_spdc(e) for e in current_etas]
                    # ノイズ付加: HAP(最後のqubit)にはノイズを乗せない仕様
                    
                    n_x = np.random.binomial(n_events, X_BASIS_RATIO)
                    n_z = n_events - n_x
                    
                    if n_z > 0:
                        batch = min(n_z, BATCH_SIZE)
                        counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='Z')
                        scale = n_z / batch
                        for out, cnt in counts.items():
                            if out.replace(" ","") not in ['0'*n_total_qubits, '1'*n_total_qubits]:
                                grp_z_errors += cnt * scale
                            grp_z_events += cnt * scale
                            
                    if n_x > 0:
                        batch = min(n_x, BATCH_SIZE)
                        counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='X')
                        scale = n_x / batch
                        for out, cnt in counts.items():
                            if out.replace(" ","").count('1') % 2 != 0:
                                grp_x_errors += cnt * scale
                            grp_x_events += cnt * scale

            sim_duration = (num_timeslots * PULSES_PER_SLOT) / FREQ
            if grp_z_events > 0:
                Q_Z = grp_z_errors / grp_z_events
                raw_rate = grp_z_events / sim_duration
                skr = calculate_ghz_skr_epping(raw_rate, Q_Z, n_total_qubits)
            else: skr = 0.0
            group_skrs_old.append(skr)
            
        sys_skr_old = min(group_skrs_old) / len(groups_old) if groups_old else 0.0
        results_old.append(sys_skr_old)
        
        # --- NEW STRATEGY (High-Low, Untrusted HAP) ---
        groups_new = create_groups_high_low(n_users, angles)
        group_skrs_new = []
        for members in groups_new:
            # ghz_multi.pyのロジック: n_total_qubits = len(members) (HAP含まない)
            n_total_qubits = len(members)
            grp_z_events = 0; grp_z_errors = 0; grp_x_events = 0; grp_x_errors = 0
            
            for ts in range(num_timeslots):
                current_etas = [eta_matrix[uid][ts] for uid in members]
                current_yield = calculate_yield_theoretical_spdc(current_etas)
                n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
                
                if n_events > 0:
                    link_qbers = [calculate_link_qber_ma2007_spdc(e) for e in current_etas]
                    # ノイズ付加: 全員にノイズが乗る
                    
                    n_x = np.random.binomial(n_events, X_BASIS_RATIO)
                    n_z = n_events - n_x
                    
                    if n_z > 0:
                        batch = min(n_z, BATCH_SIZE)
                        counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='Z')
                        scale = n_z / batch
                        for out, cnt in counts.items():
                            if out.replace(" ","") not in ['0'*n_total_qubits, '1'*n_total_qubits]:
                                grp_z_errors += cnt * scale
                            grp_z_events += cnt * scale
                            
                    if n_x > 0:
                        batch = min(n_x, BATCH_SIZE)
                        counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='X')
                        scale = n_x / batch
                        for out, cnt in counts.items():
                            if out.replace(" ","").count('1') % 2 != 0:
                                grp_x_errors += cnt * scale
                            grp_x_events += cnt * scale

            sim_duration = (num_timeslots * PULSES_PER_SLOT) / FREQ
            if grp_z_events > 0:
                Q_Z = grp_z_errors / grp_z_events
                raw_rate = grp_z_events / sim_duration
                skr = calculate_ghz_skr_epping(raw_rate, Q_Z, n_total_qubits)
            else: skr = 0.0
            group_skrs_new.append(skr)
            
        sys_skr_new = min(group_skrs_new) / len(groups_new) if groups_new else 0.0
        results_new.append(sys_skr_new)
        
        print(f"{n_users:<6} | {sys_skr_old/1e6:.4f}          | {sys_skr_new/1e6:.4f}")

if __name__ == "__main__":
    run_comparison()