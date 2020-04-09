try:
    from Tkinter import *
except ImportError:
    from tkinter import *

try:
  from urllib.request import HTTPError
except ImportError:
  from urllib2 import HTTPError

import threading
from datetime import datetime
from library.registrationController import RegistrationController
from library.resource import User, Course
import base64, json, webbrowser

class ThreadedRow(threading.Thread):
  def __init__(self, rowFrame, course, row):
    super(ThreadedRow, self).__init__()
    self.rowFrame = rowFrame
    self.course = course
    self.row = row
    self.initialThreadSettings()
    self.setupRow()
  
  def initialThreadSettings(self):
    self.daemon = True
    self.paused = True
    self.state = threading.Condition()
    self._stop_event = threading.Event()

  def setupRow(self):
    # Remove Row Button
    Button(self.rowFrame, text='X', command=self.deleteRow, width=2).grid(row=0, column=0, padx=4)
    # Course Info
    Label(self.rowFrame, text="%s%s" % (self.course.year, self.course.season), width=10, height=2, bd=1, relief="solid").grid(row=0, column=1)
    Label(self.rowFrame, text=self.course.dept, width=10, height=2, bd=1, relief="solid").grid(row=0, column=2)
    Label(self.rowFrame, text=self.course.course, width=10, height=2, bd=1, relief="solid").grid(row=0, column=3)
    Label(self.rowFrame, text=self.course.section, width=10, height=2, bd=1, relief="solid").grid(row=0, column=4)
    Label(self.rowFrame, text="Allowed" if self.course.acceptRestricted else "Not Allowed", width=10, height=2, bd=1, relief="solid").grid(row=0, column=5)
    Label(self.rowFrame, text="Section %s" % self.course.fromSection if self.course.switchSection else "N/A", width=10, height=2, bd=1, relief="solid").grid(row=0, column=6)
    # Course URL Link
    link = Label(self.rowFrame, text="Course URL", fg="blue", cursor="hand2", width=10, height=2, bd=1, relief="solid")
    link.bind("<Button-1>", lambda e: webbrowser.open_new(self.course.courseURL))
    link.grid(row=0, column=7)
    # Course Checking Status
    self.statusText = StringVar()
    self.statusText.set("Idle")
    Label(self.rowFrame, textvariable=self.statusText, width=10, height=2, bd=1, relief="solid").grid(row=0, column=8)
    # Start Scan and Remove Row buttons
    self.checkButton = Button(self.rowFrame, text='Check Course', command=self.scanCourse)
    self.checkButton.grid(row=0, column=9, padx=4)

  def run(self):
    processes.append(self)
    logs = open("logs.txt","a+")
    logs.write("%s - Started Scanning for %s %s %s!\n" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), self.course.dept, self.course.course, self.course.section))
    self.resume()
    result = -1
    while not self.stopped() and result != 0:
      with self.state:
        if self.paused:
          self.state.wait()
      try:
        result = controller.scanAvailability(self.row)
      except (ValueError, HTTPError):
        logs.write("%s - ERROR: Stopped Scanning for %s %s %s!\n" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), self.course.dept, self.course.course, self.course.section))
        self.checkButton.configure(text="Check Course", state=DISABLED)
        self.statusText.set("Invalid Course")
        return
    if not self.stopped() and result == 0:
      logs.write("%s - Seats found for %s %s %s!\n" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), self.course.dept, self.course.course, self.course.section))
      self.statusText.set("Triggered!")
      self.checkButton.configure(text="Scan Complete", state=DISABLED) 
    logs.write("%s - Stopped Scanning for %s %s %s!\n" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), self.course.dept, self.course.course, self.course.section))

  def scanCourse(self):
    self.checkButton.configure(text="Pause Scan", command=self.pause)
    self.statusText.set("Scanning...")
    self.start()

  # delete row, stop thread, and rerender table
  def deleteRow(self):
    del controller.user.courses[self.row]
    controller.saveUserInfo()
    self.rowFrame.destroy()
    renderTable()

  def resume(self):
    self.checkButton.configure(text="Pause Scan", command=self.pause)
    self.statusText.set("Scanning...")
    with self.state:
      self.paused = False
      self.state.notify() # Unblock self if waiting.

  def pause(self):
    self.checkButton.configure(text="Resume Scan", command=self.resume)
    self.statusText.set("Paused")
    with self.state:
      self.paused = True  # Block self.
    
  def stop(self):
    self._stop_event.set()

  def stopped(self):
    return self._stop_event.is_set()

