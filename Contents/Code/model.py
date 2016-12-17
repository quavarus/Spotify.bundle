import modelMangler as m
from utils import *

ART = 'concert.jpeg'

def BuildArtist(artist, callback):
  
  do = DirectoryObject(key=callback, title=artist['name'], thumb=FindBiggestImage(artist['images']))
  if Client.Product in ['Plex Web']:
    do.art=R(ART)
  else:
    do.art=FindBiggestImage(artist['images'])
  # turns on the library artist view
  do = m.addAttribute(do,"type","artist")
  do = m.addAttribute(do,"ratingKey", artist['id'])
  return do


def BuildAlbum(album, artist, callback):  

  icon = FindBiggestImage(album['images'])
  
  if useLibraryMode()==True:
    do = DirectoryObject()
    # turns on the library album view
    do = m.addAttribute(do,"type",'album')
  else:
    do = PlaylistObject()

  do.key = callback
  do.title=album['name']
  do.thumb=icon 
  # if 'images' in artist:
  # do.art=FindBiggestImage(artist['images'])
  do.art=R(ART)
  do.summary=""

  # do = m.addAttribute(do,"allowSync","0")
  # if 'tracks' in album:
  #   do = m.addAttribute(do,"leafCount",len(album['tracks']))
  # do = m.addAttribute(do,"parentRatingKey",artist['id'])
  # do = m.addAttribute(do,"index","1")

  # shows the artist image above the album image
  if 'images' in artist:
    do = m.addAttribute(do,"parentThumb",FindBiggestImage(artist['images']))
  # stops from clients from showing duplicated albums in the artist view
  do = m.addAttribute(do,"ratingKey", album['id'])
  # adds the artist name to the album view
  do = m.addAttribute(do,"parentTitle",artist['name'])
  # enables the go to artist link in some clients
  do = m.addAttribute(do,"parentKey","{0}/artists/{1}".format(PREFIX,artist['id']))
  # adds the release year to the album view
  if 'release_date' in album:
    do = m.addAttribute(do,"year",album['release_date'][:4])
  return do

# def BuildTrack(album, track):
#   artist = track['artists'][0]
#   trackId = track['id']
#   trackDuration = track['duration_ms']
#   trackTitle = track['name']
#   trackNumber = track['track_number']
#   albumName = album['name']
#   artistName = artist['name']
#   genres = []
#   tags = []
#   rating=0.0
#   sourceTitle=None
#   icon = ""
#   iconSize = 0
#   for image in album['images']:
#     if image['width']>iconSize:
#       icon = image['url']
#       iconSize = image['width']
#   trackUrl = "http://{0}:8090/track?track_id={1}".format('localhost', track['id'])
#   items = [MediaObject(audio_channels=2, audio_codec="mp3", container="mp3", duration=trackDuration, parts=[PartObject(key=TranscodeTrack(trackId),duration=trackDuration,streams=[AudioStreamObject(channels=2, codec="mp3", duration=trackDuration, bitrate=320)])])]
#   to = TrackObject(key=Callback(GetTrack, id=trackId), rating_key="track:"+trackId, duration=trackDuration, title=trackTitle, index=trackNumber, artist=artistName, album=albumName,  genres=genres, tags=tags,  rating=rating, source_title=sourceTitle, items=items, thumb=icon, art=icon)
#   return to

def BuildTrack(album, track, callback, transcode=False):
  transcode = str(transcode).lower()
  artist = track['artists'][0]
  trackId = track['id']
  trackDuration = track['duration_ms']
  trackTitle = track['name']
  trackNumber = track['track_number']
  albumName = album['name']
  artistName = artist['name']
  genres = []
  tags = []
  rating=0.0
  sourceTitle=None
  icon = FindBiggestImage(album['images'])
  port = Prefs['stream_port']
  trackUrl = "http://{0}:{1}/stream/{2}".format(Dict['LocalAddress'], port, track['id'])
  if transcode=="true":
    mediaItem = BuildMP3Media(trackId, trackDuration)
  else:
   mediaItem=BuildWavMedia(trackId, trackDuration)
  items = [mediaItem]
  to = TrackObject(key=callback, rating_key=trackId, duration=trackDuration, title=trackTitle, index=trackNumber, artist=artistName, album=albumName,  genres=genres, tags=tags,  rating=rating, source_title=sourceTitle, items=items, thumb=icon, art=icon)
  return to

def isExternal():
  host = getattr(Request,'_context').request.host
  hostSplit = host.split(":")
  return hostSplit[0]==Dict['PublicAddress']

def BuildWavMedia(trackId, trackDuration):
  port = Prefs['stream_port']
  if isExternal():
    address = Dict['PublicAddress']
  else:
    address = Dict['LocalAddress']
  trackUrl = "http://{0}:{1}/stream/{2}".format(address, port, trackId)
  return MediaObject(audio_channels=2, audio_codec="pcm", container="wav", duration=trackDuration, parts=[PartObject(key=trackUrl,duration=trackDuration,streams=[AudioStreamObject(channels=2, codec="pcm", duration=trackDuration, bitrate=320)])])

def BuildMP3Media(trackId, trackDuration):
  return MediaObject(audio_channels=2, audio_codec="mp3", container="mp3", duration=trackDuration, parts=[PartObject(key=TranscodeTrack(trackId),duration=trackDuration,streams=[AudioStreamObject(channels=2, codec="mp3", duration=trackDuration, bitrate=320)])])

def TranscodeTrack(trackId):
  # address=Network.PublicAddress
  # address=Network.Address
  url=""
  # url+="http://"+address+":32400"
  url+="/music/:/transcode/universal/start.mp3"
  url+="?audioBoost=100"
  url+="&autoAdjustQuality=0"
  url+="&directPlay=0"
  url+="&directStream=1"
  url+="&fastSeek=1"
  url+="&hasMDE=1"
  url+="&location=lan"
  url+="&maxVideoBitrate=8000"
  url+="&partIndex=0"
  url+="&path=%2Fmusic%2Fspotify%2Ftracks%2F"+trackId
  url+="&protocol=http"
  # url+="&session=f43de870c826ee07-com-plexapp-android"
  # url+="&subtitleSize=100"
  url+="&videoQuality=60"
  url+="&videoResolution=1920x1080"
  url+="&X-Plex-Platform=Windows"
  # url+="&X-Plex-Token=iZu184C2QEMtq3zpEFnp"
  return url


def FindBiggestImage(images):
  # icon = ""
  # iconSize = 0
  # for image in images:
  #   if image['width']>iconSize:
  #     icon = image['url']
  #     iconSize = image['width']
  # return icon
  # according to the docs the widest is first
  if len(images)>0:
    return images[0]['url']
  else:
  	return None


def useLibraryMode():
  # Log.Debug('useLibraryMode() Product=%s Platform=%s Version=%s'%(Client.Product, Client.Platform, Client.Version))
  # Log.Debug(Request.Headers)
  if Client.Product in ['Plex Media Player','Plex for Xbox One']:
    return False
  if Client.Platform in ['Konvergo']:
  	return False

  return Prefs['enable_library_mode']
