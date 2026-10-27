 PLUTO README DOCUMENT                                                      August 2026 (26v2)


                                      WHAT IS PLUTO™?

The Primary Land Use Tax Lot Output (PLUTO™) data file contains extensive land use and
geographic data at the tax lot level in an ASCII comma-delimited file.

The PLUTO tax lot data files contain over seventy data fields derived from data files maintained
by the Department of City Planning (DCP), Department of Finance (DOF), Department of
Citywide Administrative Services (DCAS), and Landmarks Preservation Commission (LPC).
DCP has created additional fields based on data obtained from one or more of the major data
sources. PLUTO data files contain three basic types of data:

       ●       Tax Lot Characteristics;
       ●       Building Characteristics; and
       ●       Geographic/Political/Administrative Districts.

There are two idiosyncrasies regarding the tax lot data. The PLUTO data contain one record
per tax lot except for condominiums. PLUTO data contain one record per condominium
complex instead of records for each condominium unit tax lot. A tax lot is usually a parcel of
real property. The parcel can be under water, vacant, or contain one or more buildings or
structures. The Department of Finance assigns a tax lot number to each condominium unit and
a "billing" tax lot number to the Condominium Complex. A Condominium Complex is defined as
one or more structures or properties under the auspices of the same condominium association.
DCP summarizes DOF's condominium unit tax lot data so that each Condominium Complex
within a tax block is represented by only one record. The Condominium Complex record is
assigned the "billing" tax lot number when one exists. When the "billing" tax lot number has not
yet been assigned by DOF, the lowest tax lot number within the tax block of the Condominium
Complex is assigned.

The second idiosyncrasy is related to borough and community district geography. Two portions
of the City, Marble Hill and Rikers Island, are legally located in one borough but are serviced by
another borough. Specifically, Marble Hill is legally located in Manhattan but is serviced by the
Bronx, while Rikers Island is legally part of the Bronx but is serviced by Queens.

There are two types of PLUTO updates: major and minor. Major updates occur quarterly, and
all fields are updated. A major update is represented first digit in the version number after “v,”
for example 24v1. Minor updates are released monthly between major updates and only
include updates to the zoning attributes. A minor release is represented by the decimal after the
version number – 24v1.1, 24v1.2, etc. The following fields are updated in a minor release:

                      ZoneDist1              SPDist1                CommFAR
                      ZoneDist2              SPDist2                FacilFAR
                      ZoneDist3              SPDist3                ZoneMap
                      ZoneDist4              LtdHeight              ZMCode
                      Overlay1               SplitZone              TaxMap
                      Overlay2               ResidFAR               EDesigNum




                                              1 of 16
 PLUTO README DOCUMENT                                                      August 2026 (26v2)

Check the City Planning web site, www.nyc.gov/planning for update status. The date of the
source data files and the base map used to create this version are:




DATES OF DATA

 SOURCE                                                                     DATE OF DATA
 Department of City Planning – E-Designations                               2026-07-07
 Department of City Planning – Zoning Map Index                             2019-07-01
 Department of City Planning – NYC City Owned and Leased Properties         2026-04-30
 Department of City Planning – NYC GIS Zoning Features                      2026-07-31
 Department of City Planning – Political and Administrative Districts 26C   2026-08-17
 Department of City Planning – Geosupport version 26C                       2026-08-17
 Department of Finance – Digital Tax Map (DTM)                              2026-07-31
 Department of Finance – Mass Appraisal System (CAMA)                       2026-07-29
 Department of Finance – Property Tax System (PTS)                          2026-07-29
 Department of Parks and Recreation – GreenThumb Garden Info                2026-07-29
 Landmarks Preservation Commission – Individual Landmark and                2026-02-03
 Historic District Building Database
 Landmarks Preservation Commission – Individual Landmarks                   2026-06-18
 Office of Technology & Innovation – Building Footprint Centroids           2026-08-03


City Planning also merges the PLUTO data with the DCP modified version of the DOF’s Digital
tax map to create MapPLUTO for use with various geographic information systems.

PLUTO is being provided by the Department of City Planning (DCP) on DCP’s website for
informational purposes only. DCP does not warranty the completeness, accuracy,
content, or fitness for any particular purpose or use of PLUTO, nor are any such
warranties to be implied or inferred with respect to PLUTO as furnished on the website.

DCP and the City are not liable for any deficiencies in the completeness, accuracy,
content, or fitness for any particular purpose or use of PLUTO, or applications utilizing
PLUTO, provided by any third party.

