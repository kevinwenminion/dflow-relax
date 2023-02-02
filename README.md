# dflow-relax
## Relaxation with VASP, ABACUS, and LAMMPS in autotest.
This workflow is a part of [AI Square](https://aissquare.com/). We want to refactor the autotest code based on dflow. 
This is "relaxation" (structure optimization) using VASP, LAMMPS, or ABACUS.

## Easy Install：
```
pip install "git+https://github.com/kevinwenminion/dflow-relax.git"
```

## Quick Start
You can go to the `example` folder and there are some examples for reference. You can go to one of them and fill in the `global.json` file. Then you can submit the workflow.

If you want to use VASP code to do the DFT relaxation, like the folder `vasp_demo`. You need to prepare `INCAR`, `POSCAR`, `POTCAR`, `global.json` and `param.json`, then ：
``` 
dflowrelax --vasp
```

If you want to use ABACUS code, like the folder `abacus_demo`. You need to prepare `INPUT`, `STRU`, `*.UPF`, `global.json` and `param.json` (notice that `*.orb` and `KPT` are optional ), then：
```
dflowrelax --abacus
```

If you want to use LAMMPS to do MD calculation, like the folder `dp_demo`. You need to prepare `POSCAR`, `frozen_model.pb`, `global.json` and `param.json`, then:
```
dflowrelax --lammps
```

You can monitor the workflow process on the [website](https://workflows.deepmodeling.com).

