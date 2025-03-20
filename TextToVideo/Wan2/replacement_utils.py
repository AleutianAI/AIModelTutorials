# Copyright 2024-2025 The Alibaba Wan Team Authors. All rights reserved.
import argparse
import binascii
import os
import os.path as osp

import imageio
import torch
import torchvision
import cv2

__all__ = ['cache_video', 'cache_image', 'str2bool']


def rand_name(length=8, suffix=''):
    name = binascii.b2a_hex(os.urandom(length)).decode('utf-8')
    if suffix:
        if not suffix.startswith('.'):
            suffix = '.' + suffix
        name += suffix
    return name


def cache_video(tensor, save_file=None, fps=30, suffix='.mp4', nrow=8, normalize=True,
                value_range=(-1, 1), retry=5,
                cached_tensor_file="/app/tensor_cache/cached_tensor.pt"):
    # cache file
    cache_file = osp.join('/tmp', 'temp_video' + suffix) if save_file is None else save_file

    # save to cache
    error = None
    for _ in range(retry):
        try:
            # preprocess
            torch.save(tensor, cached_tensor_file)
            print(tensor[0])
            tensor = tensor.clamp(min(value_range), max(value_range))
            tensor = torch.stack([
                torchvision.utils.make_grid(
                    u, nrow=nrow, normalize=normalize, value_range=value_range)
                for u in tensor.unbind(2)
            ], dim=1).permute(1, 2, 3, 0)
            tensor = (tensor * 255).round().type(torch.uint8).cpu()

            # Write Video
            tensor = tensor.permute(0, 3, 1, 2)
            print(f"Tensor shape before write_video: {tensor.shape}")
            torchvision.io.write_video(cache_file, tensor, fps=fps)
            return cache_file

            # # preprocess
            # tensor = tensor.clamp(min(value_range), max(value_range))
            # tensor = torch.stack([
            #     torchvision.utils.make_grid(
            #         u, nrow=nrow, normalize=normalize, value_range=value_range)
            #     for u in tensor.unbind(2)
            # ], dim=1).permute(1, 2, 3, 0)
            # print(f"Tensor dtype before scaling: {tensor.dtype}")
            # print(f"Tensor min/max before scaling: {tensor.min()}, {tensor.max()}")
            # tensor = (tensor * 255)
            # print(f"Tensor dtype after scaling: {tensor.dtype}")
            # print(f"Tensor min/max after scaling: {tensor.min()}, {tensor.max()}")
            # tensor = tensor.round().type(torch.uint8).cpu()
            # print(f"Tensor dtype after uint8 conversion: {tensor.dtype}")
            # print(f"Tensor min/max after uint8 conversion: {tensor.min()}, {tensor.max()}")
            # print(f"Frame shape: {frame.shape}")
            # print(f"Frame contiguous: {frame.flags['C_CONTIGUOUS']}")
            # torch.save(tensor, cached_tensor_file)
            # # # use open cv to write the video
            # # frames = tensor.numpy()
            # # height, width, channels = frames[0].shape
            # # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Or another codec
            # # writerCV2 = cv2.VideoWriter(cache_file, fourcc, fps, (width, height))
            # # for frame in frames:
            # #     writerCV2.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # important BGR conversion
            # # writerCV2.release()
            # # write video
            # print(f"Tensor shape: {tensor.shape}")
            # print(f"Cache file path: {cache_file}")
            # writer = imageio.get_writer(cache_file, fps=fps, codec='libx264', quality=8)
            # for frame in tensor.numpy():
            #     print(f"Frame dtype: {frame.dtype}")
            #     print(f"Frame min/max: {frame.min()}, {frame.max()}")
            #     writer.append_data(frame)
            # writer.close()
            # return cache_file
        except Exception as e:
            error = e
            continue
    else:
        print(f'cache_video failed, error: {error}', flush=True)
        return None


def cache_image(tensor,
                save_file,
                nrow=8,
                normalize=True,
                value_range=(-1, 1),
                retry=5):
    # cache file
    suffix = osp.splitext(save_file)[1]
    if suffix.lower() not in [
            '.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp'
    ]:
        suffix = '.png'

    # save to cache
    error = None
    for _ in range(retry):
        try:
            tensor = tensor.clamp(min(value_range), max(value_range))
            torchvision.utils.save_image(
                tensor,
                save_file,
                nrow=nrow,
                normalize=normalize,
                value_range=value_range)
            return save_file
        except Exception as e:
            error = e
            continue


def str2bool(v):
    """
    Convert a string to a boolean.

    Supported true values: 'yes', 'true', 't', 'y', '1'
    Supported false values: 'no', 'false', 'f', 'n', '0'

    Args:
        v (str): String to convert.

    Returns:
        bool: Converted boolean value.

    Raises:
        argparse.ArgumentTypeError: If the value cannot be converted to boolean.
    """
    if isinstance(v, bool):
        return v
    v_lower = v.lower()
    if v_lower in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v_lower in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected (True/False)')