# login with local user data to fetch pending course information
# if user does not exist, direct them to register with the pw widgets
def getUserInfo():
  idSubmit.destroy()
  cwl_user = idInput.get()
  with open('library/database.json') as f:
    data = json.load(f)
    if cwl_user not in data:
      setupPassword()
      return
    controller.setUserInfo(data[cwl_user])
  initWindow()

# save the first time user into the database
def registerUser():
  if not pwInput.get():
    popupmsg("Password cannot be empty")
    return
  cwl_user = idInput.get()
  cwl_pass = pwInput.get()
  controller.user = User(cwl_user, base64.urlsafe_b64encode(cwl_pass))
  controller.saveUserInfo()

  pwLabel.destroy()
  pwInput.destroy()
  pwSubmit.destroy()
  initWindow()

# show the password widgets for first time user
def setupPassword():
  pwLabel.grid()
  pwInput.grid()
  pwSubmit.grid()

# show the user-interactive widgets and populate them
def initWindow():
  setInitialValues()
  showWidgets()
  idInput.config(state=DISABLED)

# Restore initial user values to the widgets
def setInitialValues():
  emailInput.insert(END, controller.user.email)
  delayInput.insert(END, controller.user.delay)
  registerAutomatic.set(controller.user.registerAutomatic)
  renderTable()

# TODO might need to verify the values in the input boxes are appropriate?
# add the course with the current values in the input boxes
def addCourse():
  yearSession = sessionInput.get()
  season = yearSession[-1].upper()
  year = yearSession[:-1]
  dept = deptInput.get().upper()
  course = courseInput.get()
  section = sectionInput.get()
  restricted = acceptRestricted.get() == 1
  fromSection = switchInput.get()
  switch = switchSection.get() == 1

  c = Course(year, season, dept, course, section, restricted, fromSection=fromSection, switchSection=switch)
  controller.user.courses.append(c)
  controller.saveUserInfo()

  restoreDefaultInput()
  renderTable()

def restoreDefaultInput():
  sessionInput.delete(0, END)
  sessionInput.insert(END, '2019W')
  deptInput.delete(0, END)
  deptInput.insert(END, 'CPSC')
  courseInput.delete(0, END)
  courseInput.insert(END, '110')
  sectionInput.delete(0, END)
  sectionInput.insert(END, '101')
  switchInput.delete(0, END)
  switchInput.config(state=DISABLED)
  switchButton.config(text="Switch Section")
  acceptRestricted.set(False)
  switchSection.set(False)

# reset the password, regardless of what current password is
def resetPassword():
  cwl_pass = resetPasswordInput.get()
  controller.user.cwl_pass = base64.urlsafe_b64encode(cwl_pass)
  controller.saveUserInfo()
  resetPasswordInput.delete(0, END)

# Creates a row using a thread class for the course
def createRow(course, index):
  rowFrame = Frame(scrollableTable, bg='#D3D3D3')
  rowFrame.grid(row=index, sticky=W)
  ThreadedRow(rowFrame, course, index)

# clear and then repopulate table
def renderTable():
  for process in processes:
    process.stop()
  del processes[:]
  for row in scrollableTable.winfo_children():
    row.destroy()
  for index, course in enumerate(controller.user.courses):
    createRow(course, index)

# Save values in User Settings Frame
def saveSettings():
  delaySeconds = int(delayInput.get())
  if delaySeconds < 15:
    popupmsg("Delay needs to be at least 15 seconds")
    return
  controller.user.email = emailInput.get()
  controller.user.delay = delaySeconds
  controller.user.registerAutomatic = registerAutomatic.get() == 1
  controller.saveUserInfo()
  successLabel = Label(settingsFrame, text="Saved!", fg='#00CC00')
  successLabel.grid(row=3, column=0, sticky=W, padx=10)
  successLabel.after(1000, lambda: successLabel.destroy())

# Hide all widgets except id widgets
def hideWidgets():
  # hide password widgets
  pwLabel.grid_remove()
  pwInput.grid_remove()
  pwSubmit.grid_remove()

  # hide other frames
  settingsFrame.grid_remove()
  resetFrame.grid_remove()
  courseSettings.grid_remove()
  tableHeader.grid_remove()
  canvas.grid_remove()
  warningFrame.grid_remove()
  return

# show all widgets except id/pw widgets
def showWidgets():
  settingsFrame.grid()
  resetFrame.grid()
  courseSettings.grid()
  tableHeader.grid()
  canvas.grid()
  warningFrame.grid()
  return

def switchInputDisplay():
  if switchSection.get():
    switchButton.config(text="Switch Section From:")
    switchInput.config(state=NORMAL)
    switchInput.insert(END, '9W1')
  else:
    switchButton.config(text="Switch Section")
    switchInput.delete(0, END)
    switchInput.config(state=DISABLED)

