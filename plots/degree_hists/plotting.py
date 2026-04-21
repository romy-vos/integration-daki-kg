import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import seaborn as sns 
from matplotlib import colors
import pandas as pd

def plot_colored_hist(data, n_bins=20, title=None, x_lab="Value", y_lab="Frequency", color=None, edgecolor=None, ax=None):

    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 5))
    
    if not color:

        N, bins, patches = ax.hist(data, bins=n_bins)
        fracs = N / N.max()
        norm = colors.Normalize(fracs.min(), fracs.max())

        for thisfrac, thispatch in zip(fracs, patches):
            color_val = plt.cm.spring(norm(thisfrac))
            thispatch.set_facecolor(color_val)
    else:
        ax.hist(data, bins=n_bins, color=color, edgecolor=edgecolor)

    ax.set_xlabel(x_lab, fontsize=12) 
    ax.set_ylabel(y_lab, fontsize=12)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')

    ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.2)

    if title:
        ax.set_title(title, fontsize=14, fontweight ="bold")
        
    return ax

files = [
    ("plots/upd/ade_degrees_upd.tsv", "a. Drug hasAdverseEvent Concept"),
    ("plots/upd/ade_inverse_upd.tsv", "b. Concept hasAdverseEvent (inv) Drug"),
    ("plots/upd/ind_degrees_upd.tsv", "c. Drug isIndicatedFor Concept"),
    ("plots/upd/cind_degrees_upd.tsv", "d. Drug isContraIndicatedFor Concept")
]

plt.style.use('seaborn-v0_8-white')

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes_flat = axes.flatten()  

for i, (file_path, title) in enumerate(files):

    with open(file_path, "r") as f:
        df = pd.read_csv(f, sep = "\t")
        degrees = df["?totalEdges"]

    plot_colored_hist(
        degrees, 
        n_bins=30, 
        title=title, 
        x_lab="Number of outgoing edges", 
        color="#F08E81", 
        edgecolor="white",
        ax=axes_flat[i]
    )

plt.tight_layout()
#plt.show()
plt.savefig('plots/upd/combined_degree_distributions.pdf')