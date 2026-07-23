"""ONDA Riparian Index Explorer - Streamlit dashboard.

NOTE: Streamlit is NOT part of the pixi env because its pydeck dependency
conflicts with the modern ipywidgets used by geemap/leafmap. To run this
dashboard, create a separate lightweight venv:

    python -m venv .venv-dashboard
    .venv-dashboard\Scripts\Activate.ps1
    pip install streamlit pandas matplotlib pymannkendall ruptures
    pip install -e .
    streamlit run dashboard/app.py

Or skip it entirely - the notebooks are the primary deliverable.
"""
