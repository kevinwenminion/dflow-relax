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

from dpgen.auto_test.common_equi import (make_equi, post_equi)
from dflow.python import upload_packages

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
            'njobs': int,
            'jobs': Artifact(List[Path])
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
        for ii in conf_dirs:
            relaxation = os.path.join(ii, 'relaxation')
            relax_task = os.path.join(relaxation, 'relax_task')
            task_list.append(relax_task)

            # shutil.copytree(relaxtaion, 'relaxation')

        all_jobs = task_list
        njobs = len(all_jobs)
        jobs = []
        for job in all_jobs:
            jobs.append(pathlib.Path(job))

        os.chdir(cwd)
        op_out = OPIO({
            "output": op_in["input"],
            "njobs": njobs,
            "jobs": jobs
        })
        return op_out


class VASP(OP):
    """
    class for VASP calculation
    """

    def __init__(self, infomode=1):
        self.infomode = infomode

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            'input_relax': Artifact(Path),
            'run_command': str
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({
            'output_relax': Artifact(Path, sub_path=False)
        })

    @OP.exec_sign_check
    def execute(self, op_in: OPIO) -> OPIO:
        cwd = os.getcwd()
        os.chdir(op_in["input_relax"])
        cmd = op_in["run_command"]
        subprocess.call(cmd, shell=True)
        os.chdir(cwd)
        op_out = OPIO({
            "output_relax": op_in["input_relax"]
        })
        return op_out


class RelaxPostVASP(OP):
    """
    class for analyse calculation results
    """

    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            'input_post': Artifact(Path),
            'path': str
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({
            'output_post': Artifact(Path)
        })

    @OP.exec_sign_check
    def execute(self, op_in: OPIO) -> OPIO:
        os.chdir(op_in["input_post"])
        cwd = os.getcwd()

        post_equi(loadfn("param.json")["structures"], loadfn("param.json")["interaction"])
        os.chdir(cwd)

        op_out = OPIO({
            "output_post": op_in["input_post"]
        })
        return op_out
