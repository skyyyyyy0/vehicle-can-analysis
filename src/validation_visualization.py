from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# =========================================
# Path setup
# =========================================

OUTPUT_DIR = Path("outputs")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"

SUMMARY_PATH = OUTPUT_DIR / "multi_file_validation_summary.csv"

OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)


def load_validation_summary() -> pd.DataFrame:
    """Load multi-file validation summary CSV."""

    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Summary file not found: {SUMMARY_PATH}")

    summary_df = pd.read_csv(SUMMARY_PATH)

    print("\nValidation summary loaded successfully.")
    print(summary_df.head())

    return summary_df


def plot_dynamic_transition_ratio(summary_df: pd.DataFrame) -> None:
    """Plot dynamic transition ratio by MF4 file."""

    plt.figure(figsize=(12, 6))

    plt.bar(
        summary_df["file_name"],
        summary_df["dynamic_transition_ratio"]
    )

    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Dynamic Transition Ratio")
    plt.xlabel("MF4 File")
    plt.title("Dynamic Transition Ratio by MF4 File")

    plt.tight_layout()

    output_path = SCREENSHOT_DIR / "validation_dynamic_transition_ratio.png"

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {output_path}")


def plot_byte_4_diff_mean(summary_df: pd.DataFrame) -> None:
    """Plot mean byte_4 transition difference by MF4 file."""

    plt.figure(figsize=(12, 6))

    plt.bar(
        summary_df["file_name"],
        summary_df["byte_4_diff_mean"]
    )

    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Mean byte_4_diff")
    plt.xlabel("MF4 File")
    plt.title("Mean byte_4 Transition Difference by MF4 File")

    plt.tight_layout()

    output_path = SCREENSHOT_DIR / "validation_byte_4_diff_mean.png"

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {output_path}")


def plot_session_behavior_distribution(summary_df: pd.DataFrame) -> None:
    """Plot session behavior distribution."""

    behavior_counts = summary_df["session_behavior"].value_counts()

    plt.figure(figsize=(7, 7))

    plt.pie(
        behavior_counts,
        labels=behavior_counts.index,
        autopct="%1.1f%%"
    )

    plt.title("Session Behavior Distribution")

    plt.tight_layout()

    output_path = SCREENSHOT_DIR / "validation_session_behavior_distribution.png"

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {output_path}")


def main() -> None:
    summary_df = load_validation_summary()

    plot_dynamic_transition_ratio(summary_df)
    plot_byte_4_diff_mean(summary_df)
    plot_session_behavior_distribution(summary_df)

    print("\nValidation visualization generation complete.")


if __name__ == "__main__":
    main()