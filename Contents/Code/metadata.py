import urllib2
import base64
import re
import modelMangler as m


CLIENT_ID = 'efd43383e71247d6a7f1e244a830a7da'
CLIENT_SECRET = '55034426c8794a19a66a8ae834227903'
AUTHORIZE_URL_BASE = 'https://accounts.spotify.com/authorize'

RESPONSE_TYPE = "code"
SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"
CALLBACK_URL = "https://quavarus.github.io/Spotify.bundle/Web/callback.htm"
AUTHORIZE_URL = "%s?client_id=%s&response_type=%s&scope=%s&redirect_uri=%s"%(AUTHORIZE_URL_BASE,CLIENT_ID,RESPONSE_TYPE,String.Quote(SCOPE),String.Quote(CALLBACK_URL))
LOGIN_URL = 'https://accounts.spotify.com/api/login'
ACCEPT_URL = 'https://accounts.spotify.com/en/authorize/accept'
HOST_URL = r'accounts.spotify.com'
ORIGIN_URL = r'https://accounts.spotify.com'

class DataService():

  def __init__(self, username, password):
    Log('init DataService')
    self.username = username
    self.password = password
    Dict['password'] = password
    if self.username == Dict['username']:
      self.access_token = Dict['access_token']
      self.refresh_token = Dict['refresh_token']
      if not self.verifyCommunication():
        self.ReAuthenticate()
    else:
      self.access_token=None
      self.refresh_token=None
      self.Authenticate()

    

  def ReAuthenticate(self):
    try:
      responseObject= self.callAuthorize()
      if "redirect" in responseObject:
        return self.processRedirect(responseObject['redirect'])
      
      Log.Debug("-------------------------------------------------------------------------------------------")

      bon = responseObject['BON']
      bon = self.calculateBonCookie(bon)
      responseObject = self.callLogin(bon)

      Log.Debug("-------------------------------------------------------------------------------------------")
      referer = "%s?continue=%s"%(LOGIN_URL, String.Quote(AUTHORIZE_URL))
      responseObject = self.callAuthorize({"__bon":bon,"remember":self.username}, {"Referer":referer})
      if "redirect" in responseObject:
        return self.processRedirect(responseObject['redirect'])
      Log.Debug("-------------------------------------------------------------------------------------------")

      responseObject = self.callAccept(bon)
      if "redirect" in responseObject:
        return self.processRedirect(responseObject['redirect'])
    except urllib2.HTTPError as e:
      Log.Debug(e)
      return None


    Log.Debug("-------------------------------------------------------------------------------------------")

  def Authenticate(self):
    HTTP.ClearCookies()
    HTTP.ClearCache()
    return self.ReAuthenticate()

  def Ready(self):
    if(self.access_token):
      return True
    else:
      return False

  def verifyCommunication(self):
    try:
      user = self.LookupMyProfile()
      if user['id']==self.username:
        return True
      else:
        return True
    except Exception as e:
      return False


  # def urlEncodeParams(self, params):
  #   returnValue=""
  #   for key, value in params.iteritems():
  #     if len(returnValue) > 0:
  #       returnValue+="&"
  #       param = "%s=%s"%(key, String.Quote(value))
  #     returnValue+=param
  #   return returnValue

  def callAuthorize(self, additionalCookies=None, additionalHeaders=None):
    
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}
    headers['Accept']='application/json, text/plain, */*'

    if additionalCookies:
      cookies = self.parseCookies(HTTP.CookiesForURL(AUTHORIZE_URL))
      for key, value in additionalCookies.iteritems():
        cookies[key] = value
      headers['Cookie']=self.cookiesFromDict(cookies), 

    if additionalHeaders:
      for key, value in additionalHeaders.iteritems():
        headers[key]=value

    request = HTTP.Request(AUTHORIZE_URL, headers=headers, immediate=True)
    cookies = self.parseCookies(HTTP.CookiesForURL(AUTHORIZE_URL))
    Log.Debug(self.parseCookies(HTTP.CookiesForURL(AUTHORIZE_URL)))
    Log.Debug(request.content)
    return JSON.ObjectFromString(request.content)

  def callLogin(self, bon):

    cookies = self.parseCookies(HTTP.CookiesForURL(AUTHORIZE_URL))
    csrf_token = cookies['csrf_token']
    
    cookies["__bon"] = bon
    cookies['fb_continue']= String.Quote(AUTHORIZE_URL)
    cookies['remember']=self.username
    
    Log.Debug(cookies)
    
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}
    headers['Accept']='application/json, text/plain, */*'
    headers['Content-Type']='application/x-www-form-urlencoded'
    headers['Cookie']=self.cookiesFromDict(cookies)
    headers['Host']=HOST_URL
    headers['Origin']=ORIGIN_URL
    headers['Referer']="%s?continue=%s"%(LOGIN_URL, String.Quote(AUTHORIZE_URL))

    values = {'username':self.username, 'password':self.password, 'csrf_token':csrf_token, 'remember':'true'}
   
    request = HTTP.Request(LOGIN_URL, values=values, headers=headers, immediate=True)
    cookies = self.parseCookies(HTTP.CookiesForURL(LOGIN_URL))
    Log.Debug(cookies)
    Log.Debug(request.headers)
    Log.Debug(request.content)
    return JSON.ObjectFromString(request.content)

  def callAccept(self, bon):
    cookies = self.parseCookies(HTTP.CookiesForURL(LOGIN_URL))
    cookies["__bon"] = bon
    cookies['remember']=self.username

    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}
    headers['Accept']='application/json, text/plain, */*'
    headers['Content-Type']='application/x-www-form-urlencoded'
    headers['Cookie']=self.cookiesFromDict(cookies), 
    headers['Origin']=ORIGIN_URL
    headers['Cookie']=self.cookiesFromDict(cookies), 
    headers['Referer']=AUTHORIZE_URL

    values=dict()
    values['client_id']=CLIENT_ID
    values['response_type']=RESPONSE_TYPE
    values['scope']=SCOPE
    values['redirect_uri']=CALLBACK_URL
    values['csrf_token']=cookies['csrf_token']
    request = HTTP.Request(ACCEPT_URL, values=values, headers=headers, immediate=True)
    cookies = self.parseCookies(HTTP.CookiesForURL(ACCEPT_URL))
    Log.Debug(cookies)
    Log.Debug(request.headers)
    Log.Debug(request.content)
    return JSON.ObjectFromString(request.content)

  def processRedirect(self, redirect):
    Log.Debug(redirect)
    params = self.parseUrlParams(redirect)
    if 'code' in params:
      authRequest = "https://accounts.spotify.com/api/token"
      postValues = {}
      postValues["grant_type"]="authorization_code"
      postValues["code"]=params['code']
      postValues["redirect_uri"]=String.Quote(CALLBACK_URL)
      postValues["client_id"]=CLIENT_ID
      postValues["client_secret"]=CLIENT_SECRET

      authResponse = JSON.ObjectFromURL(authRequest, values=postValues)

      self.access_token = authResponse['access_token']
      self.refresh_token = authResponse['refresh_token']
      Dict['access_token'] = authResponse['access_token']
      Dict['refresh_token'] = authResponse['refresh_token']
      Dict['username'] = self.username
      self.expires_in = authResponse['expires_in']
      return self.access_token

  def calculateBonCookie(self, bon):
    last = bon[len(bon)-1]
    del bon[len(bon)-1]
    bon.append(str(last))
    bon.append(str(last*42))
    bon.append('1')
    bon.append('1')
    bon.append('1')
    bon.append('1')
    bon="|".join(bon)
    return base64.b64encode(bon)

  def parseUrlParams(self, url):
    returnValue = dict()
    urlParamSplit = url.split("?")
    if len(urlParamSplit)>1:
      params = url.split("?")[1]
      params = params.split("&")
      for param in params:
        keyValueSplit = param.split("=")
        returnValue[keyValueSplit[0]] = String.Unquote(keyValueSplit[1])
    return returnValue

  def parseCookies(self, cookieString):
    splits = cookieString.split(';')
    returnValue = dict()
    for split in splits:
      # split = split.strip()
      keyValue = split.split("=")
      returnValue[keyValue[0].strip()] = keyValue[1].strip()
    return returnValue

  def cookiesFromDict(self, cookieDict):
    returnValue = ""
    for key, value in cookieDict.iteritems():
      if(len(returnValue)>0):
        returnValue+="; "
      returnValue+="%s=%s"%(key, value)
    return returnValue

  def request(self, url):
    try:
      # Log.Debug("self.request(url) url="+url)
      # Log.Debug("self.request(url) access_token=%s"%(self.access_token))
      headers = {"Authorization":"Bearer %s"%(self.access_token)}
      return JSON.ObjectFromURL(url, headers=headers)
    except urllib2.HTTPError as e:
      Log.Debug('self.request(url) failed %s'%(e.code))
      if e.code==401:
        Log.Debug('self.request(url) reauth retrying')
        newToken = self.refreshAccessToken()
        headers = {"Authorization":"Bearer "+newToken}
        return JSON.ObjectFromURL(url, headers=headers)

  def refreshAccessToken(self):
    Log.Debug('reAuth')
    url = "https://accounts.spotify.com/api/token"
    authString = "{0}:{1}".format(CLIENT_ID,CLIENT_SECRET)
    # Log.Debug(authString)
    encodedAuthString = base64.b64encode(authString)
    # Log.Debug(encodedAuthString)
    headers = {"Authorization":"Basic "+encodedAuthString}
    values = {"grant_type":"refresh_token","refresh_token":self.refresh_token}
    response = JSON.ObjectFromURL(url, values=values, headers=headers)
    self.access_token = response['access_token']
    Dict['access_token'] = response['access_token']
    self.expires_in = response['expires_in']
    return response['access_token']

  ###########################################################################################################

  def LookupLibraryAlbums(self):
    url = "https://api.spotify.com/v1/me/albums?offset=0&limit=50"
    response = self.request(url)
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      items.extend(response['items'])
    return items

  def LookupLibraryTracks(self):
    url = "https://api.spotify.com/v1/me/tracks?offset=0&limit=50"
    response = self.request(url)
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      items.extend(response['items'])
    return items

  def LookupAlbum(self, id):
    url = "https://api.spotify.com/v1/albums/"+id
    return self.request(url)

  def LookupTrack(self, id):
     url =  "https://api.spotify.com/v1/tracks/{0}".format(id)
     return self.request(url)

  def LookupArtist(self, id):
    url = "https://api.spotify.com/v1/artists/"+id
    return self.request(url)

  def LookupMyProfile(self):
    url = "https://api.spotify.com/v1/me"
    return self.request(url);

  def LookupArtists(self, ids):
    idString = ",".join(ids)
    url = "https://api.spotify.com/v1/artists?ids="+idString
    return self.request(url)['artists']

  def LookupArtistAlbums(self, artistId):
    url = "https://api.spotify.com/v1/artists/{0}/albums".format(artistId)
    response = self.request(url)
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      items.extend(response['items'])
    return items

  def LookupLibraryPlaylists(self):
    url = "https://api.spotify.com/v1/me/playlists"
    response = self.request(url)
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      items.extend(response['items'])
    return items

    url = "https://api.spotify.com/v1/users/%s/playlists/%s/tracks"%(owner,id)
    response = self.request(url)
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      items.extend(response['items'])
    return items

  def LookupCategories(self):
    url = "https://api.spotify.com/v1/browse/categories"
    response = self.request(url)
    response = response['categories']
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      response = response['categories']
      items.extend(response['items'])
    return items

  def LookupCategoryPlaylists(self, id):
    url = "https://api.spotify.com/v1/browse/categories/%s/playlists"%(id)
    response = self.request(url)
    response = response['playlists']
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      response = response['playlists']
      items.extend(response['items'])
    return items

  def LookupFeaturedPlaylists(self):
    url = "https://api.spotify.com/v1/browse/featured-playlists"
    response = self.request(url)
    response = response['playlists']
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      response = response['playlists']
      items.extend(response['items'])
    return items

  def LookupNewReleases(self, limit=50):
    url = "https://api.spotify.com/v1/browse/new-releases?limit=%s"%(limit)
    response = self.request(url)
    response = response['albums']
    items = response['items']
    while response['next']:
      nextUrl = response['next']
      response = self.request(nextUrl)
      response = response['albums']
      items.extend(response['items'])
    return items
