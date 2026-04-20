import pandas as pd
import math
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar, brentq

car_mass = 300       
gravity = 9.81             
air_density = 1.225        
drag_coeff = 0.15          
frontal_area = 1.5
rolling_resistance = 0.005 
motor_efficiency = 0.8     
max_battery_joules = 5400000 


panel_area = 4.0
panel_efficiency = 0.2
max_accel = 1.5  # m/s² — max acceleration/deceleration for the solar car

def calculate_distance(lat1, lon1, lat2, lon2):
    # standard haversine formula to get distance between two points
    radius = 6371000 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(math.radians(lon2 -lon1)/2)**2
    return radius*(2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def get_solar_power(time_in_seconds):
    #gaussian curve for sun intensity throughout the day
    peak_intensity = 1073.0
    noon = 43200.0
    width = 11600.0
    irradiance = peak_intensity * math.exp(-((time_in_seconds - noon)**2) / (2 * width**2))
    return irradiance * panel_area * panel_efficiency

def drive_base_route(base_speed_ms, csv_file="route_data.csv", record_telemetry=False):
    route_data = pd.read_csv(csv_file)
    current_time = 28800.0    # Starts at 8:00 AM
    current_battery = max_battery_joules    
    
    telemetry = []
    
    # Road Limits
    min_legal_speed = 30.0 / 3.6  # 30 km/h in m/s
    max_legal_speed = 100.0 / 3.6 # 100 km/h in m/s

    prev_speed = base_speed_ms  # for acceleration constraint

    for i in range(1, len(route_data)):
        lat1, lon1 = route_data.loc[i-1, 'Latitude'], route_data.loc[i-1, 'Longitude']
        lat2, lon2 = route_data.loc[i, 'Latitude'], route_data.loc[i, 'Longitude']
        hill_slope = route_data.loc[i, 'Slope']
        
        dist = calculate_distance(lat1, lon1, lat2, lon2)
        if dist <= 0: continue

        # We adjust the speed based on the steepness of the hill.
        # 'slope_factor' dictates how aggressively we slow down for hills.
        # A factor of 100 means a 5% grade (0.05) slows us down by 5 m/s (18 km/h).
        slope_factor = 100.0 
        dynamic_speed_ms = base_speed_ms - (hill_slope * slope_factor)
        
        # Clamp the speed to legal road limits
        dynamic_speed_ms = max(min_legal_speed, min(dynamic_speed_ms, max_legal_speed))
        # Acceleration constraint: speed can only change by max_accel * dt from previous segment
        dt_est = dist / prev_speed if prev_speed > 0 else 1.0
        max_delta_v = max_accel * dt_est
        dynamic_speed_ms = max(prev_speed - max_delta_v, min(prev_speed + max_delta_v, dynamic_speed_ms))
        prev_speed = dynamic_speed_ms
        # ------------------------------------
        
        time_spent = dist / dynamic_speed_ms
        
        #calculate forces
        force_aero = 0.5 * air_density * drag_coeff * frontal_area * (dynamic_speed_ms**2)
        force_rolling = rolling_resistance * car_mass * gravity
        force_gravity = car_mass * gravity * hill_slope 
        total_force = force_aero + force_rolling + force_gravity
        
        #Power drawn with regen braking if going downhill
        if total_force < 0:
            power_used = (total_force * dynamic_speed_ms) * 0.60 
        else:
            power_used = (total_force * dynamic_speed_ms) / motor_efficiency
            
        power_used += 20.0 #other power usage
        net_power = get_solar_power(current_time) - power_used
        
        current_battery += (net_power * time_spent)
        current_time += time_spent
        current_battery = min(current_battery, max_battery_joules)
        
        if record_telemetry: 
            telemetry.append((current_time, dynamic_speed_ms, current_battery))
        
        if current_battery <= survival_limit:
            return None, None, []
            
    return current_time, current_battery, telemetry

max_battery_joules = 5400000 
survival_limit = max_battery_joules * 0.20
deadline_time = 61200
loop_distance = 35000

def simulate_n_loops(v, N, start_time, start_energy, record_telemetry=False):
    current_time = start_time
    current_energy = start_energy
    
    if N == 0:
        return current_energy, []
        
    force_aero = 0.5*air_density*drag_coeff*frontal_area*(v**2)
    force_rolling = rolling_resistance*car_mass*gravity
    power_used = ((force_aero +force_rolling) * v)/motor_efficiency + 20.0
    
    time_per_loop = loop_distance/v
    telemetry = []
    
    for i in range(N):
        #drive the loop
        for second in range(int(time_per_loop)):
            current_time += 1
            current_energy += get_solar_power(current_time) - power_used
            
            if record_telemetry and second % 10 == 0:
                telemetry.append((current_time, v, current_energy))
                
            if current_energy < survival_limit:
                return -1, telemetry
                
        if current_time > deadline_time:
            return -1, telemetry
            
        # mandatory 5 minute stop between loops
        if i < N - 1:
            for second in range(300):
                current_time += 1
                current_energy += get_solar_power(current_time)
                current_energy = min(current_energy, max_battery_joules)
                if record_telemetry and second % 10 == 0:
                    telemetry.append((current_time, 0, current_energy)) 
                
    return current_energy, telemetry

def find_optimal_vn(N, start_time, start_energy, v_low=10.0, v_high=100.0, tol=0.1):
    min_time_required = (N*(loop_distance/v_high)) + ((N - 1) * 300)
    if start_time + min_time_required > deadline_time:
        return None
        
    for i in range(100): 
        v_mid = (v_low + v_high) / 2
        final_energy, i = simulate_n_loops(v_mid, N, start_time, start_energy)
        
        if final_energy == -1: #ran out of time or dead
            v_high = v_mid 
        else:
            if final_energy-survival_limit < tol:
                return v_mid
            v_low = v_mid
            
    return (v_low + v_high)/2

def run_master_strategy():
    print("Simulating thousands of race possibilities...")

    def evaluate_base_speed(test_kmh):
        base_ms = test_kmh / 3.6
        arr_time, arr_ener, _ = drive_base_route(base_ms)
        if arr_time is None or arr_time > deadline_time:
            return 0  # invalid — contributes nothing

        curr_t = arr_time
        curr_e = arr_ener
        for sec in range(1800):
            curr_t += 1
            curr_e = min(curr_e + get_solar_power(curr_t), max_battery_joules)

        loops = 0
        best_v = 0
        for n in range(1, 20):
            opt_v = find_optimal_vn(n, curr_t, curr_e)
            if opt_v is not None:
                loops = n
                best_v = opt_v
            else:
                break

        return 220000.0 + (loops * loop_distance)

    # minimize_scalar minimizes, so we negate the distance to maximise it
    result = minimize_scalar(
        lambda v: -evaluate_base_speed(v),
        bounds=(20, 100),
        method='bounded',
        options={'xatol': 0.5}   # 0.5 km/h tolerance
    )
    win_base_speed = result.x

    # Re-run at the optimal speed to recover loop count and loop speed
    base_ms = win_base_speed / 3.6
    arr_time, arr_ener, _ = drive_base_route(base_ms)
    curr_t = arr_time
    curr_e = arr_ener
    for sec in range(1800):
        curr_t += 1
        curr_e = min(curr_e + get_solar_power(curr_t), max_battery_joules)

    win_loop_count = 0
    win_loop_speed = 0
    for n in range(1, 20):
        opt_v = find_optimal_vn(n, curr_t, curr_e)
        if opt_v is not None:
            win_loop_count = n
            win_loop_speed = opt_v * 3.6
        else:
            break

    best_distance = 220000.0 + (win_loop_count * loop_distance)
    print("Total Distance:", best_distance / 1000, "km")
    print("Base Speed:", round(win_base_speed, 2), "km/h")
    print("Loops Completed:", win_loop_count)
    print("Loop Speed:", round(win_loop_speed, 2), "km/h")

    return win_base_speed, win_loop_count, win_loop_speed

base_v, loop_c, loop_v = run_master_strategy()
arr_t, arr_e, base_telem = drive_base_route(base_v / 3.6, record_telemetry=True)

stop_telem = []
curr_t = arr_t
curr_e = arr_e
for sec in range(1800):
    curr_t += 1
    curr_e = min(curr_e + get_solar_power(curr_t), max_battery_joules)
    if sec % 10 == 0: stop_telem.append((curr_t, 0, curr_e))

Energy, loop_telem = simulate_n_loops(loop_v / 3.6, loop_c, curr_t, curr_e, record_telemetry=True)

full_telem = base_telem + stop_telem + loop_telem
df = pd.DataFrame(full_telem, columns=['Time', 'Velocity_ms', 'Energy'])
df['Time_Hours'] = df['Time'] / 3600
df['Velocity_kmh'] = df['Velocity_ms'] * 3.6
df['SOC'] = (df['Energy'] / max_battery_joules) * 100


#velocity
plt.figure(figsize=(10,5))
plt.plot(df['Time_Hours'], df['Velocity_kmh'], color='blue')
plt.title('velocity')
plt.xlabel('time')
plt.ylabel('speed (km/h)')
plt.grid()
plt.savefig('velocity_profile.png')

#soc
plt.figure(figsize=(10,5))
plt.plot(df['Time_Hours'], df['SOC'], color='green')
plt.title('soc')
plt.xlabel('time')
plt.ylabel('soc %')
plt.savefig('soc_profile.png')

df["acc"] = df['Velocity_ms'].diff() / df['Time'].diff()  # m/s²

#acc
plt.figure(figsize=(10,5))
plt.plot(df.iloc[1:]['Time_Hours'], df['acc'].iloc[1:], color='red')
plt.title('acc')
plt.xlabel('time')
plt.ylabel('acc (m/s²)')
plt.tight_layout()
plt.savefig('acc_profile.png')