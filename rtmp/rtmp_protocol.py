"""
Provides classes for creating RTMP (Real Time Message Protocol) servers and
clients.
"""


import pyamf.amf0
import pyamf.util.pure
import rtmp_protocol_base
import socket
import socks
import random  # added for the random bytes. nortxort
# import logging


class FileDataTypeMixIn(pyamf.util.pure.DataTypeMixIn):
    """
    Provides a wrapper for a file object that enables reading and writing of raw
    data types for the file.
    """

    def __init__(self, fileobject):
        self.fileobject = fileobject
        pyamf.util.pure.DataTypeMixIn.__init__(self)

    def read(self, length):
        return self.fileobject.read(length)

    def write(self, data):
        self.fileobject.write(data)

    def flush(self):
        self.fileobject.flush()

    def at_eof(self):
        return False


class DataTypes:
    """ Represents an enumeration of the RTMP message datatypes. """
    NONE = -1
    UNKNOWN = 0
    SET_CHUNK_SIZE = 1
    ABORT = 2
    ACK = 3
    USER_CONTROL = 4
    WINDOW_ACK_SIZE = 5
    SET_PEER_BANDWIDTH = 6
    AUDIO = 8
    VIDEO = 9
    DATA = 18
    SHARED_OBJECT = 19
    COMMAND = 20
    AGGREGATE = 22


class SOEventTypes:
    """ Represents an enumeration of the shared object event types. """
    USE = 1
    RELEASE = 2
    CHANGE = 4
    MESSAGE = 6
    CLEAR = 8
    DELETE = 9
    USE_SUCCESS = 11


class UserControlTypes:
    """ Represents an enumeration of the user control event types. """
    STREAM_BEGIN = 0
    STREAM_EOF = 1
    STREAM_DRY = 2
    SET_BUFFER_LENGTH = 3
    STREAM_IS_RECORDED = 4
    PING_REQUEST = 6
    PING_RESPONSE = 7


