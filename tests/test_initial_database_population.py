# tests/test_initial_population.py

import datetime
from app.models import Asset, TimeSeriesType, TimeSeries, DataPoint

def test_initial_population(populate_test_db):
    """
    Test the initial population of the test database by verifying the created entries.
    """
    # Verify that the entries were added correctly
    assert Asset.query.count() == 1, "There should be exactly one Asset."
    assert TimeSeriesType.query.count() == 1, "There should be exactly one TimeSeriesType."
    assert TimeSeries.query.count() == 1, "There should be exactly one TimeSeries."
    assert DataPoint.query.count() == 3, "There should be exactly three DataPoints."

    # Retrieve and check the Asset
    asset = Asset.query.first()
    assert asset.name == 'S&P 500', "Asset name should be 'S&P 500'."
    assert asset.description == 'Stock Market Index', "Asset description mismatch."
    assert asset.is_tradable is True, "Asset should be tradable."

    # Retrieve and check the TimeSeriesType
    time_series_type = TimeSeriesType.query.first()
    assert time_series_type.name == 'Price', "TimeSeriesType name should be 'Price'."
    assert time_series_type.description == 'Price Time Series', "TimeSeriesType description mismatch."

    # Retrieve and check the TimeSeries
    time_series = TimeSeries.query.first()
    assert time_series.name == 'S&P 500 Price', "TimeSeries name mismatch."
    assert time_series.type_id == time_series_type.id, "TimeSeries type_id mismatch."
    assert time_series.asset_id == asset.id, "TimeSeries asset_id mismatch."

    # Retrieve and check the DataPoints
    data_points = DataPoint.query.all()
    dp1 = DataPoint.query.filter_by(date=datetime.date(2024, 12, 25)).first()
    dp2 = DataPoint.query.filter_by(date=datetime.date(2024, 12, 26)).first()
    dp3 = DataPoint.query.filter_by(date=datetime.date(2024, 12, 27)).first()

    assert dp1.value == 4500.50, "DataPoint value mismatch."
    assert dp1.date_release == datetime.date(2024, 12, 26), "DataPoint date_release mismatch."

    assert dp2.value == 4550.75, "DataPoint value mismatch."
    assert dp2.date_release is None, "DataPoint date_release should be None."

    assert dp3.value == 4600.00, "DataPoint value mismatch."
    assert dp3.date_release == datetime.date(2024, 12, 28), "DataPoint date_release mismatch."