If you have any questions concerning the data, please email DCPOpendata@planning.nyc.gov




                                               2
 PLUTO README DOCUMENT                                                      August 2026 (26v2)


                                APPENDIX: CHANGE HISTORY
                                    CHANGES IN PLUTO

                          BETWEEN PLUTO26v2 AND PLUTO26v1

New ZONING DISTRICT values:

       M1-8A/R9-1

Removed ZONING DISTRICT values:

       M1-8A/R9X

                          BETWEEN PLUTO26v1 AND PLUTO25v4

New fields:
  • MANDATORY INCLUSIONARY HOUSING OPTION 1 (MIHOption1) - Flag set to “1” if
       MIH Option 1 applies to tax lot. Under Option 1, 25 percent of the residential floor area
       must be affordable to households earning an average of 60 percent of Area Median
       Income, of which 10 percent shall be affordable to families earning 40 percent of Area
       Median Income.

   •   MANDATORY INCLUSIONARY HOUSING OPTION 2 (MIHOption2) - Flag set to “1” if
       MIH Option 2 applies to tax lot. Under Option 2, 30 percent of the residential floor area
       must be affordable to households earning an average of 80 percent of Area Median
       Income.

   •   MANDATORY INCLUSIONARY HOUSING OPTION 3 (MIHOption3) - Flag set to “1” if
       MIH Option 3 (deep affordability) applies to tax lot. Under Option 3, 20 percent of the
       residential floor area must be affordable to households earning an average of 40 percent
       of Area Median Income.

   •   MANDATORY INCLUSIONARY HOUSING OPTION 4 (MIHOption4) - Flag set to “1” if
       MIH Option 4 (workforce option) applies to tax lot. Under Option 4, 30 percent of the
       residential floor area must be affordable to families earning an average of 115 percent of
       Area Median Income, of which 5 percent must be affordable to families earning 90
       percent of Area Median Income and another 5 percent must be affordable to families
       earning 70 percent of Area Median Income.

   •   TRANSIT ZONE (TrnstZone) – The Transit Zone classification of the tax lot. Under the
       Zoning Resolution, the map of New York City is apportioned into areas that generally
       govern residential parking. These include the Manhattan Core, LIC Parking Area, and
       Inner Transit Zone, where no residential parking is required. In addition, these include
       the Outer Transit Zone and the area Beyond the Greater Transit Zone where residential
       parking is required.

   •   MAXIMUM ALLOWABLE AFFORDABLE RESIDENTIAL FAR (AffResFAR) - The
       maximum allowable residential floor area ratio for affordable housing, based on the
       zoning district classification occupying the greatest percentage of the tax lot’s area as
       reported in ZoneDist1. If the lot is assigned to more than one zoning district and


                                                3
 PLUTO README DOCUMENT                                                     August 2026 (26v2)


       ZoneDist1 does not allow residential uses, MAXIMUM ALLOWABLE AFFORDABLE
       RESIDENTIAL FAR is based on ZoneDist2, ZoneDist3 or ZoneDist4, in that order.

       The maximum allowable residential floor area ratios are exclusive of bonuses for plazas,
       plaza-connected open areas, arcades, or other amenities.

   •   MAXIMUM ALLOWABLE MANUFACTURING FAR (ManuFAR) - The maximum
       allowable Manufacturing floor area ratio, based on the zoning district classification
       occupying the greatest percentage of the tax lot’s area as reported in ZoneDist1. If the
       lot is assigned to more than one zoning district and ZoneDist1 does not allow
       manufacturing uses, MAXIMUM ALLOWABLE MANUFACTURING FAR is based on
       ZoneDist2, ZoneDist3 or ZoneDist4, in that order.

       The maximum allowable manufacturing floor area ratios are exclusive of bonuses for
       plazas, plaza-connected open areas, arcades, or other amenities.

New ZONING DISTRICT values:

       C6-12


                         BETWEEN PLUTO25v4 AND PLUTO25v3.1

New ZONING DISTRICT values:

       C6-11

Values for the FAR fields and related logic have been fixed to ensure FAR fields are only based
on a lot’s ZONING DISTRICT 1 (ZoneDist1) value. This includes
        MAXIMUM ALLOWABLE RESIDENTIAL FAR (ResidFAR)
        MAXIMUM ALLOWABLE COMMERCIAL FAR (CommFAR)
        MAXIMUM ALLOWABLE COMMUNITY FACILITY FAR (FacilFAR)

                         BETWEEN PLUTO25v3.1 AND PLUTO25v3

New ZONING DISTRICT values:

       C7-1
       M1-2A/R7A
       M1-2A/R7-2
       M1-3A/R7A
       M1-3A/R7X
       M1-4A
       M1-4A/R7-2
       M1-4A/R8A
       M1-5A
       M1-5A/R8
       M1-6A
       M1-6A/R9
       M1-6A/R9A
       M1-6A/R10
       M1-8A/R9X
                                                4
 PLUTO README DOCUMENT                                                    August 2026 (26v2)


       M2-3A
       M3-2A

