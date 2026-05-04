# BIT-X Assets

**Visual, chart, and media assets for BIT-X Runtime Proof**  
**Boundary Information Theory (BIT)**  
**Author:** Bùi Quang Trịnh (Vietnam)  
**Companions:** OpenAI GPT & Google Gemini  
**Repository:** BIT-X-Runtime-Proof

---

## 1. Purpose

This `assets/` folder stores visual and supporting media files used across the BIT-X Runtime Proof repository.

The goal of this folder is to keep figures, charts, diagrams, and visual materials organized separately from source code and documentation.

In simple terms:

```text
Code lives in module folders.
Research documents live in docs/.
Visual outputs and reusable media live in assets/.
```

---

## 2. Asset Scope

The `assets/` folder may contain:

```text
architecture diagrams
runtime pipeline figures
simulation result images
infographics
module overview visuals
publication images
README support images
presentation-ready charts
```

These files are used to support the explanation of BIT-X modules and make the repository easier to understand.

---

## 3. Recommended Folder Structure

A clean asset structure may look like this:

```text
BIT-X-Runtime-Proof/assets/
│
├── README.md
│
├── architecture/
│   ├── bit_x_runtime_architecture.png
│   ├── bit_x_pipeline_overview.png
│   └── bit_x6_series_map.png
│
├── figures/
│   ├── x4_runtime_curve.png
│   ├── x5_reflex_response.png
│   ├── x6_2_boundary_diagnostics.png
│   ├── x6_3_temporal_boundary.png
│   ├── x6_4_goal_conflict_recovery.png
│   ├── x6_5_boundary_navigation.png
│   └── x6_6_boundary_mission_control.png
│
├── infographics/
│   ├── bit_x_overview_infographic.png
│   ├── bit_x6_adaptive_systems.png
│   └── bit_boundary_logic_visual.png
│
└── publication/
    ├── substack_cover.png
    ├── medium_cover.png
    └── social_preview.png
```

This structure is optional, but recommended as the repository grows.

---

## 4. Naming Convention

Use clear, lowercase file names with underscores.

Recommended style:

```text
bit_x_runtime_architecture.png
bit_x6_series_map.png
x6_2_boundary_diagnostics_output.png
x6_4_goal_conflict_recovery_chart.png
x6_6_boundary_mission_control_output.png
```

Avoid names like:

```text
image1.png
finalfinal.png
newchart.png
screenshot.png
```

Clear naming makes the repository easier to read and reuse.

---

## 5. Asset Types

Recommended asset types:

| Type | Use |
|---|---|
| `.png` | Charts, diagrams, GitHub README images |
| `.jpg` | Social media covers or compressed visuals |
| `.svg` | Clean architecture diagrams or icons |
| `.pdf` | Research handouts or professor-facing one-pagers |
| `.csv` | Prefer storing CSV logs inside module folders, not assets |
| `.mp4` | Optional demo videos or animated previews |

For most GitHub README images, `.png` is recommended.

---

## 6. Relationship to Module Folders

Each active module may already contain its own result chart.

Example:

```text
x6_5_boundary_information_navigation/
├── bit_x6_5_boundary_information_navigation.py
├── boundary_navigation_log.csv
└── bit_x6_5_boundary_navigation_output.png
```

That local output image should stay in the module folder.

The `assets/` folder should be used for:

```text
shared overview visuals
architecture maps
publication-ready images
figures reused across multiple README files
social or presentation graphics
```

In simple terms:

```text
Module-specific outputs → keep inside module folder.
Reusable global visuals → store in assets/.
```

---

## 7. How to Reference Assets in README Files

To display an image from `assets/` in the root README:

```markdown
<p align="center">
  <img src="assets/architecture/bit_x_runtime_architecture.png" width="85%" />
</p>
```

To display an image from a module folder:

```markdown
<p align="center">
  <img src="x6_5_boundary_information_navigation/bit_x6_5_boundary_navigation_output.png" width="85%" />
</p>
```

Use relative paths so the images render correctly on GitHub.

---

## 8. Recommended Main Visuals

The repository should eventually include a few high-level visuals:

| Visual | Suggested File |
|---|---|
| Full BIT-X architecture | `assets/architecture/bit_x_runtime_architecture.png` |
| X6 series pipeline | `assets/architecture/bit_x6_series_map.png` |
| Boundary logic overview | `assets/infographics/bit_boundary_logic_visual.png` |
| Runtime proof curve | `assets/figures/x4_runtime_curve.png` |
| Boundary diagnostics chart | `assets/figures/x6_2_boundary_diagnostics.png` |
| Boundary navigation chart | `assets/figures/x6_5_boundary_navigation.png` |
| Boundary mission control chart | `assets/figures/x6_6_boundary_mission_control.png` |

---

## 9. Visual Style Guidelines

Recommended style for BIT-X visuals:

```text
clean
minimal
high contrast
research-oriented
not overly decorative
easy to read in GitHub dark mode
```

Preferred visual direction:

```text
DeepMind / OpenAI style
technical but readable
diagram-first
few words, strong structure
clear labels
```

Avoid:

```text
overcrowded diagrams
too many colors
tiny unreadable labels
marketing-heavy visuals
unverified claims on images
```

---

## 10. Publication Use

Assets in this folder may be reused for:

```text
GitHub README
Substack articles
Medium posts
X / Twitter threads
research summaries
professor-facing PDFs
presentation slides
```

When using assets outside GitHub, keep claims conservative.

Recommended wording:

```text
conceptual prototype
simulation-oriented framework
preliminary result
research direction
requires independent validation
```

---

## 11. Minimal Claim

This folder does not contain evidence by itself.

It stores visual materials that support the repository.

The technical meaning of each figure should be explained in the corresponding module README, documentation file, or simulation script.

In simple terms:

```text
Assets support explanation.
They do not replace validation.
```

---

## 12. Disclaimer

The assets in this folder are for research, documentation, and communication purposes only.

They should not be interpreted as production validation, mission design approval, AI safety certification, financial advice, engineering certification, or operational guidance.

All figures should be treated as conceptual or simulation-based unless explicitly validated by independent testing.

---

## Author

**Bùi Quang Trịnh (Vietnam)**  
Founder / Author: **Boundary Information Theory (BIT)**  
Companions: **OpenAI GPT & Google Gemini**  
Repository: **BIT-X-Runtime-Proof**
