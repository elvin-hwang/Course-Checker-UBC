# UBC Course Checker

UBC Course Checker works to determine the number of remaining seats available in a course. The script can then either register in the course automatically or simply notify (open the course link).

To minimize the need to install extra modules like mechanize or requests for people who may not be tech-savy, only libraries that are already part of Python's Standard Library are included.

## Usage
The script supports both python 2.7 and python 3.5.

Double click "courseChecker.pyw" to open the GUI

Or open the directory to where "courseChecker.py" is on your terminal or command prompt
And then run "python courseChecker.pyw".
Note that you don't need to keep the terminal window open, just the program.

Some notes:

* RECOMMENDED to test with a course that is already open first, just to verify that it works. 
    * Email "courseopen@gmail.com" for any problems.
* Once you have added a course to the list, click on the URL to verify that it has been added successfully.
    *  Otherwise, double check the course and section on SSC and try again
* Logs you in only once when a course is open for registration, so it's (relatively) safe to use with not a lot of risks.
    *  If you want 0 risk, then simply uncheck the "Automatic Register" button.
* It will only ATTEMPT to register, but it may not succeed for any of the following reasons:
    *  You are registered in the waitlist for that course
    *  You have a conflicting time schedule with another course
    *  SSC Course Schedule went down for maintenance or crashed
    *  The course you have entered is not valid
* Please try and enter only correct values for each input, there's no catching protocol for incorrectly formatted input

* Mac users: If you want to keep your laptop awake until it registers you (or you terminate the process), use: 
    <code>caffeinate -i -s python courseChecker.py</code>. The screen will turn off but python will keep running. This will enable the script to keep running when the laptop is plugged in and sleeping overnight.
* Windows users: there are other programs that you can download (optional), if you want to keep your windows awake, such as this one - https://www.zhornsoftware.co.uk/caffeine/. 
