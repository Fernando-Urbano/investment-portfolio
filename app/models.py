# app/models.py

from app import db
import pandas as pd
from sqlalchemy.sql import func
import datetime
import re

# Association table for many-to-many relationship between SeriesGroup and SeriesBase
seriesgroup_seriesbase = db.Table(
    'seriesgroup_seriesbase',
    db.Column('seriesgroup_id', db.Integer, db.ForeignKey('series_group.id'), primary_key=True),
    db.Column('seriesbase_id', db.Integer, db.ForeignKey('series_base.id'), primary_key=True)
)

# Association table for many-to-many relationship between SeriesBase and Keyword
seriesbase_keyword = db.Table(
    'seriesbase_keyword',
    db.Column('seriesbase_id', db.Integer, db.ForeignKey('series_base.id'), primary_key=True),
    db.Column('keyword_id', db.Integer, db.ForeignKey('keyword.id'), primary_key=True)
)

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

class Keyword(BaseModel):
    __tablename__ = 'keyword'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Relationship to SeriesBase
    series = db.relationship(
        'SeriesBase',
        secondary=seriesbase_keyword,
        back_populates='keywords',
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<Keyword {self.word}>'

class SeriesBase(BaseModel):
    __tablename__ = 'series_base'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    type = db.Column(db.String(50))  # Discriminator column

    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(
        db.DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    def __init__(self, name, description=None, keywords=None, **kwargs):
        """
        Initializes a SeriesBase instance.

        Parameters:
        - name (str): The name of the series.
        - description (str, optional): A description of the series.
        - keywords (list of str, optional): A list of keyword strings to associate with the series.
        - **kwargs: Additional keyword arguments for other fields.
        """
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        if keywords:
            for keyword_word in keywords:
                self.add_keyword(keyword_word)

    # Many-to-Many relationship with Keyword
    keywords = db.relationship(
        'Keyword',
        secondary=seriesbase_keyword,
        back_populates='series',
        lazy='dynamic'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'series_base',
        'polymorphic_on': type,
        'with_polymorphic': '*'
    }

    def __repr__(self):
        return f'<SeriesBase {self.name}>'

    def add_keyword(self, keyword_word):
        """
        Adds a keyword to the series. Creates the keyword if it doesn't exist.
        """
        keyword = Keyword.query.filter_by(word=keyword_word).first()
        if not keyword:
            keyword = Keyword(word=keyword_word)
            db.session.add(keyword)
        if not self.keywords.filter_by(word=keyword_word).first():
            self.keywords.append(keyword)

    def remove_keyword(self, keyword_word):
        """
        Removes a keyword from the series.
        """
        keyword = Keyword.query.filter_by(word=keyword_word).first()
        if keyword and self.keywords.filter_by(word=keyword_word).first():
            self.keywords.remove(keyword)

class SeriesGroup(SeriesBase):
    __tablename__ = 'series_group'
    id = db.Column(db.Integer, db.ForeignKey('series_base.id'), primary_key=True)
    series_group_code = db.Column(db.String(5), nullable=False, unique=True)  # Renamed and kept unique

    # Self-referential relationship for nested SeriesGroups
    parent_id = db.Column(db.Integer, db.ForeignKey('series_group.id'), nullable=True)
    children = db.relationship(
        'SeriesGroup',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        foreign_keys=[parent_id]  # Explicitly specify foreign_keys
    )

    # Many-to-many relationship with SeriesBase (TimeSeries and SeriesGroup)
    series = db.relationship(
        'SeriesBase',
        secondary=seriesgroup_seriesbase,
        backref=db.backref('series_groups', lazy='dynamic'),
        lazy='dynamic'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'series_group',
    }

    def __repr__(self):
        return f'<SeriesGroup {self.name}>'

class TimeSeries(SeriesBase):
    __tablename__ = 'time_series'
    id = db.Column(db.Integer, db.ForeignKey('series_base.id'), primary_key=True)
    time_series_code = db.Column(db.String(10), nullable=False, unique=True)  # New unique field
    type_id = db.Column(db.Integer, db.ForeignKey('time_series_type.id'), nullable=False)
    time_frequency = db.Column(db.String(3), nullable=True, default='M')
    delta_type = db.Column(db.String(10), nullable=True, default='pct')

    data_points = db.relationship('DataPoint', backref='time_series', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'time_series',
    }

    def _save_dependencies(self, session):
        """
        Ensures the related TimeSeriesType and DataPoint objects are also saved.
        """
        # Save the parent TimeSeriesType if it's new or modified
        if self.time_series_type:
            session.add(self.time_series_type)

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
        series_groups=None,
        time_series_type=None,
        name=None,
        description=None,
        date_column=None,
        all_columns_have_same_series_groups=False
    ):
        """
        Creates one or more TimeSeries objects from a pandas DataFrame without saving to the database.

        Returns
        -------
        TimeSeries or List[TimeSeries]
            A single TimeSeries if exactly one column is processed, or a list of multiple TimeSeries objects.
        """
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

            # Allow series_groups to be optional
            if series_groups is not None:
                if isinstance(description, list):
                    description = description[0]
            else:
                if description is None:
                    description = ""
            
            return cls.build_time_series_object(
                df.iloc[:, 0].values,
                df.index,
                name,
                series_groups,  # Can be None
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
            
            # Allow series_groups to be optional
            if series_groups is not None:
                if isinstance(series_groups, (str, int, SeriesGroup)):
                    series_groups = [series_groups] * len(df.columns)
                elif not isinstance(series_groups, list):
                    raise ValueError("SeriesGroups must be provided as list, string, or SeriesGroup instances")
                    
                if len(series_groups) != len(df.columns):
                    if not all_columns_have_same_series_groups:
                        raise ValueError(
                            "SeriesGroups list must match the number of columns in the DataFrame or "
                            + "parameter 'all_columns_have_same_series_groups=True'."
                        )
            else:
                series_groups = [None] * len(df.columns)  # No groups associated

            if isinstance(description, str) and description is not None:
                raise ValueError("Description must be a list if multiple columns are provided.")
            
            if not all([g is None for g in series_groups]) and all_columns_have_same_series_groups:
                all_columns_have_same_series_groups = True
                col_series_groups = series_groups
            else:
                all_columns_have_same_series_groups = False


            all_columns_have_same_series_groups = (
                False if all([g is None for g in series_groups]) else all_columns_have_same_series_groups
            )

            all_time_series = []
            for i, col in enumerate(df.columns):
                if not all_columns_have_same_series_groups:
                    col_series_groups = series_groups[i]
                all_time_series.append(
                    cls.build_time_series_object(
                    df[col].values,
                    df.index,
                    name[i],
                    col_series_groups,
                    time_series_type,
                    description
                ))
            return all_time_series

    @classmethod
    def save_from_dataframe(cls,
        df,
        series_groups=None,
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
            series_groups,
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
    def build_time_series_object(cls, values, dates, time_series_name, series_groups, time_series_type, description=None):
        """
        Build a TimeSeries object with DataPoint objects from provided values and dates.
        """
        data_points = []
        for i in range(len(values)):
            data_points.append(DataPoint(date=dates[i], value=values[i]))
        ts = cls(
            name=time_series_name,
            data_points=data_points
        )
        if description is not None:
            ts.description = description
        if isinstance(time_series_type, TimeSeriesType):
            ts.time_series_type = time_series_type
        else:
            ts.type_id = time_series_type

        # Associate with SeriesGroups if provided
        if series_groups:
            if isinstance(series_groups, SeriesGroup):
                ts.series_groups.append(series_groups)
            elif isinstance(series_groups, list):
                for sg in series_groups:
                    if sg is not None:
                        ts.series_groups.append(sg)
            else:
                raise ValueError("series_groups must be a SeriesGroup instance, list of SeriesGroup instances, or None")

        return ts

class DataPoint(BaseModel):
    __tablename__ = 'data_point'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    date_release = db.Column(db.Date, nullable=True)
    time_series_id = db.Column(db.Integer, db.ForeignKey('time_series.id'), nullable=False)

    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(
        db.DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f'<DataPoint {self.date}: {self.value}>'

    def _save_dependencies(self, session):
        """
        Ensure the parent TimeSeries (and potentially its parent objects) are saved.
        """
        if self.time_series:
            # Make sure the parent TimeSeries saves its dependencies too.
            # This will also add the SeriesGroups and any other DataPoints.
            self.time_series._save_dependencies(session)
            session.add(self.time_series)

class TimeSeriesType(BaseModel):
    __tablename__ = 'time_series_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    time_series = db.relationship('TimeSeries', backref='time_series_type', lazy=True)

    date_create = db.Column(
        db.DateTime(timezone=True), server_default=func.now(),
        nullable=False
    )
    date_update = db.Column(
        db.DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    __mapper_args__ = {
        'polymorphic_identity': 'time_series_type',
    }

    def __repr__(self):
        return f'<TimeSeriesType {self.name}>'