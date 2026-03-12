import os
import matplotlib
import numpy as np

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

def set_deterministic():
    np.random.seed(4269)

def apply_style(style_name: str):
    if style_name == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("default")

def _ensure_dir(out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

def plot_bands(snapshot: dict, out_path: str, style: str = "light"):
    set_deterministic()
    apply_style(style)
    
    fig, ax = plt.subplots(figsize=(16, 9))
    
    bounds = snapshot.get("bounds", {})
    if not bounds:
        ax.text(0.5, 0.5, "No Bounds Data", ha="center", va="center")
    else:
        names = list(bounds.keys())
        y_pos = np.arange(len(names))
        
        mins = [b.get("min", 0) for b in bounds.values()]
        maxs = [b.get("max", 1) for b in bounds.values()]
        
        for i, name in enumerate(names):
            ax.plot([mins[i], maxs[i]], [i, i], marker="|", color="blue", linewidth=4, markersize=15)
            
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.set_title("Corridor Bounds")
        ax.set_xlabel("Value")
        
    plt.tight_layout()
    _ensure_dir(out_path)
    fig.savefig(out_path, dpi=100)
    plt.close(fig)

def plot_objectives(snapshot: dict, out_path: str, style: str = "light"):
    set_deterministic()
    apply_style(style)
    
    fig, ax = plt.subplots(figsize=(16, 9))
    weights = snapshot.get("weights", {})
    
    if not weights:
        ax.text(0.5, 0.5, "No Weights Data", ha="center", va="center")
    else:
        names = list(weights.keys())
        vals = [weights[n] for n in names]
        
        ax.bar(names, vals, color="green")
        ax.set_title("Objective Weights")
        ax.set_ylabel("Weight")
        ax.set_ylim(0, 1.0)
        
    plt.tight_layout()
    _ensure_dir(out_path)
    fig.savefig(out_path, dpi=100)
    plt.close(fig)

def plot_version_diff(snapshot: dict, out_path: str, style: str = "light"):
    set_deterministic()
    apply_style(style)
    
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Simple placeholder diff logic (since we might not have 'before' data)
    # We will just plot a dummy version diff or rely on 'recent_kpis'
    ax.text(0.5, 0.5, "Version Diff Placeholder", ha="center", va="center")
    ax.set_title("Version Diff Visualization")
    
    plt.tight_layout()
    _ensure_dir(out_path)
    fig.savefig(out_path, dpi=100)
    plt.close(fig)
