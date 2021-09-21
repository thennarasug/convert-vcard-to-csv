#!/usr/bin/env python
import vobject
import glob
import csv
import argparse
import os.path
import sys
import logging
import collections
import pandas as pd

input_path = ".\\input\\*.vcf"
output_path = ".\\output\\output.csv"

column_order = list()

def get_info_list(vCard):
    vcard = collections.OrderedDict()
    name = None
    increment_on_mul_email = 0
    increment_on_mul_pn = 0
    for key, val in list(vCard.contents.items()):

        if key in ['version', 'x-android-custom', 'rev', 'prodid', 'x-imagetype', 'x-abdate', 'x-ablabel', 'x-imagehash']:
            pass
        elif key in ['label']: #special case considered as note adding for information only
            pass
        else:
            if key == 'fn':
                vcard[key.upper()] = vCard.fn.value
            elif key == 'n':
                name = str(vCard.n.valueRepr()).replace('  ', ' ').strip()
                vcard[key.upper()] = name
            elif key == 'tel':
                for tel in vCard.tel_list:
                    increment_on_mul_pn = increment_on_mul_pn + 1
                    phone_label = "CELL" + str(increment_on_mul_pn).zfill(2)
                    phone = str(tel.value).strip()
                    phone = phone.replace("-", "")
                    phone = phone.replace(" ", "")
                    if phone not in vcard.values():
                        vcard[phone_label] = phone
            elif key == 'email':
                for email_item in vCard.email_list:
                    increment_on_mul_email = increment_on_mul_email + 1
                    email_label = "EMAIL" + str(increment_on_mul_email).zfill(2)
                    email = str(email_item.value).strip()
                    if email not in vcard.values():
                        vcard[email_label] = email
            elif key == 'bday':
                bday = str(vCard.bday.value).strip()
                vcard[key.upper()] = bday
            elif key == 'bday':
                bday = str(vCard.bday.value).strip()
                vcard[key.upper()] = bday
            elif key == 'note':
                note = str(vCard.note.value).strip()
                if 'NOTE' in vcard.keys():
                    note = vcard['NOTE'] + note
                vcard[key.upper()] = note
            elif key == 'org':
                org = str(vCard.org.value[0]).strip()
                vcard[key.upper()] = org
            elif key == 'title':
                title = str(vCard.title.value).strip()
                vcard[key.upper()] = title
            elif key == 'label':
                label = str(vCard.label.value).strip()
                if 'NOTE' in vcard.keys():
                    label = vcard['NOTE'] + label
                vcard['NOTE'] = label
            else:
                #other = str(vCard.note.value).strip()
                #vcard[key.upper()] = other
                # An unused key, like `adr`, `title`, `url`, etc.
                print(vCard)
                print('skipped', val)
                for v in val:
                    print(v, v.value)
                pass

    if name is None:
        logging.warning("no name for file")
    if "CELL01" not in vcard.keys():
        logging.warning("no telephone numbers with name `{}'".format(name))

    return vcard

def readable_directory(path):
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(
            'not an existing directory: {}'.format(path))
    if not os.access(path, os.R_OK):
        raise argparse.ArgumentTypeError(
            'not a readable directory: {}'.format(path))
    return path

def runme():
    logging.basicConfig(level=logging.INFO)

    vcard_pattern = os.path.join(input_path)
    vcards = sorted(glob.glob(vcard_pattern))

    vcards_extracted = list()
    unique_labels = set()

    if len(vcards) == 0:
        logging.error("no files ending with `.vcf` in directory `{}'".format(input_path))
        sys.exit(2)


    #loop to parse parsing vcard
    for vcard_path in vcards:
        with open(vcard_path) as fp:
            vCard_text = fp.read()

            #vCard_one = vobject.readOne(vCard_text)
            vCard_iterator = vobject.readComponents(vCard_text)

            for vCard in vCard_iterator:
                vCard.validate()
                vcard_info = get_info_list(vCard)
                vcards_extracted.append(vcard_info)

    #get unique keys
    for key_for_sort in vcards_extracted:
        unique_labels.update(set(key_for_sort.keys()))

    label_list = sorted(unique_labels)

    df = pd.DataFrame([], columns=label_list)

    #construct the table for output
    for key_for_sort in vcards_extracted:
        df = df.append(key_for_sort, ignore_index=True)

    df.sort_values(by=['N'], ascending=True, inplace=True)
    df.reset_index(drop=True, inplace=True)

    try:
        df.to_csv(output_path, sep='\t', encoding='utf-8', index = False, header=True)
    except Exception as e:
        logging.error("no files written as {} --> exception {}`".format(output_path, e))
    except:
        logging.error("no files written as {} --> exc_info {}`".format(output_path, sys.exc_info()[0]))


if __name__ == "__main__":
    runme()
