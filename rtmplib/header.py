"""
Original source code taken from rtmpy project (http://rtmpy.org/)

it seems as the above url is broken, so provided are the links to
rtmpy on github (https://github.com/hydralabs/rtmpy)
https://github.com/hydralabs/rtmpy/blob/master/rtmpy/protocol/handshake.py
https://github.com/hydralabs/rtmpy/blob/master/rtmpy/protocol/rtmp/header.py

This is a edited version of rtmp-python based on the original by prekageo
https://github.com/prekageo/rtmp-python
"""
import logging

log = logging.getLogger(__name__)

# TODO: Headers, rtmp reader and writer should be different for each connection we make individual classes for each).
# Otherwise connections header information may clash?
# MERGED_CHANNEL_HEADERS = {}


def decode(stream):
    """
    Reads a header from the incoming stream.

    A header can be of varying lengths and the properties that get updated
    depend on the length.

    @param stream: The byte stream to read the header from.
    @type stream: C{pyamf.util.BufferedByteStream}
    @return: The read header from the stream.
    @rtype: L{Header}
    """
    # read the size and channel_id
    channel_id = stream.read_uchar()
    bits = channel_id >> 6
    channel_id &= 0x3f

    if channel_id == 0:
        channel_id = stream.read_uchar() + 64

    if channel_id == 1:
        channel_id = stream.read_uchar() + 64 + (stream.read_uchar() << 8)

    header = Header(channel_id)

    if bits == 3:
        return header

    header.timestamp = stream.read_24bit_uint()

    if bits < 2:
        header.body_length = stream.read_24bit_uint()
        header.data_type = stream.read_uchar()

    if bits < 1:
        # streamId is little endian
        stream.endian = '<'
        header.stream_id = stream.read_ulong()
        stream.endian = '!'

        header.full = True

    if header.timestamp == 0xffffff:
        header.timestamp = stream.read_ulong()
    # WORKAROUND: even though the RTMP specification states that the
    # extended timestamp field DOES NOT follow type 3 chunks, it seems
    # that Flash player 10.1.85.3 and Flash Media Server 3.0.2.217 send
    # and expect this field here.

    # if header.timestamp >= 0x00ffffff:
    #     self.stream.read_ulong()

    log.info('header recv: %s' % header)

    return header


def encode(stream, header, previous=None):
    """
    Encodes a RTMP header to C{stream}.

    We expect the stream to already be in network endian mode.

    The channel id can be encoded in up to 3 bytes. The first byte is special as
    it contains the size of the rest of the header as described in
    L{getHeaderSize}.

    0 >= channel_id > 64: channel_id
    64 >= channel_id > 320: 0, channel_id - 64
    320 >= channel_id > 0xffff + 64: 1, channel_id - 64 (written as 2 byte int)

    @param stream: The stream to write the encoded header.
    @type stream: L{util.BufferedByteStream}
    @param header: The L{Header} to encode.
    @param previous: The previous L(Header) is there is one.
    """
    log.debug('header send: %s' % header)
    if previous is None:
        size = 0
    else:
        size = min_bytes_required(header, previous)

    channel_id = header.channel_id

    # if str(channel_id) in MERGED_CHANNEL_HEADERS:
    #     # print('channel information available in merged channel header for channel id: %s' % channel_id)
    #     latest_full_header = MERGED_CHANNEL_HEADERS[str(channel_id)]
    #     size = _get_chunk_type(latest_full_header, header)
    #     _merge_headers(latest_full_header, header)
    # else:
    #     MERGED_CHANNEL_HEADERS[str(channel_id)] = header
    #     # print('channel id header information not in merged headers for channel id: %s' % channel_id)
    #     size = 0

    if channel_id < 64:
        stream.write_uchar(size | channel_id)
    elif channel_id < 320:
        stream.write_uchar(size)
        stream.write_uchar(channel_id - 64)
    else:
        channel_id -= 64

        stream.write_uchar(size + 1)
        stream.write_uchar(channel_id & 0xff)
        stream.write_uchar(channel_id >> 0x08)

    if size == 0xc0:
        return

    if size <= 0x80:
        if header.timestamp >= 0xffffff:
            stream.write_24bit_uint(0xffffff)
        else:
            stream.write_24bit_uint(header.timestamp)

    if size <= 0x40:
        stream.write_24bit_uint(header.body_length)
        stream.write_uchar(header.data_type)

    if size == 0:
        stream.endian = '<'
        stream.write_ulong(header.stream_id)
        stream.endian = '!'

    if size <= 0x80:
        if header.timestamp >= 0xffffff:
            stream.write_ulong(header.timestamp)


