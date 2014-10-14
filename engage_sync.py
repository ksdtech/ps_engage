import argparse
import csv
import datetime
import dateutil.parser
import os
import sys

DO_NOT_ENROLL = [ 
    # Language Arts 6, History 6 - Ms. Brundige (iWeb)
    '104.ELA6-BRU', '104.HIST6-BRU', '104.CORE6-BRU',
    # Film Making 7/8 - Ms. Brundige (iWeb)
    '104.FILM78',
    # History 8 - Mr. Palmer (Google Sites)
    '104.HIST8',
    # Art 5, Art 6, Art 7/8 - Ms. Montgomery (iWeb)
    '104.ART', '104.ART5', '104.ART6', '104.ART78',
    # PE 5, PE 6, PE 7, PE 8 - Mr. Gillespie, Mr. Kelly, Ms. Chase and Ms. Fox]
    '104.PE', '104.PE5', '104.PE6', '104.PE7', '104.PE8',
]

DAYS_PAST = 7
DAYS_UPCOMING = 7
AUTOSEND = True

STUDENT_HEADERS = [
    'Student_Number',
    'SchoolID',
    'EntryDate',
    'ExitDate',
    'First_Name',
    'Middle_Name',
    'Last_Name',
    'Gender',
    'Grade_Level',
    'Network_ID',
    'Mother_First',
    'Mother',
    'Mother_Email',
    'Father_First',
    'Father',
    'Father_Email'
]

TEACHER_HEADERS = [
    'TeacherNumber',
    'First_Name',
    'Last_Name',
    'SchoolID',
    'Email_Addr'
]

COURSE_HEADERS = [
    'SchoolID',
    'Course_Name',
    'Course_Number',
    'Alt_Course_Number',
    'Code'
]

SECTION_HEADERS = [
    'SchoolID',
    'Course_Number',
    'Section_Number',
    'TermID',
    '[13]Abbreviation',
    '[13]FirstDay',
    '[13]LastDay',
    'Expression'
    '[05]TeacherNumber'
]

CC_HEADERS = [
    'Course_Number',
    'Section_Number',
    'SchoolID',
    'TermID',
    'DateEnrolled',
    'DateLeft',
    'Expression',
    '[01]Student_Number',
    '[01]First_Name',
    '[01]Last_Name',
    '[05]TeacherNumber',
    '[05]Last_Name'
]

