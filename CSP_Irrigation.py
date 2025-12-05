import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from itertools import combinations
import time

# IMPORT DATA
def load_data():
    plots = pd.read_csv("plots.csv")
    pumps = pd.read_csv("pump_settings.csv")
    first_col_val = str(pumps.iloc[0]['max_hours_per_day'])

    if ',' in first_col_val and ';' in first_col_val:
        clean_val = first_col_val.replace('"', '').replace("'", "")
        parts = clean_val.split(',', 1)
        max_hours = int(parts[0])
        raw_slots = parts[1]
    else:
        max_hours = int(pumps.iloc[0]['max_hours_per_day'])
        raw_slots = pumps.iloc[0]['time_slots']

    slot_list = []
    parts = [s.strip() for s in str(raw_slots).replace('"','').split(';') if '-' in s]

    for s in parts:
        start, end = map(int, s.split('-'))
        slot_list.append({
            'label': s,
            'start': start,
            'end': end,
            'dur': end - start
        })

    return plots, slot_list, max_hours

def generate_domains(plots, slots):
    domains = {}
    for _, row in plots.iterrows():
        pid = row['plot_id']
        need = int(row['water_need_hours'])
        possible_moves = []

        for r in range(1, len(slots) + 1):
            for combo in combinations(slots, r):
                total_dur = sum(s['dur'] for s in combo)
                if total_dur == need:
                    possible_moves.append(combo)

        if not possible_moves:
            for r in range(1, len(slots) + 1):
                for combo in combinations(slots, r):
                    total_dur = sum(s['dur'] for s in combo)
                    if total_dur >= need:
                        possible_moves.append(combo)

        possible_moves.sort(key=lambda c: (min(s['start'] for s in c), sum(s['dur'] for s in c)))
        domains[pid] = possible_moves
    return domains

# CSP
def check_conflict(val_a, prio_a, val_b, prio_b):
    slots_a = set(s['label'] for s in val_a)
    slots_b = set(s['label'] for s in val_b)

    if not slots_a.isdisjoint(slots_b):
        return True

    start_a = min(s['start'] for s in val_a)
    end_a = max(s['end'] for s in val_a)
    start_b = min(s['start'] for s in val_b)
    end_b = max(s['end'] for s in val_b)

    if prio_a < prio_b:
        if end_a > start_b: return True

    if prio_b < prio_a:
        if end_b > start_a: return True

    return False

def is_valid_assignment(assignment, new_var, new_val, plots_data):
    new_prio = plots_data[new_var]['priority_score']

    for assigned_var, assigned_val in assignment.items():
        existing_prio = plots_data[assigned_var]['priority_score']
        if check_conflict(new_val, new_prio, assigned_val, existing_prio):
            return False

    return True

# AC-3
def revise(xi, xj, domains, plots_data):
    revised = False
    prio_i = plots_data[xi]['priority_score']
    prio_j = plots_data[xj]['priority_score']

    for x_val in domains[xi][:]:
        is_consistent = False
        for y_val in domains[xj]:
            if not check_conflict(x_val, prio_i, y_val, prio_j):
                is_consistent = True
                break

        if not is_consistent:
            domains[xi].remove(x_val)
            revised = True

    return revised

def ac3(domains, plots_data):
    queue = [(xi, xj) for xi in domains for xj in domains if xi != xj]

    while queue:
        (xi, xj) = queue.pop(0)

        if revise(xi, xj, domains, plots_data):
            if not domains[xi]: return False

            for xk in domains:
                if xk != xi and xk != xj:
                    queue.append((xk, xi))
    return True

# HEURISTICS
def count_degree(var, unassigned_vars, plots_data):
    neighbors = [v for v in unassigned_vars if v != var]
    return len(neighbors)

def select_unassigned_variable(assignment, domains, plots_data):
    unassigned = [v for v in plots_data if v not in assignment]

    unassigned.sort(key=lambda v: (
        plots_data[v]['priority_score'],
        -plots_data[v]['need'],
        len(domains[v]),
        -count_degree(v, unassigned, plots_data)
    ))

    return unassigned[0]

