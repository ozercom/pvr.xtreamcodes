# -*- coding: utf-8 -*-
import sys
import json
import time
import os
import unicodedata
from urllib.parse import urlencode, parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE = sys.argv[0]
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
CACHE_FILE = os.path.join(PROFILE, 'all_channels.json')
CACHE_TTL = 600


def rpc(method, params=None):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}}
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(payload, ensure_ascii=False)))
        if 'error' in response:
            xbmc.log('Xtream Browser JSON-RPC error: %s' % response['error'], xbmc.LOGERROR)
            return None
        return response.get('result')
    except Exception as exc:
        xbmc.log('Xtream Browser JSON-RPC exception: %s' % exc, xbmc.LOGERROR)
        return None


def url_for(**kwargs):
    return BASE + '?' + urlencode(kwargs)


def norm(value):
    value = str(value or '').casefold().replace('ı', 'i')
    value = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in value if not unicodedata.combining(ch))


def get_groups():
    result = rpc('PVR.GetChannelGroups', {'channeltype': 'tv'})
    return (result or {}).get('channelgroups', [])


def get_group_channels(group_id):
    result = rpc('PVR.GetChannels', {
        'channelgroupid': group_id,
        'properties': ['channelid', 'label', 'channelnumber', 'icon', 'thumbnail', 'channeltype']
    })
    if result is None:
        return None
    return result.get('channels', [])


def all_channels(force=False):
    try:
        if not force and os.path.exists(CACHE_FILE):
            if time.time() - os.path.getmtime(CACHE_FILE) < CACHE_TTL:
                with open(CACHE_FILE, 'r', encoding='utf-8') as stream:
                    cached = json.load(stream)
                    if isinstance(cached, list):
                        return cached
    except Exception as exc:
        xbmc.log('Xtream Browser cache read failed: %s' % exc, xbmc.LOGWARNING)

    # Kodi's documented virtual group 'alltv' returns every TV channel
    # across all PVR groups in one request. This avoids slow per-group scans.
    channels = get_group_channels('alltv')
    if channels is None:
        xbmcgui.Dialog().notification('Kanal arama', 'Kodi PVR kanal listesi alınamadı', xbmcgui.NOTIFICATION_ERROR, 3000)
        return []
    try:
        xbmcvfs.mkdirs(PROFILE)
        temp_file = CACHE_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as stream:
            json.dump(channels, stream, ensure_ascii=False)
        os.replace(temp_file, CACHE_FILE)
    except Exception as exc:
        xbmc.log('Xtream Browser cache write failed: %s' % exc, xbmc.LOGWARNING)
    return channels


def channel_sort_key(channel):
    number = channel.get('channelnumber', 0)
    try:
        number = int(number)
    except Exception:
        number = 0
    return (number, norm(channel.get('label', '')))


def add_folder(label, mode, **kwargs):
    item = xbmcgui.ListItem(label=label)
    item.setArt({'icon': 'DefaultFolder.png', 'thumb': 'DefaultFolder.png'})
    xbmcplugin.addDirectoryItem(HANDLE, url_for(mode=mode, **kwargs), item, True)


def add_channel(channel):
    channel_id = int(channel['channelid'])
    name = str(channel.get('label') or 'Channel %s' % channel_id)
    number = channel.get('channelnumber', '')
    group = channel.get('group_label', '')
    prefix = ('%s  |  ' % number) if number not in ('', None, 0) else ''
    suffix = ('  [%s]' % group) if group else ''
    item = xbmcgui.ListItem(label=prefix + name + suffix)
    icon = channel.get('icon') or channel.get('thumbnail') or ''
    if icon:
        item.setArt({'icon': icon, 'thumb': icon})
    item.setInfo('video', {'title': name, 'mediatype': 'video'})
    item.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(HANDLE, url_for(mode='play', channelid=channel_id), item, False)


def root():
    xbmcplugin.setPluginCategory(HANDLE, 'TV Kanal Grupları')
    add_folder('Tüm kanallarda ara', 'search')
    add_folder('Kanal indeksini yenile', 'refresh')
    groups = get_groups()
    for group in groups:
        group_id = group.get('channelgroupid')
        label = group.get('label') or 'Grup %s' % group_id
        if group_id is not None:
            add_folder(label, 'group', groupid=group_id, groupname=label)
    xbmcplugin.endOfDirectory(HANDLE)


def show_group(group_id, group_name):
    xbmcplugin.setPluginCategory(HANDLE, group_name)
    channels = get_group_channels(group_id)
    if channels is None:
        xbmcgui.Dialog().notification('Kanal grubu', 'Grup kanalları alınamadı', xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    channels.sort(key=channel_sort_key)
    for channel in channels:
        channel['group_label'] = group_name
        add_channel(channel)
    xbmcplugin.endOfDirectory(HANDLE)


def search_channels(force=False):
    dialog = xbmcgui.Dialog()
    query = dialog.input('Tüm kanallarda ara', type=xbmcgui.INPUT_ALPHANUM)
    if not query:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    needle = norm(query)
    channels = all_channels(force=force)
    matches = []
    for channel in channels:
        name = norm(channel.get('label', ''))
        number = norm(channel.get('channelnumber', ''))
        if needle in name or needle in number:
            matches.append(channel)
    matches.sort(key=channel_sort_key)
    xbmcplugin.setPluginCategory(HANDLE, 'Arama: %s (%d)' % (query, len(matches)))
    for channel in matches:
        add_channel(channel)
    if not matches:
        xbmcgui.Dialog().notification('Kanal arama', 'Eşleşen kanal bulunamadı', xbmcgui.NOTIFICATION_INFO, 2500)
    xbmcplugin.endOfDirectory(HANDLE)


def play(channel_id):
    result = rpc('Player.Open', {'item': {'channelid': int(channel_id)}})
    if result is None:
        xbmcgui.Dialog().notification('Kanal', 'Kanal açılamadı', xbmcgui.NOTIFICATION_ERROR, 3000)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=result is not None)


def main():
    params = dict(parse_qsl(sys.argv[2][1:])) if len(sys.argv) > 2 else {}
    mode = params.get('mode', 'root')
    if mode == 'group':
        show_group(params.get('groupid'), params.get('groupname', 'Kanallar'))
    elif mode == 'search':
        search_channels()
    elif mode == 'refresh':
        all_channels(force=True)
        xbmcgui.Dialog().notification('Kanal indeksi', 'Tüm gruplar yenilendi', xbmcgui.NOTIFICATION_INFO, 2500)
        root()
    elif mode == 'play':
        play(params.get('channelid'))
    else:
        root()


if __name__ == '__main__':
    main()
