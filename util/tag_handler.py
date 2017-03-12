
""" Manage (create/load) the tags from FLV iteration stored in tdata files """

# Imports for storing iterated tags.
# import os
# import pickle
# import gzip

# Imports for FLV parsing.
from flashmedia import FLV, FLVError
from flashmedia.tag import ScriptData
# from flashmedia import metadata

# A/V types
audio = 8
video = 9

# Video control types
key_frame = 0x12
inter_frame = 0x22
disposable_frame = 0x32
generated_frame = 0x42

tag_message = '<<<TAG-HANDLER>>>'


def iterate_frames(file_object):
    """
    Loop over the content of an FLV file to generate tag/frame data.
    Once looped, return a list containing all the appropriate packet(s) i.e. audio/video packet.
    :param file_object: object FLV file with the data (opened to read bytes) to be loaded.
    """
    # List where all the frame data will be stored in
    saved_frames = []

    # Parse metadata in the FLV.
    # metadata_frame_rate = metadata.main(filename)
    # print(tag_message, 'FLV frame-rate:', metadata_frame_rate)

    print('%s Beginning read of FLV.' % tag_message)

    # Find the tags in the FLV.
    try:
        flv = FLV(file_object)
    except FLVError as err:  # On an error print and exit.
        print('%s Invalid FLV: %s' % (tag_message, err))
        return False

    # Set essential local variables.
    # - alternate between control types:
    # alternate_control = True

    # - start with a key-frame.
    # control = key_frame

    print('%s Iterating over FLV content.' % tag_message)
    # Iterate over tags.
    for tag in flv:
        # On any Null type, stop iteration of FLV tags/frames.
        if tag is not None:
            # Skip metadata in the file.
            if isinstance(tag.data, ScriptData) and tag.data.name == 'onMetaData':
                continue

            # Load video tag.
            if tag.type == video:
                control = key_frame

                # if control != key_frame:
                #     if alternate_control:
                #         Inter-frame - Sorenson H.263.
                #         control = disposable_frame
                #     else:
                #         Disposable-frame - Sorenson H.263.
                #         control = inter_frame

                # Record tag/frame information.
                saved_frames.append([tag.type, tag.data.data, control, tag.timestamp])

            # Load audio tag.
            elif tag.type == audio:
                control = 0x22
                # control = inter_frame

                # Record tag/frame information.
                saved_frames.append([tag.type, tag.data.data, control, tag.timestamp])

            # Save either the loaded video/audio tag:
            # - switch to the other control type:
            # alternate_control = not alternate_control
            # control = None
        else:
            break

    print('%s Saved frames (%s) into list.' % (tag_message, len(saved_frames)))
    # Returned the iterated tags.
    return saved_frames


# def store_frame_data(tag_folder, filename, frames):
#     """
#     Store any tag/frame data given in a list.
#     :param tag_folder: str the location of the tag/frame data folder.
#     :param filename: str the whole file name with extension.
#     :param frames: list the entirety of the tag/frame information from iteration
#                         over FLV content.
#     """
#
#     # If tag data directory does not exist, then create a new one
#     if not os.path.exists(filename):
#         os.mkdir(tag_folder)
#
#     # Generate a new "tdata" (tag_data) file
#     FLV_name = filename.split('.flv')
#     tag_data_file_name = tag_folder + FLV_name[0] + '.tdata'
#     tag_data_file = gzip.open(tag_data_file_name, 'wb')
#
#     print('%s Opened %s for saving tag/frame data.' % (tag_message, tag_data_file_name))
#
#     # Store all the tag/frame data, using compression.
#     print('%s Saving data with compression. Just a moment ...' % tag_message)
#     pickle.dump(frames, tag_data_file)
#
#     print('%s Finished compression and save. Closing file.' % tag_message)
#     tag_data_file.close()
#
#     if os.path.exists(tag_data_file_name):
#         return True
#     else:
#         return False


# def load_frame_data(tag_data_file):
#     """
#     Load any tag/frame data file created using the handler (.tdata extension).
#     :param tag_data_file: str the full file location and filename (with extension).
#     """
#
#     if os.path.exists(tag_data_file):
#         print('%s Opening compressed file.' % tag_message)
#         tag_data = gzip.open(tag_data_file, 'rb')
#         print(tag_message + ' Loading tag/frame data file. Just a moment...')
#         tag_data_content = pickle.load(tag_data)
#         return tag_data_content
#     else:
#         print('%s No file (%s) was found.' % tag_data_file)
#         return None