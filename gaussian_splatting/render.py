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
import math

import numpy
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
from ab_utils import *

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

def render_view_blender(atom_coords, atom_color_list, props):
    from argparse import Namespace

    args = Namespace(compute_cov3D_python=False, convert_SHs_python=True, data_device='cuda', debug=False, eval=False,
              images='images', iteration=-1, model_path='/harddisk1/home.local/qa43nawu/gaussian_splatting/output/9224d987-c/', quiet=False, resolution=-1, sh_degree=3,
              skip_test=False, skip_train=False, source_path='/harddisk1/home.local/qa43nawu/input_files/voldata',
              white_background=False)

    ply_model = '/harddisk1/home.local/qa43nawu/gaussian_splatting/output/9224d987-c/'
    model = ModelParams(ply_model)
    dataset = model.extract(args)
    gaussians = GaussianModel(dataset.sh_degree)
    # gaussians = GaussianModel(3)

    atom_coords_numpy = numpy.asarray(atom_coords)
    gaussians.xyz = torch.tensor(atom_coords, dtype=torch.float32, device="cuda")

    pipeline = PipelineParams(args)
    bg_color = props["background_color"]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
    scene = Scene(dataset, gaussians, atom_coords_numpy, props, load_iteration=-1, shuffle=False)

    colmad_id = 1

    # R = np.asarray([props['R'][0][:3], props['R'][1][:3], props['R'][2][:3]])
    # R_old = np.asarray([props['R'][0][:3], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    a_x = props['R'][0]
    a_y = props['R'][1]
    a_z = props['R'][2]
    R_x = np.asarray([[1.0, 0.0, 0.0], [0.0, math.cos(a_x), -math.sin(a_x)], [0.0, math.sin(a_x), math.cos(a_x)]])
    R_y = np.asarray([[math.cos(a_y), 0.0, math.sin(a_y)], [0.0, 1.0, 0.0], [-math.sin(a_y), 0.0, math.cos(a_y)]])
    R_z = np.asarray([[math.cos(a_z), -math.sin(a_z), 0.0], [math.sin(a_z), math.cos(a_z), 0.0], [0.0, 0.0, 1.0]])

    R = np.matmul(np.matmul(R_x, R_y), R_z)

    # T = np.asarray([-2.6, 300, 40])
    T = np.asarray(props['T'])
    FoVx = props['FoVx']
    FoVy = props['FoVy']
    # FoVx = 0.0001
    # FoVy = 0.0001
    uid = 0

    dummy_cam = Camera(colmad_id, R, T, FoVx, FoVy, None, None, 'bla', uid)

    # color preparation
    colors = torch.tensor(np.asarray(atom_color_list)[:, :3], dtype=torch.float32, device="cuda")

    rendering = render(dummy_cam, gaussians, pipeline, background, override_color=colors)["render"]
    render_path = '/harddisk1/home.local/qa43nawu/out/'
    torchvision.utils.save_image(rendering, os.path.join(render_path, '{0:05d}'.format(0) + ".png"))


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

    # render_sets(model.extract(args), args.iteration, pipeline.extract(args), args.skip_train, args.skip_test)
    atom_coords = read_atom_coords()
    render_without_blender(atom_coords)