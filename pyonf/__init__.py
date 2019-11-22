from __future__ import print_function
import argparse
import sys
import os
import logging
import yaml


log = logging.getLogger(__name__)


def _deep_update(in_dict, _update):
    """
        Recursively update a dict with another, returns the result
    """
    for key, val in _update.items():
        if isinstance(val, dict):
            in_dict[key] = _deep_update(in_dict.get(key, {}), val)
        else:
            in_dict[key] = val
    return in_dict


        else:
            d[k] = v
    return d


def _dict_to_args(in_dict):
    """
        Convert nested dict keys to argparsable argument strings

        :Example:
        >>> _dict_to_args({k1: {k2: {k3 : v}}})
        {"k1-k2-k3": v}
    """
    args = []
    for arg, val in in_dict.items():
        if isinstance(val, dict):
            args += [
                (str(arg) + "-" + str(argd), vald) for argd, vald in _dict_to_args(val)
            ]
        else:
            args.append((str(arg), val))
    return args


def _args_to_dict(d_arg, d_orig={}):
    """
        Convert dict of argparse arguments and values to nested dict

        :param d_orig: used to infer original keys' name and type

        :Example:
        >>> _args_to_dict({"k1-k2-k3": v})
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
        setattr(namespace, self.dest, yaml.safe_load("[" + values + "]"))


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

    log.debug("default_conf: %s (%s)", default_conf, type(default_conf))
    if isinstance(default_conf, str):
        if os.path.isfile(default_conf):
            try:
                log.debug(" open as YAML file")
                conf = yaml.safe_load(open(default_conf))
            except Exception as ex:
                print(
                    "pyonf: Cannot parse 'default_conf' argument:\n"
                    + "%s is not a valid YAML file\n%s" % (default_conf, ex),
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            try:
                conf = yaml.safe_load(default_conf)
            except Exception as ex:
                log.debug(" open as YAML string")
                print(
                    "pyonf: Cannot parse 'default_conf' argument:\n"
                    + "%s is not a valid YAML string\n%s" % (default_conf, ex),
                    file=sys.stderr,
                )
                sys.exit(1)
        if not isinstance(conf, dict):
            print(
                "pyonf: Malformed 'default_conf' argument:\n"
                + "Parsed content is not a dict: %s" % conf,
                file=sys.stderr,
            )
            sys.exit(1)

    elif isinstance(default_conf, dict):
        log.debug("default conf is a dict")
        conf = default_conf.copy()

    else:
        print(
            "pyonf: Cannot parse 'default_conf' argument: \n"
            + "%s is not a valid YAML file, string or Python dict object"
            % default_conf,
            file=sys.stderr,
        )
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
            pargs.append("-" + arg[0])
            short_args.add(arg[0])

        pkwargs = {}

        if isinstance(val, bool) and not val:
            pkwargs["action"] = "store_true"
        elif isinstance(val, bool) and val:
            pkwargs["action"] = "store_false"
        elif isinstance(val, list):
            pkwargs["action"] = ListAction
        else:
            pkwargs["action"] = "store"

        if not isinstance(val, bool):
            if val is not None and not isinstance(val, list):
                pkwargs["type"] = type(val)
            else:
                pkwargs["type"] = str

        if isinstance(val, (tuple, list)):
            pkwargs["metavar"] = "%s,%s,..." % (arg.upper()[0], arg.upper()[0])

        helpmsg = "*mandatory*, " if arg in mandatory_opts else ""
        if isinstance(val, (tuple, list)):
            helpmsg += 'set elements of "%s" list, separated by ","' % arg
        elif isinstance(val, bool):
            helpmsg += 'turn %s "%s"' % ("on" if not val else "off", arg)
        else:
            helpmsg += 'set "%s" value, as %s' % (arg, pkwargs["type"].__name__)
        if val:
            helpmsg += " (%s %s)" % (
                "e.g.," if arg in mandatory_opts else "default is",
                val,
            )
        pkwargs["help"] = helpmsg

        log.debug(" argparse parameters: %s, %s", pargs, pkwargs)
        parser.add_argument(*pargs, **pkwargs)

    log.debug("parsing command line")

    cli_args = parser.parse_args(argv)
    cli_conf = {arg: val
                for arg, val in vars(cli_args).items()
                if arg != 'conf_file' and val is not None}
    cli_conf = _args_to_dict(cli_conf, conf)

    log.debug(" config from command line is: %s", cli_conf)

    if cli_args.conf_file:
        file_conf = yaml.safe_load(cli_args.conf_file)
        log.debug(" config from provided file is: %s" % file_conf)

    conf = _deep_update(conf, file_conf)
    conf = _deep_update(conf, cli_conf)
    log.debug("full config is: %s", conf)

    for mopt in mandatory_opts:
        if mopt not in [x for x, y in _dict_to_args(file_conf)] and mopt not in [
            x for x, y in _dict_to_args(cli_conf)
        ]:
            print('Error: "%s" option is not set' % mopt, file=sys.stderr)
            sys.exit(1)

    return conf
