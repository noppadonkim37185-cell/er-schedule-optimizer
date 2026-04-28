# ER Schedule Optimizer

## Project Overview

This is a browser-based Streamlit application for creating monthly ER doctor schedules.

The project has been refactored into a deployment-ready structure while preserving the original scheduling engine behavior.

## What The App Does

- Select year and month.
- Add special holidays.
- Record doctor OFF requests.
- Record doctor ON requests.
- Configure doctor scheduling preferences.
- Generate an ER monthly schedule with OR-Tools.
- Show workload summaries.
- Export the schedule and summary to Excel with the same formulas and output meaning as the original app.

## Project Structure

```text
project_root/
  app/
    __init__.py
    config.py
    constants.py
    services/
      __init__.py
      scheduler_service.py
      excel_export.py
    ui/
      __init__.py
      streamlit_app.py
    utils/
      __init__.py
      state.py
  core/
    __init__.py
    engine.py
  app.py
  requirements.txt
  README.md
  Dockerfile
  .dockerignore
  .gitignore
  run_local.bat
  run_local.sh
```

## Important Solver Note

The scheduling logic is preserved in `core/engine.py`.

Do not edit `core/engine.py` unless you intentionally need to change the solver rules. The Streamlit UI and deployment helpers are separated from the engine so normal UI changes can happen without changing OR-Tools behavior.

## Local Setup

```bash
python3 -m pip install -r requirements.txt
```

## Running On Windows

```bat
run_local.bat
```

Or run directly:

```bat
python -m streamlit run app.py
```

## Running On Mac/Linux

```bash
chmod +x run_local.sh
./run_local.sh
```

Or run directly:

```bash
python3 -m streamlit run app.py
```

## Running With Docker

Build the image:

```bash
docker build -t er-schedule-optimizer .
```

Run the container:

```bash
docker run --rm -p 8501:8501 er-schedule-optimizer
```

Open:

```text
http://localhost:8501
```

## Troubleshooting

- If Streamlit is not found, install dependencies again with `python3 -m pip install -r requirements.txt`.
- If OR-Tools installation fails, confirm you are using a supported Python version.
- If no feasible schedule is found, review OFF requests, ON requests, and doctor profile constraints.
- If Docker cannot access the app, confirm port `8501` is not already in use.

## Which Files To Edit

- UI and labels: `app/ui/streamlit_app.py`
- Doctor names, shift labels, reusable constants: `app/constants.py`
- Excel export helper: `app/services/excel_export.py`
- Thin solver call wrapper: `app/services/scheduler_service.py`
- Solver logic and scheduling rules: `core/engine.py`
# er-schedule-optimizer
