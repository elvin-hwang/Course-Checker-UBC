import re, copy, smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class User():

  # init User class
  def __init__(self, cwl_user, cwl_pass, email="", automatic=False, delay=60, courses=[]):
    self.cwl_user = cwl_user
    self.cwl_pass = cwl_pass
    self.email = email
    self.registerAutomatic = automatic
    self.delay = delay
    self.courses = courses
  
  def toDict(self):
    tempUser = copy.copy(self)
    temp = []
    for course in self.courses:
      temp.append(course.__dict__)
    tempUser.courses = temp
    return tempUser.__dict__

class Course():

  # init Course class
  def __init__(self, year, season, dept, course, section, acceptRestricted, fromSection="", switchSection=False, courseURL=None, registerURL=None, switchURL=""):
    self.year = year
    self.season = season
    self.dept = dept
    self.course = course
    self.section = section
    self.fromSection = fromSection

    self.switchSection = switchSection
    self.acceptRestricted = acceptRestricted
    self.courseURL = 'https://courses.students.ubc.ca/cs/courseschedule?sesscd=%s&pname=subjarea&tname=subj-section&sessyr=%s&course=%s&section=%s&dept=%s' % (self.season, self.year, self.course, self.section, self.dept) if courseURL is None else courseURL
    self.registerURL = "https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-section&submit=Register%sSelected&wldel=%s%s%s%s%s" % ('%20', self.dept, '%2C', self.course, '%2C', self.section) if registerURL is None else registerURL
    self.switchURL = "https://courses.students.ubc.ca/cs/courseschedule?pname=regi_sections&tname=regi_sections&switchFromKey=%s%s%s%s%s&switchtype=sect&wldel=%s%s%s%s%s&submit=Switch+Sections" % (self.dept, '%2C', self.course, '%2C', self.fromSection, self.dept, '%2C', self.course, '%2C', self.section) if switchSection else switchURL

class Email():

  # init Email class
  def __init__(self, toAddr, course):
    self.fromAddr = "courseopen@outlook.com"
    self.toAddr = toAddr
    self.course = course
  
  def sendEmail(self):
    if (self.toAddr):
      try:
        msg = self.createMessage(self.course)
        # Send the message via gmail's regular server, over SSL - passwords are being sent, afterall
        s = smtplib.SMTP('smtp-mail.outlook.com', 587)
        # uncomment if interested in the actual smtp conversation
        # s.set_debuglevel(1)
        # do the smtp auth; sends ehlo if it hasn't been sent already
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self.fromAddr, r"course123")

        s.sendmail(self.fromAddr, self.toAddr, msg.as_string())
        s.quit()
      except Exception as e:
        print e

  def createMessage(self, course):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Course %s %s %s is open for registration!" % (self.course.dept, self.course.course, self.course.section)
    msg['From'] = self.fromAddr
    msg['To'] = self.toAddr

    # adding this email puts the email in the SPAM box
    #emailCourseURL = self.course.courseURL
    line1 = '<p style="font-size:14px;">Hi, The following course is open for registration!</p>'
    line2 = '<p style="font-size:14px;">%s %s %s</p>' % (self.course.dept, self.course.course, self.course.section)
    line3 = '<p style="font-size:14px;">Register now or check if you have been registered if you signed up for autoregistration!</p>'

    html = '<html><body>%s%s%s</body></html>' % (line1, line2, line3)
    part2 = MIMEText(html, 'html')

    msg.attach(part2)
    return msg

