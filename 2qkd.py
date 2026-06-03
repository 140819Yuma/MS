import numpy as np
import math
import warnings
import sys
import os

# --- HAP Channel Model Import ---
# new_tool.py が同じディレクトリにあることを前提とします
from new_tool import generate_realistic_eta


from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- Constants ---
# Physics Parameters (Ma et al. 2007 / SPDC for BBM92)
MU_OPTIMAL = 0.125
LAMBDA_VAL = MU_OPTIMAL / 2.0  # For SPDC
Y0 = 1e-5     
ED = 0.01     
E0 = 0.5      

# Simulation Parameters
FREQ = 1e9             
PULSES_PER_SLOT = 10**6 # 1ms equivalent
BATCH_SIZE = 1000      
ETA_HAP = 1.0          # HAP holds one photon locally
SIFTING_FACTOR = 0.5   # BBM92 (Basis matching probability)

# --- Helper Functions (SPDC for BBM92) ---

def P_spdc(n, lam):
    """SPDC photon number distribution (Thermal-like)"""
    if n < 0: return 0.0
    numerator = (n + 1) * (lam ** n)
    denominator = (1 + lam) ** (n + 2)
    return numerator / denominator

def binary_entropy(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

def calculate_link_qber_ma2007_spdc(eta):
    """
    Ma et al. (2007) model for SPDC source.
    Calculates QBER for a link between HAP (eta=1.0) and User (eta).
    """
    total_yield = 0.0
    total_error_prob = 0.0
    eta_alice = 1.0  # HAP (Local)
    eta_bob = eta    # Ground User
    
    for n in range(17):
        prob_n = P_spdc(n, LAMBDA_VAL)
        
        # Yield formula
        term_a = 1 - (1 - Y0) * ((1 - eta_alice) ** n)
        term_b = 1 - (1 - Y0) * ((1 - eta_bob) ** n)
        y_n = term_a * term_b
        
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
            e_n = E0 - (2 * (E0 - ED) / ((n + 1) * y_n)) * term_bracket
        
        q_n = prob_n * y_n
        total_yield += q_n
        total_error_prob += q_n * e_n

    return total_error_prob / total_yield if total_yield > 0 else 0.5

def calculate_yield_theoretical_spdc(etas):
    """
    Coincidence Yield for N parties using SPDC.
    For BBM92 (N=2): etas = [1.0, eta_user]
    """
    total_yield = 0.0
    for n in range(17):
        prob_n = P_spdc(n, LAMBDA_VAL)
        p_detect_all = 1.0
        for eta in etas:
            p_detect_i = 1 - (1 - Y0) * ((1 - eta) ** n)
            p_detect_all *= p_detect_i
        total_yield += prob_n * p_detect_all
    return total_yield

def calculate_ghz_skr_epping(raw_rate, Q, N):
    """
    Epping et al. (2017) formula.
    Applied exactly as is for N=2 (BBM92).
    """
    if Q >= 0.5: return 0.0
    denom = 2**N - 2
    if denom == 0: return 0.0

    c1 = (2**N - 1) / denom
    c2 = (2**(N-1)) / denom
    
    term1 = math.log2(2**(N-1) - 1)
    term2 = c1 * math.log2(2**N - 1)
    val_term_lin = (term1 - term2) * Q
    
    arg1 = np.clip(Q, 0, 1)
    arg2 = np.clip(c1 * Q, 0, 1)
    arg3 = np.clip(c2 * Q, 0, 1)

    h_q = binary_entropy(arg1)
    h_c1q = binary_entropy(arg2)
    h_c2q = binary_entropy(arg3)
    
    r_inf = 1 + h_q - h_c1q - h_c2q + val_term_lin
    
    if r_inf < 0: r_inf = 0
    return raw_rate * r_inf

# --- Qiskit Simulation ---

def create_bell_pair_circuit():
    # BBM92 uses entangled pairs (e.g., |Phi+>)
    qc = QuantumCircuit(2)
    qc.h(0) 
    qc.cx(0, 1)
    qc.measure_all()
    return qc

def run_simulation_for_errors(num_shots, qbers):
    if num_shots == 0: return 0
    
    qc = create_bell_pair_circuit()
    noise_model = NoiseModel()
    
    # Apply noise to measurements (representing link errors)
    for i, qber in enumerate(qbers):
        depol_param = min(1.0, 2.0 * qber)
        error = depolarizing_error(depol_param, 1)
        noise_model.add_quantum_error(error, 'measure', [i])
        
    backend = AerSimulator()
    job = backend.run(qc, noise_model=noise_model, shots=num_shots)
    counts = job.result().get_counts()
    
    error_count = 0
    for out_str, cnt in counts.items():
        out = out_str.replace(" ", "")
        # For |Phi+>, 00 and 11 are correct.
        if out != "00" and out != "11":
            error_count += cnt
            
    return error_count

# --- Main Logic ---

def main():
    print("==========================================================")
    print("   2QKD (BBM92) Sequential Simulation   ")
    print("==========================================================")
    print(f" - Physics   : SPDC (Ma et al. 2007)")
    print(f" - Protocol  : BBM92 (HAP holds 1 photon, Sends 1)")
    print(f" - Channel   : new_tool.py (HAP Model)")
    print(f" - SKR       : Epping et al. (2017) with N=2")
    print("----------------------------------------------------------")

    try:
        user_input = input("Enter number of users (N): ")
        num_users = int(user_input)
        if num_users < 1:
            print("Error: Need at least 1 user.")
            return
    except ValueError:
        print("Error: Invalid number.")
        return

    angles = []
    print(f"\nEnter Zenith Angle (deg) for each user:")
    for i in range(num_users):
        while True:
            try:
                ang_str = input(f"  User {i} Angle (e.g., 0-60): ")
                ang_val = float(ang_str)
                angles.append(ang_val)
                break
            except ValueError:
                print("  Invalid angle. Please enter a number.")
    
    num_timeslots = 10000
    
    print(f"\nGenerating channel data using HAP model...")
    try:
        # new_tool.py の generate_realistic_eta を使用
        # 引数は (n_users, n_timeslots, zenith_angle_list)
        eta_matrix = generate_realistic_eta(num_users, num_timeslots, zenith_angle_list=angles)
        eta_matrix = np.array(eta_matrix)
    except Exception as e:
        print(f"Error generating eta: {e}")
        return

    user_results = []

    for uid in range(num_users):
        print(f"Processing User {uid} (Angle: {angles[uid]} deg) ...")
        
        total_sifted_bits = 0
        total_error_bits = 0
        
        for ts in range(num_timeslots):
            eta_u = eta_matrix[uid][ts]
            # BBM92: HAP(1.0) + User(eta_u)
            if eta_u <= 0:
                current_etas = [ETA_HAP, 0.0]
            else:
                current_etas = [ETA_HAP, eta_u]
            
            # Calculate Yield using SPDC model
            current_yield = calculate_yield_theoretical_spdc(current_etas)
            
            n_total_detections = np.random.binomial(PULSES_PER_SLOT, current_yield)
            
            if n_total_detections > 0:
                # Sifting (50% for BBM92)
                n_sifted = np.random.binomial(n_total_detections, SIFTING_FACTOR)
                
                if n_sifted > 0:
                    link_qbers = []
                    for eta in current_etas:
                        link_qbers.append(calculate_link_qber_ma2007_spdc(eta))
                    
                    batch_size = min(n_sifted, BATCH_SIZE)
                    errors_in_batch = run_simulation_for_errors(batch_size, link_qbers)
                    
                    estimated_errors = errors_in_batch * (n_sifted / batch_size)
                    
                    total_sifted_bits += n_sifted
                    total_error_bits += estimated_errors

        sim_duration_sec = (num_timeslots * PULSES_PER_SLOT) / FREQ
        
        if total_sifted_bits > 0:
            QBER = total_error_bits / total_sifted_bits
            sifted_rate_bps = total_sifted_bits / sim_duration_sec
            
            skr_bps = calculate_ghz_skr_epping(sifted_rate_bps, QBER, N=2)
        else:
            QBER = 0.5
            skr_bps = 0.0

        user_results.append({
            'user_id': uid,
            'angle': angles[uid],
            'skr': skr_bps,
            'qber': QBER
        })
        
        print(f"   -> SKR: {skr_bps/1e6:.4f} Mbps (QBER: {QBER:.2%})")

    print("\n==========================================================")
    print("   Final Results (BBM92)   ")
    print("==========================================================")
    
    skr_list = [res['skr'] for res in user_results]
    
    if len(skr_list) > 0:
        system_skr = min(skr_list)/num_users
        avg_skr = sum(skr_list) / len(skr_list)
    else:
        system_skr = 0.0
        avg_skr = 0.0

    print(f"{'User ID':<10} | {'Angle (deg)':<15} | {'SKR (Mbps)':<15} | {'QBER':<10}")
    print("-" * 65)
    for res in user_results:
        print(f"{res['user_id']:<10} | {res['angle']:<15.1f} | {res['skr']/1e6:<15.4f} | {res['qber']:.2%}")
    
    print("-" * 65)
    print(f"System SKR (min) : {system_skr/1e6:.4f} Mbps")
    print(f"Average SKR      : {avg_skr/1e6:.4f} Mbps")
    print("==========================================================")

if __name__ == '__main__':
    main()