import pandas as pd
import numpy as np
import os
from pandas.io.json import json_normalize
import sys
import irsparser as irs
sys.path.append("../../")


def parse_officer_list(df):
    """Parse the Officer List and build new dataframe officer_list

    Takes the OfficerList column returned from IRS990 and builds it into a data frame
    with each officer getting their own row"""
    officers_cols = ["EIN", "ObjectId", "OrganizationName", "TaxYr", "StateAbbr", "OfficerList"]
    df_tmp = officers[officers_cols].copy()
    officer_list = pd.DataFrame()
    for i, row in enumerate(df_tmp.itertuples()):
        if row[6] is not None:
            tbl = row[6]
            tmp = json_normalize(tbl)
            tmp["EIN"] = row[1]
            tmp["ObjectId"] = row[2]
            tmp["OrganizationName"] = row[3]
            tmp["TaxYr"] = row[4]
            tmp["StateAbbr"] = row[5]
            officer_list = officer_list.append(tmp, sort=False)
        if i % 500 == 0:
            print(f"Parsed {str(i)} of {str(len(df_tmp))}: {str(100. * i/len(df_tmp))}%")

    print(f"Number of officers with PersonNm: {officer_list['PersonNm'].notnull().sum()}")
    print(f"Number of officers with PersonNm: {officer_list['BusinessName.BusinessNameLine1Txt'].notnull().sum()}")
    print(f"Number of officers with PersonNm: {officer_list['BusinessName.BusinessNameLine1'].notnull().sum()}")

    # Consolidate Parsing Quirks
    names = np.where(
        officer_list["PersonNm"].isnull(),
        officer_list["BusinessName.BusinessNameLine1Txt"],
        officer_list["PersonNm"])
    names = np.where(pd.Series(names).isnull(), officer_list["BusinessName.BusinessNameLine1"], names)
    officer_list["PersonNm"] = names

    del officer_list['BusinessName.BusinessNameLine1Txt']
    del officer_list['BusinessName.BusinessNameLine2Txt']
    del officer_list['BusinessName.BusinessNameLine1']
    del officer_list['BusinessName.BusinessNameLine2']

    column_order = [
        'EIN', 'ObjectId', 'OrganizationName', 'TaxYr', 'StateAbbr',
        'PersonNm', 'TitleTxt', 'AverageHoursPerWeekRt',
        'ReportableCompFromOrgAmt', 'OtherCompensationAmt',
        # Other org
        'ReportableCompFromRltdOrgAmt', 'AverageHoursPerWeekRltdOrgRt',
        # Flags
        'IndividualTrusteeOrDirectorInd', 'OfficerInd',
        'HighestCompensatedEmployeeInd', 'FormerOfcrDirectorTrusteeInd',
        'KeyEmployeeInd', 'InstitutionalTrusteeInd']

    # Binarize the Position Type
    type_cols = [
        'IndividualTrusteeOrDirectorInd', 'HighestCompensatedEmployeeInd',
        'FormerOfcrDirectorTrusteeInd', 'KeyEmployeeInd',
        'InstitutionalTrusteeInd', 'OfficerInd']

    for col in type_cols:
        officer_list[col] = np.where(officer_list[col] == 'X', True, False)

    # Convert Number Columns from String to Float
    num_cols = [
        "AverageHoursPerWeekRt", "ReportableCompFromOrgAmt", "OtherCompensationAmt",
        "ReportableCompFromRltdOrgAmt", "AverageHoursPerWeekRltdOrgRt"]
    for col in num_cols:
        officer_list[col] = officer_list[col].fillna(0).astype(float)

    # Caps Names
    officer_list["PersonNm"] = officer_list["PersonNm"].apply(lambda x: x.upper())

    # Deal with Titles
    officer_list["TitleTxt"] = officer_list["TitleTxt"].apply(lambda x: x.upper())

    df_officer = officer_list[column_order].copy()
    df_officer["TotalCompFromOrgAmt"] = df_officer["ReportableCompFromOrgAmt"] + df_officer["OtherCompensationAmt"]

    return df_officer


if __name__ == "__main__":
    # Runtime
    client = irs.Client(
        local_data_dir="../../data", ein_filename="eins",
        index_years=[2016, 2017, 2018], save_xml=False,
        parser="base")
    client.parse_xmls(add_organization_info=True)
    df = client.getFinalDF()

    officers = df[[
        "EIN", "ObjectId", "OrganizationName", "TaxYr", "StateAbbr", "Mission",
        "OfficerName", "OfficerTitle", "OfficerCompensationPart9",
        "CYTotalExpenses", "OfficerList"]].copy()

    # Add Officer Compensation Percentage of Total Expenses
    officers["OfficerCompensationPct"] = officers["OfficerCompensationPart9"] / officers["CYTotalExpenses"]

    # Parse Officer List
    df_officers = parse_officer_list(officers)
