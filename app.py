# Import libraries
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from datetime import datetime
from sqlalchemy import and_
from flask import Flask, jsonify


#init Flask app
app = Flask(__name__)


# --------------------------
# All the code from jupyter notebook here
# --------------------------

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# We can view all of the classes that automap found
#Base.classes.keys()
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station
# Create our session (link) from Python to the DB
session = Session(engine)

# Inspect the tables
inspector = inspect(engine)
for table_name in inspector.get_table_names():
    print("----------")
    print(f'Table: {table_name}')
    print("----------")
    for column in inspector.get_columns(table_name):
        print(column['name'], column['type'])


# --------------------------
# All the code for the routes here
# --------------------------

#routes
@app.route("/")
def home():
    print("Server received a GET request...MAIN route")
    str = f"""
    <h1> Hello to the Climate APP </h1>
    <br>
    <h3>The next routes are available</h3>
    <br>
    <ul>
        <li>The home page: <b>/</b></li>
        <li>Precipitations by date: <b><a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a></b></li>
        <li>Available stations: <b><a href="/api/v1.0/stations">/api/v1.0/stations</a></b></li>
        <li>Temperature from the most active station (last 12 months): <b><a href="/api/v1.0/tobs">/api/v1.0/tobs</a></b></li>
        <li>Temperature above (replace &lt;start&gt; for date in format YYYY-MM-DD): <b><a href="/api/v1.0/2016-08-01">/api/v1.0/&lt;start&gt;</a></b></li>
        <li>Temperature range (replace &lt;start&gt; and &lt;end&gt; for date in format YYYY-MM-DD) <b><a href="/api/v1.0/2016-08-01/2017-05-20">/api/v1.0/&lt;start&gt;/&lt;end&gt;</a></b></li>
    </ul>
    """
    return str

@app.route("/api/v1.0/precipitation")
def precipitation():
    print('Server received a GET request on /api/v1.0/precipitation')
    
    # Make the query to fetch all the measurements
    precipitations = (
        session.query(Measurement)
        .order_by(Measurement.date.desc())
        .all()
    )
    
    # Create dictionary
    prcp_dict = {}

    # Populate dictionary
    for prcp in precipitations:
        prcp_dict.update({prcp.date: prcp.prcp})

    return jsonify(prcp_dict)


@app.route("/api/v1.0/stations")
def stations():
    print('Server received a GET request on /api/v1.0/stations')
    
    # Make the query to fetch all the stations data
    stations = (
        session.query(Station)
        .all()
    )
    # Create list for results
    stations_list = []

    # Cycle through the data to get a list of dictionaries
    for stat in stations:
        # Populate dictionary
        stations_dict = {}
        stations_dict["id"] = stat.id
        stations_dict["station"] = stat.station
        stations_dict["name"] = stat.name
        stations_dict["latitude"] = stat.latitude
        stations_dict["longitude"] = stat.longitude
        stations_dict["elevation"] = stat.elevation
        # Append dictionary to list
        stations_list.append(stations_dict)

    # Return the list of dictionaries with all information
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    print('Server received a GET request on /api/v1.0/tobs')
    
    # Get the most active station
    most_active_station = (
        session
        .query(Measurement.station)
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()
    )
    #Get the last date on the DB and 12 months less (1 year) form the most active station
    last_date = (
        session.query(Measurement.date)
        .filter(Measurement.station == most_active_station.station)
        .order_by(Measurement.date.desc())
        .first()
    )
    year,month,day = last_date.date.split("-")
    finish_date = dt.date(int(year),int(month),int(day))
    start_date = dt.date(int(year)-1,int(month),int(day))
    
    station_data_query = (
        session
        .query(Measurement)
        .filter(and_(Measurement.station == most_active_station.station, Measurement.date <= finish_date, Measurement.date >= start_date))
        .all()
    )

    # create data list
    data = []
    
    # Get the data
    for record in station_data_query:
        rec_dict = {}
        rec_dict["station"] = record.station
        rec_dict["date"] = record.date
        rec_dict["tobs"] = record.tobs
        # Append to the list
        data.append(rec_dict)
    
    return jsonify(data)



@app.route("/api/v1.0/<start>")
def above(start):
    print(f"Server received a GET request on /api/v1.0/{start}")
    
    # Get the max temperature above the date provided
    max_temp = (
        session
        .query(func.max(Measurement.tobs))
        .filter(Measurement.date >= start)
        .all()
    )

    # Get the min temperature above the date provided
    min_temp = (
        session
        .query(func.min(Measurement.tobs))
        .filter(Measurement.date >= start)
        .all()
    )
    
    # Get the average of temperature from the date and above
    avg_temp = (
        session
        .query(func.min(Measurement.tobs))
        .filter(Measurement.date >= start)
        .all()
    )

    temp_dict = {
        "max": max_temp,
        "min": min_temp,
        "avg": avg_temp
    }

    return jsonify(temp_dict)
    


@app.route("/api/v1.0/<start>/<end>")
def range(start,end):
    print(f"Server received a GET request on /api/v1.0/{start}/{end}")
    # Get the max temperature above the date provided
    max_temp = (
        session
        .query(func.max(Measurement.tobs))
        .filter(and_(Measurement.date >= start, Measurement.date <= end))
        .all()
    )

    # Get the min temperature above the date provided
    min_temp = (
        session
        .query(func.min(Measurement.tobs))
        .filter(and_(Measurement.date >= start, Measurement.date <= end))
        .all()
    )
    
    # Get the average of temperature from the date and above
    avg_temp = (
        session
        .query(func.avg(Measurement.tobs))
        .filter(and_(Measurement.date >= start, Measurement.date <= end))
        .all()
    )

    temp_dict = {
        "max": max_temp,
        "min": min_temp,
        "avg": avg_temp
    }

    return jsonify(temp_dict)


if __name__ == "__main__":
    app.run(debug=True)
