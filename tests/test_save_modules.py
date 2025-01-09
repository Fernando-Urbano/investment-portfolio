import pytest
import datetime
from app import db
from app.models import Asset, TimeSeriesType, TimeSeries, DataPoint

def test_save_asset(app):
    """
    Test saving a standalone Asset to the database using the `save` method.
    """
    asset = Asset(name="AST", description="Test Asset", is_tradable=True)
    asset.save()  # or db.session.add(asset); db.session.commit()

    assert asset.id is not None, "Asset ID should be generated after saving."
    assert Asset.query.count() == 1, "Exactly one Asset should exist in the database."

    retrieved = Asset.query.first()
    assert retrieved.name == "AST", "Retrieved Asset name should match 'AST'."
    assert retrieved.is_tradable is True, "Asset should be marked as tradable."

def test_save_time_series_type(app):
    """
    Test saving a TimeSeriesType to the database using the `save` method.
    """
    tst = TimeSeriesType(name="Price", description="Price Time Series")
    tst.save()

    assert tst.id is not None, "TimeSeriesType ID should be set after saving."
    assert TimeSeriesType.query.count() == 1, "Exactly one TimeSeriesType should exist."

    retrieved = TimeSeriesType.query.first()
    assert retrieved.name == "Price", "Retrieved name should be 'Price'."

def test_save_time_series_with_dependencies(app):
    """
    Test saving a TimeSeries that depends on an Asset and a TimeSeriesType.
    Verifies the parent objects can be saved together if they're new.
    """
    asset = Asset(name="AST2", description="Second Asset", is_tradable=False)
    tstype = TimeSeriesType(name="Volume", description="Volume Time Series")

    ts = TimeSeries(
        name="TS-Test",
        asset=asset,
        time_series_type=tstype
    )
    # If you have a custom save method that cascades, this will save asset & tstype, too.
    ts.save()

    # Verify TimeSeries
    assert ts.id is not None, "TimeSeries ID should be set after saving."
    assert TimeSeries.query.count() == 1, "One TimeSeries should exist."

    # Verify Asset
    assert asset.id is not None, "Asset ID should be set after saving TimeSeries."
    assert Asset.query.count() == 1, "One Asset should exist."

    # Verify TimeSeriesType
    assert tstype.id is not None, "TimeSeriesType ID should be set after saving TimeSeries."
    assert TimeSeriesType.query.count() == 1, "One TimeSeriesType should exist."

def test_save_data_points_with_timeseries(app):
    """
    Test saving a TimeSeries along with multiple DataPoints.
    Ensures child DataPoints are also saved.
    """
    asset = Asset(name="AST3", description="Third Asset", is_tradable=True)
    tstype = TimeSeriesType(name="Price", description="Price Time Series")

    ts = TimeSeries(name="TS-DataPoints", asset=asset, time_series_type=tstype)

    dp1 = DataPoint(date=datetime.date(2025, 1, 10), value=4000.0)
    dp2 = DataPoint(date=datetime.date(2025, 1, 11), value=4050.5)
    ts.data_points.extend([dp1, dp2])

    ts.save()  # Should save ts, asset, tstype, and dp1/dp2

    # Verify
    assert TimeSeries.query.count() == 1, "One TimeSeries should be saved."
    assert DataPoint.query.count() == 2, "Two DataPoints should be saved."

    retrieved_ts = TimeSeries.query.first()
    assert len(retrieved_ts.data_points) == 2, "Retrieved TimeSeries should have 2 DataPoints."

