"""FastAPI backend for DC-Pickaxe Analytics."""

from __future__ import annotations
import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sheets import reader

app = FastAPI(title="DC-Pickaxe Analytics API", version="1.0.0")

_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _parse_field(value):
    if value is None:
        return None
    v = str(value).strip()
    if v in ("", "nan", "None", "[]", "{}"):
        return None
    try:
        return json.loads(v)
    except Exception:
        pass
    try:
        return ast.literal_eval(v)
    except Exception:
        return v


def _clean_daily(row: dict) -> dict:
    return {
        **row,
        "keywords":         _parse_field(row.get("keywords")),
        "top_posts":        _parse_field(row.get("top_posts")),
        "has_issue":        bool(int(row.get("has_issue", 0) or 0)),
        "is_borderline":    bool(int(row.get("is_borderline", 0) or 0)),
        "issue_score":      int(row.get("issue_score", 0) or 0),
        "posts_total":      int(row.get("posts_total", 0) or 0),
        "avg_7d":           float(row.get("avg_7d", 0) or 0),
        "avg_same_weekday": float(row.get("avg_same_weekday", 0) or 0),
        "momentum_avg":     float(row.get("momentum_avg", 0) or 0),
    }


def _clean_weekly(row: dict) -> dict:
    return {
        **row,
        "keywords":    _parse_field(row.get("keywords")),
        "top_posts":   _parse_field(row.get("top_posts")),
        "daily_counts": _parse_field(row.get("daily_counts")),
        "total_posts": int(row.get("total_posts", 0) or 0),
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/calendar")
def calendar():
    return {
        "issue_dates":  reader.get_daily_issue_dates(),
        "weekly_dates": reader.get_weekly_gallery_list(),
    }


@app.get("/api/daily/latest")
def daily_latest():
    return reader.get_latest_daily_issue_info() or {}


@app.get("/api/daily/dates")
def daily_dates():
    return reader.get_daily_issue_dates()


@app.get("/api/daily/{date}")
def daily_by_date(date: str):
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(status_code=400, detail="Invalid date format")
    df = reader.get_daily_issues_by_date(date)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for date")
    return [_clean_daily(r) for r in df.to_dict("records")]


@app.get("/api/weekly/latest")
def weekly_latest():
    return reader.get_latest_weekly_info() or {}


@app.get("/api/weekly/list")
def weekly_list():
    return reader.get_weekly_gallery_list()


@app.get("/api/weekly/{week_start}")
def weekly_by_week(week_start: str):
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", week_start):
        raise HTTPException(status_code=400, detail="Invalid date format")
    galleries_df = reader.get_weekly_galleries(week_start)
    overall      = reader.get_weekly_overall(week_start)
    if galleries_df.empty:
        raise HTTPException(status_code=404, detail="No data for week")
    return {
        "galleries": [_clean_weekly(r) for r in galleries_df.to_dict("records")],
        "overall":   overall or {},
    }
