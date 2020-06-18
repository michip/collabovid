import csv
from datetime import datetime, timedelta
from functools import total_ordering
from timeit import default_timer as timer

from sqlalchemy import and_, Column, create_engine, Date, Float, ForeignKey, func, Integer, or_, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class TimeZone(Base):
    __tablename__ = 'timezone'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    locations = relationship('Location', backref='timezone', order_by='Location.id')


@total_ordering
class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    ascii_name = Column(String, nullable=False, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    feature_class = Column(String)
    feature_code = Column(String)
    country_code = Column(String)
    cc2 = Column(String)
    admin1_code = Column(String)
    admin2_code = Column(String)
    admin3_code = Column(String)
    admin4_code = Column(String)
    population = Column(Integer)
    elevation = Column(Integer)
    dem = Column(Integer)
    timezone_id = Column(Integer, ForeignKey('timezone.id'))
    modification_date = Column(Date)

    aliases = relationship('Alias', backref='location', order_by='Alias.id')

    @property
    def feature_label(self):
        return f'{self.feature_class}.{self.feature_code}'

    @property
    def feature_value(self):
        hierarchy = [
            'A.PCL', 'P.PPLC', 'A.ADM1', 'A.ADM2', 'A.ADM3', 'A.ADM4', 'A.ADM5', 'A', 'P.PPL', 'P', '',
        ]

        return len(hierarchy) - 1 - next(
            (idx for idx in range(len(hierarchy)) if self.feature_label.startswith(hierarchy[idx])), -1
        )

    def __lt__(self, other):
        if self.feature_value != other.feature_value:
            return self.feature_value < other.feature_value
        return self.population < other.population


class Alias(Base):
    __tablename__ = 'alias'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=False, nullable=False, index=True)
    location_id = Column(Integer, ForeignKey('location.id'), index=True)


class GeonamesDB:
    class RecordNotFound(LookupError):
        def __init__(self, search_term):
            self.search_term = search_term

        def __str__(self):
            return f"'{self.search_term}' not found in geonames database"

        def __repr__(self):
            return str(self)

    def __init__(self, path):
        self._connection_string = f'sqlite:///{path}'
        self.session = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()

    def connect(self):
        engine = create_engine(self._connection_string, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def close_session(self):
        if self.session:
            self.session.close()

    @property
    def timezones(self):
        return self.session.query(TimeZone)

    @property
    def locations(self):
        return self.session.query(Location)

    @property
    def aliases(self):
        return self.session.query(Alias)

    def search_country(self, country_code):
        return self.locations.filter(
            Location.country_code == country_code,
            Location.feature_class == 'A',
            Location.feature_code.like(f'PCL%'),
        ).first()

    def search(self, query, country_code=None, feature=None):
        lquery = query.lower()
        q = Location.id.in_(self.session.query(Alias.location_id).filter(Alias.name == lquery))

        if country_code:
            q = and_(q, Location.country_code == country_code)

        if feature:
            fclass, fcode = feature.split('.')
            q = and_(q, Location.feature_class == fclass, Location.feature_code == fcode)
        return self.locations.filter(q)

    def search_most_probable(self, query, country=None, feature=None):
        result = sorted(self.search(query, country_code=country, feature=feature), reverse=True)
        if len(result) == 0:
            raise GeonamesDB.RecordNotFound(query)
        return result[0]

    def loaddata(self, path):
        engine = create_engine(self._connection_string, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        core_session = Session()

        def _int_or_none(x):
            return int(x) if x else None

        def _float_or_none(x):
            return float(x) if x else None

        if not self.session:
            self.connect()
        with open(path, 'r') as tsv_file:
            reader = csv.reader(tsv_file, delimiter='\t')
            timezones, buffer_tz, buffer_loc, buffer_alias = [], [], [], []
            time = timer()
            for idx, row in enumerate(reader):
                if idx % 100000 == 0:
                    print(f"{idx}, {timedelta(seconds=timer() - time)}")
                    time = timer()

                if row[6] not in ('A', 'P'):
                    continue

                tz_name = row[17].strip()
                if tz_name:
                    if tz_name not in timezones:
                        tz_id = len(timezones)
                        buffer_tz.append({'name': tz_name})
                        timezones.append(tz_name)
                    else:
                        tz_id = timezones.index(tz_name)
                else:
                    tz_id = None

                pk = _int_or_none(row[0])
                name = row[1].strip()
                ascii_name = row[2].strip()

                buffer_loc.append({
                    'id': pk,
                    'name': name,
                    'ascii_name': ascii_name,
                    # ignore row 3, contains aliases
                    'latitude': _float_or_none(row[4]),
                    'longitude': _float_or_none(row[5]),
                    'feature_class': row[6],
                    'feature_code': row[7],
                    'country_code': row[8],
                    'cc2': row[9],
                    'admin1_code': row[10],
                    'admin2_code': row[11],
                    'admin3_code': row[12],
                    'admin4_code': row[13],
                    'population': _int_or_none(row[14]),
                    'elevation': _int_or_none(row[15]),
                    'dem': _int_or_none(row[16]),
                    'timezone_id': tz_id,
                    'modification_date': datetime.strptime(row[18], "%Y-%m-%d") if row[18] else None,
                })

                aliases = {name.lower(), ascii_name.lower(), *[alias.strip().lower() for alias in row[3].split(",")]}
                buffer_alias += [{'name': alias, 'location_id': pk} for alias in aliases]

                if len(buffer_loc) % 100000 == 0:
                    engine.execute(TimeZone.__table__.insert(), buffer_tz)
                    engine.execute(Location.__table__.insert(), buffer_loc)
                    engine.execute(Alias.__table__.insert(), buffer_alias)
                    buffer_tz, buffer_loc, buffer_alias = [], [], []
            core_session.close()