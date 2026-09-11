import subprocess
import shutil
import uuid

from app.schemas.model import ModelParams
import flopy

class ModelRunError(Exception):
    """MODFLOW 运行失败或不收敛。"""

    def __init__(self, log_tail: str):
        self.log_tail = log_tail
        super().__init__(f"MODFLOW 运行失败:\n{log_tail}")

class ModelTimeoutError(Exception):
    """MODFLOW 运行超过时限。"""

    def __init__(self, timeout: int):
        self.timeout = timeout
        super().__init__(f"MODFLOW 运行超时（超过 {timeout} 秒）")

def build_and_run_model(params: ModelParams):
  sim_ws = f'runs/{uuid.uuid4()}'
  sim = flopy.mf6.MFSimulation(
    sim_name=params.sim_name, 
    sim_ws=sim_ws,
    exe_name="mf6",
    version='mf6'
  )
  tdis = flopy.mf6.ModflowTdis(
    sim,
    time_units="DAYS",
    nper=1,
    perioddata=[(1.0, 1, 1.0)]
  )
  ims = flopy.mf6.ModflowIms(
    sim,
    print_option="SUMMARY",
    complexity="SIMPLE",
  )
  gwf = flopy.mf6.ModflowGwf(
    sim,
    modelname=params.modelname,
    save_flows=True
  )
  dis = flopy.mf6.ModflowGwfdis(
    gwf,
    length_units="METERS",
    nlay=1,
    nrow=params.nrow,
    ncol=params.ncol,
    delr=params.delr,
    delc=params.delc,
    top=1.0,
    botm=0.0
  )
  npf = flopy.mf6.ModflowGwfnpf(
    gwf,
    k=params.k
  )
  ic = flopy.mf6.ModflowGwfic(
    gwf,
    strt=1.0
  )
  chd_spd = []
  for chd_item in params.chds:
    chd_spd.append(((0, chd_item.row, chd_item.col), chd_item.head))
  chd = flopy.mf6.ModflowGwfchd(
    gwf,
    stress_period_data=chd_spd
  )
  wel_spd = []
  for wel_item in params.wells:
    wel_spd.append(((0, wel_item.row, wel_item.col), wel_item.rate))
  if params.wells:
    wel = flopy.mf6.ModflowGwfwel(
      gwf,
      stress_period_data=wel_spd
    )
  oc = flopy.mf6.ModflowGwfoc(
    gwf,
    head_filerecord=f"{params.modelname}.hds",
    saverecord=[("HEAD", "ALL")]
  )
  sim.write_simulation(silent=True)

  # 超时上限 30s 来自 PRD 非功能需求，后续迁入 core/config.py
  RUN_TIMEOUT = 30
  try:
    run_result = subprocess.run(
      ["mf6"],
      cwd=sim_ws,
      capture_output=True,
      text=True,
      timeout=RUN_TIMEOUT,
    )

    if run_result.returncode != 0 or "normal termination" not in run_result.stdout.lower():
      raise ModelRunError(log_tail=run_result.stdout[-800:])

    head_file = flopy.utils.HeadFile(
      filename=sim_ws + f'/{params.modelname}.hds'
    )
    return head_file.get_data()[0].tolist()

  except subprocess.TimeoutExpired:
    raise ModelTimeoutError(RUN_TIMEOUT)

  finally:
    shutil.rmtree(sim_ws, ignore_errors=True)
