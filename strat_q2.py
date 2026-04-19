T_max = 5400 
L = 30000     
E_current = 5400000
E_min = 720000    
E_avail = E_current - E_min
P_solar = 250   

P_base = 20        
eff = 0.8             
k = 0.08

def constraint(v, N):
    P_mech = k * (v**3) + P_base
    P_drawn = P_mech / eff
    P_batt = P_drawn - P_solar

    time = (N * L) / v
    E_used = P_batt * time
    return E_used - E_avail

def v_bisect(N,v_low = 1, v_high = 100, tol=1e-5, r=100):
    f_low = constraint(v_low, N)
    f_high = constraint(v_high, N)

    for i in range(r):
        v_mid = (v_low + v_high)/2.0
        f_mid = constraint(v_mid, N)
        
        if abs(f_mid) < tol:
            return v_mid
            
        if f_low * f_mid < 0:
            v_high = v_mid
        else:
            v_low = v_mid
            f_low = f_mid  
            
    return (v_low + v_high) / 2.0

target_v = 0
max_N =1

for N in range(1,100):
    v_min = N*L/T_max
    v_battery_max = v_bisect(N)

    if v_battery_max is None or v_min > v_battery_max:
        continue

    else:
        max_N = N
        target_v = v_min

print("max N :",max_N)
print("targest velocity for this is :",target_v)
