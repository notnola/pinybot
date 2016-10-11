""" A broadcast/camera managing module to handle streaming FLV data. """

import os
import struct

# from flashmedia import FLV as FLVParser
# from flashmedia import FLVError
# from flashmedia.tag import ScriptData

# A/V types
AUDIO = 0x08
VIDEO = 0x09

# Video control types
KEY_FRAME = 0x12
INTER_FRAME = 0x22
DISPOSABLE_FRAME = 0x32
GENERATED_FRAME = 0x42

manager_state = '<CameraManager>'


class FLV(object):
    """ """

    def __init__(self, path):
        """ """
        self.flv_content = open(path, 'rb')
        self.flv_location = path
        self.tags = None

        self.tsr0 = None
        self.tsa = 0
        self.tsv = 0

    def set_tags(self, flv_tags):
        """

        :param flv_tags:
        """
        self.tags = flv_tags


# from flv_handler import FLVParse
# TODO: Inherit a core background class for parsing - FLVHandle?
class CameraManager:  # FLVParse
    """ The main broadcast/camera management instance. """

    # TODO: Init with also the configurations to broadcast, audio/video on/off & length, time..
    def __init__(self):
        """ """
        # self.current_flv_file = None
        self._flv_tags = []

    @staticmethod
    def load_flv(flv_location):
        """
        Load an FLV file to parse it's tag data from.
        :param flv_location:
        """
        # self.current_flv_file = FLVFile(flv_location)
        loaded_flv = FLV(flv_location)
        return loaded_flv

    def get_tags(self, tag_flv):
        """
        Retrieve the frames
        :return:
        """
        read_flv = self.iterate_frames(tag_flv)
        read_flv.flv_content.close()
        return read_flv

    @staticmethod
    def iterate_frames(read_flv):
        """
        Loop over the content of an FLV file to generate tag/frame data.
        Once looped, return a list containing all the appropriate packet(s) i.e. audio/video packet.
        :param read_flv: FLV object with the data (opened to read bytes) to be loaded.
        """
        # print('%s Beginning read of FLV.' % manager_state)

        magic, version, flags, offset = struct.unpack('!3sBBI', read_flv.flv_content.read(9))

        if magic != 'FLV':
            raise ValueError('This is not an FLV file.')

        if version != 1:
            raise ValueError('Unsupported FLV file version.')

        if offset > 9:
            read_flv.flv_content.seek(offset - 9, os.SEEK_CUR)

        read_flv.flv_content.read(4)

        saved_tags = []

        while True:
            data_bytes = read_flv.flv_content.read(11)
            if len(data_bytes) is not 0:
                data_type, len0, len1, ts0, ts1, ts2, sid0, sid1 = struct.unpack('>BBHBHBBH', data_bytes)
                read_length = (len0 << 16) | len1
                ts = (ts0 << 16) | (ts1 & 0x0ffff) | (ts2 << 24)
                # TODO: An extra character at the start of the body causes the body to become unreadable,
                #       reading past the first character fixes this.
                body = read_flv.flv_content.read(read_length)[1:]

                previous_tag_size, = struct.unpack('>I', read_flv.flv_content.read(4))
                if previous_tag_size != (read_length + 11):
                    # print('Invalid previous tag size found:', previous_tag_size)
                    pass

                # control = 0x22
                if data_type == AUDIO:
                    read_flv.tsa, ts = ts, ts - max(read_flv.tsa, read_flv.tsv)
                    control = 0x22
                elif data_type == VIDEO:
                    read_flv.tsv, ts = ts, ts - max(read_flv.tsa, read_flv.tsv)
                    control = INTER_FRAME
                else:
                    continue

                if ts < 0:
                    ts = 0
                # elif ts > 0:
                #     time.sleep(ts/1000.0)

                # print([body])

                saved_tags.append([data_type, body, control, ts])
            else:
                break

        read_flv.tags = saved_tags
        # print('Length of tags saved:', len(saved_tags))
        # print("DONE!")
        return read_flv

        # Parse the tags from the FLV file.
        # try:
        #     flv_content = FLV(flv_file)
        # except FLVError as ex:
            # On an error print the exception and return null.
            # print('%s Invalid FLV: %s' % (manager_state, ex))
            # return None

        # List where all the tag data will be stored within.
        # saved_tags = []

        # print('%s Iterating over FLV content.' % manager_state)
        # Iterate over tags.
        # for tag in flv_content:
            # On any Null type, stop iteration of FLV tags/frames.
            # if tag is not None:
                # Skip metadata in the file.
                # if isinstance(tag.data, ScriptData) and tag.data.name == 'onMetaData':
                #     continue
                # else:
                #     Load audio tag.
                    # if tag.type == AUDIO:
                    #     control = 0x22

                        # Record tag/frame information.
                        # saved_tags.append([tag.type, tag.data.data, control, tag.timestamp])

                    # Load video tag.
                    # elif tag.type == VIDEO:
                    #     control = KEY_FRAME

                        # Record tag/frame information.
                        # saved_tags.append([tag.type, tag.data.data, control, tag.timestamp])

        # print('%s Saved frames (%s) into tag list.' % (manager_state, len(saved_tags)))
        # Returned the iterated tags.

        # self.read_flv_tags = saved_tags


# manage = CameraManager()
# flv_file = manage.load_flv('logo.flv')
# read_flv = manage.get_tags(flv_file)

# logo_img = open('logo.flv1', 'wb')

# for tag in read_flv.tags:
#     logo_img.write(tag[1])

# logo_img.close()

# print(len(read_flv.tags[25][1]))

# fd = open('am.flv', 'rb')

# # Open a FLV, pass any readable file-like object
# try:
#     flv = FLVParser(fd)
# except FLVError as err:
#     print("Invalid FLV")
#     sys.exit()

# save_bytes = []
# # Iterate over tags
# # for tag in flv:
# count = 0
# for tag in flv:
#     if count == 27:
#         break
#     else:
#         if tag is not None:
#             # tag.data contains the parsed data, it's either a AudioData, VideoData or ScriptData object
#             print("Tag with timestamp %d contains %s" % (tag.timestamp, repr(tag.data)))

#             # Modify the metadata
#             if isinstance(tag.data, ScriptData) and tag.data.name == "onMetaData":
#                 tag.data.value["description"] = "This file has been modified through python!"
#                 continue

#             # print(len(tag.data.data))

#             print(len(tag.data.data))
#             count += 1

#             # Serialize the tag back into bytes
#             # data = tag.serialize()