New SPECIAL DISTRICT values:

       MX-30

Removed SPECIAL DISTRICT values:

       MX-9

                         BETWEEN PLUTO25v3 AND PLUTO25v2.1

New ZONING DISTRICT values:

       M1-6A/R8
       M1-8A/R11
       M1-8A/R12
       M1-9A
       M1-9A/R12

Removed ZONING DISTRICT values:

       M1-6D

New SPECIAL DISTRICT values:

       MSX
       MX-27

Removed SPECIAL DISTRICT values:

       GC

HISTORIC DISTRICT NAME (HistDist) – a bug fix was made to the HistDist field, which for
certain records had erroneously specified HistDist as “Individual Landmark”. For individual
landmark information, please see the LANDMARK STATUS (Landmark) field.


                         BETWEEN PLUTO25v2 AND PLUTO25v1.1

New ZONING DISTRICT values:

       M1-1A/R6B
       M1-2A
       M1-2A/R6A
       M1-3/R7D
       M1-3A
       M1-3A/R7D
       M1-4A/R9A

New SPECIAL DISTRICT values:
                                               5
 PLUTO README DOCUMENT                                                     August 2026 (26v2)



       AAM
       MX-26

Removed SPECIAL DISTRICT values:

       MX-20


APPORTIONMENT BBL (APPBBL) – logic for determining APPBBL has been updated. If a
condo lot record does not have an APPBBL directly associated with it, PLUTO now assigns an
APPBBL from one of the associated condo unit lots (if one is found).

Values for the FAR fields have been updated for new and existing zoning districts related to the
adoption of the City of Yes initiatives. This includes
       MAXIMUM ALLOWABLE RESIDENTIAL FAR (ResidFAR)
       MAXIMUM ALLOWABLE COMMERCIAL FAR (CommFAR)
       MAXIMUM ALLOWABLE COMMUNITY FACILITY FAR (FacilFAR)

                         BETWEEN PLUTO25v1.1 AND PLUTO25v1

NEW ZONING DISTRICT values:

       R6D

                          BETWEEN PLUTO24v3 AND PLUTO24v2

ZONING DISTRICT 1 (ZoneDist1) character length has been changed from 9 to 12.
ZONING DISTRICT 2 (ZoneDist2) character length has been changed from 9 to 12.
ZONING DISTRICT 3 (ZoneDist3) character length has been changed from 9 to 12.
ZONING DISTRICT 4 (ZoneDist4) character length has been changed from 9 to 12.

NEW ZONING DISTRICT values:

       M1-1A/R7-3
       R6-1

NEW SPECIAL PURPOSE DISTRICT values:
     ETC        Special Eastchester – East Tremont Corridor District


                          BETWEEN PLUTO23v3 AND PLUTO23v2

DATA CHANGES

Corrections

       •   ZONING DISTRICT 1 (ZoneDist1)
           ZONING DISTRICT 2 (ZoneDist2)
           ZONING DISTRICT 3 (ZoneDist3)
           ZONING DISTRICT 4 (ZoneDist4)
           SPECIAL PURPOSE DISTRICT 1 (SPDist1)
                                               6
 PLUTO README DOCUMENT                                                        August 2026 (26v2)


           SPECIAL PURPOSE DISTRICT 2 (SPDist2)
           SPECIAL PURPOSE DISTRICT 3 (SPDist3)
           The logic for calculating the 7 zoning fields listed above has been adjusted to
           account for multipart zoning districts. In previous versions, the percentage of the
           zoning district covering the lot was calculated using each individual zoning polygon,
           and duplicate zoning values on the same tax lot would be removed. Starting with
           this version, the zoning districts are merged into multipart features; therefore, there is
           no need to remove duplicates. The result is now the ZoneDist1 value on a tax lot
           may have changed because with this new method we are accurately capturing the
           zoning district covering the greatest percentage of a tax lot’s area.
           The following zoning related fields are also impacted by this change: ResidFAR,
           CommFAR, FacilFAR.


                                 CHANGES IN PLUTO
                         BETWEEN PLUTO23v1.2 AND PLUTO23v1.1

PLUTO23v1.1 is a minor release and only contains updates to zoning related fields. The
universe of lots and all non-zoning fields are unchanged from version 23v1.

