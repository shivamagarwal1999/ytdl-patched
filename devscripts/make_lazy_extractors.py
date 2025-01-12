#!/usr/bin/env python3
from __future__ import unicode_literals, print_function

from inspect import getsource
import io
import os
import re
from os.path import dirname as dirn
import sys

sys.path.insert(0, dirn(dirn((os.path.abspath(__file__)))))

lazy_extractors_filename = sys.argv[1] if len(sys.argv) > 1 else 'yt_dlp/extractor/lazy_extractors.py'
if os.path.exists(lazy_extractors_filename):
    os.remove(lazy_extractors_filename)

# Block plugins from loading
plugins_dirname = 'ytdlp_plugins'
plugins_blocked_dirname = 'ytdlp_plugins_blocked'
if os.path.exists(plugins_dirname):
    os.rename(plugins_dirname, plugins_blocked_dirname)

from yt_dlp.extractor import _ALL_CLASSES
from yt_dlp.extractor.common import InfoExtractor, SearchInfoExtractor

if os.path.exists(plugins_blocked_dirname):
    os.rename(plugins_blocked_dirname, plugins_dirname)

with open('devscripts/lazy_load_template.py', 'rt') as f:
    module_template = f.read()

CLASS_PROPERTIES = ['ie_key', 'working', '_match_valid_url', 'suitable', '_match_id', 'get_temp_id']
module_contents = [
    module_template,
    *[getsource(getattr(InfoExtractor, k)) for k in CLASS_PROPERTIES],
    '\nclass LazyLoadSearchExtractor(LazyLoadExtractor):\n    pass\n']

ie_template = '''
class {name}({bases}):
    _module = '{module}'
'''

make_valid_template = '''
    @classmethod
    def _make_valid_url(cls):
        return {valid_url!r}
'''


def get_base_name(base):
    if base is InfoExtractor:
        return 'LazyLoadExtractor'
    elif base is SearchInfoExtractor:
        return 'LazyLoadSearchExtractor'
    else:
        return base.__name__


def cleanup_regex(regex_str):
    if not isinstance(regex_str, (str, bytes)):
        return regex_str
    has_extended = re.search(r'\(\?[aiLmsux]*x[aiLmsux]*\)', regex_str)  # something like (?xxs) may match, but (?s) or (?i) won't
    if not has_extended:
        return regex_str
    # remove comments
    regex_str = re.sub(r'(?m)\s+#.+?$', '', regex_str)
    # remove spaces and indents
    regex_str = re.sub(r'\s+', '', regex_str)
    # remove x (EXTENDED) from all inline flags
    regex_str = re.sub(r'\(\?([aiLmsux]+)\)', lambda m: '(?%s)' % m.group(1).replace('x', ''), regex_str)
    regex_str = re.sub(r'\(\?\)', '', regex_str)

    return regex_str


def build_lazy_ie(ie, name):
    s = ie_template.format(
        name=name,
        bases=', '.join(map(get_base_name, ie.__bases__)),
        module=ie.__module__)
    valid_url = getattr(ie, '_VALID_URL', None)
    valid_url = cleanup_regex(valid_url)
    if valid_url:
        s += f'    _VALID_URL = {valid_url!r}\n'
    if not ie._WORKING:
        s += '    _WORKING = False\n'
    if ie.suitable.__func__ is not InfoExtractor.suitable.__func__:
        s += f'\n{getsource(ie.suitable)}'
    if hasattr(ie, '_make_valid_url'):
        # search extractors
        s += make_valid_template.format(valid_url=ie._make_valid_url())
    return s


# find the correct sorting and add the required base classes so that subclasses
# can be correctly created
classes = _ALL_CLASSES[:-1]
ordered_cls = []
while classes:
    for c in classes[:]:
        bases = set(c.__bases__) - set((object, InfoExtractor, SearchInfoExtractor))
        stop = False
        for b in bases:
            if b not in classes and b not in ordered_cls:
                if b.__name__ == 'GenericIE':
                    exit()
                classes.insert(0, b)
                stop = True
        if stop:
            break
        if all(b in ordered_cls for b in bases):
            ordered_cls.append(c)
            classes.remove(c)
            break
ordered_cls.append(_ALL_CLASSES[-1])

names = []
for ie in ordered_cls:
    name = ie.__name__
    src = build_lazy_ie(ie, name)
    module_contents.append(src)
    if ie in _ALL_CLASSES:
        names.append(name)

module_contents.append(
    '\n_ALL_CLASSES = [{0}]'.format(', '.join(names)))

module_src = '\n'.join(module_contents) + '\n'

with io.open(lazy_extractors_filename, 'wt', encoding='utf-8') as f:
    f.write(module_src)
