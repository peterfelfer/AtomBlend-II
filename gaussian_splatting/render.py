#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#
import numpy as np
import torch
from gaussian_splatting.scene import Scene
import os
from tqdm import tqdm
from os import makedirs
from gaussian_splatting.gaussian_renderer import render
import torchvision
from gaussian_splatting.utils.general_utils import safe_state
from argparse import ArgumentParser
from gaussian_splatting.arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_splatting.gaussian_renderer import GaussianModel
from gaussian_splatting.scene.cameras import Camera

def render_set(model_path, name, iteration, views, gaussians, pipeline, background):
    render_path = os.path.join(model_path, name, "ours_{}".format(iteration), "renders")
    gts_path = os.path.join(model_path, name, "ours_{}".format(iteration), "gt")

    makedirs(render_path, exist_ok=True)
    makedirs(gts_path, exist_ok=True)

    for idx, view in enumerate(tqdm(views, desc="Rendering progress")):
        rendering = render(view, gaussians, pipeline, background)["render"]
        gt = view.original_image[0:3, :, :]
        torchvision.utils.save_image(rendering, os.path.join(render_path, '{0:05d}'.format(idx) + ".png"))
        torchvision.utils.save_image(gt, os.path.join(gts_path, '{0:05d}'.format(idx) + ".png"))

def render_sets(dataset : ModelParams, iteration : int, pipeline : PipelineParams, skip_train : bool, skip_test : bool):
    with torch.no_grad():
        gaussians = GaussianModel(dataset.sh_degree)
        scene = Scene(dataset, gaussians, load_iteration=iteration, shuffle=False)

        bg_color = [1,1,1] if dataset.white_background else [0, 0, 0]
        background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

        if not skip_train:
             render_set(dataset.model_path, "train", scene.loaded_iter, scene.getTrainCameras(), gaussians, pipeline, background)

        if not skip_test:
             render_set(dataset.model_path, "test", scene.loaded_iter, scene.getTestCameras(), gaussians, pipeline, background)

def render_view_blender(atom_coords, camera_specs):
    from argparse import Namespace

    args = Namespace(compute_cov3D_python=False, convert_SHs_python=False, data_device='cuda', debug=False, eval=False,
              images='images', iteration=-1, model_path='/harddisk1/home.local/qa43nawu/gaussian_splatting/output/9224d987-c/', quiet=False, resolution=-1, sh_degree=3,
              skip_test=False, skip_train=False, source_path='/harddisk1/home.local/qa43nawu/input_files/voldata',
              white_background=False)

    ply_model = '/harddisk1/home.local/qa43nawu/gaussian_splatting/output/9224d987-c/'
    model = ModelParams(ply_model)
    dataset = model.extract(args)
    gaussians = GaussianModel(dataset.sh_degree)

    gaussians.xyz = torch.tensor(atom_coords, dtype=torch.float32, device="cuda")
    # gaussians.xyz = torch.tensor([[1.0, 1.0,1.0],[0.0,1.0,0.0],[1.0,0.0,0.0]], dtype=torch.float32, device="cuda")
    gaussians._opacity = torch.tensor([[1.0],[1.0],[1.0]], dtype=torch.float32, device="cuda")
    gaussians._rotation = torch.tensor([[1.0,0.0,0.0],[1.0,0.0,0.0],[1.0,0.0,0.0]], dtype=torch.float32, device="cuda")
    gaussians._scaling = torch.tensor([[1.0,1.0,1.0],[1.0,1.0,1.0],[1.0,1.0,1.0]], dtype=torch.float32, device="cuda")
    # gaussians = GaussianModel(xyz, dataset.sh_degree)

    pipeline = PipelineParams(args)
    bg_color = [1, 1, 1]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
    scene = Scene(dataset, gaussians, load_iteration=-1, shuffle=False)
    view = scene.getTrainCameras()


    v = view[0]

    # def __init__(self, colmap_id, R, T, FoVx, FoVy, image, gt_alpha_mask,
    #              image_name, uid,
    #              trans=np.array([0.0, 0.0, 0.0]), scale=1.0, data_device = "cuda"
    #              ):
    colmad_id = 1
    R = np.asarray([[1., 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    # T = np.asarray([-2.6, 300, 40])
    T = np.asarray(camera_specs['T'])
    FoVx = camera_specs['FoVx']
    FoVy = camera_specs['FoVy']
    # FoVx = 0.0001
    # FoVy = 0.0001
    uid = 0

    dummy_cam = Camera(colmad_id, R, T, FoVx, FoVy, None, None, 'bla', uid)

    rendering = render(dummy_cam, gaussians, pipeline, background)["render"]
    render_path = '/harddisk1/home.local/qa43nawu/out/'
    torchvision.utils.save_image(rendering, os.path.join(render_path, '{0:05d}'.format(0) + ".png"))


    print('done')

if __name__ == "__main__":
    # Set up command line argument parser
    parser = ArgumentParser(description="Testing script parameters")
    model = ModelParams(parser, sentinel=True)
    pipeline = PipelineParams(parser)
    parser.add_argument("--iteration", default=-1, type=int)
    parser.add_argument("--skip_train", action="store_true")
    parser.add_argument("--skip_test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = get_combined_args(parser)
    print("Rendering " + args.model_path)

    # Initialize system state (RNG)
    safe_state(args.quiet)

    render_sets(model.extract(args), args.iteration, pipeline.extract(args), args.skip_train, args.skip_test)