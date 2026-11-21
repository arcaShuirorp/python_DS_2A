import os
from pathlib import Path
import requests             # Télécharger depuis IMDB
import pandas as pd
from tqdm import tqdm       # Afficher barre de progression

import pyarrow as pa
import pyarrow.parquet as pq
import csv

# === Configuration 

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

BASE_URL = "https://datasets.imdbws.com/"  # On télécharge les fichiers depuis cet URL

FILES = [
    "title.basics.tsv.gz",
    "title.ratings.tsv.gz",
    "title.crew.tsv.gz",
    "title.principals.tsv.gz"
]

chunk_size = 200_000  # Permet de pas convertir d'un coup mais bout par bout pour éviter de tuer la ram
TIMEOUT = 60


# === Téléchargement

def download_file(filename):
    """
    Télécharge un fichier IMDb .tsv.gz, le sauvegarde dans le dossier data.
    """

    print(f"\nTéléchargement de {filename}...")

    response = requests.get(BASE_URL + filename, stream=True, timeout=TIMEOUT)
    total_size = int(response.headers.get("content-length", 0))

    with open(OUTPUT_DIR / filename, "wb") as file, tqdm(
        total=total_size, unit="B", unit_scale=True, desc=filename
    ) as progress:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)
            progress.update(len(chunk))

    print(f"Téléchargement terminé : {filename}")



# === Lecture des .gz convertion en parquet 


def convert_to_parquet(filename):

    input_path = OUTPUT_DIR / filename

    output_name = filename.replace(".tsv.gz", ".parquet")
    output_path = OUTPUT_DIR / output_name

    print(f"\nConversion de {filename}...")

    reader = pd.read_csv(
        input_path,
        sep="\t",
        chunksize=chunk_size,
        dtype="string",
        na_values="\\N",
        quoting=csv.QUOTE_NONE
    )                       # Le fichier en format dataframe qu'on va convertir en parquet

    writer = None
    total_rows = 0

    for chunk in tqdm(reader, desc=output_name):  # Chunk est un bout de reader de taille chunk_size

        table = pa.Table.from_pandas(
            chunk,
            preserve_index=False # Pas besoin de conserver l'index panda car il existe sur IMDB
        )

        if writer is None:
            writer = pq.ParquetWriter(
                output_path,
                table.schema,
                compression="snappy" # Compromis taille de fichier vitesse
            )

        writer.write_table(table)
        total_rows += len(chunk)

    print(f"{total_rows:,} lignes sauvegardées dans {output_name}")


def main():

    for filename in FILES:

        # Téléchargement
        download_file(filename)

        # Conversion
        convert_to_parquet(filename)

    print("\n" + "=" * 50)
    print("Tous les fichiers IMDb ont été récupérés !")
    print("=" * 50)


if __name__ == "__main__":
    main()
