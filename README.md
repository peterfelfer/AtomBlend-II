# A visualization tool for atom probe tomography data using Gaussian Splatting

## Installation

1. Install miniconda: https://docs.anaconda.com/miniconda/
2. Clone the repository (remember to clone the gaussian-splatting branch!):
   ```
   git clone -b gaussian-splatting https://github.com/peterfelfer/AtomBlend-II.git
   ```
3. Create conda environment from file environment.yml in the repository
   ```
   conda env create --file environment.yml
   ```
4. Activate your created enviroment
   ```
   conda activate gaussian-splatting
   ```
5. Install the submodules simple-knn and diff-gaussian-rasterization
   ```
   pip install gaussian_splatting/submodules/diff-gaussian-rasterization/
   ```
   ```
   pip install gaussian_splatting/submodules/simple-knn/
   ```

## Preprocessing
Using preprocessing.py, you can generate .ply files that can later be used as input to the visualizer.
You need either a .pos or .epos and either a .rng or .rrng file to use preprocssing.py, so the --epos_path and --rrng_path parameters are required.

```
python preprocessing.py --epos_path path/to/your/position/file.(e)pos --rrng_path path/to/your/range/file.(r)rng
```

Also, some more parameters can be adjusted. Run `python preprocessing.py -h` to see the possible arguments.

For example, you can execute the following command to get a .ply with 10 million atoms, a maximum neighbors distance in PCA of 10 and file name test_file.ply:

```
python preprocessing.py --epos_path your_file.(e)pos --rrng_path your_file.(r)rng --num_neighbors 10000000 --max_distance 10 --out_file_name test_file.ply
```

`preprocessing.py` will produce a .ply file that can be used as an input to the visualizer.

## Visualizer
You can start the visualizer using this command:

```
python gspy_viewer/main.py
```

The visualizer will load a small dummy scene per default.
You can load your own file by clicking `open .ply` in the Control window. 
The control and atom settings window also contains some settings to adjust your rendering.
