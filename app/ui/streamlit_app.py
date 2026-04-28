import calendar

import streamlit as st

from app.config import APP_TITLE, DEFAULT_YEAR, PAGE_LAYOUT, PAGE_TITLE
from app.constants import (
    DOCTOR_COLOR_STYLES,
    DOCTOR_NAME_BY_ID,
    MONTH_NAMES,
    PREFERENCE_COLUMNS,
    SHIFT_OPTIONS_OFF,
    SHIFT_OPTIONS_ON,
)
from app.services.excel_export import build_schedule_excel
from app.services.scheduler_service import generate_schedule
from app.utils.state import initialize_session_state


def highlight_doctors(val):
    return DOCTOR_COLOR_STYLES.get(val, "")


def style_schedule(df_schedule):
    try:
        return df_schedule.style.map(highlight_doctors)
    except AttributeError:
        return df_schedule.style.applymap(highlight_doctors)


def build_preferences_dict(preferences_df):
    prefs_dict = {}
    for _, row in preferences_df.iterrows():
        prefs_dict[row["ชื่อแพทย์"]] = {
            "no_night": row.get(PREFERENCE_COLUMNS["no_night"], False),
            "no_consec_night": row.get(PREFERENCE_COLUMNS["no_consec_night"], False),
            "no_aft_ngt_mon": row.get(PREFERENCE_COLUMNS["no_aft_ngt_mon"], False),
            "no_aft_ngt_thu": row.get(PREFERENCE_COLUMNS["no_aft_ngt_thu"], False),
            "no_resus_tue": row.get(PREFERENCE_COLUMNS["no_resus_tue"], False),
            "no_resus_fri": row.get(PREFERENCE_COLUMNS["no_resus_fri"], False),
            "no_aft_to_resus": row.get(PREFERENCE_COLUMNS["no_aft_to_resus"], False),
            "no_resus": row.get(PREFERENCE_COLUMNS["no_resus"], False),
            "max_shifts": row.get(PREFERENCE_COLUMNS["max_shifts"], 0),
        }
    return prefs_dict


def render_month_controls():
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input("ปี (ค.ศ.)", value=DEFAULT_YEAR, step=1)
        selected_month_idx = st.selectbox("เดือน", range(1, 13), format_func=lambda x: MONTH_NAMES[x - 1])
    with col2:
        _, num_days = calendar.monthrange(selected_year, selected_month_idx)
        special_holidays = st.multiselect("ระบุวันหยุดนักขัตฤกษ์/พิเศษเพิ่มเติม (วันที่)", range(1, num_days + 1))

    return selected_year, selected_month_idx, num_days, special_holidays


def render_request_list(session_key, options, clear_label):
    if st.session_state[session_key]:
        for i, (d, p, s) in enumerate(st.session_state[session_key]):
            col_text, col_btn = st.columns([5, 1])
            with col_text:
                st.write(f"- วันที่ {d}: {DOCTOR_NAME_BY_ID[p]} ({options[s]})")
            with col_btn:
                if st.button("ลบ", key=f"del_{session_key}_{i}"):
                    st.session_state[session_key].pop(i)
                    st.rerun()
        if st.button(clear_label):
            st.session_state[session_key] = []
            st.rerun()