# ScrollableTable related
def onFrameConfigure(canvas, event):
  canvas.configure(scrollregion=canvas.bbox("all"))

# ScrollableTable related
def chat_width(event, canvas_frame):
  canvas_width = event.width
  canvas.itemconfig(canvas_frame, width = canvas_width)

# ScrollableTable related
def mouse_scroll(event):
  if event.delta:
    canvas.yview_scroll(-1*(event.delta/120), 'units')
  else:
    move = -1
    if event.num == 5:
      move = 1
    canvas.yview_scroll(move, 'units')

def factoryReset():
  with open('library/database.json', 'w') as f: 
      json.dump({}, f, ensure_ascii=False, sort_keys=True, indent=2)
  logs = open("logs.txt","w")
  logs.write("")
  onClose()

# Shows a popup dialog with the 'msg'
def popupmsg(msg):
    popup = Tk()
    popup.wm_title("Error!")
    label = Label(popup, text=msg, font=("Helvetica", 10))
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="Okay", command=popup.destroy)
    B1.pack()
    popup.mainloop()

# Actions to take when window is closed
def onClose():
  print('...Closing UBC Course Checker UI...')
  for process in processes:
    process.stop()
  app.destroy()
  sys.exit()

print('...Running UBC Course Checker UI...')

'''
Setup App UI Window basic settings
- title, size, onClose, resizable
'''
controller = RegistrationController()
processes = []
app = Tk()
app.title('UBC Course Checker')
app.protocol("WM_DELETE_WINDOW", onClose)
#You can set the geometry attribute to change the root windows size
app.geometry("750x560")
app.resizable(1, 1) #Allow resizing in the x or y direction

'''
Top half of the application - userFrame
- contains loginFrame, settingsFrame, and resetFrame
'''
userFrame = Frame(app)
userFrame.grid(row=0, column=0)

'''
Setup User submission area - loginFrame
'''
loginFrame = Frame(userFrame)
loginFrame.grid(row=0, column=0, sticky=N, pady=10, padx=2)

idLabel = Label(loginFrame, text="CWL Login ID").grid(row=0)
idInput = Entry(loginFrame)
idInput.grid(row=0, column=1)

idSubmit = Button(loginFrame, text='Submit', command=getUserInfo)
idSubmit.grid(row=0, column=2, sticky=W, padx=10)

pwLabel = Label(loginFrame, text="CWL Password")
pwLabel.grid(row=1)
pwInput = Entry(loginFrame, show="*")
pwInput.grid(row=1, column=1)

pwSubmit = Button(loginFrame, text='Register', command=registerUser)
pwSubmit.grid(row=1, column=2, sticky=W, padx=10)

'''
Setup User specific info area - settingsFrame
'''
settingsFrame = Frame(userFrame, bd=1, relief="solid")
settingsFrame.grid(row=0, column=1, sticky=W+N, pady=10, padx=2)

emailLabel = Label(settingsFrame, text="Email-Address:").grid(row=0, column=0)
emailInput = Entry(settingsFrame, width=25)
emailInput.grid(row=0, column=1)

delayLabel = Label(settingsFrame, text="Check every (seconds):").grid(row=1, column=0)
delayInput = Entry(settingsFrame, width=4)
delayInput.grid(row=1, column=1, sticky=W)

automaticLabel = Label(settingsFrame, text="Automatic Register:").grid(row=2, column=0)
registerAutomatic = BooleanVar()
autoRegButton = Checkbutton(settingsFrame, text='', variable=registerAutomatic)
autoRegButton.grid(row=2, column=1, sticky=W)

saveButton = Button(settingsFrame, text='Save', command=saveSettings).grid(row=3, column=1, sticky=E, padx=10, pady=5)


'''
Setup reset area - resetFrame
'''
resetFrame = Frame(userFrame)
resetFrame.grid(row=0, column=2, sticky=N, pady=10, padx=2)

resetPasswordButton = Button(resetFrame, text='Reset Password', command=resetPassword).grid(row=0, column=0)
resetPasswordInput = Entry(resetFrame, show="*", width=18)
resetPasswordInput.grid(row=0, column=1, sticky=W, padx=5)

completeReset = Button(resetFrame, text='Factory Reset', command=factoryReset).grid(row=1, column=0)
resetWarning = Label(resetFrame, text="[Run before sharing program]").grid(row=1, column=1)

'''
Setup the area to input course information - courseSettings Frame
  - courseInfo Frame - top half
  - courseOptions Frame - bottom half
'''
courseSettings = Frame(app, bd=1, relief="solid")
courseSettings.grid(row=1, column=0, pady=10)
courseInfo = Frame(courseSettings)
courseInfo.grid(row=0, column=0, pady=5)
courseOptions = Frame(courseSettings)
courseOptions.grid(row=1, column=0, pady=5)

