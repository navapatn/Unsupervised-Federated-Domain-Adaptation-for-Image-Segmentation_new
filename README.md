### Unsupervised Federated Domain Adaptation for Image Segmentation

This repository contains the codes forked from following paper 

 [DeepJDOT](https://arxiv.org/abs/1803.10081)
 [UDA](https://www.frontiersin.org/articles/10.3389/fncom.2020.00019/full)

 and our ensemble methods proposed in our paper

 [UFDA](https://arxiv.org/html/2401.02941v2)

### Prerequisites

* Python3 (3.7.3)
* PyTorch (1.6.0)
* POT (0.7.0)
* Numpy (1.16.4)
* Scipy (1.2.0)
* argparse (1.1)
* os
* CUDA

### Dataset Used
We used MICCAI2016 brain lesion dataset to train DeepJDOT and our ensemble methods. More details on the dataset and access can be found in the following link, paper
* [MICCAI2016] (https://inria.hal.science/hal-03358961/document).
* [shanoir] (https://shanoir.irisa.fr/shanoir-ng/dataset-acquisition/list)

### What is included

* patches_comparison -Deepjdot module contains the implementation of the DeepJDOT
* dnn - import necessary functions from keras
* 3dunet - prebuilt 3d unet model
* training_testing - code for training and testing for MICCAI 2016 and ensemble code
* call.sh, main.py - batch script to automate training and testing process
* create_exp.py - script for creating multiple hyperparameter setups for running experiments.
* config.py - configuration file for custom adjustment of hyperparameters, file path, etc.


