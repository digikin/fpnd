# coding: utf-8

"""
    Default fpn ctlr state variables.
    :var net_trie: a Trie of JSON state objects
"""
import string

import datrie


net_trie = datrie.Trie(string.hexdigits)