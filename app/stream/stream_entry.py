from bson.objectid import ObjectId
from mongoengine import StringField, IntField, EmbeddedDocumentField, EmbeddedDocument, DateTimeField, BooleanField, \
    FloatField, ObjectIdField
from datetime import datetime

import app.constants as constants

from .common_entry import Urls, Rational, Size, Logo, Url

ID_FIELD = "id"
TYPE_FIELD = "type"
FEEDBACK_DIR_FIELD = "feedback_directory"
LOG_LEVEL_FIELD = "log_level"
INPUT_FIELD = "input"
OUTPUT_FIELD = "output"
AUDIO_SELECT_FIELD = "audio_select"
HAVE_VIDEO_FIELD = "have_video"
HAVE_AUDIO_FIELD = "have_audio"
LOOP_FIELD = "loop"
AUTO_EXIT_TIME_FIELD = "auto_exit_time"
RESTART_ATTEMPTS_FIELD = "restart_attempts"

# encode
DEINTERLACE_FIELD = "deinterlace"
FRAME_RATE_FIELD = "frame_rate"
VOLUME_FIELD = "volume"
VIDEO_CODEC_FIELD = "video_codec"
AUDIO_CODEC_FIELD = "audio_codec"
AUDIO_CHANNELS_COUNT_FIELD = "audio_channels"
SIZE_FIELD = "size"
VIDEO_BIT_RATE_FIELD = "video_bitrate"
AUDIO_BIT_RATE_FIELD = "audio_bitrate"
LOGO_FIELD = "logo"
ASPCET_RATIO_FIELD = "aspect_ratio"
# relay
VIDEO_PARSER_FIELD = "video_parser"
AUDIO_PARSER_FIELD = "audio_parser"
# timeshift recorder
TIMESHIFT_CHUNK_DURATION = "timeshift_chunk_duration"
TIMESHIFT_CHUNK_LIFE_TIME = "timeshift_chunk_life_time"
TIMESHIFT_DIR = "timeshift_dir"
# timeshift player
TIMESHIFT_DELAY = "timeshift_delay"


class StreamFields:
    NAME = 'name'  # UI field
    ID = 'id'
    TYPE = 'type'
    INPUT_STREAMS = 'input_streams'
    OUTPUT_STREAMS = 'output_streams'
    LOOP_START_TIME = 'loop_start_time'
    RSS = 'rss'
    CPU = 'cpu'
    STATUS = 'status'
    RESTARTS = 'restarts'
    START_TIME = 'start_time'
    TIMESTAMP = 'timestamp'


DEFAULT_STREAM_NAME = 'Stream'
MIN_STREAM_NAME_LENGTH = 3
MAX_STREAM_NAME_LENGTH = 64


