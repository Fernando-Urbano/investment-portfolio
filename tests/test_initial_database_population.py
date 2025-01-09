# tests/test_initial_population.py

from app.models import Asset, TimeSeriesType, TimeSeries, DataPoint
import datetime

def test_initial_population(populate_test_db):
    """
    Test the initial population of the test database by verifying the created entries.
    """
    # Populate the database with 3 assets and 5 data points per time series
    populate_test_db(num_assets=3, num_data_points=5, start_date="2024-01-01")

    # Verify the number of entries created
    assert Asset.query.count() == 3, "There should be exactly 3 Assets."
    assert TimeSeriesType.query.count() == 1, "There should be exactly one TimeSeriesType."
    assert TimeSeries.query.count() == 3, "Each Asset should have exactly one TimeSeries."
    assert DataPoint.query.count() == 15, "Each TimeSeries should have 5 DataPoints."

    # Retrieve and check the Assets
    for asset in Asset.query.all():
        assert len(asset.name) == 3, f"Asset name '{asset.name}' should have exactly three characters."
        assert asset.description.endswith("Description"), f"Asset description mismatch for '{asset.name}'."
        assert isinstance(asset.is_tradable, bool), f"Asset '{asset.name}' should have a boolean value for 'is_tradable'."

    # Retrieve and check the TimeSeriesType
    time_series_type = TimeSeriesType.query.first()
    assert time_series_type.name == 'Price', "TimeSeriesType name should be 'Price'."
    assert time_series_type.description == 'Price Time Series', "TimeSeriesType description mismatch."

    # Retrieve and check the TimeSeries and their DataPoints
    for time_series in TimeSeries.query.all():
        assert len(time_series.name) > 0, "TimeSeries name should not be empty."
        assert time_series.type_id == time_series_type.id, "TimeSeries type_id mismatch."
        assert time_series.asset_id in [asset.id for asset in Asset.query.all()], "TimeSeries asset_id mismatch."

        data_points = time_series.data_points
        assert len(data_points) == 5, f"TimeSeries '{time_series.name}' should have exactly 5 DataPoints."

        # Verify the DataPoints
        start_date = datetime.date(2024, 1, 1)
        for i, dp in enumerate(data_points):
            expected_date = start_date + datetime.timedelta(days=i)
            assert dp.date == expected_date, f"DataPoint date mismatch: expected {expected_date}, got {dp.date}."
            assert isinstance(dp.value, float), "DataPoint 'value' should be a float."
            assert dp.time_series_id == time_series.id, f"DataPoint time_series_id mismatch for {dp}."

            # Check `date_release` conditionally
            if dp.date_release:
                assert dp.date_release == dp.date + datetime.timedelta(days=1), (
                    f"DataPoint 'date_release' mismatch: expected {dp.date + datetime.timedelta(days=1)}, got {dp.date_release}."
                )