import json
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import pytz
import requests

from commonfreehours.zapi.exceptions import *


def validate_instance(instance_id):
    # Validates the instance id. if incorrect, raises a zermelo value error

    # Regex to validate if its a correct subdomain
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'

    # Match pattern, raise exception if no match
    if re.match(pattern, instance_id) is None:
        raise ZermeloValueError(f"Incorrect instance id: {instance_id}")


def get_school_year(date = None):
    if date is None:
        date = datetime.now()
    if date.month < 8:
        # TODO: change to < 8 after testing
        return date.year - 1
    else:
        return date.year


class Zermelo:

    def __init__(self, api_version=3):
        self.logger = logging.getLogger(__name__)

        self.api_version = api_version

        self.logger.info(f"Instance created with api version {api_version}")

        self.instance_id = None
        self.token = None
        self.logged_in = False

        self._settings = {}
        self._user = None
        self.max_appointment_weeks = 52

    def require_setting(self, setting, value, endpoint=None, school_year=None):
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        if self.get_settings(school_year).get(setting) != value:
            raise ZermeloFunctionSettingsError(setting, self.get_settings().get(setting), value, endpoint)

    def get_schoolInSchoolYear(self, school_year=None):
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        return self.get_settings(school_year).get('schoolInSchoolYear')

    def get_user(self):
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        if self._user:
            return self._user

        self._user = self.send_request('GET', 'users/~me').get('data')[0]

        return self._user

    def get_settings(self, school_year=None):
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        if school_year is None:
            date = datetime.now()
            school_year = get_school_year(date)

        if self._settings.get(school_year):
            return self._settings.get(school_year)

        SISYs = self.get_user().get('schoolInSchoolYears')
        self.logger.info(f"SchoolInSchoolYears: {SISYs}")

        params = {
            "archived": "false",
            "schoolInSchoolYear": ",".join(map(str, SISYs)),
            "year": school_year,
            # "fields": "schoolInSchoolYear"
        }

        d = self.send_request('GET', 'schoolfunctionsettings', params=params)

        try:
            self._settings[school_year] = d.get('data')[0]
        except IndexError:
            raise ZermeloApiDataException('No response data in settings request.')

        return d.get('data')[0]

    def get_appointments(self, start: int, end: int, user: str, is_teacher: bool = False, valid_only: bool = True):
        # Gets the raw schedule from the api

        self.logger.info("method get_appointments called")

        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        self.require_setting(f"{'student' if self.get_user().get('isStudent') else 'employee'}CanViewProjectSchedules",
                             True, 'appointments', get_school_year(datetime.fromtimestamp(start, tz=pytz.timezone('Europe/Amsterdam'))))

        params = {
            'start': int(start),
            'end': int(end),
            'teachers' if (is_teacher) else 'possibleStudents': user
        }

        if valid_only:
            params['valid'] = True
            params['cancelled'] = False

        try:
            d = self.send_request('GET', 'appointments', params=params)
        except ZermeloApiHttpStatusException as e:
            # Not allowed to search for value, possibly due to summer holidays?
            if e.status == 403:
                raise ZermeloApiDataException(
                    'No response data in appointments request due to 403 (forbidden). Check if you can access the schedules in the zermelo portal.')
            raise e

        try:
            return d.get('data')
        except AttributeError:
            raise ZermeloApiDataException('No response data in appointments request.')

    def get_current_weeks_appointments(self, user: str, is_teacher: bool = False, weeks: int = 1,
                                       valid_only: bool = False, fix_403: bool = True,
                                       max_weeks_optimization: bool = True, max_weeks_optimization_original_weeks: int = None):
        self.logger.info("method get_current_weeks_appointments called")

        if max_weeks_optimization_original_weeks is None:
            max_weeks_optimization_original_weeks = weeks

        # The appointments of the current week
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        self.require_setting(f"{'student' if self.get_user().get('isStudent') else 'employee'}CanViewProjectSchedules",
                             True, 'appointments', get_school_year(datetime.now()))

        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        end = start + timedelta(days=6 + 7 * (weeks - 1), hours=23, minutes=59, seconds=59)

        try:
            appointments = self.get_appointments(start.timestamp(), end.timestamp(), user, is_teacher, valid_only)

            if weeks != max_weeks_optimization_original_weeks:
                self.max_appointment_weeks = weeks

            return appointments
        except ZermeloApiDataException as e:

            if fix_403 and '403' in str(e) and weeks > 1:

                if max_weeks_optimization:
                    weeks = min(weeks - 1, self.max_appointment_weeks)
                else:
                    weeks -= 1

                return self.get_current_weeks_appointments(user, is_teacher, weeks, valid_only, True,
                                                           max_weeks_optimization, max_weeks_optimization_original_weeks)
            else:
                raise e

    def get_students(self, school_year: int = None, fields: str = None):
        self.logger.info("method get_students called")
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        if self.get_user().get('isStudent'):
            # TODO: check if this is the right one
            self.require_setting('studentCanViewProjectSchedules', True, 'studentsindepartments', school_year)
        else:
            self.require_setting('employeeCanViewProjectSchedules', True, 'studentsindepartments', school_year)

        params = {
            "schoolInSchoolYear": self.get_settings(school_year).get('schoolInSchoolYear'),
            "isStudent": "true",
            "fields": fields
        }
        try:
            d = self.send_request('GET', 'users', params=params)
        except ZermeloApiHttpStatusException as e:
            # Not allowed to search for value, possibly due to summer holidays?
            if e.status == 403:
                raise ZermeloApiDataException(
                    'No response data in students request due to 403 (forbidden). Check if you can access the schedules in the zermelo portal.')
            raise e
        return d.get('data')

    def get_teachers(self, school_year: int = None, fields: str =None):
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        if self.get_user().get('isStudent'):
            # TODO: check if this is the right one
            self.require_setting('studentCanViewRelatedTeacherSchedules', True, 'contracts', school_year)
        else:
            self.require_setting('employeeCanViewColleagueSchedules', True, 'contracts', school_year)

        params = {
            "schoolInSchoolYear": self.get_settings(school_year).get('schoolInSchoolYear'),
            "isEmployee": "true",
            "fields": fields
        }
        try:
            d = self.send_request('GET', 'users', params=params)
        except ZermeloApiHttpStatusException as e:
            # Not allowed to search for value, possibly due to summer holidays?
            if e.status == 403:
                raise ZermeloApiDataException(
                    'No response data in students request due to 403 (forbidden). Check if you can access the schedules in the zermelo portal.')
            raise e
        return d.get('data')

    def send_request(self, method, endpoint, params={}, data={}, headers={}):
        # Send requests, once logged in
        self.logger.info("method send_request called")

        url = f'https://{self.instance_id}.zportal.nl/api/v{self.api_version}/{endpoint.strip()}'

        params['access_token'] = self.token

        # Stop if not logged in
        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        # Sending the request
        self.logger.info(f"Request: {method} {url}")
        self.logger.debug(f"Request params: {params}")
        self.logger.debug(f"Request data: {data}")
        self.logger.debug(f"Request headers: {headers}")

        # Choose request method
        try:

            if method.upper() == 'GET':
                r = requests.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                r = requests.post(url, params=params, json=data, headers=headers)
            elif method.upper() == 'PUT':
                r = requests.put(url, params=params, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                r = requests.delete(url, params=params, headers=headers)

        except requests.exceptions.ConnectionError:
            raise ZermeloApiNetworkError("Could not reach the zermelo servers")

        self.logger.info(f"Request response: {r}")
        self.logger.debug(f"Response url: {r.url}")
        # self.logger.debug(f"Request body: {r.text}")

        # Stop if request returned an http error code
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if r.status_code == 401:
                # Unauthorised, token is expired
                self.token = None
                self.instance_id = None
                self.logged_in = False

                raise ZermeloAuthException('Session expired')
            raise ZermeloApiHttpStatusException(r.status_code, r.text)

        # Return request data if exist
        try:
            return r.json().get('response')
        except json.decoder.JSONDecodeError:
            return r.text

    def check_token(self, token, instance_id, min_seconds_left=60 * 60):
        # Check if a token is valid
        self.logger.info("method check_token called")

        instance_id = instance_id.strip()
        validate_instance(instance_id)

        self.logger.debug(f"Validating token {token} on {instance_id}")

        try:
            now_seconds = (datetime.now() - datetime(1970, 1, 1)).total_seconds()

            url = f'https://{instance_id}.zportal.nl/api/v{self.api_version}/tokens/~current?access_token={token}'

            try:
                r = requests.get(url, allow_redirects=False)
                r.raise_for_status()
                expires_seconds = r.json().get('response').get('data')[0].get('expires')

            except requests.exceptions.ConnectionError:
                raise ZermeloApiNetworkError("Could not reach the zermelo servers")

            except requests.exceptions.HTTPError:
                # TODO: HTTP 500 zermelo bug
                if r.status_code == 404:
                    self.logger.error(f"Instance {instance_id} does not exist.")
                    raise ZermeloValueError(f"Incorrect instance id: {instance_id}")

                raise ZermeloApiHttpStatusException(r.status_code, r.text)

            if expires_seconds - now_seconds > min_seconds_left:
                self.logger.info(f"Token expires in {timedelta(seconds=expires_seconds - now_seconds)}")
                return True
            self.logger.info(f"Expired token: {token}")
            return False

        except (AttributeError, IndexError, json.decoder.JSONDecodeError) as e:
            self.logger.info(f"Invalid token: {token}")
            return False

    def token_login(self, token, instance_id, check=True):
        # Logs in using the users token. Token validation can be disabled.
        self.logger.info("method token_login called")

        instance_id = instance_id.strip()
        validate_instance(instance_id)

        if check and not self.check_token(token, instance_id):
            raise ZermeloAuthException(f"Invalid token: {token} for instance {instance_id}")

        self.token = token
        self.logger.debug(f"Set token: {self.token}")

        self.instance_id = instance_id
        self.logger.debug(f"Set instance id: {self.instance_id}")

        self.logged_in = True
        self.logger.debug(f"Set logged in: True")

        self.logger.info("Logged in")

    def password_login(self, instance_id, user, password):
        # Logs in using the users password. Zermelo doesnt allow this for everyone, so check their docs.
        self.logger.warning("method password_login called")

        instance_id = instance_id.strip()
        user = user.strip()
        password = password.strip()

        validate_instance(instance_id)

        # Send a request with the credentials
        data = {
            'username': user,
            'password': password,
            'client_id': 'OAuthPage',
            'redirect_uri': '/main/',
            'scope': '',
            'state': '4E252A',
            'response_type': 'code',
            'tenant': instance_id
        }
        url = f'https://{instance_id}.zportal.nl/api/v{self.api_version}/oauth'

        try:
            r = requests.post(url, data=data, allow_redirects=False)
            r.raise_for_status()

        except requests.exceptions.ConnectionError:
            raise ZermeloApiNetworkError("Could not reach the zermelo servers")

        except requests.exceptions.HTTPError as e:
            if r.status_code == 500:
                self.logger.error(f"Instance {instance_id} does not exist.")
                raise ZermeloValueError(f"Incorrect instance id: {instance_id}")
            else:
                raise e

        self.logger.debug(f"Request POST /oath: {r}")

        # Get the url containing the authentication code
        try:
            data_url = r.headers['Location']
        except (AttributeError, KeyError):
            data_url = r.text

            if r.text.strip() == '':
                raise ZermeloApiDataException('No data url forwarded in auth request.')

        # Parse url to get the authentication code
        parsed_data_url = parse_qs(urlparse(data_url).query)

        try:
            code = parsed_data_url.get('code')[0]
        except TypeError:
            # NoneType is not subscriptable
            raise ZermeloAuthException("Incorrect password or user name")

        self.logger.debug(f"Parsed authentication code: {code}")

        self.code_login(code, instance_id)

    def code_login(self, code, instance_id):
        # Logs in using the 'connect app' code
        self.logger.info("method code_login called")

        code = code.strip()

        instance_id = instance_id.strip()
        validate_instance(instance_id)

        # Send a request with the code to get the token.
        # TODO: client secret
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'rememberMe': True
        }
        url = f'https://{instance_id}.zportal.nl/api/v{self.api_version}/oauth/token'

        try:
            r = requests.post(url, data=data)
            r.raise_for_status()

        except requests.exceptions.ConnectionError:
            raise ZermeloApiNetworkError("Could not reach the zermelo servers")

        except requests.exceptions.HTTPError:
            if r.status_code == 404:
                self.logger.error(f"Instance {instance_id} does not exist.")
                raise ZermeloValueError(f"Incorrect instance id: {instance_id}")
            elif r.status_code == 400:
                # Workaround zermelo bug returning Body: b'{"response":{"status":400,"message":"The request was syntactically incorrect. Did you provide valid JSON?"}}'
                # when the linkcode is expired
                raise  ZermeloAuthException("Invalid linkcode")
            raise ZermeloApiHttpStatusException(r.status_code, r.content)

        self.logger.debug(f"Request POST /oath/token: {r}")

        jsondata = json.loads(r.text)

        token = jsondata.get('access_token', '')

        # Invalid link code?
        if token == '':
            raise ZermeloAuthException('Linkcode expired.')

        # Log in with token, dont validate because the token is correct
        self.token_login(token, instance_id, False)

    def logout(self, logged_out_ok=True):
        self.logger.info("method logout called")

        try:
            # Log the current token out
            self.send_request('POST', 'oauth/logout')

            # Set logged in to False
            self.token = None
            self.instance_id = None
            self.logged_in = False

            self._settings = {}
            self._user = None
            self.max_appointment_weeks = 52

            self.logger.info("Logged out")
        except ZermeloAuthException as e:
            if logged_out_ok:
                self.logger.warn("Not logged in while logging out")
            else:
                raise e

    def get_token(self):
        # Returns the token for later usage
        self.logger.info("method get_token called")

        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        return self.token

    def get_instance_id(self):
        # Returns the instance id for later usage
        self.logger.info("method get_instance_id called")

        if not self.logged_in:
            raise ZermeloAuthException('Not logged in')

        return self.instance_id
