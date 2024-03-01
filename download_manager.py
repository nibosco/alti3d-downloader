import requests
import random
import time
import csv
import logging
from pathlib import Path
import subprocess
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def download_file(url, download_path):
    try:
        response = requests.get(url)
        if response.status_code ==   200:
            with open(download_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"File downloaded successfully to: {download_path}")
            return True
        else:
            logging.error("Failed to download the file.")
            return False
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return False

def merge_and_convert(raw_folder_path, output_folder_path):
    # List all GeoTIFF files in the 'raw' folder
    geotiff_files = list(raw_folder_path.glob('*.tif'))
    merge_inputs = ' '.join([str(f) for f in geotiff_files])
    
    # Define the output file for the merge operation
    merged_geotiff = output_folder_path / f'{output_folder_path.stem}_merged.tif'
    
    # Merge all GeoTIFF files into a single file
    merge_command = f'gdal_merge.py -o {merged_geotiff} {merge_inputs}'
    logging.info("Starting to merge all GeoTIFFs ...")
    subprocess.run(merge_command, shell=True, check=True)
    logging.info(f"Merged all geotiffs into: {merged_geotiff}")
    
    #Convert geotiff to ASCII XYZ
    convert_to_xyz = os.getenv('CONVERT_TO_XYZ', 'True').lower() == 'true'
    if convert_to_xyz:
        merged_xyz = output_folder_path / f'{output_folder_path.stem}_merged.xyz'
        xyz_command = f'gdal_translate -of XYZ -a_srs EPSG:2056 -co "DECIMAL_PRECISION=2" {merged_geotiff} {merged_xyz}'
        logging.info("Starting to convert merged GeoTIFF ...")
        subprocess.run(xyz_command, shell=True, check=True)
        logging.info(f"Converted merged GeoTIFF in to ASCII XYZ: {merged_xyz}")
    else:
        logging.info("Conversion to ASCII xyz skipped due to user setting in .env")

def process_csv(filename):
    folder_name = Path(filename).stem
    folder_path = Path.cwd() / folder_name
    raw_folder_path = folder_path / 'raw'
    raw_folder_path.mkdir(parents=True, exist_ok=True)
    
    remaining_file = folder_path / f"{folder_name}_remaining.csv"
    if remaining_file.exists():
        with open(remaining_file, "r") as file:
            urls = list(csv.reader(file, delimiter=","))
    else:
        with open(filename, "r") as file:
            urls = list(csv.reader(file, delimiter=","))
    
    while urls:
        url = random.choice(urls)
        download_filename = Path(url[0]).name
        download_filepath = raw_folder_path / download_filename
        
        # Attempt to download the file
        success = download_file(url[0], download_filepath)
        if success:
            # If download is successful, remove the URL from the list and update the remaining.csv file
            urls.remove(url)
            with open(remaining_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(urls)
        else:
            # If download fails, do not remove the URL from the list
            logging.error(f"Failed to download {url[0]}. Retrying...")
        
        time.sleep(random.randint(1,5))
    
    # Check if there are no remaining URLs, then delete the original and remaining CSV files
    if not urls:
        try:
            Path.unlink(filename)
            Path.unlink(remaining_file)
            logging.info(f"Deleted original and remaining CSV files for {folder_name}")
        except FileNotFoundError:
            logging.error(f"Files not found for deletion: {filename}, {remaining_file}")
    #Post-processsing of downloaded data
    merge_and_convert(raw_folder_path, folder_path)

def monitor_directory(input_dir):
    input_dir_path = Path(input_dir)
    logging.info(f"Monitoring directory: {input_dir_path}")
    while True:
        if input_dir_path.exists():
            for filename in input_dir_path.iterdir():
                if filename.suffix == '.csv':
                    process_csv(filename)
                    logging.info(f"Processed: {filename.name}")
                #else:
                    #logging.info('No csv-files in input directory')
        else:
            logging.info("No files in input folder")
        time.sleep(5)


def main():
    # Assuming using the folder structure with /input as the monitored dir
    monitor_directory("input")

if __name__ == "__main__":
    main()
