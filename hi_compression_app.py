import streamlit as st
import pandas as pd
import math

# --- Page config ---
st.set_page_config(
    page_title="H/I Column — Compression Design",
    page_icon="🏛️",
    layout="wide"
)
st.title("H and I-Section Column — Compressive Resistance")
st.caption("Per SANS 10162-1 | Cl. 11 (Classification), 13.3 (Compressive Resistance), 10.4 (Slenderness)")

# --- Load section databases ---
@st.cache_data
def load_sections():
    import os
    local_path = r"W:\Central Information\DESIGN\VIKO Design Tool\H & I Compression Only"

    if os.path.exists(local_path):
        h = pd.read_csv(local_path + r"\h_sections.csv", sep=";", decimal=",", encoding="utf-8-sig", dtype=str)
        i = pd.read_csv(local_path + r"\i_sections.csv", sep=";", decimal=",", encoding="utf-8-sig", dtype=str)
    else:
        h = pd.read_csv("h_sections.csv", sep=";", decimal=",", encoding="utf-8-sig", dtype=str)
        i = pd.read_csv("i_sections.csv", sep=";", decimal=",", encoding="utf-8-sig", dtype=str)

    h.columns = h.columns.str.strip()
    i.columns = i.columns.str.strip()

    for df in [h, i]:
        for col in df.columns:
            if col != "designation":
                df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")

    return h, i

h_df, i_df = load_sections()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Section")
section_type = st.sidebar.radio("Section type", ["I-Section", "H-Section"])

if section_type == "H-Section":
    designations = h_df["designation"].tolist()
    df_use       = h_df
else:
    designations = i_df["designation"].tolist()
    df_use       = i_df

selected = st.sidebar.selectbox("Designation", designations)
row = df_use[df_use["designation"] == selected].iloc[0]

# Extract section properties
m   = float(row["m"])
h   = float(row["h"])
b   = float(row["b"])
tw  = float(row["tw"])
tf  = float(row["tf"])
r1  = float(row["r"])
A   = float(row["A"]) * 1e3
d   = float(row["d"])
Ix  = float(row["Ix"]) * 1e6
Zex = float(row["Zex"]) * 1e3
rx  = float(row["rx"])
Iy  = float(row["Iy"]) * 1e6
Zey = float(row["Zey"]) * 1e3
ry  = float(row["ry"])
J   = float(row["J"]) * 1e3
Cw  = float(row["Cw"]) * 1e9

hw = float(row["d"])   # clear web depth from CSV (between fillet welds)

# ── Materials ─────────────────────────────────────────────────────────────────
st.sidebar.header("Material")
steel_grades = {
    "S355JR — fy = 355 MPa": 355,
    "S275JR — fy = 275 MPa": 275,
    "S235JR — fy = 235 MPa": 235,
    "Custom...": None,
}
grade_label = st.sidebar.selectbox("Steel Grade", list(steel_grades.keys()))

if grade_label == "Custom...":
    fy = st.sidebar.number_input(
        "Custom fy (MPa)",
        min_value=200,
        max_value=700,
        value=355,
        step=5,
        help="Enter the yield strength of your custom steel grade in MPa"
    )
else:
    fy = steel_grades[grade_label]

    if tf > 16:
        if fy == 355:
            fy = 345
        elif fy == 275:
            fy = 265
        elif fy == 235:
            fy = 225

E = 200000   # MPa
G = 77000    # MPa
phi = 0.90

# ── Manufacturing type ────────────────────────────────────────────────────────
st.sidebar.header("Manufacturing")
mfg = st.sidebar.radio(
    "Manufacturing type (sets parameter n)",
    ["Hot-rolled (n = 1.34)", "Welded stress-relieved (n = 2.24)"]
)
n_param = 1.34 if "1.34" in mfg else 2.24

# ── Effective lengths ─────────────────────────────────────────────────────────
st.sidebar.header("Effective Lengths")
st.sidebar.caption("Enter KL values — set to 0 for axes that are laterally restrained")

