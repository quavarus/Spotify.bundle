# -*- coding: utf-8 -*-
PREFIX = '/video/spotify'

TITLE = L('Spotify')
ART = 'art-default.jpg'
ICON = 'icon-default.png'
PREFS = 'icon-preferences.png'

CLIENT_ID = 'efd43383e71247d6a7f1e244a830a7da'
CLIENT_SECRET = '55034426c8794a19a66a8ae834227903'
AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'




####################################################################################################
def Start():
  InputDirectoryObject.thumb = R('Search.png')
  InputDirectoryObject.art = R(ART)

  HTTP.CacheTime = CACHE_1HOUR
  #HTTP.Headers['User-Agent'] = USER_AGENT
#  HTTP.Headers['X-GData-Key'] = "key=%s" % DEVELOPER_KEY

#  Dict.Reset()
  Authenticate()

####################################################################################################
@route(PREFIX + '/validate')
def ValidatePrefs():
  Log ("ValidatePrefs()")
  Authenticate()

####################################################################################################
@handler(PREFIX, TITLE, R(ART), R(ICON))
def MainMenu():
  oc = ObjectContainer(no_cache = True)
  if Authenticate()==True:
    oc.add(DirectoryObject(key=Callback(listMyAlbums), title="My Albums"))
#  return ObjectContainer(header="Empty", message="Maybe Authenticated.")  
  oc.add(PrefsObject(title='Preferences'))
  return oc

@route(PREFIX + '/my/albums')
def listMyAlbums():
  url = "https://api.spotify.com/v1/me/albums"
  response = ApiRequest(url)
  # Log (response)
  oc = ObjectContainer(title2="My Albums")
  items = response['items']
  for item in items:
    album = item['album']
    icon = ""
    iconSize = 0
    for image in album['images']:
      if image['width']>iconSize:
        icon = image['url']
        iconSize = image['width']
    oc.add(AlbumObject(key=PREFIX+"/albums/"+album['id'], rating_key=album['id'], title=album['name'], thumb=icon))
  return oc
  
@route(PREFIX + '/albums/{id}')
def GetAlbum(id):
  url = "https://api.spotify.com/v1/albums/"+id
  album = ApiRequest(url)
  oc = ObjectContainer(title2=album['name'])
  for track in album['tracks']['items']:
    trackId = track['id']
    trackDuration = track['duration_ms']
    trackTitle = track['name']
    trackNumber = track['track_number']
    albumName = album['name']
    artistName = track['artists'][0]['name']
    genres = []
    tags = []
    rating=0.0
    sourceTitle="Spotify"
    Log ("trackId="+trackId+" trackDuration="+str(trackDuration)+" trackTitle="+trackTitle+" trackNumber="+str(trackNumber)+" albumName="+albumName+" artistName="+artistName)
    oc.add(TrackObject(key=PREFIX+"/tracks/"+trackId, rating_key=trackId, duration=trackDuration, title=trackTitle, index=trackNumber, artist=artistName, album=albumName,  genres=genres, tags=tags,  rating=rating, source_title=sourceTitle))
  return oc

@route(PREFIX + '/tracks/{id}')
def GetTrack(id):
  pass


def ApiRequest(url):
#  try:
    Log ("ApiRequest(url) url="+url)
    Log ("ApiRequest(url) access_token="+Dict['access_token'])
    headers = {"Authorization":"Bearer "+Dict['access_token']}
    return JSON.ObjectFromURL(url, headers=headers)
#  except HTTPError as err:
#    Log ("HTTPError "+err)



####################################################################################################
## AUTHENTICATION
####################################################################################################
@route(PREFIX + '/authenticate')
def Authenticate():
  Log ("Authenticate()")
   
  if Prefs['code'] and Prefs['code']!=Dict['code']:  
    if 'access_token' in Dict:
      del Dict['access_token']
    code = Prefs['code']
    Dict['code']=code
    authRequest = "https://accounts.spotify.com/api/token"
    postValues = {}
    postValues["grant_type"]="authorization_code"
    postValues["code"]=code
    postValues["redirect_uri"]="https%3A%2F%2Fquavarus.github.io%2FSpotify.bundle%2FWeb%2Fcallback.htm"
    postValues["client_id"]=CLIENT_ID
    postValues["client_secret"]=CLIENT_SECRET
#    headers = {'Authorization':'Basic '+String.Encode(CLIENT_ID+":"+CLIENT_SECRET)}
    # Prefs['code'] = None
    Log (authRequest)
    Log (code)
    authResponse = JSON.ObjectFromURL(authRequest, values=postValues)
    Dict['access_token'] = authResponse['access_token']
    Dict['refresh_token'] = authResponse['refresh_token']
    Dict['expires_in'] = authResponse['expires_in']
    Log (Dict['access_token'])

  if 'access_token' in Dict:
    return True
  else:
    return False

