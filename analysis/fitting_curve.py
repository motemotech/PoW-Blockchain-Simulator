import argparse
import numpy as np
import matplotlib.pyplot as plt


def compute_r_A(alpha_a: float, T: float, Delta: np.ndarray) -> np.ndarray:
    """Compute r_A for given parameters.

    Parameters
    - alpha_a: dominant node hashrate share (0..1)
    - T: target block interval (ms)
    - Delta: propagation delay(s) (ms), scalar or ndarray
    """
    Delta = np.asarray(Delta, dtype=np.float64)

    E = np.exp(- alpha_a * Delta / T)

    # 支配的なノードのラウンド開始率
    numerator = (
        alpha_a * E
        + Delta * alpha_a * alpha_a * E / T
        + 1 - E
        - Delta * alpha_a * E / T
    )
    denominator = 1 + Delta * alpha_a * alpha_a * E / T - Delta * alpha_a * E / T
    pi_A = numerator / denominator

    W_A = 1.0
    W_1 = Delta * alpha_a * E / T
    W_2 = 1 - E - Delta * alpha_a * E / T
    S = (alpha_a - alpha_a * W_2 + W_2) / (1 + alpha_a * W_1 - W_1)
    W_O = W_1 * S + W_2

    r_A = pi_A * W_A + (1 - pi_A) * W_O
    return r_A


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot r_A vs Delta (propagation delay)")
    parser.add_argument("--alpha", type=float, default=0.5, help="dominant node hashrate share α_A (default: 0.5)")
    parser.add_argument("--T", type=float, default=600000.0, help="target block interval T in ms (default: 600000)")
    parser.add_argument("--delta-min", type=float, default=300000.0, help="min Delta in ms (default: 300000)")
    parser.add_argument("--delta-max", type=float, default=6000000.0, help="max Delta in ms (default: 6000000)")
    parser.add_argument("--num", type=int, default=300, help="number of sample points (default: 300)")
    parser.add_argument("--out", type=str, default="r_A_vs_Delta.png", help="output figure filename")
    parser.add_argument("--no-show", action="store_true", help="do not display the plot window")
    args = parser.parse_args()

    # Delta grid
    Delta = np.linspace(args.delta_min, args.delta_max, args.num)
    r_A = compute_r_A(args.alpha, args.T, Delta)

    # Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(Delta, r_A, color="#1f77b4", lw=2)
    ax.set_title(r"$r_A$ vs $\Delta$")
    ax.set_xlabel(r"Propagation delay $\Delta$ (ms)")
    ax.set_ylabel(r"$r_A$")
    ax.grid(True)
    fig.tight_layout()
    plt.savefig(args.out, dpi=300)
    print(f"Saved figure to: {args.out}")
    if not args.no_show:
        try:
            plt.show()
        except Exception:
            pass


if __name__ == "__main__":
    main()
