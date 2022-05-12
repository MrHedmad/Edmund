import logging
import os
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path

from edmund.config import CONFIG

__VERSION__ = "0.0.1"

# Save the path to here
ROOT = Path(__file__).parent

# Setup logging
log = logging.getLogger("edmund")  # Keep this at the module level name
log.setLevel(logging.DEBUG)
log.propagate = False
# Keep this at DEBUG - set levels in handlers themselves

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_LOG_PATH = CONFIG["logs"]["path"]

if Path(_LOG_PATH).parent.exists() is False:
    os.makedirs(Path(_LOG_PATH).parent)

file_h = RotatingFileHandler(
    filename=Path(_LOG_PATH),
    encoding="utf-8",
    mode="a+",
    maxBytes=1e5,
    backupCount=5,
)
file_h.setFormatter(formatter)
file_h.setLevel(CONFIG["logs"]["file_level"])
stream_h = StreamHandler()
stream_h.setFormatter(formatter)
stream_h.setLevel(CONFIG["logs"]["stdout_level"])

log.addHandler(file_h)
log.addHandler(stream_h)


import edmund.modules.CHASM.extractCHASMPlus
import edmund.modules.CHASM.retrieve_lymph
import edmund.modules.CHASM.vcf_speed_test

# I do this like this because i cannot find an alternative and I've already
# lost 3 fucking hours on this.
import edmund.modules.data_retrival.dumpClinical
import edmund.modules.data_retrival.get_all_mutations
import edmund.modules.utilities.fuse_csvs
import edmund.modules.utilities.melt_VCF

# import edmund.modules.