def render_off_tab(num_days):
    mode_off = st.radio("รูปแบบการระบุวันหยุด (Off):", ["ระบุวันเดียว", "ระบุเป็นช่วง (หลายวันติดกัน)"], horizontal=True, key="mode_off")
    col_off1, col_off2, col_off3 = st.columns(3)
    with col_off1:
        doc_off = st.selectbox("เลือกแพทย์", options=list(DOCTOR_NAME_BY_ID.keys()), format_func=lambda x: DOCTOR_NAME_BY_ID[x], key="off_doc")
    with col_off2:
        if mode_off == "ระบุวันเดียว":
            day_off = st.selectbox("เลือกวันที่", range(1, num_days + 1), key="off_day_single")
            day_off_start, day_off_end = day_off, day_off
        else:
            day_off_start, day_off_end = st.slider("เลือกช่วงวันที่", 1, num_days, (1, 1), key="off_day_slider")
    with col_off3:
        shift_off = st.selectbox("ช่วงเวลาที่ต้องการ Off", options=list(SHIFT_OPTIONS_OFF.keys()), format_func=lambda x: SHIFT_OPTIONS_OFF[x], key="off_shift")

    if st.button("เพิ่มรายการ Off"):
        for d in range(day_off_start, day_off_end + 1):
            if (d, doc_off, shift_off) not in st.session_state.off_data:
                st.session_state.off_data.append((d, doc_off, shift_off))
        if day_off_start == day_off_end:
            st.success(f"บันทึก: {DOCTOR_NAME_BY_ID[doc_off]} Off วันที่ {day_off_start} [{SHIFT_OPTIONS_OFF[shift_off]}]")
        else:
            st.success(f"บันทึก: {DOCTOR_NAME_BY_ID[doc_off]} Off วันที่ {day_off_start} ถึง {day_off_end} [{SHIFT_OPTIONS_OFF[shift_off]}]")

    if st.session_state.off_data:
        st.markdown("**รายการ Off ปัจจุบัน:**")
        render_request_list("off_data", SHIFT_OPTIONS_OFF, "ล้างข้อมูล Off ทั้งหมด")


def find_doctor_preferences(doc_name):
    for _, row in st.session_state.preferences.iterrows():
        if row["ชื่อแพทย์"] == doc_name:
            return row
    return {}


def validate_on_request(selected_year, selected_month_idx, special_holidays, doc_on, shift_on, day_on_start, day_on_end):
    for d_on in range(day_on_start, day_on_end + 1):
        wd = calendar.weekday(selected_year, selected_month_idx, d_on)
        is_weekend = (wd >= 5) or (d_on in special_holidays)

        for d_off, p_off, s_off in st.session_state.off_data:
            conflict = False
            if d_off == d_on and p_off == doc_on:
                if s_off == "All" or shift_on == "All" or s_off == shift_on:
                    conflict = True
                elif s_off == "Morning" and shift_on in [0, 1, 2, "Morning"]:
                    conflict = True
                elif shift_on == "Morning" and s_off in [0, 1, 2, "Morning"]:
                    conflict = True
                elif s_off == "Afternoon_Night" and shift_on in [4, 5, "Afternoon_Night"]:
                    conflict = True
                elif shift_on == "Afternoon_Night" and s_off in [4, 5, "Afternoon_Night"]:
                    conflict = True

                if conflict:
                    return False, f"⚠️ ตรวจพบข้อขัดแย้ง: {DOCTOR_NAME_BY_ID[doc_on]} มีการขอ Off ในวันที่ {d_on} อยู่แล้ว"

        doc_prefs = find_doctor_preferences(DOCTOR_NAME_BY_ID[doc_on])

        if doc_prefs is not None:
            if shift_on in [5, "Afternoon_Night"] and doc_prefs.get(PREFERENCE_COLUMNS["no_night"], False):
                return False, f"⚠️ ขัดแย้งกับโปรไฟล์: {DOCTOR_NAME_BY_ID[doc_on]} ตั้งค่างดเวรดึกถาวร"

            if shift_on in [4, 5, "Afternoon_Night"]:
                if wd == 0 and doc_prefs.get(PREFERENCE_COLUMNS["no_aft_ngt_mon"], False):
                    return False, f"⚠️ ขัดแย้งกับโปรไฟล์: วันที่ {d_on} เป็นวันจันทร์ ซึ่ง {DOCTOR_NAME_BY_ID[doc_on]} ตั้งค่างดบ่าย/ดึก"
                if wd == 3 and doc_prefs.get(PREFERENCE_COLUMNS["no_aft_ngt_thu"], False):
                    return False, f"⚠️ ขัดแย้งกับโปรไฟล์: วันที่ {d_on} เป็นวันพฤหัสบดี ซึ่ง {DOCTOR_NAME_BY_ID[doc_on]} ตั้งค่างดบ่าย/ดึก"

            if shift_on == 2:
                if is_weekend:
                    return False, f"⚠️ วันที่ {d_on} เป็นวันหยุด ไม่มีโซน Resus เฉพาะให้ลง (กรุณาเลือก 'เวรเช้า: วันหยุด' แทน)"
                if doc_prefs.get(PREFERENCE_COLUMNS["no_resus"], False):
                    return False, f"⚠️ ขัดแย้งกับโปรไฟล์: {DOCTOR_NAME_BY_ID[doc_on]} ตั้งค่างดเวร Resus ถาวร"
                if wd == 1 and doc_prefs.get(PREFERENCE_COLUMNS["no_resus_tue"], False):
                    return False, f"⚠️ ขัดแย้งกับโปรไฟล์: วันที่ {d_on} เป็นวันอังคาร ซึ่ง {DOCTOR_NAME_BY_ID[doc_on]} ตั้งค่างด Resus"
                if wd == 4 and doc_prefs.get(PREFERENCE_COLUMNS["no_resus_fri"], False):
                    return False, f"⚠️ ขัดแย้งกับโปรไฟล์: วันที่ {d_on} เป็นวันศุกร์ ซึ่ง {DOCTOR_NAME_BY_ID[doc_on]} ตั้งค่างด Resus"

            if shift_on in [0, 1] and is_weekend:
                return False, f"⚠️ วันที่ {d_on} เป็นวันหยุด ไม่มีโซนในเวลาให้ลง (กรุณาเลือก 'เวรเช้า: วันหยุด' แทน)"

    return True, ""


