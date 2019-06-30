try:
  from http.cookiejar import CookieJar
except ImportError:
  from cookielib import CookieJar

try:
  from urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
  from urllib.parse import urlencode
except ImportError:
  from urllib2 import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
  from urllib import urlencode

import re
import time
import webbrowser
import base64
import json
from resource import User, Course, Email
from random import randrange
from datetime import datetime

class RegistrationController():

  # init CourseChecker()
  def __init__(self):
    self.user = None
    self.execution = open("library/execution.txt", "r").read()
    # Search pattern (compiled for efficiency)
    self.totalSeats = re.compile("<td width=&#39;200px&#39;>Total Seats Remaining:</td>" + "<td align=&#39;left&#39;><strong>(.*?)</strong></td>")
    self.generalSeats = re.compile("<td width=&#39;200px&#39;>General Seats Remaining:</td>" + "<td align=&#39;left&#39;><strong>(.*?)</strong></td>")
    self.restrictedSeats = re.compile("<td width=&#39;200px&#39;>Restricted Seats Remaining\*:</td>" + "<td align=&#39;left&#39;><strong>(.*?)</strong></td>")

  def setUserInfo(self, userInfo):
    userCourses = []
    for course in userInfo['courses']:
      c = Course(str(course['year']), str(course['season']), str(course['dept']), str(course['course']), str(course['section']), course['acceptRestricted'], str(course['fromSection']), course['switchSection'], str(course['courseURL']), str(course['registerURL']), str(course['switchURL']))
      userCourses.append(c)
    self.user = User(str(userInfo['cwl_user']), str(userInfo['cwl_pass']), str(userInfo['email']), userInfo['registerAutomatic'], int(userInfo['delay']), userCourses)

  def saveUserInfo(self):
    # Save user information into the database (in this case a JSON file)
    with open('library/database.json') as f:
      data = json.load(f)
      data[self.user.cwl_user] = self.user.toDict()
    with open('library/database.json', 'w') as f: 
      json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=2)
  
  # Notify that a course is available
  def notify(self, index):
    print("Seat available.")
    email = Email(self.user.email, self.user.courses[index])
    email.sendEmail()
    webbrowser.open_new(self.user.courses[index].courseURL)

  # Delay to prevent sending too many requests
  def wait(self):
    randDelay = self.user.delay + int(randrange(11))
    time.sleep(randDelay) 

  # Automatically registers in the course
  def autoRegister(self, index):
    # Cookie / Opener holder
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))

    # Login Header
    opener.addheaders = [('User-agent', 'UBC-Login')]

    # Install opener
    install_opener(opener)

    # Form POST URL
    postURL = "https://cas.id.ubc.ca/ubc-cas/login"

    # First request form data
    formData = {
      'username': self.user.cwl_user,
      'password': base64.urlsafe_b64decode(self.user.cwl_pass),
      'execution': self.execution,
      '_eventId': 'submit'
      }

    # Encode form data
    data = urlencode(formData).encode('UTF-8')

    # First request object
    req = Request(postURL, data)

    # Submit request and read data
    resp = urlopen(req)
    respRead = resp.read().decode('utf-8')
    course = self.user.courses[index]

    loginURL = "https://courses.students.ubc.ca/cs/secure/login"
    sessionURL = 'https://courses.students.ubc.ca/cs/courseschedule?sessyr=%s&sesscd=%s&pname=regi_sections&tname=regi_sections' % (course.year, course.season)
    registerURL = course.switchURL if course.switchSection else course.registerURL

    # Perform login and registration
    urlopen(loginURL)
    urlopen(sessionURL)

    register = urlopen(registerURL)
    respReg = register.read().decode('utf-8')
    print("Course Registeration Attempted. Verify on ssc")
    self.notify(index)

    # Temporary
    # postURL = "https://courses.students.ubc.ca/cs/courseschedule"

    # # First request form data
    # formData = {
    #   'pname': "regi_sections",
    #   'tname': "regi_sections",
    #   'switchFromKey': "CRWR,201,001",
    #   'switchtype': "sect",
    #   'wldel': "CRWR,201,002",
    #   'submit': "Switch Sections",
    #   }

    # data = urlencode(formData).encode('UTF-8')
    # # First request object
    # req = Request(postURL, data)

    # # Submit request and read data
    # resp = urlopen(req)
    # respRead = resp.read().decode('utf-8')
    # print(respRead)


  # Scan webpage for seats
  def checkSeats(self, index):
    course = self.user.courses[index]
    logs = open("logs.txt","a+") 
    logs.write("%s - Scanning for %s %s %s\n" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), course.dept, course.course, course.section))
    url = course.courseURL
    ubcResp = urlopen(url)
    ubcPage = ubcResp.read().decode('utf-8')

    # Search for the seat number element
    t = re.search(self.totalSeats, ubcPage)
    g = re.search(self.generalSeats, ubcPage)
    r = re.search(self.restrictedSeats, ubcPage)

    # Find remaining seats
    if t:
      if t.group(1) == '0':
        return 0
    else:
      raise ValueError("Error: Can't locate number of seats.")

    if g:
      if g.group(1) != '0':
        return 1
    else:
      raise ValueError("Error: Can't locate number of seats.")

      
    if r:
      if r.group(1) != '0':
        return 2
    else:
      raise ValueError("Error: Can't locate number of seats.")

  # Conditional for determining whether to register/notify
  def scanAvailability(self, index):
    status = self.checkSeats(index)
    if status == 0:
      self.wait()
    if status == 1:
      if self.user.registerAutomatic == True:
        self.autoRegister(index)
      else:
        self.notify(index)
      return 0
    if status == 2:
      if self.user.courses[index].acceptRestricted == True:
        if self.user.registerAutomatic == True:
          self.autoRegister(index)
        else:
          self.notify(index)
        return 0
      else:
        self.wait()
    return -1
      
# if __name__ == "__main__":
#   c = RegistrationController()
#   c.userInput()
#   print ("Scanning seat availablility...")
#   c.scanAvailability()