The following zoning related fields are updated for a minor release.

       ZoneDist1                      SPDist1                        CommFAR
       ZoneDist2                      SPDist2                        FacilFAR
       ZoneDist3                      SPDist3                        ZoneMap
       ZoneDist4                      LtdHeight                      ZMCode
       Overlay1                       SplitZone                      TaxMap
       Overlay2                       ResidFAR                       EDesigNum

                                  CHANGES IN PLUTO
                           BETWEEN PLUTO22v3 AND PLUTO22v2

SANBORN MAP # (Sanborn) has been deprecated. This data is no longer considered reliable
and will be removed at a future date.

OWNER NAME (OwnerName) – additional spelling variants of city and state agency names
have been normalized.

                                  CHANGES IN PLUTO
                           BETWEEN PLUTO22v2 AND PLUTO22v1

The geographic features in MapPLUTO come from DOF’s Digital Tax Map (DTM). Because of
timing issues, some BBLs in the DTM will not yet be available in Geosupport. Geosupport is the
source for many fields, including CENSUS TRACT 2020 (BCT2020), COMMUNITY DISTRICT
(CD), SCHOOL DISTRICT (SchoolDist), FIRE COMPANY (FireComp), and other municipal
service areas. When these data are unavailable from Geosupport, MapPLUTO uses the spatial
data from BYTES Districts datasets to calculate a value. The code to do this was broken and
has been fixed with version PLUTO 22v2.

The code to backfill missing values in MapPLUTO has also been enhanced to calculate X
COORDINATE (XCoord), Y COORDINATE (YCoord), LATITUDE (Latitude), and LONGITUDE

                                                  7
 PLUTO README DOCUMENT                                                        August 2026 (26v2)


(Longitude) by using the centroid of the lot, with the constraint that the resulting point must be
within the lot boundaries.

NUMBER OF FLOORS (NumFloors) has been modified to show <null> for values of zero and
for other values of less than one.

OWNER NAME (OwnerName) values that started with punctuation such as commas and
percentage signs has been modified to remove this punctuation.


                                   CHANGES IN PLUTO
                            BETWEEN PLUTO22v1 AND PLUTO21v4

DCP Edits

       In order to improve data quality and consistency, City Planning applies changes to
       selected field values. CHANGE BY DCP is set to “1” if a record contains any changed
       values. The changes made to a tax lot record are records in
       PLUTOChangeFile20v1.csv, which is available as part of the MapPLUTO download on
       BYTES of the BIG APPLETM. The change file contains the BBL; field name; old and new
       values; and the reason that the field was changed.

       YEAR BUILT (YearBuilt) – For ~700 additional buildings, YearBuilt has been changed to
       the date high value from Landmarks Preservation Commission’s Individual Landmark
       and Historic District Building Database. These changes were for lots with more than one
       building on the lot. Changes were made after confirming that all buildings on the lot were
       built in the same year.

New SPECIAL PURPOSE DISTRICT values:
     BNY        Special Brooklyn Navy Yard District
     SNX        Special SoHo-NoHo Mixed Use District


                                   CHANGES IN PLUTO
                            BETWEEN PLUTO21v4 AND PLUTO21v3

New fields

       •      CENSUS TRACT 2020 (BCT2020) – The seven-digit code representing the one-
             digit borough code followed by the six-digit census tract number for one address of
             the tax lot.

       •      CENSUS BLOCK 2020 (BCTCB2020) – The eleven-digit code representing the
             one-digit borough code followed by the six-digit census tract number and then the
             four-digit census block number for one address of the tax lot.

New SPECIAL PURPOSE DISTRICT values:
     MX-23      Special Mixed Use District (MX-23)
     G          Special Gowanus Mixed Use District


                                                 8
 PLUTO README DOCUMENT                                                        August 2026 (26v2)


The sub-area fields, including: ComArea, ResArea, OfficeArea, RetailArea, GarageArea,
StrgeArea, FactryArea, and OtherArea have been updated to reflect all buildings on a lot. In
prior versions, these fields reflected only the primary building in some cases.

DCP Edits

       In order to improve data quality and consistency, City Planning applies changes to
       selected field values. CHANGE BY DCP is set to “1” if a record contains any changed
       values. The changes made to a tax lot record are records in
       PLUTOChangeFile20v1.csv, which is available as part of the MapPLUTO download on
       BYTES of the BIG APPLETM. The change file contains the BBL; field name; old and new
       values; and the reason that the field was changed.

       YEAR BUILT (YearBuilt) – For ~100 buildings, YearBuilt has been changed to the
       date_high value from Landmarks Preservation Commission’s Individual Landmark and
       Historic District Building Database. These changes were primarily in two newly
       designated historic districts, Manida Street Historic District and East 25th Street Historic
       District
                                       CHANGES IN PLUTO
                            BETWEEN PLUTO21v3 AND PLUTO21v2

