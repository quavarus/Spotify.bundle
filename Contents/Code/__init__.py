from utils import *
from playback import PlaybackService
from streamserver import StreamServer
from metadata import DataService

import modelMangler as m
from model import *

from lxml import etree

TITLE = L('Spotify')
ICON = 'icon-default.png'
ART = "concert.jpeg"
ABOUT = "about1_1.png"

VERSION = "0.1.2"

data = DataService()
playback = PlaybackService()
playback.start()
streamserver = StreamServer(playback)
cache = dict()

####################################################################################################
def Start():
  
  HTTP.CacheTime = None

  ObjectContainer.art = R(ART)
  Dict['LocalAddress']=Network.Address
  Dict['PublicAddress']=Network.PublicAddress
  Initialize()
  Thread.Create(refreshLibraryIndex)

def Initialize():
  Log.Debug("Initialize()")

  if not checkPreferences():
    data.Login(Prefs['username'], Prefs['password'])
    if data.Ready():

      playback.logout()
      playback.login(Prefs['username'], Prefs['password'])
      streamserver.stop()
      streamserver.start(int(Prefs['stream_port']))
      if 'library_user' not in Dict or Dict['library_user']!=Prefs['username']:
        buildLibraryIndex()
      
      if not 'saved_track_list' in cache:
        loadLibraryIndexGlobally()
      
    

####################################################################################################
@route(PREFIX + '/validate')
def ValidatePrefs(**kwargs):
  Log.Debug("ValidatePrefs()")
  if(checkPreferences()):
    Log.Debug(checkPreferences())
    return False

  Initialize() 
  if not data.Ready():
    Log.Debug("Preferences: Username or Password is not correct")
    return False

  return True

def checkPreferences():
  if not Prefs['username'] or len(Prefs['username'])==0:
    return "Preferences: Username and Password must be set"
  if not Prefs['password'] or len(Prefs['password'])==0:
    return "Preferences: Username and Password must be set"

  port = Prefs['stream_port']
  try:
    int(port)
  except ValueError:
    return "Preferences: Streaming Port is not a valid number"

  max_items = Prefs['max_page_items']
  try:
    int(max_items)
  except ValueError:
    return "Preferences: Max Items Per Page is not a valid number"
  
  return None

def refreshLibraryIndex():
  while True:
    try:
      if Prefs['library_refresh_interval'] == "Off":
        interval = 0
      elif Prefs['library_refresh_interval'] == "1 Minute":
        interval = 60*1
      elif Prefs['library_refresh_interval'] == "2 Minutes":
        interval = 60*2
      elif Prefs['library_refresh_interval'] ==  "5 Minutes":
        interval = 60*5
      elif Prefs['library_refresh_interval'] ==  "15 Minutes":
        interval = 60*15
      elif Prefs['library_refresh_interval'] ==  "1/2 Hour":
        interval = 60*30
      elif Prefs['library_refresh_interval'] ==  "1 Hour":
        interval = 60*60
      else:
        interval = 60*5

      if interval==0:
        Thread.Sleep(60*5)
      else:
        Thread.Sleep(interval)
        buildLibraryIndex()
    except Exception as ex:
      Log.Warn("An error ocurred refreshing library index. Will continue after next interval. ex=%s"%ex)

def buildLibraryIndex():
  Log.Debug('Start Refreshing Library Index')
  if data.Ready():
    tracks = {}
    albums = {}
    artistIds = set()
    artists = {}
    artistAlbums = {}
    
    items = data.LookupLibraryTracks()
    for item in items:
      track = item['track']
      tracks[track['id']] = track
      albums[track['album']['id']] = track['album']
      for artist in track['album']['artists']:
        artistIds.add(artist['id'])
        if not artist['id'] in artistAlbums:
          artistAlbums[artist['id']] = {}
        aAlbums = artistAlbums[artist['id']]
        aAlbums[track['album']['id']] = track['album']

    artistLookupList = []
    for id in artistIds:
      artistLookupList.append(id)
      if len(artistLookupList) == 50:
        fullArtists = data.LookupArtists(artistLookupList)
        for fullArtist in fullArtists:
          artists[fullArtist['id']] = fullArtist
        del artistLookupList[:]
    if len(artistLookupList) > 0:
      fullArtists = data.LookupArtists(artistLookupList)
      for fullArtist in fullArtists:
        artists[fullArtist['id']] = fullArtist


    Dict['library_user']=Prefs['username']
    cache['track_index'] = tracks
    trackList = sorted(tracks.values(), key=lambda t: t['name'].lower())
    cache['saved_track_list'] = trackList
    cache['album_index'] = albums
    cache['artist_index'] = artists
    cache['artist_albums_index'] = artistAlbums

    Data.SaveObject('library_track_index',tracks)
    Data.SaveObject('library_track_list',trackList)
    Data.SaveObject('library_album_index',albums)
    Data.SaveObject('library_artist_index',artists)
    Data.SaveObject('library_artist_albums_index',artistAlbums)

  Log.Debug('Finished Refreshing Library Index')

