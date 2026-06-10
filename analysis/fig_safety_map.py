#!/usr/bin/env python3
"""fig_safety_map.py — static Kampala safety map: basemap + Voronoi coverage cells colored by
predicted EPA tier, sensors as points. 3 panels: NOW / +1 day / +7 days. Validates the projection
and gives an embeddable figure for the pyramid views."""
import os, json, warnings; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
import features as F

OUT = os.path.join(F.HERE, "results")
m = json.load(open(os.path.join(OUT, "map_predictions.json")))
img = plt.imread(os.path.join(OUT, "basemap_kampala.png"))
W, H = m["meta"]["img_w"], m["meta"]["img_h"]
TC = m["tier_colors"]

fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8))
for ax, (hz, title) in zip(axes, [("now", "NOW (today)"), ("d1", "+1 DAY"), ("d7", "+7 DAYS")]):
    ax.imshow(img, extent=[0, W, H, 0], zorder=0)
    for s in m["sites"]:
        pr = s.get(hz)
        col = TC[pr["tier"]] if pr else "#999999"
        if s["poly"] and len(s["poly"]) >= 3:
            ax.add_patch(Polygon(s["poly"], closed=True, facecolor=col, edgecolor="white",
                                 lw=0.7, alpha=0.42, zorder=1))
        x, y = s["px"]
        ax.scatter([x], [y], s=14, c="#111", edgecolor="white", lw=0.5, zorder=3)
    # flag site_54
    s54 = next(s for s in m["sites"] if s["site"] == "site_54")
    ax.scatter(*s54["px"], s=160, facecolor="none", edgecolor="#c0392b", lw=2, zorder=4)
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{title}", fontsize=12, fontweight="bold")
leg = [Line2D([0],[0], marker='s', ls='', mfc=TC["Elevated"], mec='white', ms=12, label='Elevated ≤35.4'),
       Line2D([0],[0], marker='s', ls='', mfc=TC["High"], mec='white', ms=12, label='High 35.5–55.4'),
       Line2D([0],[0], marker='s', ls='', mfc=TC["Dangerous"], mec='white', ms=12, label='Dangerous >55.4'),
       Line2D([0],[0], marker='o', ls='', mfc='#c0392b', mec='#c0392b', fillstyle='none', ms=11, label='site_54 (anomaly)')]
axes[1].legend(handles=leg, loc='upper center', bbox_to_anchor=(0.5, -0.04), ncol=4, fontsize=9, frameon=False)
fig.suptitle("Kampala planner safety map — predicted EPA tier per sensor coverage area  ·  © OpenStreetMap © CARTO",
             fontsize=12.5, fontweight="bold", y=1.04)
fig.tight_layout(); p = os.path.join(OUT, "fig_safety_map.png")
fig.savefig(p, dpi=125, bbox_inches="tight"); plt.close(fig)
print("wrote", os.path.relpath(p, F.HERE))
