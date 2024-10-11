import numpy as np
from plyfile import PlyData
from dataclasses import dataclass
import dpg_plotting

@dataclass
class GaussianData:
    xyz: np.ndarray
    rot: np.ndarray
    scale: np.ndarray
    opacity: np.ndarray
    sh: np.ndarray
    cov3D: np.ndarray
    num_of_atoms_by_element: dict
    g_volume: np.ndarray
    g_distance: np.ndarray
    indices: np.ndarray

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
            'is_rendered': True,
        },
    }
    gau_cov3D = np.array([
        [1, 0, 0, 1, 0, 1],
        [1, 0, 0, 1, 0, 1],
        [1, 0, 0, 1, 0, 1],
    ]).astype(np.float32).reshape(-1, 3)

    gau_g_volume = np.array([1, 1, 1])
    gau_distance_opacity = np.array([1, 1, 1])

    gau_indices = np.array([[1], [1], [1], [1]])

    return GaussianData(
        gau_xyz,
        gau_rot,
        gau_s,
        gau_a,
        gau_c,
        gau_cov3D,
        gau_num_of_atoms_by_element,
        gau_g_volume,
        gau_distance_opacity,
        gau_indices
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
                    'scale': 0.001,
                    'is_rendered': True,
                }

                num_of_atoms_by_element[element_name.split(' ')[1]] = obj

        if line.startswith('property'):
            break

    xyz = np.stack((np.asarray(plydata.elements[0]["x"]),
                    np.asarray(plydata.elements[0]["y"]),
                    np.asarray(plydata.elements[0]["z"])),  axis=1)

    cov3D_names = [p.name for p in plydata.elements[0].properties if p.name.startswith("cov3D")]
    cov3D_names = sorted(cov3D_names, key = lambda x: int(x.split('_')[-1]))
    cov3Ds = np.zeros((xyz.shape[0], len(cov3D_names)))
    for idx, attr_name in enumerate(cov3D_names):
        cov3Ds[:, idx] = np.asarray(plydata.elements[0][attr_name])

    g_volume = np.ones((xyz.shape[0], 1))
    g_volume[:, 0] = np.asarray(plydata.elements[0]["g_volume"])

    g_distance = np.ones((xyz.shape[0], 1))
    g_distance[:, 0] = np.asarray(plydata.elements[0]["g_distance"])

    indices = np.zeros((xyz.shape[0], 1))
    indices[:, 0] = np.asarray(plydata.elements[0]["indices"])

    # pass activate function
    xyz = xyz.astype(np.float32)
    rots = np.array([])
    scales = np.array([])
    opacities = np.array([])
    g_volume = g_volume.astype(np.float32)
    g_distance = g_distance.astype(np.float32)
    indices = indices.astype(np.float32)
    shs = np.array([])

    # plotting settings
    dpg_plotting.plotting_data["volume_min_max"] = [0.0, g_volume.max()]
    # dpg_plotting.plotting_data["volume_alpha_range"] = [0.0, g_volume.max()]

    return GaussianData(xyz, rots, scales, opacities, shs, cov3Ds, num_of_atoms_by_element, g_volume, g_distance, indices)

if __name__ == "__main__":
    gs = load_ply("/home/qa43nawu/temp/qa43nawu/out/point_cloud.ply")
    a = gs.flat()
    print(a.shape)
