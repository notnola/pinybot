
""" Manage (create/load) the tags from FLV iteration stored in tdata files """

# Tag handling
import os
import pickle
import gzip

# FLV parsing imports
from flashmedia import FLV, FLVError
from flashmedia.tag import ScriptData
from flashmedia import metadata

# A/V types
audio = 8
video = 9

# Video control types
key_frame = 0x12
inter_frame = 0x22
disposable_frame = 0x32
generated_frame = 0x42

tag_message = '<<<TAG-HANDLER>>>'


def iterate_frames(filename):
    """
    Loop over the content of an FLV file to generate tag/frame data
    Once looped, return a list containing all the appropriate packet(s) i.e. audio/video packet.
    :param filename: str the location of the FLV file to be loaded.
    """
    # NOTE: This is experimental and may be prone to errors; please use with discretion.
    # :param frame_delay: int/float delay (automatically calculated or set manually) between packets.
    # :param audio: Boolean True/False send audio packets (default False ~ OFF).
    # :param video: Boolean True/False send video packets (default True ~ ON).

    # if tag.type == rtmp_protocol.DataTypes.AUDIO_MESSAGE: # if the tag is equal to AMF data type 8 i.e. audio message
        # if audio:
            # self._audio_packet(tag.data.data, inter_frame, tag.timestamp) # NOTE: Since audio is not encoded properly, it cannot be sent as NellyMoser,
                                                                          #       instead inter-frame is the only distinguishable control type which works.

    # elif tag.type == rtmp_protocol.DataTypes.VIDEO_MESSAGE: # if the tag is equal to AMF data type 9 i.e. video message
        # if video:
            # self._video_packet(tag.data.data, control, tag.timestamp)

    # time.sleep(frame_delay) # Apply frame delay

    # List where all the frame data will be stored in
    saved_frames = []

    print(tag_message + ' Opening FLV file and beginning read.')

    # metadata_framerate = metadata.main(filename)
    # print(tag_message, 'FLV frame-rate:', metadata_framerate)

    # Open a FLV, pass any readable file-like object (read bytes)
    fd = open(filename, 'rb')

    # Find the tags in the FLV
    try:
        flv = FLV(fd)
    except FLVError as err:  # On an error print and exit
        print(tag_message + ' Invalid FLV')
        return None

    # Set essential local variables
    alternate_control = True  # Alternate between control types

    # Start with key-frame
    control = key_frame

    print(tag_message + ' Iterating over FLV content.')
    # Iterate over tags
    for tag in flv:

        # On any Null type, stop iteration of FLV tags/frames
        if tag is None:
            break

        # Skip metadata in the file
        if isinstance(tag.data, ScriptData) and tag.data.name == 'onMetaData':
            continue

        if tag.type == video:
            if control != key_frame:
                if alternate_control:
                    control = inter_frame  # Inter-frame - Sorenson H.263
                else:
                    control = disposable_frame  # Disposable-frame - Sorenson H.263

        elif tag.type == audio:
            control = inter_frame

        saved_frames.append([tag.type, tag.data.data, control, tag.timestamp]) # Record tag/frame information

        alternate_control = not alternate_control # Switch to the other control type
        control = None

    return saved_frames


def store_frame_data(tag_folder, filename, frames):
    """
    Store any tag/frame data given in a list.
    :param tag_folder: str the location of the tag/frame data folder.
    :param filename: str the whole file name with extension.
    :param frames: list the entirety of the tag/frame information from iteration
                        over FLV content.
    """

    # If tag data directory does not exist, then create a new one
    if not os.path.exists(filename):
        os.mkdir(tag_folder)

    # Generate a new tdata (tag_data) file
    FLV_name = filename.split('.flv')
    tag_data_file_name = tag_folder + FLV_name[0] + '.tdata'
    tag_data_file = gzip.open(tag_data_file_name, 'wb')

    print(tag_message + ' Opened ' + tag_data_file_name + ' for saving tag/frame data.')

    # Store all the tag/frame data, using compression.
    print(tag_message + ' Saving data with compression. Just a moment...')
    pickle.dump(frames, tag_data_file)

    print(tag_message + ' Finished compression and save. Closing file.')
    tag_data_file.close()

    if os.path.exists(tag_data_file_name):
        return True
    else:
        return False


def load_frame_data(tag_data_file):
    """
    Load any tag/frame data file created using the handler (.tdata extension).
    :param tag_data_file: str the full file location and filename (with extension).
    """

    if os.path.exists(tag_data_file):
        print(tag_message + 'Opening compressed file.')
        tag_data = gzip.open(tag_data_file, 'rb')
        print(tag_message + ' Loading tag/frame data file. Just a moment...')
        tag_data_content = pickle.load(tag_data)
        return tag_data_content
    else:
        print(tag_message + ' No file named ' + tag_data_file + ' was found.')
        return None
