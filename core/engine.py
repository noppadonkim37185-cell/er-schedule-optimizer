from ortools.sat.python import cp_model
import pandas as pd
import calendar
import math

def generate_er_schedule(year, month, special_holidays, off_requests, on_requests=[], preferences={}):
    _, num_days = calendar.monthrange(year, month)
    days = range(1, num_days + 1)
    
    weekends = set(special_holidays)
    for d in days:
        if calendar.weekday(year, month, d) >= 5: 
            weekends.add(d)
    
    doc_names_list = ["นพดล", "สกล", "ธานินทร์", "สุจริต", "มุกดา", "หฤทัย", "จารุภา", "ใจประภัสส์", "กิตติยา"]
    num_doctors = len(doc_names_list)
    doctors = range(num_doctors)
    
    shifts = ['Trauma', 'Non-Trauma', 'Resus', 'Morning_Weekend', 'Afternoon', 'Night']
    num_shifts = len(shifts)
    
    shift_name_map = {
        "All": "หยุดทั้งวัน",
        "Morning": "เวรเช้า (ปรับตามวันธรรมดา/หยุด)",
        "Any": "เวรใดก็ได้",
        "Afternoon_Night": "เวรบ่ายและดึก",
        0: "เช้า: Trauma",
        1: "เช้า: Non-Trauma",
        2: "เช้า: Resus",
        3: "เช้า: วันหยุด",
        4: "บ่าย",
        5: "ดึก"
    }
    
    def try_solve(flex):
        model = cp_model.CpModel()
        x = {}
        for d in days:
            for s in range(num_shifts):
                for p in doctors:
                    x[(d, s, p)] = model.NewBoolVar(f'x_{d}_{s}_{p}')
                    
        assumptions = []
        request_literals = {}
        
        # 1. จัดการคำขอ Off เวร
        for i, (req_day, req_doc, req_shift) in enumerate(off_requests):
            req_var = model.NewBoolVar(f'off_req_{i}')
            assumptions.append(req_var)
            doc_name = doc_names_list[req_doc]
            s_name = shift_name_map.get(req_shift, str(req_shift))
            request_literals[req_var.Index()] = f"🛑 ขอหยุดเวร: {doc_name} วันที่ {req_day} [{s_name}]"
            
            if req_shift == "All":
                for s in range(num_shifts):
                    model.Add(x[(req_day, s, req_doc)] == 0).OnlyEnforceIf(req_var)
            elif req_shift == "Morning":
                if req_day in weekends:
                    model.Add(x[(req_day, 3, req_doc)] == 0).OnlyEnforceIf(req_var)
                else:
                    for s in [0, 1, 2]:
                        model.Add(x[(req_day, s, req_doc)] == 0).OnlyEnforceIf(req_var)
            elif req_shift == "Afternoon_Night":
                model.Add(x[(req_day, 4, req_doc)] == 0).OnlyEnforceIf(req_var)
                model.Add(x[(req_day, 5, req_doc)] == 0).OnlyEnforceIf(req_var)
            else:
                model.Add(x[(req_day, req_shift, req_doc)] == 0).OnlyEnforceIf(req_var)

        # 2. จัดการคำขอระบุวันทำงาน
        for i, (req_day, req_doc, req_shift) in enumerate(on_requests):
            req_var = model.NewBoolVar(f'on_req_{i}')
            assumptions.append(req_var)
            doc_name = doc_names_list[req_doc]
            s_name = shift_name_map.get(req_shift, str(req_shift))
            request_literals[req_var.Index()] = f"✅ ขอขึ้นเวร: {doc_name} วันที่ {req_day} [{s_name}]"

            if req_shift == "Any":
                model.Add(sum(x[(req_day, s, req_doc)] for s in range(num_shifts)) >= 1).OnlyEnforceIf(req_var)
            elif req_shift == "Morning":
                if req_day in weekends:
                    model.Add(x[(req_day, 3, req_doc)] == 1).OnlyEnforceIf(req_var)
                else:
                    model.Add(sum(x[(req_day, s, req_doc)] for s in [0, 1, 2]) == 1).OnlyEnforceIf(req_var)
            elif req_shift == "Afternoon_Night":
                model.Add(x[(req_day, 4, req_doc)] == 1).OnlyEnforceIf(req_var)
                model.Add(x[(req_day, 5, req_doc)] == 1).OnlyEnforceIf(req_var)
            else:
                model.Add(x[(req_day, req_shift, req_doc)] == 1).OnlyEnforceIf(req_var)

        model.AddAssumptions(assumptions)

        # 3. ความต้องการกำลังคน (Coverage)
        for d in days:
            if d not in weekends:
                model.AddExactlyOne(x[(d, 0, p)] for p in doctors)
                model.AddExactlyOne(x[(d, 1, p)] for p in doctors)
                model.AddExactlyOne(x[(d, 2, p)] for p in doctors)
                for p in doctors: model.Add(x[(d, 3, p)] == 0)
            else:
                for s in [0, 1, 2]:
                    for p in doctors: model.Add(x[(d, s, p)] == 0)
                model.AddExactlyOne(x[(d, 3, p)] for p in doctors)
                
            model.AddExactlyOne(x[(d, 4, p)] for p in doctors)
            model.AddExactlyOne(x[(d, 5, p)] for p in doctors)

        # 4. ข้อจำกัดเวลาพัก (Rest Times) & โปรไฟล์เฉพาะบุคคล
        for p in doctors:
            doc_name = doc_names_list[p]
            prefs = preferences.get(doc_name, {})
            no_night = prefs.get("no_night", False)
            no_consec_night = prefs.get("no_consec_night", False)
            no_aft_ngt_mon = prefs.get("no_aft_ngt_mon", False)
            no_aft_ngt_thu = prefs.get("no_aft_ngt_thu", False)
            no_resus_tue = prefs.get("no_resus_tue", False)
            no_resus_fri = prefs.get("no_resus_fri", False)
            no_aft_to_resus = prefs.get("no_aft_to_resus", False)
            no_resus = prefs.get("no_resus", False)
            max_shifts = prefs.get("max_shifts", 0)

            for d in days:
                morning_shifts = sum(x[(d, s, p)] for s in [0, 1, 2, 3])
                model.Add(morning_shifts <= 1)
                model.Add(morning_shifts + x[(d, 4, p)] <= 1)
                model.Add(x[(d, 4, p)] + x[(d, 5, p)] <= 1)
                model.Add(sum(x[(d, s, p)] for s in range(num_shifts)) <= 2)

                if d < num_days:
                    morning_shifts_next = sum(x[(d + 1, s, p)] for s in [0, 1, 2, 3])
                    model.Add(x[(d, 5, p)] + morning_shifts_next <= 1) 
                    model.Add(x[(d, 5, p)] + x[(d + 1, 4, p)] <= 1)    

            # --- กฎเฉพาะบุคคล (Personalized Rules) ---
            if no_night:
                for d in days: model.Add(x[(d, 5, p)] == 0)
            
            if no_consec_night:
                for d in range(1, num_days): model.Add(x[(d, 5, p)] + x[(d+1, 5, p)] <= 1) 
            else:
                for d in range(1, num_days - 1): model.Add(x[(d, 5, p)] + x[(d+1, 5, p)] + x[(d+2, 5, p)] <= 2)

            # งดบ่าย/ดึก วันจันทร์
            if no_aft_ngt_mon:
                for d in days:
                    if calendar.weekday(year, month, d) == 0:
                        model.Add(x[(d, 4, p)] == 0)
                        model.Add(x[(d, 5, p)] == 0)

            # งดบ่าย/ดึก วันพฤหัส
            if no_aft_ngt_thu:
                for d in days:
                    if calendar.weekday(year, month, d) == 3:
                        model.Add(x[(d, 4, p)] == 0)
                        model.Add(x[(d, 5, p)] == 0)

            # งด Resus วันอังคาร (เวรเช้าในเวลา)
            if no_resus_tue:
                for d in days:
                    if calendar.weekday(year, month, d) == 1 and d not in weekends:
                        model.Add(x[(d, 2, p)] == 0)

            # งด Resus วันศุกร์ (เวรเช้าในเวลา)
            if no_resus_fri:
                for d in days:
                    if calendar.weekday(year, month, d) == 4 and d not in weekends:
                        model.Add(x[(d, 2, p)] == 0)

            # ห้ามบ่าย ต่อ เช้า Resus ในวันถัดไป
            if no_aft_to_resus:
                for d in range(1, num_days):
                    if (d + 1) not in weekends: 
                        model.Add(x[(d, 4, p)] + x[(d+1, 2, p)] <= 1)

            # งดเวรเช้า Resus แบบถาวร
            if no_resus:
                for d in days:
                    if d not in weekends:
                        model.Add(x[(d, 2, p)] == 0)

            if max_shifts > 0:
                model.Add(sum(x[(d, s, p)] for d in days for s in range(num_shifts)) <= max_shifts)

        # 5. การเกลี่ยเวรและ AI Optimization
        total_wd = num_days - len(weekends)
        
        active_night_docs = [p for p in doctors if not preferences.get(doc_names_list[p], {}).get("no_night", False)]
        active_total_docs = [p for p in doctors if preferences.get(doc_names_list[p], {}).get("max_shifts", 0) == 0]
        
        num_night_docs = len(active_night_docs) if len(active_night_docs) > 0 else 1
        num_total_docs = len(active_total_docs) if len(active_total_docs) > 0 else 1

        avg_out_hours = (len(weekends) + (num_days * 2)) / num_total_docs
        avg_in_hours = (total_wd * 3) / num_total_docs
        avg_night = num_days / num_night_docs
        avg_afternoon = num_days / num_total_docs

        doc_out_vars, doc_in_vars, doc_ngt_vars, doc_aft_vars, doc_zone_diffs = [], [], [], [], []

        for p in doctors:
            doc_name = doc_names_list[p]
            prefs = preferences.get(doc_name, {})
            no_night = prefs.get("no_night", False)
            no_resus = prefs.get("no_resus", False)
            is_custom = prefs.get("max_shifts", 0) > 0

            out_var = model.NewIntVar(0, int(num_days*3), f'out_p{p}')
            model.Add(out_var == sum(x[(d, 3, p)] for d in days if d in weekends) + sum(x[(d, 4, p)] for d in days) + sum(x[(d, 5, p)] for d in days))
            in_var = model.NewIntVar(0, int(num_days*3), f'in_p{p}')
            model.Add(in_var == sum(x[(d, s, p)] for d in days if d not in weekends for s in [0, 1, 2]))
            ngt_var = model.NewIntVar(0, num_days, f'ngt_p{p}')
            model.Add(ngt_var == sum(x[(d, 5, p)] for d in days))
            aft_var = model.NewIntVar(0, num_days, f'aft_p{p}')
            model.Add(aft_var == sum(x[(d, 4, p)] for d in days))

            if not is_custom:
                doc_out_vars.append(out_var)
                doc_in_vars.append(in_var)
                doc_aft_vars.append(aft_var)
                
                model.Add(out_var >= max(0, math.floor(avg_out_hours) - (flex * 2)))
                model.Add(out_var <= math.ceil(avg_out_hours) + (flex * 2))
                model.Add(in_var >= max(0, math.floor(avg_in_hours) - (flex * 2)))
                model.Add(in_var <= math.ceil(avg_in_hours) + (flex * 2))

                t_var = model.NewIntVar(0, num_days, f't_p{p}')
                nt_var = model.NewIntVar(0, num_days, f'nt_p{p}')
                r_var = model.NewIntVar(0, num_days, f'r_p{p}')
                model.Add(t_var == sum(x[(d, 0, p)] for d in days if d not in weekends))
                model.Add(nt_var == sum(x[(d, 1, p)] for d in days if d not in weekends))
                model.Add(r_var == sum(x[(d, 2, p)] for d in days if d not in weekends))
                
                max_z = model.NewIntVar(0, num_days, f'max_z_{p}')
                min_z = model.NewIntVar(0, num_days, f'min_z_{p}')
                
                if no_resus:
                    model.AddMaxEquality(max_z, [t_var, nt_var])
                    model.AddMinEquality(min_z, [t_var, nt_var])
                else:
                    model.AddMaxEquality(max_z, [t_var, nt_var, r_var])
                    model.AddMinEquality(min_z, [t_var, nt_var, r_var])
                
                z_diff = model.NewIntVar(0, num_days, f'z_diff_{p}')
                model.Add(z_diff == max_z - min_z)
                doc_zone_diffs.append(z_diff)

            if not no_night and not is_custom:
                doc_ngt_vars.append(ngt_var)

        max_out = model.NewIntVar(0, int(num_days*3), 'max_out')
        min_out = model.NewIntVar(0, int(num_days*3), 'min_out')
        if doc_out_vars:
            model.AddMaxEquality(max_out, doc_out_vars)
            model.AddMinEquality(min_out, doc_out_vars)

        max_in = model.NewIntVar(0, int(num_days*3), 'max_in')
        min_in = model.NewIntVar(0, int(num_days*3), 'min_in')
        if doc_in_vars:
            model.AddMaxEquality(max_in, doc_in_vars)
            model.AddMinEquality(min_in, doc_in_vars)

        max_ngt = model.NewIntVar(0, num_days, 'max_ngt')
        min_ngt = model.NewIntVar(0, num_days, 'min_ngt')
        if doc_ngt_vars:
            model.AddMaxEquality(max_ngt, doc_ngt_vars)
            model.AddMinEquality(min_ngt, doc_ngt_vars)

        max_aft = model.NewIntVar(0, num_days, 'max_aft')
        min_aft = model.NewIntVar(0, num_days, 'min_aft')
        if doc_aft_vars:
            model.AddMaxEquality(max_aft, doc_aft_vars)
            model.AddMinEquality(min_aft, doc_aft_vars)

        total_z_diff = model.NewIntVar(0, num_days * num_doctors, 'total_z_diff')
        if doc_zone_diffs:
            model.Add(total_z_diff == sum(doc_zone_diffs))

        model.Minimize(
            (max_out - min_out) * 1000 +    
            (max_in - min_in) * 500 +       
            total_z_diff * 300 +            
            (max_ngt - min_ngt) * 200 +     
            (max_aft - min_aft) * 100       
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 20.0 
        status = solver.Solve(model)
        
        conflicts = []
        if status == cp_model.INFEASIBLE:
            core = solver.SufficientAssumptionsForInfeasibility()
            conflicts = [request_literals[c] for c in core if c in request_literals]

        return solver, x, status, conflicts

    best_solver = None
    best_x = None
    final_conflicts = []
    
    for attempt_flex in [2, 4, 6]:
        solver, x, status, conflicts = try_solve(attempt_flex)
        if status == cp_model.OPTIMAL:
            best_solver = solver
            best_x = x
            break 
        elif status == cp_model.FEASIBLE and best_solver is None:
            best_solver = solver
            best_x = x
            break 
        else:
            final_conflicts = conflicts 
            
    if best_solver is not None:
        schedule_data = []
        for d in days:
            row = {'วันที่': d}
            for idx, s_name in enumerate(shifts):
                assigned_doc = ""
                for p in doctors:
                    if best_solver.Value(best_x[(d, idx, p)]): assigned_doc = doc_names_list[p]
                row[s_name] = assigned_doc
            schedule_data.append(row)
            
        summary_data = []
        for p in doctors:
            row = {'ชื่อแพทย์': doc_names_list[p]}
            t_trauma = sum(best_solver.Value(best_x[(d, 0, p)]) for d in days)
            t_nontrauma = sum(best_solver.Value(best_x[(d, 1, p)]) for d in days)
            t_resus = sum(best_solver.Value(best_x[(d, 2, p)]) for d in days)
            t_we_morn = sum(best_solver.Value(best_x[(d, 3, p)]) for d in days)
            t_aft = sum(best_solver.Value(best_x[(d, 4, p)]) for d in days)
            t_night = sum(best_solver.Value(best_x[(d, 5, p)]) for d in days)
            
            we_shifts_worked = sum(best_solver.Value(best_x[(d, s, p)]) for d in weekends for s in [3, 4, 5])
            we_days_off = len(weekends) - we_shifts_worked
            
            row['วันหยุดที่ได้พัก (วัน)'] = we_days_off
            row['Trauma'] = t_trauma
            row['Non-Trauma'] = t_nontrauma
            row['Resus'] = t_resus
            row['เช้าวันหยุด'] = t_we_morn
            row['บ่าย'] = t_aft
            row['ดึก'] = t_night
            
            row['รวมในเวลา'] = t_trauma + t_nontrauma + t_resus
            row['รวมนอกเวลา (ได้ค่าเวร)'] = t_we_morn + t_aft + t_night
            row['รวมทั้งหมด'] = row['รวมในเวลา'] + row['รวมนอกเวลา (ได้ค่าเวร)']
            
            summary_data.append(row)
            
        return pd.DataFrame(schedule_data), pd.DataFrame(summary_data), []
    else:
        return None, None, final_conflicts