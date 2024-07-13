### Module presets
`module save|restore` to save/restore preset of modules
`module use|unuse` to control module repositories (HILE will have different subset of modules for example): https://version.helsinki.fi/it-for-science/hpc/-/wikis/3.0-Software-Module-User-Guide

### Write dependencies in LMOD
If you have a package X that depends on A, in the .lua file for X add `depends_on("A")`: https://lmod.readthedocs.io/en/latest/098_dependent_modules.html

### Install python and libraries on LUMI
It's very easy to use pytorch or tensorflow on lumi if you only need these specific packages and nothing else. CSC provides some already-built containers for this purpose: https://docs.lumi-supercomputer.eu/software/local/csc/. Also maybe it's possible to use those if you also need a few more packages with those containers. (This is described in the next paragraph)

If you have an already built container but want a few more packages, you can use an existing container with a pip virtual environment: https://docs.lumi-supercomputer.eu/software/installing/python/#use-an-existing-container-with-a-pip-virtual-environment

If you want to manage multiple packages, then it's better to use lumi-container-wrapper to wrap your conda env file or smth like that. It's also very easy: https://docs.lumi-supercomputer.eu/software/installing/python/#use-the-lumi-container-wrapper
