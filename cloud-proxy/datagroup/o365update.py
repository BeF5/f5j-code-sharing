#!/usr/bin/python
# -*- coding: utf-8 -*-
# O365 url/ip update automation for BIG-IP
# Version: 1.30
# Last Modified: 2 July 2021
# Author: Makoto Omura, F5 Networks Japan G.K.
#
# This Sample Software provided by the author is for illustrative
# purposes only which provides customers with programming information
# regarding the products. This software is supplied "AS IS" without any
# warranties and support.
#
# The author assumes no responsibility or liability for the use of the
# software, conveys no license or title under any patent, copyright, or
# mask work right to the product.
#
# The author reserves the right to make changes in the software without
# notification. The author also make no representation or warranty that
# such application will be suitable for the specified use without
# further testing or modification.

import httplib
import urllib
import uuid
import os
import re
import json
import commands
import datetime
import sys

#-----------------------------------------------------------------------
# User Options - Configure as desired
#-----------------------------------------------------------------------

# Record types to download & update
use_url = 1     # URL based proxy bypassing: 0=do not use, 1=use
use_ipv4 = 0    # IPv4 based routing: 0=do not use, 1=use
use_ipv6 = 0    # IPv6 based routing: 0=do not use, 1=use

# Generate 2 more lists with & without Express Route
use_url_express_route = 0   # URL lists: 0=do not generate, 1=generate
use_ipv4_express_route = 0  # IPv4 lists: 0=do not generate, 1=generate
use_ipv6_express_route = 0  # IPv6 lists: 0=do not generate, 1=generate

# O365 "SeviceArea" (application) to include in bypass lists
care_common = 1     # "Common": 0=ignore, 1=include
care_exchange = 1   # "Exchange": 0=ignore, 1=include
care_skype = 1      # "Skype": 0=ignore, 1=include
care_sharepoint = 1 # "SharePoint": 0=ignore, 1=include

# O365 "category" to include in bypass lists
care_cat_allow  = 1     # "Allow" category: 0=ignore, 1=include
care_cat_optimize = 1   # "Optimize" category: 0=ignore, 1=include
care_cat_default = 1    # "Default" category: 0=ignore, 1=include

# Action if O365 endpoint list is not updated
force_o365_record_refresh = 0   # 0=do not update, 1=update (for test/debug purpose)

# BIG-IP Data Group name
dg_urls_to_bypass_all = "ext_o365_url"              # All URLs
dg_urls_to_bypass_er_true = "ext_o365_url_er_true"  # URLs to go via Express Route
dg_urls_to_bypass_er_none = "ext_o365_url_er_none"  # URLs not to go via Express Route
dg_ip4s_to_bypass_all = "ext_o365_ip4"              # All IPv4 endpoints
dg_ip4s_to_bypass_er_true = "ext_o365_ip4_er_true"  # IPv4 endpoints to go via Express Route
dg_ip4s_to_bypass_er_none = "ext_o365_ip4_er_none"  # IPv4 endpoints not to go via Express Route
dg_ip6s_to_bypass_all = "ext_o365_ip6"              # All IPv6 endpoints
dg_ip6s_to_bypass_er_true = "ext_o365_ip6_er_true"  # IPv6 endpoints to go via Express Route
dg_ip6s_to_bypass_er_none = "ext_o365_ip6_er_none"  # IPv6 endpoints not to go via Express Route

# BIG-IP HA Configuration
device_group_name = "dg-failover-1"     # Name of Sync-Failover Device Group.  Required for HA paired BIG-IP.
ha_config = 1                           # 0=stand alone, 1=HA paired

# Log configuration
log_level = 1   # 0=none, 1=normal, 2=verbose
log_dest_file = "/var/log/o365_update"

#-----------------------------------------------------------------------
# User Options - Modify only when necessary
#-----------------------------------------------------------------------

# Work directory, file name for guid & version management
work_directory = "/var/tmp/o365"
file_name_guid = "/var/tmp/o365/guid.txt"
file_ms_o365_version = "/var/tmp/o365/o365_version.txt"

