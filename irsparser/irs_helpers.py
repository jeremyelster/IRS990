from os.path import join
import pandas as pd
import xmltodict


def xml_parser3(content, parser="base"):
    xml_attribs = True
    d = xmltodict.parse(content, xml_attribs=xml_attribs)
    version = d["Return"]["@returnVersion"]

    if parser == "propublica":
        important_things = propublicaParser(d)
    else:
        important_things = base_parser(d, version)

    important_things.update(get_header(d))

    return important_things


def get_header(d):

    header = d.get('Return').get("ReturnHeader")
    if header.get("Filer").get("USAddress", False):
        address = (
            header.get("Filer").get("USAddress").get("AddressLine1Txt", False))
        if not address:
            address = (
                header.get("Filer").get("USAddress").get("AddressLine1", None))
        city_abbr = (
            header.get("Filer").get("USAddress").get("CityNm", False))
        if not city_abbr:
            city_abbr = (
                header.get("Filer").get("USAddress").get("City", False))
        state_abbr = (
            header.get("Filer").get("USAddress").get("StateAbbreviationCd", False))
        if not state_abbr:
            state_abbr = (
                header.get("Filer").get("USAddress").get("State", None))

        country_abbr = "US"
    elif header.get("Filer").get("ForeignAddress", False):
        address = None
        city_abbr = header.get("Filer").get("ForeignAddress").get("CityNm")
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
        "Address": address,
        "City": city_abbr,
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


def base_parser(d, version):

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


def propublicaParser(d):
    irs990 = d.get("Return").get("ReturnData").get("IRS990")

    # Revenue
    cy_total_rev = float(irs990.get("CYTotalRevenueAmt", 0))
    cy_total_exp = float(irs990.get("CYTotalExpensesAmt", 0))
    cy_rev_less_exp = float(irs990.get("CYRevenuesLessExpensesAmt", 0))
    total_assets_eoy = float(irs990.get("TotalAssetsEOYAmt", 0))
    total_liabilities_eoy = float(irs990.get("TotalLiabilitiesEOYAmt", 0))

    # Propublica Revenue Sources
    cy_contributions = float(irs990.get("CYContributionsGrantsAmt", 0))
    cy_program_rev = float(irs990.get("CYProgramServiceRevenueAmt", 0))
    cy_investment = float(irs990.get("InvestmentIncomeGrp", {}).get("TotalRevenueColumnAmt", 0))
    cy_bond = float(irs990.get("IncmFromInvestBondProceedsGrp", {}).get("TotalRevenueColumnAmt", 0))
    cy_royalties = float(irs990.get("RoyaltiesRevenueGrp", {}).get("TotalRevenueColumnAmt", 0))
    cy_rental_property = float(irs990.get("NetRentalIncomeOrLossGrp", {}).get("TotalRevenueColumnAmt", 0))
    cy_fundraising_rev = float(irs990.get("NetIncmFromFundraisingEvtGrp", {}).get("TotalRevenueColumnAmt", 0))
    cy_sale_assets = float(irs990.get("CYInvestmentIncomeAmt", 0))
    cy_net_inventory = float(irs990.get("IncmFromInvestBondProceedsGrp", {}).get("TotalRevenueColumnAmt", 0))
    cy_other_rev = float(irs990.get("OtherRevenueTotalAmt", 0))

    # Propublica Expenses Sources
    cy_executive_comp = float(irs990.get("CompCurrentOfcrDirectorsGrp", {}).get("TotalAmt", 0))
    fundraise = irs990.get("FeesForServicesProfFundraising", None)
    if fundraise is not None:
        cy_fundraising_exp = float(fundraise.get("TotalAmt", 0))
    else:
        cy_fundraising_exp = 0
    cy_other_salary = float(irs990.get("OtherSalariesAndWagesGrp", {}).get("TotalAmt", 0))
    cy_program_exp = float(irs990.get("TotalProgramServiceExpensesAmt", 0))

    val_dict = {
        "TotalRevenue": cy_total_rev,
        "TotalExpenses": cy_total_exp,
        "RevenueLessExpenses": cy_rev_less_exp,
        "TotalAssets": total_assets_eoy,
        "TotalLiabilities": total_liabilities_eoy,
        "NetAssets": total_assets_eoy - total_liabilities_eoy,

        # Propublica Revenue Sources
        "Contributions": cy_contributions,
        "ProgramServices": cy_program_rev,
        "InvestmentIncome": cy_investment,
        "BondProceeds": cy_bond,
        "Royalties": cy_royalties,
        "RentalPropertyIncome": cy_rental_property,
        "NetFundraising": cy_fundraising_rev,
        "SalesOfAssets": cy_sale_assets,
        "NetInventorySales": cy_net_inventory,
        "OtherRevenue": cy_other_rev,

        # Propublica Expenses Sources
        "ExecutiveCompensation": cy_executive_comp,
        "ProfessionalFundraisingFees": cy_fundraising_exp,
        "OtherSalaryWages": cy_other_salary,
        "ProgramExpenses": cy_program_exp,
    }

    return val_dict


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
