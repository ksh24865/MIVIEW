import subprocess
import dcm2img
def convert_img(src: str, dest: str) -> None:
    subprocess.run([
        "python",
        "dcm2img.py",
        "-i",
        src,
        "-o",
        dest
        ])

def segmentation_img(src: str, dest: str) -> None:
    subprocess.run([
        "python",
        "deep/predict.py",
        "-m",
        "deep/body.pth",
        "-i",        
        src,
        "-o",
        dest,
        "-s",
        "1.0"
        ])


# convert_img("b.jpg", "c.jpg")
# segmentation_img("deep/img", "deep/temp")