from app import db

class Asset(db.Model):
    __tablename__ = 'asset'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    is_tradable = db.Column(db.Boolean, default=False)
    time_series = db.relationship('TimeSeries', backref='asset', lazy=True)

    def __repr__(self):
        return f'<Asset {self.name}>'


class TimeSeriesType(db.Model):
    __tablename__ = 'time_series_type'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    time_series = db.relationship('TimeSeries', backref='time_series_type', lazy=True)

    def __repr__(self):
        return f'<TimeSeriesType {self.name}>'


class TimeSeries(db.Model):
    __tablename__ = 'time_series'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('time_series_type.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    data_points = db.relationship('DataPoint', backref='time_series', lazy=True)

    def __repr__(self):
        return f'<TimeSeries {self.name}>'


class DataPoint(db.Model):
    __tablename__ = 'data_point'  # Explicitly defining the table name
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    time_series_id = db.Column(db.Integer, db.ForeignKey('time_series.id'), nullable=False)

    def __repr__(self):
        return f'<DataPoint {self.date}: {self.value}>'