The sub-area fields, which includes the following fields: ComArea, ResArea, OfficeArea,
RetailArea, GarageArea, StrgeArea, FactryArea, and OtherArea had not been updated since
2019, because the source data for these fields had not been updated since 2019. This issue
has been resolved in 21v3 where the source data has been updated, and subsequently the sub-
area values in PLUTO are up to date as of 2021

                                  CHANGES IN PLUTO
                           BETWEEN PLUTO21v2 AND PLUTO21v1

The SPECIAL PURPOSE DISTRICT value for the Special Flushing Waterfront District has
changed from “WF” to “FW”. For the Coastal Resiliency District, there are now several
numbered districts, so “CR” has been replaced with “CR-1”, “CR-2”, etc.

New SPECIAL PURPOSE DISTRICT values:
     MX-21      Special Mixed Use District (MX-21)
     MX-22      Special Mixed Use District (MX-22)

UNITSRES and UNITSTOTAL for condo lots are calculated by summing the values for the
individual condo unit lots to get the residential and total unit counts for the condo development
as a whole. In this version, the condo main (7500 lot) is no longer included in this calculation,
resulting in a decrease in the total number of residential and total units.

                                  CHANGES IN PLUTO
                           BETWEEN PLUTO21v1 AND PLUTO20v8

ASSESSED LAND VALUE (AssessLand), ASSESSED TOTAL VALUE AssessTot), and
EXEMPT TOTAL VALUE (ExemptTot) have been updated to reflect the Department of
Finance’s FY22 Tentative Assessment Roll.


                                                 9
 PLUTO README DOCUMENT                                                     August 2026 (26v2)


PLUTO version 20v8 contained null values for LANDMARK STATUS (Landmark). This issue
has been fixed in PLUTO21v1.

New SPECIAL PURPOSE DISTRICT values:
     WF         Special Flushing Waterfront District
     MX-19      Special Mixed Use District (MX-19)
     MX-20      Special Mixed Use District (MX-20)

                                     CHANGES IN PLUTO
                              BETWEEN PLUTO20v7 AND PLUTO20v8

Changes to the Property Tax System (PTS) data from the Department of Finance resulted in an
~6% decrease in aggregate BUILDING AREA (bldgarea). In previous versions, the BUILDING
AREA for ~60 condominium lots was wrong. There was also a ~6% decrease in aggregate LOT
AREA (lotarea) because previous versions had bad values for two lots near JFK (BBLs
4142600080 and 4142600085). The LOT AREA for these two lots has been corrected.

PLUTO20v8 uses updated data on community gardens from the Department of Parks and
Recreation, resulting in 52 fewer lots assigned to BUILDING CLASS (bldgclass) “QG”.

                                     CHANGES IN PLUTO
                              BETWEEN PLUTO20v6 AND PLUTO20v7

PLUTO versions 19v2 through 20v6 contained null values for E-DESIGNATION NUMBER. This
issue has been fixed in PLUTO20v7. Just over 9000 tax lots now correctly have a value for E-
DESIGNATION NUMBER.

                                     CHANGES IN PLUTO
                              BETWEEN PLUTO20v5 AND PLUTO20v6

Lots designated by the Department of Finance as vacant, but having a community garden
registered with the Department of Parks and Recreation, have been assigned a new BUILDING
CLASS of “QG” and a LAND USE CATEGORY of “09” (Open Space & Outdoor Recreation).
This is being done to comply with Local Law 46 of 2020. This land use assignment is solely
informational and does not confer or change a legal status for such a tax lot

                                     CHANGES IN PLUTO
                              BETWEEN PLUTO20v4 AND PLUTO20v5

In version 20v1, a Notes field was added, which had a value of 1 for tax lots affected by the
12/19/19 court order on the Special Inwood District Rezoning. In July 2020, the Appellate Division
upheld the rezoning, so this value has been removed from all lots.

                                 CHANGES IN PLUTO
                          BETWEEN PLUTO20v4 AND PLUTO20v3

EXEMPT TOTAL VALUE (ExemptTot) has been updated for most lots with a non-zero value.
This reflects STAR exempt values from New York State that were received after the tentative
roll was released.

DATA CHANGES

                                               10
 PLUTO README DOCUMENT                                                      August 2026 (26v2)


Methodology change

       •     NUMBER OF BUILDINGS (NumBldgs) – The number of buildings on a lot is now
             calculated by taking the BINs for every building in DoITT’s Building Footprints
             dataset, running Geosupport function BN to get the BBL associated with that BIN,
             and summing the number of buildings per BBL.

             Previous versions of PLUTO used the Structures field from Geosupport FN 1B for
             the number of buildings. The Geosupport Structures field may include some
             buildings that have been demolished.

             This change affects ~14,500 lots and results in a decrease of ~15,500 buildings
             overall.

