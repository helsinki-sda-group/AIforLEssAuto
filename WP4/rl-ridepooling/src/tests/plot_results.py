import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re


# ------------------------- SMOOTHING -------------------------
def smooth(y, window):
    """Centered moving average smoothing, exact-length, clean edges."""
    y = np.asarray(y)
    n = len(y)

    if window <= 1 or window > n:
        return y.copy()

    # pandas implementation gives perfect centered smoothing
    try:
        import pandas as pd
        return pd.Series(y).rolling(window=window,
                                    center=True,
                                    min_periods=1).mean().values
    except ImportError:
        # fallback implementation if pandas missing
        y_smooth = np.zeros_like(y, dtype=float)
        half = window // 2
        for i in range(n):
            start = max(0, i - half)
            end   = min(n, i + half + 1)
            y_smooth[i] = np.mean(y[start:end])
        return y_smooth


# ------------------------- LOADING -------------------------
def load_monitor_csv(path, use_cumsum=False):
    """Loads SB3 monitor.csv and returns (x_axis, rewards).

    If use_cumsum=True, x_axis is cumulative episode length (training timesteps).
    Otherwise, x_axis is the 't' column from the file.
    """
    if not os.path.exists(path):
        return None, None
    df = pd.read_csv(path, skiprows=1)
    rewards = df["r"].values

    if use_cumsum:
        x = np.cumsum(df["l"].values)  # cumulative RL steps
    else:
        x = df["t"].values             # whatever was logged as t (e.g. SUMO time)

    return x, rewards



def load_eval_npz(path):
    """Loads evaluations.npz and returns (train_timesteps, eval_rewards)."""
    if not os.path.exists(path):
        return None, None
    data = np.load(path)
    return data["timesteps"], data["results"].flatten()


def extract_static_baselines(stdout_path):
    """Parses static baseline rewards from stdout.txt."""
    if not os.path.exists(stdout_path):
        return None

    pattern = r"accumulated reward:\s*([0-9\.\-eE]+)"
    values = []
    with open(stdout_path, "r") as f:
        for line in f:
            m = re.search(pattern, line)
            if m:
                values.append(float(m.group(1)))

    if len(values) == 0:
        return None

    return max(values)  # best only


# ---------------------- MAIN PLOT FUNCTION ----------------------
def plot_all(exp_name, smooth_win, out_path=None):

    base_dir = os.path.join("src", "tests", "output", exp_name)

    # ------------------ TRAIN ------------------
    train_t, train_r = load_monitor_csv(
        os.path.join(base_dir, "train", "monitor.csv"),
        use_cumsum=True,        
    )


    # ------------------ EVALUATION ------------------
    eval_npz_path = os.path.join(base_dir, "eval", "evaluations.npz")
    eval_t, eval_r = load_eval_npz(eval_npz_path)

    # ------------------ TEST (mean ± std) ------------------
    _, test_r = load_monitor_csv(os.path.join(base_dir, "test", "monitor.csv"))
    test_mean = np.mean(test_r) if test_r is not None else None
    test_std  = np.std(test_r) if test_r is not None else None

    # ------------------ RANDOM (mean ± std) ------------------
    _, rand_r = load_monitor_csv(os.path.join(base_dir, "test_random", "monitor.csv"))
    rand_mean = np.mean(rand_r) if rand_r is not None else None
    rand_std  = np.std(rand_r) if rand_r is not None else None

    # ------------------ STATIC BASELINE ------------------
    best_static = extract_static_baselines(os.path.join(base_dir, "stdout.txt"))

    # ------------------ PLOTTING ------------------
    plt.figure(figsize=(14, 8))

    # TRAIN CURVE
    if train_r is not None:
        plt.plot(train_t,
                 smooth(train_r, smooth_win),
                 label="Train reward (smoothed)",
                 color="steelblue",
                 linewidth=2)

    # EVAL CURVE (correct training timestep axis!)
    if eval_r is not None:
        plt.plot(eval_t,
                 smooth(eval_r, smooth_win),
                 label="Evaluation reward (smoothed)",
                 color="darkorange",
                 linewidth=2)

    # TEST mean ± std
    if test_mean is not None:
        xmax = np.max(train_t) if train_t is not None else np.max(eval_t)
        plt.axhline(test_mean, color="green", linestyle="--",
                    label=f"Test mean: {test_mean:.1f}")
        plt.fill_between([0, xmax],
                         test_mean - test_std,
                         test_mean + test_std,
                         color="green", alpha=0.12)

    # RANDOM mean ± std
    if rand_mean is not None:
        xmax = np.max(train_t) if train_t is not None else np.max(eval_t)
        plt.axhline(rand_mean, color="purple", linestyle="--",
                    label=f"Random mean: {rand_mean:.1f}")
        plt.fill_between([0, xmax],
                         rand_mean - rand_std,
                         rand_mean + rand_std,
                         color="purple", alpha=0.12)

    # BEST STATIC BASELINE
    if best_static is not None:
        plt.axhline(best_static, color="red", linestyle="--",
                    linewidth=2,
                    label=f"Best static baseline: {best_static:.1f}")

    # AXIS, GRID, LEGEND
    plt.title(f"Results for experiment: {exp_name}", fontsize=16)
    plt.xlabel("Training Timesteps", fontsize=14)
    plt.ylabel("Reward", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)

    # OUTPUT PATH
    if out_path is None:
        out_path = os.path.join(base_dir, f"{exp_name}.png")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"Saved plot to: {out_path}")


# ---------------------- ENTRY POINT ----------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        # python src/tests/plot_results.py delta_3_2 1 
        print("Usage: python plot_results.py <experiment_name> <smooth_window> [output_path]")
        sys.exit(1)

    exp_name = sys.argv[1]
    smooth_win = int(sys.argv[2])
    out_path = sys.argv[3] if len(sys.argv) >= 4 else None

    plot_all(exp_name, smooth_win, out_path)
