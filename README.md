# dbfetch
Rough set of python scripts for fetching JSON data, shoving it into a database, and plotting graphs.

This was designed somewhat as a companion for weewx. It resides on the same server and generates graph plots which can be inserted into the weewx templates alongside its own native graphs.

Can be configured through included ini files.

Three modules so far:

* awair

  Polls the web interface on an awair device and stores the resulting air quality data.
  
* pmsa

  Polls a [sensors server](https://github.com/indigoparadox/dbfetch-sensors) and stores the resulting sensor data.
  
* covid

  Polls the NY state COVID testing data analytics website and stores a copy of the data.

Now refactored so the models are defined in YAML files. No module-specific code remains.

