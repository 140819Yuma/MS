import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# 自作モジュール (new_tool.py) がある前提
from new_tool import generate_realistic_eta


warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- Constants ---
MU_OPTIMAL = 0.125
LAMBDA_VAL = MU_OPTIMAL / 2.0
Y0 = 1e-5
ED = 0.01
E0 = 0.5

FREQ = 1e9
PULSES_PER_SLOT = 10**6 
BATCH_SIZE = 1000      
X_BASIS_RATIO = 0.1    
GROUP_SIZE = 2         
ETA_HAP = 1.0          

# --- Helper Functions (SPDC) ---

def P_spdc(n, lam):
    if n < 0: return 0.0
    numerator = (n + 1) * (lam ** n)
    denominator = (1 + lam) ** (n + 2)
    return numerator / denominator

def binary_entropy(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

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
        
        if y_n == 0:
            e_n = 0.5
        else:
            denom_diff = eta_bob - eta_alice
            if abs(denom_diff) < 1e-15:
                term_limit = (n + 1) * ((1 - eta_alice) ** n)
            else:
                term_limit = ((1 - eta_alice)**(n + 1) - (1 - eta_bob)**(n + 1)) / denom_diff
            
            term_bracket = ((1 - ((1 - eta_alice)**(n + 1)) * ((1 - eta_bob)**(n + 1))) / 
                            (1 - (1 - eta_alice) * (1 - eta_bob)) - term_limit)
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

    h_q = binary_entropy(arg1)
    h_c1q = binary_entropy(arg2)
    h_c2q = binary_entropy(arg3)
    
    r_inf = 1 + h_q - h_c1q - h_c2q + val_term_lin
    if r_inf < 0: r_inf = 0
    return raw_rate * r_inf

# --- Qiskit Simulation ---

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

# --- Main Logic ---

def main():
    print("==========================================================")
    print("   GHZ-QKD Grouped Simulation (Double Loop Structure)   ")
    print("==========================================================")
    print(f" - Pulse Rate: {FREQ/1e9} GHz")
    print(f" - Time Slot : 1 ms ({PULSES_PER_SLOT} pulses)")
    print(f" - Metric    : System SKR = min(Group_SKRs)")
    print("----------------------------------------------------------")

    # 1. User Input (Number of Users)
    try:
        user_input = input("Enter number of users (N): ")
        num_users = int(user_input)
        if num_users < 2:
            print("Error: Need at least 2 users.")
            return
    except ValueError:
        print("Error: Invalid number.")
        return

    # 2. Angle Input (Per User)
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
    
    # Simulation settings
    num_timeslots = 10000 
    
    # 3. Grouping
    groups = []
    for i in range(0, num_users, GROUP_SIZE):
        members = list(range(i, min(i + GROUP_SIZE, num_users)))
        if len(members) == GROUP_SIZE:
            groups.append(members)
        else:
            print(f"Warning: Users {members} excluded (Need pair).")
    
    num_groups = len(groups)
    print(f"\nConfiguration:")
    print(f" - Total Users: {num_users}")
    print(f" - Angles     : {angles}")
    print(f" - Groups     : {num_groups} (Size: {GROUP_SIZE} users/group)")
    print("----------------------------------------------------------")
    
    # Generate Environment Data
    # Pass the specific angles list to the generator
    eta_matrix = generate_realistic_eta(num_users, num_timeslots, angles)

    group_results = []

    # === Outer Loop: Groups ===
    for g_idx, members in enumerate(groups):
        print(f"Processing Group {g_idx+1}/{num_groups}: Users {members} ...")
        
        grp_z_events = 0
        grp_z_errors = 0
        grp_x_events = 0
        grp_x_errors = 0
        
        n_total_qubits = len(members) + 1  # HAP + Group
        
        # === Inner Loop: Time Slots ===
        for ts in range(num_timeslots):
            current_etas = [ETA_HAP]
            for uid in members:
                current_etas.append(eta_matrix[uid][ts])
            
            current_yield = calculate_yield_theoretical_spdc(current_etas)
            n_events_in_slot = np.random.binomial(PULSES_PER_SLOT, current_yield)
            
            if n_events_in_slot > 0:
                link_qbers = []
                for eta in current_etas:
                    link_qbers.append(calculate_link_qber_ma2007_spdc(eta))
                
                n_x = np.random.binomial(n_events_in_slot, X_BASIS_RATIO)
                n_z = n_events_in_slot - n_x
                
                if n_z > 0:
                    batch = min(n_z, BATCH_SIZE) 
                    counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='Z')
                    scale = n_z / batch
                    for out_str, cnt in counts.items():
                        out = out_str.replace(" ", "")
                        all_zeros = '0' * n_total_qubits
                        all_ones  = '1' * n_total_qubits
                        
                        grp_z_events += cnt * scale
                        if out != all_zeros and out != all_ones:
                            grp_z_errors += cnt * scale

                if n_x > 0:
                    batch = min(n_x, BATCH_SIZE)
                    counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='X')
                    scale = n_x / batch
                    for out_str, cnt in counts.items():
                        out = out_str.replace(" ", "")
                        parity = out.count('1') % 2
                        grp_x_events += cnt * scale
                        if parity != 0: 
                            grp_x_errors += cnt * scale

        # === End of Inner Loop ===
        
        sim_duration_sec = (num_timeslots * PULSES_PER_SLOT) / FREQ
        
        if grp_z_events > 0:
            Q_Z = grp_z_errors / grp_z_events
            if grp_x_events > 0:
                Q_X = grp_x_errors / grp_x_events
            else:
                Q_X = 0.5
            
            raw_rate_bps = grp_z_events / sim_duration_sec
            skr_bps = calculate_ghz_skr_epping(raw_rate_bps, Q_Z, n_total_qubits)
        else:
            Q_Z = 0.5; Q_X = 0.5; skr_bps = 0.0

        group_results.append({
            'group_id': g_idx,
            'members': members,
            'skr': skr_bps,
            'qz': Q_Z,
            'qx': Q_X
        })
        
        print(f"   -> SKR: {skr_bps/1e6:.4f} Mbps (Qz: {Q_Z:.2%}, Qx: {Q_X:.2%})")

    # === Evaluation ===
    print("\n==========================================================")
    print("   Final Results   ")
    print("==========================================================")
    
    skr_list = [res['skr'] for res in group_results]
    
    if len(skr_list) > 0:
        system_skr = min(skr_list)/num_groups
        avg_skr = sum(skr_list) / len(skr_list)
    else:
        system_skr = 0.0
        avg_skr = 0.0

    print(f"{'Group':<10} | {'Users (Angles)':<25} | {'SKR (Mbps)':<15}")
    print("-" * 60)
    for res in group_results:
        mems = res['members']
        # メンバーの角度を表示用に取得
        ang_str = f"{[angles[m] for m in mems]}"
        u_str = f"{mems} {ang_str}"
        s_val = res['skr'] / 1e6
        print(f"{res['group_id']:<10} | {u_str:<25} | {s_val:<15.4f}")
    
    print("-" * 60)
    print(f"System SKR (min) : {system_skr/1e6:.4f} Mbps")
    print(f"Average SKR      : {avg_skr/1e6:.4f} Mbps")
    print("==========================================================")

if __name__ == '__main__':
    main()