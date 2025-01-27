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

from argparse import ArgumentParser, Namespace
import sys
import os

class GroupParams:
    pass

class ParamGroup:
    def __init__(self, parser: ArgumentParser, name : str, fill_none = False):
        group = parser.add_argument_group(name)
        for key, value in vars(self).items():
            shorthand = False
            if key.startswith("_"):
                shorthand = True
                key = key[1:]
            t = type(value)
            value = value if not fill_none else None 
            if shorthand:
                if t == bool:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, action="store_true")
                elif t == list:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, 
                                        type=lambda x: [float(y) for y in x.split(',')])
                else:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, type=t)
            else:
                if t == bool:
                    group.add_argument("--" + key, default=value, action="store_true")
                elif t == list:
                    group.add_argument("--" + key, default=value, 
                                        type=lambda x: [float(y) for y in x.split(',')])
                else:
                    group.add_argument("--" + key, default=value, type=t)

    def extract(self, args):
        group = GroupParams()
        for arg in vars(args).items():
            if arg[0] in vars(self) or ("_" + arg[0]) in vars(self):
                setattr(group, arg[0], arg[1])
        return group

class ModelParams(ParamGroup): 
    def __init__(self, parser, sentinel=False):
        self.sh_degree = 3
        self._source_path = ""
        self._model_path = ""
        self._images = "images"
        self._resolution = -1
        self._white_background = False
        self.bg_dist = 500
        self.data_device = "cuda"
        self.eval = False
        self.num_train_images = 3
        self.camera_radius_scale = 0.33 # `scale` parameter in DiffusioNerf
        self.random_initialisation = False
        super().__init__(parser, "Loading Parameters", sentinel)

    def extract(self, args):
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g

class PipelineParams(ParamGroup):
    def __init__(self, parser):
        self.convert_SHs_python = True
        self.compute_cov3D_python = False
        self.debug = False
        super().__init__(parser, "Pipeline Parameters")

class OptimizationParams(ParamGroup):
    def __init__(self, parser):
        self.iterations = 30_000
        self.position_lr_init = 0.00016
        self.position_lr_final = 0.0000016
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 30_000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.05
        self.scaling_lr = 0.005
        self.rotation_lr = 0.001
        self.percent_dense = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 100
        self.opacity_reset_interval = 3000
        self.densify_from_iter = [500]
        self.densify_until_iter = [15_000]
        # self.densify_from_iter2 = 16_000
        # self.densify_until_iter2 = 20_000
        self.densify_grad_threshold = 0.0002
        self.max_gaussians = 1000000
        # Regularisation
        self.fg_reg_weight = 0.02
        # Patch regularisation
        self.skip_reconstructions = -1
        self.patch_regulariser_path = ""
        self.initial_diffusion_time = 0.1
        self.final_diffusion_time = 0.0
        self.patch_reg_start_step = [500]
        self.patch_reg_finish_step = [-1]
        self.patch_weight_start = [1.]
        self.patch_weight_finish = [1.]
        self.patch_sample_downscale_factor = 4
        self.normalise_diffusion_losses = False
        self.frustum_check_patches = False
        self.debug_visualise_patches = False
        self.diffusion_batch_size = 8
        self.p_sample_patch_start = 0.25
        self.p_sample_patch_finish = 0.25
        self.recompute_depth_iterations = 100
        self.perturbation_strength_start = 0.0
        self.perturbation_strength_finish = 0.5
        # Frustum regularisation
        self.frustum_regularise_patches = False
        self.min_near = 0.05
        self.frustum_reg_initial_weight = 1.
        self.frustum_reg_final_weight = 1e-2
        # Lenticular regularisation
        self.lenticular_reg_initial_weight = 1.
        self.lenticular_reg_final_weight = 1e-2
        super().__init__(parser, "Optimization Parameters")

def get_combined_args(parser : ArgumentParser):
    cmdlne_string = sys.argv[1:]
    cfgfile_string = "Namespace()"
    args_cmdline = parser.parse_args(cmdlne_string)

    try:
        cfgfilepath = os.path.join(args_cmdline.model_path, "cfg_args")
        print("Looking for config file in", cfgfilepath)
        with open(cfgfilepath) as cfg_file:
            print("Config file found: {}".format(cfgfilepath))
            cfgfile_string = cfg_file.read()
    except TypeError:
        print("Config file not found at")
        pass
    args_cfgfile = eval(cfgfile_string)

    merged_dict = vars(args_cfgfile).copy()
    for k,v in vars(args_cmdline).items():
        if v != None:
            merged_dict[k] = v
    return Namespace(**merged_dict)
