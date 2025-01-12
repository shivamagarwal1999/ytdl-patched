# coding: utf-8
from __future__ import unicode_literals

import functools
import re

from .instances import instances
from ..common import InfoExtractor, SelfHostedInfoExtractor
from ...compat import compat_str
from ...utils import (
    int_or_none,
    parse_resolution,
    str_or_none,
    try_get,
    unified_timestamp,
    url_or_none,
    urljoin,
    OnDemandPagedList,
    ExtractorError,
    preferredencoding,
)


known_valid_instances = set()


class PeerTubeBaseIE(SelfHostedInfoExtractor):

    @staticmethod
    def _test_peertube_instance(ie, hostname, skip, prefix):
        if isinstance(hostname, bytes):
            hostname = hostname.decode(preferredencoding())
        hostname = hostname.encode('idna').decode('utf-8')

        if hostname in instances:
            return True
        if hostname in known_valid_instances:
            return True

        # continue anyway if "peertube:" is used
        if prefix:
            return True
        # without --check-peertube-instance,
        #   skip further instance check
        if skip:
            return False

        ie.report_warning('Testing if %s is a PeerTube instance because it is not listed in either joinpeertube.org, the-federation.info or fediverse.observer.' % hostname)

        try:
            # try /api/v1/config
            api_request_config = ie._download_json(
                'https://%s/api/v1/config' % hostname, hostname,
                note='Testing PeerTube API /api/v1/config')
            if not api_request_config.get('instance', {}).get('name'):
                return False

            # try /api/v1/videos
            api_request_videos = ie._download_json(
                'https://%s/api/v1/videos' % hostname, hostname,
                note='Testing PeerTube API /api/v1/videos')
            if not isinstance(api_request_videos.get('data'), (tuple, list)):
                return False
        except (IOError, ExtractorError):
            return False

        # this is probably peertube instance
        known_valid_instances.add(hostname)
        return True

    @staticmethod
    def _is_probe_enabled(ydl):
        return ydl.params.get('check_peertube_instance', False)

    @classmethod
    def _probe_selfhosted_service(cls, ie: InfoExtractor, url, hostname):
        prefix = ie._search_regex(
            # (PeerTubeIE._VALID_URL, PeerTubePlaylistIE._VALID_URL),
            cls._VALID_URL,
            url, 'peertube test', group='prefix', default=None)
        return cls._test_peertube_instance(ie, hostname, False, prefix)