# Data Group File name
dg_file_name_urls_all = "/var/tmp/o365/o365_urls.txt"
dg_file_name_urls_er_true = "/var/tmp/o365/o365_urls_er_true.txt"
dg_file_name_urls_er_none = "/var/tmp/o365/o365_urls_er_none.txt"
dg_file_name_ip4_all = "/var/tmp/o365/o365_ip4.txt"
dg_file_name_ip4_er_true = "/var/tmp/o365/o365_ip4_er_true.txt"
dg_file_name_ip4_er_none = "/var/tmp/o365/o365_ip4_er_none.txt"
dg_file_name_ip6_all = "/var/tmp/o365/o365_ip6.txt"
dg_file_name_ip6_er_true = "/var/tmp/o365/o365_ip6_er_true.txt"
dg_file_name_ip6_er_none = "/var/tmp/o365/o365_ip6_er_none.txt"

# Microsoft Web Service URL & URI
url_ms_o365_endpoints = "endpoints.office.com"
uri_ms_o365_endpoints = "/endpoints/worldwide?ClientRequestId="
url_ms_o365_version = "endpoints.office.com"
uri_ms_o365_version = "/version?ClientRequestId="

#-----------------------------------------------------------------------
# Non Options - Please do not modify here and below
#-----------------------------------------------------------------------

def log(lev, msg):
    if log_level >= lev:
        log_string = "{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now()) + " " + msg + "\n"
        f = open(log_dest_file, "a")
        f.write(log_string)
        f.flush()
        f.close()
    return


def extract_urls(o365_ep_element, output_list, log_label):
    # Append "urls" if existent in each record
    if o365_ep_element.has_key('urls'):
        list_urls = list(o365_ep_element['urls'])
        for url in list_urls:
            output_list.append(url)


def extract_ips(o365_ep_element, output_list_v4, output_list_v6, log_label):
    # Append "ips" if existent in each record
    if o365_ep_element.has_key('ips'):
        list_ips = list(o365_ep_element['ips'])
        for ip in list_ips:
            if re.match('^.+:', ip):
                output_list_v6.append(ip)
            else:
                output_list_v4.append(ip)


def datagroup_output_urls(source_file_name, output_data_group, log_label):
    # -----------------------------------------------------------------------
    # Data Group File update
    # -----------------------------------------------------------------------
    # The object appears in WebUI: System › File Management : Data Group File List >> xxx_object
    # {source_file_name} expects one of the Data Group File name variables (dg_file_name_xxx_xxx)
    # {target_data_group} expects one of the Data Group name variables (dg_xxx_to_bypass_xxx)
    result = commands.getoutput("tmsh list sys file data-group " + output_data_group + "_object")
    # Create or update Data Group File from text file (given for variable "source_file_name")
    if "was not found" in result:
        result2 = commands.getoutput("tmsh create /sys file data-group " + output_data_group
                                     + "_object type string source-path file:" + source_file_name)
        log(2, log_label + ": Data Group File " + output_data_group + "_object was not found.  Created from "
            + source_file_name + ".")
    else:
        result2 = commands.getoutput("tmsh modify /sys file data-group " + output_data_group
                                     + "_object source-path file:" + source_file_name)
        log(2, log_label + ": Data Group File " + output_data_group + "_object was found.  Updated from "
            + source_file_name + ".")

    # -----------------------------------------------------------------------
    # Make sure Data Group exists that corresponds to File update
    # -----------------------------------------------------------------------
    # The object appears in WebUI: Local Traffic >> iRules : Data Group List >> (External File) xxx
    # The object needs to exist, but does not have to be explicitly updated by this script
    result = commands.getoutput("tmsh list /ltm data-group external " + output_data_group)
    if "was not found" in result:
        result2 = commands.getoutput("tmsh create /ltm data-group external " + output_data_group
                                     + " external-file-name " + output_data_group + "_object")
        log(2, log_label + ": Data Group " + output_data_group + " was not found.  Creating it from "
            + output_data_group + "_object")


