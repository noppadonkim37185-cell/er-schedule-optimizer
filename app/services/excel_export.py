import io

import pandas as pd


def build_schedule_excel(df_schedule, df_summary, styled_schedule):
    """Build the Excel workbook using the same formulas and layout as the original app."""
    df_summary_excel = df_summary.copy()
    formula_columns = [
        "Trauma",
        "Non-Trauma",
        "Resus",
        "เช้าวันหยุด",
        "บ่าย",
        "ดึก",
        "รวมในเวลา",
        "รวมนอกเวลา (ได้ค่าเวร)",
        "รวมทั้งหมด",
    ]
    df_summary_excel[formula_columns] = df_summary_excel[formula_columns].astype("object")

    num_days_schedule = len(df_schedule)
    last_day_row = num_days_schedule + 1
    start_row_pandas = num_days_schedule + 2
    summary_data_start_row = start_row_pandas + 2

    for idx in df_summary_excel.index:
        r = summary_data_start_row + idx
        df_summary_excel.at[idx, "Trauma"] = f"=COUNTIF(B$2:B${last_day_row}, A{r})"
        df_summary_excel.at[idx, "Non-Trauma"] = f"=COUNTIF(C$2:C${last_day_row}, A{r})"
        df_summary_excel.at[idx, "Resus"] = f"=COUNTIF(D$2:D${last_day_row}, A{r})"
        df_summary_excel.at[idx, "เช้าวันหยุด"] = f"=COUNTIF(E$2:E${last_day_row}, A{r})"
        df_summary_excel.at[idx, "บ่าย"] = f"=COUNTIF(F$2:F${last_day_row}, A{r})"
        df_summary_excel.at[idx, "ดึก"] = f"=COUNTIF(G$2:G${last_day_row}, A{r})"
        df_summary_excel.at[idx, "รวมในเวลา"] = f"=SUM(C{r}:E{r})"
        df_summary_excel.at[idx, "รวมนอกเวลา (ได้ค่าเวร)"] = f"=SUM(F{r}:H{r})"
        df_summary_excel.at[idx, "รวมทั้งหมด"] = f"=I{r}+J{r}"

    total_row_idx = len(df_summary_excel)
    total_r = summary_data_start_row + total_row_idx

    df_summary_excel.loc[total_row_idx] = [
        "Total",
        "",
        f"=SUM(C{summary_data_start_row}:C{total_r-1})",
        f"=SUM(D{summary_data_start_row}:D{total_r-1})",
        f"=SUM(E{summary_data_start_row}:E{total_r-1})",
        f"=SUM(F{summary_data_start_row}:F{total_r-1})",
        f"=SUM(G{summary_data_start_row}:G{total_r-1})",
        f"=SUM(H{summary_data_start_row}:H{total_r-1})",
        f"=SUM(I{summary_data_start_row}:I{total_r-1})",
        f"=SUM(J{summary_data_start_row}:J{total_r-1})",
        f"=SUM(K{summary_data_start_row}:K{total_r-1})",
    ]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        styled_schedule.to_excel(writer, sheet_name="ตารางเวร", index=False)
        df_summary_excel.to_excel(writer, sheet_name="ตารางเวร", startrow=start_row_pandas, index=False)

    return buffer.getvalue()
