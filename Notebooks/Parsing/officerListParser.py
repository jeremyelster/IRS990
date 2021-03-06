import pandas as pd
import numpy as np
from pandas.io.json import json_normalize
import flatten_json
import sys
import irsparser as irs
sys.path.append("../../")


def parse_officer_list(df):
    """Parse the Officer List and build new dataframe officer_list

    Takes the OfficerList column returned from IRS990 and builds it into a data frame
    with each officer getting their own row"""
    officers_cols = ["EIN", "ObjectId", "OrganizationName", "TaxYr", "StateAbbr", "OfficerList"]
    df_tmp = df[officers_cols].copy()
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
            print(f"Parsed {str(i)} of {str(len(df_tmp))}: {str(round(100. * i/len(df_tmp), 2))}%")

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
    officer_list["TitleTxt"] = officer_list["TitleTxt"].apply(lambda x: str(x).upper())

    df_officer = officer_list[column_order].copy()
    df_officer["TotalCompFromOrgAmt"] = df_officer["ReportableCompFromOrgAmt"] + df_officer["OtherCompensationAmt"]
    df_officer.reset_index(inplace=True, drop=True)

    return df_officer

def get_bool(x):

    if (x == "true") | (x == "1"):
        return 1
    elif (x == "false") | (x == "0") | (x is None):
        return 0
    else:
        print(f"Error: {x}")
        return x

def parse_schedule_j(df):
    officers = []
    df_tmp = df[["EIN", "ObjectId", "OrganizationName", "TaxYr", "StateAbbr", "ScheduleJ"]].copy()

    for row in df_tmp.itertuples():
        if row[6] is not None:

            tmp = {}
            tmp["EIN"] = row[1]
            tmp["ObjectId"] = row[2]
            tmp["OrganizationName"] = row[3]
            tmp["TaxYr"] = row[4]
            tmp["StateAbbr"] = row[5]

            d = row[6]

            tmp["SeverancePaymentInd"] = d.get("SeverancePaymentInd", None)
            tmp["TravelForCompanionsInd"] = d.get("TravelForCompanionsInd", None)

            tbl = d.get("RltdOrgOfficerTrstKeyEmplGrp", False)
            if tbl:
                if isinstance(tbl, dict):
                    # If its the only element in table, put it in a list to iterate over
                    tmp2 = []
                    tmp2.append(tbl)
                    tbl = tmp2
                for officer in tbl:
                    tmp_officer = flatten_json.flatten(officer)
                    tmp_officer.update(tmp)
                    officers.append(tmp_officer)
        else:
            tmp = {}

    df = pd.DataFrame(officers)

    id_cols = [
        'EIN', 'ObjectId', 'OrganizationName', 'StateAbbr', 'TaxYr',
        'PersonNm', 'TitleTxt']

    comp_cols = [
        'TotalCompensationFilingOrgAmt',
        'BaseCompensationFilingOrgAmt', 'BonusFilingOrganizationAmount',
        'OtherCompensationFilingOrgAmt', 'DeferredCompensationFlngOrgAmt',
        'NontaxableBenefitsFilingOrgAmt', 'TotalCompensationRltdOrgsAmt',
        'OtherCompensationRltdOrgsAmt', 'BonusRelatedOrganizationsAmt',
        'CompensationBasedOnRltdOrgsAmt', 'DeferredCompRltdOrgsAmt',
        'NontaxableBenefitsRltdOrgsAmt', 'CompReportPrior990FilingOrgAmt',
        'CompReportPrior990RltdOrgsAmt']

    other_cols = ['BusinessName_BusinessNameLine1',
        'BusinessName_BusinessNameLine1Txt', 'BusinessName_BusinessNameLine2',
        'SeverancePaymentInd', 'TravelForCompanionsInd']

    # Reorganize Columns
    df = df[id_cols + comp_cols + other_cols].copy()

    # Upper Case Name and Title
    df["PersonNm"] = df["PersonNm"].apply(lambda x: str(x).upper())
    df["TitleTxt"] = df["TitleTxt"].apply(lambda x: str(x).upper())
    df["BusinessName_BusinessNameLine1"] = df["BusinessName_BusinessNameLine1"].apply(lambda x: str(x).upper())
    df["BusinessName_BusinessNameLine1Txt"] = df["BusinessName_BusinessNameLine1Txt"].apply(lambda x: str(x).upper())

    # Fill null values for compensation with 0
    for col in comp_cols:
        df[col] = df[col].fillna(0).astype(float)

    # See if there is a severance payment
    df["SeverancePaymentInd"] = df["SeverancePaymentInd"].apply(get_bool)

    # Replace NA Names with Business Values where appropriate
    df["PersonNm"] = np.where(
        df["PersonNm"] == "NAN",
        df["BusinessName_BusinessNameLine1"],
        df["PersonNm"])

    df["PersonNm"] = np.where(
        df["PersonNm"] == "NAN",
        df["BusinessName_BusinessNameLine1Txt"],
        df["PersonNm"])

    del df["BusinessName_BusinessNameLine1Txt"]
    del df["BusinessName_BusinessNameLine1"]
    del df["BusinessName_BusinessNameLine2"]

    return df


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
        "CYTotalExpenses"]].copy()

    # Caps Names
    officers["OfficerName"] = officers["OfficerName"].apply(lambda x: x.upper())
    # Deal with Titles
    officers["OfficerTitle"] = officers["OfficerTitle"].apply(lambda x: str(x).upper())
    # Add Officer Compensation Percentage of Total Expenses
    tmp_val = officers["OfficerCompensationPart9"] / officers["CYTotalExpenses"]
    officers.loc[:, "OfficerCompensationPct"] = tmp_val.copy()

    # Parse Officer List Form990PartVIISectionAGrp
    df_officers = parse_officer_list(officers)

    # Parse Schedule J
    df_schedulej = parse_schedule_j(df)

    # Dump to SQL
    con = irs.db_connect()
    cur = con.cursor()
    irs.initialize_db(con)

    officers.to_sql("officer_org", con=con, if_exists="replace", index=False)
    df_officers.to_sql("officer_payment", con=con, if_exists="replace", index=False)
    df_schedulej.to_sql("schedule_j", con-con, if_exists="replace", index=False)

