_base_ = r"C:\Users\kopchonyPyos\mmdetection\configs\rtmdet\rtmdet_tiny_8xb32-300e_coco.py"

data_root = r"C:\dev\projects\CV_counting_bags\dataset\\"
work_dir = r"C:\dev\projects\CV_counting_bags\work_dirs\rtmdet_tiny_bag"

metainfo = {
    "classes": ("bag",),
}

model = dict(
    bbox_head = dict(
        num_classes = 1
    )
)

train_dataloader = dict(
    batch_size = 2,
    num_workers = 2,
    dataset = dict(
        data_root = data_root,
        ann_file = r"annotations\instances_train.json",
        data_prefix = dict(img = "train/"),
        metainfo = metainfo,
    )
)

val_dataloader = dict(
    batch_size = 1,
    num_workers = 2,
    dataset = dict(
        data_root = data_root,
        ann_file = r"annotations\instances_val.json",
        data_prefix = dict(img = "val/"),
        metainfo = metainfo,
    )
)

val_evaluator = dict(
    ann_file = data_root + r"annotations\instances_val.json",
)

test_dataloader = val_dataloader
test_evaluator = val_evaluator

load_from = r"C:\dev\projects\CV_counting_bags\checkpoints\rtmdet_tiny.pth"

train_cfg = dict(
    max_epochs = 30,
    val_interval = 1,
)

optim_wrapper = dict(
    optimizer = dict(
        lr = 0.00025
    )
)

default_hooks = dict(
    checkpoint = dict(
        type = "CheckpointHook",
        interval = 1,
        max_step_ckpts = 3,
        save_best = r"coco\bbox_mAP"
    )
)