def test_save_datapoint_alone_with_parents(app):
    """
    Test saving a single DataPoint that has a reference to a new TimeSeries,
    which references a new Asset and TimeSeriesType. All should be saved.
    """
    asset = Asset(name="AST4", description="Fourth Asset")
    tstype = TimeSeriesType(name="Bids", description="Bid Time Series")
    ts = TimeSeries(name="TS-Bids", asset=asset, time_series_type=tstype)

    dp = DataPoint(date=datetime.date(2025, 1, 12), value=5001.5, time_series=ts)
    dp.save()  # Should cascade and save dp, ts, asset, tstype

    assert dp.id is not None, "DataPoint should have an ID after saving."
    assert asset.id is not None, "Asset should be saved."
    assert tstype.id is not None, "TimeSeriesType should be saved."
    assert ts.id is not None, "TimeSeries should be saved."

    # Verify counts
    assert Asset.query.count() == 1, "Exactly one Asset should be in DB."
    assert TimeSeriesType.query.count() == 1, "Exactly one TimeSeriesType should be in DB."
    assert TimeSeries.query.count() == 1, "Exactly one TimeSeries should be in DB."
    assert DataPoint.query.count() == 1, "Exactly one DataPoint should be in DB."

def test_save_multiple_objects_in_one_session(app):
    """
    Test saving multiple objects in one transaction without committing until the end.
    """
    asset = Asset(name="AST5", description="Fifth Asset", is_tradable=False)
    tstype = TimeSeriesType(name="Spread", description="Spread Time Series")
    ts = TimeSeries(name="TS-Spread", asset=asset, time_series_type=tstype)
    dp = DataPoint(date=datetime.date(2025, 1, 13), value=3999.9, time_series=ts)

    # Manually pass commit=False to gather them in the session, then commit once
    asset.save(commit=False)
    tstype.save(commit=False)
    ts.save(commit=False)
    dp.save(commit=False)

    # Now commit explicitly
    db.session.commit()

    # Verify
    assert Asset.query.count() == 1, "Exactly one Asset should be saved."
    assert TimeSeriesType.query.count() == 1, "Exactly one TimeSeriesType should be saved."
    assert TimeSeries.query.count() == 1, "Exactly one TimeSeries should be saved."
    assert DataPoint.query.count() == 1, "Exactly one DataPoint should be saved."

    retrieved_dp = DataPoint.query.first()
    assert retrieved_dp.value == 3999.9, "DataPoint value should be as assigned."
    assert retrieved_dp.time_series.name == "TS-Spread", "DataPoint should link to the correct TimeSeries."


# tests/test_exception_cases.py

import pytest
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import TimeSeriesType, TimeSeries, Asset, DataPoint
import pandas as pd

def test_timeseries_type_duplicate_name_raises(app):
    """
    Verify that creating two TimeSeriesType objects with the same name
    (where name is unique) raises an IntegrityError.
    """
    # First TimeSeriesType
    tstype1 = TimeSeriesType(name="UniqueName", description="First Type")
    db.session.add(tstype1)
    db.session.commit()

    # Second TimeSeriesType with the same name
    tstype2 = TimeSeriesType(name="UniqueName", description="Second Type")
    db.session.add(tstype2)

    # Expect an IntegrityError upon commit
    with pytest.raises(IntegrityError):
        db.session.commit()

def test_timeseries_invalid_dataframe_raises(app):
    """
    Verify that TimeSeries.from_dataframe raises ValueError
    if the DataFrame doesn't have a proper date column/index.
    """
    # Create a minimal DataFrame that lacks a datetime column/index
    df = pd.DataFrame({
        "some_column": [1, 2, 3]
    })

    # Create required objects
    asset = Asset(name="AST", description="Asset for test", is_tradable=True)
    db.session.add(asset)
    db.session.commit()

    tstype = TimeSeriesType(name="Price", description="Price Time Series")
    db.session.add(tstype)
    db.session.commit()

    # Attempt to create a TimeSeries from a DataFrame with no date
    try:
        ts = TimeSeries.from_dataframe(
            df=df,
            time_series_type=tstype.id,
            asset=asset.id
            # Not passing date_column because we expect the index to be a datetime or raise ValueError
        )
        raise AssertionError("Expected ValueError for missing date column but got no exception")
    except ValueError:
        pass
    except AssertionError as e:
        raise e
    except Exception as e:
        raise AssertionError(f"Expected ValueError for missing date column but got exception of type {type(e)}")



if __name__ == "__main__":
    test_timeseries_invalid_dataframe_raises()