class Header(object):
    """
    An RTMP Header. Holds contextual information for an RTMP Channel.
    """

    __slots__ = ('stream_id', 'data_type', 'timestamp',
                 'body_length', 'channel_id', 'full')

    def __init__(self, channel_id, timestamp=-1, data_type=-1,
                 body_length=-1, stream_id=-1, full=False):
        self.channel_id = channel_id
        self.timestamp = timestamp
        self.data_type = data_type
        self.body_length = body_length
        self.stream_id = stream_id
        self.full = full

    def __repr__(self):
        attrs = []

        for k in self.__slots__:
            v = getattr(self, k, None)

            if v == -1:
                v = None

            attrs.append('%s=%r' % (k, v))

        return '<%s.%s %s at 0x%x>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            ' '.join(attrs),
            id(self))


def min_bytes_required(old, new):
    """
    Returns the number of bytes needed to de/encode the header based on the
    differences between the two.

    Both headers must be from the same channel.

    @type old: L{Header}
    @type new: L{Header}
    """
    if old is new:
        return 0xc0

    if old.channel_id != new.channel_id:
        raise Exception('HeaderError: channel_id mismatch on diff old=%r, new=%r' % (old, new))

    if old.stream_id != new.stream_id:
        return 0  # full header

    if old.data_type == new.data_type and old.body_length == new.body_length:
        if old.timestamp == new.timestamp:
            return 0xc0

        return 0x80

    return 0x40

# def _get_chunk_type(latest_full_header, header_to_encode):
#     """
#     Returns the number of bytes needed to encode the header based on the differences between the two.
#
#     NOTE: Both headers must be from the same chunk stream in order for this to work.
#           By comparing the size of the header we need to encode into the stream, we can reduce overhead in formats
#           by only writing the necessary parts of the header.
#
#     :param latest_full_header: the last full header that we received in this chunk stream.
#     @type latest_full_header: L{Header}
#     :param header_to_encode: the header we need to encode into the RTMP stream.
#     @type header_to_encode: L{Header}
#     """
#     # If the header is not on the same chunk stream then we cannot get a mask.
#     if latest_full_header.channel_id == header_to_encode.channel_id:
#         # If the header we just received and the header previous to it is identical,
#         # then it is an RTMP message in chunks.
#         # Return that size corresponds to a type 3 header.
#         if latest_full_header is header_to_encode:
#             return 0xc0  # 192
#         else:
#             # If the stream id are not the same, then this indicates the use of a Type 0 message.
#             # A message stream is being used on the RTMP stream.
#             if latest_full_header.stream_id != header_to_encode.stream_id:
#                 # Return that size corresponds to a type 0 header.
#                 return 0x00
#
#             # If the previous header and the new headers message type id match and they have the same body size,
#             # then send the chunk as Type 2, this saves space on the stream.
#             # header.body_size, header.timestamp
#             if latest_full_header.data_type == header_to_encode.data_type \
#                     and latest_full_header.body_length == header_to_encode.body_length:
#                 # If the old header's timestamp and the new_header's timestamp match then send via Type 3,
#                 # we do not need to send a type 2 since the timestamp delta is the same.
#                 if latest_full_header.timestamp == header_to_encode.timestamp:
#                     # Return that size corresponds to a type 3 header.
#                     return 0xc0  # 192
#
#                 # If the body size is the same we can send via Type 2.
#                 # Return that size corresponds to a type 2 header.
#                 return 0x80  # 128
#
#             # Return that size corresponds to a type 1 header.
#             return 0x40  # 64
#     else:
#         # raise HeaderError('chunk_stream_id mismatch on diff old=%r, new=%r' %
#         #                   (latest_full_header, header_to_encode))
#         return None


# def _merge_headers(original_header, next_header):
#     """
#     Returns the merged header from the original header by comparing the missing parts in the next header
#     and copying over the parts that are necessary.
#
#     NOTE: The original header should be an up-to-date version of the current status of headers in the chunk stream.
#
#     :param original_header: L(Header)
#     :param next_header: L(Header)
#     :return next_header: L(Header)
#     """
#     # print('Merging headers.')
#     # Since the packets are on the same channels, we can copy over missing information.
#     if original_header.channel_id == next_header.channel_id:
#         # print('On the same chunk stream.')
#         if original_header != next_header:
#
#             if next_header.timestamp == -1:
#                 next_header.timestamp = original_header.timestamp
#                 # print('assumed timestamp')
#
#             if next_header.body_length == -1:
#                 next_header.body_length = original_header.body_length
#                 # print('assumed body_length')
#
#             if next_header.data_type == -1:
#                 next_header.data_type = original_header.data_type
#                 # print('assumed data_type')
#
#             if next_header.stream_id == -1:
#                 next_header.stream_id = original_header.stream_id
#                 # print('assumed stream_id')
#
#             # print('Merging complete.')
#             # We can now store the latest header information for that chunk stream to the merged headers dictionary.
#             # self._merged_chunk_streams_header[str(original_header.chunk_stream_id)] = next_header
#             MERGED_CHANNEL_HEADERS[str(original_header.channel_id)] = next_header
#         # else:
#             # print('Headers are the same, no need to merge headers.')
#     # else:
#         # print('The chunk streams were different, we can not merge.')
