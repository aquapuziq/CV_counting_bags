from mmdet.apis import init_detector
from pathlib import Path

pr_root = Path(__file__).resolve().parents[2]
config_path = pr_root / "configs" / "rtmdet_tiny_bag.py"
ckpt_path = pr_root / "checkpoints" / "best_coco_bbox_mAP_epoch_27.pth"
def load_model():
    return init_detector(
    str(config_path),
    str(ckpt_path),
    device = "cuda:0"
)