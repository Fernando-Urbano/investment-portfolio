from app import db
import pandas as pd
from sqlalchemy.sql import func
import datetime
import re

class BaseModel(db.Model):
    __abstract__ = True

    def save(self, session=None, commit=True):
        """
        Saves the current instance to the database, ensuring any dependent objects are also saved.
        session (db.session): The SQLAlchemy session to use. If None, uses db.session.
        commit (bool): Whether or not to commit immediately.
        """
        if session is None:
            session = db.session

        self._save_dependencies(session)

        session.add(self)

        if commit:
            session.commit()

    def _save_dependencies(self, session):
        """
        Override this in child classes to save any dependencies (parents or children).
        Default implementation does nothing.
        """
        pass


class Asset(BaseModel):
    __tablename__ = 'asset'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    is_tradable = db.Column(db.Boolean, default=False)
    time_series = db.relationship('TimeSeries', backref='asset', lazy=True)

    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<Asset {self.name}>'


class TimeSeriesType(BaseModel):
    __tablename__ = 'time_series_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    time_series = db.relationship('TimeSeries', backref='time_series_type', lazy=True)

    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<TimeSeriesType {self.name}>'
    

class TimeSeries(BaseModel):
    __tablename__ = 'time_series'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('time_series_type.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    data_points = db.relationship('DataPoint', backref='time_series', lazy=True)

    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<TimeSeries {self.name}>'

    def _save_dependencies(self, session):
        """
        Ensures the related TimeSeriesType, Asset, and DataPoint objects are also saved.
        """
        # Save the parent TimeSeriesType if it's new or modified
        if self.time_series_type:
            session.add(self.time_series_type)

        # Save the parent Asset if it's new or modified
        if self.asset:
            session.add(self.asset)

        # Save child DataPoints
        for dp in self.data_points:
            session.add(dp)


    def to_dataframe(
            self,
            only_most_recent_per_date=True,
            filter_date_release_smaller_or_equal_to=None,
            include_date_release=False,
            include_date_create=False
        ):
        """
        Returns the TimeSeries data as a pandas DataFrame.
        """
        import pandas as pd

        data = {
            'date': [dp.date for dp in self.data_points],
            'value': [dp.value for dp in self.data_points],
            'date_create': [dp.date_create for dp in self.data_points],
            'date_release': [dp.date_release for dp in self.data_points]
        }
        ts_dataframe = (
            pd.DataFrame(data)
            .sort_values(['date', 'date_release', 'date_create'])
        )
        if only_most_recent_per_date:
            ts_dataframe = ts_dataframe.drop_duplicates(subset=['date'])
        ts_dataframe = (
            ts_dataframe
            .set_index('date')
            .rename({'value': self.name}, axis=1)
        )
        if filter_date_release_smaller_or_equal_to is not None:
            if isinstance(filter_date_release_smaller_or_equal_to, str):
                try:
                    filter_date = pd.to_datetime(filter_date_release_smaller_or_equal_to)
                except ValueError:
                    raise ValueError("filter_date_release_smaller_or_equal_to must be a valid date string.")
            elif not isinstance(filter_date_release_smaller_or_equal_to, (datetime.datetime, datetime.date)):
                raise ValueError("filter_date_release_smaller_or_equal_to must be a valid date string.")
            else:
                filter_date = filter_date_release_smaller_or_equal_to
            ts_dataframe = ts_dataframe[ts_dataframe['date_release'] <= filter_date]
        
        if not include_date_release:
            ts_dataframe = ts_dataframe.drop(columns=['date_release'])
        if not include_date_create:
            ts_dataframe = ts_dataframe.drop(columns=['date_create'])
        return ts_dataframe
        

    @classmethod
    def from_dataframe(
        cls,
        df,
        asset=None,
        time_series_type=None,
        name=None,
        description=None,
        date_column=None
    ):
        """
        Creates one or more TimeSeries objects from a pandas DataFrame without saving to the database.

        Returns
        -------
        TimeSeries or List[TimeSeries]
            A single TimeSeries if exactly one column is processed, or a list of multiple TimeSeries objects.
        """
        import pandas as pd

        if date_column is not None:
            if date_column not in df.columns:
                raise ValueError(f"Date column '{date_column}' not found in DataFrame.")
            df = df.set_index(date_column)

        if 'date' in [c.lower() for c in df.columns.tolist()]:
            df = df.set_index('date')
        try:
            df.index = pd.to_datetime(df.index)
        except ValueError:
            raise ValueError("The DataFrame must have a datetime index or specify a date_column.")
        df.index.name = 'date'

        if len(df.columns) == 1:
            if name is None:
                name = df.columns[0]

            if asset is None:
                raise ValueError("Asset must be provided for DataFrame")
            
            if isinstance(description, list):
                description = description[0]

            return cls.build_time_series_object(
                df.iloc[:, 0].values,
                df.index,
                name,
                asset,
                time_series_type,
                description
            )
        else:
            if name is None:
                name = df.columns
            elif name and not isinstance(name, list):
                raise ValueError("Name must be a list if multiple columns are provided.")
            elif len(name) != len(df.columns):
                raise ValueError("Name list must match the number of columns in the DataFrame.")
            else:
                raise ValueError("Name must be provided as list")
            
            if asset is None:
                raise ValueError("Asset must be provided for DataFrame")
            elif isinstance(asset, (str, int)):
                asset = [asset] * len(df.columns)
            elif not isinstance(asset, list):
                raise ValueError("Asset must be provided as list, string, or id")
                
            if len(asset) != len(df.columns):
                raise ValueError("Asset list must match the number of columns in the DataFrame.")
            
            if isinstance(description, str) and description is not None:
                raise ValueError("Description must be a list if multiple columns are provided.")
            
            all_time_series = []
            for i, col in enumerate(df.columns):
                all_time_series.append(
                    cls.build_time_series_object(
                    df[col].values,
                    df.index,
                    name[i],
                    asset[i],
                    time_series_type,
                    description
                ))
            return all_time_series
        

    @classmethod
    def save_from_dataframe(cls,
        df,
        asset=None,
        time_series_type=None,
        name=None,
        description=None,
        date_column=None,
        value_columns=None,
    ):
        """
        Creates one or more TimeSeries objects from a pandas DataFrame and saves them to the database.

        Returns
        -------
        TimeSeries or List[TimeSeries]
            A single TimeSeries if exactly one column is processed, or a list of multiple TimeSeries objects.
        """
        time_series_objects = cls.from_dataframe(
            df,
            asset,
            time_series_type,
            name,
            description,
            date_column,
            value_columns
        )
        if isinstance(time_series_objects, list):
            for ts in time_series_objects:
                ts.save()
        else:
            time_series_objects.save()
        return True
    
        
    @classmethod
    def build_time_series_object(cls, values, dates, time_series_name, asset, time_series_type, description=None):
        """
        Build a TimeSeries object with DataPoint objects from provided values and dates.
        """
        from app.models import DataPoint

        data_points = []
        for i in range(len(values)):
            data_points.append(DataPoint(date=dates[i], value=values[i]))
        ts = cls(
            name=time_series_name,
            data_points=data_points
        )
        if description is not None:
            ts.description = description
        if isinstance(asset, Asset):
            ts.asset = asset
        else:
            ts.asset_id = asset
        if isinstance(time_series_type, TimeSeriesType):
            ts.time_series_type = time_series_type
        else:
            ts.type_id = time_series_type
        return ts


class DataPoint(BaseModel):
    __tablename__ = 'data_point'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    date_release = db.Column(db.Date, nullable=True)
    time_series_id = db.Column(db.Integer, db.ForeignKey('time_series.id'), nullable=False)

    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<DataPoint {self.date}: {self.value}>'

    def _save_dependencies(self, session):
        """
        Ensure the parent TimeSeries (and potentially its parent objects) are saved.
        """
        if self.time_series:
            # Make sure the parent TimeSeries saves its dependencies too.
            # This will also add the Asset, TimeSeriesType, and any other DataPoints.
            self.time_series._save_dependencies(session)
            session.add(self.time_series)