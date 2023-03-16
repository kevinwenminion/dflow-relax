from typing import List
from dflow import (
    Workflow,
    Step,
    argo_range,
    SlurmRemoteExecutor,
    upload_artifact,
    download_artifact,
    InputArtifact,
    OutputArtifact,
    ShellOPTemplate
)
from dflow.python import (
    PythonOPTemplate,
    OP,
    OPIO,
    OPIOSign,
    Artifact,
    Slices,
    upload_packages
)
import time

import subprocess, os, shutil, glob, dpdata, pathlib
from pathlib import Path
from typing import List
from dflow.plugins.bohrium import BohriumContext, BohriumExecutor
from dpdata.periodic_table import Element
from monty.serialization import loadfn

try:
    from dpgen.auto_test.common_equi import (make_equi, post_equi)
except:
    pass

from dflow.python import upload_packages

import shutil
upload_packages.append(__file__)


class RelaxMakeVASP(OP):
    """
    class for making calculation tasks
    """

    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            'input': Artifact(Path)
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({
            'output': Artifact(Path),
            'task_names': List[str],
            'task_paths': Artifact(List[Path])
        })

    @OP.exec_sign_check
    def execute(
            self,
            op_in: OPIO,
    ) -> OPIO:
        cwd = os.getcwd()

        os.chdir(op_in["input"])
        work_d = os.getcwd()

        structures = loadfn("param.json")["structures"]
        inter_parameter = loadfn("param.json")["interaction"]
        parameter = loadfn("param.json")["relaxation"]

        make_equi(structures, inter_parameter, parameter)

        conf_dirs = []
        for conf in structures:
            conf_dirs.extend(glob.glob(conf))
        conf_dirs.sort()

        task_list = []
        task_list_str = []
        for ii in conf_dirs:
            relaxation = os.path.join(ii, 'relaxation')
            task_list_str.append(relaxation)
            relax_task = os.path.join(relaxation, 'relax_task')
            task_list.append(os.path.join(work_d, relax_task))

        all_jobs = task_list
        jobs = []
        for job in all_jobs:
            jobs.append(pathlib.Path(job))

        os.chdir(cwd)
        op_out = OPIO({
            "output": op_in["input"],
            "task_names": task_list_str,
            "task_paths": jobs
        })
        return op_out


class RelaxPostVASP(OP):
    """
    class for analyzing calculation results
    """

    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            'input_post': Artifact(Path, sub_path=False),
            'input_param': Artifact(Path, sub_path=False)
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({
            'output_post': Artifact(Path, sub_path=False)
        })

    @OP.exec_sign_check
    def execute(self, op_in: OPIO) -> OPIO:
        os.chdir(str(op_in['input_post']))
        shutil.copytree(str(op_in['input_param']), './', dirs_exist_ok=True)

        post_equi(loadfn("param.json")["structures"], loadfn("param.json")["interaction"])

        op_out = OPIO({
            'output_post': op_in["input_post"]
        })
        return op_out
