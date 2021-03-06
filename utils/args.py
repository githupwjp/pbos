import logging


def add_logging_args(parser):
    group = parser.add_argument_group('logging arguments')
    group.add_argument('--log_level', '-ll', default='INFO',
                       help='log level used by logging module')
    return group


def set_logging_config(args):
    """Set log level using args.log_level"""
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=numeric_level)


def dump_args(args, logger=None, save_path=None):
    """
    log args
    save the args if `save_path` is not None
    """
    import json

    if not isinstance(args, dict):
        args = vars(args)

    if logger:
        logger.info(json.dumps(args, indent=2))
    else:
        logging.info(json.dumps(args, indent=2))

    if save_path:
        with open(save_path, 'w') as fout:
            json.dump(args, fout, indent=2)
