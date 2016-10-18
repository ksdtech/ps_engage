import argparse
import csv
import datetime
import dateutil.parser
import os
import sys

DAYS_PAST = 7
DAYS_UPCOMING = 7
AUTOSEND = True

SECTION_CODES_HEADERS = [s.strip() for s in '''
ID
SchoolID
[Courses]Course_Name
[Teachers]Last_Name
Edline_Class_ID
Edline_Class_Name
Course_Number
Section_Number
[Teachers]TeacherNumber
[Terms]Abbreviation
Expression
'''.split('\n')[1:-1]]

STUDENT_HEADERS = [s.strip() for s in '''
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
'''.split('\n')[1:-1]]

TEACHER_HEADERS = [s.strip() for s in '''
TeacherNumber
First_Name
Last_Name
SchoolID
Email_Addr
Status
StaffStatus
CA_SEID
'''.split('\n')[1:-1]]

COURSE_HEADERS = [s.strip() for s in '''
SchoolID
Course_Name
Course_Number
Alt_Course_Number
Code
'''.split('\n')[1:-1]]

SECTION_HEADERS = [s.strip() for s in '''
SchoolID
Course_Number
Section_Number
TermID
[13]Abbreviation
[13]FirstDay
[13]LastDay
Expression
[05]TeacherNumber
'''.split('\n')[1:-1]]

CC_HEADERS = [s.strip() for s in '''
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
'''.split('\n')[1:-1]]