class RtmpReader:
    """ This class reads RTMP messages from a stream. """

    chunk_size = 128

    def __init__(self, stream):
        """
        Initialize the RTMP reader and set it to read from the specified stream.
        """
        self.stream = stream

    def __iter__(self):
        return self

    def next(self):
        """ Read one RTMP message from the stream and return it. """
        if self.stream.at_eof():
            raise StopIteration
        # Read the message into body_stream. The message may span a number of
        # chunks (each one with its own header).
        message_body = []
        msg_body_len = 0
        header = rtmp_protocol_base.header_decode(self.stream)

        while True:
            read_bytes = min(header.bodyLength - msg_body_len, self.chunk_size)
            message_body.append(self.stream.read(read_bytes))
            msg_body_len += read_bytes
            if msg_body_len >= header.bodyLength:
                break
            next_header = rtmp_protocol_base.header_decode(self.stream)
            # WORKAROUND: even though the RTMP specification states that the
            # extended timestamp field DOES NOT follow type 3 chunks, it seems
            # that Flash player 10.1.85.3 and Flash Media Server 3.0.2.217 send
            # and expect this field here.
            if header.timestamp >= 0x00ffffff:
                self.stream.read_ulong()

        assert header.bodyLength == msg_body_len, (header, msg_body_len)
        body_stream = pyamf.util.BufferedByteStream(''.join(message_body))

        # Decode the message based on the datatype present in the header
        ret = {'msg': header.datatype}

        if ret['msg'] == DataTypes.NONE:
            return self.next()

        elif ret['msg'] == DataTypes.UNKNOWN:
            # ret['stream_id'] = header.streamId # contextual information use
            # try:
                # ret['unknown_type_char'] = body_stream.read_uchar()
            # except:
                # pass
            # try:
                # ret['unknown_type_long'] = body_stream.read_ulong()
            # except:
                # pass
            # try:
                # ret['unknown_type_short'] = body_stream.read_ushort()
            # except:
                # pass
            # ret['unknown_data'] = body_stream.read()
            pass

        elif ret['msg'] == DataTypes.USER_CONTROL:
            ret['stream_id'] = header.streamId # contextual information use
            # ret['event_data_long'] = body_stream.read_ulong()
            # ret['event_data_char'] = body_stream.read_uchar()
            ret['event_type'] = body_stream.read_ushort()
            ret['event_data'] = body_stream.read()

        elif ret['msg'] == DataTypes.ACK:
            # ret['stream_id'] = header.streamId # contextual information use
            # try:
                # ret['ack_type_char'] = body_stream.read_uchar()
            # except:
                # pass
            # try:
                # ret['ack_type_long'] = body_stream.read_ulong()
            # except:
                # pass
            # try:
                # ret['ack_type_short'] = body_stream.read_ushort()
            # except:
                # pass
            # ret['ack_data'] = body_stream.read()
            pass

        elif ret['msg'] == DataTypes.WINDOW_ACK_SIZE:
            ret['window_ack_size'] = body_stream.read_ulong()

        elif ret['msg'] == DataTypes.SET_PEER_BANDWIDTH:
            ret['window_ack_size'] = body_stream.read_ulong()
            ret['limit_type'] = body_stream.read_uchar()

        elif ret['msg'] == DataTypes.SHARED_OBJECT:
            decoder = pyamf.amf0.Decoder(body_stream)
            obj_name = decoder.readString()
            curr_version = body_stream.read_ulong()
            flags = body_stream.read(8)

            # A shared object message may contain a number of events.
            events = []
            while not body_stream.at_eof():
                #event = self.read_shared_object_event(body_stream, decoder)
                event = RtmpReader.read_shared_object_event(body_stream, decoder)
                events.append(event)

            ret['obj_name'] = obj_name
            ret['curr_version'] = curr_version
            ret['flags'] = flags
            ret['events'] = events

        elif ret['msg'] == DataTypes.COMMAND:
            ret['stream_id'] = header.streamId # contexutal information
            decoder = pyamf.amf0.Decoder(body_stream)
            commands = []
            while not body_stream.at_eof():
                commands.append(decoder.readElement())
            ret['command'] = commands

        elif ret['msg'] == DataTypes.SET_CHUNK_SIZE:
            ret['chunk_size'] = body_stream.read_ulong()

        elif ret['msg'] == DataTypes.DATA:
            ret['stream_id'] = header.stream_id
            ret['metadata'] = message_body

        elif ret['msg'] == DataTypes.AUDIO:
            # ret['stream_id'] = header.streamId
            # ret['control'] = body_stream.read_uchar()
            # ret['data'] = body_stream.read()
            # ret['timestamp'] = header.timestamp

            # View individual header information
            # print(':RTMP HEADER:', '<type:>', header.datatype, '<channel id>:', header.channelId, '<stream id>:', header.streamId,
                # '<bodylength>:', header.bodyLength, '<timestamp>:', header.timestamp)

            # View individual body information
            # print(':RTMP BODY:', '<control>', ret['control'], '<audio data>', '...') # ret['data'] is the raw audio data
            pass

        elif ret['msg'] == DataTypes.VIDEO:
            # ret['stream_id'] = header.streamId
            # ret['control'] = body_stream.read_uchar()
            # ret['data'] = body_stream.read()
            # ret['timestamp'] = header.timestamp


            # View individual header information
            # print(':RTMP HEADER:', '<type:>', header.datatype, '<channel id>:', header.channelId, '<stream id>:', header.streamId,
            #      '<bodylength>:', header.bodyLength, '<timestamp>:', header.timestamp)
            # print("Control", ret['control'])

            # View individual body information
            # print(':RTMP BODY:', '<control>', ret['control'], '<video data>', '...') # ret['data'] is the raw video data
            pass

        else:
            assert False, header

        # logging.debug('recv %r', ret)
        return ret

    @staticmethod
    def read_shared_object_event(body_stream, decoder):
        """
        Helper method that reads one shared object event found inside a shared
        object RTMP message.
        """
        so_body_type = body_stream.read_uchar()
        so_body_size = body_stream.read_ulong()

        event = {'type': so_body_type}
        if event['type'] == SOEventTypes.USE:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        elif event['type'] == SOEventTypes.RELEASE:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        elif event['type'] == SOEventTypes.CHANGE:
            start_pos = body_stream.tell()
            changes = {}
            while body_stream.tell() < start_pos + so_body_size:
                attrib_name = decoder.readString()
                attrib_value = decoder.readElement()
                assert attrib_name not in changes, (attrib_name, changes.keys())
                changes[attrib_name] = attrib_value
            assert body_stream.tell() == start_pos + so_body_size,\
                (body_stream.tell(), start_pos, so_body_size)
            event['data'] = changes
        elif event['type'] == SOEventTypes.MESSAGE:
            start_pos = body_stream.tell()
            msg_params = []
            while body_stream.tell() < start_pos + so_body_size:
                msg_params.append(decoder.readElement())
            assert body_stream.tell() == start_pos + so_body_size,\
                (body_stream.tell(), start_pos, so_body_size)
            event['data'] = msg_params
        elif event['type'] == SOEventTypes.CLEAR:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        elif event['type'] == SOEventTypes.DELETE:
            event['data'] = decoder.readString()
        elif event['type'] == SOEventTypes.USE_SUCCESS:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        else:
            assert False, event['type']

        return event