class Stream(EmbeddedDocument):
    meta = {'allow_inheritance': True, 'auto_create_index': True}

    def __init__(self, *args, **kwargs):
        super(Stream, self).__init__(*args, **kwargs)

    id = ObjectIdField(required=True, default=ObjectId,
                       unique=True, primary_key=True)
    name = StringField(default=DEFAULT_STREAM_NAME, max_length=MAX_STREAM_NAME_LENGTH,
                       min_length=MIN_STREAM_NAME_LENGTH, required=True)
    created_date = DateTimeField(default=datetime.now)  # for inner use
    log_level = IntField(default=constants.StreamLogLevel.LOG_LEVEL_INFO, required=True)

    input = EmbeddedDocumentField(Urls, default=Urls())
    output = EmbeddedDocumentField(Urls, default=Urls())
    have_video = BooleanField(default=constants.DEFAULT_HAVE_VIDEO, required=True)
    have_audio = BooleanField(default=constants.DEFAULT_HAVE_AUDIO, required=True)
    audio_select = IntField(default=constants.INVALID_AUDIO_SELECT, required=True)
    loop = BooleanField(default=constants.DEFAULT_LOOP, required=True)
    restart_attempts = IntField(default=constants.DEFAULT_RESTART_ATTEMPTS, required=True)
    auto_exit_time = IntField(default=constants.DEFAULT_AUTO_EXIT_TIME, required=True)

    # runtime
    _status = constants.StreamStatus.NEW
    _cpu = 0.0
    _timestamp = 0
    _rss = 0
    _loop_start_time = 0
    _restarts = 0
    _start_time = 0
    _input_streams = str()
    _output_streams = str()
    _feedback_dir = str()

    def set_feedback_dir(self, feedback_dir):
        self._feedback_dir = feedback_dir

    def reset(self):
        self._status = constants.StreamStatus.NEW
        self._cpu = 0.0
        self._timestamp = 0
        self._rss = 0
        self._loop_start_time = 0
        self._restarts = 0
        self._start_time = 0
        self._input_streams = str()
        self._output_streams = str()

    def update_runtime_fields(self, params: dict):
        assert self.get_id() == params[StreamFields.ID]
        assert self.get_type() == params[StreamFields.TYPE]
        self._status = constants.StreamStatus(params[StreamFields.STATUS])
        self._cpu = params[StreamFields.CPU]
        self._timestamp = params[StreamFields.TIMESTAMP]
        self._rss = params[StreamFields.RSS]
        self._loop_start_time = params[StreamFields.LOOP_START_TIME]
        self._restarts = params[StreamFields.RESTARTS]
        self._start_time = params[StreamFields.START_TIME]
        self._input_streams = params[StreamFields.INPUT_STREAMS]
        self._output_streams = params[StreamFields.OUTPUT_STREAMS]

    def to_front(self) -> dict:
        return {StreamFields.NAME: self.name, StreamFields.ID: self.get_id(), StreamFields.TYPE: self.get_type(),
                StreamFields.STATUS: self._status, StreamFields.CPU: self._cpu, StreamFields.TIMESTAMP: self._timestamp,
                StreamFields.RSS: self._rss, StreamFields.LOOP_START_TIME: self._loop_start_time,
                StreamFields.RESTARTS: self._restarts, StreamFields.START_TIME: self._start_time,
                StreamFields.INPUT_STREAMS: self._input_streams, StreamFields.OUTPUT_STREAMS: self._output_streams}

    def config(self) -> dict:
        conf = {
            ID_FIELD: self.get_id(),  # required
            TYPE_FIELD: self.get_type(),  # required
            FEEDBACK_DIR_FIELD: self.generate_feedback_dir(),  # required
            LOG_LEVEL_FIELD: self.get_log_level(),
            AUTO_EXIT_TIME_FIELD: self.get_auto_exit_time(),
            LOOP_FIELD: self.get_loop(),
            HAVE_VIDEO_FIELD: self.get_have_video(),  # required
            HAVE_AUDIO_FIELD: self.get_have_audio(),  # required
            RESTART_ATTEMPTS_FIELD: self.get_restart_attempts(),
            INPUT_FIELD: self.input.to_mongo(),  # required empty in timeshift_player
            OUTPUT_FIELD: self.output.to_mongo()  # required empty in timeshift_record
        }

        audio_select = self.get_audio_select()
        if audio_select != constants.INVALID_AUDIO_SELECT:
            conf[AUDIO_SELECT_FIELD] = audio_select
        return conf

    def generate_feedback_dir(self):
        return '{0}/{1}/{2}'.format(self._feedback_dir, self.get_type(), self.get_id())

    def get_log_level(self):
        return self.log_level

    def get_audio_select(self):
        return self.audio_select

    def get_have_video(self):
        return self.have_video

    def get_have_audio(self):
        return self.have_audio

    def get_id(self):
        return str(self.id)

    def get_type(self):
        raise NotImplementedError('subclasses must override get_type()!')

    def get_loop(self):
        return self.loop

    def get_restart_attempts(self):
        return self.restart_attempts

    def get_auto_exit_time(self):
        return self.auto_exit_time