class EngageUploader(object):
    def __init__(self, source_dir=None, output_dir=None, autosend=False, effective_date=datetime.date.today()):
        self.students = { }
        self.teachers = { }
        self.classes = { }
        self.sections = { }
        self.enrollments = { }
        self.section_codes = { }
        self.class_names = { }
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
        self.loadTeachers('bacich')
        self.loadTeachers('kent')
        self.loadSections('kent')
        self.loadEnrollments()

    def excludeFromEnrollment(self, school_class_id):
        for ex in DO_NOT_ENROLL:
            if ex == school_class_id:
                return True
            if ex[-2:1] == '.*':
                school_id, class_id = school_class_id.split('.')
                test_school = ex[0:-2]
                if school_id == test_school:
                    return True
        return False

    def getEdlineClassInfo(self, school_id, course_number, section_number):
        class_id = ''
        class_name = ''
        enroll = False
        code_id = '.'.join((school_id, course_number, section_number))
        class_id = self.section_codes.get(code_id)
        if class_id:
            class_name = self.class_names.get(class_id)
            if class_name:
                enroll = True
        return (class_id, class_name, enroll)

    def getTeacherName(self, teacher_id):
        teacher_data = self.teachers.get(teacher_id)
        if teacher_data:
            return teacher_data['Last_Name']
        return '?'

    def loadCodes(self):
        with open(os.path.join(self.source_dir, 'section-codes.txt')) as f:
            codes = csv.DictReader(f, dialect='excel-tab', lineterminator='\n')
            for row in codes:
                class_id = row['Edline_Class_ID']
                class_name = row['Edline_Class_Name']
                if class_id and class_name:
                    school_id = row['SchoolID']
                    course_number =  row['Course_Number']
                    section_number = row['Section_Number']
                    teacher_number = row['[Teachers]TeacherNumber']
                    school_section_id = '.'.join((school_id, course_number, section_number))
                    self.section_codes[school_section_id] = class_id
                    self.class_names[class_id] = class_name

    def loadStudents(self):
        with open(os.path.join(self.source_dir, 'students.txt')) as f:
            fieldnames = None if not self.autosend else STUDENT_HEADERS
            students = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in students:
                student_id = 'S' + row['Student_Number']
                self.students[student_id] = row

    def loadTeachers(self, school_name):
        with open(os.path.join(self.source_dir, 'teachers-%s.txt' % school_name)) as f:
            fieldnames = None if not self.autosend else TEACHER_HEADERS
            teachers = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in teachers:
                teacher_id = 'T' + row['TeacherNumber']
                row.update({'Assigned': '0'})
                self.teachers[teacher_id] = row

    def loadSections(self, school_name):
        with open(os.path.join(self.source_dir, 'sections-%s.txt' % school_name)) as f:
            fieldnames = None if not self.autosend else SECTION_HEADERS
            sections = csv.DictReader(f, fieldnames=fieldnames, dialect='excel-tab', lineterminator='\n')
            for row in sections:
                school_id = row['SchoolID']
                course_number = row['Course_Number']
                section_number = row['Section_Number']
                teacher_id = 'T' + row['[05]TeacherNumber']
                if teacher_id in self.teachers:
                    if self.teachers[teacher_id]['Status'] == '1':
                        self.teachers[teacher_id]['Assigned'] = '1'
                        school_section_id = '.'.join((school_id, course_number, section_number))
                        self.sections[school_section_id] = row
                        class_id = self.section_codes.get(school_section_id)
                        if class_id:
                            class_name = self.class_names.get(class_id)
                            if class_name:
                                self.classes[class_id] = (class_name, teacher_id, school_id)
                    else:
                        print "section %s.%s (%s): teacher %s is not active" % (course_number, section_number, school_id, teacher_id)
                else:
                    print "section %s.%s (%s): missing teacher %s" % (course_number, section_number, school_id, teacher_id)

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
                    section_number = row['Section_Number']
                    class_id, class_name, enroll = self.getEdlineClassInfo(school_id, course_number, section_number)
                    if class_id and enroll:
                        student_id = 'S' + row['[01]Student_Number']
                        teacher_id = 'T' + row['[05]TeacherNumber']
                        enrollment_id = '.'.join((school_id, class_id, student_id, course_number, section_number, teacher_id))
                        self.enrollments[enrollment_id] = row

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

    def writeTeachersFile(self):
        with open(os.path.join(self.output_dir, 'teachers.csv'), 'w') as f:
            w = csv.writer(f, dialect='excel', lineterminator='\r\n')
            w.writerow(['ID', 'LastName', 'FirstName', 'GradeLevel', 'SchoolId'])
            for teacher_id, teacher_data in self.teachers.iteritems():
                if teacher_data['Assigned'] == '1':
                    school_id = teacher_data['SchoolID']
                    last_name = teacher_data['Last_Name']
                    first_name = teacher_data['First_Name']
                    w.writerow([teacher_id, last_name, first_name, '', school_id])

    def writeStudentsFile(self):
        with open(os.path.join(self.output_dir, 'students.csv'), 'w') as f:
            w = csv.writer(f, dialect='excel')
            w.writerow(['ID', 'LastName', 'FirstName', 'GradeLevel', 'SchoolId'])
            for student_id, student_data in self.students.iteritems():
                school_id = student_data['SchoolID']
                last_name = student_data['Last_Name']
                first_name = student_data['First_Name']
                grade_level = student_data['Grade_Level']
                w.writerow([student_id, last_name, first_name, grade_level, school_id])

    def writeStudentContactsFile(self):
        with open(os.path.join(self.output_dir, 'contacts.csv'), 'w') as f:
            w = csv.writer(f, dialect='excel')
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
                    student_email += '@kentfieldschools.org'
                mother_email = student_data['Mother_Email']
                father_email = student_data['Father_Email']
                w.writerow([school_id, student_id, last_name, first_name,
                    student_email, '', '', '',
                    mother_email, father_email, '', '',
                    '', '', '', '',
                    '', '', '', '' ])

    def writeClassesFile(self):
        seen_classes = { }
        with open(os.path.join(self.output_dir, 'classes.csv'), 'w')  as f:
            w = csv.writer(f, dialect='excel')
            w.writerow(['ClassID', 'Class Name', 'TeacherID', 'SchoolId'])
            for class_id in self.classes:
                class_name, teacher_id, school_id = self.classes[class_id]
                w.writerow([class_id, class_name, teacher_id, school_id])

    def writeSchedulesFile(self):
        with open(os.path.join(self.output_dir, 'schedules.csv'), 'w')  as f:
            w = csv.writer(f, dialect='excel')
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
        uploader.writeTeachersFile()
        uploader.writeClassesFile()
        uploader.writeStudentsFile()
        uploader.writeStudentContactsFile()
        uploader.writeSchedulesFile()
