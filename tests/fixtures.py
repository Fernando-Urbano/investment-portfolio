import pytest
import random
import string
from app.models import Asset, TimeSeriesType, TimeSeries, DataPoint
import datetime
import pandas as pd
from app import db
import numpy as np

# tests/fixtures.py

@pytest.fixture
def create_asset_and_type(app):
    """
    Fixture to create an Asset and a TimeSeriesType for testing.
    Returns their IDs, rather than returning detached instances.
    """
    with app.app_context():
        # Create a TimeSeriesType
        tstype = TimeSeriesType(name="Price", description="Price Time Series")
        db.session.add(tstype)
        db.session.commit()

        # Create an Asset
        asset = Asset(name="AST", description="Test Asset", is_tradable=True)
        db.session.add(asset)
        db.session.commit()

        return asset.id, tstype.id

@pytest.fixture
def populate_test_db(app):
    """
    Fixture to populate the test database with initial data.
    Accepts parameters for the number of assets and data points per time series.
    """

    def _populate_test_db(num_assets=1, num_data_points=10, start_date=datetime.date(2020, 1, 1)):
        """
        Internal function to populate the test database.
        
        Args:
            num_assets (int): Number of assets to create.
            num_data_points (int): Number of data points per time series.
            start_date (date or str): Start date for generating data points.
        """

        # Convert `start_date` to a `datetime.date` object if it's a string
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        def generate_random_name(length=3):
            """Generate a random name with the specified length."""
            return ''.join(random.choices(string.ascii_uppercase, k=length))

        def create_data_points(time_series_id, num_points, start_date):
            """Create random data points for a given time series."""
            data_points = []
            for i in range(num_points):
                date = start_date + datetime.timedelta(days=i)
                value = round(random.uniform(1000.0, 5000.0), 2)  # Random value between 1000 and 5000

                # Randomly decide whether to assign a `date_release` or leave it as None
                if random.choice([True, False]):
                    date_release = date + datetime.timedelta(days=1)
                else:
                    date_release = None

                data_point = DataPoint(
                    date=date,
                    value=value,
                    date_release=date_release,
                    time_series_id=time_series_id
                )
                data_points.append(data_point)
            return data_points

        with app.app_context():
            # Set a fixed random seed for reproducibility
            random.seed(42)

            # Create a TimeSeriesType
            time_series_type = TimeSeriesType(name='Price', description='Price Time Series')
            db.session.add(time_series_type)
            db.session.commit()

            # Generate the specified number of assets and time series
            for _ in range(num_assets):
                # Create a random asset
                asset_name = generate_random_name()
                asset = Asset(
                    name=asset_name,
                    description=f"{asset_name} Description",
                    is_tradable=bool(random.getrandbits(1))
                )
                db.session.add(asset)
                db.session.commit()

                # Create a random time series for the asset
                time_series_name = generate_random_name()
                time_series = TimeSeries(
                    name=f"{asset_name} {time_series_name}",
                    type_id=time_series_type.id,
                    asset_id=asset.id
                )
                db.session.add(time_series)
                db.session.commit()

                # Create random data points for the time series
                data_points = create_data_points(time_series.id, num_data_points, start_date)
                db.session.add_all(data_points)
                db.session.commit()

    return _populate_test_db

@pytest.fixture
def sample_df_single_column():
    """
    Returns a single-column DataFrame (with a DateTimeIndex).
    """
    rng = np.random.default_rng(seed=42)
    returns = rng.normal(0.0001, 0.01, 252)
    prices = 100 * (1 + np.cumsum(returns))
    dates = pd.date_range("2025-01-01", periods=252, freq="D")
    return pd.DataFrame({"price": prices}, index=dates)

@pytest.fixture
def sample_df_multiple_columns():
    """
    Returns a multi-column DataFrame (with a DateTimeIndex).
    """
    rng = np.random.default_rng(seed=42)
    returns = rng.normal(0.0001, 0.01, 252)
    prices = 100 * (1 + np.cumsum(returns))
    volumes = rng.integers(1000, 10000, 252)
    dates = pd.date_range("2025-01-01", periods=252, freq="D")
    return pd.DataFrame({"price": prices, "volume": volumes}, index=dates)