def loadLibraryIndexGlobally():

  if Dict['library_user']==Prefs['username']:
    if Data.Exists('library_track_index'):
      cache['track_index'] = Data.LoadObject('library_track_index')
    if Data.Exists('library_track_list'):
      cache['saved_track_list'] = Data.LoadObject('library_track_list')
    if Data.Exists('library_album_index'):
      cache['album_index'] = Data.LoadObject('library_album_index')
    if Data.Exists('library_artist_index'):
      cache['artist_index'] = Data.LoadObject('library_artist_index')
    if Data.Exists('library_artist_albums_index'):
      cache['artist_albums_index'] = Data.LoadObject('library_artist_albums_index')
  Log.Debug('Loaded Library Index Globally')

def getErrorMessage():
  if checkPreferences():
    return checkPreferences();
  if not data.Ready():
    return "Preferences: Username or Password is not correct"

def getDataServiceStatus():
  try:
    if data:
      if data.Ready():
        return L("Ready")
      else:
        return L("Authentication Failed")
    else:
      return L("Not Initialized")
  except NameError:
    return L("Not Initialized")

def getPlaybackServiceStatus():
  try:
    if playback:
      return playback.status
    else:
      return L("Not Initialized")
  except NameError:
    return L("Not Initialized")

def getStreamServiceStatus():
  try:
    if streamserver:
      return streamserver.status()
    else:
      return L("Not Initialized")
  except NameError:
    return L("Not Initialized")

####################################################################################################
@handler(PREFIX, TITLE, R(ART), R(ICON))
def MainMenu(**kwargs):
  errorMessage = getErrorMessage()
  oc = ObjectContainer(content=ContainerContent.Mixed,
    title_bar='True',
    title1=L('Spotify'),
    title2=L('Spotify'),
    no_cache=True,
    message = errorMessage,
    source_title=L('Spotify'))
  if errorMessage==None and data.Ready():
    oc.add(DirectoryObject(key=Callback(GetLibrary), title=L("Your Music"), thumb=R('yourMusic.png'), art=R(ART)))
    oc.add(DirectoryObject(key=Callback(GetCategories), title=L("Categories"), thumb=R('browse.png'), art=R(ART)))
    oc.add(DirectoryObject(key=Callback(GetFeaturedPlaylists), title=L("Featured Playlists"), thumb=R('featured.png'), art=R(ART)))
    oc.add(PopupDirectoryObject(key=Callback(GetNewReleases), title=L("New Releases"), thumb=R('newRelease1_1.png'), art=R(ART)))

  oc.add(PrefsObject(title=L('Preferences'), thumb=R('preferences1_1.png')))
  oc.add(PopupDirectoryObject(key=Callback(GetAbout), title=L("About"), thumb=R(ABOUT), art=R(ART)))  
  return oc

