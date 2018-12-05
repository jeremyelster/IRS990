from os.path import join
import pandas as pd
import xmltodict


def xml_parser3(content):
    xml_attribs = True
    d = xmltodict.parse(content, xml_attribs=xml_attribs)
    version = d["Return"]["@returnVersion"]

    important_things = version_parser(d, version)
    important_things.update(get_header(d))

    return important_things


def get_header(d):

    header = d.get('Return').get("ReturnHeader")
    if header.get("Filer").get("USAddress", False):
        state_abbr = (
            header.get("Filer").get("USAddress").get("StateAbbreviationCd"))
        country_abbr = "US"
    elif header.get("Filer").get("ForeignAddress", False):
        state_abbr = header.get("Filer").get("ForeignAddress").get("CityNm")
        country_abbr = (
            header.get("Filer").get("ForeignAddress").get("CountryCd"))
    else:
        print(header.get("Filer"))

    return {
        "ReturnTs": header.get("ReturnTs"),
        "TaxPeriodEndDt": header.get("TaxPeriodEndDt"),
        "PerparerFirmGrp": (
            header
            .get("PreparerFirmGrp", {})
            .get("PreparerFirmName", {})
            .get("BusinessNameLine1Txt", None)),
        "ReturnTypeCd": header.get("ReturnTypeCd"),
        "TaxPeriodBeginDt": header.get("TaxPeriodBeginDt"),
        "EIN": header.get("Filer").get("EIN"),
        "StateAbbr": state_abbr,
        "CountryAbbr": country_abbr,

        "OfficerName": header.get("BusinessOfficerGrp").get("PersonNm"),
        "OfficerTitle": header.get("BusinessOfficerGrp").get("PersonTitleTxt"),
        "PreparerPersonName": (
            header
            .get("PreparerPersonGrp", {})
            .get("PreparerPersonNm", None)),
        "PreparerDate": (
            header
            .get("PreparerPersonGrp", {})
            .get("PreparationDt", None)),
        "TaxYr": header.get("TaxYr"),
        "BuildTs": header.get("BuildTS"),
    }


