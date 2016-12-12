from tornado import httpserver
from tornado import web
from tornado import ioloop

from threading import Event
import StringIO,struct
import functools

class StreamServer():

  def __init__(self, playbackService):  
    self.playbackService = playbackService
    self.application = web.Application([
          (r"/stream/(.+)", StreamHandler,dict(streamer=self.playbackService)),
      ])  
    self.application.status = StreamServierStatus.Created
  

  def start(self, port):
    Log('StreamServer: start(port=%s)'%(port))
    self.port = port
    try:
      self.server = httpserver.HTTPServer(self.application)
      self.server.bind(self.port)
      self.server.start(1)
      # ioloop.IOLoop.instance().start()
      Log("thread exit start")
      self.application.status = StreamServierStatus.Started
    except Exception as e:
      self.application.status = StreamServierStatus.Error
      Log("StreamServer: start(..) type=%s args=%s"%(type(e),e.args))

  def stop(self):
    Log.Debug("StreamServer: stop()")
    self.application.status = StreamServierStatus.Stopped
    if hasattr(self,"server"):
      self.server.stop()

  def status(self):
    return self.application.status


class StreamHandler(web.RequestHandler):

  def initialize(self, streamer):
    Log("StreamHandler: initialize")
    self.streamer = streamer

  @web.asynchronous
  def get(self, trackId):
    try:
      self.application.status = StreamServierStatus.Streaming
      trackId = trackId.rsplit('.', 1)[0]
      Log('actual trackId=%s'%(trackId))
      writer = OutputWriter(self)
      self.streamer.startTrack(writer,trackId)
      Log('streamer request complete')
    except Exception as e:
      self.application.status = StreamServierStatus.Error
      Log(e)
      self.finish()
    
class OutputWriter():
  def __init__(self, requestHandler):
    self.request = requestHandler
    self.firstFrame = True

  def write(self, total_num_samples, data, data_num_samples, sample_width, sample_rate, num_channels):

    if self.firstFrame==True:
      Log('writeTrackData: first frame')
      self.firstFrame = False
      header, filesize = self.generate_wave_header(total_num_samples, num_channels, sample_rate, sample_width)
      self.request.set_status(200)
      # self.set_header("Accept-Ranges","bytes")
      self.request.set_header("Content-Type","audio/x-wave")
      self.request.set_header("Content-Length",filesize)
      self.request.write(header)
      self.request.flush()

    event = Event()
    callback = functools.partial(self.writeRequest, data, event)
    io = ioloop.IOLoop.instance()
    io.add_callback(callback)
    event.wait()

    return data_num_samples


  def finish(self):
    self.request.application.status = StreamServierStatus.Ready
    self.request.finish()
    # self.request = None
    del self.request

  def writeRequest(self,data,event):
   self.request.write(data)
   self.request.flush()
   event.set()

  def generate_wave_header(self, numsamples, channels, samplerate, bitspersample):
    file = StringIO.StringIO()
    
    #Generate format chunk
    format_chunk_spec = "<4sLHHLLHH"
    format_chunk = struct.pack(
        format_chunk_spec,
        "fmt ", #Chunk id
        16, #Size of this chunk (excluding chunk id and this field)
        1, #Audio format, 1 for PCM
        channels, #Number of channels
        samplerate, #Samplerate, 44100, 48000, etc.
        samplerate * channels * (bitspersample / 8), #Byterate
        channels * (bitspersample / 8), #Blockalign
        bitspersample, #16 bits for two byte samples, etc.
    )
    
    #Generate data chunk
    data_chunk_spec = "<4sL"
    datasize = numsamples * channels * (bitspersample / 8)
    data_chunk = struct.pack(
        data_chunk_spec,
        "data", #Chunk id
        int(datasize), #Chunk size (excluding chunk id and this field)
    )
    
    sum_items = 4  #"WAVE" string following size field
    sum_items += struct.calcsize(format_chunk_spec)  #"fmt " + chunk size field + chunk size
    sum_items += struct.calcsize(data_chunk_spec) + datasize #Size of data chunk spec + data size
        
    #Generate main header
    all_cunks_size = int(sum_items)
    main_header_spec = "<4sL4s"
    main_header = struct.pack(
        main_header_spec,
        "RIFF",
        all_cunks_size,
        "WAVE"
    )
    
    #Write all the contents in
    file.write(main_header)
    file.write(format_chunk)
    file.write(data_chunk)
    
    return file.getvalue(), all_cunks_size + 8

class StreamServierStatus:
  Created               = "Created" #Playback Created
  Started               = "Started"
  Streaming             = "Streaming"
  Ready                 = "Ready"
  Error                 = "Error"
  Stopped               = "Stopped"
  