def render_on_tab(selected_year, selected_month_idx, num_days, special_holidays):
    mode_on = st.radio("รูปแบบการระบุวันขึ้นเวร (On):", ["ระบุวันเดียว", "ระบุเป็นช่วง (หลายวันติดกัน)"], horizontal=True, key="mode_on")
    col_on1, col_on2, col_on3 = st.columns(3)
    with col_on1:
        doc_on = st.selectbox("เลือกแพทย์", options=list(DOCTOR_NAME_BY_ID.keys()), format_func=lambda x: DOCTOR_NAME_BY_ID[x], key="on_doc")
    with col_on2:
        if mode_on == "ระบุวันเดียว":
            day_on = st.selectbox("เลือกวันที่", range(1, num_days + 1), key="on_day_single")
            day_on_start, day_on_end = day_on, day_on
        else:
            day_on_start, day_on_end = st.slider("เลือกช่วงวันที่", 1, num_days, (1, 1), key="on_day_slider")
    with col_on3:
        shift_on = st.selectbox("ช่วงเวลาที่ต้องการขึ้นเวร", options=list(SHIFT_OPTIONS_ON.keys()), format_func=lambda x: SHIFT_OPTIONS_ON[x], key="on_shift")

    if st.button("เพิ่มรายการ ขอขึ้นเวร"):
        is_valid, conflict_msg = validate_on_request(selected_year, selected_month_idx, special_holidays, doc_on, shift_on, day_on_start, day_on_end)

        if is_valid:
            for d_on in range(day_on_start, day_on_end + 1):
                if (d_on, doc_on, shift_on) not in st.session_state.on_data:
                    st.session_state.on_data.append((d_on, doc_on, shift_on))
            if day_on_start == day_on_end:
                st.success(f"บันทึก: {DOCTOR_NAME_BY_ID[doc_on]} ขอขึ้นเวรวันที่ {day_on_start} [{SHIFT_OPTIONS_ON[shift_on]}]")
            else:
                st.success(f"บันทึก: {DOCTOR_NAME_BY_ID[doc_on]} ขอขึ้นเวรวันที่ {day_on_start} ถึง {day_on_end} [{SHIFT_OPTIONS_ON[shift_on]}]")
        else:
            st.error(conflict_msg)

    if st.session_state.on_data:
        st.markdown("**รายการขอขึ้นเวรปัจจุบัน:**")
        render_request_list("on_data", SHIFT_OPTIONS_ON, "ล้างข้อมูล ขึ้นเวร ทั้งหมด")


