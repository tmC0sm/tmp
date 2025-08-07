#!/usr/bin/env python3
import argparse
import base64
import json
import logging
import re
import sys
import struct
import pefile
from capstone import *
from capstone.x86 import *
import os

ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
FILENAMES_BLACKLIST = ["rundll32.exe", "Powershell.exe"]

PROCESSING_NAME = "amadey_configuration_extractor"
VERSION = 1

def get_processing_name():
    return PROCESSING_NAME

def get_version():
    return VERSION


def decrypt_vigenere(data: list, key: str) -> str:
    """
    Decrypt a Vigenère cipher using the provided key

    :param data: cipher text
    :param key: key to decrypt the data
    :return: decrypted string
    """
    hash = ''
    for i in range(len(data)):
        hash += key[i % len(key)]

    decrypted = ''
    for i in range(len(data)):
        if data[i] not in ALPHABET:
            decrypted += data[i]
            continue
        index = (ALPHABET.index(data[i]) - ALPHABET.index(hash[i])) % len(ALPHABET)
        decrypted += ALPHABET[index]

    return base64.b64decode(decrypted).decode()

def get_section_by_name(pe: pefile.PE, section_name: str):
    """Get a section by its name"""
    for section in pe.sections:
        if section_name in section.Name:
            return section
    return None

def get_strings(pe: pefile.PE) -> list:
    """Extract strings from the .rdata section of the PE file"""
    rdata_section = get_section_by_name(pe, b".rdata")
    if not rdata_section:
        for section in pe.sections:
            if section.Characteristics & 0x40 == 0x40: # IMAGE_SCN_CNT_INITIALIZED_DATA
                rdata_section = section
                break
    if not rdata_section:
        logging.error("No '.rdata' section found")
        return []
    rdata_data = rdata_section.get_data()

    strings_set = []
    current_string = b""

    for byte in rdata_data:
        if byte != 0: # null byte
            current_string += bytes([byte])
        elif current_string:
            decoded_string = current_string.decode('utf-8', errors='replace')
            if re.match(r'[a-zA-Z =0-9]{4,}', decoded_string):
                strings_set.append(decoded_string)
            current_string = b""

    return strings_set

def find_key_vigenere_rc4_buildid(pe: pefile.PE) -> tuple:
    """
    Find the Vigenère key in the PE file using the following pattern:
    The function put the string in a custom string structure
    It can to find the vigenere key, the RC4 key and the build id
    .text:00401020 6A 20                             push    20h ; ' '
    .text:00401022 68 40 52 45 00                    push    offset aC5b33acb9a2efa ; "c5b33acb9a2efab2febfc1028a2f75c9"
    .text:00401027 B9 20 FC 45 00                    mov     ecx, offset dword_45FC20
    .text:0040102C E8 5F 4E 01 00                    call    decrypt_string

    :param pe: pefile.PE object
    :param insts: list of capstone instruction objects
    :return: Vigenère key
    """
    addr_key, key_size = None, None
    code_section = get_section_by_name(pe, b".text")

    if code_section is None:
        return None, None, None
    
    code = code_section.get_data()

    regex = rb"\x6A(.)\x68(....)\xB9....\xE8...."
    str_list = [] # contains tuple (addr, size)
    for i in range(3):
        match = re.search(regex, code)
        if match:
            key_size = struct.unpack("<b", match.group(1))[0]
            addr_key = struct.unpack("<I", match.group(2))[0]
            str_list.append((addr_key, key_size))
            logging.debug("Found key at address: %s (size: %d)", hex(addr_key), key_size)
            code = code[match.end():]
        else:
            break
    
    if len(str_list) != 3:
        logging.error("Keys and build id not found")
        return None, None, None

    rdata_section = get_section_by_name(pe, b".rdata")
    if not rdata_section:
        for section in pe.sections:
            if section.Characteristics & 0x40 == 0x40: # IMAGE_SCN_CNT_INITIALIZED_DATA
                rdata_section = section
                break

    if not rdata_section:
        logging.error("No '.rdata' section found")
        return None, None, None

    rdata_section_data = rdata_section.get_data()
    rdata_section_addr = pe.OPTIONAL_HEADER.ImageBase + rdata_section.VirtualAddress

    extract_data = [] # [0] = vigenere key  [1] = RC4 key  [2] = Build id
    for data in str_list:
        offset_within_section = data[0] - rdata_section_addr
        extract_data.append(rdata_section_data[offset_within_section:offset_within_section + data[1]].decode())
    return extract_data[0], extract_data[1], extract_data[2]

