# tests/fixtures.py

import pytest
from app.models import Asset, TimeSeriesType, TimeSeries, DataPoint
import datetime
from app import db

@pytest.fixture
def populate_test_db(app):
    """
    Fixture to populate the test database with initial data.
    """
    with app.app_context():
        # Create a TimeSeriesType
        price_type = TimeSeriesType(name='Price', description='Price Time Series')
        db.session.add(price_type)
        db.session.commit()

        # Create an Asset
        asset = Asset(name='S&P 500', description='Stock Market Index', is_tradable=True)
        db.session.add(asset)
        db.session.commit()

        # Create a TimeSeries
        time_series = TimeSeries(name='S&P 500 Price', type_id=price_type.id, asset_id=asset.id)
        db.session.add(time_series)
        db.session.commit()

        # Create multiple DataPoints
        data_points = [
            DataPoint(
                date=datetime.date(2024, 12, 25),
                value=4500.50,
                date_release=datetime.date(2024, 12, 26),
                time_series_id=time_series.id
            ),
            DataPoint(
                date=datetime.date(2024, 12, 26),
                value=4550.75,
                date_release=None,  # Allows NULL
                time_series_id=time_series.id
            ),
            DataPoint(
                date=datetime.date(2024, 12, 27),
                value=4600.00,
                date_release=datetime.date(2024, 12, 28),
                time_series_id=time_series.id
            ),
        ]
        db.session.add_all(data_points)
        db.session.commit()

        yield

        # Teardown is handled by the `app` fixture's teardown