class PeerTubeIE(PeerTubeBaseIE):
    _UUID_RE = r'[\da-zA-Z]{22}|[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'
    _API_BASE = 'https://%s/api/v1/videos/%s/%s'
    _VALID_URL = r'''(?x)
                    (?P<prefix>peertube:)(?:
                        (?P<host>[^:]+):|
                        https?://(?P<host_2>[^/]+)/(?:videos/(?:watch|embed)|api/v\d/videos|w)/
                    )
                    (?P<id>%s)
                    ''' % _UUID_RE
    _TESTS = [{
        'url': 'https://framatube.org/videos/watch/9c9de5e8-0a1e-484a-b099-e80766180a6d',
        'md5': '8563064d245a4be5705bddb22bb00a28',
        'info_dict': {
            'id': '9c9de5e8-0a1e-484a-b099-e80766180a6d',
            'ext': 'mp4',
            'title': 'What is PeerTube?',
            'description': 'md5:3fefb8dde2b189186ce0719fda6f7b10',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'timestamp': 1538391166,
            'upload_date': '20181001',
            'uploader': 'Framasoft',
            'uploader_id': '3',
            'uploader_url': 'https://framatube.org/accounts/framasoft',
            'channel': 'A propos de PeerTube',
            'channel_id': '2215',
            'channel_url': 'https://framatube.org/video-channels/joinpeertube',
            'language': 'en',
            'license': 'Attribution - Share Alike',
            'duration': 113,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': ['framasoft', 'peertube'],
            'categories': ['Science & Technology'],
        }
    }, {
        'url': 'https://peertube2.cpy.re/w/122d093a-1ede-43bd-bd34-59d2931ffc5e',
        'info_dict': {
            'id': '122d093a-1ede-43bd-bd34-59d2931ffc5e',
            'ext': 'mp4',
            'title': 'E2E tests',
            'uploader_id': '37855',
            'timestamp': 1589276219,
            'upload_date': '20200512',
            'uploader': 'chocobozzz',
        }
    }, {
        'url': 'https://peertube2.cpy.re/w/3fbif9S3WmtTP8gGsC5HBd',
        'info_dict': {
            'id': '3fbif9S3WmtTP8gGsC5HBd',
            'ext': 'mp4',
            'title': 'E2E tests',
            'uploader_id': '37855',
            'timestamp': 1589276219,
            'upload_date': '20200512',
            'uploader': 'chocobozzz',
        },
    }, {
        'url': 'https://peertube2.cpy.re/api/v1/videos/3fbif9S3WmtTP8gGsC5HBd',
        'info_dict': {
            'id': '3fbif9S3WmtTP8gGsC5HBd',
            'ext': 'mp4',
            'title': 'E2E tests',
            'uploader_id': '37855',
            'timestamp': 1589276219,
            'upload_date': '20200512',
            'uploader': 'chocobozzz',
        },
    }, {
        # Issue #26002
        'url': 'peertube:spacepub.space:d8943b2d-8280-497b-85ec-bc282ec2afdc',
        'info_dict': {
            'id': 'd8943b2d-8280-497b-85ec-bc282ec2afdc',
            'ext': 'mp4',
            'title': 'Dot matrix printer shell demo',
            'uploader_id': '3',
            'timestamp': 1587401293,
            'upload_date': '20200420',
            'uploader': 'Drew DeVault',
        }
    }, {
        'url': 'https://peertube.debian.social/videos/watch/0b04f13d-1e18-4f1d-814e-4979aa7c9c44',
        'only_matching': True,
    }, {
        # nsfw
        'url': 'https://vod.ksite.de/videos/watch/9bb88cd3-9959-46d9-9ab9-33d2bb704c39',
        'only_matching': True,
    }, {
        'url': 'https://vod.ksite.de/videos/embed/fed67262-6edb-4d1c-833b-daa9085c71d7',
        'only_matching': True,
    }, {
        'url': 'https://peertube.tv/api/v1/videos/c1875674-97d0-4c94-a058-3f7e64c962e8',
        'only_matching': True,
    }, {
        'url': 'peertube:framatube.org:b37a5b9f-e6b5-415c-b700-04a5cd6ec205',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_peertube_url(webpage, source_url):
        mobj = re.match(
            r'https?://(?P<host>[^/]+)/(?:videos/(?:watch|embed)|w)/(?P<id>%s)'
            % PeerTubeIE._UUID_RE, source_url)
        if mobj and any(p in webpage for p in (
                'meta property="og:platform" content="PeerTube"',
                '<title>PeerTube<',
                'There will be other non JS-based clients to access PeerTube',
                '>We are sorry but it seems that PeerTube is not compatible with your web browser.<')):
            return 'peertube:%s:%s' % mobj.group('host', 'id')

    @staticmethod
    def _extract_urls(webpage, source_url):
        entries = re.findall(
            r'''(?x)<iframe[^>]+\bsrc=["\'](?P<url>(?:https?:)?//[^/]+?/videos/embed/%s)'''
            % PeerTubeIE._UUID_RE, webpage)
        if not entries:
            peertube_url = PeerTubeIE._extract_peertube_url(webpage, source_url)
            if peertube_url:
                entries = [peertube_url]
        return entries

    @classmethod
    def suitable(cls, url):
        mobj = cls._match_valid_url(url)
        if not mobj:
            return False
        prefix = mobj.group('prefix')
        hostname = mobj.group('host') or mobj.group('host_2')
        return cls._test_peertube_instance(None, hostname, True, prefix)

    def _call_api(self, host, video_id, path, note=None, errnote=None, fatal=True):
        return self._download_json(
            self._API_BASE % (host, video_id, path), video_id,
            note=note, errnote=errnote, fatal=fatal)

    def _get_subtitles(self, host, video_id):
        captions = self._call_api(
            host, video_id, 'captions', note='Downloading captions JSON',
            fatal=False)
        if not isinstance(captions, dict):
            return
        data = captions.get('data')
        if not isinstance(data, list):
            return
        subtitles = {}
        for e in data:
            language_id = try_get(e, lambda x: x['language']['id'], compat_str)
            caption_url = urljoin('https://%s' % host, e.get('captionPath'))
            if not caption_url:
                continue
            subtitles.setdefault(language_id or 'en', []).append({
                'url': caption_url,
            })
        return subtitles

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        host = mobj.group('host') or mobj.group('host_2')
        video_id = mobj.group('id')

        video = self._call_api(
            host, video_id, '', note='Downloading video JSON')

        title = video['name']

        formats = []
        files = video.get('files') or []
        for playlist in (video.get('streamingPlaylists') or []):
            if not isinstance(playlist, dict):
                continue
            playlist_files = playlist.get('files')
            if not (playlist_files and isinstance(playlist_files, list)):
                continue
            files.extend(playlist_files)
        for file_ in files:
            if not isinstance(file_, dict):
                continue
            file_url = url_or_none(file_.get('fileUrl'))
            if not file_url:
                continue
            file_size = int_or_none(file_.get('size'))
            format_id = try_get(
                file_, lambda x: x['resolution']['label'], compat_str)
            f = parse_resolution(format_id)
            f.update({
                'url': file_url,
                'format_id': format_id,
                'filesize': file_size,
            })
            if format_id == '0p':
                f['vcodec'] = 'none'
            else:
                f['fps'] = int_or_none(file_.get('fps'))
            formats.append(f)
        self._sort_formats(formats)

        description = video.get('description')
        if description and len(description) >= 250:
            # description is shortened
            full_description = self._call_api(
                host, video_id, 'description', note='Downloading description JSON',
                fatal=False)

            if isinstance(full_description, dict):
                description = str_or_none(full_description.get('description')) or description

        subtitles = self.extract_subtitles(host, video_id)

        def data(section, field, type_):
            return try_get(video, lambda x: x[section][field], type_)

        def account_data(field, type_):
            return data('account', field, type_)

        def channel_data(field, type_):
            return data('channel', field, type_)

        category = data('category', 'label', compat_str)
        categories = [category] if category else None

        age_limit = 18 if video.get('nsfw') else 0

        webpage_url = 'https://%s/videos/watch/%s' % (host, video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': urljoin(webpage_url, video.get('thumbnailPath')),
            'timestamp': unified_timestamp(video.get('publishedAt')),
            'uploader': account_data('displayName', compat_str),
            'uploader_id': str_or_none(account_data('id', int)),
            'uploader_url': url_or_none(account_data('url', compat_str)),
            'channel': channel_data('displayName', compat_str),
            'channel_id': str_or_none(channel_data('id', int)),
            'channel_url': url_or_none(channel_data('url', compat_str)),
            'language': data('language', 'id', compat_str),
            'license': data('licence', 'label', compat_str),
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('views')),
            'like_count': int_or_none(video.get('likes')),
            'dislike_count': int_or_none(video.get('dislikes')),
            'age_limit': age_limit,
            'tags': try_get(video, lambda x: x['tags'], list),
            'categories': categories,
            'formats': formats,
            'subtitles': subtitles,
            'webpage_url': webpage_url,
        }


class PeerTubePlaylistIE(PeerTubeBaseIE):
    IE_NAME = 'PeerTube:Playlist'
    _TYPES = {
        'a': 'accounts',
        'c': 'video-channels',
        'w/p': 'video-playlists',
    }
    _VALID_URL = r'''(?x)
                        (?P<prefix>peertube:)?https?://(?P<host>[^/]+)/(?P<type>(?:%s))/
                    (?P<id>[^/]+)
                    ''' % ('|'.join(_TYPES.keys()), )
    _TESTS = [{
        'url': 'https://peertube.tux.ovh/w/p/3af94cba-95e8-4b74-b37a-807ab6d82526',
        'info_dict': {
            'id': '3af94cba-95e8-4b74-b37a-807ab6d82526',
            'description': 'playlist',
            'timestamp': 1611171863,
            'title': 'playlist',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://peertube.tux.ovh/w/p/wkyqcQBnsvFxtUB2pkYc1e',
        'info_dict': {
            'id': 'wkyqcQBnsvFxtUB2pkYc1e',
            'description': 'Cette liste de vidéos contient uniquement les jeux qui peuvent être terminés en une seule vidéo.',
            'title': 'Let\'s Play',
            'timestamp': 1604147331,
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://peertube.debian.social/w/p/hFdJoTuyhNJVa1cDWd1d12',
        'info_dict': {
            'id': 'hFdJoTuyhNJVa1cDWd1d12',
            'description': 'Diversas palestras do Richard Stallman no Brasil.',
            'title': 'Richard Stallman no Brasil',
            'timestamp': 1599676222,
        },
        'playlist_mincount': 9,
    }, {
        'url': 'https://peertube2.cpy.re/a/chocobozzz/videos',
        'info_dict': {
            'id': 'chocobozzz',
            'timestamp': 1553874564,
            'title': 'chocobozzz',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://framatube.org/c/bf54d359-cfad-4935-9d45-9d6be93f63e8/videos',
        'info_dict': {
            'id': 'bf54d359-cfad-4935-9d45-9d6be93f63e8',
            'timestamp': 1519917377,
            'title': 'Les vidéos de Framasoft',
        },
        'playlist_mincount': 345,
    }, {
        'url': 'https://peertube2.cpy.re/c/blender_open_movies@video.blender.org/videos',
        'info_dict': {
            'id': 'blender_open_movies@video.blender.org',
            'timestamp': 1542287810,
            'title': 'Official Blender Open Movies',
        },
        'playlist_mincount': 11,
    }]
    _API_BASE = 'https://%s/api/v1/%s/%s%s'
    _PAGE_SIZE = 30

    @classmethod
    def suitable(cls, url):
        mobj = cls._match_valid_url(url)
        if not mobj:
            return False
        hostname, prefix = mobj.group('host', 'prefix')
        return cls._test_peertube_instance(None, hostname, True, prefix)

    def call_api(self, host, name, path, base, **kwargs):
        return self._download_json(
            self._API_BASE % (host, base, name, path), name, **kwargs)

    def fetch_page(self, host, id, type, page):
        page += 1
        video_data = self.call_api(
            host, id,
            f'/videos?sort=-createdAt&start={self._PAGE_SIZE * (page - 1)}&count={self._PAGE_SIZE}&nsfw=both',
            type, note=f'Downloading page {page}').get('data', [])
        for video in video_data:
            shortUUID = video.get('shortUUID') or try_get(video, lambda x: x['video']['shortUUID'])
            video_title = video.get('name') or try_get(video, lambda x: x['video']['name'])
            yield self.url_result(
                f'https://{host}/w/{shortUUID}', PeerTubeIE.ie_key(),
                video_id=shortUUID, video_title=video_title)

    def _extract_playlist(self, host, type, id):
        info = self.call_api(host, id, '', type, note='Downloading playlist information', fatal=False)

        playlist_title = info.get('displayName')
        playlist_description = info.get('description')
        playlist_timestamp = unified_timestamp(info.get('createdAt'))
        channel = try_get(info, lambda x: x['ownerAccount']['name']) or info.get('displayName')
        channel_id = try_get(info, lambda x: x['ownerAccount']['id']) or info.get('id')
        thumbnail = info.get('thumbnailPath')
        thumbnail = f'https://{host}{thumbnail}' if thumbnail else None

        entries = OnDemandPagedList(functools.partial(
            self.fetch_page, host, id, type), self._PAGE_SIZE)

        return self.playlist_result(
            entries, id, playlist_title, playlist_description,
            timestamp=playlist_timestamp, channel=channel, channel_id=channel_id, thumbnail=thumbnail)

    def _real_extract(self, url):
        type, host, id = self._match_valid_url(url).group('type', 'host', 'id')
        type = self._TYPES[type]
        return self._extract_playlist(host, type, id)