KLx = st.sidebar.number_input("KLx — about strong axis (mm)", min_value=0,    max_value=20000, value=6000, step=100)
KLy = st.sidebar.number_input("KLy — about weak axis (mm)",   min_value=0,    max_value=20000, value=6000, step=100)
KLz = st.sidebar.number_input("KLz — torsional (mm)",          min_value=0,    max_value=20000, value=6000, step=100)

# ── Design check ──────────────────────────────────────────────────────────────
st.sidebar.header("Design Check (optional)")
C_f = st.sidebar.number_input("Factored axial load C* (kN)", min_value=0.0, value=0.0, step=10.0)

# ══ CALCULATIONS ══════════════════════════════════════════════════════════════

# 1. Section classification (Cl. 11, Table 3 / Table 4.2)
b1_flange    = b / 2
flange_ratio = b1_flange / tf
flange_limit = 200 / math.sqrt(fy)
flange_class = "Class 4 (slender)" if flange_ratio > flange_limit else "Not Class 4"

web_ratio  = hw / tw
web_limit  = 670 / math.sqrt(fy)
web_class  = "Class 4 (slender)" if web_ratio > web_limit else "Not Class 4"

is_class4     = flange_class.startswith("Class 4") or web_class.startswith("Class 4")
section_class = "Class 4 (Slender)" if is_class4 else "Class 3 or better"

# 2. Slenderness ratios (Cl. 10.4.2.1, limit ≤ 200)
sl_x = KLx / rx if KLx > 0 else 0
sl_y = KLy / ry if KLy > 0 else 0
sl_x_ok = sl_x <= 200
sl_y_ok = sl_y <= 200

# 3. Elastic buckling stresses
def safe_fe(KL, r):
    if KL <= 0:
        return float("inf")
    return math.pi**2 * E / (KL / r)**2

f_ex = safe_fe(KLx, rx)
f_ey = safe_fe(KLy, ry)

if KLz > 0:
    r0_sq = rx**2 + ry**2
    f_ez  = (math.pi**2 * E * Cw / KLz**2 + G * J) / (A * r0_sq)
else:
    f_ez = float("inf")

f_e = min(f_ex, f_ey, f_ez)

if   f_e == f_ex: governing_mode = "Flexural buckling about x-axis"
elif f_e == f_ey: governing_mode = "Flexural buckling about y-axis"
else:             governing_mode = "Torsional buckling about z-axis"

# 4. Effective area (Cl. 13.3.3) — calculated AFTER governing fe is known
# Per Cl. 13.3.3, f is the calculated compressive stress in the element (≤ fy).
# Per textbook example: f = fy·(1 + λ^(2n))^(-1/n) — actual compressive stress
# under ultimate load using the column resistance formula (without phi).
def effective_area(A_gross, f_calc):
    """Reduce element widths per Cl. 13.3.3 / Eq. 4.46 — only if Class 4."""
    Aef = A_gross
    reductions = {"flange": 0.0, "web": 0.0}

    # Flange — supported on one edge (k = 0.43) — only if flange is Class 4
    if flange_class.startswith("Class 4"):
        W_f     = b1_flange / tf
        W_lim_f = 0.644 * math.sqrt(0.43 * E / f_calc)
        if W_f > W_lim_f:
            b_eff_f = 0.95 * tf * math.sqrt(0.43 * E / f_calc) * (1 - (0.208 / W_f) * math.sqrt(0.43 * E / f_calc))
            # 4 outstand portions: 2 flanges × 2 outstands per flange
            reductions["flange"] = 4 * (b1_flange - b_eff_f) * tf
            Aef -= reductions["flange"]

    # Web — supported on both edges (k = 4.0) — only if web is Class 4
    if web_class.startswith("Class 4"):
        W_w     = hw / tw
        W_lim_w = 0.644 * math.sqrt(4.0 * E / f_calc)
        if W_w > W_lim_w:
            b_eff_w = 0.95 * tw * math.sqrt(4.0 * E / f_calc) * (1 - (0.208 / W_w) * math.sqrt(4.0 * E / f_calc))
            reductions["web"] = (hw - b_eff_w) * tw
            Aef -= reductions["web"]

    return max(Aef, 0), reductions

