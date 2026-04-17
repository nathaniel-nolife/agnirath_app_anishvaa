import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def smoothen_series(x):
    sum_6 = x[:6]
    avg = sum(sum_6)/6
    smoothened_series = [np.nan] * 5
    smoothened_series.append(avg)

    for i in range(len(x)-6):
        avg = avg + (x[6+i]-x[i])/(6)
        smoothened_series.append(avg)

    return smoothened_series
    
data = pd.read_csv("telemetry_A.csv")

#used these commands initally to get an idea of the data
#print(data)
#print(data.info())

#setting the faulty calues to nan, i did this by looking at the data and finding the outliers based on this
data.loc[(data["velocity_ms"] < 7) | (data["velocity_ms"] > 23), "velocity_ms"] = np.nan
data.loc[(data["Gradient_deg"] < -1 )| (data["Gradient_deg"] > 1), "Gradient_deg"] = np.nan

data[["velocity_ms", "Gradient_deg"]] = data[["velocity_ms", "Gradient_deg"]].interpolate()

#to smoothen the data as said by the hint i will use a rolling average
data["velocity_ms"] = smoothen_series(data["velocity_ms"])
data["Gradient_deg"] = smoothen_series(data["Gradient_deg"])

data = data.iloc[5:]#removing the rows with Nan

#values of m and Ar i took are random idk the values
m = 500
g = 9.8
rho = 1.22
Ar = 1

data["acc"] = data["velocity_ms"].diff()
data = data.dropna().copy() #doing the .diff(0 will make the first value nan)
theta_rad = np.radians(data['Gradient_deg'])
a = data["acc"]
v = data["velocity_ms"]

b = (m*g*np.sin(theta_rad)) - (m*a)

crr = m*g*np.cos(theta_rad)
cda = 0.5*rho*(v**2)*Ar

#finding the values of coefficients
coeffs = np.vstack([crr, cda]).T

#seperating out the rows that will be considered coasting
coasting = b > 0

coeffs_n = coeffs[coasting]
b_n = b[coasting]

sol, residuals,rank, s = np.linalg.lstsq(coeffs_n,b_n, rcond=None)

#The values of crr, cd
print("crr : ",sol[0])
print("cd : ",sol[1])

#plotting
plt.figure(figsize=(10,6))
x_axis = range(len(b))

b_fitted = coeffs.dot(sol) #using the sol i got to fit the model

#plotting the data point, coasting and all
plt.scatter(x_axis,b,color='gray', alpha=0.7, s=10, label='force')
plt.scatter(np.array(x_axis)[coasting], b_n, color='blue', alpha=0.7, s=10, label='force(coasting)')

#plotting the fit model
plt.plot(x_axis, b_fitted, color='red', linewidth=3, label='fit model')

plt.title("Fit Model vs data")
plt.xlabel("time")
plt.ylabel("Force")

plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

