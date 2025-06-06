USE cfb_schema;
DROP TABLE GameInfo;
CREATE TABLE GameInfo (
    ID INTEGER PRIMARY KEY,
    AwayName VARCHAR(50),
    HomeName VARCHAR(50),
    NeutralSite BOOLEAN,
    WeekNumber INTEGER,
    HomeDist INTEGER,
    AwayDist INTEGER,
    HomeRest INTEGER,
    AwayRest INTEGER,
    HomeScore INTEGER,
    AwayScore INTEGER
);