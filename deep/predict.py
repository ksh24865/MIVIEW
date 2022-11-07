import argparse
import logging
import os
import datetime

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from unet import UNet
from utils.data_vis import plot_img_and_mask
from utils.dataset import BasicDataset


def predict_img(net,
                full_img,
                device,
                scale_factor=1,
                out_threshold=0.5):
    net.eval()

    img = torch.from_numpy(BasicDataset.preprocess(full_img, scale_factor))

    img = img.unsqueeze(0)
    img = img.to(device=device, dtype=torch.float32)

    with torch.no_grad():
        output = net(img)

        if net.n_classes > 1:
            probs = F.softmax(output, dim=1)
        else:
            probs = torch.sigmoid(output)

        probs = probs.squeeze(0)

        tf = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize(full_img.size[1]),
                transforms.ToTensor()
            ]
        )

        probs = tf(probs.cpu())
        full_mask = probs.squeeze().cpu().numpy()

    return full_mask > out_threshold


def get_args():
    parser = argparse.ArgumentParser(description='Predict masks from input images',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--model', '-m', default='MODEL.pth',
                        metavar='FILE',
                        help="Specify the file in which the model is stored")
    parser.add_argument('--input', '-i', metavar='INPUT', nargs='+',
                        help='filenames of input images', required=True)

    parser.add_argument('--output', '-o', metavar='INPUT', nargs='+',
                        help='Filenames of ouput images')
    parser.add_argument('--viz', '-v', action='store_true',
                        help="Visualize the images as they are processed",
                        default=False)
    parser.add_argument('--no-save', '-n', action='store_true',
                        help="Do not save the output masks",
                        default=False)
    parser.add_argument('--mask-threshold', '-t', type=float,
                        help="Minimum probability value to consider a mask pixel white",
                        default=0.5)
    parser.add_argument('--scale', '-s', type=float,
                        help="Scale factor for the input images",
                        default=0.5)

    return parser.parse_args()


def get_output_filenames(args):
    in_files = args.input
    out_files = []

    if not args.output:
        for f in in_files:
            pathsplit = os.path.splitext(f)
            out_files.append("{}_OUT{}".format(pathsplit[0], pathsplit[1]))
    elif len(in_files) != len(args.output):
        logging.error("Input files and output files are not of the same length")
        raise SystemExit()
    else:
        out_files = args.output

    return out_files


def mask_to_image(mask):
    return Image.fromarray((mask * 255).astype(np.uint8))


if __name__ == "__main__":
    args = get_args()
    path_dir = args.input[0]
    file_list = os.listdir(path_dir)
#     in_files = args.input

    net = UNet(n_channels=1, n_classes=1)

    logging.info("Loading model {}".format(args.model))

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#     device = torch.device('cpu')
    logging.info(f'Using device {device}')
    net.to(device=device)
    net.load_state_dict(torch.load(args.model, map_location=device))

    logging.info("Model loaded !")
    
    nowDate = datetime.datetime.now()
    
    folder_name = args.output[0] + "/segmentation"
    
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
        os.mkdir(folder_name + "/mask")
        os.mkdir(folder_name + "/combine")

    for i, fn in enumerate(file_list):
        mask_img = Image.new('RGBA', (512, 512), (0, 0, 0, 255))
        fn = path_dir + '/' + file_list[i]
        logging.info("\nPredicting image {} ...".format(fn))

        img = Image.open(fn).convert('L')

        mask = predict_img(net=net,
                           full_img=img,
                           scale_factor=args.scale,
                           out_threshold=args.mask_threshold,
                           device=device)

        if not args.no_save:
            mask_data = []
            newData = []
            
            mask_img = Image.new('RGBA', (img.size[0], img.size[1]), (0, 0, 0, 255))
            mask_img2 = Image.new('RGBA', (img.size[0], img.size[1]), (0, 0, 0, 255))
            out_fn_mask = folder_name + "/mask/" + file_list[i]
            out_fn_combine = folder_name + "/combine/" + file_list[i]
            
            result = mask_to_image(mask)
            result.save(out_fn_mask[:-4] + ".png", "PNG")
            datas = result.getdata()
            
            for item in datas:
                if item > 0:
                    newData.append((255, 0, 0, 255))
                else:
                    newData.append((0, 0, 0, 255))
            
            mask_img2.putdata(newData)
            
            mask_img = Image.blend(img.convert("RGBA"), mask_img2, alpha=0.3)
            
            mask_img.save(out_fn_combine[:-4] + ".png", "PNG")
            
        if args.viz:
            logging.info("Visualizing results for image {}, close to continue ...".format(fn))
            plot_img_and_mask(img, mask)
