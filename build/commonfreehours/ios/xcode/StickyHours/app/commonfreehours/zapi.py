# from calendar import weekday
import os.path
import requests
import json
import time
import base64
# from datetime import datetime
import datetime


class zermelo:
    expires_in = 0
    school = ''
    username = ''
    teacher = False
    debug = False
    TimeToAddToUtc = 0

    def __init__(self, school, username, password=None, teacher=False, version=3, debug=False, linkcode=None,
                 token_file='./token'):
        self.school = school
        self.username = username
        self.teacher = teacher
        self.debug = debug
        self.version = 'v' + str(version)
        self.TimeToAddToUtc = self.get_date()[2]
        self.token_file = token_file

        self.token = self.gettokenfromfile(linkcode=linkcode, password=password)

    def updatetoken(self, linkcode):
        self.token = self.gettokenfromfile(linkcode=linkcode)

    def gettokenfromlinkcode(self, linkcode=None):
        if linkcode == None:
            raise ValueError('Incorrect linkcode')
        else:
            linkcode = str(linkcode).replace(" ", '')
        return json.loads(requests.post(
            f"https://ozhw.zportal.nl/api/v3/oauth/token?grant_type=authorization_code&code={linkcode}").text)[
            "access_token"]

    def get_tokenfromusrpsw(self, school=None, username=None, password=None):
        if (school == None):
            school = self.school
        if (username == None):
            username = self.username

        url = 'https://' + school + '.zportal.nl/api/' + self.version + '/oauth'
        myobj = {'username': username, 'password': password, 'client_id': 'OAuthPage', 'redirect_uri': '/main/',
                 'scope': '', 'state': '4E252A', 'response_type': 'code', 'tenant': school}
        x = requests.post(url, data=myobj, allow_redirects=False)
        if self.debug:
            print(x.text)
        try:
            respons = x.headers['Location']
        except:
            respons = x.text
        # exit(0)
        # exit(0)
        start = respons.find("code=") + len("code=")
        end = respons.find("&", start)
        token = respons[start:end]
        start = respons.find("tenant=") + len("tenant=")
        end = respons.find("&", start)
        school = respons[start:end]
        start = respons.find("expires_in=") + len("expires_in=")
        end = respons.find("&", start)
        self.expires_in = respons[start:end]
        start = respons.find("loginMethod=") + len("loginMethod=")
        end = respons.find("&", start)
        self.loginMethod = respons[start:end]
        start = respons.find("interfaceVersion=") + len("interfaceVersion=")
        end = respons.find("&", start)
        self.interfaceVersion = respons[start:end]
        if (school == None):
            school = self.school
        if (token == None):
            token = self.get_token()
        if self.debug:
            print(token)
        url = f'https://{self.school}.zportal.nl/api/{self.version}/oauth/token'
        myobj = {'code': token, 'client_id': 'ZermeloPortal', 'client_secret': 42,
                 'grant_type': 'authorization_code', 'rememberMe': True}
        if self.debug:
            print("\n\n")
        if self.debug:
            print(myobj, url)
        l = requests.post(url, data=myobj)
        if self.debug:
            print(l.text)
        jl = json.loads(l.text)

        try:
            token = jl['access_token']
        except KeyError:
            raise ValueError('Error during auth')

        self.settokentofile(token)

        return token

    def gettokenfromfile(self, linkcode=None, password=None):
        if not os.path.exists(self.token_file):
            if linkcode is None and password != None:
                self.token = self.get_tokenfromusrpsw(school=self.school, username=self.username, password=password)
            else:
                self.settokentofile(linkcode=linkcode)
            return

        with open(self.token_file) as f:
            filevalue = f.read()

        print(f'read token from path: {self.token_file}')

        return str(base64.b64decode(filevalue))[2:-1]

    def settokentofile(self, token=None, linkcode=None):
        if token == None:
            token = self.gettokenfromlinkcode(linkcode=linkcode)
        file = str(base64.b64encode(bytes(token, "utf-8")))[2:-1]
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, "w") as f:
            f.write(str(file))

        print(f'wrote token to path: {self.token_file}')

    def get_date(self):
        now = datetime.datetime.now()
        return (now.year, now.isocalendar()[1], int((datetime.datetime.fromtimestamp(
            now.timestamp()) - datetime.datetime.utcfromtimestamp(now.timestamp())).total_seconds() / 3600))

    def get_raw_schedule(self, year: int = None, week: int = None, username: str = None, teacher: bool = False, weeks=2) -> dict:
        time = self.get_date()
        if year == None:
            year = time[0]
        if week == None:
            week = time[1]

        # indexing starts at 0 apparently
        week -= 1

        if username == None:
            url = f"https://{self.school}.zportal.nl/api/v3/liveschedule?access_token={self.token}&{'teacher' if (self.teacher) else 'student'}={self.username}&week={year}{week:0>2}"
        else:
            start = str(datetime.datetime.strptime(f"{year}-{week}-0", "%Y-%U-%w").timestamp())[0:-2]
            end = str(datetime.datetime.strptime(f"{year}-{week + weeks - 1}-6", "%Y-%U-%w").timestamp())[0:-2]
            url = f"https://{self.school}.zportal.nl/api/v3/appointments?access_token={self.token}&start={start}&end={end}&{'teachers' if (teacher) else 'possibleStudents'}={username}"
        rawr = requests.get(url)
        if self.debug:
            print(rawr)
        rl = json.loads(rawr.text)

        if rl.get('response', {}).get('status') == 401:
            raise ValueError('Zermelo authentication error')

        return rl

    def get_schedule(self, rawschedule: dict = None, year=None, week=None, username=None, teacher=None):
        if rawschedule == None:
            rawschedule = self.get_raw_schedule(year=year, week=week, username=username, teacher=teacher)
        response = rawschedule["response"]
        if username != None:
            appointments = response["data"]
        else:
            data = response["data"][0]
            appointments = data["appointments"]
        return (appointments)

    def sort_schedule(self, schedule=None, year=None, week=None, username=None, teacher=None, only_valid=True):
        if (schedule == None):
            schedule = self.get_schedule(year=year, week=week, username=username, teacher=teacher)
        pdate = 0
        days = [[[], [], []]]
        thisweek = {}
        for les in schedule:
            date = datetime.datetime.utcfromtimestamp(les["start"]).strftime('%Y%m%d')
            hour = str(int(datetime.datetime.utcfromtimestamp(
                les["start"]).strftime('%H')) + self.TimeToAddToUtc)
            time = datetime.datetime.utcfromtimestamp(les["start"]).strftime('%Y-%m-%d ') + (hour if int(
                hour) > 9 else ('0' + hour)) + datetime.datetime.utcfromtimestamp(les["start"]).strftime(':%M')
            ehour = str(int(datetime.datetime.utcfromtimestamp(
                les["end"]).strftime('%H')) + self.TimeToAddToUtc)
            etime = datetime.datetime.utcfromtimestamp(les["end"]).strftime('%Y-%m-%d ') + (ehour if int(
                ehour) > 9 else ('0' + ehour)) + datetime.datetime.utcfromtimestamp(les["end"]).strftime(':%M')
            # print(les["status"])
            if username != None:
                code = 2002

                if not les["groups"]:
                    continue

                if only_valid and les["cancelled"] or not les["valid"] or les["moved"] or les["modified"]:
                    continue

                if les["cancelled"] or not les["valid"]:
                    code = 4007
                elif les["moved"]:
                    code = 3012
                elif les["modified"]:
                    code = 3011
                if not date in thisweek:
                    thisweek[date] = [[], []]
                if (not les["cancelled"] and les["valid"]):
                    thisweek[date][0].append([les["subjects"][0], time, etime,
                                              str(les["locations"]), [{"code": code}], False])
                else:
                    thisweek[date][1].append([les["subjects"][0], time, etime,
                                              str(les["locations"]), [{"code": code}], False])
            else:
                if date != pdate:
                    days.append([[], [], []])
                if self.debug:
                    print(les)  #,les["appointmentType"])
                    # pass

                for appointment in (les["actions"] if les["appointmentType"] == "choice" else [
                    {'appointment': les, 'status': les['status']}]):
                    app = appointment["appointment"]
                    if app != None and (len(appointment["status"]) > 0):
                        if (appointment["status"][0]["code"] < 4000 and appointment["status"][0]["code"] >= 2000):
                            days[-1][0].append([app["subjects"][0], time, etime,
                                                str(app["locations"]), appointment["status"], app["online"], "",
                                                app["id"]])
                        elif (appointment["status"][0]["code"] == 1004):
                            days[-1][2].append([app["subjects"][0], time, etime,
                                                str(app["locations"]), appointment["status"], app["online"],
                                                appointment["post"], app["id"]])
                        else:
                            days[-1][1].append([app["subjects"][0], time, etime,
                                                str(app["locations"]), appointment["status"], app["online"], "",
                                                app["id"]])
            pdate = date
        if username != None:
            thisweekdayssorted = [thisweek[i] for i in [str(c) for c in sorted([int(i) for i in thisweek.keys()])]]
            days = []
            for v in thisweekdayssorted:
                part = []
                for v2 in v:
                    part.append(sorted(v2, key=lambda x: int(x[1].replace(":", "").replace("-", "").replace(" ", ""))))
                days.append(part)
        else:
            days.pop(0)
        return (days)

    def enroll(self, les=None, lesid=0):
        if les == None and lesid == 0:
            return False
        url = f"https://{self.school}.zportal.nl{les[6] if lesid == 0 else f'/api/v3/liveschedule/enrollment?enroll={lesid}'}&access_token={self.token}"
        if self.debug:
            print(url)
        req = requests.post(url)
        if self.debug:
            print(req, req.text)
        return True

    def unenroll(self, les=None, lesid=0):
        if les == None and lesid == 0:
            return False
        url = f"https://{self.school}.zportal.nl{str(les[6]).replace('&unenroll=', '').replace('enroll', 'unenroll') if lesid == 0 else f'/api/v3/liveschedule/enrollment?unenroll={lesid}'}&access_token={self.token}"
        if self.debug:
            print(url)
        req = requests.post(url)
        if self.debug:
            print(req, req.text)
        return True

    def readable_schedule(self, days=None, year=None, week=None, username=None, teacher=None):
        result = ''
        if (days == None):
            days = self.sort_schedule(year=year, week=week, username=username, teacher=teacher)
        daysofweek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for i, day in enumerate(days):
            if len(day[0]) > 0:
                result += (daysofweek[i] + "\nstart: " + day[0][0][1] + "\tend: " + day[0][-1][2] + '\n')
            else:
                result += (f"{daysofweek[i]}\n")
            for les in day[0]:
                # if (les[4][0]["code"] < 4000 and les[4][0]["code"] >= 2000):
                if True:
                    result += f"les: {les[0].ljust(8, ' ')}  lokaal: {('📷' if (les[5]) else (les[3][2:-2] if (len(les[3][2:-2]) > 0) else '----')).ljust(8, ' ')}  start: {les[1]}\tend: {les[2]}\n"
                    pass
            result += ("\n\n")
        return result

    def print_schedule(self, readable=None, days=None, year=None, week=None, username=None, teacher=None):
        if (readable == None):
            readable = self.readable_schedule(days=days, year=year, week=week, username=username, teacher=teacher)
        print(readable)

    @staticmethod
    def get_school_year_start(date):
        year = date.year
        if date.month < 9:
            return year - 1
        else:
            return year

    def getSchoolInSchoolYears(self):
        url = f"https://cvo-nf.zportal.nl/api/v3/users/~me?access_token={self.token}&fields=code,displayName,schoolInSchoolYears"

        if self.debug:
            print(url)
        rawr = requests.get(url)
        if self.debug:
            print(rawr)
        rl = json.loads(rawr.text)

        if rl.get('response', {}).get('status') == 401:
            raise ValueError('Zermelo authentication error')

        return rl.get('response').get('data')[0].get('schoolInSchoolYears')

    def getSchoolInSchoolYear(self, schoolInSchoolYears):
        school_year = self.get_school_year_start(datetime.datetime.now())
        url = f"https://cvo-nf.zportal.nl/api/v3/schoolfunctionsettings?access_token={self.token}&archived=false&schoolInSchoolYear={",".join(map(str, schoolInSchoolYears))}&year={school_year}&fields=schoolInSchoolYear"
        rawr = requests.get(url)
        if self.debug:
            print(rawr)
        rl = json.loads(rawr.text)

        if rl.get('response', {}).get('status') != 200:
            raise ValueError('Zermelo authentication error')

        return rl.get('response').get('data')[0].get('schoolInSchoolYear')

    def getStudents(self, schoolInSchoolYear):
        school_year = self.get_school_year_start(datetime.datetime.now())
        url = f"https://cvo-nf.zportal.nl/api/v3/studentsindepartments?access_token={self.token}&schoolInSchoolYear={schoolInSchoolYear}&fields=student,firstName,prefix,lastName,mainGroupName,mainGroup,mentorGroup,departmentOfBranch"
        rawr = requests.get(url)
        if self.debug:
            print(rawr)
        rl = json.loads(rawr.text)

        if rl.get('response', {}).get('status') != 200:
            raise ValueError('Zermelo error')

        return rl.get('response').get('data')

    def getTeachers(self, schoolInSchoolYear):
        school_year = self.get_school_year_start(datetime.datetime.now())
        url = f"https://cvo-nf.zportal.nl/api/v3/contracts?access_token={self.token}&schoolInSchoolYear={schoolInSchoolYear}&fields=employee,prefix,lastName,schoolInSchoolYear,mainBranchOfSchool"
        rawr = requests.get(url)
        if self.debug:
            print(rawr)
        rl = json.loads(rawr.text)

        if rl.get('response', {}).get('status') != 200:
            raise ValueError('Zermelo error')

        return rl.get('response').get('data')

    def getAccounts(self, schoolInSchoolYear):
        raw_students = self.getStudents(schoolInSchoolYear)
        raw_teachers = self.getTeachers(schoolInSchoolYear)

        accounts = []

        for teacher in raw_teachers:
            name = f"{teacher['prefix']} {teacher['lastName']}" if teacher['prefix'] else f"{teacher['lastName']}"
            accounts.append({"name": f"{name} ({teacher['employee']})", "id": teacher['employee'], 'teacher': True})

        # Process the student list
        for student in raw_students:
            name = f"{student['firstName']} {student['prefix']} {student['lastName']}" if student['prefix'] else f"{student['firstName']} {student['lastName']}"
            accounts.append({"name": f"{name} ({student['student']})", "id": student['student'], 'teacher': False})

        return accounts