def render_preferences_tab():
    st.info("💡 **คำแนะนำ:** ติ๊กเลือกเงื่อนไขเพื่อตั้งเป็นขอบเขตอัตโนมัติ (นพ.สุจริต: งดบ่าย/ดึก จันทร์ + งด Resus อังคาร | นพ.สกล: งดบ่าย/ดึก พฤหัส + งด Resus ศุกร์)")

    edited_prefs = st.data_editor(
        st.session_state.preferences,
        hide_index=True,
        width="stretch",
        column_config={
            "ชื่อแพทย์": st.column_config.Column(disabled=True),
            PREFERENCE_COLUMNS["no_night"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_consec_night"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_aft_ngt_mon"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_aft_ngt_thu"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_resus_tue"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_resus_fri"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_aft_to_resus"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["no_resus"]: st.column_config.CheckboxColumn(),
            PREFERENCE_COLUMNS["max_shifts"]: st.column_config.NumberColumn(min_value=0, max_value=31, step=1),
        },
    )
    st.session_state.preferences = edited_prefs


def render_request_tabs(selected_year, selected_month_idx, num_days, special_holidays):
    st.subheader("จัดการคำขอและโปรไฟล์แพทย์")
    tab_off, tab_on, tab_pref = st.tabs(["🛑 ขอหยุดเวร (OFF)", "✅ ขอขึ้นเวร (ON)", "⚙️ ตั้งค่าโปรไฟล์แพทย์"])

    with tab_off:
        render_off_tab(num_days)
    with tab_on:
        render_on_tab(selected_year, selected_month_idx, num_days, special_holidays)
    with tab_pref:
        render_preferences_tab()


def render_results(selected_year, selected_month_idx, special_holidays):
    if st.button("ประมวลผลจัดตารางเวร", type="primary"):
        with st.spinner("กำลังคำนวณโครงสร้างตารางและเกลี่ยเวรให้สอดคล้องกับโปรไฟล์ของทุกคน..."):
            prefs_dict = build_preferences_dict(st.session_state.preferences)
            df_schedule, df_summary, conflicts = generate_schedule(
                selected_year,
                selected_month_idx,
                special_holidays,
                st.session_state.off_data,
                st.session_state.on_data,
                preferences=prefs_dict,
            )

            if df_schedule is not None:
                st.success("ประมวลผลสำเร็จ!")

                st.subheader("📊 สรุปจำนวนเวรรายบุคคล (Workload Summary)")
                st.dataframe(df_summary, width="stretch")

                st.subheader("📅 ตารางเวร ER รายเดือน")
                styled_schedule = style_schedule(df_schedule)
                st.dataframe(styled_schedule, width="stretch")

                excel_bytes = build_schedule_excel(df_schedule, df_summary, styled_schedule)
                st.download_button(
                    label="📥 ดาวน์โหลดตารางเวร (Excel รวม Sheet พร้อมสูตรและสี)",
                    data=excel_bytes,
                    file_name=f"ER_Schedule_{selected_year}_{selected_month_idx}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.error("❌ ไม่สามารถจัดตารางได้! โปรดตรวจสอบข้อจำกัดหรือการขอเวรที่ขัดแย้งกัน")
                if conflicts:
                    st.warning("⚠️ พบรายการที่ชนกันและทำให้ระบบล้มเหลว (โปรดพิจารณาลบหรือแก้ไขรายการเหล่านี้):")
                    for msg in conflicts:
                        st.write(f"- {msg}")
                else:
                    st.info("ไม่พบรายการขอเวรที่ขัดแย้งกันโดยตรง แต่อาจเกิดจากมีผู้ขอหยุดในวันเดียวกันมากเกินไปจนอัตรากำลังไม่เพียงพอ")


def main():
    st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)
    st.title(APP_TITLE)
    initialize_session_state()

    selected_year, selected_month_idx, num_days, special_holidays = render_month_controls()
    st.markdown("---")
    render_request_tabs(selected_year, selected_month_idx, num_days, special_holidays)
    st.markdown("---")
    render_results(selected_year, selected_month_idx, special_holidays)
