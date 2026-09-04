_base_ = "./base/mmdetection/configs/rtmdet/rtmdet_tiny_8xb32-300e_coco.py"

data_root = "dataset/"
work_dir = "work_dirs/rtmdet_tiny_bag"

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

load_from = None

max_epochs = 30

train_cfg = dict(
    _delete_ = True,
    type = "EpochBasedTrainLoop",
    max_epochs = max_epochs,
    val_interval = 1,
)

optim_wrapper = dict(
    optimizer = dict(
        lr = 0.00025
    )
)

default_hooks = dict(
    checkpoint = dict(
        _delete_ = True,
        type = "CheckpointHook",
        interval = 1,
        max_keep_ckpts = 3,
        save_best = "coco/bbox_mAP"
    )
)

