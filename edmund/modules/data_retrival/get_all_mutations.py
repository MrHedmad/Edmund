import gzip
from io import StringIO

import click
import pandas as pd
import requests
from tqdm import tqdm

from edmund.entrypoint import cli

all_tcga_ids = [
    "LAML",
    "ACC",
    "BLCA",
    "LGG",
    "BRCA",
    "CESC",
    "CHOL",
    "COAD",
    "ESCA",
    "GBM",
    "HNSC",
    "KICH",
    "KIRC",
    "KIRP",
    "LIHC",
    "LUAD",
    "LUSC",
    "DLBC",
    "MESO",
    "OV",
    "PAAD",
    "PCPG",
    "PRAD",
    "READ",
    "SARC",
    "SKCM",
    "STAD",
    "TGCT",
    "THYM",
    "THCA",
    "UCS",
    "UCEC",
    "UVM",
]

all_data = []
endpoint = (
    "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-{}.mutect2_snv.tsv.gz"
)


@cli.command()
@click.argument("output_file", type=str)
def get_all_mutdata(output_file):
    """Retrieve a big file with all mutations from the TCGA project, complete
    with which tumor type they came from.

    Uses a terrible manual endpoint.
    """
    for id in tqdm(all_tcga_ids):
        final_endpoint = endpoint.format(id)
        try:
            data = requests.get(final_endpoint)
        except Exception as e:
            print(f"Got an error: {e} while processing {id}")
            continue

        data = gzip.decompress(data.content).decode("UTF-8")
        data = pd.read_csv(StringIO(data))
        data["tumor_type"] = f"TCGA-{id}"
        all_data.append(data)

    print("Saving data...")
    pd.concat(all_data).to_csv(output_file)
