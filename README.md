# POM tool

## Description
This is CLI-tool to create population of model and calibrate your model. It can calculate biomarkers, and calibrate either your model or your population based on those parameters.

## Using
Currently, just clone the repository and run:
```
./POMTool.py run --config my_config.yaml
```
Use -h to get help-file for the CLI.

Every config should describe model. This section describes how model you are interested can be run and how to input parameters to it.

You have two options what to do with model, you can run POM-experiment (experiment), or model optimization (optimization).

In POM-experiment first model is run for each set of parameters as described in `experiment`. After that `biomarkers` are calculated. With biomarkers, we can calibrate our population based on protocols described in `calibration`.

In optimization, parameters are changed with goal to match biomarkers given as arguments. Biomarkers are calculated as given in `biomarkers` and `optimization` describes optimization process.

To create your own config, check examples directory. All examples there are runnable (at moment of writing, only one example). 

## Future
* More ways to use the tool will be made available as the project progresses
* This documentation will be made better
* More examples will be provided, and some example projects will be made public for best practices
* Some thoughts can also be found from roadmap

## Acknowledgements
Initial production of this tool was partly funded by [SMASH-HCM](https://smash-hcm.eu/), which is funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Education and Culture Executive Agency (EACEA). Neither the European Union nor EACEA can be held responsible for them.

## Authors
Ossi Noita - Original concept and current maintainer
Olli Ylinen - Major contributions to optimization, biomarkers, and testing
