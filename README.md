# ABVP Thane Mahanagar Karyalay Automation Tool

This is a local Streamlit app for the Karyalay Mantri workflow.

## Features

- Student grievance/help desk register
- Membership register and college-wise analytics
- Meeting minutes and meeting notice generator
- Formal letter / nivedan draft generator
- Inventory tracking with low-stock alerts
- Task tracker for follow-ups
- CSV export for all records
- Delete selected records or clear stored CSV data from the app

## Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The app stores records in CSV files inside the `data/` folder.
