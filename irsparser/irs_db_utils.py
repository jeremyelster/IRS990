import sqlite3
import pandas as pd


class DBConnect:

    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def initialize_db(self):

        self.cur.execute("DROP TABLE IF EXISTS officer_payment")
        self.cur.execute("DROP TABLE IF EXISTS schedule_j")
        self.cur.execute("DROP TABLE IF EXISTS irs_dashboard")
        self.cur.execute("DROP TABLE IF EXISTS grants")

        self.cur.execute(officer_payment_sql)
        self.cur.execute(schedule_j_sql)
        self.cur.execute(irs_dashboard_sql)
        self.cur.execute(grants_sql)

    def saveDF(self, df_pandas, table, insert="replace", index=False):
        df_pandas.to_sql(table, con=self.con, if_exists=insert, index=index)

    def query(self, sqlStr):
        df = pd.read_sql(sqlStr, con=self.con)
        return df


irs_dashboard_sql = """
CREATE TABLE irs_dashboard (
    EIN text,
    URL text,
    LastUpdated text,
    OrganizationName text,
    TaxPeriod text,
    TaxPeriodBeginDt text,
    TaxPeriodEndDt text,
    TaxYr text,
    StateAbbr text,
    Mission text,
    TotalEmployee text,
    ObjectId text,
    NTEECommonCode text,
    Foundation text,
    OfficerName text,
    OfficerTitle text,
    OfficerCompensationPart9 float,
    GrantDesc text,
    GrantMoneyTotal float,
    ProgramExpenses float,
    PYTotalRevenue float,
    CYTotalRevenue float,
    PYRevenuesLessExpenses float,
    CYRevenuesLessExpenses float,
    TotalAssetsBOY float,
    TotalAssetsEOY float,
    TotalLiabilitiesBOY float,
    TotalLiabilitiesEOY float,
    TotalExpenses float,
    CYTotalExpenses float,
    PYTotalExpenses float,
    WorkingCapital float,
    LiabilitiesToAsset float,
    SurplusMargin float,
    ProgramExp float,
    ScheduleA text,
    ScheduleJ text,
    ScheduleI text,
    ScheduleO text)"""

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
CREATE TABLE schedule_j (
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