# Calculate f per Cl. 13.3.3 / textbook formula
lam_for_aef = math.sqrt(fy / f_e)
f_for_aef   = fy * (1 + lam_for_aef**(2 * n_param))**(-1 / n_param)
f_for_aef   = min(f_for_aef, fy)   # cap at fy per code

if is_class4:
    A_eff, area_reductions = effective_area(A, f_for_aef)
else:
    A_eff = A
    area_reductions = {"flange": 0.0, "web": 0.0}

# 5. Compressive resistance — Eq. 4.24
lam = math.sqrt(fy / f_e)
Cr  = phi * A_eff * fy * (1 + lam**(2 * n_param))**(-1 / n_param) / 1000   # kN

# Check slenderness pass/fail
slenderness_ok = (sl_x == 0 or sl_x_ok) and (sl_y == 0 or sl_y_ok)

# ══ DISPLAY ═══════════════════════════════════════════════════════════════════

st.subheader("Section properties")
props = {
    "Designation":   selected,
    "Section type":  section_type,
    "Mass m":        f"{m:.1f} kg/m",
    "Depth h":       f"{h:.1f} mm",
    "Width b":       f"{b:.1f} mm",
    "tw":            f"{tw:.1f} mm",
    "tf":            f"{tf:.1f} mm",
    "Web depth hw":  f"{hw:.1f} mm",
    "A (gross)":     f"{A:.0f} mm²",
    "Ix":            f"{Ix:.2e} mm⁴",
    "Iy":            f"{Iy:.2e} mm⁴",
    "rx":            f"{rx:.1f} mm",
    "ry":            f"{ry:.1f} mm",
    "J":             f"{J:.2e} mm⁴",
    "Cw":            f"{Cw:.2e} mm⁶",
    "fy (used)":     f"{fy} MPa",
}
cols = st.columns(4)
for i, (k, v) in enumerate(props.items()):
    cols[i % 4].markdown(f"**{k}:** {v}")

st.divider()

# ── Headline result ───────────────────────────────────────────────────────────
if C_f > 0:
    util   = C_f / Cr
    status = "✅ PASS" if Cr >= C_f else "❌ FAIL"
    header = (
        f"**Compressive resistance Cr = {Cr:.1f} kN**  |  "
        f"Governing: {governing_mode}  |  "
        f"C* = {C_f:.1f} kN  |  "
        f"Utilisation = {util:.2f}  |  {status}"
    )
else:
    header = (
        f"**Compressive resistance Cr = {Cr:.1f} kN**  |  "
        f"Governing: {governing_mode}"
    )

st.subheader("Design results")

