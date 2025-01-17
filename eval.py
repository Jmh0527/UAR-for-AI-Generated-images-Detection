import argparse
import logging
from pathlib import Path

import torch
from torch.utils.data import DataLoader
import numpy as np
from sklearn.metrics import accuracy_score, average_precision_score

from networks import NetworkRegistry
from dataset import BaseDataset
from preprocess import TransformRegistry
from eval_engine import Validator

def main(args):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load the model
    if args.model not in NetworkRegistry.list_registered():
        raise ValueError(f"Model {args.model} is not registered in NetworkRegistry.")
    model = NetworkRegistry[args.model]()  # Instantiate the model

    # Load transform
    if args.transform in TransformRegistry.list_registered():
        transform = TransformRegistry[args.transform]()
    else:
        transform = None

    # Load dataset and dataloader
    val_dataloaders = []
    for val in args.validation_sets:
        dataset = BaseDataset(img_paths=Path(args.dataroot)/Path(val), transform=transform)
        val_dataloaders.append(DataLoader(dataset, batch_size=args.batch_size, shuffle=False))

    def write_or_log(line, output_path):
        if output_path:
            with open(output_path, 'a') as f:
                f.write(line+'\n')
        else:
            logger.info(line)

    # Validator
    ACC = []
    for idx, dataloader in enumerate(val_dataloaders):
        validator = Validator(model, dataloader, args.checkpoint)
        acc, ap, r_acc, f_acc = validator.eval()
        result_line = f"{args.validation_sets[idx]} acc: {acc:.4f}, ap: {ap:.4f}, r_acc: {r_acc:.4f}, f_acc: {f_acc:.4f}"
        ACC.append(acc) 
        write_or_log(result_line, args.output)

    average_acc = sum(ACC) / len(ACC)
    average_line = f"average acc: {average_acc:.4f}\n"
    write_or_log(average_line, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='AIMClassifier', help="Defined in the NetworkRegistry: AIMClassifier or PatchCraft")
    parser.add_argument('--dataroot', type=str, required=True, help="Path to the validation dataset root.")
    parser.add_argument('--checkpoint', type=str, required=True, help="Directory containing model checkpoints.")
    parser.add_argument('--batch_size', type=int, default=32, help="Batch size for validation.")
    parser.add_argument('--transform', type=str, default=None, help="Defined TransformRegistry: HighPassFilter or Patch.")
    parser.add_argument(
        '--validation_sets',
        nargs='+',
        help="List of validation set names, if you don't have child dir, then give the value of ''. ",
        default=[
            'progan', 'stylegan', 'biggan', 'cyclegan', 'stargan', 'gaugan',
            'stylegan2', 'whichfaceisreal', 'ADM', 'Glide', 'Midjourney',
            'stable_diffusion_v_1_4', 'stable_diffusion_v_1_5', 'VQDM', 'wukong', 'DALLE2'
        ]
    )
    parser.add_argument('--output', type=str, default=None, help="Output file for validation results.")
    
    args = parser.parse_args()
    main(args)

# python eval.py --dataroot /home/data2/jmh/demo/demo_aimnpy --checkpoint /home/data2/jmh/checkpoints/AIMClassifier/epoch_0_model.pth --validation_sets ''
# python eval.py --dataroot /home/data2/jingmh/data/test_npy --checkpoint /home/data2/jmh/checkpoints/AIMClassifier2/epoch_0_model.pth