DCP edits
      • OWNER NAME (OwnerName) – This version contains additional normalizations to
          owner names for publicly owned tax lots.
      • NUMBER OF FLOORS (NumFloors) – Manual research was done on buildings for
          which NUMBER OF FLOORS was not consistent with the height of the building in
          DoITT’s Building Footprints. NUMBER OF FLOORS was corrected for ~20 buildings


                                   CHANGES IN PLUTO
                            BETWEEN PLUTO20v1 AND PLUTO20v2

ASSESSED LAND VALUE (AssessLand), ASSESSED TOTAL VALUE AssessTot), and
EXEMPT TOTAL VALUE (ExemptTot) have been updated to reflect the Department of
Finance’s FY21 Tentative Assessment Roll.

DATA CHANGES

Corrections

       •     NUMBER OF BUILDINGS (NumBldgs) – Version 20v2 fixes a problem with the
             number of buildings for condominiums.


                                   CHANGES IN PLUTO
                            BETWEEN PLUTO19v2 AND PLUTO20v1

DATA CHANGES

New fields

       •     LATITUDE (Latitude) – The WGS 84 latitude of the latitude/longitude coordinate pair
             for the approximate location of the tax lot.

       •     LONGITUDE (Longitude) – The WGS 84 longitude of the latitude/longitude
             coordinate pair for the approximate location of the tax lot.



                                                11
 PLUTO README DOCUMENT                                                        August 2026 (26v2)


       •    NOTES (Notes) – A text field containing notes of importance to one or more tax lots.
            Refer to the PLUTO Data Dictionary for more information. For version 20v1, the field
            only has a value for tax lots affected by the 12/19/19 court order on the Special
            Inwood District Rezoning.

Corrections

       •    RESIDENTIAL UNITS (UnitsRes), TOTAL UNITS (UnitsTot), and TOTAL
            BUILDING FLOOR AREA (BldgArea) – In version 19v2, there was an error in the
            number of units and building area for some condominiums that had not yet been
            assigned a billing BBL. For these condos, pluto.csv and the table
            NOT_MAPPED_LOTS contained a record for each individual condo unit with
            UnitsRes, UnitsTot, or BldgArea values that pertained to the entire building. These
            records are now excluded.

            This error was not in MapPLUTO, which uses the geometry of the billing BBL.
            Because these lots did not have a billing BBL assigned, they were not mapped.

       •    ZONING DISTRICT 1 (ZoneDist1) – The logic for calculating ZONING DISTRICT 1
            has been adjusted to account for large lots that are primarily under water. In previous
            versions, ZONING DISTRICT 1 was blank if no zoning district covered at least 10%
            of the lot area. Starting with this version, the zoning district classification occupying
            the greatest percentage of a tax lot’s area is assigned to ZONING DISTRICT 1, even
            if the percentage is under 10%.

DCP Edits

In order to improve data quality and consistency, City Planning applies changes to selected field
values. CHANGE BY DCP is set to “1” if a record contains any changed values. The changes
made to a tax lot record are records in PLUTOChangeFile20v1.csv, which is available as part of
the MapPLUTO download on BYTES of the BIG APPLETM. The change file contains the BBL;
field name; old and new values; and the reason that the field was changed.

       •    YEAR BUILT (YearBuilt) – For ~26,000 buildings, YearBuilt has been changed to
            the date high value from Landmarks Preservation Commission’s Individual Landmark
            and Historic District Building Database. Changes were only included if there was a
            one to one relationship between PLUTO and the LPC database, i.e. PLUTO showed
            just one building on the tax lot and LPC had one record for the tax lot. If the lot had a
            demolition or new construction permit that was issued after the designation date for
            the historic district, YearBuilt was not updated.

       •    OWNER NAME (OwnerName) – For publicly owned tax lots, owner names were
            normalized in version 19v2. This version contains additional normalizations.

PROCESSING CHANGES

PLUTO aggregates condominium unit tax lot information to the billing lot. Previous versions of
PLUTO contained records for individual unit tax lots that had not yet been assigned a
CONDOMINIUM NUMBER. Version 20v1 excludes unit tax lots if the record contains values for
RESIDENTIAL UNITS or BUILDING AREA that pertain to the entire condominium. See TAX
LOT in the PLUTO Data Dictionary for more information.

                                                 12
 PLUTO README DOCUMENT                                                      August 2026 (26v2)



                                  CHANGES IN PLUTO
                           BETWEEN PLUTO19v1 AND PLUTO19v2

