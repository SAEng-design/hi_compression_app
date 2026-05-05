# H and I-Section Column — Compressive Resistance

A structural design tool for ViKO Consulting Engineers that calculates the design compressive resistance of H and I-section columns under axial load, in accordance with **SANS 10162-1**.

🔗 **Live App:** [Launch App](https://hicompressionapp-aotarm3guenobx57j8ojnb.streamlit.app/)

---

## Overview

This app calculates the factored compressive resistance `Cr` of H and I-section columns based on the design clauses of SANS 10162-1, including:

- Section classification per Cl. 11
- Slenderness ratio check per Cl. 10.4.2.1
- Flexural and torsional-flexural buckling per Cl. 13.3
- Effective area reduction for Class 4 sections per Cl. 13.3.3

The result is presented as a single governing `Cr` value, with a full breakdown of intermediate calculations.

---

## How the App Works

### 1. Section Selection

The app reads section properties directly from two CSV databases sourced from the SAISC Red Book:

- `h_sections.csv` — H-sections (column sections)
- `i_sections.csv` — I-sections (universal beam sections)

Users select the section type (H or I) and the designation from a dropdown. All geometric and sectional properties (`A`, `Ix`, `Iy`, `rx`, `ry`, `J`, `Cw`, etc.) are pulled automatically.

### 2. Material Selection

Users choose from standard steel grades or define a custom grade:

- **S355JR** — fy = 355 MPa
- **S275JR** — fy = 275 MPa
- **S235JR** — fy = 235 MPa
- **Custom** — user-defined fy between 200 and 700 MPa

For standard grades with flange thickness `tf > 16 mm`, the app automatically reduces fy per SANS specification (e.g., S355 → 345).

### 3. Manufacturing Type

The user selects the manufacturing process which sets the parameter `n` in Eq. 4.24:

- **Hot-rolled** — `n = 1.34`
- **Welded stress-relieved** — `n = 2.24`

### 4. Effective Lengths

Three independent effective lengths are entered:

- `KLx` — about the strong (x) axis
- `KLy` — about the weak (y) axis
- `KLz` — torsional buckling length

Setting any value to `0` indicates that axis is laterally restrained and excluded from the buckling check.

---

## Calculation Procedure

### Step 1: Section Classification (Cl. 11)

The flange and web are classified separately as **Class 3 or better** or **Class 4 (slender)**:

- **Flange** (supported on one edge): `b₁/t ≤ 200/√fy`
- **Web** (supported on both edges): `hw/tw ≤ 670/√fy`

Where:
- `b₁ = b/2` (half flange width)
- `hw = d` (clear web depth between flange fillet welds, taken from the CSV)

If either element exceeds its limit, the overall section is classified as **Class 4** and an effective area calculation is required.

### Step 2: Slenderness Check (Cl. 10.4.2.1)

Both `KLx/rx` and `KLy/ry` must not exceed **200**. The app flags any axis that exceeds this limit.

### Step 3: Elastic Buckling Stresses

Three elastic buckling stresses are calculated:

- **Flexural about x-axis:** `f_ex = π²E / (KLx/rx)²`
- **Flexural about y-axis:** `f_ey = π²E / (KLy/ry)²`
- **Torsional about z-axis:** `f_ez = [π²E·Cw/(KLz)² + GJ] / (A·r₀²)`

Where `r₀² = rx² + ry²` (for doubly symmetric sections, x₀ = y₀ = 0).

The governing elastic stress is `f_e = min(f_ex, f_ey, f_ez)`.

> **Note:** For commonly available H and I sections, flexural buckling almost always governs, but the torsional check is included for completeness.

### Step 4: Effective Area for Class 4 Sections (Cl. 13.3.3)

If the section is Class 4, the effective area is calculated using:
W = b/t
W_lim = 0.644 × √(k·E/f)
b_eff = 0.95t·√(k·E/f) × (1 - 0.208/W × √(k·E/f))
Where:
- `k = 0.43` for elements supported on one edge (flanges)
- `k = 4.0` for elements supported on both edges (webs)
- `f` is the calculated compressive stress in the element, taken as `f = fy·(1 + λ^(2n))^(-1/n)` (the actual compressive stress under ultimate load), capped at fy

The reduction is applied **only to elements that are individually Class 4**:
- Flange reduction is multiplied by 4 (2 flanges × 2 outstands per flange)
- Web reduction is applied once (single element)

### Step 5: Compressive Resistance (Cl. 13.3.1, Eq. 4.24)

The factored compressive resistance is calculated as:

Cr = φ·A_eff·fy·(1 + λ^(2n))^(-1/n)
Where:
- `φ = 0.90` (resistance factor)
- `A_eff` = gross area `A` for non-Class 4 sections, or reduced effective area for Class 4
- `λ = √(fy/f_e)` (non-dimensional slenderness ratio)
- `n` = 1.34 (hot-rolled) or 2.24 (welded stress-relieved)

---

## Output

The app displays:

1. **Section properties summary** — all dimensions and section properties in one panel
2. **Headline result** — `Cr` in kN, governing buckling mode, utilisation ratio, and PASS/FAIL status (if a factored load is provided)
3. **Detailed calculation breakdown** — every intermediate value from classification through to final `Cr`
4. **Buckling mode comparison table** — `Cr` if each individual buckling mode were to govern

If a factored axial load `C*` is entered, the app automatically computes the utilisation ratio and checks whether the section passes.

---

## Important Notes & Limitations

- ⚠️ **For Class 4 sections, always cross-check the `Cr` value against the SAISC Red Book.** The effective area calculation per Cl. 13.3.3 can be sensitive to the assumed value of `f`, and minor differences may occur compared to other reference tools.
- The app uses `hw = d` (clear depth between fillet welds) per the formal SANS 10162 definition, matching the textbook worked Example E4.3 exactly.
- Torsional-flexural buckling typically does not govern for H and I sections but is always included as a check.
- The factored material reduction for `tf > 16 mm` only applies to standard steel grades — custom grades require the user to enter the correct `fy` directly.
- The resistance factor `φ = 0.90` is fixed in line with SANS 10162-1 Cl. 13.3.1.

---

## Verification

The app has been verified against:

- **Worked Example E4.3** — 356×171×67 I-section, S355JR, KL = 6000 mm, hot-rolled
  - Expected: `Cr = 603 kN` ✅
  - App result: `Cr = 603 kN` ✅
- **QC comparison sheet** against SAISC SteelDesign Excel app for multiple sections — all non-Class 4 sections match to within 1%, Class 4 sections match within 5%

---

## Tech Stack

- **Python 3** with `pandas` for data handling and `streamlit` for the web interface
- **Hosted on:** [Streamlit Community Cloud](https://share.streamlit.io)
- **Section database:** `h_sections.csv` and `i_sections.csv` (extracted from SAISC Red Book)

---

---

## ⚠️ Disclaimer

This application is provided as a **design aid only** and does not replace the engineer's professional judgment or responsibility.

By using this app, the user accepts the following:

- The user is solely responsible for verifying all input values, intermediate calculations, and final results before using them in any structural design or for any project deliverable.
- All output should be **independently checked** against the relevant code (SANS 10162-1) and reference tools such as the SAISC Red Book or hand calculations, particularly for Class 4 sections, unusual configurations, or critical applications.
- ViKO Consulting Engineers, Jandre Nel, and any associated parties accept **no liability** for errors, omissions, misinterpretations, or any direct or indirect loss, damage, or harm arising from the use of this app or reliance on its results.
- This app is intended for use by qualified structural engineers who understand the underlying theory, code provisions, and limitations of the calculations performed.
- The app is provided "as is" without any warranty of accuracy, completeness, or fitness for a particular purpose.

**The engineer using this app remains fully responsible for the integrity, safety, and code compliance of any design produced.**

---
## About

Developed by **ViKO Consulting Engineers** as part of the internal Engineering Design Tools suite.


For questions, bug reports, or feature requests, please use the GitHub Issues tab.

---

*ViKO Consulting Engineers | 
Jandre Nel 081 756 1292

