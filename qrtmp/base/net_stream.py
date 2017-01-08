"""
The NetStream module handles any NetStream related commands and data to an RTMP server.
"""

from qrtmp.io.net_stream import messages


class NetStream:
    """
    This is an addition to the NetConnection class which allows you to interact with the
    """

    def __init__(self, rtmp_writer):
        """
        Initialise the NetStream variables, the RtmpWriter is given, so messages and NetStream related data
        can be written into the stream.
        """
        # Initialise the RtmpWriter.
        self._rtmp_writer = rtmp_writer
        # Initialise the NetStream messages class.
        self.messages = messages.NetStreamMessages(rtmp_writer)

