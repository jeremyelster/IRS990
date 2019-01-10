import os
import sqlite3

DEFAULT_PATH = '../data/database.sqlite3'


class DBConnect:

    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def initialize_db(self):

        self.cur.execute("DROP TABLE IF EXISTS officer_payment")
        self.cur.execute("DROP TABLE IF EXISTS officer_org")
        self.cur.execute("DROP TABLE IF EXISTS schedule_j")
        self.cur.execute("DROP TABLE IF EXISTS irs_base")
        self.cur.execute("DROP TABLE IF EXISTS grants")

        self.cur.execute(officer_payment_sql)
        self.cur.execute(schedule_j_sql)
        self.cur.execute(irs_main_sql)
        self.cur.execute(grants_sql)

    def saveDF(self, df_pandas, table, insert="replace", index=False):
        df_pandas.to_sql(table, con=self.con, if_exists=insert, index=index)

    def query(self, sqlStr):
        df = pd.read_sql(sqlStr, con=self.con)
        return df


officer_payment_sql = """
    CREATE TABLE officer_payment (
        EIN text PRIMARY KEY,
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

schedule_j_sql = """
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

grants_sql = """
CREATE TABLE grants (
    EIN text,
    ObjectId text,
    OrganizationName text,
    TaxYr text,
    Address text,
    City text,
    StateAbbr text,
    RecipientEIN text,
    RecipientBusinessName_BusinessNameLine1Txt text,
    PurposeOfGrantTxt text,
    CashGrantAmt float,
    NonCashAssistanceAmt float,
    NonCashAssistanceDesc text,
    IRCSectionDesc text,
    USAddress_CityNm text,
    USAddress_StateAbbreviationCd text,
    ForeignAddress_AddressLine1Txt text,
    ForeignAddress_CountryCd text)"""

if __name__ == "__main__":
    # create a default path to connect to and create (if necessary) a database
    # called 'database.sqlite3' in the same directory as this script
    DEFAULT_PATH = '../data/database.sqlite3'

    con = db_connect()
    initialize_db(con)