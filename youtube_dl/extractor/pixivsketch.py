# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    try_get,
    ExtractorError,
)
from ..compat import (
    compat_str
)


class PixivSketchBaseIE(InfoExtractor):
    IE_DESC = False  # Do not list


class PixivSketchIE(PixivSketchBaseIE):
    IE_NAME = 'pixiv:sketch'
    # https://sketch.pixiv.net/@kotaru_taruto/lives/3404565243464976376
    _VALID_URL = r'https?://sketch\.pixiv\.net/(?P<username>@[a-zA-Z0-9_-]+)/lives/(?P<id>\d+)'
    _TEST = {}
    API_JSON_URL = 'https://sketch.pixiv.net/api/lives/%s.json'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(self.API_JSON_URL % video_id, video_id, headers={
            'Referer': url,
            'X-Requested-With': url,
        })['data']

        if not data['is_broadcasting']:
            raise ExtractorError('This live is offline.', expected=True)

        formats = self._extract_m3u8_formats(
            data['owner']['hls_movie']['url'], video_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        title = data['name']
        uploader = try_get(data, (
            lambda x: x['user']['name'],
            lambda x: x['owner']['user']['name'],
        ), None)
        uploader_id = try_get(data, (
            lambda x: compat_str(x['user']['id']),
            lambda x: compat_str(x['owner']['user']['id']),
        ), None)
        uploader_pixiv_id = try_get(data, (
            lambda x: compat_str(x['user']['pixiv_user_id']),
            lambda x: compat_str(x['owner']['user']['pixiv_user_id']),
        ), None)
        if data['is_r18']:
            age_limit = 18
        elif data['is_r15']:
            age_limit = 15
        else:
            age_limit = 0

        return {
            'formats': formats,
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_pixiv_id': uploader_pixiv_id,
            'age_limit': age_limit,
            # 'raw': data,
        }