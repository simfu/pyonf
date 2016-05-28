=====
Pyonf
=====
--------------------------------------------------------------------------------------------
Easy configuration parsing for your Python script, using command line argument or YAML file.
--------------------------------------------------------------------------------------------


Quickstart
----------

Content of ``myapp.py``:
::
  #!/usr/bin/env python
  from pyonf import pyonf

  default_configuration = {
      'user': 'foo',
      'password': 'changeme',
      'debug': False
  }
  conf = pyonf(default_configuration)
  print(conf)

Set configuration from command line:
::
  $ ./myapp.py --user simfu -d
  {'debug': True, 'password': 'changeme', 'user': 'simfu'}

Or from YAML configuration file ``myconfig.yml``:
::
  user: simfu
  password: secretpass

gives:
::
  $ ./myapp.py myconfig.yml
  {'debug': False, 'password': 'secretpass', 'user': 'simfu'}

Get script usage:
::
  $ ./myapp.py --help
  usage: myapp.py [-h] [--debug] [--password PASSWORD] [--user USER] [conf_file]
  
  Configuration file:
    conf_file             Path to YAML configuration file (optional)
  
  Options:
    -h, --help            show this help message and exit
    --debug, -d           turn on "debug"
    --password PASSWORD, -p PASSWORD
                          set "password" value, as str (default is changeme)
    --user USER, -u USER  set "user" value, as str (default is foo)


Features
--------
- Automatically build a command line or configuration file parser by providing a default configuration
- Support for complex configuration schemes (e.g.: lists, dict of dict of ...), mandatory options
- Default configuration can be provided as Python dict object, YAML string or YAML file
- Compatible with Python 2 & 3


More Examples
-------------

Automatic argparse'ing: help message, short and long parameters
::
  $ ./myapp.py --help
  usage: myapp.py [-h] [--debug] [--password PASSWORD] [--user USER] [conf_file]
  
  Configuration file:
    conf_file             Path to YAML configuration file (optional)
  
  Options:
    -h, --help            show this help message and exit
    --debug, -d           turn on "debug"
    --password PASSWORD, -p PASSWORD
                          set "password" value, as str (default is changeme)
    --user USER, -u USER  set "user" value, as str (default is foo)

  $ ./myapp.py -u simfu
  {'debug': False, 'password': 'changeme', 'user': 'simfu'}

  $ ./myapp.py --user simfu
  {'debug': False, 'password': 'changeme', 'user': 'simfu'}


Use both configuration file and command line argument (the latter takes precedence)
::
  $ ./myapp.py myconfig.yml -d
  {'debug': True, 'password': 'secretpass', 'user': 'simfu'}


Multiple input for default configuration
::
  # Using a dict
  default_configuration = {
      'user': 'foo',
      'password': 'changeme',
      'debug': False
  }

  # Using a YAML String
  default_configuration = """
  user: foo
  password: changeme
  debug: false
  """
  conf = pyonf(defaulf_configuration)
  print(conf)

  # Using a YAML file
  default_configuration = "/etc/myapp.conf"
  conf = pyonf(defaulf_configuration)
  print(conf)


Smart parsing of option type
::
  default_configuration = """
  user: foo
  password: changeme
  debug: false
  level: 3
  """
  conf = pyonf(defaulf_configuration)
  print(conf)

i.e.:
::
  ./myapp.py -l 4  # OK
  ./myapp.py -l quatre  # Will not work, level needs to be an integer

  # Boolean option does not need argument, its value will be switched
  ./myapp.py -d


Complex configuration scheme
::
  default_configuration = """
  user: foo
  password: changeme
  suboptions:
    param1: value1
    param2: value2
  """
  conf = pyonf(defaulf_configuration)
  print(conf)

set "sub-keys" with:
::
  $ ./myapp.py --suboptions-param1 my_new_value

Mandatory options:
::
  default_configuration = """
  user: foo
  password: changeme
  debug: false
  level: 3
  """
  conf = pyonf(defaulf_configuration, mandatory_opts = ['user', 'password'])
  print(conf)

you have to defined ``user`` and ``password`` option:
::
  $ ./my_app.py
  Error: "user" option is not set