def extract(file_path: str) -> tuple:
    """
    Extract the Amadey configuration from the PE file
    
    :param file_path: path to the PE file
    :return: tuple (success, config)
    """
    pe = pefile.PE(file_path)
    md = Cs(CS_ARCH_X86, CS_MODE_32) # x86 32-bit
    md.skipdata = True
    md.detail = True
    
    """
    text_section = get_section_by_name(pe, b".text")
    if not text_section:
        logging.error("No '.text' section found")
        return 1, {}
    """
    for section in pe.sections:
        if section.Characteristics & 0x20000020 != 0: # IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_CNT_CODE
            text_section = section
            text_section_addr = pe.OPTIONAL_HEADER.ImageBase + text_section.VirtualAddress
            vigenere_key, rc4_key, build_id = find_key_vigenere_rc4_buildid(pe)
            logging.debug("Vigenère key: %s", vigenere_key)
            logging.debug("RC4 key: %s", vigenere_key)
            logging.debug("Build id: %s", vigenere_key)
            strings = get_strings(pe)

            config = {
              "filename": None,
              "c2_path": None,
              "version": None,
              "build": None,
              "rc4_key": None
            }

            config["build"] = build_id if build_id and len(build_id) == 6 else None
            config["rc4_key"] = rc4_key if rc4_key and len(rc4_key) == 32 else None
            possible_hosts = []
            for string in strings:
                try:
                    decrypted_string = decrypt_vigenere(string, vigenere_key)
                    if decrypted_string:
                        logging.debug("decrypt_vigenere('%s', '%s') = '%s'", string, vigenere_key, decrypted_string)

                        ip_addresses = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", decrypted_string)
                        c2_paths = re.findall(r'/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.php', decrypted_string)
                        version_numbers = re.findall(r'\b\d\.\d{1,2}\b', decrypted_string)     
                        dropped_files = re.findall(r'\b\w+\.exe\b', decrypted_string)
                        domain_names = re.findall(r"^(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.(?:com|net|space|ltd)$", decrypted_string) 

                        for ip_address in ip_addresses:
                            possible_hosts.append(ip_address)
                        
                        for domain_name in domain_names:
                            possible_hosts.append(domain_name)

                        for dropped_file in dropped_files:
                            if dropped_file not in FILENAMES_BLACKLIST:
                                config["filename"] = dropped_file

                        for c2_path in c2_paths:
                            config["c2_path"] = c2_path

                        for version in version_numbers:
                            config["version"] = version

                except:
                    pass

            success = len(possible_hosts) > 0 and config["filename"] is not None
            if success:
                if len(possible_hosts) == 1:
                    config["host"] = possible_hosts[0]
                else:
                    config["hosts"] = possible_hosts
                return 0, config
    logging.info("[-] No configuration found")
    return 2, {}

def load_or_create_json_sample_file(sample_path: str, json_path: str) -> dict:
    j_sample = None
    # Load json file if exists
    if json_path is not None :
        if os.path.exists(json_path):
            with open(json_path, "rb") as f:
                return json.load(f)

    with open(sample_path, "rb") as f:
        content = f.read()
    m = hashlib.md5()
    m.update(content)
    md5 = m.hexdigest()
    m = hashlib.sha1()
    m.update(content)
    sha1 = m.hexdigest()
    m = hashlib.sha256()
    m.update(content)
    sha256 = m.hexdigest()
    j_sample = {"sample": {"md5": md5, "sha1": sha1, "sha256": sha256, "size": len(content)}}
    with open(json_path, "w") as f:
        json.dump(j_sample, f, indent=4)
    return j_sample

def extract_for_tracker(sample_path: str, json_path : str, b_verbose: bool):
    """
    Extraction function for La Poste tracker.

    sample_path -- sample to process
    b_verbose -- guess what ?
    """
    try:
        log_level = logging.root.level
        logging.basicConfig(level=logging.DEBUG if b_verbose else logging.INFO)
        ret, config = extract(sample_path)
        # save json file
        if ret == 0:
            j_sample = load_or_create_json_sample_file(sample_path, json_path)
            j_sample["sample"]["configuration"] = {"decoded_configuration": config}
            with open(json_path, "w") as f:
                json.dump(j_sample, f, indent=4)
        logging.basicConfig(level=log_level)
        return ret, config
    except:
        logging.exception('Exception')
        return 999, None


def extract_json(sample_path: str) -> int:
    try:
        ret, config = extract(sample_path)
        if ret == 0:
            json.dump(config, open(args.file + ".json", "w"), indent=4)
            return 0
    except Exception as err:
        logging.error("Error: %s", err)
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract configuration from Amadey sample")
    parser.add_argument("file", help="Sample path")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    ret, config = extract(args.file)
    if ret==0:
        print(json.dumps(config, indent=4))
    sys.exit(ret)