def datagroup_output_ips(source_file_name, output_data_group, log_label):
    # -----------------------------------------------------------------------
    # Data Group File update
    # -----------------------------------------------------------------------
    # The object appears in WebUI: System › File Management : Data Group File List >> xxx_object
    # {source_file_name} expects one of the Data Group File name variables (dg_file_name_xxx_xxx)
    # {target_data_group} expects one of the Data Group name variables (dg_xxx_to_bypass_xxx)
    result = commands.getoutput("tmsh list /sys file data-group " + output_data_group + "_object")

    # Create or update Data Group File from text file (given for variable "source_file_name")
    if "was not found" in result:
        result2 = commands.getoutput("tmsh create /sys file data-group " + output_data_group
                                     + "_object type ip source-path file:" + source_file_name)
        log(2, log_label + ": Data Group File " + output_data_group
            + "_object was not found.  Created from " + source_file_name + ".")
    else:
        result2 = commands.getoutput("tmsh modify /sys file data-group " + output_data_group
                                     + "_object source-path file:" + source_file_name)
        log(2, log_label + ": Data Group File " + output_data_group
            + "_object was found.  Updated from " + source_file_name + ".")

    # -----------------------------------------------------------------------
    # Make sure Data Group exists that corresponds to File update
    # -----------------------------------------------------------------------
    # The object appears in WebUI: Local Traffic >> iRules : Data Group List >> (External File) xxx
    # The object needs to exist, but does not have to be explicitly updated by this script
    result = commands.getoutput("tmsh list /ltm data-group external " + output_data_group)
    if "was not found" in result:
        result2 = commands.getoutput("tmsh create /ltm data-group external " + output_data_group
                                     + " external-file-name " + output_data_group  + "_object")
        log(2, log_label + ": Data Group " + output_data_group
            + " was not found.  Creating it from " + output_data_group  + "_object")


# -----------------------------------------------------------------------
# O365 endpoints URL asterisk removal and re-format to fit into Data Group
# -----------------------------------------------------------------------
def process_urls(list_urls, output_file_name, log_label):
    # Process asterisk nicely.  Force lower case letter.
    temporary_list_urls = []
    for url in list_urls:
        url_processed = re.sub('^.*[*][^.]*', '', url).lower()
        temporary_list_urls.append(url_processed)

    # URL sort & dedupe. Generate file for External Data Group
    fout = open(output_file_name, 'w')
    num_urls_post = 0
    for url in (list(sorted(set(temporary_list_urls)))):
        fout.write(str(url) + " := 1,\n")
        num_urls_post += 1
    fout.flush()
    fout.close()
    log(2, log_label + ": Number of ENDPOINTS to import (after dedupe) - URL:" + str(num_urls_post))
    return (num_urls_post)


# -----------------------------------------------------------------------
# IP addresses distinguished as either network or host, then saved to text file
# -----------------------------------------------------------------------
def process_ips(list_ips, output_file_name, log_label):
    # Process IP dictionaries
    fout = open(output_file_name, 'w')
    num_ips_post = 0
    for ip in (list(sorted(set(list_ips)))):
        num_ips_post += 1
        if "/" in ip:
            fout.write("network " + str(ip) + ",\n")
        else:
            fout.write("host " + str(ip) + ",\n")
    fout.flush()
    fout.close()
    log(2, log_label + ": Number of ENDPOINTS to import (after dedupe) -IP:" + str(num_ips_post))
    return (num_ips_post)


