import pydicom
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt


def get_args():
    parser = argparse.ArgumentParser(description="Convert DICOM File to Image File")
    parser.add_argument('-i', '--input', metavar='path', type=str, required=True, help='Input File Path or File Name',
                        dest='input')
    parser.add_argument('-o', '--output', metavar='path', type=str, default=False, help='Output File Path or File Name',
                        dest='output')
    parser.add_argument('-t', '--type', metavar='type', type=str, default='.bmp', help='Output File Extension Type',
                        dest='type')
    parser.add_argument('-wc', '--window-center', metavar='val', type=int, default=False, help='Window Center Value',
                        dest='wc')
    parser.add_argument('-ww', '--window-width', metavar='val', type=int, default=False, help='Window Width Value',
                        dest='ww')

    return parser.parse_args()


def load_dcm(path):
    file_type = os.path.splitext(path)[1]

    try:
        if file_type != ".dcm":
            raise TypeError

        dcm_data = pydicom.dcmread(path)

    except TypeError:
        print(f'"{file_type}": That is not DICOM File.')
        return False

    except FileNotFoundError:
        print(f'No such files were found: "{path}"')
        return False

    try:
        ww = dcm_data.WindowWidth[0]
        wc = dcm_data.WindowCenter[0]

    except TypeError:
        ww = dcm_data.WindowWidth
        wc = dcm_data.WindowCenter

    except AttributeError:
        ww = 0
        wc = 0

    try:
        reslope = int(dcm_data.RescaleSlope)
        reinter = int(dcm_data.RescaleIntercept)

    except:
        reslope = 1
        reinter = 0

    hu_data = reslope * dcm_data.pixel_array + reinter

    return hu_data, {'ww': ww, 'wc': wc}


def clip_array(hu, ww, wc):
    return np.clip(hu, wc - (ww / 2), wc + (ww / 2))


def run_script(input, output):
    hu_array, window_info = load_dcm(input)

    ww = window_info['ww']
    wc = window_info['wc']

    clip_hu = clip_array(hu_array, ww, wc)

    split_output = os.path.splitext(output)

    file_name = split_output[0]
    file_type = split_output[1]

    output = file_name + file_type

    try:
        plt.imsave(output, clip_hu, cmap='gray')
    except FileNotFoundError:
        print(f'There is no directory: "{output}"')
        print("Make directory")
        os.mkdir(os.path.split(output)[0])
        plt.imsave(output, clip_hu, cmap='gray')

    print(f'SAVE: {output}')