import numpy as np
from plyfile import PlyData
from dataclasses import dataclass

@dataclass
class GaussianData:
    xyz: np.ndarray
    rot: np.ndarray
    scale: np.ndarray
    opacity: np.ndarray
    sh: np.ndarray
    cov3D: np.ndarray
    num_of_atoms_by_element: dict

    def flat(self) -> np.ndarray:
        ret = np.concatenate([self.xyz, self.rot, self.scale, self.opacity, self.sh], axis=-1)
        return np.ascontiguousarray(ret)
    
    def __len__(self):
        return len(self.xyz)
    
    @property 
    def sh_dim(self):
        return self.sh.shape[-1]


def naive_gaussian():
    gau_xyz = np.array([
        0, 0, 0,
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
    ]).astype(np.float32).reshape(-1, 3)
    gau_rot = np.array([
        1, 0, 0, 0,
        1, 0, 0, 0,
        1, 0, 0, 0,
        1, 0, 0, 0
    ]).astype(np.float32).reshape(-1, 4)
    gau_s = np.array([
        0.03, 0.03, 0.03,
        0.2, 0.03, 0.03,
        0.03, 0.2, 0.03,
        0.03, 0.03, 0.2
    ]).astype(np.float32).reshape(-1, 3)
    gau_c = np.array([
        1, 0, 1, 
        1, 0, 0, 
        0, 1, 0, 
        0, 0, 1, 
    ]).astype(np.float32).reshape(-1, 3)
    gau_c = (gau_c - 0.5) / 0.28209
    gau_a = np.array([
        1, 1, 1, 1
    ]).astype(np.float32).reshape(-1, 1)
    gau_num_of_atoms_by_element = {
        'dummy': {
            'num': 4,
            'color': (1.0, 0.0, 0.0, 1.0),
            'scale': 0.1,
        },
    }
    gau_cov3D = np.array([
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]).astype(np.float32).reshape(-1, 3)

    return GaussianData(
        gau_xyz,
        gau_rot,
        gau_s,
        gau_a,
        gau_c,
        gau_cov3D,
        gau_num_of_atoms_by_element
    )


def load_ply(path):
    max_sh_degree = 3
    plydata = PlyData.read(path)

    num_of_atoms_by_element = {}
    for line in plydata.header.split('\n'):
        if line.startswith('comment'):
            if '//' in line:
                element_name, rest = line.split('//', 1)
                num, r, g, b = rest.split(' ')
                r = float(int(r) / 255)
                g = float(int(g) / 255)
                b = float(int(b) / 255)

                obj = {
                    'num': int(num),
                    'color': (r, g, b, 1.0),
                    'scale': 0.1,
                }

                num_of_atoms_by_element[element_name.split(' ')[1]] = obj

        if line.startswith('property'):
            break

    xyz = np.stack((np.asarray(plydata.elements[0]["x"]),
                    np.asarray(plydata.elements[0]["y"]),
                    np.asarray(plydata.elements[0]["z"])),  axis=1)
    opacities = np.asarray(plydata.elements[0]["opacity"])[..., np.newaxis]
    opacities = np.asarray([[1.0]] * len(xyz))

    features_dc = np.zeros((xyz.shape[0], 3, 1))
    features_dc[:, 0, 0] = np.asarray(plydata.elements[0]["f_dc_0"])
    features_dc[:, 1, 0] = np.asarray(plydata.elements[0]["f_dc_1"])
    features_dc[:, 2, 0] = np.asarray(plydata.elements[0]["f_dc_2"])

    '''
    extra_f_names = [p.name for p in plydata.elements[0].properties if p.name.startswith("f_rest_")]
    extra_f_names = sorted(extra_f_names, key = lambda x: int(x.split('_')[-1]))
    assert len(extra_f_names)==3 * (max_sh_degree + 1) ** 2 - 3
    features_extra = np.zeros((xyz.shape[0], len(extra_f_names)))
    for idx, attr_name in enumerate(extra_f_names):
        features_extra[:, idx] = np.asarray(plydata.elements[0][attr_name])
    # Reshape (P,F*SH_coeffs) to (P, F, SH_coeffs except DC)
    features_extra = features_extra.reshape((features_extra.shape[0], 3, (max_sh_degree + 1) ** 2 - 1))
    features_extra = np.transpose(features_extra, [0, 2, 1])
    '''

    scale_names = [p.name for p in plydata.elements[0].properties if p.name.startswith("scale_")]
    scale_names = sorted(scale_names, key = lambda x: int(x.split('_')[-1]))
    scales = np.zeros((xyz.shape[0], len(scale_names)))
    for idx, attr_name in enumerate(scale_names):
        scales[:, idx] = np.asarray(plydata.elements[0][attr_name])

    rot_names = [p.name for p in plydata.elements[0].properties if p.name.startswith("rot")]
    rot_names = sorted(rot_names, key = lambda x: int(x.split('_')[-1]))
    rots = np.zeros((xyz.shape[0], len(rot_names)))
    for idx, attr_name in enumerate(rot_names):
        rots[:, idx] = np.asarray(plydata.elements[0][attr_name])

    cov3D_names = [p.name for p in plydata.elements[0].properties if p.name.startswith("cov3D")]
    cov3D_names = sorted(cov3D_names, key = lambda x: int(x.split('_')[-1]))
    cov3Ds = np.zeros((xyz.shape[0], len(cov3D_names)))
    for idx, attr_name in enumerate(cov3D_names):
        bla = np.asarray(plydata.elements[0][attr_name])
        cov3Ds[:, idx] = np.asarray(plydata.elements[0][attr_name])

        if np.isnan(bla).any():
            print('NAN', bla)

    # pass activate function
    xyz = xyz.astype(np.float32)
    # rots = rots / np.linalg.norm(rots, axis=-1, keepdims=True)
    rots = rots.astype(np.float32)
    scales = np.exp(scales)
    scales = scales.astype(np.float32)
    # opacities = 1/(1 + np.exp(- opacities))  # sigmoid
    opacities = opacities.astype(np.float32)
    # shs = np.concatenate([features_dc.reshape(-1, 3),
    #                     features_extra.reshape(len(features_dc), -1)], axis=-1).astype(np.float32)
    # shs = shs.astype(np.float32)


    shs = features_dc.reshape(-1, 3)

    return GaussianData(xyz, rots, scales, opacities, shs, cov3Ds, num_of_atoms_by_element)

if __name__ == "__main__":
    gs = load_ply("/home/qa43nawu/temp/qa43nawu/out/point_cloud.ply")
    a = gs.flat()
    print(a.shape)
