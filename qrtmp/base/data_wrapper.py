import pyamf
import pyamf.util.pure

# TODO: Place pyamf somewhere else so we can access the ASObjects variable (in a more central location).


class SocketDataTypeMixInFile(pyamf.util.pure.DataTypeMixIn):
    """

    """

    def __init__(self, socket_object):
        """

        :param socket_object:
        """
        self.fileobject = socket_object
        pyamf.util.pure.DataTypeMixIn.__init__(self)

    def read(self, length):
        """

        :param length:
        :return:
        """
        return self.fileobject.read(length)

    def write(self, data):
        """

        :param data:
        """
        self.fileobject.write(data)

    def flush(self):
        """

        :return:
        """
        self.fileobject.flush()

    @staticmethod
    def at_eof():
        """

        :return False:
        """
        return False


# TODO: If the socket is a file object and FileDataTypeMixIn inherited read/write, we can just alter
#       that to read data.
# TODO: We will have to enclose all BufferedByteStream actions with a recv/send to make sure
#       the data is present to do these actions.