DATA QUALITY IMPROVEMENTS

Starting with version 19v2, City Planning is applying changes to selected field values, where
appropriate. This is being done to improve data quality and consistency. This version includes
changes to LOT AREA and OWNER NAME. User reported errors will also be corrected once
City Planning has verified the correction.

DCPEdited is a new field that is set to “1” if the record contains any changed values. To see
what changes have been made for a record, see PLUTOChangeFile19v2.csv, available as part
of the download on BYTES of the BIG APPLETM, This file contains the BBL; field name; old and
new values; and the reason that the field was changed.

Changed fields
      • LOT AREA (LotArea) – If the lot area from the Department of Finance’s Property Tax
          System is zero, this field is changed to show the area of the tax lot’s geometric
          shape in the Digital Tax Map.
      • OWNER NAME (OwnerName) – For publicly owned tax lots, owner names have
          been normalized. For example, “NYC PARKS”, “PARKS DEPARTMENT”, and
          “PARKS AND RECREATION (GENERAL)” have been changed to “NYC
          DEPARTMENT OF PARKS AND RECREATION”.

New fields
       • CHANGED BY DCP (DCPEdited) – Flag set to “1” if City Planning has made a
           change to any field values for this tax lot. To see which field(s) were changed, refer
           to PLUTOChangeFileYYv#.#.csv, where YYV#.# is the version number. See the
           PLUTO change file readme document for more information.

NEW SPECIAL PURPOSE DISTRICT

MX-18

                                 CHANGES IN PLUTO
                          BETWEEN PLUTO18v2.1 AND PLUTO19v1

PLUTO version 19v1 uses Department of Finance’s (DOF) new Property Tax System (PTS),
which replaced DOF’s Real Property Assessment Data (RPAD) in early 2019. Certain fields
have changed as a result:

        •   NUMBER OF EASEMENTS (Easements) – This data now comes from PTS rather
            than CAMA.
        •   OWNER NAME (OwnerName) – The field size has increased from 21 characters to
            80 characters. Owner names that were previously truncated at 21 characters will
            show a change from the previous version.
        •   COMMERCIAL, RESIDENTIAL, OFFICE, RETAIL, GARAGE, STORAGE,
            FACTORY and OTHER FLOOR AREA – Data for these fields was previously taken
            from CAMA. Starting with this version, the primary source is PTS. If PTS does not
            contain data for a lot, CAMA data is used.

                                                13
 PLUTO README DOCUMENT                                                       August 2026 (26v2)


       •   EXTENSION CODE (Ext) – A value of “N” has been added for lots without an
           extension or garage. A blank (in PLUTO) or a null value (in MapPLUTO) indicates
           that DOF does not have information for that lot.
       •   CONDOMINIUM NUMBER (CondoNo) – If no condominium number is assigned to a
           lot, the field contains a blank (in PLUTO) or a null value (in MapPLUTO). In previous
           versions, the value for these lots was 0.
       •   APPORTIONMENT BBL (APPBBL) – If no apportionment BBL exists for a lot, the
           field contains a blank (in PLUTO) or a null value (in MapPLUTO). In previous
           versions, the value for these lots was 0.

Deleted fields
       • EXEMPT LAND VALUE (ExemptLand) – This field has been deleted. It is no longer
            available from DOF.

BUILT FLOOR AREA RATIO (BuiltFAR) – Version 18v2.1 corrected an error in building area
(BldgArea) for approximately 7000 condominium lots. BuiltFAR should have been recalculated
for these lots, but was not. This has been corrected in 19v1.

MAXIMUM ALLOWABLE RESIDENTIAL FAR (ResidFAR) - For R2X, R3, R4, and C3 zoning
districts, ResidFAR no longer includes the attic allowance, under which the FAR may be
increased by up to 20% for the inclusion of space beneath a pitched roof.

                                 CHANGES IN PLUTO
                       BETWEEN PLUTO18v2 Beta AND PLUTO18v2.1

PLUTO version 18v2.1 uses the same source data as PLUTO version 18v2 Beta but fixes an
error in building area (BldgArea) for approximately 7000 condominium lots. Other building area
fields, such as ComArea, ResArea, etc., were not affected by this problem. The only change in
this version is to the BldgArea and AreaSource fields for these condominiums.

                                 CHANGES IN PLUTO
                       BETWEEN PLUTO18v1.1 AND PLUTO18v2 Beta

The methodology used to create PLUTO has changed with version 18v2 Beta. Most of the
processing has been rewritten to run in PostgresSQL and the code is available on GitHub.
Every effort has been made to use the same data sources and calculations for PLUTO fields.
However, there were changes in a small number of fields. These are listed below.