def version_parser(d, version):

    if version != "206v3.0":

        return_version = d.get("Return").get("@returnVersion")

        return_data = d.get("Return").get("ReturnData")
        irs990 = d.get("Return").get("ReturnData").get("IRS990")

        # Org Data
        org_type = return_data.get("IRS990ScheduleA", None)
        mission = irs990.get("ActivityOrMissionDesc", None)
        total_employee = irs990.get("TotalEmployeeCnt", 0)
        not_follow_sfas117 = irs990.get("OrgDoesNotFollowSFAS117Ind", None)

        # Revenue
        py_total_rev = float(irs990.get("PYTotalRevenueAmt", 0))
        cy_total_rev = float(irs990.get("CYTotalRevenueAmt", 0))
        py_total_exp = float(irs990.get("PYTotalExpensesAmt", 0))
        cy_total_exp = float(irs990.get("CYTotalExpensesAmt", 0))
        py_rev_less_exp = float(irs990.get("PYRevenuesLessExpensesAmt", 0))
        cy_rev_less_exp = float(irs990.get("CYRevenuesLessExpensesAmt", 0))
        total_assets_boy = float(irs990.get("TotalAssetsBOYAmt", 0))
        total_assets_eoy = float(irs990.get("TotalAssetsEOYAmt", 0))
        total_liabilities_boy = float(irs990.get("TotalLiabilitiesBOYAmt", 0))
        total_liabilities_eoy = float(irs990.get("TotalLiabilitiesEOYAmt", 0))

        # Grants
        grant_money_total = irs990.get("GrantAmt", 0)
        grant_desc = irs990.get("Desc", None)
        program_expenses = irs990.get("TotalProgramServiceExpensesAmt", 0)
        schedule_i = return_data.get("IRS990ScheduleI", None)

        # People in charge
        officer_list = irs990.get("Form990PartVIISectionAGrp", None)
        officer_comp_part_9 = float(
            irs990.get("CompCurrentOfcrDirectorsGrp", {}).get("TotalAmt", 0))
        officer_comp_part_7 = float(
            irs990.get("TotalReportableCompFromOrgAmt", 0))
        schedule_j = return_data.get("IRS990ScheduleJ", None)
        # Misc
        addtl_info = return_data.get("IRS990ScheduleO", None)
        loans_from_officer_boy = float(
            irs990.get("LoansFromOfficersDirectorsGrp", {}).get("BOYAmt", 0))
        loans_from_officer_eoy = float(
            irs990.get("LoansFromOfficersDirectorsGrp", {}).get("EOYAmt", 0))
        loans_to_officer_boy = float(
            irs990.get("ReceivablesFromOfficersEtcGrp", {}).get("BOYAmt", 0))
        loans_to_officer_eoy = float(
            irs990.get("ReceivablesFromOfficersEtcGrp", {}).get("EOYAmt", 0))
        schedule_l = return_data.get("IRS990ScheduleL", None)

        # Metrics
        program_services = float(
            irs990.get("TotalFunctionalExpensesGrp", {})
            .get("ProgramServicesAmt", 0))
        total_fn_expenses = float(
            irs990.get("TotalFunctionalExpensesGrp", {}).get("TotalAmt", 0))
        if total_fn_expenses == 0:
            program_exp = 0
        else:
            program_exp = program_services / total_fn_expenses
            # TOTAL AMT ON PROGRAM SHOULD BE ABOVE 75%

        if total_assets_eoy == 0:
            liabilities_to_asset = 0
        else:
            liabilities_to_asset = total_liabilities_eoy / total_assets_eoy
            # defined previously

        unres_net_assets = float(
            irs990.get("UnrestrictedNetAssetsGrp", {}).get("EOYAmt", 0))
        temp_rstr_net_assets = float(
            irs990.get("TemporarilyRstrNetAssetsGrp", {}).get("EOYAmt", 0))
        if total_fn_expenses == 0:
            working_capital = 0
        else:
            working_capital = (
                (unres_net_assets + temp_rstr_net_assets) / total_fn_expenses)

        total_net_assets_eoy = float(
            irs990.get("TotalNetAssetsFundBalanceGrp", {}).get("EOYAmt", 0))
        total_net_assets_boy = float(
            irs990.get("TotalNetAssetsFundBalanceGrp", {}).get("BOYAmt", 0))
        if cy_total_rev == 0:
            surplus_margin = 0
        else:
            surplus_margin = (
                (total_net_assets_eoy - total_net_assets_boy) / cy_total_rev)

        total_expenses = total_fn_expenses

    important_things = {
        "returnVersion": return_version,

        # Org Data
        "ScheduleA": org_type,
        "Mission": mission,
        "TotalEmployee": total_employee,
        "NotFollowSFAS117": not_follow_sfas117,

        # Revenue
        "PYTotalRevenue": py_total_rev,
        "CYTotalRevenue": cy_total_rev,
        "PYTotalExpenses": py_total_exp,
        "CYTotalExpenses": cy_total_exp,
        "PYRevenuesLessExpenses": py_rev_less_exp,
        "CYRevenuesLessExpenses": cy_rev_less_exp,
        "TotalAssetsBOY": total_assets_boy,
        "TotalAssetsEOY": total_assets_eoy,
        "TotalLiabilitiesBOY": total_liabilities_boy,
        "TotalLiabilitiesEOY": total_liabilities_eoy,

        # Grants
        "GrantMoneyTotal": grant_money_total,
        "GrantDesc": grant_desc,
        "ProgramExpenses": program_expenses,
        "ScheduleI": schedule_i,

        # People in charge
        "ScheduleJ": schedule_j,
        "OfficerCompensationPart7": officer_comp_part_7,
        "OfficerCompensationPart9": officer_comp_part_9,
        "OfficerList": officer_list,

        # Misc
        "ScheduleO": addtl_info,
        "ScheduleL": schedule_l,
        "LoansToOfficerBOY": loans_to_officer_boy,
        "LoansToOfficerEOY": loans_to_officer_eoy,
        "LoansFromOfficerBOY": loans_from_officer_boy,
        "LoansFromOfficerEOY": loans_from_officer_eoy,

        # Metrics
        "ProgramExp": program_exp,
        "LiabilitiesToAsset": liabilities_to_asset,
        "WorkingCapital": working_capital,
        "SurplusMargin": surplus_margin,
        "TotalExpenses": total_expenses
    }
    return important_things