class EngageUploader(object):
    def __init__(self, source_dir=None, output_dir=None, autosend=False, effective_date=datetime.date.today()):
        self.students = { }
        self.teachers = { }
        self.courses = { }
        self.sections = { }
        self.enrollments = { }
        self.course_teachers = { }
        self.valid_codes = { }
        self.codes = { }
        self.source_dir = source_dir or './source'
        self.output_dir = output_dir or './output'
        try:
            os.makedirs(self.output_dir)
        except:
            pass
        self.autosend = autosend
        self.effectiveDate = effective_date
        self.loadCodes()
        self.loadStudents()
        self.loadTeachers()
        self.loadCourses()
        self.loadSections()
        self.loadEnrollments()
        
    def getEdlineClassId(self, school_id, course_number, teacher_id):
        code_id = '.'.join((school_id, course_number, teacher_id))
        return self.codes.get(code_id)

    def getTeacherName(self, teacher_id):
        teacher_data = self.teachers.get(teacher_id)
        if teacher_data:
            return teacher_data['Last_Name']
        return '?'

    def loadCodes(self):
        with open(os.path.join(self.source_dir, 'edline_classes.txt')) as f:
            codes = csv.DictReader(f, dialect='excel-tab', lineterminator='\n')
            for row in codes:
                class_id =  row['Code']
                if class_id:
                    school_id = row['SchoolID']
                    school_class_id = '.'.join((school_id, class_id))
                    self.valid_codes[school_class_id] = 1
        with open(os.path.join(self.source_dir, 'codes.txt')) as f:
            codes = csv.DictReader(f, dialect='excel-tab', lineterminator='\n')
            for row in codes:
                class_id =  row['Code']
                if class_id:
                    school_id = row['SchoolID']
                    school_class_id = '.'.join((school_id, class_id))
                    if school_class_id not in self.valid_codes:
                        raise Exception('invalid code %s' % school_class_id)
                    if not school_class_id in DO_NOT_ENROLL:
                        course_number = row['Course_Number']
                        teacher_id = row['Teacher_Id']
                        code_id = '.'.join((school_id, course_number, teacher_id))
                        self.codes[code_id] = class_id
    
    def loadStudents(self):
        with open(os.path.join(self.source_dir, 'students.txt')) as f:
            fieldnames = None if not self.autosend else STUDENT_HEADERS
            students = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in students:
                student_id = 'S' + row['Student_Number']
                self.students[student_id] = row

    def loadTeachers(self):
        with open(os.path.join(self.source_dir, 'teachers.txt')) as f:
            fieldnames = None if not self.autosend else TEACHER_HEADERS
            teachers = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in teachers:
                teacher_id = 'T' + row['TeacherNumber']
                self.teachers[teacher_id] = row

    def loadCourses(self):
        with open(os.path.join(self.source_dir, 'courses.txt')) as f:
            fieldnames = None if not self.autosend else COURSE_HEADERS
            courses = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in courses:
                course_number = row['Course_Number']
                self.courses[course_number] = row

    def loadSections(self):
        with open(os.path.join(self.source_dir, 'sections.txt')) as f:
            fieldnames = None if not self.autosend else SECTION_HEADERS
            sections = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in sections:
                school_id = row['SchoolID']
                course_number = row['Course_Number']
                section_number = row['Section_Number']
                section_id = '.'.join((school_id, course_number, section_number))
                self.sections[section_id] = row
                teacher_id = 'T' + row['[05]TeacherNumber']
                course_teacher_id = '.'.join((school_id, course_number, teacher_id))
                self.course_teachers[course_teacher_id] = 1
                
    def loadEnrollments(self):
        with open(os.path.join(self.source_dir, 'cc.txt')) as f:
            fieldnames = None if not self.autosend else CC_HEADERS
            cc = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in cc:
                start_date = dateutil.parser.parse(row['DateEnrolled']).date() - datetime.timedelta(days=DAYS_UPCOMING)
                end_date   = dateutil.parser.parse(row['DateLeft']).date() + datetime.timedelta(days=DAYS_PAST)
                if self.effectiveDate >= start_date and self.effectiveDate <= end_date:
                    school_id = row['SchoolID']
                    course_number = row['Course_Number']
                    teacher_id = 'T' + row['[05]TeacherNumber']
                    class_id = self.getEdlineClassId(school_id, course_number, teacher_id)
                    if class_id:
                        student_id = 'S' + row['[01]Student_Number']
                        section_number = row['Section_Number']
                        enrollment_id = '.'.join((school_id, class_id, student_id, course_number, section_number, teacher_id))
                        self.enrollments[enrollment_id] = row
                    
    def dumpAllCourses(self):
        f = sys.stdout
        w = csv.writer(f, dialect='excel-tab', lineterminator='\n')
        w.writerow(['course_name', 'course_number', 'teacher_id', 'teacher_name', 'code'])
        for course_teacher_id in self.course_teachers:
            school_id, course_number, teacher_id = course_teacher_id.split('.')
            course_name = self.courses[course_number]['Course_Name']
            teacher_name = self.getTeacherName(teacher_id)
            class_id = self.getEdlineClassId(school_id, course_number, teacher_id)
            w.writerow([course_name, course_number, teacher_id, teacher_name, class_id])        
                        
    def dumpActiveEnrollments(self):
        f = sys.stdout
        w = csv.writer(f, dialect='excel-tab', lineterminator='\n')
        w.writerow(['course_name', 'course_number', 'section_number', 'teacher_id', 'teacher_name', 'code', 'student_id'])
        for enrollment_id, enrollment_data in self.enrollments.iteritems():
            school_id, class_id, student_id, course_number, section_number, teacher_id = enrollment_id.split('.')
            course_name = self.courses[course_number]['Course_Name']
            teacher_name = self.teachers[teacher_id]['Last_Name']
            section_id = '.'.join((school_id, course_number, section_number))
            section_data = self.sections[section_id]
            term = section_data['[13]Abbreviation']
            w.writerow([course_name, course_number, section_number, teacher_id, teacher_name, class_id, student_id])        

    def writeStudentsFile(self):
        with open(os.path.join(self.output_dir, 'students.csv'), 'w') as f:
            w = csv.writer(f, dialect='excel', lineterminator='\r\n')
            w.writerow(['ID', 'LastName', 'FirstName', 'GradeLevel', 'SchoolId'])
            for student_id, student_data in self.students.iteritems():
                school_id = student_data['SchoolID']
                last_name = student_data['Last_Name']
                first_name = student_data['First_Name']
                grade_level = student_data['Grade_Level']
                w.writerow([student_id, last_name, first_name, grade_level, school_id])
                
    def writeStudentContactsFile(self):
        with open(os.path.join(self.output_dir, 'contacts.csv'), 'w') as f:
            w = csv.writer(f, dialect='excel', lineterminator='\r\n')
            w.writerow(['SchoolID','UserID','LastName','FirstName',
                'Email','Email2','Email3','Email4',
                'ParentEmail','ParentEmail2','ParentEmail3','ParentEmail4',
                'Phone','Phone2','Phone3','Phone4',
                'ParentPhone','ParentPhone2','ParentPhone3','ParentPhone4'])
            for student_id, student_data in self.students.iteritems():
                school_id = student_data['SchoolID']
                last_name = student_data['Last_Name']
                first_name = student_data['First_Name']
                student_email = student_data['Network_ID']
                if student_email:
                    student_email += '@kentstudents.org'
                mother_email = student_data['Mother_Email']
                father_email = student_data['Father_Email']
                w.writerow([school_id, student_id, last_name, first_name,
                    student_email, '', '', '',
                    mother_email, father_email, '', '',
                    '', '', '', '',
                    '', '', '', '' ])
            
    def writeSchedulesFile(self):
        with open(os.path.join(self.output_dir, 'schedules.csv'), 'w')  as f:
            w = csv.writer(f, dialect='excel', lineterminator='\r\n')
            w.writerow(['ClassID', 'StudentID', 'SchoolId'])
            seen = dict()
            for enrollment_id, enrollment_data in self.enrollments.iteritems():
                school_id, class_id, student_id, course_number, section_number, teacher_id = enrollment_id.split('.')
                key = '.'.join((school_id, class_id, student_id))
                if key not in seen:
                    seen[key] = 1
                    w.writerow([class_id, student_id, school_id])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files for Edline LiveSync.')
    parser.add_argument('-a', '--autosend', action='store_true',
        help='use autosend files (no header line)')
    parser.add_argument('-s', '--source_dir', help='source directory')
    parser.add_argument('-o', '--output_dir', help='output directory')
    parser.add_argument('-d', '--dump', action='store_true', 
        help='dump courses and sections')
    args = parser.parse_args()

    uploader = EngageUploader(source_dir=args.source_dir, output_dir=args.output_dir, autosend=args.autosend)
    if args.dump:
        uploader.dumpAllCourses()
        uploader.dumpActiveEnrollments()
    else:
        uploader.writeStudentsFile()
        uploader.writeStudentContactsFile()
        uploader.writeSchedulesFile()