@route(PREFIX+"/about")
def GetAbout(**kwargs):
  # bulletPrefix = r' • '
  bulletPrefix = u'\u2001\u2022\u0020'
  directoryTemplate = r'<Directory art="'+R(ART)+r'" thumb="'+R("about1_1.png")+r'" key="'+Callback(GetAbout)+r'" title="%s"/>'
  content = r'<MediaContainer art="'+R(ART)+r'" title1="'+L("Spotify")+r'" title2="'+L("About")+r'" size="16" identifier="'+Plugin.Identifier+r'" sourceTitle="'+L("Spotify")+r'" mediaTagPrefix="/system/bundle/media/flags/" prefsKey="/:/plugins/'+Plugin.Identifier+r'/prefs">'
  content+= directoryTemplate%(L("Version")+": "+VERSION)
  content+= directoryTemplate%(bulletPrefix+L("Data Service Status")+": %s"%(getDataServiceStatus()))
  content+= directoryTemplate%(bulletPrefix+L("Playback Service Status")+": %s"%(getPlaybackServiceStatus()))
  content+= directoryTemplate%(bulletPrefix+L("Stream Service Status")+": %s"%(getStreamServiceStatus()))
  content+= directoryTemplate%(L("Code Credits"))
  content+= directoryTemplate%(bulletPrefix+r'&quot;pyspotify-ctypes&quot; by mazkolain (https://github.com/mazkolain/pyspotify-ctypes)')
  content+= directoryTemplate%(L("Icon Credits"))
  content+= directoryTemplate%(bulletPrefix+r'Artists Icon: &quot;Microphone&quot; Created By EliRatus from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'Playlists Icon: &quot;Music&quot; Created By Marco Galtarossa from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'Categories Icon: &quot;Records&quot; Created By Oliviu Stoian from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'New Releases Icon: &quot;Equalizer&quot; Created By Marco Galtarossa from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'Preferences Icon: &quot;Gears&quot; Created By Sergey Demushkin from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'About Icon: &quot;About&quot; Created By Hector from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'Next Icon: &quot;Right&quot; Created By Hea Poh Lin from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'Previous Icon: &quot;Left&quot; Created By Hea Poh Lin from the Noun Project')
  content+= directoryTemplate%(bulletPrefix+r'Featured Playlists Icon: &quot;Star&quot; Created By Kevin from the Noun Project')

  content+= r'</MediaContainer>'
  Log(content)
  tree = etree.fromstring(str(content))
  return tree
  # oc = ObjectContainer(title2=L("About"))
  # oc.add(DirectoryObject(key=Callback(GetAbout), title=L("Version")+": "+VERSION, thumb=R(ABOUT)))
  # oc.add(DirectoryObject(key=Callback(GetAbout), title=u'●'+L("Data Service Status")+": %s"%(getDataServiceStatus()), thumb=R(ABOUT)))
  # oc.add(DirectoryObject(key=Callback(GetAbout), title=u'●'+L("Playback Service Status")+": %s"%(getPlaybackServiceStatus()), thumb=R(ABOUT)))
  # oc.add(DirectoryObject(key=Callback(GetAbout), title=u'\u0149'+L("Stream Service Status")+": %s"%(getStreamServiceStatus()), thumb=R(ABOUT)))
  # oc.add(DirectoryObject(key=Callback(GetAbout), title=L("Credits"), thumb=R(ABOUT)))
  # return oc

@route(PREFIX+"/library")
def GetLibrary(**kwargs):
  oc = ObjectContainer(title2=L("Your Music"))
  oc.add(DirectoryObject(key=Callback(GetLibraryArtists), title=L("Artists"), thumb=R('artists.png'), art=R(ART)))
  oc.add(DirectoryObject(key=Callback(GetLibraryAlbums), title=L("Albums"), thumb=R('albums.png'), art=R(ART)))
  oc.add(DirectoryObject(key=Callback(GetLibraryTracks), title=L("Songs"), thumb=R('songs.png'), art=R(ART)))
  oc.add(DirectoryObject(key=Callback(GetMyPlaylists), title=L("Playlists"), thumb=R('playlists.png'), art=R(ART)))
  
  return oc

@route(PREFIX+"/categories")
def GetCategories(**kwargs):
  categories = data.LookupCategories()
  oc = ObjectContainer(title2=L("Browse"))
  for category in categories:
    oc.add(DirectoryObject(key=Callback(GetCategoryPlaylists, id=category['id'], name=category['name']), title=category['name'], thumb=FindBiggestImage(category['icons']), art=R(ART)))
  return oc

@route(PREFIX+"/featured")
def GetFeaturedPlaylists(**kwargs):
  playlists = data.LookupFeaturedPlaylists()
  oc = ObjectContainer(title2=L('Featured'))
  for playlist in playlists:
    oc.add(PlaylistObject(key=Callback(GetPlaylistTracks, owner=playlist['owner']['id'], id=playlist['id'] ), title=playlist['name'], thumb=FindBiggestImage(playlist['images']), art=R(ART)))
  return oc

@route(PREFIX+"/categories/{id}/playlists")
def GetCategoryPlaylists(id, **kwargs):
  playlists = data.LookupCategoryPlaylists(id)
  oc = ObjectContainer(title2=kwargs['name'])
  for playlist in playlists:
    oc.add(PlaylistObject(key=Callback(GetPlaylistTracks, owner=playlist['owner']['id'], id=playlist['id'] ), title=playlist['name'], thumb=FindBiggestImage(playlist['images']), art=R(ART)))
  return oc

@route(PREFIX + '/my/tracks')
def GetLibraryTracks(page=1, **kwargs):
  Log.Debug('listMyTracks')
  
  itemsPerPage = int(Prefs['max_page_items'])
  
  tracks = cache['saved_track_list']
  totalTracks = len(tracks)
  Log.Debug('totalTracks= %s'%(totalTracks))
  endIndex = int(page)*itemsPerPage
  startIndex = endIndex-itemsPerPage
  endIndex = min(endIndex,totalTracks)

  oc = ObjectContainer(title2=L("Songs"), no_history=True, replace_parent=True)

  if int(page)>1:
    oc.add(DirectoryObject(key=Callback(GetLibraryTracks, page=int(page)-1), title=L("Previous"), thumb=R('back1_1.png')))
  for track in tracks[startIndex:endIndex]:
    callback = Callback(GetTrack, id=track['id'], transcode=Prefs['force_transcode'])
    oc.add(BuildTrack(track['album'],track, callback, Prefs['force_transcode']))
  if endIndex<totalTracks: 
    oc.add(NextPageObject(key=Callback(GetLibraryTracks, page=int(page)+1), title=L("Next"), thumb=R('next1_1.png')))
  return oc

@route(PREFIX+'/my/playlists')
def GetMyPlaylists(**kwargs):
  playlists = data.LookupLibraryPlaylists()
  oc = ObjectContainer(title2=L("Playlists"))
  for playlist in playlists:
    oc.add(PlaylistObject(key=Callback(GetPlaylistTracks, owner=playlist['owner']['id'], id=playlist['id']), title=playlist['name'], thumb=FindBiggestImage(playlist['images']), art=R(ART)))
  return oc

@route(PREFIX+'/playlists/{owner}/{id}')
def GetPlaylistTracks(owner, id, **kwargs):
  tracks = data.LookupPlaylistTracks(owner,id)
  oc = ObjectContainer()
  for trackInfo in tracks:
    track = trackInfo['track']
    if track['id']:
      callback = Callback(GetTrack, id=track['id'], transcode=Prefs['force_transcode'])
      oc.add(BuildTrack(track['album'], track, callback, Prefs['force_transcode']))
  return oc

@route(PREFIX + '/library/artists')
def GetLibraryArtists(page=1, **kwargs):
  Log.Debug('listMyArtists')

  artists = cache['artist_index']
  totalTracks = len(artists)
  if useLibraryMode():
    itemsPerPage = totalTracks
  else:
    itemsPerPage = int(Prefs['max_page_items'])
  # Log.Debug('totalTracks= %s'%(totalTracks))
  endIndex = int(page)*itemsPerPage
  startIndex = endIndex-itemsPerPage
  endIndex = min(endIndex,totalTracks)

  oc = ObjectContainer(title2=L("Artists"), content="artist", no_cache=True, mixed_parents=True)
  if useLibraryMode()==True:
    oc.identifier="com.plexapp.plugins.library"
  if int(page)>1:
    oc.add(DirectoryObject(key=Callback(GetLibraryArtists, page=int(page)-1), title=L("Previous"), thumb=R('back1_1.png')))
  sortedArtists = sorted(artists.values(), key=lambda a: a['name'].lower())
  for artist in sortedArtists[startIndex:endIndex]:
    if useLibraryMode()==True:
      callback = Callback(GetLibraryArtistChildren, id=artist['id'])
    else:
      callback = Callback(GetLibraryArtistAlbums, id=artist['id'])
    oc.add(BuildArtist(artist, callback))
  if endIndex<totalTracks: 
    oc.add(NextPageObject(key=Callback(GetLibraryArtists, page=int(page)+1), title=L("Next"), thumb=R('next1_1.png')))
  return oc

@route(PREFIX + '/newreleases')
def GetNewReleases(**kwargs):
  albums = data.LookupNewReleases()
  oc = ObjectContainer(title2=L("Albums"), no_cache=True, mixed_parents=True)
  if useLibraryMode()==True:
    oc.identifier="com.plexapp.plugins.library"
  for album in albums: 
    if useLibraryMode()==True:
      callback = Callback(GetAlbumChildren, id=album['id'])
    else:
      callback = Callback(GetAlbumTracks, id=album['id'])
    oc.add(BuildAlbum(album, album['artists'][0], callback))
  return oc

@route(PREFIX + '/library/albums')
def GetLibraryAlbums(page=1, **kwargs):
  Log.Debug('listMyAlbums')

  
  
  albums = cache['album_index']
  totalTracks = len(albums)
  if useLibraryMode():
    itemsPerPage = totalTracks
  else:
    itemsPerPage = int(Prefs['max_page_items'])
  # Log.Debug('totalTracks= %s'%(totalTracks))
  endIndex = int(page)*itemsPerPage
  startIndex = endIndex-itemsPerPage
  endIndex = min(endIndex,totalTracks)

  oc = ObjectContainer(title2=L("Albums"), no_cache=True, mixed_parents=True)
  if useLibraryMode()==True:
    oc.identifier="com.plexapp.plugins.library"

  if int(page)>1:
    oc.add(DirectoryObject(key=Callback(GetLibraryAlbums, page=int(page)-1), title=L("Previous"), thumb=R('back1_1.png')))
  sortedAlbums = sorted(albums.values(), key=lambda a: a['name'].lower())
  for album in sortedAlbums[startIndex:endIndex]:
    if useLibraryMode()==True:
      callback = Callback(GetLibraryAlbumChildren, id=album['id'])
    else:
      callback = Callback(GetLibraryAlbumTracks, id=album['id'])
    oc.add(BuildAlbum(album, album['artists'][0], callback))
  if endIndex<totalTracks: 
    oc.add(NextPageObject(key=Callback(GetLibraryAlbums, page=int(page)+1), title=L("Next"), thumb=R('next1_1.png')))
  return oc

@route(PREFIX + "/my/artists/{id}")
def GetLibraryArtist(id, **kwargs):
  Log.Debug("GetLibraryArtist(id={0})".format(id))
  artist = cache['artist_index'][id]
  oc = ObjectContainer()
  if useLibraryMode()==True:
    callback = Callback(GetLibraryArtistChildren, id=artist['id'])
  else:
    callback = Callback(GetLibraryArtistAlbums, id=artist['id'])
  oc.add(BuildArtist(artist, callback))
  return oc

@route(PREFIX + "/artists/{id}")
def GetArtist(id, **kwargs):
  Log.Debug("GetArtist(id={0})".format(id))
  artist = data.LookupArtist(id)  
  oc = ObjectContainer()
  if useLibraryMode()==True:
    callback = Callback(GetArtistChildren, id=artist['id'])
  else:
    callback = Callback(GetArtistAlbums, id=artist['id'])
  oc.add(BuildArtist(artist, callback))
  return oc

@route(PREFIX + '/my/artists/{id}/children')
def GetLibraryArtistChildren(id, **kwargs):
  return GetLibraryArtistAlbums(id, **kwargs)

@route(PREFIX + '/my/artists/{id}/albums')
def GetLibraryArtistAlbums(id, **kwargs):
  artist = cache['artist_index'][id]
  artistAlbums = cache['artist_albums_index'][id]
  albums = artistAlbums.values()
  oc = ObjectContainer(art=FindBiggestImage(artist['images']),no_cache=True, title1="Artist", title2=artist['name'])
  if useLibraryMode()==True:
    oc.identifier="com.plexapp.plugins.library"
  for album in albums:
    # if album['id'] in cache['album_index']:
    if useLibraryMode()==True:
      callback = Callback(GetLibraryAlbumChildren, id=album['id'])
    else:
      callback = Callback(GetLibraryAlbumTracks, id=album['id'])
    oc.add(BuildAlbum(album,artist,callback))
  return oc

@route(PREFIX + "/artists/{id}/children")
def GetArtistChildren(id, **kwargs):
  return GetArtistAlbums(id,**kwargs)

@route(PREFIX + "/artists/{id}/albums")
def GetArtistAlbums(id, **kwargs):
  Log.Debug("GetArtistAlbums(id={0})".format(id))
  artist = data.LookupArtist(id)
  albums = data.LookupArtistAlbums(id)
  oc = ObjectContainer(art=FindBiggestImage(artist['images']),no_cache=True, title1="Artist", title2=artist['name'])
  if useLibraryMode()==True:
    oc.identifier="com.plexapp.plugins.library"
  for album in albums:
    if useLibraryMode()==True:
      callback = Callback(GetAlbumChildren, id=album['id'])
    else:
      callback = Callback(GetAlbumTracks, id=album['id'])
    oc.add(BuildAlbum(album,artist,callback))
  return oc

@route(PREFIX + "/albums/{id}")
def GetAlbum(id, **kwargs):
  Log.Debug("GetAlbum(id={0})".format(id))
  oc = ObjectContainer(no_cache=True)
  album = data.LookupAlbum(id)
  if useLibraryMode()==True:
    callback = Callback(GetAlbumChildren, id=album['id'])
  else:
    callback = Callback(GetAlbumTracks, id=album['id'])
  do = BuildAlbum(album, album['artists'][0], callback)
  oc.add(do)
  return oc

@route(PREFIX + "/my/albums/{id}")
def GetLibraryAlbum(id, **kwargs):
  Log.Debug("GetAlbum(id={0})".format(id))
  album = cache['album_index'][id]
  artist = album['artists'][0]
  oc = ObjectContainer(no_cache=True)
  if useLibraryMode()==True:
    callback = Callback(GetLibraryAlbumChildren, id=album['id'])
  else:
    callback = Callback(GetLibraryAlbumTracks, id=album['id'])
  do = BuildAlbum(album, artist, callback)
  oc.add(do)
  return oc

@route(PREFIX + '/my/albums/{id}/children')
def GetLibraryAlbumChildren(id, **kwargs):
  return GetLibraryAlbumTracks(id, **kwargs)
  
@route(PREFIX + '/my/albums/{id}/tracks')
def GetLibraryAlbumTracks(id, **kwargs):
  Log.Debug("GetLibraryAlbumTracks(id={0}, args={1})".format(id, kwargs))
  album =  data.LookupAlbum(id)
  artist = album['artists'][0]

  icon = FindBiggestImage(album['images'])
  oc = ObjectContainer(title1=album['artists'][0]['name'], title2=album['name'], no_cache=True, art=icon)
  for track in album['tracks']['items']:
    if track['id'] in cache['track_index']:
      callback = Callback(GetTrack, id=track['id'], transcode=Prefs['force_transcode'])
      oc.add(BuildTrack(album, track, callback, Prefs['force_transcode']))
  return oc


@route(PREFIX + '/albums/{id}/children')
def GetAlbumChildren(id, **kwargs):
  return GetAlbumTracks(id, **kwargs)
  
@route(PREFIX + '/albums/{id}/tracks')
def GetAlbumTracks(id, **kwargs):
  Log.Debug("GetAlbumTracks(id={0}, args={1})".format(id, kwargs))
  album = data.LookupAlbum(id)
  
  icon = FindBiggestImage(album['images'])
  oc = ObjectContainer(title1=album['artists'][0]['name'], title2=album['name'], no_cache=True, art=icon)
  for track in album['tracks']['items']:
    callback = Callback(GetTrack, id=track['id'], transcode=Prefs['force_transcode'])
    oc.add(BuildTrack(album, track, callback, Prefs['force_transcode']))
  return oc

@route(PREFIX + '/tracks/{id}')
def GetTrack(id, transcode=False, **kwargs):
  Log.Debug("GetTrack(id={0}, transcode={1})".format(id,transcode))
  track = data.LookupTrack(id)
  album = track['album']
  oc = ObjectContainer()
  callback = Callback(GetTrack, id=track['id'], transcode = transcode)
  oc.add(BuildTrack(album,track,callback, transcode))
  return oc
