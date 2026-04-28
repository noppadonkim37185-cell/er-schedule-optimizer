import calendar


DOCTOR_NAMES = ["นพดล", "สกล", "ธานินทร์", "สุจริต", "มุกดา", "หฤทัย", "จารุภา", "ใจประภัสส์", "กิตติยา"]
DOCTOR_NAME_BY_ID = {i: name for i, name in enumerate(DOCTOR_NAMES)}
MONTH_NAMES = list(calendar.month_name)[1:]

SHIFT_OPTIONS_OFF = {
    "All": "หยุดทั้งวัน (All Day)",
    "Morning": "เวรเช้า (ปรับตามวันธรรมดา/หยุดอัตโนมัติ)",
    "Afternoon_Night": "เวรบ่ายและดึก (Afternoon & Night)",
    0: "เวรเช้า: Trauma (เฉพาะวันธรรมดา)",
    1: "เวรเช้า: Non-Trauma (เฉพาะวันธรรมดา)",
    2: "เวรเช้า: Resus (เฉพาะวันธรรมดา)",
    4: "เวรบ่าย",
    5: "เวรดึก",
}

SHIFT_OPTIONS_ON = {
    "Any": "เวรใดก็ได้ในวันนั้น (อย่างน้อย 1 เวร)",
    "Morning": "เวรเช้า (ปรับตามวันธรรมดา/หยุดอัตโนมัติ)",
    "Afternoon_Night": "เวรบ่ายและดึก (Afternoon & Night)",
    0: "เวรเช้า: Trauma (เฉพาะวันธรรมดา)",
    1: "เวรเช้า: Non-Trauma (เฉพาะวันธรรมดา)",
    2: "เวรเช้า: Resus (เฉพาะวันธรรมดา)",
    4: "เวรบ่าย",
    5: "เวรดึก",
}

PREFERENCE_COLUMNS = {
    "no_night": "งดเวรดึก (No Night)",
    "no_consec_night": "ห้ามดึกติดกัน (Max 1 Night)",
    "no_aft_ngt_mon": "งดบ่าย/ดึก (จันทร์)",
    "no_aft_ngt_thu": "งดบ่าย/ดึก (พฤหัส)",
    "no_resus_tue": "งด Resus (อังคาร)",
    "no_resus_fri": "งด Resus (ศุกร์)",
    "no_aft_to_resus": "ห้ามบ่ายต่อเช้า Resus",
    "no_resus": "งดเวรเช้า Resus (ทุกวัน)",
    "max_shifts": "จำกัดเวรรวม/เดือน",
}

DOCTOR_COLOR_STYLES = {
    "นพดล": "background-color: #FFDDC1; color: #000;",
    "สกล": "background-color: #FFABAB; color: #000;",
    "ธานินทร์": "background-color: #FFC3A0; color: #000;",
    "สุจริต": "background-color: #D5AAFF; color: #000;",
    "มุกดา": "background-color: #85E3FF; color: #000;",
    "หฤทัย": "background-color: #B9FBC0; color: #000;",
    "จารุภา": "background-color: #F6A6FF; color: #000;",
    "ใจประภัสส์": "background-color: #FFFFD1; color: #000;",
    "กิตติยา": "background-color: #E7FFAC; color: #000;",
}
