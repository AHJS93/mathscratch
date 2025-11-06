import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# Data
# ------------------------------------------------------------
NOTES_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MODE_PATTERNS = {
    "Ionian":       [2, 2, 1, 2, 2, 2, 1],
    "Dorian":       [2, 1, 2, 2, 2, 1, 2],
    "Phrygian":     [1, 2, 2, 2, 1, 2, 2],
    "Lydian":       [2, 2, 2, 1, 2, 2, 1],
    "Mixolydian":   [2, 2, 1, 2, 2, 1, 2],
    "Aeolian":      [2, 1, 2, 2, 1, 2, 2],
    "Locrian":      [1, 2, 2, 1, 2, 2, 2],
}
IONIAN_TRIADS = ["maj", "min", "min", "maj", "maj", "min", "dim"]

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def build_scale(root: str, intervals: list[int]):
    root_index = NOTES_SHARP.index(root)
    scale = [root]
    for step in intervals[:-1]:
        root_index = (root_index + step) % 12
        scale.append(NOTES_SHARP[root_index])
    return scale

def chord_quality_from_mode(mode: str):
    ionian = IONIAN_TRIADS.copy()
    shift = list(MODE_PATTERNS.keys()).index(mode)
    return ionian[shift:] + ionian[:shift]

def mode_scale(root: str, mode: str):
    pattern = MODE_PATTERNS[mode]
    scale = build_scale(root, pattern)
    qualities = chord_quality_from_mode(mode)
    chords = [f"{n}{qual if qual != 'maj' else ''}" for n, qual in zip(scale, qualities)]
    return scale, chords

def relative_modes(parent_key: str):
    all_modes = list(MODE_PATTERNS.keys())
    parent_scale = build_scale(parent_key, MODE_PATTERNS["Ionian"])
    modes = {}
    for i, mode in enumerate(all_modes):
        mode_root = parent_scale[i]
        _, chords = mode_scale(mode_root, mode)
        modes[f"{mode_root} {mode}"] = chords
    return modes

def parallel_modes(root_key: str):
    modes = {}
    for mode in MODE_PATTERNS.keys():
        _, chords = mode_scale(root_key, mode)
        modes[f"{root_key} {mode}"] = chords
    return modes

def reorder_modes(modes_dict, start_mode_name):
    keys = list(modes_dict.keys())
    start_idx = next((i for i, k in enumerate(keys) if k.endswith(start_mode_name)), 0)
    rotated_keys = keys[start_idx:] + keys[:start_idx]
    return {k: modes_dict[k] for k in rotated_keys}

def find_parent_major(selected_key, selected_mode):
    """Find the Ionian (major) key producing the selected key/mode"""
    modes = list(MODE_PATTERNS.keys())
    mode_index = modes.index(selected_mode)
    intervals = MODE_PATTERNS["Ionian"]
    total_semitones = sum(intervals[:mode_index])
    root_index = (NOTES_SHARP.index(selected_key) - total_semitones) % 12
    return NOTES_SHARP[root_index]

# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------
st.set_page_config(page_title="Mode & Key Chord Calculator", page_icon="🎵")


# 🔹 Global font & table styling
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 18px !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    h1, .stTitle {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stDataFrame"] table {
        font-size: 16px !important;
    }
    /* Wider content area */
    .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1100px;
    }
    @media (min-width: 1600px) {
        .block-container {
            max-width: 1300px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Inputs
selected_key = st.pills("Select a Key", NOTES_SHARP, index=0, horizontal=True, selection_mode="single")
selected_mode = st.radio("Select a Mode", list(MODE_PATTERNS.keys()), horizontal=True)
parallel = st.checkbox("Show Parallel Modes (same tonic)")
brightness_mode = st.checkbox("Highlight Modes by Brightness")
sort_by_brightness = st.checkbox("Sort Modes by Brightness")

# 🔹 Compute results
if parallel:
    results = parallel_modes(selected_key)
    st.subheader(f"Parallel modes for {selected_key}:")
else:
    parent_key = find_parent_major(selected_key, selected_mode)
    results = relative_modes(parent_key)
    st.subheader(f"Relative modes derived from {parent_key} major (selected: {selected_key} {selected_mode})")

# Reorder to start with selected mode
results = reorder_modes(results, selected_mode)

# 🔹 Build DataFrame
data_list = [{"Mode": mode, "Chords": chords} for mode, chords in results.items()]
df_chords = pd.DataFrame(data_list)

# Split chords into separate columns
max_chords = max(df_chords["Chords"].str.len())
chord_columns = pd.DataFrame(df_chords["Chords"].tolist(), columns=[f"Chord {i+1}" for i in range(max_chords)])
chord_df = pd.concat([df_chords["Mode"], chord_columns], axis=1)

# 🔹 Brightness mapping for sorting and coloring
BRIGHTNESS_ORDER = ["Lydian", "Ionian", "Mixolydian", "Dorian", "Aeolian", "Phrygian", "Locrian"]
BRIGHTNESS_MAP = {mode: idx for idx, mode in enumerate(BRIGHTNESS_ORDER)}
MODE_COLORS = {
    "Lydian": "rgba(0, 255, 255, 0.3)",       # cyan
    "Ionian": "rgba(0, 200, 0, 0.3)",         # green
    "Mixolydian": "rgba(173, 255, 47, 0.3)",  # yellow-green
    "Dorian": "rgba(255, 255, 0, 0.3)",       # yellow
    "Aeolian": "rgba(255, 165, 0, 0.3)",      # orange
    "Phrygian": "rgba(255, 69, 0, 0.3)",      # red-orange
    "Locrian": "rgba(128, 0, 128, 0.3)",      # purple
}

# 🔹 Sort by brightness if requested
if sort_by_brightness:
    chord_df["BrightnessRank"] = chord_df["Mode"].apply(lambda x: BRIGHTNESS_MAP.get(x.split()[-1], 100))
    chord_df = chord_df.sort_values("BrightnessRank").drop(columns=["BrightnessRank"]).reset_index(drop=True)

# 🔹 Highlighting function
def highlight_rows(row, selected_mode_name, parent_key_name, brightness=False):
    mode_name = row["Mode"]
    if brightness:
        mode_key = mode_name.split()[-1]
        color = MODE_COLORS.get(mode_key, '')
        if color:
            return [f'background-color: {color}; font-weight: bold'] * len(row)
        return [''] * len(row)
    else:
        if mode_name.endswith(selected_mode_name):
            return ['background-color: #2E86C1; color: white; font-weight: bold'] * len(row)
        elif not parallel and mode_name.startswith(parent_key_name) and "Ionian" in mode_name:
            return ['background-color: rgba(46, 134, 193, 0.2); font-weight: bold'] * len(row)
        else:
            return [''] * len(row)

# 🔹 Apply styling
styled_chord_df = chord_df.style.apply(
    highlight_rows,
    axis=1,
    selected_mode_name=selected_mode,
    parent_key_name=parent_key if not parallel else "",
    brightness=brightness_mode
).set_table_styles([
    {"selector": "td", "props": [("padding", "8px 20px"), ("text-align", "center")]}
])

# 🔹 Display the table
st.dataframe(styled_chord_df, width='stretch', hide_index=True)
