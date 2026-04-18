import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

class pid:
    def __init__(self, kp, ki, kd, sp):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.sp = sp
        self.integral_sum = 0
        self.previous_error = 0

    def compute(self,current_x, dt):
        error = self.sp - current_x
        self.integral_sum += error * dt

        P = self.kp*error
        I = self.ki*self.integral_sum
        D = self.kd*(error - self.previous_error)/dt

        self.previous_error = error

        control_u = P+I+D

        return control_u

M = 1.0
m = 0.1
l = 0.5 
g = 9.81 

def cartpole(t, state, F):
    # Unpack the State Variables (x)
    x, x_dot, theta, theta_dot = state
    
    sin_t = np.sin(theta)
    cos_t = np.cos(theta)
    
    # Calculate angular acceleration and cart acceleration
    theta_ddot = (g * sin_t + cos_t * ((-F - m * l * theta_dot**2 * sin_t) / (M + m))) / \
                 (l * (4.0/3.0 - (m * cos_t**2) / (M + m)))
    x_ddot = (F + m * l * (theta_dot**2 * sin_t - theta_ddot * cos_t)) / (M + m)
    
    return [x_dot, x_ddot, theta_dot, theta_ddot]

dt = 0.01
t = 10
steps =  int(t/dt)

current_state = np.array([0.0,0.0, 0.1, 0.0])
mypid = pid(1,20,10,0)

time = []
theta_history = []
x_history = []

for step in range(steps):
    t_current = step*dt
    theta = current_state[2]
    x = current_state[0]

    if(abs(theta)>24):
        break
    if(abs(x)>10):
        break

    time.append(t_current)
    theta_history.append(theta)
    x_history.append(x)

    force_u = -mypid.compute(theta, dt)
    force_u = np.clip(force_u, -20.0, 20.0)

    t_span = (t_current, t_current + dt)
    solution = solve_ivp(cartpole, t_span, current_state,args=(force_u,))
    
    current_state = solution.y[:,-1]

plt.figure(figsize=(10,6))

plt.plot(time,x_history,label = "position", color = "red")
plt.plot(time, theta_history,label = "angle", color = "blue")

plt.xlabel("time")
plt.legend()
plt.tight_layout()
plt.show()