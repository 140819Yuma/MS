import numpy as np
import math
import warnings
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

try:
    from new_tool import generate_realistic_eta
except ImportError:
    print("Error: new_tool.py not found.")
    import sys; sys.exit(1)

warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- Configuration ---
NUM_USERS = 15
ZENITH_ANGLES = np.linspace(0, 60, NUM_USERS).tolist()

# --- Constants (Same as above) ---
MU_OPTIMAL = 0.125; LAMBDA_VAL = MU_OPTIMAL / 2.0; Y0 = 1e-5; ED = 0.01; E0 = 0.5
FREQ = 1e9; PULSES_PER_SLOT = 10**6; BATCH_SIZE = 1000; X_BASIS_RATIO = 0.5

# --- Helper Functions (Same) ---
def P_spdc(n, lam): return ((n + 1) * (lam ** n)) / ((1 + lam) ** (n + 2))
def calculate_link_qber_ma2007_spdc(eta):
    total_yield = 0.0; total_error_prob = 0.0; eta_alice = 1.0; eta_bob = eta
    for n in range(17): 
        prob_n = P_spdc(n, LAMBDA_VAL)
        term_a = 1 - (1 - Y0) * ((1 - eta_alice) ** n)
        term_b = 1 - (1 - Y0) * ((1 - eta_bob) ** n)
        y_n = term_a * term_b
        if y_n == 0: e_n = 0.5
        else:
            denom_diff = eta_bob - eta_alice
            if abs(denom_diff) < 1e-15: term_limit = (n + 1) * ((1 - eta_alice) ** n)
            else: term_limit = ((1 - eta_alice)**(n + 1) - (1 - eta_bob)**(n + 1)) / denom_diff
            term_bracket = ((1 - ((1 - eta_alice)**(n + 1)) * ((1 - eta_bob)**(n + 1))) / (1 - (1 - eta_alice) * (1 - eta_bob)) - term_limit)
            e_n = E0 - (2 * (E0 - ED) / ((n + 1) * y_n)) * term_bracket
        q_n = prob_n * y_n; total_yield += q_n; total_error_prob += q_n * e_n
    return total_error_prob / total_yield if total_yield > 0 else 0.5
def calculate_yield_theoretical_spdc(etas):
    total_yield = 0.0
    for n in range(17):
        prob_n = P_spdc(n, LAMBDA_VAL)
        p_detect_all = 1.0
        for eta in etas: p_detect_i = 1 - (1 - Y0) * ((1 - eta) ** n); p_detect_all *= p_detect_i
        total_yield += prob_n * p_detect_all
    return total_yield
def binary_entropy(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)
def calculate_ghz_skr_epping(raw_rate, Q_Z, N):
    if Q_Z >= 0.5: return 0.0
    denom = 2**N - 2; 
    if denom == 0: return 0.0
    c1 = (2**N - 1) / denom; c2 = (2**(N-1)) / denom
    val_term_lin = (math.log2(2**(N-1) - 1) - c1 * math.log2(2**N - 1)) * Q_Z
    arg1 = np.clip(Q_Z, 0, 1); arg2 = np.clip(c1 * Q_Z, 0, 1); arg3 = np.clip(c2 * Q_Z, 0, 1)
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

# --- Topology Logic: Star (Leader) ---
def create_star_groups(n_users):
    groups = []
    leader = 0 # 常にUser 0がリーダー
    # 残りのメンバー (1, ..., N-1) を2人ずつペアにする
    others = list(range(1, n_users))
    
    for i in range(0, len(others), 2):
        chunk = others[i: min(i+2, len(others))]
        if len(chunk) < 2:
            # 端数が出たら、他のメンバー(例えば最後のペアの片割れ)を借りる
             needed = 2 - len(chunk)
             extras = [k for k in others if k not in chunk]
             if len(extras) >= needed:
                 chunk.extend(extras[-needed:])
        
        # Leader + 2 Members
        members = [leader] + chunk
        groups.append(sorted(members))
    return groups

def main():
    print("=== Star (Leader) Topology Simulation ===")
    
    if len(ZENITH_ANGLES) < NUM_USERS:
        angles = ZENITH_ANGLES + [0]*(NUM_USERS - len(ZENITH_ANGLES))
    else:
        angles = ZENITH_ANGLES[:NUM_USERS]
        
    groups = create_star_groups(NUM_USERS)
    print(f"Users: {NUM_USERS}, Groups: {len(groups)}")
    for i, g in enumerate(groups):
        print(f"  Group {i}: {g} (Leader: {g[0]})")
    
    num_timeslots = 1000 
    eta_matrix = generate_realistic_eta(NUM_USERS, num_timeslots, angles)
    
    group_skrs = []
    
    for g_idx, members in enumerate(groups):
        grp_z_events = 0; grp_z_errors = 0; grp_x_events = 0; grp_x_errors = 0
        n_total_qubits = len(members)
        
        for ts in range(num_timeslots):
            current_etas = [eta_matrix[uid][ts] for uid in members]
            current_yield = calculate_yield_theoretical_spdc(current_etas)
            n_events = np.random.binomial(PULSES_PER_SLOT, current_yield)
            
            if n_events > 0:
                link_qbers = [calculate_link_qber_ma2007_spdc(e) for e in current_etas]
                n_x = np.random.binomial(n_events, X_BASIS_RATIO)
                n_z = n_events - n_x
                if n_z > 0:
                    batch = min(n_z, BATCH_SIZE)
                    counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='Z')
                    scale = n_z / batch
                    for out, cnt in counts.items():
                        if out.replace(" ","") not in ['0'*n_total_qubits, '1'*n_total_qubits]: grp_z_errors += cnt * scale
                        grp_z_events += cnt * scale
                if n_x > 0:
                    batch = min(n_x, BATCH_SIZE)
                    counts = run_ghz_batch_simulation(n_total_qubits, batch, link_qbers, basis='X')
                    scale = n_x / batch
                    for out, cnt in counts.items():
                        if out.replace(" ","").count('1') % 2 != 0: grp_x_errors += cnt * scale
                        grp_x_events += cnt * scale

        sim_duration = (num_timeslots * PULSES_PER_SLOT) / FREQ
        if grp_z_events > 0:
            Q_Z = grp_z_errors / grp_z_events
            raw_rate = grp_z_events / sim_duration
            skr = calculate_ghz_skr_epping(raw_rate, Q_Z, n_total_qubits)
        else: skr = 0.0
        
        group_skrs.append(skr)
        print(f"  Group {g_idx} SKR: {skr/1e6:.4f} Mbps")

    # システム全体レート
    # リーダーが各グループと順番に鍵を作っていく
    min_skr = min(group_skrs) if group_skrs else 0.0
    final_rate = min_skr / len(groups)
    
    print("-" * 40)
    print(f"System Throughput (Star): {final_rate/1e6:.4f} Mbps")
    print(f"(Limited by min link {min_skr/1e6:.4f} Mbps / {len(groups)} slots)")

if __name__ == '__main__':
    main()