sessionInput = Entry(courseInfo, width=10, bd=1, relief="solid")
deptInput = Entry(courseInfo, width=10, bd=1, relief="solid")
courseInput = Entry(courseInfo, width=10, bd=1, relief="solid")
sectionInput = Entry(courseInfo, width=10, bd=1, relief="solid")

sessionInput.insert(END, '2019W')
deptInput.insert(END, 'CPSC')
courseInput.insert(END, '110')
sectionInput.insert(END, '101')

acceptRestricted = BooleanVar()
acceptRestricted.set(False)
restrictedButton = Checkbutton(courseOptions, text="Accept Restricted", variable=acceptRestricted)

switchSection = BooleanVar()
switchSection.set(False)
switchButton = Checkbutton(courseOptions, text="Switch Section", variable=switchSection, command=switchInputDisplay, width=15)
switchInput = Entry(courseOptions, width=10, bd=1, relief="solid", state=DISABLED)

sessionInput.grid(row=0, column=0, padx=10, sticky=W)
deptInput.grid(row=0, column=1, padx=10, sticky=W)
courseInput.grid(row=0, column=2, padx=10, sticky=W)
sectionInput.grid(row=0, column=3, padx=10, sticky=W)

restrictedButton.grid(row=0, column=1, padx=10)
switchButton.grid(row=0, column=2, sticky=W, padx=5)
switchInput.grid(row=0, column=3, padx=5)
Button(courseOptions, text='Add Course', command=addCourse).grid(row=0, column=4, sticky=W, padx=5)

sessionInput.bind("<FocusIn>", lambda args: sessionInput.delete('0', 'end'))
deptInput.bind("<FocusIn>", lambda args: deptInput.delete('0', 'end'))
courseInput.bind("<FocusIn>", lambda args: courseInput.delete('0', 'end'))
sectionInput.bind("<FocusIn>", lambda args: sectionInput.delete('0', 'end'))
switchInput.bind("<FocusIn>", lambda args: switchInput.delete('0', 'end'))

'''
Setup Table Header Frame
'''
tableHeader = Frame(app, bd=1, relief="solid")
tableHeader.grid(row=2, sticky=W+S, padx=44)
Label(tableHeader, text="Session", width=10, height=1, bd=1, relief="solid").grid(row=0, column=0)
Label(tableHeader, text="Department", width=10, height=1, bd=1, relief="solid").grid(row=0, column=1)
Label(tableHeader, text="Course #", width=10, height=1, bd=1, relief="solid").grid(row=0, column=2)
Label(tableHeader, text="Section", width=10, height=1, bd=1, relief="solid").grid(row=0, column=3)
Label(tableHeader, text="Restricted", width=10, height=1, bd=1, relief="solid").grid(row=0, column=4)
Label(tableHeader, text="Switch From", width=10, height=1, bd=1, relief="solid").grid(row=0, column=5)
Label(tableHeader, text="Course Link", width=10, height=1, bd=1, relief="solid").grid(row=0, column=6)
Label(tableHeader, text="Status", width=10, height=1, bd=1, relief="solid").grid(row=0, column=7)

'''
Setup list of checking courses table
- canvas and scrollableTable Frame
'''
canvas = Canvas(app, bg='#D3D3D3', bd=1, relief='solid', width=700, height=300)
canvas.grid(row=3, sticky=W+E, padx=10)
scrollableTable = Frame(canvas, bg='#D3D3D3')

vertscroll = Scrollbar(canvas, orient='vertical', command=canvas.yview)
canvas.configure(yscrollcommand=vertscroll.set)

app.bind('<Configure>', lambda event, canvas=canvas: onFrameConfigure(canvas, event))
app.bind_all('<MouseWheel>', mouse_scroll)
app.bind_all('<Button-4>', mouse_scroll)
app.bind_all('<Button-5>', mouse_scroll)

canvas_frame = canvas.create_window((4, 4), window=scrollableTable, anchor="nw")
vertscroll.pack(side=RIGHT, fill=Y)
canvas.bind('<Configure>', lambda event, canvas_frame=canvas_frame: chat_width(event, canvas_frame))

'''
Setup Warning label - warningFrame
'''
warningFrame = Frame(app)
warningFrame.grid(row=4, column=0)
resetWarning = Label(warningFrame, text="Note: This program must be running in order to scan for seats.").grid(row=0, column=0, sticky=W)

# TODO include terminal window or not include.. hmmm

hideWidgets()

if __name__ == "__main__":
  app.mainloop()