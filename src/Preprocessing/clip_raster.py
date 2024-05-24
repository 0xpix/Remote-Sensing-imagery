import os
import subprocess
import argparse
import fnmatch
from osgeo import gdal
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), r"C:\Users\nschl\Documents\AIMS_MSc_Project_CERI\GitHub\CERI-Project\src\data"))
from country_code import country_code_dict  # Import the country code dictionary

def clip_raster_with_shapefile(raster_path, shapefile_path, output_path, time_period, country):
    # Use GDAL warp to clip the raster and capture the output
    process = subprocess.run([
        'gdalwarp',
        '-cutline', shapefile_path,
        '-crop_to_cutline',
        '-dstalpha',
        raster_path,
        output_path
    ], capture_output=True, text=True, check=True)
    
    # Modify and print the GDAL output
    for line in process.stdout.splitlines():
        if "Creating output file" in line:
            print(f"{time_period.capitalize()} - {country}: {line}")
        elif "Processing" in line and "[1/1]" in line:
            print(f"{time_period.capitalize()} - {country}: done\n")
        else:
            print(line)

def find_shapefiles(directory, pattern="gadm41_*_1.shp"):
    shapefiles = []
    for root, _, files in os.walk(directory):
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                shapefiles.append(os.path.join(root, file))
    return shapefiles

def find_input_file(input_dir, year):
    pattern = f"LULC_{year}_lccs_class.tiff"
    input_file = os.path.join(input_dir, pattern)
    if os.path.exists(input_file):
        return input_file
    return None

def main(input_directory, shapefile_directory, output_directory, disaster_dict_file):
    # Load the disaster dictionary from the JSON file
    with open(disaster_dict_file, 'r') as f:
        disaster_dict = json.load(f)
    
    # Reverse the country_code_dict to map country names to codes
    name_to_code_dict = {v: k for k, v in country_code_dict.items()}
    
    # Find all shapefiles
    shapefiles = find_shapefiles(shapefile_directory)
    
    if not shapefiles:
        print("No shapefiles found matching the pattern.")
        return
    
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    for year in disaster_dict:
        print(f"\n\n====================================")
        print(f"Processing year: {year}")
        print(f"====================================")
        for country in disaster_dict[year]:
            # Get the country code from the reversed dictionary
            country_code = name_to_code_dict.get(country)
            if not country_code:
                print(f"No country code found for country: {country}")
                continue
            
            shapefile_pattern = f"gadm41_{country_code}_1.shp"
            country_shapefiles = [s for s in shapefiles if fnmatch.fnmatch(os.path.basename(s), shapefile_pattern)]
            
            if not country_shapefiles:
                print(f"No shapefiles found for country: {country} with code: {country_code}")
                continue
            print("\n==================================================")
            print(f"Processing year: {year}, country: {country} ({country_code})")
            print("==================================================")
            for offset, time_period in zip([-1, 0, 1], ['the year before disaster', 'the year of disaster', 'the year after disaster']):
                target_year = int(year) + offset
                raster_path = find_input_file(input_directory, target_year)
                
                if not raster_path:
                    print(f"  No raster file found for year {target_year}.")
                    continue
                
                raster_name = os.path.splitext(os.path.basename(raster_path))[0]
                year_output_directory = os.path.join(output_directory, str(year))
                os.makedirs(year_output_directory, exist_ok=True)
                
                for shapefile in country_shapefiles:
                    output_path = os.path.join(year_output_directory, f'{country}_{raster_name}_{time_period.replace(" ", "_")}.tif')
                    
                    print("==================================================")
                    print(f"Clipping raster for {country} for {time_period} ...")
                    
                    clip_raster_with_shapefile(raster_path, shapefile, output_path, time_period, country)
                    
                    print(f"  Saved clipped raster for {time_period}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clip rasters by shapefiles')
    parser.add_argument('--input', type=str, required=True, help='Directory containing raster files')
    parser.add_argument('--shapefiles', type=str, required=True, help='Directory containing shapefiles')
    parser.add_argument('--output', type=str, required=True, help='Directory to save clipped rasters')
    parser.add_argument('--disaster_dict', type=str, required=True, help='Path to the JSON file representing the disaster dictionary')

    args = parser.parse_args()
    
    main(args.input, args.shapefiles, args.output, args.disaster_dict)