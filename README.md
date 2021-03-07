# dbfetch

Rough set of python scripts for fetching JSON data, shoving it into a database, and plotting graphs. This can be used as a relatively low-resource, and simple alternative for a NoSQL solution for specific usage cases. A relational database is required.

This was designed somewhat as a companion for weewx. It resides on the same server and generates graph plots which can be inserted into the weewx templates alongside its own native graphs.

## Configuration

In addition to the module configurations below, the following global configuraton is also available:

### \[smtp\]

* server (optional, required if using e-mail notifications)

  SMTP server through which e-mail notifications should be relayed.

* user (optional)

  Username to authneticate with SMTP server for e-mail notifications.

* password (optional)

  Password to authenticate with SMTP server for e-mail notifications.

* from (optional, required if using e-mail notifications)

  From: address to use when sending e-mail notifications.

* to (optional, required if using e-mail notifications)

  Address to which e-mail notifications should be sent.

## Modules

Three modules so far:

* awair

  Polls the web interface on an awair device and stores the resulting air quality data.
  
* pmsa

  Polls a [sensors server](https://github.com/indigoparadox/dbfetch-sensors) and stores the resulting sensor data.
  
* covid

  Polls the NY state COVID testing data analytics website and stores a copy of the data.

Now refactored so the models are defined in YAML files. No module-specific code remains.

## Common Module Configuration

### \[<module name>\] (e.g. \[awair\])

* connection

  SQLAlchemy database connection string. e.g. mysql+pymysql://user:password@database.example.com/database_name

* locations

  Comma-separated list of location indexes. Each one should have its own configuration stanza, outlined below.

* public_html

  Directory in which plotted graph images should be saved.

### \[<module name>-location-<module index>\]

* title

  Title printed on the plotted graph image produced for this location.

* output

  This string will be combined with the module name and the interval (day/week/etc) to create the filenames for plotted graph images.

* url

  URL from which to fetch the (currently only JSON-formatted) data to store in the database and plot graph images from.

* tz_offset

  Integer number of hours to add to timestamps in fetched data. Can be positive or negative.
