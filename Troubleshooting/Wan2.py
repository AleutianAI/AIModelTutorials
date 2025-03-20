import torch
import torchvision


def main() -> None:
    print("it works")
    loaded_tensor = torch.load("/home/jintdev/Documents/tensor_cache/cached_tensor.pt")
    print("Loaded tensor successfully")
    print("Tensor shape:", loaded_tensor.shape) # Tensor shape: torch.Size([81, 3, 480, 832])

    if "loaded_tensor" in locals():
        print(loaded_tensor[0])
        tensor = loaded_tensor.clamp(-1, 1)

        nrow = 1
        normalize = True
        value_range = (-1, 1)

        print(f"Tensor min: {tensor.min()}, max: {tensor.max()}")

        print("stacking the tensor")
        tensor = torch.stack([
            torchvision.utils.make_grid(
                u, nrow=nrow, normalize=normalize, value_range=value_range)
            for u in tensor.unbind(2)
        ], dim=1).permute(1, 2, 3, 0)
        print("roundning and casting the tensor")
        tensor = (tensor * 255).round().type(torch.uint8).cpu()

        # Write Video
        print("permuting the tensor")
        tensor = tensor.permute(0, 3, 1, 2)
        cache_file = "/home/jintdev/Documents/output_video.mp4"
        print("writing the video")
        torchvision.io.write_video(cache_file, tensor, fps=30)
        print("Video saved to: ", cache_file)


if __name__ == "__main__":
    main()