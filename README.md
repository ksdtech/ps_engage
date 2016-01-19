ps_engage
=========
File processor for Edline (classes and rosters).

Installation
------------
Currently running on a Windows server with Python 2.7 and python-dateutil package.
Copy "source/section-codes.txt" to the SFTP source directory before running edline.bat
batch file.


Usage
-----

$ python engage_sync.py

Data Files
----------

There are 7 input files required

1. Export Student records into source/students.txt with following fields

Student_Number
SchoolID
EntryDate
ExitDate
First_Name
Middle_Name
Last_Name
Gender
Grade_Level
Network_ID
Mother_First
Mother
Mother_Email
Father_First
Father
Father_Email

2. Export Teacher records into source/teachers.txt with following fields

TeacherNumber
First_Name
Last_Name
SchoolID
Email_Addr

3. Export Course records into source/courses.txt with following fields

SchoolID
Course_Name
Course_Number
Alt_Course_Number
Code

4. Export Section records into source/sections.txt with following fields

SchoolID
Course_Number
Section_Number
TermID
[13]Abbreviation
[13]FirstDay
[13]LastDay
Expression
[05]TeacherNumber

5. Export CC records into source/cc.txt with following fields

Course_Number
Section_Number
SchoolID
TermID
DateEnrolled
DateLeft
Expression
[01]Student_Number
[01]First_Name
[01]Last_Name
[05]TeacherNumber
[05]Last_Name

6. Create source/codes.txt with columns

SchoolID
Course_Name
Course_Number
Teacher_Id
Teacher_Name
Code

Example:

SchoolID	Course_Name	Course_Number	Teacher_Id	Teacher_Name	Code
104	Academic Workshop 	9971	T104128	Anderson	AWKS-AND

7. Create source/edline\_classes.txt with columns

SchoolID
Code (Edline ClassID)

Example:

Code  ClassID
104   AWKS-HET


