"""This module holds the stuff to run a GSEA analysis on the output of a
bioTEA run.

Find bioTEA here: https://github.com/CMA-Lab/bioTEA

It:
    - Takes in the output DEG Tables, and reads them to memory;
    - Generates the necessary .rnk file(s) with the pre-ranked genes;
    - Stages new folders as is necessary;
    - Runs the GSEA analysis;
    - Saves the output plots and data (namely the GSEA scores);

This is designed with the following in mind:
- Make a folder with a unique name (e.g. Zhang);
- Retrieve the data in the folder;
- Generate the options file in the folder;
- Prep the data in the same folder;
- Run the analysis in the same folder, making the DEG table a child of "Zhang/".
- Repeat for all projects.
- Run this command on the parent folder with all the (uniquely named) children.
"""

import logging
import os
import re
from multiprocessing import cpu_count
from pathlib import Path

import click
import gseapy as gsea
import pandas as pd
from matplotlib import table

from edmund.entrypoint import cli

log = logging.getLogger(__name__)


def find_deg_tables(
    target: Path, pattern: str = "(.*?) - DEG Table (.*?).csv", recursive: bool = False
) -> dict:
    """Find all DEG tables in a target folder

    Actually matches all files with a pattern, by default looking for DEG
    tables as generated by bioTEA.

    Reads them into a list of pd.DataFrames.

    Args:
        target (Path): The target folder to search in.
        patters (str): A RegEx string to match filenames with.
        recursive (bool): Should the function look into folders recursively? Defaults to False.

    Returns:
        dict: A dict of Path: DataFrame with the output dataframes and their original paths.
    """
    target = target.expanduser().resolve()

    if not target.is_dir():
        raise ValueError(f"Target {target} is not a dir.")

    cpattern = re.compile(pattern)

    found_files = {}
    for file in target.iterdir():
        if file.is_dir() and recursive:
            log.info(f"Looking in {file}...")
            res = find_deg_tables(target=file, pattern=pattern, recursive=True)
            found_files.update(res)
            continue

        match = cpattern.match(file.name)
        if match:
            log.info(f"Found a matching file: {file}")
            new_name = (
                f"{file.parent.parent.name}_{match.groups()[0]}_{match.groups()[1]}"
            )
            found_files[new_name] = file

    log.info(f"Found {len(found_files)} matching files.")

    tables = {}
    for name, file in found_files.items():
        try:
            tables[name] = pd.read_csv(file, header=0)
            log.info(",".join(tables[name].columns))
        # PANDAS DOES NOT EXPOSE ERRORS. Fuck me, right?
        except Exception as e:
            if e is KeyboardInterrupt:
                raise
            log.error(f"Got an error while trying to parse {file}: {e}. Ignoring it.")
            continue

    if tables == {}:
        log.warn("Returning an empty dataset.")

    return tables


def make_rank_df(deg_table: pd.DataFrame, score_statistic: str = "t") -> pd.DataFrame:
    """Make a .rnk file from a dataframe, looking at a single statistic.

    Args:
        deg_table (pd.DataFrame): The table to sort. Has to have a "probe_id" col with rownames.
        score_statistic (str, optional): The score statistic to use. Defaults to "t".

    Returns:
        The subsetted pandas dataframe.
    """
    if score_statistic not in deg_table.columns:
        raise ValueError(
            f"The target statistic ({score_statistic}) cannot be found in the table."
        )

    if "probe_id" not in deg_table.columns:
        raise ValueError(f"Cannot find the probe_id column in the table.")

    subset = deg_table[["SYMBOL", score_statistic]]
    subset.sort_values(by=[score_statistic], inplace=True)

    log.info("Dropping NA values...")
    subset.dropna(inplace=True)

    log.info("Removing duplicate genes...")
    subset.drop_duplicates(subset="SYMBOL", keep="first", inplace=True)

    return subset


def run_gsea(
    target_path: Path,
    output_path: Path,
    target_gsea_sets: Path | str,
    score_statistic: str = "t",
    save_rnk: bool = True,
    recursive_search: bool = False,
    overwrite: bool = False,
):
    output_path = output_path.expanduser().absolute()
    tables = find_deg_tables(target_path, recursive=recursive_search)
    results = {}
    if not output_path.exists():
        os.makedirs(output_path)
        log.info(f"Made {output_path}")

    for name, table in tables.items():
        log.info(f"Processing {name}...")
        try:
            rnk = make_rank_df(table, score_statistic)
        except ValueError:
            log.error(f"Cannot make a .rnk file with {name}. Skipping it.")
            continue

        if save_rnk:
            outfile = output_path / f"{name}.rnk"
            if outfile.exists() and overwrite is False:
                raise ValueError(
                    f"File {outfile} already exists, and overwrite is False."
                )
            with outfile.open("w+") as outstream:
                rnk.to_csv(outstream)

        log.info("Launching GSEA.")
        gsea_out_dir = output_path / f"GSEA_{name}"
        if not gsea_out_dir.exists():
            os.makedirs(gsea_out_dir)
            log.info(f"Made {gsea_out_dir}")

        result = gsea.prerank(
            rnk,
            gene_sets=target_gsea_sets,
            outdir=str(gsea_out_dir),
            processes=cpu_count(),
            verbose=True,
        )
        log.info("GSEA done.")
        results[name] = pd.DataFrame.from_dict(results)

        all_res = pd.concat(list(results.values()), ignore_index=True)
        all_res.set_index(list(results.keys()))
        all_res.to_csv(output_path / "All_GSEA_results.csv")

    log.info("Done.")


@cli.command(name="gsea")
@click.argument(
    "target_path",
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
)
@click.argument(
    "output_path", type=click.Path(file_okay=False, writable=True, path_type=Path)
)
@click.argument("target_gsea_sets")
@click.option("--score-statistic", default="t")
@click.option("--save-rnk/--no-save-rnk", default=True)
@click.option("--recursive-search/--no-recursive-search", default=True)
@click.option("--overwrite/--no-overwrite", default=False)
def run_gsea_command(*args, **kwargs):
    run_gsea(*args, **kwargs)