with st.expander(header, expanded=True):

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cr",            f"{Cr:.1f} kN")
    c2.metric("λ",             f"{lam:.3f}")
    c3.metric("f_e",           f"{f_e:.1f} MPa")
    c4.metric("Section class", "Class 4" if is_class4 else "Cl. 3 or better")

    rows = [
        ("─── 1. Section classification — Cl. 11 ───",                           ""),
        ("Flange b₁/t",                                                          f"{flange_ratio:.2f}"),
        ("Flange limit (200/√fy)",                                               f"{flange_limit:.2f}"),
        ("Flange",                                                               flange_class),
        ("Web hw/tw",                                                            f"{web_ratio:.2f}"),
        ("Web limit (670/√fy)",                                                  f"{web_limit:.2f}"),
        ("Web",                                                                  web_class),
        ("Overall section",                                                      section_class),

        ("─── 2. Slenderness check — Cl. 10.4.2.1 ───",                          ""),
        ("KLx / rx",                                                             f"{sl_x:.1f}" if KLx > 0 else "— (laterally restrained)"),
        ("KLy / ry",                                                             f"{sl_y:.1f}" if KLy > 0 else "— (laterally restrained)"),
        ("Limit",                                                                "200"),
        ("KLx/rx status",                                                        "OK ✅" if (KLx == 0 or sl_x_ok) else "EXCEEDS LIMIT ❌"),
        ("KLy/ry status",                                                        "OK ✅" if (KLy == 0 or sl_y_ok) else "EXCEEDS LIMIT ❌"),

        ("─── 3. Elastic buckling stresses ───",                                 ""),
        ("f_ex = π²E / (KLx/rx)²",                                               f"{f_ex:.1f} MPa" if KLx > 0 else "— (restrained)"),
        ("f_ey = π²E / (KLy/ry)²",                                               f"{f_ey:.1f} MPa" if KLy > 0 else "— (restrained)"),
        ("f_ez = [π²E·Cw/(KLz)² + GJ] / (A·r₀²)",                               f"{f_ez:.1f} MPa" if KLz > 0 else "— (restrained)"),
        ("Governing f_e",                                                        f"{f_e:.1f} MPa"),
        ("Governing mode",                                                       governing_mode),

        ("─── 4. Effective area — Cl. 13.3.3 ───",                               ""),
        ("f used = fy·(1+λ²ⁿ)^(-1/n), capped at fy",                            f"{f_for_aef:.1f} MPa"),
        ("A (gross)",                                                            f"{A:.0f} mm²"),
        ("Flange reduction (only if flange is Class 4)",                         f"{area_reductions['flange']:.1f} mm²"),
        ("Web reduction (only if web is Class 4)",                               f"{area_reductions['web']:.1f} mm²"),
        ("A_eff (used in Cr)",                                                   f"{A_eff:.0f} mm²"),
        ("Area reduction",                                                       f"{(1 - A_eff/A)*100:.1f} %"),

        ("─── 5. Compressive resistance — Cl. 13.3.1 / Eq. 4.24 ───",            ""),
        ("Manufacturing parameter n",                                            f"{n_param}"),
        ("λ = √(fy/f_e)",                                                        f"{lam:.3f}"),
        ("Resistance factor φ",                                                  f"{phi}"),
        ("Cr = φ·A_eff·fy·(1 + λ^(2n))^(-1/n)",                                  f"{Cr:.1f} kN"),
    ]

    df_out = pd.DataFrame(rows, columns=["Parameter", "Value"])
    st.dataframe(df_out, use_container_width=True, hide_index=True)

# ── Buckling mode comparison ──────────────────────────────────────────────────
st.subheader("Buckling mode comparison")
mode_rows = []
for label, fe_val, KL_val, axis in [
    ("Flexural about x-axis", f_ex, KLx, "rx"),
    ("Flexural about y-axis", f_ey, KLy, "ry"),
    ("Torsional about z-axis", f_ez, KLz, "—"),
]:
    if KL_val == 0:
        Cr_mode = "—"
        marker  = ""
    else:
        lam_mode = math.sqrt(fy / fe_val)
        Cr_mode_v = phi * A_eff * fy * (1 + lam_mode**(2 * n_param))**(-1 / n_param) / 1000
        Cr_mode   = f"{Cr_mode_v:.1f}"
        marker    = "★ " if abs(fe_val - f_e) < 0.01 else ""
    mode_rows.append({
        "Buckling mode":   marker + label,
        "Effective length (mm)": KL_val if KL_val > 0 else "Restrained",
        "f_e (MPa)":        f"{fe_val:.1f}" if KL_val > 0 else "—",
        "Cr if this governed (kN)": Cr_mode,
    })
st.dataframe(pd.DataFrame(mode_rows), use_container_width=True, hide_index=True)