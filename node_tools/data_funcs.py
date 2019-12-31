# coding: utf-8

"""Data update helper functions."""
from __future__ import print_function

import logging
import datetime
import functools

from diskcache import Index

from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.helper_funcs import update_state, get_cachedir
from node_tools.helper_funcs import ENODATA, NODE_SETTINGS

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


logger = logging.getLogger(__name__)
cache = Index(get_cachedir())
max_age = NODE_SETTINGS['max_cache_age']
id_list = NODE_SETTINGS['moon_list']


def do_announce_node(id_list):
    moons = find_moons(id_list)
    if moons:
        # send nanoservice client request
        logger.debug('Send msg to {} with addr: {}'.format(moons[0].identity, moons[0].address))
        return 'OK'
    else:
        return None


def do_log_node_data():
    nodeStatus = get_node_status(cache)
    logger.debug('Node status tuple: {}'.format(nodeStatus))


def do_logstats(msg=None):
    """Log cache size/key stats with optional ``msg`` string"""
    size = len(cache)
    if msg:
        logger.debug(msg)
    logger.debug('{} items currently in cache.'.format(size))
    logger.debug('Cache items: {}'.format(list(cache)))


def find_moons(id_list):
    """
    Find fpn moon(s) using cached peer data.
    :param cache: <cache> object
    :param id_list: list of moon IDs from settings
    :return moons: list of namedTuples for matching moons
    """
    peers = get_peer_status(cache)
    moons = []
    logger.debug('Entering peer loop with: {}'.format(peers))
    if peers:
        for Peer in peers:
            if 'MOON' in Peer.role:
                logger.debug('Found moon in peers: {}'.format(Peer.identity))
                for id in id_list:
                    if Peer.identity == id:
                        moons.append(Peer)
                logger.debug('Exiting id_list with: {}'.format(moons))
    return moons


def with_cache_aging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        cache wrapper for update_runner() function
        * get timestamp and clear cache if stale
        * log some debug info
        * update cache timestamp based on result
        :return: result from update_runner()
        """
        stamp = None
        utc_stamp = datetime.datetime.now(utc)
        do_logstats('Entering cache wrapper')
        if 'utc-time' in cache:
            stamp = cache['utc-time']
            cache_age = utc_stamp - stamp  # this is a timedelta
            logger.debug('Cache age is: {} sec'.format(cache_age.seconds))
            logger.debug('Maximum cache age: {} sec'.format(max_age))
            if cache_age.seconds > max_age:
                logger.debug('Cache data is too old!!')
                logger.debug('Stale data will be removed!!')
                cache.clear()
            else:
                logger.info('Cache is {} sec old (still valid)'.format(cache_age.seconds))
        else:
            cache.update([('utc-time', utc_stamp)])

        result = func(*args, **kwargs)
        logger.info('Get data result was: {}'.format(result))

        if stamp is not None and result is ENODATA or None:
            cache.update([('utc-time', stamp)])
            logger.debug('Old cache time is: {}'.format(stamp.isoformat(' ')))
        else:
            cache.update([('utc-time', utc_stamp)])
            logger.debug('New cache time is: {}'.format(utc_stamp.isoformat(' ')))
        return result
    return wrapper


@with_cache_aging
def update_runner():
    do_logstats('Entering update_runner')

    try:
        res = update_state()
        size = len(cache)
    except:  # noqa: E722
        logger.debug('No data available, cache was NOT updated')
        pass
    else:
        if size < 1:
            logger.debug('No data available (live or cached)')
        elif size > 0:
            do_logstats()
        else:
            logger.debug('Cache empty and API returned ENODATA')
    do_logstats('Leaviing update_runner')
    return res
