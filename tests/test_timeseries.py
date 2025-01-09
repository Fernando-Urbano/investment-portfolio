import pytest
import datetime
import pandas as pd
from app.models import TimeSeries, DataPoint, Asset, TimeSeriesType
from app import db  # Import db for database operations


def test_from_dataframe_single_column(
    app,
    sample_df_single_column,
    create_asset_and_type
):
    """
    Test that from_dataframe handles a single-column DataFrame and returns one TimeSeries.
    """
    asset_id, tstype_id = create_asset_and_type

    with app.app_context():
        # Re-query Asset and TimeSeriesType to ensure they're attached to the current session
        asset = db.session.get(Asset, asset_id)
        tstype = db.session.get(TimeSeriesType, tstype_id)

        ts_obj = TimeSeries.from_dataframe(
            df=sample_df_single_column,
            asset=asset,
            time_series_type=tstype
        )

        # Expect a single TimeSeries (not a list)
        assert isinstance(ts_obj, TimeSeries), "Should return a single TimeSeries object."
        assert ts_obj.name == "price", "TimeSeries name should match the DataFrame column name."
        assert len(ts_obj.data_points) == 252, "TimeSeries should have 252 DataPoints."

        # Check the data points
        for i, dp in enumerate(ts_obj.data_points):
            expected_date = sample_df_single_column.index[i].date()
            expected_value = sample_df_single_column["price"].iloc[i]
            assert dp.date.date() == expected_date, f"Expected date {expected_date}, got {dp.date}"
            assert dp.value == expected_value, f"Expected value {expected_value}, got {dp.value}"


def test_from_dataframe_single_column_with_asset_id_and_tstype_id(
    app,
    sample_df_single_column,
    create_asset_and_type
):
    """
    Test that from_dataframe handles a single-column DataFrame and returns one TimeSeries.
    """
    asset_id, tstype_id = create_asset_and_type

    with app.app_context():
        ts_obj = TimeSeries.from_dataframe(
            df=sample_df_single_column,
            asset=asset_id,
            time_series_type=tstype_id
        )

        # Expect a single TimeSeries (not a list)
        assert isinstance(ts_obj, TimeSeries), "Should return a single TimeSeries object."
        assert ts_obj.name == "price", "TimeSeries name should match the DataFrame column name."
        assert len(ts_obj.data_points) == 252, "TimeSeries should have 252 DataPoints."

        # Check the data points
        for i, dp in enumerate(ts_obj.data_points):
            expected_date = sample_df_single_column.index[i].date()
            expected_value = sample_df_single_column["price"].iloc[i]
            assert dp.date.date() == expected_date, f"Expected date {expected_date}, got {dp.date}"
            assert dp.value == expected_value, f"Expected value {expected_value}, got {dp.value}"


def test_from_dataframe_single_column_with_date_as_column(
    app,
    sample_df_single_column,
    create_asset_and_type
):
    """
    Test that from_dataframe handles a single-column DataFrame and returns one TimeSeries.
    """
    asset_id, tstype_id = create_asset_and_type

    sample_df = sample_df_single_column
    sample_df["Datetime"] = sample_df.index
    sample_df = sample_df.reset_index(drop=True)

    with app.app_context():
        ts_obj = TimeSeries.from_dataframe(
            df=sample_df_single_column,
            asset=asset_id,
            time_series_type=tstype_id,
            date_column="Datetime"
        )

        # Expect a single TimeSeries (not a list)
        assert isinstance(ts_obj, TimeSeries), "Should return a single TimeSeries object."
        assert ts_obj.name == "price", "TimeSeries name should match the DataFrame column name."
        assert len(ts_obj.data_points) == 252, "TimeSeries should have 252 DataPoints."

        # Check the data points
        for i, dp in enumerate(ts_obj.data_points):
            expected_date = sample_df_single_column.index[i].date()
            expected_value = sample_df_single_column["price"].iloc[i]
            assert dp.date.date() == expected_date, f"Expected date {expected_date}, got {dp.date}"
            assert dp.value == expected_value, f"Expected value {expected_value}, got {dp.value}"


def test_from_dataframe_multi_column(
    app,
    sample_df_multiple_columns,
    create_asset_and_type
):
    """
    Test that from_dataframe handles a multi-column DataFrame and returns multiple TimeSeries.
    """
    asset_id, tstype_id = create_asset_and_type
    num_columns = len(sample_df_multiple_columns.columns)

    with app.app_context():
        ts_objs = TimeSeries.from_dataframe(
            df=sample_df_multiple_columns,
            asset=asset_id,
            time_series_type=tstype_id
        )

        # Expect a list of TimeSeries objects
        assert isinstance(ts_objs, list), "Should return a list of TimeSeries objects."
        assert len(ts_objs) == num_columns, "Should return one TimeSeries per column."
        assert all(isinstance(ts, TimeSeries) for ts in ts_objs), "All elements should be TimeSeries objects."
        assert ts_objs[0].name == "price", "First TimeSeries name should match the first DataFrame column name."


def test_to_dataframe_multi_column(
    app,
    sample_df_multiple_columns,
    create_asset_and_type
):
    """
    Test that from_dataframe handles a multi-column DataFrame and returns multiple TimeSeries.
    """
    asset_id, tstype_id = create_asset_and_type

    with app.app_context():
        ts_objs = TimeSeries.from_dataframe(
            df=sample_df_multiple_columns,
            asset=asset_id,
            time_series_type=tstype_id
        )
        for ts_obj in ts_objs:
            ts_dataframe = ts_obj.to_dataframe()
            assert isinstance(ts_dataframe, pd.DataFrame), "Should return a DataFrame."
            assert len(ts_dataframe.index) == len(sample_df_multiple_columns.index), "DataFrame index length should match input length."


def test_to_dataframe_single_column(
    app,
    sample_df_single_column,
    create_asset_and_type
):
    """
    Test that from_dataframe handles a single-column DataFrame and returns one TimeSeries.
    """
    asset_id, tstype_id = create_asset_and_type

    with app.app_context():
        ts_obj = TimeSeries.from_dataframe(
            df=sample_df_single_column,
            asset=asset_id,
            time_series_type=tstype_id
        )

        ts_dataframe = ts_obj.to_dataframe()
        assert isinstance(ts_dataframe, pd.DataFrame), "Should return a DataFrame."
        assert len(ts_dataframe.index) == len(sample_df_single_column.index), "DataFrame index length should match input length."
        assert list(ts_dataframe.columns) == ["price"], "DataFrame columns should match the input DataFrame."
        for i in range(5):
            assert ts_dataframe.iloc[i, 0] == sample_df_single_column.iloc[i, 0], "DataFrame values should match the input DataFrame."


    