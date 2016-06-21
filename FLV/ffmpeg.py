
""" Simple FFMPEG Audio/Video conversion wrapper for FLV output """

# Default FLV codec set to flv1 (Sorenson H.263)

import subprocess
import os
import sys

# ------------------------------------------------------------------------------------------------
# Run on Linux terminal:
#       sudo apt-get update
#       apt-get install ffmpeg
# Windows users can run with having the ffmpeg.exe file in the FLV directory.
# ------------------------------------------------------------------------------------------------

FFMPEG_prefix = '<<<FFMPEG>>>'

# Set correct FFMPEG option
other_operating_systems = ['posix', 'os2', 'ce', 'java', 'riscos']

if os.name in other_operating_systems:
    FFMPEG_BIN = 'ffmpeg'
elif os.name == 'nt':
    FFMPEG_BIN = 'ffmpeg.exe'  # ffmpeg.exe
else:
    print (FFMPEG_prefix + ' We could not find your Operating System type.')
    sys.exit()

###############################
# FFMPEG default arguments
# Standard arguments
ff_file_force = '-y'
ff_file_loop = '-loop'
ff_file_input = '-i'
ff_hide_banner = '-hide_banner'

# Audio arguments:
ff_no_audio = '-an'
ff_audio_codec = '-acodec'
ff_audio_sample_rate = '-ar'
ff_audio_channels = '-ac'
ff_audio_volume = '-af'

# Video arguments:
ff_no_video = '-vn'
ff_video_codec = '-vcodec'
ff_video_framerate = '-r'
ff_video_size = '-s'
ff_video_time = '-t'
###############################

# WARNING: No frame-rate support for non-audio/non-video outputs, advisable to
#          keep both turned off.
# Switch to True to disable audio
VIDEO_NO_AUDIO = False

# Switch to True to disable video
AUDIO_NO_VIDEO = False

# Default output file name
TEMPORARY_OUTPUT = 'temp.flv'


def process_encode_options(command, OUTPUT):
    """
    Process the various FFMPEG options to accompany the encoding of the file.
    NOTE: FILE_PROCESS SET TO 1 in order for this to be executed.
    :param command: list the original set of commands.
    :param OUTPUT: str the output file name.
    :return:
    """
    # Audio options
    if not VIDEO_NO_AUDIO:
        # PROMPT: '-acodec', AUDIO_CODEC, '-ar', AUDIO_SAMPLE_RATE, '-ac', AUDIO_CHANNELS, '-af', AUDIO_VOLUME,
        # AUDIO_CODEC = 'mp3'
        # command.extend([ff_audio_codec, AUDIO_CODEC])
        # AUDIO_SAMPLE_RATE = '16000'
        # command.extend([ff_audio_sample_rate, AUDIO_SAMPLE_RATE])
        # AUDIO_CHANNELS = '1' # Mono
        # command.extend([ff_audio_channels, AUDIO_CHANNELS])
        AUDIO_VOLUME = 'volume=0.5' #  set 0.5 for half the original volume
        command.extend([ff_audio_volume, AUDIO_VOLUME])

    # Video options
    if not AUDIO_NO_VIDEO:
        # PROMPT: '-vcodec', VIDEO_CODEC, '-r', FPS, '-s', SIZE,
        VIDEO_CODEC = 'flv1' # Sorenson FLV1 codec
        command.extend([ff_video_codec, VIDEO_CODEC])
        FPS = '10'
        command.extend([ff_video_framerate, FPS])
        SIZE = '320x240' # 1024x768
        command.extend([ff_video_size, SIZE])

    # Set audio/video output
    if VIDEO_NO_AUDIO:
        command.append(ff_no_audio)
    elif AUDIO_NO_VIDEO:
        command.append(ff_no_video)

    # Append temporary output file and return the newly generated command
    command.append(OUTPUT)
    return command


def process_image_options(command, OUTPUT):
    """
    Process the options required to format an image e.g. '.jpg' or '.gif' into an flv (flv1 codec) file.
    NOTE: FILE_PROCESS SET TO 2 in order for this to be executed.
    :param command: list the original set of commands.
    :param OUTPUT: str the output file name.
    """
    # Image options
    VIDEO_CODEC = 'flv1'
    command.extend([ff_video_codec, VIDEO_CODEC])
    FPS = '10'
    command.extend([ff_video_framerate, FPS])
    SIZE = '320x240'
    command.extend([ff_video_size, SIZE])
    TIME = '20'
    command.extend([ff_video_time, TIME])

    # Append temporary output file and return the new generated command
    command.append(OUTPUT)
    return command


def main(file_process, file_location, output=None):
    """
    Set conversion settings.
    :param file_process:
    :param file_location:
    :param output:
    """
    global AUDIO_NO_VIDEO
    global VIDEO_NO_AUDIO
    global TEMPORARY_OUTPUT

    if output is None:
        OUTPUT = TEMPORARY_OUTPUT
    else:
        OUTPUT = output

    if VIDEO_NO_AUDIO and AUDIO_NO_VIDEO:
        print (FFMPEG_prefix + ' You cannot have both video and audio turned off for a valid output. Turn one or the other on.')
        return None
    else:
        # Only proceed if the file exists
        if os.path.exists(file_location):
            print(FFMPEG_prefix + ' File found for encoding.')
        else:
            print(FFMPEG_prefix + ' File to encode was not found. Aborting encoding.')
            return False

        # Default command
        if file_process is 1:
            command = [FFMPEG_BIN, ff_hide_banner, ff_file_force, ff_file_input]
        elif file_process is 2:
            command = [FFMPEG_BIN, ff_hide_banner, ff_file_force, ff_file_loop, '1', ff_file_input]

        # Original video file
        input_file = file_location
        command.append(input_file)

        # Generate FFMPEG command to pass on
        # Make this more efficient by removing the branch with numbers.
        if file_process is 1:
            command = process_encode_options(command, OUTPUT)
        elif file_process is 2:
            command = process_image_options(command, OUTPUT)
        else:
            print(FFMPEG_prefix + ' Invalid file process provided. Aborting encoding.')
            return False

        print(FFMPEG_prefix + ' FFMPEG Command generated:')
        print(command)
        print(FFMPEG_prefix + ' Initiating FFMPEG and encoding.')

        # Call the command in FFMPEG
        subprocess.call(command)

        if os.path.exists(OUTPUT):
            print(FFMPEG_prefix + ' File was generated successfully.')
            return True
        else:
            print(FFMPEG_prefix + ' File generated was not found.')
            return False


# Standard video settings:
# Video conversion
# main(1, '.mp4', '.flv')

# Image conversion
# main(2, 'AI.jpg', 'ai.flv')

