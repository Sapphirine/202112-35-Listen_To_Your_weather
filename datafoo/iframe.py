
def getIframePlaylist(playlist_id):
    """ Utilizes playlist_id to create a url for iframe """
    open_base_url = 'https://open.spotify.com/embed?uri=spotify'
    iframe_playlist_url = '{}:playlist:{}'.format(open_base_url,playlist_id)

    return iframe_playlist_url

def getIframeTrackList(raw_track_list):
    """ Utilizes a list of tracklist, unfiltered, to create a track url for iframe """
    open_base_url = 'https://open.spotify.com/embed?uri=spotify'
    track_id = [x.get('id') for x in raw_track_list]
    iframe_url = ['{}:track:{}'.format(open_base_url,track) for track in track_id]
    return iframe_url