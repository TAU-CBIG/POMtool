## Matlab-example
This is an example on how to run Matlab cardiomyocyte model Forouzandehmehr2024.

# Prerequsites
- POMtool (python + other requirements).
- Submodule should be loaded, i.e. you should now have directory `Forouzandehmehr2024-hiPSC-CMs-Model-hiMCES` (hint: git submodule init --recurse)
- MATLAB (by MathWorks)
- optional: `matlab`-command in your path (you should be able to run `matlab -h`, without errors)
- optional: use path to your matlab command e.g `path/to/your/Mathwork/bin/matlab`, instead of `matlab`, also do this change 

Our goal is to run function `run_hiMCES` with different arguments, so we should be able to run following:
`matlab -batch "addpath('Forouzandehmehr2024-hiPSC-CMs-Model-hiMCES'); tic; [val, time] = run_hiMCES(simTime=10, stimFlag=1); toc;"`

If you manage to run this, you should be able to get the elapsed time printed to your stdout. That means things are working.

# Population of models
You can run example config with following:
`../../POMtool.py --config matlab_config.yaml`

The result is generated into directory `_example_matlab_results`.

You can also run in patches. In this example, we just do the heaviest part in patches, running the model (ie. experiment)
`../../POMtool.py --config matlab_config.yaml --patch_count=3 --only-experiment --patch_idx=0`
`../../POMtool.py --config matlab_config.yaml --patch_count=3 --only-experiment --patch_idx=1`
`../../POMtool.py --config matlab_config.yaml --patch_count=3 --only-experiment --patch_idx=2`

These patches can be then merged with:
`../../POMtool.py merge --config matlab_config.yaml --only-experiment --patch_count=3`

Then we continue our running without patches:
`../../POMtool.py --config matlab_config.yaml --skip-experiment --patch_count=3`

# Optimization
We can also optimize parameters instead of creating and calibrating model. 
`../../POMtool.py --config matlab_config.yaml --optimization`
