import pandas as pd
import streamlit as st

from app.constants import DOCTOR_NAMES, PREFERENCE_COLUMNS


def default_preferences():
    default_prefs = []
    for name in DOCTOR_NAMES:
        default_prefs.append(
            {
                "ชื่อแพทย์": name,
                PREFERENCE_COLUMNS["no_night"]: False,
                PREFERENCE_COLUMNS["no_consec_night"]: False,
                PREFERENCE_COLUMNS["no_aft_ngt_mon"]: False,
                PREFERENCE_COLUMNS["no_aft_ngt_thu"]: False,
                PREFERENCE_COLUMNS["no_resus_tue"]: False,
                PREFERENCE_COLUMNS["no_resus_fri"]: False,
                PREFERENCE_COLUMNS["no_aft_to_resus"]: False,
                PREFERENCE_COLUMNS["no_resus"]: False,
                PREFERENCE_COLUMNS["max_shifts"]: 0,
            }
        )
    return pd.DataFrame(default_prefs)


def initialize_session_state():
    if "preferences" not in st.session_state or PREFERENCE_COLUMNS["no_aft_ngt_mon"] not in st.session_state.preferences.columns:
        st.session_state.preferences = default_preferences()

    if "off_data" not in st.session_state:
        st.session_state.off_data = []

    if "on_data" not in st.session_state:
        st.session_state.on_data = []
