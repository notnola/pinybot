""" Commands that are available by default to send on NetStream. """

import logging

from qrtmp.formats import types

log = logging.getLogger(__name__)


class NetStreamMessages:

    def __init__(self, rtmp_writer):
        """
        Initialise the NetStream messages class with the RtmpWriter object.

        :param rtmp_writer: RtmpWriter object to write the preset NetStream messages with.
        """
        self._rtmp_writer = rtmp_writer

    def send_receive_audio(self, stream_id, receive):
        """
        Send a 'receiveAudio' request on the RTMP stream channel.

        :param stream_id: int the id on which we would like to send the receive request.
        :param receive: bool True/False if we want to receive audio or not.
        """
        receive_audio = self._rtmp_writer.new_packet()

        receive_audio.set_chunk_stream_id(types.RTMP_STREAM_CHUNK_STREAM)
        receive_audio.set_type(types.DT_COMMAND)
        receive_audio.set_stream_id(stream_id)
        receive_audio.body = {
            'command_name': 'receiveAudio',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            'options': [receive]
        }

        log.debug('Sending receiveAudio to the server:', receive_audio)

        # Setup the packet for sending.
        receive_audio.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(receive_audio)

    def send_receive_video(self, stream_id, receive):
        """
        Send a 'receiveVideo' request on the RTMP stream channel.

        :param stream_id: int the id on which we would like to send the receive request.
        :param receive: bool True/False if we want to receive video or not.
        """
        receive_video = self._rtmp_writer.new_packet()

        receive_video.set_chunk_stream_id(types.RTMP_STREAM_CHUNK_STREAM)
        receive_video.set_type(types.DT_COMMAND)
        receive_video.set_stream_id(stream_id)
        receive_video.body = {
            'command_name': 'receiveVideo',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            'options': [receive]
        }

        log.debug('Sending receiveVideo to the server:', receive_video)

        # Setup the packet for sending.
        receive_video.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(receive_video)

    def send_play(self, stream_id, stream_name, start=-2, duration=-1, reset=False):
        """
        Send a 'play' request on the RTMP stream channel.

        NOTE: When passing the stream name into the function, make sure the appropriate file-type
              precedes the stream name (unless it is an FLV file) and the file extension. E.g. the
              playback of 'sample.m4v' on the server is issued with a stream name of 'mp4:sample.m4v'
              in the 'play' request.

              Like wise:
                    'BigBuckBunny_115k.mov' -> 'mp4:BigBuckBunny_115k.mov'
                    MP3 or ID3 tags do not need the file extension: 'sample.mp3' -> 'mp3:sample'
                    FLV files can be played back without file-type or file extension:
                        'stream_123.flv' -> 'stream_123'

        :param stream_id: int
        :param stream_name: str the stream name of the file you want to request playback for (READ ABOVE)
        :param start: int (default -2)
        :param duration: int (default -1)
        :param reset: bool (default False)
        """
        play_stream = self._rtmp_writer.new_packet()

        play_stream.set_chunk_stream_id(types.RTMP_STREAM_CHUNK_STREAM)
        play_stream.set_type(types.DT_COMMAND)
        play_stream.set_stream_id(stream_id)
        play_stream.body = {
            'command_name': 'play',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            # TODO: Support start, duration and reset parameters.
            'options': [stream_name, start]
        }

        # Add the specific duration to play the stream for (if it is not set to play until it finishes).
        if duration is not -1:
            play_stream.body['options'].append(duration)
        # Add the reset option if it is not set to False (and is instead True).
        if reset is not False:
            play_stream.body['options'].append(reset)

        log.debug('Sending play to the server:', play_stream)

        # Set up the packet for sending.
        play_stream.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(play_stream)

    # def send_play2(self):
    #     """
    #     Send a 'play2' request on the RTMP stream channel.
    #
    #     Properties include: len(number) - duration of playback in seconds.
    #                         offset(number) - absolute stream time at which server switches between streams of
    #                                          different bit-rates for Flash Media Server dynamic streaming
    #                         oldStreamName(string) - name of the old stream or the stream to transition from
    #                         start(number) - start time in seconds
    #                         streamName(string) - name of the new stream to transition to or to play
    #                         transition(string) - mode in which the stream name is played or transitioned to.
    #
    #     NOTE: These are all AMF3 encoded values in AS3 object.
    #     """

    def send_seek(self, stream_id, time_point):
        """
        Send a 'seek' request on the RTMP stream channel.

        :param stream_id: int the stream id in which we want to send the seek request.
        :param time_point: float the point in the playlist (in milliseconds) to seek to.
        """
        seek_stream = self._rtmp_writer.new_packet()

        seek_stream.set_chunk_stream_id(types.RTMP_STREAM_CHUNK_STREAM)
        seek_stream.set_type(types.DT_COMMAND)
        seek_stream.set_stream_id(stream_id)
        seek_stream.body = {
            'command_name': 'seek',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            'options': [stream_id, time_point]
        }

        log.debug('Sending seek to the server:', seek_stream)

        # Set up the packet for sending.
        seek_stream.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(seek_stream)

    def send_pause(self, stream_id, pause_flag, time_point=0.0):
        """
        Send a 'pause' request on the RTMP stream channel.

        :param stream_id: int
        :param pause_flag: bool (True/False) whether the stream should be paused or resumed.
        :param time_point: float the point at which the stream should be paused or resumed.
        """
        pause_stream = self._rtmp_writer.new_packet()

        pause_stream.set_chunk_stream_id(types.RTMP_STREAM_CHUNK_STREAM)
        pause_stream.set_type(types.DT_COMMAND)
        pause_stream.set_stream_id(stream_id)
        pause_stream.body = {
            'command_name': 'pause',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            'options': [pause_flag, time_point]
        }

        log.debug('Sending pause to the server:', pause_stream)

        # Set up the packet for sending.
        pause_stream.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(pause_stream)

    def send_publish(self, stream_id, publish_name, publish_type):
        """
        Send a 'publish' request on the RTMP stream channel.

        :param stream_id: int
        :param publish_name:
        :param publish_type:
        """
        publish_stream = self._rtmp_writer.new_packet()

        publish_stream.set_chunk_stream_id(types.RTMP_STREAM_CHUNK_STREAM)
        publish_stream.set_type(types.DT_COMMAND)
        publish_stream.set_stream_id(stream_id)
        publish_stream.body = {
            'command_name': 'publish',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            'options': [str(publish_name), publish_type]
        }

        log.debug('Sending publish request:', publish_stream)

        # Set up the packet for sending.
        publish_stream.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(publish_stream)

    def send_close_stream(self, command_object=None):
        """
        Send a 'closeStream' request on the stream given by the stream id, this will be the same as
        the stream id in which a publish RTMP message was sent on.

        :param command_object: dict (default None) any command information to be sent.
        """
        close_stream = self._rtmp_writer.new_packet()

        close_stream.set_type(types.DT_COMMAND)
        close_stream.body = {
            'command_name': 'closeStream',
            'transaction_id': self._rtmp_writer.transaction_id,
            'command_object': None,
            'options': []
        }

        log.debug('Sending closeStream request:', close_stream)

        # Set up the packet for sending.
        close_stream.setup()

        # Send the packet.
        self._rtmp_writer.send_packet(close_stream)

