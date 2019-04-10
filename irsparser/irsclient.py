import urllib.request
import requests
import datetime
from os.path import join
import pandas as pd
import os
import json
import re
import certifi
import urllib3
import flatten_json
from .irs_helpers import xml_parser3
from .irs_helpers import commonNTEEparser, deductibilityParser
from .irs_helpers import descNTEEparser, organizationParser
from .irs_db_utils import DBConnect
from .irs_schedule_helpers import parse_officer_list, parse_schedule_j, parse_grant_table, get_irs_base_dashboard


class Client():
    """Initialize a client that will hold the data necessary to parse IRS data.
    We will need to initalize the following:

    1. A list of EINs that will be used to subset the indices
    2. A list of indices that we will use to find XML files
    3. The location of the data folder to put/retrieve data
    """

    def __init__(
        self, local_data_dir=None, ein_filename=None,
        index_years=[2016, 2017, 2018], save_xml=False,
        parser="base", build_db=True, db_name="database.sqlite3"
    ):

        self.local_data_dir = local_data_dir
        self.save_xml = save_xml
        self.parser = parser
        self.db_path = join(self.local_data_dir, db_name)
        db_conn = DBConnect(self.db_path)

        eins = self.get_eins(ein_filename)
        indices_all = self.get_index(
            index_years)

        self.jewish_orgs_all = [
            org for org in indices_all if org["EIN"] in eins]
        print((
            "Number of Jewish Orgs in Indices: " +
            str(len(self.jewish_orgs_all))))

        jewish_orgs_all_df = pd.DataFrame(self.jewish_orgs_all)

        self.most_recent_filings = jewish_orgs_all_df.loc[
            jewish_orgs_all_df["FormType"] == "990", :]\
            .sort_values(["EIN", "TaxPeriod", "LastUpdated"])\
            .groupby(["EIN", "TaxPeriod"], as_index=False).last()

        self.obj_ids = self.most_recent_filings["ObjectId"].values
        self.eins = eins
        self.parse_xmls(add_organization_info=True)

        # Parse Officer List Form990PartVIISectionAGrp
        self.df_officers = parse_officer_list(self.df)
        # Parse Schedule J
        self.df_schedulej = parse_schedule_j(self.df)

        # Parse Grant List to Table - Schedule I
        self.df_grants = parse_grant_table(self.df)

        # Get Working Dashboard for SQL
        self.df_dash = get_irs_base_dashboard(self.df)

        # Save to SQL
        if build_db:
            db_conn.initialize_db()
            table_insert = "replace"
        else:
            table_insert = "append"
        db_conn.saveDF(self.df_dash, table="irs_dashboard", insert=table_insert)
        db_conn.saveDF(self.df_officers, table="officer_payment", insert=table_insert)
        db_conn.saveDF(self.df_schedulej, table="schedule_j", insert=table_insert)
        db_conn.saveDF(self.df_grants, table="grants", insert=table_insert)

    def get_eins(self, filename):
        """Provide a list of EINS in a text file with each EIN on a newline.
        """

        # Get the list of EINS
        eins = []
        filename = join(self.local_data_dir, filename)
        with open(filename, 'r') as f:
            for line in f:
                eins.append(line.replace('-', '').strip('\n'))
        print(f"Number of EINS: {len(eins)}")
        return eins

    def get_index(self, years):
        """Provide a list of years. This function will check to see if the
        index exists in your data folder, otherwise it will download the file
        from AWS.

        Sample Input:
        years = [2016, 2017, 2018]
        """
        indices_all = []

        for year in years:
            idx_name = "index_" + str(year) + ".json"
            filename = join(self.local_data_dir, idx_name)

            if not os.path.exists(filename):
                url = "https://s3.amazonaws.com/irs-form-990/" + idx_name
                urllib.request.urlretrieve(url, filename)

            with open(filename, 'r') as f:
                filing_name = "Filings" + str(year)
                d = json.load(f)
                res = d[filing_name]

            print(f"Gathered for {filing_name}")
            indices_all = indices_all + res
        return indices_all

    def parse_xmls(self, add_organization_info=True):
        success_file, error_file = self.irs_parse(
            self.obj_ids,
            save_xml=self.save_xml)

        # Match EIN types for merge
        self.most_recent_filings["EIN"] = (
            self.most_recent_filings["EIN"].astype(str))
        success_file["EIN"] = success_file["EIN"].astype(str)

        self.df = pd.merge(
            self.most_recent_filings, success_file,
            how="right",
            on=["EIN", "ObjectId", "URL"])

        if add_organization_info:
            df_org = self.getOrgProfiles
            self.df = pd.merge(self.df, df_org, on="EIN", how="left")
        self.error_file = error_file

    def irs_parse(self, obj_ids, save_xml=False):
        success = []
        error_file = []
        t0 = datetime.datetime.now()

        for i, oid in enumerate(obj_ids):

            new_url = (
                "https://s3.amazonaws.com/irs-form-990/" + oid + "_public.xml")
            fname = os.path.join(
                self.local_data_dir, "xml_files", oid + ".xml")

            if os.path.exists(fname):
                try:
                    with open(fname, "rb") as f:
                        txt = f.read()
                    tmp = xml_parser3(txt, self.parser)
                    tmp["ObjectId"] = oid
                    tmp["URL"] = new_url
                    success.append(tmp)
                except Exception as e:
                    with open(fname, "rb") as f:
                        txt = f.read()
                    p = re.compile('returnVersion="(\d+v\d.\d)"')
                    version = str(p.findall(str(txt))[0])
                    error_file.append(
                        {"url": new_url, "error": e, "version": version})

            else:
                try:
                    txt = requests.get(new_urlß)
                    if save_xml:
                        with open(fname, "wb") as f:
                            f.write(txt.content)
                    tmp = xml_parser3(txt.content, self.parser)
                    tmp["ObjectId"] = oid
                    tmp["URL"] = new_url

                    success.append(tmp)
                except Exception as e:
                    error_file.append({"url": new_url, "error": e})

            if (i % 1000 == 0) & (i > 0):
                t1 = datetime.datetime.now()
                print(str(i) + " records processed")
                print((
                    "Total Runtime " +
                    str((t1 - t0).total_seconds()) + " seconds"))
        return pd.DataFrame(success), pd.DataFrame(error_file)

    @property
    def getOrgProfiles(self):

        # NTEE Values
        df = pd.DataFrame()
        filename = join(self.local_data_dir, "eo1.csv")

        if not os.path.exists(filename):
            for i in range(1, 5):
                eo = requests.get(f"https://www.irs.gov/pub/irs-soi/eo{str(i)}.csv")
                filename = join(self.local_data_dir, f"eo{str(i)}.csv")
                with open(filename, 'wb') as f:
                    for chunk in eo:
                        f.write(chunk)

        for eo in ["eo1.csv", "eo2.csv", "eo3.csv", "eo4.csv"]:
            filename = join(self.local_data_dir, eo)
            tmp = pd.read_csv(
                filename,
                usecols=[
                    "EIN", "NTEE_CD", "DEDUCTIBILITY",
                    "FOUNDATION", "ORGANIZATION"],
                dtype={"EIN": str})
            tmp["EIN"] = tmp["EIN"].astype(str)
            tmp.index = tmp.index.astype(str)
            tmp_sub = tmp.loc[tmp["EIN"].isin(self.eins), :].copy()
            df = df.append(tmp_sub)

        # NTEE Common Codes
        filename = join(self.local_data_dir, 'ntee_common_codes.csv')
        tmp = pd.read_csv(filename, index_col="Code")
        ntee_common_codes = tmp.to_dict().get("Description")
        df["NTEE_COMMON"] = (
            df["NTEE_CD"]
            .apply(lambda x: commonNTEEparser(str(x)[0:3], ntee_common_codes)))

        # NTEE Descriptions
        filename = join(self.local_data_dir, "ntee_codes_descr.csv")
        tmp = pd.read_csv(filename, index_col="Code")
        ntee_names = tmp.to_dict().get("Description")
        df["NTEE_DESCR"] = (
            df["NTEE_CD"]
            .apply(lambda x: descNTEEparser(str(x)[0:3], ntee_names)))

        # Deductibility
        df["DEDUCTIBILITY"] = df["DEDUCTIBILITY"].apply(deductibilityParser)

        # Foundation
        filename = join(self.local_data_dir, 'foundation_codes.csv')
        tmp = pd.read_csv(filename, index_col="Code")
        foundation_codes = tmp.to_dict().get("Description")
        df["FOUNDATION"] = df["FOUNDATION"].map(foundation_codes)

        # Organization
        df["ORGANIZATION"] = df["ORGANIZATION"].apply(organizationParser)

        df.rename(
            columns={
                "DEDUCTIBILITY": "Deductibility",
                "ORGANIZATION": "Organization",
                "FOUNDATION": "Foundation", "NTEE_COMMON": "NTEECommonCode",
                "NTEE_CD": "NTEECode", "NTEE_DESCR": "NTEECodeDescription"},
            inplace=True)
        return df

    def getFinalDF(self):
        return self.df

    def getErrorDF(self):
        return self.error_file

    def getScheduleJ(self):
        return self.df_schedulej

    def getOfficerDF(self):
        return self.df_officers

    def getGrantsDF(self):
        return self.df_grants

    def getDashboardDF(self):
        return self.df_dash

    def getPrincipalOfficerDF(self):
        # First Grab the Principal Officer listed on the first page of the IRS Form
        officers = self.df[[
            "EIN", "ObjectId", "OrganizationName", "TaxYr", "StateAbbr", "Mission",
            "OfficerName", "OfficerTitle", "OfficerCompensationPart9",
            "CYTotalExpenses"]].copy()

        # Caps Names
        officers["OfficerName"] = officers["OfficerName"].apply(lambda x: x.upper())
        # Deal with Titles
        officers["OfficerTitle"] = officers["OfficerTitle"].apply(lambda x: str(x).upper())
        # Add Officer Compensation Percentage of Total Expenses
        tmp_val = officers["OfficerCompensationPart9"] / officers["CYTotalExpenses"]
        officers.loc[:, "OfficerCompensationPct"] = tmp_val.copy()
        return officers


