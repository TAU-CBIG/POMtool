# POM tool

## Description
This is commpand line interface (CLI) tool to create population of model and calibrate your model. It can calculate biomarkers, and calibrate either your model or your population based on those parameters.

## Installation
There are few options how to start using POMtool.

### pipx
Using pipx you can download package and install it as command line interface. In addition, it is recommended to set your version
```
pipx install "POMtool~=100.0"
```
However, typically you do not have correct python version. as your default.

POMtool version 100.0 requires python 3.11, so using python, so you would need to use 
```
pipx install --python <path/to/correct/python> "POMtool~=100.0"
```

For example, if you have python3.11 installed, you can use
```
pipx install --python python3.11 "POMtool~=100.0"
```
For pyenv installation, point to correct shim
```
pipx install --python ~/.pyenv/versions/3.11.11/bin/python "POMtool~=100.0"
```

### Clone
Clone the repository and run inside the repository:
```
./POMtool.py run --help
```

To follow other examples, create alias for `POMtool`, or keep using `./POMtool.py` directly. For example with:
```
./POMtool.py run --help && alias POMtool="python $(pwd)/POMtool.py"
```

### pip
Using pip is also possible. Just create virtual environment with correct python version. For most use cases, you should use `pipx` instead.

## Using
Use -h to get help-file for the CLI. Currently, this is only tested on python, newer python version might not work.

Every config should describe model. This section describes how model you are interested can be run and how to input parameters to it.

You have two options what to do with model, you can run POM-experiment (experiment), or model optimization (optimization).

In POM-experiment first model is run for each set of parameters as described in `experiment`. After that `biomarkers` are calculated. With biomarkers, we can calibrate our population based on protocols described in `calibration`.

In optimization, parameters are changed with goal to match biomarkers given as arguments. Biomarkers are calculated as given in `biomarkers` and `optimization` describes optimization process.

To create your own config, check examples directory. All examples there are runnable (at moment of writing, only one example). 

## Future
* More ways to use the tool will be made available as the project progresses
* Improvements to this document are added, as issues arise
* More examples will be provided, and some example projects will be made public for best practices
* Some thoughts can also be found from roadmap

## Acknowledgements
Initial production of this tool was partly funded by [SMASH-HCM](https://smash-hcm.eu/), which is funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Education and Culture Executive Agency (EACEA). Neither the European Union nor EACEA can be held responsible for them.

## Authors
Ossi Noita - Original concept and current maintainer
Olli Ylinen - Major contributions to optimization, biomarkers, and testing
