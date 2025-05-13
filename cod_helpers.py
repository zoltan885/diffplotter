# -*- coding: utf-8 -*-

import requests
import logging
import numpy as np

def search_cif(**kwargs):
    """
    Searches the Crystallography Open Database (COD) for crystallographic information files (CIFs)
    based on the provided search criteria.
    Parameters:
        formula (str, optional): The chemical formula to search for.
        elements (list of str, optional): A list of elements that must be present in the structure.
        notelements (list of str, optional): A list of elements that must not be present in the structure.
        minelements (int, optional): The minimum number of elements in the structure.
        maxelements (int, optional): The maximum number of elements in the structure.
    Returns:
        list: A list of search results, where each result is a dictionary containing information
              about a matching CIF entry. Returns an empty list if no results are found or if an error occurs.
    Notes:
        - The function sends a GET request to the COD API with the specified search parameters.
        - If the request fails, an error message is printed, and an empty list is returned.
    """
    logging.debug("Starting search_cif function")
    logging.debug("Keyword arguments:")
    logging.debug(kwargs)

    # Define the base URL for the COD search
    base_url = "https://www.crystallography.net/cod/result"

    # Prepare the search parameters
    params = {
        "format": "json",
    }
    if "cod_id" in kwargs:
        if kwargs["cod_id"].isdigit():
            params["id"] = kwargs["cod_id"]
    if "formula" in kwargs:
        if kwargs["formula"] != "":
            # Check if the formula is a valid string
            params["formula"] = kwargs["formula"]
    if "elements" in kwargs:
        for i,el in enumerate(kwargs["elements"]):
            params[f"el{i+1}"] = el
    if "notelements" in kwargs:
        for i,nel in enumerate(kwargs["notelements"]):
            params[f"nel{i+1}"] = nel
    if "minelements" in kwargs:
        if kwargs["minelements"] > 0:
            params["min"] = kwargs["minelements"]
    if "maxelements" in kwargs:
        if kwargs["maxelements"] > 0:
            params["strictmax"] = kwargs["maxelements"]

    # Send a GET request to the COD API
    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        return None



def download_cif(cod_id, save_path="./cif"):
    """
    Download a CIF file from COD by its ID.
    
    Args:
        cod_id (str or int): The COD identifier (e.g., 9000001).
        save_path (str): Path to save the downloaded CIF file.
    """
    url = f"https://www.crystallography.net/cod/{cod_id}.cif"
    response = requests.get(url)

    if response.status_code == 200:
        file_path = f"{save_path}/{cod_id}.cif"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        logging.info(f"Downloaded CIF file saved to: {file_path}")
    else:
        logging.error(f"Failed to download CIF file {cod_id}. Status code: {response.status_code}")

def download_cifs(cod_ids, save_path="./cif"):
    """
    Download multiple CIF files from COD by their IDs.
    
    Args:
        cod_ids (list): List of COD identifiers (e.g., [9000001, 9000002]).
        save_path (str): Path to save the downloaded CIF files.
    """
    for cod_id in cod_ids:
        download_cif(cod_id, save_path)


from pymatgen.io.cif import CifParser
from pymatgen.analysis.diffraction.xrd import XRDCalculator

def getMaterialFromCIF(infilename, tthrange=(0, 20)):
    structure = CifParser(infilename).get_structures()[0]
    pks = XRDCalculator(wavelength=0.1).get_pattern(structure, two_theta_range=tthrange)
    hkls = pks.hkls
    d_hkls = pks.d_hkls
    two_pi_per_dhkls = [2*np.pi/d for d in d_hkls]
    material = {h[0]['hkl']:(d,two_pi_per_d) for h,d,two_pi_per_d in zip(hkls, d_hkls, two_pi_per_dhkls)}
    return material




