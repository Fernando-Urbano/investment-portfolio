from app import db
from sqlalchemy.sql import func


class Asset(db.Model):
    __tablename__ = 'asset'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    is_tradable = db.Column(db.Boolean, default=False)
    time_series = db.relationship('TimeSeries', backref='asset', lazy=True)

    # Timestamp fields
    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<Asset {self.name}>'


class TimeSeriesType(db.Model):
    __tablename__ = 'time_series_type'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    description = db.Column(db.String(200))
    time_series = db.relationship('TimeSeries', backref='time_series_type', lazy=True)

    # Timestamp fields
    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<TimeSeriesType {self.name}>'


class TimeSeries(db.Model):
    __tablename__ = 'time_series'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('time_series_type.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    data_points = db.relationship('DataPoint', backref='time_series', lazy=True)

    # Timestamp fields
    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<TimeSeries {self.name}>'


class DataPoint(db.Model):
    __tablename__ = 'data_point'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    date_release = db.Column(db.Date, nullable=True)  # New field added
    time_series_id = db.Column(db.Integer, db.ForeignKey('time_series.id'), nullable=False)

    # Timestamp fields
    date_create = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_update = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<DataPoint {self.date}: {self.value}>'