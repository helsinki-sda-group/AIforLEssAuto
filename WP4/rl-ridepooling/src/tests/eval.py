# plot_evaluations.py
import numpy as np
import matplotlib.pyplot as plt
import sys

if len(sys.argv) < 2:
    print("Usage: python plot_evaluations.py /path/to/evaluations.npz")
    exit()

path = sys.argv[1]
print(path)

data = np.load(path)

timesteps = data["timesteps"]
results = data["results"]

if results.ndim == 1:
    mean_rewards = results
else:
    mean_rewards = results.mean(axis=1)

plt.figure(figsize=(10,5))
plt.plot(timesteps, mean_rewards, marker='o')
plt.title("Evaluation rewards")
plt.xlabel("Training steps")
plt.ylabel("Evaluation reward")
plt.grid(True)
plt.show()
