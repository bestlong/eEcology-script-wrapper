# Copyright 2013 Netherlands eScience Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema
from geoalchemy import GeometryColumn, Geometry, WKTSpatialElement

Base = declarative_base()

logger = logging.getLogger('script_wrapper')

GPS_SCHEMA = 'gps'


class Device(Base):
    __tablename__ = 'uva_device_limited'
    __table_args__ = {'schema': GPS_SCHEMA}

    device_info_serial = Column(Integer, primary_key=True)


class Individual(Base):
    __tablename__ = 'uva_individual_limited'
    __table_args__ = {'schema': GPS_SCHEMA}

    ring_number = Column(String, primary_key=True)
    species = Column(String)


class TrackSession(Base):
    __tablename__ = 'uva_track_session_limited'
    __table_args__ = {'schema': GPS_SCHEMA}

    device_info_serial = Column(Integer,
                                ForeignKey(Device.device_info_serial),
                                primary_key=True,
                                )
    ring_number = Column(String,
                         ForeignKey(Individual.ring_number),
                         primary_key=True,
                         )
    project_leader = Column(String)



class Tracking(Base):
    __tablename__ = 'uva_tracking_limited'
    __table_args__ = {'schema': GPS_SCHEMA}

    device_info_serial = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Integer)
    pressure = Column(Integer)
    temperature = Column(Float)
    satellites_used = Column(Integer)
    gps_fixtime = Column(Float)
    positiondop = Column(Float)
    h_accuracy = Column(Float)
    v_accuracy = Column(Float)
    x_speed = Column(Float)
    y_speed = Column(Float)
    z_speed = Column(Float)
    speed_accuracy = Column(Float)
    location = GeometryColumn(Geometry(2))


class Speed(Base):
    __tablename__ = 'uva_tracking_speed_limited'  # uva_tracking_speed
    __table_args__ = {'schema': GPS_SCHEMA}

    device_info_serial = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Integer)
    pressure = Column(Integer)
    temperature = Column(Float)
    satellites_used = Column(Integer)
    gps_fixtime = Column(Float)
    positiondop = Column(Float)
    h_accuracy = Column(Float)
    v_accuracy = Column(Float)
    x_speed = Column(Float)
    y_speed = Column(Float)
    z_speed = Column(Float)
    speed_accuracy = Column(Float)
    location = GeometryColumn(Geometry(2))
    vnorth = Column(Float)
    veast = Column(Float)
    vdown = Column(Float)
    speed = Column(Float)
    speed3d = Column(Float)
    direction = Column(Float)


class Acceleration(Base):
    __tablename__ = 'uva_acceleration_limited'  # uva_acceleration101
    __table_args__ = {'schema': GPS_SCHEMA}

    device_info_serial = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    index = Column(Integer)

class Energy(Base):
    __tablename__ = 'uva_energy_limited'  # uva_energy101
    __table_args__ = {'schema': GPS_SCHEMA}

    device_info_serial = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    vsll = Column(Float)
    vbat = Column(Float)
    ssw = Column(Integer)
    temperature = Column(Float)


def request_credentials(request):
    (method, auth) = request.environ['HTTP_AUTHORIZATION'].split(' ', 1)
    if method.lower() != 'basic':
        raise NotImplementedError('Can only request credentials from Basic Authentication')
    (username, password) = auth.strip().decode('base64').split(':', 1)
    return (username, password)


def db_url_from_request(request):
    settings = request.registry.settings
    (username, password) = request_credentials(request)
    db_url = make_url(settings['sqlalchemy.url'])
    if username is not None:
        db_url.username = username
    if password is not None:
        db_url.password = password
    return str(db_url)


def DBSession(db_url):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session


def make_session_from_request(request):
    db_url = db_url_from_request(request)
    engine = create_engine(db_url, poolclass=NullPool)
    Session = sessionmaker(bind=engine)
    return Session