def getOrgProfiles(eins, local_dir=None):

    # NTEE Values
    df = pd.DataFrame()
    for eo in ["eo1.csv", "eo2.csv", "eo3.csv", "eo4.csv"]:
        filename = join(local_dir, eo)
        tmp = pd.read_csv(
            filename,
            usecols=[
                "EIN", "NTEE_CD", "DEDUCTIBILITY",
                "FOUNDATION", "ORGANIZATION"],
            dtype={"EIN": str})
        tmp["EIN"] = tmp["EIN"].astype(str)
        tmp.index = tmp.index.astype(str)
        tmp_sub = tmp.loc[tmp["EIN"].isin(eins), :].copy()
        df = df.append(tmp_sub)

    # NTEE Common Codes
    filename = join(local_dir, 'ntee_common_codes.csv')
    tmp = pd.read_csv(filename, index_col="Code")
    ntee_common_codes = tmp.to_dict().get("Description")
    df["NTEE_COMMON"] = (
        df["NTEE_CD"]
        .apply(lambda x: commonNTEEparser(str(x)[0:3], ntee_common_codes)))

    # NTEE Descriptions
    filename = join(local_dir, "ntee_codes_descr.csv")
    tmp = pd.read_csv(filename, index_col="Code")
    ntee_names = tmp.to_dict().get("Description")
    df["NTEE_DESCR"] = (
        df["NTEE_CD"].apply(lambda x: descNTEEparser(str(x)[0:3], ntee_names)))

    # Deductibility
    df["DEDUCTIBILITY"] = df["DEDUCTIBILITY"].apply(deductibilityParser)

    # Foundation
    filename = join(local_dir, 'foundation_codes.csv')
    tmp = pd.read_csv(filename, index_col="Code")
    foundation_codes = tmp.to_dict().get("Description")
    df["FOUNDATION"] = df["FOUNDATION"].map(foundation_codes)

    # Organization
    df["ORGANIZATION"] = df["ORGANIZATION"].apply(organizationParser)

    df.rename(
        columns={
            "DEDUCTIBILITY": "Deductibility", "ORGANIZATION": "Organization",
            "FOUNDATION": "Foundation", "NTEE_COMMON": "NTEECommonCode",
            "NTEE_CD": "NTEECode", "NTEE_DESCR": "NTEECodeDescription"},
        inplace=True)
    return df


def descNTEEparser(code, d):
    if code is None:
        return None
    else:
        return d.get(str(code)[0:3])


def commonNTEEparser(code, d):
    if code is None:
        return None
    else:
        return d.get(str(code)[0:1])


def deductibilityParser(code):
    if (code is None) | (code == 0):
        return None
    elif code == 1:
        return "Deductible"
    elif code == 2:
        return "Not Deductible"
    elif code == 4:
        return "Deductible by Treaty"
    else:
        return code


def organizationParser(code):
    if code is None:
        return None
    elif code == 1:
        return "Corporation"
    elif code == 2:
        return "Trust"
    elif code == 3:
        return "Co-operative"
    elif code == 4:
        return "Partnership"
    elif code == 5:
        return "Association"
    else:
        return code


def testing_object_id(obj_id):
    # Testing

    fname = join("xml_files", obj_id + ".xml")
    with open(fname, "rb") as f:
        txt = f.read()
        d2 = xml_parser3(txt)
        d = xmltodict.parse(txt)
    # d.get("Return").get("ReturnData").get()
    return d2, d