class RtmpWriter:
    """ This class writes RTMP messages into a stream. """

    chunk_size = 128

    def __init__(self, stream):
        """
        Initialize the RTMP writer and set it to write into the specified
        stream.
        """
        self.stream = stream

    def flush(self):
        """ Flush the underlying stream. """
        self.stream.flush()

    def write(self, message):
        """ Encode and write the specified message into the stream. """
        # logging.debug('send %r', message)
        datatype = message['msg']
        body_stream = pyamf.util.BufferedByteStream()
        encoder = pyamf.amf0.Encoder(body_stream)

        if datatype == DataTypes.USER_CONTROL:
            body_stream.write_ushort(message['event_type'])
            body_stream.write(message['event_data'])

        elif datatype == DataTypes.WINDOW_ACK_SIZE:
            body_stream.write_ulong(message['window_ack_size'])

        elif datatype == DataTypes.SET_CHUNK_SIZE:
            body_stream.write_long(message['chunk_size'])

        elif datatype == DataTypes.SET_PEER_BANDWIDTH:
            body_stream.write_ulong(message['window_ack_size'])
            body_stream.write_uchar(message['limit_type'])

        elif datatype == DataTypes.COMMAND:
            for command in message['command']:
                encoder.writeElement(command)

        elif datatype == DataTypes.SHARED_OBJECT:
            encoder.serialiseString(message['obj_name'])
            body_stream.write_ulong(message['curr_version'])
            body_stream.write(message['flags'])

            for event in message['events']:
                RtmpWriter.write_shared_object_event(event, body_stream)

        elif datatype == DataTypes.DATA:
             pass

        elif datatype == DataTypes.AUDIO:
            # Write an audio message into the stream
            body_stream.write_uchar(message['body']['control']) # Write control
            body_stream.write(message['body']['data']) # Write data

        elif datatype == DataTypes.VIDEO:
            # Write an video message into the stream
            body_stream.write_uchar(message['body']['control']) # Write control
            body_stream.write(message['body']['data']) # Write data

        else:
            assert False, message

        self.send_msg(datatype, body_stream.getvalue(), message)

    @staticmethod
    def write_shared_object_event(event, body_stream):
        inner_stream = pyamf.util.BufferedByteStream()
        encoder = pyamf.amf0.Encoder(inner_stream)

        event_type = event['type']
        if event_type == SOEventTypes.USE:
            assert event['data'] == '', event['data']
        elif event_type == SOEventTypes.CHANGE:
            for attrib_name in event['data']:
                attrib_value = event['data'][attrib_name]
                encoder.serialiseString(attrib_name)
                encoder.writeElement(attrib_value)
        elif event['type'] == SOEventTypes.CLEAR:
            assert event['data'] == '', event['data']
        elif event['type'] == SOEventTypes.USE_SUCCESS:
            assert event['data'] == '', event['data']
        else:
            assert False, event

        body_stream.write_uchar(event_type)
        body_stream.write_ulong(len(inner_stream))
        body_stream.write(inner_stream.getvalue())

    def send_msg(self, datatype, body, message=None):
        """
        Helper method that sends the specified message into the stream. Takes
        care to prepend the necessary headers and split the message into
        appropriately sized chunks.
        """
        # Values that just work. :-)
        if 1 <= datatype <= 7:
            channel_id = 2
            stream_id = 0
        else:
            channel_id = 3
            stream_id = 0
        timestamp = 0

        try:
            stream_id = message['stream_id']

            if 'closeStream' in body:
                channel_id = 8
            elif 'deleteStream' in body:
                channel_id = 3
            elif 'publish' in body:
                channel_id = 8
            elif 'play' in body:
                channel_id = 8
            elif datatype == DataTypes.SET_CHUNK_SIZE:
                channel_id = 2
            elif datatype == DataTypes.AUDIO or datatype == DataTypes.VIDEO:
                channel_id = random.randint(10, 50)
                timestamp = message['timestamp']
        except Exception:
            pass

        header = rtmp_protocol_base.Header(
            channelId=channel_id,
            timestamp=timestamp,
            streamId=stream_id,
            bodyLength=len(body),
            datatype=datatype)
        rtmp_protocol_base.header_encode(self.stream, header)

        for i in xrange(0, len(body), self.chunk_size):
            chunk = body[i:i+self.chunk_size]
            self.stream.write(chunk)
            if i+self.chunk_size < len(body):
                rtmp_protocol_base.header_encode(self.stream, header, header)