def populate(session):
    """

    Install Postgresql server with PostGIS extension

    Create db::

        sudo -u postgres -i
        createdb -O stefanv eecology
        psql -d eecology -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
        psql -d eecology -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql

    In python shell::

        import script_wrapper.models as m
        u = 'postgresql://localhost/eecology?sslmode=require'
        Session = m.DBSession(u)
        session = Session()
        m.populate(session)
        Session.close_all()

    Grant other users select rights::

        GRANT USAGE ON SCHEMA gps TO public;
        GRANT SELECT ON TABLE gps.uva_device_limited_device_info_serial_seq TO public;
        GRANT SELECT ON TABLE gps.uva_tracking_limited_device_info_serial_seq TO public;
        GRANT SELECT ON TABLE gps.uva_device_limited TO public;
        GRANT SELECT ON TABLE gps.uva_individual_limited TO public;
        GRANT SELECT ON TABLE gps.uva_track_session_limited TO public;
        GRANT SELECT ON TABLE gps.uva_tracking_limited TO public;
        GRANT SELECT ON TABLE gps.uva_tracking_speed_limited TO public;
        GRANT SELECT ON TABLE gps.uva_tracking_acceleration_limited TO public;
        GRANT SELECT ON TABLE gps.uva_energy_limited TO public;

        -- Create elevation schema
        CREATE SCHEMA elevation AUTHORIZATION stefanv;
        GRANT USAGE ON SCHEMA elevation TO public;
        CREATE OR REPLACE FUNCTION elevation.srtm_getvalue(IN my_point geometry, OUT altitude numeric)
  RETURNS numeric AS
$BODY$

--Usage: select elevation.srtm_getvalue (pointfromtext('POINT(90 90)',4326))
--When srtm3 does not give an elevation, srtm30 is used
--On borders between cells the south and/or east  cell is selected, also between tiles!
select -9999.0
$BODY$
  LANGUAGE sql IMMUTABLE STRICT
  COST 100;
ALTER FUNCTION elevation.srtm_getvalue(geometry)
  OWNER TO stefanv;



    """
    engine = session.get_bind()
    # Create schema
    try:
        engine.execute(CreateSchema(GPS_SCHEMA))
    except ProgrammingError as e:
        if 'already exists' not in str(e):
            raise e
    # Create tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    # Fill tables
    for tid in range(1, 10):
        device = Device(device_info_serial=tid)
        session.add(device)
        rn = 'C-{}'.format(tid)
        individual = Individual(ring_number=rn,
                                species='Lesser Black-backed Gull',
                                )
        session.add(individual)
        session.flush()
        session.add(TrackSession(device_info_serial=tid,
                                 ring_number=rn,
                                 project_leader='Someone, someone@example.com'
                                 ))
        dt = datetime.datetime.now()
        offset = tid * 0.1
        lon = 4.830617 + offset
        lat = 52.979970 + offset
        loc = WKTSpatialElement('POINT({} {})'.format(lon, lat))
        session.add(Tracking(device_info_serial=tid,
                             date_time=dt,
                             longitude=lon,
                             latitude=lat,
                             location=loc,
                             ))
        session.add(Speed(device_info_serial=tid,
                          date_time=dt,
                          longitude=lon,
                          latitude=lat,
                          location=loc,
                          ))
        session.add(Acceleration(device_info_serial=tid,
                                 date_time=dt,
                                 index=1,
                                 ))
        session.add(Energy(device_info_serial=tid,
                           date_time=dt,
                           vsll=0.009,
                           vbat=3.929,
                           ssw=63,
                           ))
    session.commit()

def getAccelerationCount(db_url, device_info_serial, start, end):
    """Returns the number of acceleration rows for selected tracker and time range.
    """
    s = DBSession(db_url)
    q = s().query(Acceleration)
    q = q.filter(Acceleration.device_info_serial==device_info_serial)
    q = q.filter(Acceleration.date_time.between(start, end))
    return q.count()