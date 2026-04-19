# Refund analytics dashboard

Operational dashboard for refund tracking with month-to-date comparisons, KPI cards, and filters by country and course track. Built for non-technical team access and deployed on Streamlit Cloud.

## Features

- MTD refund volume vs. prior month comparison
- KPI cards: total refunds, refund rate, average ticket
- Filters by country and course track
- Automated data refresh

## Stack

Python · Streamlit · pandas · plotly

## Structure

```
├── app.py           ← main dashboard
├── requirements.txt
└── README.md
```

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Live demo

Deployed on Streamlit Cloud — [[link here]](https://refund-dashboard-65rhzabonxgxygrryp2hnt.streamlit.app/)