OWNER TYPE – Approximately 76,000 tax lots that had a value of “P” in version 18v1.1 have a
value of blank in version 18v2 Beta. As noted in the PLUTO Data Dictionary, either value
indicates that the owner is most likely a private entity.

BUILDING CLASS – There are fewer tax lots assigned to building class “Q0” (Open Space).
DCP assigns this building class to tax lots with an RPAD building class starting with “V” that it
determines are parklands. Previous versions of PLUTO used a variety of datasets to identify
parklands. Starting with version 18v2 Beta, only vacant lots identified in the NYC GIS Zoning
Database as PARK, BALL FIELD, PLAYGROUND, or PUBLIC SPACE will be reassigned to
building class “Q0”.

LAND USE – The land use for building class “G2” (Auto Body/Collision or Auto Repair) was
changed from “10” to “07”

                                                14
 PLUTO README DOCUMENT                                                       August 2026 (26v2)


LANDMARK STATUS – This field was formerly called LANDMARK NAME. In version 18v1.1,
non-blank values were either “INDIVIDUAL LANDMARK” or “INTERIOR LANDMARK”. Because
some tax lots contain both types of landmarks, version 18v2 Beta classifies these lots as
“INDIVIDUAL AND INTERIOR LANDMARK”. For the name of the landmark building, see the
source data set in NYC Open Data, Landmarks Preservation Commission – Individual
Landmarks.

Most field definitions in the PLUTO Data Dictionary have been revised to clarify the description
and the methodology used to calculate the field.

                                 CHANGES IN PLUTO
                          BETWEEN PLUTO18v1 AND PLUTO18v1.1

CHANGE IN METHODOLOGY FOR ZONING FIELDS

To update zoning fields in previous versions of PLUTO, City Planning maintained a dataset with
the zoning characteristics of each lot. This was updated for every rezoning, as well as for lot
changes resulting from merger, apportionment, or condo conversion. This was a labor-intensive
process and sometimes resulted in lots with zoning that did not agree with the underlying zoning
districts.

The new methodology programmatically determines the zoning designations using the NYC GIS
Zoning Features available on BYTES of the BIG APPLE™. A zoning district is assigned to a tax
lot if it covers at least 10% of the lot’s area. A commercial overlay is assigned to a tax lot if it
covers at least 10% of the lot’s area OR at least 50% of the commercial overlay district is
contained within the lot. See the data dictionary for additional information.

Previously, a variety of sources were used to identify parkland. Starting with PLUTO18v1.1,
NYC GIS Zoning Features are the data source used for identifying parkland and tax lots that
intersect with areas designated in NYC GIS Zoning Features as PARK, BALL FIELD,
PLAYGROUND, and PUBLIC SPACES have been assigned a single value of PARK. No other
parkland datasets are incorporated. The NYC GIS Zoning Features do not constitute a definitive
list of parks in the city. Lots designated as PARK should not be used to calculate the amount of
open space in an area.

The abbreviations used to designate special districts have been changed to agree with those in
NYC GIS Zoning Features. Special districts “CR1” and “CR2” are combined into “CR”. In the
area of Manhattan covered by both the Special 125th Street District and the Special Transit
District, previous versions of PLUTO set Special District 1 equal to “125” and Special District 2
equal to “TA”. The special district for these areas is now designated as “125th/TA”. In the area
of Brooklyn covered by both the Special Enhanced Commercial District 5 or 6 and Mixed Use
District MX-16), previous versions set Special District 1 equal to “EC-5” or “EC-6” and Special
District 2 equal to “MX-16”. These areas are now designated as “MX-16/EC-5” or “MX-16/EC-6”.
See the table below for a list of changes to special district abbreviations.

FIELDS UPDATED FOR ZONING ONLY UPDATE




                                                15
PLUTO README DOCUMENT                                                August 2026 (26v2)




CHANGES TO SPECIAL DISTRICT ABBREVIATIONS

     18v1     18v1.1       Description
     125      125th        Special 125th Street District
              125th/TA     Special 125th Street Dist/Transit Land use Dist
     CR-1     CR           Special Coastal Risk District
     CR-2     CR           Special Coastal Risk District
              EHC          East Harlem Corridors
              EHC/TA       East Harlem Corridors/Transit Land Use District
              IN           Special Inwood District
     MID      MiD          Special Midtown District
              MX-16/EC-5   Mixed Use District/Enhanced Commercial District 5
              MX-16/EC-6   Mixed Use District/Enhanced Commercial District 6
     WCH      WCh          Special West Chelsea District




NEW ZONING DISTRICT

M1-4/R9A




                                         16
