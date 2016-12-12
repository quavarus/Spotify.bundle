from utils import *
load_libspotify()
from spotify import MainLoop, ConnectionState, ErrorType, Bitrate, link, ConnectionType,SampleType
from spotify import track as _track
from spotify.utils.loaders import load_track
from spotify.session import Session, SessionCallbacks
import threading

logoutEvent = threading.Event()
loginEvent = threading.Event()

class PlaybackService(SessionCallbacks):
  def __init__(self):
    Log.Debug("PlaybackService Initializing")
    self.prev_error = 0
    self.status = PlaybackStatus.Created
    self.stream = None
    self.trackLock = threading.Lock()
    self.session = None

  def start(self):
    Log.Debug('PlaybackService: start()')
    data_dir, cache_dir, settings_dir = check_dirs()
    self.mainloop = MainLoop()
    self.session = Session(
        self,
        app_key=appkey,
        user_agent="python ctypes bindings",
        settings_location=settings_dir,
        cache_location=cache_dir,
        initially_unload_playlists=False
    )
    self.session.preferred_bitrate(Bitrate.Rate320k)
    self.session.set_volume_normalization(True)
    self.session.set_volume_normalization(True)
    self.session.set_connection_type(ConnectionType.Wired)

    Thread.Create(self.StartWorkerThread)

    self.status = PlaybackStatus.Started

  def stop(self):
    Log.Debug('PlaybackService: stop()')
    if self.session:
      self.logout()
      self.mainloop.quit()
      self.session.process_events()
      self.session.release()    
      self.session = None
    self.status = PlaybackStatus.Stopped

  def login(self, username, password):
    Log.Debug("PlaybackService do_login(username=%s)", username)
    self.status = PlaybackStatus.Authenticating
    #If no previous errors and we have a remembered user
    if self.prev_error == 0 and try_decode(self.session.remembered_user()) == username:
        self.session.relogin()
        Log( "Cached session found" )
    else:
        #do login with stored credentials
        self.session.login(username, password, True)
    loginEvent.clear()
    loginEvent.wait()

  def logout(self):
    Log.Debug("PlaybackService: logout()")
    self.status = PlaybackStatus.LoggedOut
    self.endTrack()
    if self.session.user():
      Log("PlaybackService: logout() user_name=%s", self.session.user_name())
      self.session.logout()
      logoutEvent.clear()
      logoutEvent.wait()
    

  def StartWorkerThread(self):
    self.mainloop.loop(self.session)

  def startTrack(self, stream, trackId):
    with self.trackLock:
      try:
        Log("playback starting: %s"%(trackId))
        self.endTrack_Internal()
        self.stream = stream
        link_obj = link.create_from_string("spotify:track:%s" % trackId)
        if link_obj is not None:
          track_obj = link_obj.as_track()
          self.track = load_track(self.session, track_obj)
          self.status = PlaybackStatus.Streaming
          self.firstFrame = True
          self.session.player_load(track_obj)
          self.session.player_play(True)
          Log("playback started: %s"%(trackId))
      except Exception as e:
        Log("Playback Service: Error Starting Track %s"%(e))
        self.endTrack_Internal()

  def writeTrackData(self, data, num_samples, sample_type, sample_rate, num_channels): 
    with self.trackLock:
      try:
        total_samples = self.get_total_samples(sample_rate)
        sample_width = self.get_sample_width(sample_type)
        self.stream.write(total_samples, data, num_samples, sample_width, sample_rate, num_channels)
      except Exception as e:
        Log(e)
        self.endTrack_Internal()

  def endTrack_Internal(self):
    Log('endTrack_Internal')
    try:
      self.session.player_unload()
      if self.stream:
        Log('closing stream %s'%(self.stream))
        self.stream.finish()
      self.stream = None
      self.track = None
      self.status=PlaybackStatus.Ready
      self.session.flush_caches()
    except Exception as e:
      self.status=PlaybackStatus.Ready
      Log("Playback Service: Error Ending Track %s"%(e))

  def endTrack(self):
    with self.trackLock:
      self.endTrack_Internal()

  def get_total_samples(self, sample_rate):
    return sample_rate * self.track.duration() / 1000

  def get_sample_width(self, sample_type):
    if sample_type == SampleType.Int16NativeEndian:
        return 16
    
    else:
        return -1

  def GetStatus(self):
    return self.lookupConnectionState(self.session.connectionstate())

  def lookupConnectionState(self, id):
    if id==ConnectionState.LoggedOut:
      return "LoggedOut"
    elif id==ConnectionState.LoggedIn:
      return "LoggedIn"
    elif id==ConnectionState.Disconnected:
      return "Disconnected"
    elif id==ConnectionState.Undefined:
      return "Undefined"
    elif id==ConnectionState.Offline:
      return 'Offline'
    else:
      return None


#########################################################################
## Callback Functions

  def logged_in(self, session, error_num):
    self.prev_error = error_num
    if error_num == ErrorType.Ok:
      Log.Debug("PlaybackService Login Success")
      self.status = PlaybackStatus.Ready
    else:
      Log.Debug("PlaybackService Login Failed error=%s"%(error_num))
      self.status = PlaybackStatus.AuthenticationFailed
    loginEvent.set()

  def logged_out(self, session):
    Log('PlaybackService Logged Out')
    logoutEvent.set()
    self.status = PlaybackStatus.LoggedOut

  def connection_error(self, session, error):
    Log('connection error: {0:d}'.format(error))

  def message_to_user(self, session, data):
    Log('message to user: {0}'.format(data))

  def log_message(self, session, data):
    Log("Spotify Callbacks: %s" %data, True)
    pass

  def streaming_error(self, session, error):
    Log('streaming error: {0:d}'.format(error))

  def play_token_lost(self, session):
    Log ('play_token_lost')
    self.endTrack()

  def end_of_track(self, session):
    Log ('end_of_track')
    self.endTrack()

  def notify_main_thread(self, session):
    # Log('notify_main_thread')
    self.mainloop.notify()

  def music_delivery(self, session, data, num_samples, sample_type, sample_rate, num_channels):
    # try:
      # Log('music_delivery num_samples=%s, sample_type=%s, sample_rate=%s, num_channels=%s' % (num_samples,sample_type,sample_rate,num_channels))
      return self.writeTrackData(data, num_samples, sample_type, sample_rate, num_channels)
    # except Exception as e:
    #   Log(e)
    #   self.endTrack()

  def start_playback(self, session):
    Log ('start_playback')
    
  def stop_playback(self, session):
    Log ('stop_playback')
  
  # def get_audio_buffer_stats(self, session):
  #   Log ('get_audio_buffer_stats')
  
  def offline_status_updated(self, session):
    Log ('offline_status_updated')
  
  def offline_error(self, session, error):
    Log ('offline_error')
  
  def credentials_blob_updated(self, session, blob):
    Log ('credentials_blob_updated')
  
  def connectionstate_updated(self, session):
    Log("connectionstate_updated")
    stateStr = self.GetStatus()
    Log ('connectionstate_updated state=%s'%(stateStr))

class PlaybackStatus:
  Created               = "Created" #Playback Created
  Started               = "Started"
  Authenticating        = "Authenticating"
  AuthenticationFailed  = "Authentication Failed"
  Ready                 = "Ready"
  Error                 = "Error"
  Streaming             = "Streaming"
  LoggedOut             = "Logged Out"
  Stopped               = "Stopped"
