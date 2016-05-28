from __future__ import print_function
import yaml
import argparse
import sys
import os
import logging


log = logging.getLogger(__name__)


def _deep_update(d, u):
    """
        Recursively update a dict with another, returns the result
    """
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = _deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def _dict_to_args(d):
    """
        Convert nested dict keys to argparsable argument strings

        :Example:
        >>> _dict_to_args({k1: {k2: {k3 : v}}})
        {"k1-k2-k3": v}
    """
    args = []
    for arg, val in d.items():
        if isinstance(val, dict):
            args += [(str(arg)+"-"+str(argd), vald)
                     for argd, vald in _dict_to_args(val)]
        else:
            args.append((str(arg), val))
    return args


def _args_to_dict(d_arg, d_orig={}):
    """
        Convert dict of argparse arguments and values to nested dict

        :param d_orig: used to infer original keys' name and type

        :Example:
        >>> _args_to_dict({"k1_k2_k3": v})
        {k1: {k2: {k3 : v}}}

    """
    for arg, val in d_arg.items():
        if "_" in arg:
            d_ptr = d_arg
            d_optr = d_orig
            args = arg.split('_')
            while args:
                key, args = args[0], args[1:]
                if [k for k in d_optr.keys() if str(k) == key]:
                    key = [k for k in d_optr.keys() if str(k) == key].pop()
                if not args or d_optr.get('_'.join([key]+args)):
                    d_ptr[key] = val
                    del d_arg[arg]
                    break
                else:
                    if not d_ptr.get(key):
                        d_ptr[key] = {}
                    d_ptr = d_ptr[key]
                    d_optr = d_optr.get(key, {})
    return d_arg


class ListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, yaml.safe_load("["+values+"]"))


def pyonf(default_conf={}, mandatory_opts=[], argv=sys.argv[1:]):
    """
        Build command line and configuration parser from a default config.

        Calling this function will parse command line arguments and:
        - accept a path to a YAML configuration file
        - accept command line options with respect to default_conf content
        It will then returns a dict with parsed configuration options

        :param default_conf:   Default configuration, as a path to YAML file,
                               YAML string or Python dict
        :param mandatory_opts: List of options that must be defined by user
                               (none by default)
        :param argv:           List of arguments to parse
                               (sys.argv[1:] by default)
        :return:               New configuration after parsing


    """

    conf = {}
    file_conf = {}
    cli_conf = {}

    log.debug("default_conf: %s (%s)" % (default_conf, type(default_conf)))
    if isinstance(default_conf, str):
        if os.path.isfile(default_conf):
            try:
                log.debug(" open as YAML file")
                conf = yaml.safe_load(open(default_conf))
            except Exception as e:
                print("pyonf: Cannot parse 'default_conf' argument:\n" +
                      "%s is not a valid YAML file\n%s"
                      % (default_conf, e),
                      file=sys.stderr)
                sys.exit(1)
        else:
            try:
                conf = yaml.safe_load(default_conf)
            except Exception as e:
                log.debug(" open as YAML string" % default_conf)
                print("pyonf: Cannot parse 'default_conf' argument:\n" +
                      "%s is not a valid YAML string\n%s"
                      % (default_conf, e),
                      file=sys.stderr)
                sys.exit(1)
        if not isinstance(conf, dict):
            print("pyonf: Malformed 'default_conf' argument:\n" +
                  "Parsed content is not a dict: %s" % conf,
                  file=sys.stderr)
            sys.exit(1)

    elif isinstance(default_conf, dict):
        log.debug(" is a dict" % default_conf)
        conf = default_conf.copy()

    else:
        print("pyonf: Cannot parse 'default_conf' argument: \n" +
              "%s is not a valid YAML file, string or Python dict object"
              % default_conf,
              file=sys.stderr)
        sys.exit(1)
    log.debug(" content: %s" % conf)

    parser = argparse.ArgumentParser()
    parser._positionals.title = 'Configuration file'
    parser._optionals.title = 'Options'
    parser.add_argument("conf_file",
                        help="Path to YAML configuration file (optional)",
                        type=argparse.FileType('r'),
                        nargs='?')

    short_args = set()
    for arg, val in sorted(_dict_to_args(conf)):
        log.debug("building argparse for arg:%s val:%s type:%s" %
                  (arg, val, type(val).__name__))

        pargs = ["--"+arg]
        if not arg[0] in short_args:
            pargs.append("-"+arg[0])
            short_args.add(arg[0])
        pkwargs = {'action': 'store_true' if isinstance(val, bool) and not val
                   else 'store_false' if isinstance(val, bool) and val
                   else ListAction if isinstance(val, list)
                   else 'store'}
        if not isinstance(val, bool):
            pkwargs['type'] = (
                type(val) if val is not None and not isinstance(val, list)
                else str
                )
        helpmsg = '*mandatory*, ' if arg in mandatory_opts else ""
        if isinstance(val, (tuple, list)):
            helpmsg += 'set elements of "%s" list, separated by ","' % \
                       arg
            pkwargs['metavar'] = '%s,%s,...' % \
                                 (arg.upper()[0], arg.upper()[0])
        elif isinstance(val, bool):
            helpmsg += 'turn %s "%s"' % ('on' if not val else 'off', arg)
        else:
            helpmsg += 'set "%s" value, as %s' % \
                       (arg, pkwargs['type'].__name__)
        if val:
            helpmsg += ' (%s %s)' % \
                       ('e.g.,' if arg in mandatory_opts
                        else 'default is ', val)
        pkwargs['help'] = helpmsg

        log.debug(" argparse parameters: %s, %s" % (pargs, pkwargs))
        parser.add_argument(*pargs, **pkwargs)

    log.debug("parsing command line")

    cli_args = parser.parse_args(argv)
    cli_conf = {arg: val
                for arg, val in vars(cli_args).items()
                if arg != 'conf_file' and val is not None}
    cli_conf = _args_to_dict(cli_conf, conf)

    log.debug(" config from command line is: %s" % cli_conf)

    if cli_args.conf_file:
        file_conf = yaml.safe_load(cli_args.conf_file)
        log.debug(" config from provided file is: %s" % file_conf)

    conf = _deep_update(conf, file_conf)
    conf = _deep_update(conf, cli_conf)
    log.debug("full config is: %s" % conf)

    for m in mandatory_opts:
        if m not in [x for x, y in _dict_to_args(file_conf)] \
           and m not in [x for x, y in _dict_to_args(cli_conf)]:
            print('Error: "%s" option is not set' % m,
                  file=sys.stderr)
            sys.exit(1)

    return conf
