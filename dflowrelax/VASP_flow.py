import json, pathlib
from typing import List
from dflow import (
    Workflow,
    Step,
    argo_range,
    argo_len,
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
import subprocess, os, shutil, glob
from pathlib import Path
from typing import List
from dflow.plugins.dispatcher import DispatcherExecutor
from monty.serialization import loadfn
from monty.serialization import loadfn
from dflow.python import upload_packages

upload_packages.append(__file__)
from dflowrelax.VASP_OPs import RelaxMakeVASP, RelaxPostVASP

from fpop.vasp import PrepVasp, VaspInputs, RunVasp
from fpop.utils.step_config import (
    init_executor
)

def main_vasp():
    global_param = loadfn("global.json")
    work_dir = global_param.get("work_dir", None)
    email = global_param.get("email", None)
    password = global_param.get("password", None)
    program_id = global_param.get("program_id", None)
    dpgen_image_name = global_param.get("dpgen_image_name", None)
    vasp_image_name = global_param.get("vasp_image_name", None)
    abacus_image_name = global_param.get("abacus_image_name", None)
    cpu_scass_type = global_param.get("cpu_scass_type", None)
    gpu_scass_type = global_param.get("gpu_scass_type", None)
    vasp_run_command = global_param.get("vasp_run_command", None)
    upload_python_packages = global_param.get("upload_python_packages", None)

    run_step_config = {
        "executor": {
            "type": "dispatcher",
            "machine_dict": {
                "batch_type": "Bohrium",
                "context_type": "Bohrium",
                "remote_profile": {
                    "email": email,
                    "password": password,
                    "program_id": program_id,
                    "input_data": {
                        "job_type": "container",
                        "platform": "ali",
                        "scass_type": cpu_scass_type,
                    }
                }
            }
        }
    }

    cwd = os.getcwd()
    work_dir = cwd
    wf = Workflow(name="relax")

    relaxmake = Step(
        name="Relaxmake",
        template=PythonOPTemplate(RelaxMakeVASP, image=dpgen_image_name, command=["python3"]),
        artifacts={"input": upload_artifact(work_dir)},
    )
    wf.add(relaxmake)


    vasp_cal = Step(name="VASP-Cal", template=PythonOPTemplate(RunVasp,
                slices=Slices(
                "{{item}}",
                input_parameter=["task_name"],
                input_artifact=["task_path"],
                output_artifact=["backward_dir"]
                ),
                python_packages=upload_python_packages,
                image=vasp_image_name
                ),
                parameters={
                    "run_image_config": {"command": vasp_run_command},
                    "task_name": relaxmake.outputs.parameters["task_names"],
                    "backward_list": ["INCAR", "POSCAR", "OUTCAR", "CONTCAR"],
                    "backward_dir_name": "relax_task"
                },
                artifacts={
                    "task_path": relaxmake.outputs.artifacts["task_paths"]
                },
                with_param=argo_range(argo_len(relaxmake.outputs.parameters["task_names"])),
                key="VASP-Cal-{{item}}",
                executor=init_executor(run_step_config.pop("executor")),
                **run_step_config
                )

    wf.add(vasp_cal)

    relaxpost = Step(
        name="Relaxpost",
        template=PythonOPTemplate(RelaxPostVASP, image=dpgen_image_name, command=["python3"]),
        artifacts={"input_post": vasp_cal.outputs.artifacts["backward_dir"], "input_param": upload_artifact('./param.json')}
    )
    wf.add(relaxpost)

    wf.submit()

    while wf.query_status() in ["Pending", "Running"]:
        time.sleep(4)
    assert (wf.query_status() == 'Succeeded')
    step = wf.query_step(name="Relaxpost")[0]
    download_artifact(step.outputs.artifacts["output_post"])