# BACKTRACKING SOLVER
def solve_csp(assignment, domains, plots_data, max_hours):
    if len(assignment) == len(plots_data):
        return assignment

    var = select_unassigned_variable(assignment, domains, plots_data)

    for value in domains[var]:
        if is_valid_assignment(assignment, var, value, plots_data):

            current_total_need = sum(plots_data[p]['need'] for p in assignment) + plots_data[var]['need']
            if current_total_need > max_hours:
                continue

            local_domains = {k: v[:] for k, v in domains.items()}
            possible = True

            unassigned_neighbors = [v for v in plots_data if v not in assignment and v != var]
            prio_var = plots_data[var]['priority_score']

            for neighbor in unassigned_neighbors:
                prio_neighbor = plots_data[neighbor]['priority_score']

                valid_neighbor_vals = [
                    val for val in local_domains[neighbor]
                    if not check_conflict(value, prio_var, val, prio_neighbor)
                ]

                if not valid_neighbor_vals:
                    possible = False
                    break
                local_domains[neighbor] = valid_neighbor_vals

            if not possible:
                continue

            assignment[var] = value
            result = solve_csp(assignment, local_domains, plots_data, max_hours)
            if result:
                return result

            del assignment[var]

    return None

# VISUALISASI
def visualize(solution, plots_data):
    if not solution: return

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = {'high': '#ff6b6b', 'medium': '#feca57', 'low': '#48dbfb'}

    y_pos = 0
    y_ticks = []
    y_labels = []

    sorted_plots = sorted(solution.keys(), key=lambda k: min(s['start'] for s in solution[k]))

    for pid in sorted_plots:
        slots = solution[pid]
        prio = plots_data[pid]['original_prio']

        for s in slots:
            ax.barh(y_pos, s['dur'], left=s['start'], height=0.6,
                    color=colors.get(prio, 'gray'), edgecolor='black')
            ax.text(s['start'] + s['dur']/2, y_pos, f"{s['start']}-{s['end']}",
                    ha='center', va='center', color='black', fontsize=9, fontweight='bold')

        y_ticks.append(y_pos)
        y_labels.append(f"{pid} ({prio.title()})")
        y_pos += 1

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Waktu (Jam)")
    ax.set_title("Visualisasi Jadwal Irigasi")
    ax.set_xlim(6, 24)
    ax.set_xticks(range(6, 25))
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    patches = [mpatches.Patch(color=c, label=p.title()) for p, c in colors.items()]
    plt.legend(handles=patches, loc='upper right')
    plt.tight_layout()
    plt.show()

# MAIN
def main():
    start_time = time.time()
    try:
        plots_df, slots, max_hours = load_data()
    except Exception as e:
        print(f"Error Loading Data: {e}")
        return

    prio_map = {'high': 0, 'medium': 1, 'low': 2}
    plots_data = {}
    for _, row in plots_df.iterrows():
        p_str = row['priority'].strip().lower()
        plots_data[row['plot_id']] = {
            'need': int(row['water_need_hours']),
            'priority_score': prio_map.get(p_str, 3),
            'original_prio': p_str
        }

    domains = generate_domains(plots_df, slots)

    if ac3(domains, plots_data):
        pass
    else:
        print("   -> AC-3: Tidak ada solusi yang mungkin.")
        return

    solution = solve_csp({}, domains, plots_data, max_hours)

    end_time = time.time()

    if solution:
        print("\nJADWAL IRIGASI DITEMUKAN")
        sorted_sol = sorted(solution.items(), key=lambda item: min(s['start'] for s in item[1]))

        total_durasi = 0
        for pid, val in sorted_sol:
            times = " & ".join([s['label'] for s in val])
            print(f"Plot {pid} ({plots_data[pid]['original_prio']}) -> {times}")
            total_durasi += plots_data[pid]['need']

        print(f"\nTotal Waktu Pompa: {total_durasi} Jam / {max_hours} Jam")
        print(f"Waktu Komputasi: {end_time - start_time:.4f} detik")

        visualize(solution, plots_data)
    else:
        print("Maaf, tidak ditemukan jadwal yang memenuhi semua kriteria.")

if __name__ == "__main__":
    main()
