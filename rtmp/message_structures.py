# Made by: TechWhizZ199

""" Retains all the various RTMP message structures which can be used in general (providing parameters are given) """


def sendCommand(datatype, command, parameters):
    """
    Construct a remote procedure call (RPC) message provided the command and the parameters are given.
    :param datatype: int the RTMP datatype.
    :param command: str the RPC command name.
    :param parameters: list with all the parameters to pass on in the message.
    """
    msg = {'msg': datatype, 'command': [u'' + command, 0, None] + parameters}
    return msg


def createStream(datatype, transaction_id):
    """
    Construct a 'createStream' message to issue a new stream on which data can travel through.
    :param datatype: int the RTMP datatype.
    :param transaction_id: int the transaction id in which the message will be sent on.
    """
    msg = {'msg': datatype, 'command': [u'createStream', transaction_id, None]}
    return msg


def publish(datatype, stream_id, name, publishing_type):
    """
    Construct a 'publish' message to send publish information to start a broadcast.
    :param datatype: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on (received from createStream).
    :param name: str the name of the stream to publish on the server.
    :param publishing_type: str the type of publishing method i.e. 'live'/'record'/'append'.
    """
    msg = {'msg': datatype, 'stream_id': stream_id, 'command': [u'publish', 0, None, u'' + str(name), u'' + publishing_type]}
    return msg


def SET_CHUNK_SIZE(datatype, stream_id, new_size):
    """
    Construct a 'SET_CHUNK_SIZE' message to adjust the chunk size at which the RTMP library works with.
    :param datatype: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on.
    :param new_size: int the new size of future message chunks from the client (1<=size<=2147483647).
                         NOTE: All sizes set after 16777215 are equivalent.
    """
    msg = {'msg': datatype, 'stream_id': stream_id, 'chunk_size': new_size}
    return msg


def play(datatype, stream_id, name, start=-2, duration=-1, reset=False):
    """
    Construct a 'play' message to start receive audio/video data from publishers on the server.
    :param datatype: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on.
    :param name: str the name of the stream that is published/recorded on the server.
    :param start: N/A
    :param duration: N/A
    :param reset: N/A
    """
    # start, duration, reset
    msg = {'msg': datatype, 'stream_id': stream_id, 'command': [u'play', 0, None, u'' + str(name)]}
    return msg


def audio(datatype, stream_id, data, control, timestamp):
    """
    Construct an audio message to send audio data to the server.
    :param datatype: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on (same as the publish StreamID).
    :param data: bytes the raw audio data.
    :param control: bytes in hex the control type to send the data as.
    :param timestamp: int the timestamp of the packet.
    """
    msg = {'msg': datatype, 'stream_id': stream_id,'timestamp': timestamp, 'body': {'control': control, 'data': data}}
    return msg


def video(type, stream_id, data, control, timestamp):
    """
    Construct a video message to send video data to the server.
    :param type: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on (same as the publish StreamID).
    :param data: bytes the raw video data.
    :param control: bytes in hex the control type to send the data as.
    :param timestamp: int the timestamp of the packet.
    """
    msg = {'msg': type, 'stream_id': stream_id, 'timestamp': timestamp, 'body': {'control': control, 'data': data}}
    return msg


def closeStream(type, stream_id):
    """
    Construct a 'closeStream' message to close an open stream between the client and server, by the server.
    :param type: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on.
    """
    msg = {'msg': type, 'stream_id': stream_id, 'command': [u'closeStream', 0, None]}
    return msg


def deleteStream(type, stream_id):
    """
    Construct a 'deleteStream' message to delete a closed stream between the client and server, on the server.
    :param type: int the RTMP datatype.
    :param stream_id: int the stream which the message will be sent on.
    """
    msg = {'msg': type, 'stream_id': stream_id, 'command': [u'deleteStream', 0, None, stream_id]}
    return msg


def PING(type, event_type, ping_data=None):
    """
    Construct a 'PING' message to send either a 'PING_REQUEST' or 'PING_RESPONSE' to the server.
    :param type: int the RTMP datatype.
    :param event_type: int the type of message you want to send (PING_REQUEST = 6 or PING_RESPONSE = 7).
    :param ping_data: bytes the data you want to send to the server (DEFAULT: blank bytes.)
    """
    if ping_data is None:
        ping_data = b"\x00\x00\x00\x00"

    msg = {'msg': type, 'event_type': event_type, 'event_data': ping_data}
    return msg
