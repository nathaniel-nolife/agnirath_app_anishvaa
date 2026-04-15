import pandas as pd
import numpy as np

#a) loads the csv
data = pd.read_csv("example.csv")
print(data.info())

#b) cleaning the data and interpolating
data.loc[data["velocity"] < 0, "velocity"] = np.nan
data.loc[data["voltage"] > 160, "voltage"] = np.nan
data.loc[data["solar_irradiance"] > 1200, "solar_irradiance"] =np.nan

data["velocity","voltage","solar_irradiance"] = data["velocity","voltage","solar_irradiance"].interpolate()

#c) creating a new column (area = 4m^2, eff = 0.25)
#these approximations are made based on the rules of the race (cars typically have 5) and the efficiency is also typically in this range.
eff = 0.25
area = 5
data["power_input"] = data["solar_irradiance"] * eff * area





