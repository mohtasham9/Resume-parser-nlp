create or replace table cr.PersonalInformation (
    CandidateID INT NOT NULL,
    Name VARCHAR(255) NOT NULL,     
    ContactNumber VARCHAR(20),     
    EmailID VARCHAR(255),
    Location VARCHAR(255),     
    JobTitle VARCHAR(255),     
    DateOfBirth DATE,     
    Nationality VARCHAR(255),     
    LanguagesKnown VARCHAR(255),
    TimeStamp VARCHAR(50),
    PRIMARY KEY (CandidateID));



create or replace table cr.EducationalDetails (
    Degree VARCHAR(255),
    Branch VARCHAR(255),
    CompletedYear INT,
    GPAOrPercentage FLOAT,
    SchoolOrCollege VARCHAR(255),
    CandidateID INT,
    FOREIGN KEY (CandidateID) REFERENCES PersonalInformation(CandidateID)
);

create or replace table cr.WorkExperiences
    (CandidateID INT,
    Company VARCHAR(255),
    Role VARCHAR(255),
    StartTime DATE,
    EndTime DATE,
    ExperienceInYears INT,
    KeyResponsibilities TEXT,
    FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID));

create or replace table cr.ExperienceDetails (
    CandidateID INT,
    OverallYearsofExperience INT,
    TechnicalSkill VARCHAR(255),
    FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID));

create or replace table cr.Certification (
    CandidateID INT,
    CertificateName VARCHAR(255),
    YearOfCertification VARCHAR(10),
    CertificateProvider VARCHAR(255),
    CertificateID VARCHAR(50),
    SkillsCovered VARCHAR(255),
    FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)
);

create or replace table cr.CoursesCompleted (
    CandidateID INT,
    CourseName VARCHAR(255),
    YearOfCourseCompletion VARCHAR(10),
    CourseProvider VARCHAR(255),
    CertificateID VARCHAR(50),
    TopicsCovered VARCHAR(255),
    FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)
);

