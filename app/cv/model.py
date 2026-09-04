from mmdet.apis import init_detector
from pathlib import Path

config_path = Path(r"configs\rtmdet_tiny_bag.py")
ckpt_path = Path(r"work_dirs\rtmdet_tiny_bag\best_coco_bbox_mAP_epoch_27.pth")

def load_model():
    return init_detector(
    str(config_path),
    str(ckpt_path),
    device = "cuda:0"
)