class RelayStream(Stream):
    def __init__(self, *args, **kwargs):
        super(RelayStream, self).__init__(*args, **kwargs)
        # super(RelayStream, self).type = constants.StreamType.RELAY

    video_parser = StringField(default=constants.DEFAULT_VIDEO_PARSER, required=True)
    audio_parser = StringField(default=constants.DEFAULT_AUDIO_PARSER, required=True)

    def get_type(self):
        return constants.StreamType.RELAY

    def config(self) -> dict:
        conf = super(RelayStream, self).config()
        conf[VIDEO_PARSER_FIELD] = self.get_video_parser()
        conf[AUDIO_PARSER_FIELD] = self.get_audio_parser()
        return conf

    def get_video_parser(self):
        return self.video_parser

    def get_audio_parser(self):
        return self.audio_parser


class EncodeStream(Stream):
    def __init__(self, *args, **kwargs):
        super(EncodeStream, self).__init__(*args, **kwargs)

    deinterlace = BooleanField(default=constants.DEFAULT_DEINTERLACE, required=True)
    frame_rate = IntField(default=constants.INVALID_FRAME_RATE, required=True)
    volume = FloatField(default=constants.DEFAULT_VOLUME, required=True)
    video_codec = StringField(default=constants.DEFAULT_VIDEO_CODEC, required=True)
    audio_codec = StringField(default=constants.DEFAULT_AUDIO_CODEC, required=True)
    audio_channels_count = IntField(default=constants.INVALID_AUDIO_CHANNELS_COUNT, required=True)
    size = EmbeddedDocumentField(Size, default=Size())
    video_bit_rate = IntField(default=constants.INVALID_VIDEO_BIT_RATE, required=True)
    audio_bit_rate = IntField(default=constants.INVALID_AUDIO_BIT_RATE, required=True)
    logo = EmbeddedDocumentField(Logo, default=Logo())
    aspect_ratio = EmbeddedDocumentField(Rational, default=Rational())

    def get_type(self):
        return constants.StreamType.ENCODE

    def config(self) -> dict:
        conf = super(EncodeStream, self).config()
        conf[DEINTERLACE_FIELD] = self.get_deinterlace()
        frame_rate = self.get_frame_rate()
        if frame_rate != constants.INVALID_FRAME_RATE:
            conf[FRAME_RATE_FIELD] = frame_rate
        conf[VOLUME_FIELD] = self.get_volume()
        conf[VIDEO_CODEC_FIELD] = self.get_video_codec()
        conf[AUDIO_CODEC_FIELD] = self.get_audio_codec()
        audio_channels = self.get_audio_channels_count()
        if audio_channels != constants.INVALID_AUDIO_CHANNELS_COUNT:
            conf[AUDIO_CHANNELS_COUNT_FIELD] = audio_channels

        if self.size.is_valid():
            conf[SIZE_FIELD] = str(self.size)

        vid_rate = self.get_video_bit_rate()
        if vid_rate != constants.INVALID_VIDEO_BIT_RATE:
            conf[VIDEO_BIT_RATE_FIELD] = vid_rate
        audio_rate = self.get_audio_bit_rate()
        if audio_rate != constants.INVALID_AUDIO_BIT_RATE:
            conf[AUDIO_BIT_RATE_FIELD] = self.get_audio_bit_rate()
        if self.logo.is_valid():
            conf[LOGO_FIELD] = self.logo.to_dict()
        if self.aspect_ratio.is_valid():
            conf[ASPCET_RATIO_FIELD] = str(self.aspect_ratio)
        return conf

    def get_deinterlace(self):
        return self.deinterlace

    def get_frame_rate(self):
        return self.frame_rate

    def get_volume(self):
        return self.volume

    def get_video_codec(self):
        return self.video_codec

    def get_audio_codec(self):
        return self.audio_codec

    def get_audio_channels_count(self):
        return self.audio_channels_count

    def get_video_bit_rate(self):
        return self.video_bit_rate

    def get_audio_bit_rate(self):
        return self.audio_bit_rate


class TimeshiftRecorderStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(TimeshiftRecorderStream, self).__init__(*args, **kwargs)

    timeshift_chunk_duration = IntField(default=constants.DEFAULT_TIMESHIFT_CHUNK_DURATION, required=True)
    timeshift_chunk_life_time = IntField(default=constants.DEFAULT_TIMESHIFT_CHUNK_LIFE_TIME, required=True)

    # runtime
    _timeshift_dir = str()

    def get_type(self):
        return constants.StreamType.TIMESHIFT_RECORDER

    def set_timeshift_dir(self, timeshift_dir):
        self._timeshift_dir = timeshift_dir

    def config(self) -> dict:
        conf = super(TimeshiftRecorderStream, self).config()
        conf[TIMESHIFT_CHUNK_DURATION] = self.get_timeshift_chunk_duration()
        conf[TIMESHIFT_DIR] = self.generate_timeshift_dir()
        conf[TIMESHIFT_CHUNK_LIFE_TIME] = self.timeshift_chunk_life_time
        return conf

    def get_timeshift_chunk_duration(self):
        return self.timeshift_chunk_duration

    def generate_timeshift_dir(self):
        return '{0}/{1}'.format(self._timeshift_dir, self.get_id())


class CatchupStream(TimeshiftRecorderStream):
    def __init__(self, *args, **kwargs):
        super(CatchupStream, self).__init__(*args, **kwargs)
        self.timeshift_chunk_duration = constants.DEFAULT_CATCHUP_CHUNK_DURATION
        self.auto_exit_time = constants.DEFAULT_CATCHUP_EXIT_TIME

    def get_type(self):
        return constants.StreamType.CATCHUP


class TimeshiftPlayerStream(RelayStream):
    timeshift_dir = StringField(required=True)  # FIXME default
    timeshift_delay = IntField(default=constants.DEFAULT_TIMESHIFT_DELAY, required=True)

    def __init__(self, *args, **kwargs):
        super(TimeshiftPlayerStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.TIMESHIFT_PLAYER

    def config(self) -> dict:
        conf = super(TimeshiftPlayerStream, self).config()
        conf[TIMESHIFT_DIR] = self.timeshift_dir
        conf[TIMESHIFT_DELAY] = self.timeshift_delay
        return conf


class TestLifeStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(TestLifeStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.TEST_LIFE

    def config(self) -> dict:
        conf = super(TestLifeStream, self).config()
        return conf


def make_relay_stream(feedback_dir: str) -> RelayStream:
    stream = RelayStream()
    stream._feedback_dir = feedback_dir
    stream.input = Urls(urls=[Url(id=Url.generate_id())])
    stream.output = Urls(urls=[Url(id=Url.generate_id())])
    return stream


def make_encode_stream(feedback_dir: str) -> EncodeStream:
    stream = EncodeStream()
    stream._feedback_dir = feedback_dir
    stream.input = Urls(urls=[Url(id=Url.generate_id())])
    stream.output = Urls(urls=[Url(id=Url.generate_id())])
    return stream


def make_timeshift_recorder_stream(feedback_dir: str, timeshift_dir: str) -> TimeshiftRecorderStream:
    stream = TimeshiftRecorderStream()
    stream._feedback_dir = feedback_dir
    stream._timeshift_dir = timeshift_dir
    stream.input = Urls(urls=[Url(id=Url.generate_id())])
    return stream


def make_catchup_stream(feedback_dir: str, timeshift_dir: str) -> CatchupStream:
    stream = CatchupStream()
    stream._feedback_dir = feedback_dir
    stream._timeshift_dir = timeshift_dir
    stream.input = Urls(urls=[Url(id=Url.generate_id())])
    return stream


def make_timeshift_player_stream(feedback_dir: str) -> TimeshiftPlayerStream:
    stream = TimeshiftPlayerStream()
    stream._feedback_dir = feedback_dir
    stream.input = Urls(urls=[Url(id=Url.generate_id())])
    stream.output = Urls(urls=[Url(id=Url.generate_id())])
    return stream


def make_test_life_stream(feedback_dir: str) -> TestLifeStream:
    stream = TestLifeStream()
    stream._feedback_dir = feedback_dir
    stream.input = Urls(urls=[Url(id=Url.generate_id())])
    stream.output = Urls(urls=[Url(id=Url.generate_id(), uri=constants.DEFAULT_TEST_URL)])
    return stream
