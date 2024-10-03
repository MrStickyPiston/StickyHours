import logging
from datetime import datetime

import pytz

from stickyhours.zapi import Zermelo


def process_appointments(appointments, user_id) -> dict:
    # Preprocesses the appointments for getting the gaps
    days = {}
    gaps = {}

    previous_slot = None
    previous_time = None

    appointments.sort(key=lambda arr: arr.get('start'))

    for a in appointments:
        # Check if list is empty
        if not a.get('groups'):

            if not user_id in a.get('teachers'):
                logging.info(f'No group for appointment: {a}')
                logging.info(f'User not in teachers list for this appointment, skipping hour. (subjects: {a.get('subjects')})')
                continue
            else:
                logging.info(f'No group for this appointment but {user_id} is in teachers list: {a}')

        s = a["startTimeSlot"]
        e = a["endTimeSlot"]

        st = datetime.fromtimestamp(a.get('start'), tz=pytz.timezone('Europe/Amsterdam'))
        et = datetime.fromtimestamp(a.get('end'), tz=pytz.timezone('Europe/Amsterdam'))

        d = str(datetime.fromtimestamp(a.get('start'), tz=pytz.timezone('Europe/Amsterdam')).date())

        if s is None or e is None:
            print(f"Appointment without start or end timeslot: {a}")
            continue

        if days.get(d) is None:
            days[d] = []

        if gaps.get(d) is None:
            gaps[d] = []

        elif previous_slot[1] + 1 < s:
            gaps[d].append([[previous_slot[1] + 1, s - 1], [previous_time[1], st]])

        previous_slot = [s, e]
        previous_time = [st, et]



        days[d].append([s, e])
    return gaps

def get_common_gaps(*gaps) -> dict[list] | dict:
    # Returns common gaps between gap lists in a days dict
    # UNSORTED!

    common_gaps = {}

    if len(gaps) == 0:
        return common_gaps

    elif len(gaps) == 1:
        for date in gaps[0].keys():
            for gap in gaps[0].get(date):
                if common_gaps.get(date) is None:
                    common_gaps[date] = []
                common_gaps.get(date).append(gap)
        return common_gaps

    # Convert tuple to list
    gaps_list = list(gaps)

    # Start with the first gap
    result = gaps_list[0]

    # Iterate through the remaining gaps
    for i in range(1, len(gaps_list)):
        new_common_gaps = {}
        gaps_b = gaps_list[i]

        # Iter through all days
        for date in set(result.keys()).union(set(gaps_b.keys())):
            if not result.get(date) or not gaps_b.get(date):
                continue
            for gap_a in result.get(date):
                for gap_b in gaps_b.get(date):
                    overlap_start_slot = max(gap_a[0][0], gap_b[0][0])
                    overlap_end_slot = min(gap_a[0][1], gap_b[0][1])

                    if overlap_start_slot <= overlap_end_slot:
                        # Create day if it does not exist
                        if new_common_gaps.get(date) is None:
                            new_common_gaps[date] = []

                        # Add gap to list
                        new_common_gaps[date].append([[overlap_start_slot, overlap_end_slot], [max(gap_a[1][0], gap_b[1][0]), min(gap_a[1][1], gap_b[1][1])]])

        result = new_common_gaps

    return result

def get_accounts(zermelo: Zermelo, school_year: int):
    students = zermelo.get_students(school_year)
    teachers = zermelo.get_teachers(school_year)

    accounts = []

    for teacher in teachers:
        name = f"{teacher['prefix']} {teacher['lastName']}" if teacher['prefix'] else f"{teacher['lastName']}"
        accounts.append({"name": f"{name} ({teacher['code']})", "id": teacher['code'], 'teacher': True})

    for student in students:
        name = []

        if not zermelo.get_user().get('isStudent') or zermelo.get_settings().get('studentCanViewProjectNames'):
            # can use student names
            name.append(student.get('firstName'))

            if student.get('prefix'):
                name.append(student.get('prefix'))

            name.append(student.get('lastName'))
            name.append(f'({student.get('code')})')
        else:
            name.append(student.get('code'))

        accounts.append({"name": " ".join(name), "id": student['code'], 'teacher': False})

    return accounts