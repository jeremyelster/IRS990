import os
import sqlite3

DEFAULT_PATH = '../data/database.sqlite3'

def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con

def initialize_db(con):
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS officer_payment")
    cur.execute("DROP TABLE IF EXISTS officer_org")
    cur.execute("DROP TABLE IF EXISTS schedule_j")
    cur.execute("DROP TABLE IF EXISTS irs_main_sql")

    cur.execute(officer_org)
    cur.execute(officer_payment)
    cur.execute(schedule_j)
    cur.execute(irs_main_sql)


officer_payment = """
    CREATE TABLE officer_payment (
        EIN text PRIMARY KEY
        ObjectId text,
        OrganizationName text,
        TaxYr text,
        StateAbbr text,
        PersonNm text,
        TitleTxt text,
        AverageHoursPerWeekRt float,
        ReportableCompFromOrgAmt float,
        OtherCompensationAmt float,
        ReportableCompFromRltdOrgAmt float,
        AverageHoursPerWeekRltdOrgRt float,
        IndividualTrusteeOrDirectorInd bool,
        OfficerInd bool,
        HighestCompensatedEmployeeInd bool,
        FormerOfcrDirectorTrusteeInd bool,
        KeyEmployeeInd bool,
        InstitutionalTrusteeInd bool,
        TotalCompFromOrgAmt float)"""

officer_org = """
CREATE TABLE officer_org (
    EIN text PRIMARY KEY,
    ObjectId text,
    OrganizationName text,
    TaxYr text,
    StateAbbr text,
    Mission text,
    OfficerName text,
    OfficerTitle text,
    OfficerCompensationPart9 float,
    CYTotalExpenses float,
    OfficerCompensationPct float)"""

schedule_j = """
CREATE TABLE (
    EIN text,
    ObjectId text,
    OrganizationName text,
    StateAbbr text,
    TaxYr text,
    PersonNm text,
    TitleTxt text,
    TotalCompensationFilingOrgAmt float,
    BaseCompensationFilingOrgAmt float,
    BonusFilingOrganizationAmount float,
    OtherCompensationFilingOrgAmt float,
    DeferredCompensationFlngOrgAmt float,
    NontaxableBenefitsFilingOrgAmt float,
    TotalCompensationRltdOrgsAmt float,
    OtherCompensationRltdOrgsAmt float,
    BonusRelatedOrganizationsAmt float,
    CompensationBasedOnRltdOrgsAmt float,
    DeferredCompRltdOrgsAmt float,
    NontaxableBenefitsRltdOrgsAmt float,
    CompReportPrior990FilingOrgAmt float,
    CompReportPrior990RltdOrgsAmt float,
    SeverancePaymentInd bool,
    TravelForCompanionsInd text)"""

irs_main_sql = """
CREATE TABLE irs_base (
    EIN text PRIMARY KEY,
    TaxPeriod text NOT NULL,
    DLN text NOT NULL,
    FormType text NOT NULL,
    LastUpdate text NOT NULL,
    ObjectId text NOT NULL,
    OrganizationName text NOT NULL,
    SubmittedOn text NOT NULL,
    URL text NOT NULL,
    BondProceeds text,
    BuildTs text,
    Contributions text,
    CountryAbbr text,
    ExecutiveCompensation text,
    InvestmentIncome text,
    NetAssets text,
    NetFundraising text,
    NetInventorySales text,
    OfficerName text,
    OfficerTitle text,
    OtherRevenue text,
    OtherSalaryWages text,
    PerparerFirmGrp text,
    PreparerDate text,
    PreparerPersonName text,
    ProfessionalFundraisingFees text,
    ProgramExpenses text,
    ProgramServices text,
    RentalPropertyIncome text,
    ReturnTs text,
    ReturnTypeCd text,
    RevenueLessExpenses text,
    Royalties text,
    SalesOfAssets text,
    StateAbbr text,
    TaxPeriodBeginDt text, 
    TaxPeriodEndDt text,
    TaxYr text, 
    TotalAssets text,
    TotalExpenses text
    TotalLiabilities text,
    TotalRevenue text,
    Deductibility text,
    Foundation text,
    Organization text,
    NTEECode text,
    NTEECommonCode text,
    NTEECodeDescription text)"""

if __name__ == "__main__":
    # create a default path to connect to and create (if necessary) a database
    # called 'database.sqlite3' in the same directory as this script
    DEFAULT_PATH = '../data/database.sqlite3'

    con = db_connect()
    initialize_db(con)