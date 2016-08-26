""" Interface with the VideoCapture library """

# Developed by Goel Biju (2016)
# https://github.com/GoelBiju/

import time
# import os
# import sys

# Testing out PyAV compatibility.
# import av
# import argparse

from VideoCapture import Device
# from numpy import array
# from subprocess import Popen, PIPE

# Handle arguments:
# arg_parser = argparse.ArgumentParser()
# arg_parser.add_argument('-r', '--rate', default='23.976')
# arg_parser.add_argument('-f', '--format', default='yuv420p')
# arg_parser.add_argument('-w', '--width', type=int)
# arg_parser.add_argument('--height', type=int)
# arg_parser.add_argument('-b', '--bitrate', type=int, default=8000000)
# arg_parser.add_argument('-c', '--codec', default='mpeg4')
# arg_parser.add_argument('inputs', nargs='+')
# arg_parser.add_argument('output', nargs=1)
# args = arg_parser.parse_args()

# output = av.open(args.output[0], 'w')
# output = av.open('file.mp4', 'w')
# stream = output.add_stream('mpeg4')
# stream.pix_fmt = 'yuv420p'
# stream = output.add_stream(args.codec, args.rate)
# stream.bit_rate = args.bitrate
# stream.pix_fmt = args.format

# Webcam instance; must use "del cam" in this case to stop using the webcam.
cam = Device(devnum=1)

print('Display device: %s' % cam.getDisplayName())
# Save an snapshot taken with the webcam.
try:
    for x in range(50):
        # Take a snapshot and only show it without saving it to disk.
        # cam.saveSnapshot(only_show=True)

        # Get an image directly via PIL and then show it.
        # img = cam.getImage()
        # img.show()

        # Retrieve the buffer from the image generated,
        # getBuffer returns 3 items (raw buffer, width, height of the iamge).
        cam_buffer = cam.getBuffer()
        print('Length of buffer generated: %s bytes' % len(cam_buffer[0]))
        time.sleep(1)

        # Add information to stream.
        # stream.width = cam_buffer[1]
        # stream.height = cam_buffer[2]

        # Store the PIL image as a numpy array.
        # np_array = array(img)
        # print('Length of numpy array: %s' % len(np_array))

        # Generate a frame with PyAV.
        # frame = av.VideoFrame.from_ndarray(img)
        # frame = av.VideoFrame.from_image(img)

        # Encode a packet into the stream.
        # packet = stream.encode(frame)

        # Mux the packet into the output file.
        # output.mux(packet)

    # Close the output file.
    # output.close()

except Exception as ex:
    print(ex)
finally:
    # Delete the webcam instance that was generated; this will free the camera from Python,
    # if it is not deleted, the instance will remain until the script is restarted.
    del cam


# The buffer that is generated from the image taken.
# print  "Length of buffer:", len(buf), "Width of image:", width, "Height of image:", height

# args = ["ffmpeg.exe", "-y", "-f", "mpeg4", "-i", "-", "-vcodec", "flv1", "new.flv"]

"""
pipe = Popen(args, stdin=PIPE, stdout=PIPE)

file_content = open('big_buck.mp4', 'rb')
file_data = file_content.read()
print "Length of data:", len(file_data)

pipe.stdin.write(file_data)

pipe.stdin.close()
pipe.stderr.close()
pipe.wait()
"""
#
# command = ["ffmpeg.exe",
#            '-y', # (optional) overwrite output file if it exists
#            '-f', 'rawvideo',
#            '-vcodec','rawvideo',
#            '-s', '%dx%d' % (420, 360), # size of one frame
#            '-pix_fmt', 'rgb24',
#            #'-r', '24', # frames per second
#            '-i', '-', # The imput comes from a pipe
#            '-an', # Tells FFMPEG not to expect any audio
#            '-vcodec', 'mpeg4', "-"] # mpeg4
#            #'my_output_videofile.mp4']
#
# proc = Popen(command, stdin=PIPE, stderr=PIPE, stdout=PIPE)

# a = np.zeros((width, height, 3), dtype=np.uint8)

# for ii in range(5*24):
#    print(ii)
#    proc.stdin.write(a.tostring())
#    time.sleep(1/24)

# Get the buffer, width and height from the image from the camera.
# buf, width, height = cam.getBuffer()
# proc.stdin.write(buf)

# output = proc.stdout.readline()

# del cam