class FlashSharedObject:
    """
    This class represents a Flash Remote Shared Object. Its data are located
    inside the self.data dictionary.
    """

    def __init__(self, name):
        """
        Initialize a new Flash Remote SO with a given name and empty data.
        """
        self.name = name
        self.data = {}
        self.use_success = False

    def use(self, writer):
        """
        Initialize usage of the SO by contacting the Flash Media Server. Any
        remote changes to the SO should be now propagated to the client.
        """
        self.use_success = False

        msg = {
            'msg': DataTypes.SHARED_OBJECT,
            'curr_version': 0,
            'flags': '\x00\x00\x00\x00\x00\x00\x00\x00',
            'events': [
                {
                    'data': '',
                    'type': SOEventTypes.USE
                }
            ],
            'obj_name': self.name
        }
        writer.write(msg)
        writer.flush()

    def handle_message(self, message):
        """
        Handle an incoming RTMP message. Check if it is of any relevance for the
        specific SO and process it, otherwise ignore it.
        """
        if message['msg'] == DataTypes.SHARED_OBJECT and message['obj_name'] == self.name:
            events = message['events']

            if not self.use_success:
                assert events[0]['type'] == SOEventTypes.USE_SUCCESS, events[0]
                assert events[1]['type'] == SOEventTypes.CLEAR, events[1]
                events = events[2:]
                self.use_success = True

            self.handle_events(events)
            return True
        else:
            return False

    def handle_events(self, events):
        """ Handle SO events that target the specific SO. """
        for event in events:
            event_type = event['type']
            if event_type == SOEventTypes.CHANGE:
                for key in event['data']:
                    self.data[key] = event['data'][key]
                    self.on_change(key)
            elif event_type == SOEventTypes.DELETE:
                key = event['data']
                assert key in self.data, (key, self.data.keys())
                del self.data[key]
                self.on_delete(key)
            elif event_type == SOEventTypes.MESSAGE:
                self.on_message(event['data'])
            else:
                assert False, event

    def on_change(self, key):
        """ Handle change events for the specific shared object. """
        print(key)
        # pass

    def on_delete(self, key):
        pass

    def on_message(self, data):
        pass


