import pandas as pd
import matplotlib.pyplot as plt

file = "8_ETF_Strangle"

df = pd.read_csv(file, header=None)
print(df)


plt.plot(df[0], df[1], label="Buy price")
plt.plot(df[0], df[2], label="Sell price")

plt.xlabel("Column 0")
plt.ylabel("Values")
plt.title(file)
plt.legend()
plt.grid(True)
plt.show()
