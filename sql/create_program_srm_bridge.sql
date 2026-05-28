/*
  Bridge: marketing program_id (vw_program / lead cube) -> StudentRevenueMaster
  degreelevel + majorname.

  Populate from: python scripts/build_program_bridge.py
  (writes data/program_srm_bridge.csv then run import below or use BULK INSERT)
*/
IF OBJECT_ID('dbo.program_srm_bridge', 'U') IS NOT NULL
    DROP TABLE dbo.program_srm_bridge;
GO

CREATE TABLE dbo.program_srm_bridge (
    program_id              VARCHAR(18)  NOT NULL PRIMARY KEY,
    full_program_name       NVARCHAR(200) NOT NULL,
    lead_program_name       NVARCHAR(200) NULL,
    degree_level            NVARCHAR(50)  NULL,
    degree_type             NVARCHAR(50)  NULL,
    program_code_cvue       NVARCHAR(20)  NULL,
    account_group           NVARCHAR(100) NULL,
    is_enrolling            BIT           NOT NULL DEFAULT 0,
    srm_degreelevel         NVARCHAR(50)  NOT NULL,
    srm_majorname           NVARCHAR(200) NOT NULL,
    match_method            VARCHAR(32)   NOT NULL,
    match_confidence        DECIMAL(4,2)  NOT NULL,
    srm_student_count_3yr   INT           NULL,
    updated_at              DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX IX_program_srm_bridge_srm
    ON dbo.program_srm_bridge (srm_degreelevel, srm_majorname);
GO

-- Example join for demographics / revenue by marketing program:
/*
SELECT b.program_id, b.full_program_name, b.lead_program_name,
       s.gender, s.race, s.pell, COUNT(*) AS students
FROM dbo.StudentRevenueMaster s
INNER JOIN dbo.program_srm_bridge b
  ON s.degreelevel = b.srm_degreelevel
 AND s.majorname = b.srm_majorname
WHERE s.MATRICDATE >= DATEADD(year, -1, GETDATE())
GROUP BY b.program_id, b.full_program_name, b.lead_program_name,
         s.gender, s.race, s.pell;
*/