class RtmpClient:
    """ Represents an RTMP client. """

    def __init__(self, ip, port, tc_url, page_url, swf_url, app, swf_version,
                 room_type, prefix, room, version, cookie, account='', proxy=None,):
        """ Initialize a new RTMP client. """
        self.ip = ip
        self.port = port
        self.tc_url = tc_url
        self.page_url = page_url
        self.swf_url = swf_url
        self.app = app
        self.swf_version = swf_version
        self.shared_objects = []
        self.room_type = room_type
        self.prefix = prefix
        self.room_name = room
        self.version = version
        self.cookie = cookie
        self.account = account
        self.proxy = proxy

    @staticmethod
    def create_random_bytes(length, readable=False):
        """ Creates random bytes for the handshake. """
        ran_bytes = ''
        i, j = 0, 0xff
        if readable:
            i, j = 0x41, 0x7a
        for x in xrange(0, length):
            ran_bytes += chr(random.randint(i, j))
        return ran_bytes

    def handshake(self):
        """ Perform the handshake sequence with the server. """

        self.stream.write_uchar(3)
        c1 = rtmp_protocol_base.Packet()
        c1.first = 0
        c1.second = 0
        c1.payload = self.create_random_bytes(1528)
        c1.encode(self.stream)
        self.stream.flush()

        self.stream.read_uchar()
        s1 = rtmp_protocol_base.Packet()
        s1.decode(self.stream)

        c2 = rtmp_protocol_base.Packet()
        c2.first = s1.first
        c2.second = s1.second
        c2.payload = s1.payload
        c2.encode(self.stream)
        self.stream.flush()

        s2 = rtmp_protocol_base.Packet()
        s2.decode(self.stream)

    def connect_rtmp(self, connect_params):
        """ Initiate a NetConnection with a Flash Media Server. """
        msg = {
            'msg': DataTypes.COMMAND,
            'command':
            [
                u'connect',
                1,
                {
                    'app': u'' + self.app,
                    'flashVer': u'' + self.swf_version,
                    'swfUrl': u'' + self.swf_url,
                    'tcUrl': u'' + self.tc_url,
                    'fpad': True,
                    'capabilities': 239,
                    'audioCodecs': 0x004,  # 3575,
                    'videoCodecs': 0x0004,  # 252,
                    'videoFunction': 0,  # SUPPORT_VID_CLIENT_SEEK
                    'pageUrl': self.page_url,
                    'objectEncoding': 0
                },
                {
                    'cookie': u'' + self.cookie,     # cauth cookie
                    'type': u'' + self.room_type,    # 'show' if its a registered room else 'default'
                    'account': u'' + self.account,   # tinychat login account
                    'room': u'' + self.room_name,    # name of the room
                    'prefix': u'' + self.prefix,     # 'tinychat' or 'greenroom'.
                    'version': u'' + self.version,   # desktop version
                }
            ]
        }

        msg['command'].extend(connect_params)
        self.writer.write(msg)
        self.writer.flush()

    def call(self, proc_name, parameters={}, trans_id=0):
        """ Runs remote procedure calls (RPC) at the receiving end. """
        msg = {
            'msg': DataTypes.COMMAND,
            'command':
            [
                proc_name,
                trans_id,
                parameters
            ]
        }

        self.writer.write(msg)
        self.writer.flush()

    def connect(self, connect_params):
        """ Connect to the server with the given connect parameters. """
        if self.proxy:
            parts = self.proxy.split(':')
            ip = parts[0]
            port = int(parts[1])

            ps = socks.socksocket()
            ps.set_proxy(socks.HTTP, addr=ip, port=port)
            self.socket = ps
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((self.ip, self.port))
        self.file = self.socket.makefile()
        self.stream = FileDataTypeMixIn(self.file)

        # Turn on TCP keepalive.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        self.handshake()
        self.reader = RtmpReader(self.stream)
        self.writer = RtmpWriter(self.stream)
        self.connect_rtmp(connect_params)

    def shutdown(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def shared_object_use(self, so):
        """ Use a shared object and add it to the managed list of SOs. """
        if so in self.shared_objects:
            return
        so.use(self.reader, self.writer)
        self.shared_objects.append(so)

    def handle_messages(self):
        """ Start the message handling loop. """
        while True:
            msg = self.reader.next()

            handled = self.handle_simple_message(msg)

            if handled:
                continue

            for so in self.shared_objects:
                if so.handle_message(msg):
                    handled = True
                    break
            if not handled:
                assert False, msg

    def handle_simple_message(self, msg):
        """ Handle simple messages, e.g. ping requests. """
        if msg['msg'] == DataTypes.USER_CONTROL and msg['event_type'] == UserControlTypes.PING_REQUEST:
            resp = {
                'msg': DataTypes.USER_CONTROL,
                'event_type': UserControlTypes.PING_RESPONSE,
                'event_data': msg['event_data'],
            }
            self.writer.write(resp)
            self.writer.flush()
            return True
        return False
