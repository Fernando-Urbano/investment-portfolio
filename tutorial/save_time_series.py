# Import standard libraries
import sys
import os
import pandas as pd

# Import Flask and SQLAlchemy-related modules
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Determine the current working directory (where the notebook is located)
current_dir = os.getcwd()

# Navigate up one level to reach the project root
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))

# Add the project root to sys.path if it's not already there
if project_root not in sys.path:
    sys.path.append(project_root)

# Now, import your Flask app's create_app function and db instance
from app import create_app, db
from app.utils import create_returns_df

# Import your models
from app.models import SeriesGroup, TimeSeriesType, TimeSeries, Keyword, DataPoint
from app.series import SeriesSearcher

# Your existing import statements...

# Create the Flask application using the factory function
app = create_app('development')  # Ensure 'development' uses the correct configuration

# Push the application context to allow database operations
app_context = app.app_context()
app_context.push()

# Enable foreign key constraints in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Create the DataFrame
df = create_returns_df()

# Debug: Check the DataFrame
print("DataFrame Head:")
print(df.head())

# Fetch existing TimeSeries from the database based on codes
existing_codes = list(df.columns)
existing_ts_list = TimeSeries.query.filter(TimeSeries.time_series_code.in_(existing_codes)).all()

# Add the new keyword 'GGG' to each existing TimeSeries
for ts in existing_ts_list:
    ts.add_keyword('GGG')  # This modifies ts.keywords and schedules the keyword for addition

# Save all changes in bulk without individual commits
TimeSeries.save_all(existing_ts_list, commit=True)

# Debug: Verify that keywords are added
for ts in existing_ts_list:
    print(f"TimeSeries ID: {ts.id}, Name: {ts.name}, Keywords: {[kw.word for kw in ts.keywords]}")