def main():
    list_urls_all = []
    list_urls_er_true = []
    list_urls_er_none = []
    list_ips4_all = []
    list_ips4_er_true = []
    list_ips4_er_none = []
    list_ips6_all = []
    list_ips6_er_true = []
    list_ips6_er_none = []
    failover_state = ""

    # Supposed {log_label} elements
    # ["URL_ALL" | "URL_ER_TRUE" | "URL_ER NONE" | "IP_ALL" | "IP_ER_TRUE" | "IP_ER_NONE"]

    # -----------------------------------------------------------------------
    # Check if this BIG-IP is ACTIVE for the traffic group (= traffic_group_name)
    # -----------------------------------------------------------------------
    result = commands.getoutput("tmsh show /cm failover-status field-fmt")
    if ("status ACTIVE" in result)\
            or (ha_config == 0):
        failover_state = "active"       # For future use
        log(1, "This BIG-IP is ACTIVE. Initiating O365 update.")
    else:
        failover_state = "non-active"   # For future use
        log(1, "This BIG-IP is STANDBY. Aborting O365 update.")
        sys.exit(0)

    # -----------------------------------------------------------------------
    # GUID management
    # -----------------------------------------------------------------------
    # Create GUID file if not existent
    if not os.path.isdir(work_directory):
        os.mkdir(work_directory)
        log(1, "Created work directory " + work_directory + " because it did not exist.")
    if not os.path.exists(file_name_guid):
        f = open(file_name_guid, "w")
        f.write("\n")
        f.flush()
        f.close()
        log(1, "Created GUID file " + file_name_guid + " because it did not exist.")

    # Read GUID from file and validate.  Create one if not existent
    f = open(file_name_guid, "r")
    f_content = f.readline()
    f.close()
    if re.match('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', f_content):
        guid = f_content
        log(2, "Valid GUID is read from local file " + file_name_guid + ".")
    else:
        guid = str(uuid.uuid4())
        f = open(file_name_guid, "w")
        f.write(guid)
        f.flush()
        f.close()
        log(1, "Generated a new GUID, and saved it to " + file_name_guid + ".")

    # -----------------------------------------------------------------------
    # O365 endpoints list version check
    # -----------------------------------------------------------------------
    # Read version of previously received record
    if os.path.isfile(file_ms_o365_version):
        f = open(file_ms_o365_version, "r")
        f_content = f.readline()
        f.close()
        # Check if the VERSION record format is valid
        if re.match('[0-9]{10}', f_content):
            ms_o365_version_previous = f_content
            log(2, "Valid previous VERSION found in " + file_ms_o365_version + ".")
        else:
            ms_o365_version_previous = "1970010200"
            f = open(file_ms_o365_version, "w")
            f.write(ms_o365_version_previous)
            f.flush()
            f.close()
            log(1, "Valid previous VERSION was not found.  Wrote dummy value in " + file_ms_o365_version + ".")
    else:
        ms_o365_version_previous = "1970010200"
        f = open(file_ms_o365_version, "w")
        f.write(ms_o365_version_previous)
        f.flush()
        f.close()
        log(1, "Valid previous VERSION was not found.  Wrote dummy value in " + file_ms_o365_version + ".")

    # -----------------------------------------------------------------------
    # O365 endpoints list VERSION check - lookup MS server
    # -----------------------------------------------------------------------
    request_string = uri_ms_o365_version + guid
    conn = httplib.HTTPSConnection(url_ms_o365_version)
    conn.request('GET', request_string)
    res = conn.getresponse()

    if not res.status == 200:
        # MS O365 version request failed
        log(1, "VERSION request to MS web service failed.  Assuming VERSIONs did not match, and proceed.")
        dict_o365_version = {}
    else:
        # MS O365 version request succeeded
        log(2, "VERSION request to MS web service was successful.")
        dict_o365_version = json.loads(res.read())

    ms_o365_version_latest = ""
    for record in dict_o365_version:
        if record.has_key('instance'):
            if record["instance"] == "Worldwide" and record.has_key("latest"):
                latest = record["latest"]
                if re.match('[0-9]{10}', latest):
                    ms_o365_version_latest = latest
                    f = open(file_ms_o365_version, "w")
                    f.write(ms_o365_version_latest)
                    f.flush()
                    f.close()

    log(2, "Previous VERSION is " + ms_o365_version_previous)
    log(2, "Latest VERSION is " + ms_o365_version_latest)

    if ms_o365_version_latest == ms_o365_version_previous and force_o365_record_refresh == 0:
        log(1, "You already have the latest MS O365 URL/IP Address list: " + ms_o365_version_latest + ". Aborting operation.")
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Request O365 endpoints list & put it in dictionary
    # -----------------------------------------------------------------------
    request_string = uri_ms_o365_endpoints + guid
    conn = httplib.HTTPSConnection(url_ms_o365_endpoints)
    conn.request('GET', request_string)
    res = conn.getresponse()

    if not res.status == 200:
        log(1, "ENDPOINTS request to MS web service failed. Aborting operation.")
        sys.exit(0)
    else:
        log(2, "ENDPOINTS request to MS web service was successful.")
        dict_o365_all = json.loads(res.read())

    # -----------------------------------------------------------------------
    # Pick only required categories of records
    # -----------------------------------------------------------------------


    # -----------------------------------------------------------------------
    # Process each record (O365 endpoint) which is dictionary type
    # -----------------------------------------------------------------------
    for dict_o365_record in dict_o365_all:
        ep_service_area = str(dict_o365_record['serviceArea'])
        ep_category = str(dict_o365_record['category'])
        id = str(dict_o365_record['id'])

        if (care_common and ep_service_area == "Common") \
            or (care_exchange and ep_service_area == "Exchange") \
            or (care_sharepoint and ep_service_area == "SharePoint") \
            or (care_skype and ep_service_area == "Skype"):

            if (care_cat_allow and ep_category == "Allow") \
                or (care_cat_optimize and ep_category == "Optimize") \
                or (care_cat_default and ep_category == "Default"):

                if use_url:
                    #def extract_urls(o365_ep_element, output_list, log_label):
                    extract_urls(dict_o365_record, list_urls_all, "URL_ALL")

                if use_url_express_route:
                    #def extract_urls(o365_ep_element, output_list, log_label):
                    if (dict_o365_record.get("expressRoute") == 1):
                        extract_urls(dict_o365_record, list_urls_er_true, "URL_ER_TRUE")
                    else:
                        extract_urls(dict_o365_record, list_urls_er_none, "URL_ER NONE")

                if use_ipv4 or use_ipv6:
                    #def extract_ips(o365_ep_element, output_list_v4, output_list_v6, log_label):
                    extract_ips(dict_o365_record, list_ips4_all, list_ips6_all, "URL_ALL")

                if use_ipv4_express_route or use_ipv6_express_route:
                    #def extract_ips(o365_ep_element, output_list_v4, output_list_v6, log_label):
                    if (dict_o365_record.get("expressRoute") == 1):
                        extract_ips(dict_o365_record, list_ips4_er_true, list_ips6_er_true, "URL_ER_TRUE")
                    else:
                        extract_ips(dict_o365_record, list_ips4_er_none, list_ips6_er_none, "URL_ER NONE")

    # -----------------------------------------------------------------------
    # Process lists of ips & urls
    # -----------------------------------------------------------------------

    num_list_urls_all_pre       = len(list_urls_all)
    num_list_urls_er_true_pre   = len(list_urls_er_true)
    num_list_urls_er_none_pre   = len(list_urls_er_none)
    num_list_ips4_all_pre       = len(list_ips4_all)
    num_list_ips4_er_true_pre   = len(list_ips4_er_true)
    num_list_ips4_er_none_pre   = len(list_ips4_er_none)
    num_list_ips6_all_pre       = len(list_ips6_all)
    num_list_ips6_er_true_pre   = len(list_ips6_er_true)
    num_list_ips6_er_none_pre   = len(list_ips6_er_none)

    num_list_urls_all_post      = 0
    num_list_urls_er_true_post  = 0
    num_list_urls_er_none_post  = 0
    num_list_ips4_all_post      = 0
    num_list_ips4_er_true_post  = 0
    num_list_ips4_er_none_post  = 0
    num_list_ips6_all_post      = 0
    num_list_ips6_er_true_post  = 0
    num_list_ips6_er_none_post  = 0

    if use_url:
        # def process_urls(list_urls, output_file_name, log_label):
        num_list_urls_all_post = process_urls(list_urls_all, dg_file_name_urls_all, "URL_ALL")
        # def datagroup_output_urls(source_file_name, output_data_group, log_label):
        datagroup_output_urls(dg_file_name_urls_all, dg_urls_to_bypass_all, "URL_ALL")

    if use_url_express_route:
        num_list_urls_er_true_post = process_urls(list_urls_er_true, dg_file_name_urls_er_true, "URL_ER_TRUE")
        datagroup_output_urls(dg_file_name_urls_er_true, dg_urls_to_bypass_er_true, "URL_ER_TRUE")
        num_list_urls_er_none_post = process_urls(list_urls_er_none, dg_file_name_urls_er_none, "URL_ER_NONE")
        datagroup_output_urls(dg_file_name_urls_er_none, dg_urls_to_bypass_er_none, "URL_ER_NONE")

    if use_ipv4:
        # def process_ips(list_ips, output_file_name, log_label):
        num_list_ips4_all_post = process_ips(list_ips4_all, dg_file_name_ip4_all, "URL_ALL")
        # def datagroup_output_ips(source_file_name, target_data_group, log_label):
        datagroup_output_ips(dg_file_name_ip4_all, dg_ip4s_to_bypass_all, "URL_ALL")

    if use_ipv6:
        num_list_ips6_all_post = process_ips(list_ips6_all, dg_file_name_ip6_all, "URL_ALL")
        datagroup_output_ips(dg_file_name_ip6_all, dg_ip6s_to_bypass_all, "URL_ALL")

    if use_ipv4_express_route:
        num_list_ips4_er_true_post = process_ips(list_ips4_er_true, dg_file_name_ip4_er_true, "URL_ER_TRUE")
        datagroup_output_ips(dg_file_name_ip4_er_true, dg_ip4s_to_bypass_er_true, "URL_ER_TRUE")
        num_list_ips4_er_none_post = process_ips(list_ips4_er_none, dg_file_name_ip4_er_none, "URL_ER_NONE")
        datagroup_output_ips(dg_file_name_ip4_er_none, dg_ip4s_to_bypass_er_none, "URL_ER_NONE")

    if use_ipv6_express_route:
        num_list_ips6_er_true_post = process_ips(list_ips6_er_true, dg_file_name_ip6_er_true, "URL_ER_TRUE")
        datagroup_output_ips(dg_file_name_ip6_er_true, dg_ip6s_to_bypass_er_true, "URL_ER_TRUE")
        num_list_ips6_er_none_post = process_ips(list_ips6_er_none, dg_file_name_ip6_er_none, "URL_ER_NONE")
        datagroup_output_ips(dg_file_name_ip6_er_none, dg_ip6s_to_bypass_er_none, "URL_ER_NONE")

    log(1, "# records to import before dedupe - URL:" + str(num_list_urls_all_pre) + ", IPv4 host/net:"
        + str(num_list_ips4_all_pre) + ", IPv6 host/net:" + str(num_list_ips6_all_pre))
    log(1, "# records to import after dedupe - URL:" + str(num_list_urls_all_post) + ", IPv4 host/net:"
        + str(num_list_ips4_all_post) + ", IPv6 host/net:" + str(num_list_ips6_all_post))

    log(1, "# records to import (Express Route: true) before dedupe - URL:" + str(num_list_urls_er_true_pre)
        + ", IPv4 host/net:" + str(num_list_ips4_er_true_pre) + ", IPv6 host/net:"
        + str(num_list_ips6_er_true_pre))
    log(1, "# records to import (Express Route: true) after dedupe - URL:" + str(num_list_urls_er_true_post)
        + ", IPv4 host/net:" + str(num_list_ips4_er_true_post) + ", IPv6 host/net:"
        + str(num_list_ips6_er_true_post))

    log(1, "# records to import (Express Route: none) before dedupe - URL:" + str(num_list_urls_er_none_pre)
        + ", IPv4 host/net:" + str(num_list_ips4_er_none_pre) + ", IPv6 host/net:"
        + str(num_list_ips6_er_none_pre))
    log(1, "# records to import (Express Route: none) after dedupe - URL:" + str(num_list_urls_er_none_post)
        + ", IPv4 host/net:" + str(num_list_ips4_er_none_post) + ", IPv6 host/net:"
        + str(num_list_ips6_er_none_post))

    #-----------------------------------------------------------------------
    # Save config
    #-----------------------------------------------------------------------
    log(1, "Saving BIG-IP Configuration.")
    result = commands.getoutput("tmsh save /sys config")
    log(2, result + "\n")

    #-----------------------------------------------------------------------
    # Initiate Config Sync: Device to Group
    #-----------------------------------------------------------------------

    if ha_config == 1:
        log(1, "Initiating Config-Sync.")
        result = commands.getoutput("tmsh run cm config-sync to-group " + device_group_name)
        log(2, result + "\n")

    log(1, "Completed O365 URL/IP address update process.")

if __name__=='__main__':
    main()
