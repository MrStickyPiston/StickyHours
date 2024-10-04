import logging
from datetime import datetime
from typing import List, TypedDict

import pytz

from stickyhours.zapi import Zermelo

class Appointment(TypedDict):
    appointmentInstance: int
    branch: str
    branchOfSchool: int
    cancelled: bool
    changeDescription: str
    created: int
    end: int
    groups: List[str]
    groupsInDepartments: List[int]
    hidden: bool
    id: int
    lastModified: int
    locations: List[str]
    locationsOfBranch: List[int]
    modified: bool
    moved: bool
    new: bool
    remark: str
    start: int
    subjects: List[str]
    teachers: List[str]
    type: str
    valid: bool

    endTimeSlot: int
    endTimeSlotName: str
    startTimeSlot: int
    startTimeSlotName: str


class Response(TypedDict):
    data: List[Appointment]
    details: str
    endRow: int
    eventId: int
    message: str
    startRow: int
    status: int
    totalRows: int


class WrappedResponse(TypedDict):
    response: Response


type timeslot = dict[str, int]


class ProcessedAppointments(TypedDict):
    timeslots: dict[str, timeslot]
    daily_appointments: dict[str, List[Appointment]]
    days: list[str]

def is_valid_appointment(appointment: Appointment, user_id: str) -> bool:
    if not appointment.get('groups'):

        if not user_id in appointment.get('teachers'):
            logging.info(f'No group for appointment: {appointment}')
            logging.info(
                f'User not in teachers list for this appointment, skipping hour. (subjects: {appointment.get('subjects')})')
            return False
        else:
            logging.info(f'No group for this appointment but {user_id} is in teachers list: {appointment}')

    return True


def process_user_data(appointments: List[Appointment], user_id: str) -> ProcessedAppointments:
    timeslots: dict[str, dict[str, int]] = {}
    daily_appointments: dict[str, list[Appointment]] = {}

    for appointment in appointments:

        if not is_valid_appointment(appointment, user_id):
            continue

        date = str(datetime.fromtimestamp(
            appointment.get('start'), tz=pytz.timezone('Europe/Amsterdam')).date()
                   )

        if not timeslots.get(date):
            timeslots[date] = {
                'start': appointment.get('startTimeSlot'),
                'end': appointment.get('endTimeSlot')
            }

        else:
            timeslots[date]['start'] = min(timeslots[date]['start'], appointment.get('startTimeSlot'))
            timeslots[date]['end'] = max(timeslots[date]['end'], appointment.get('endTimeSlot'))

        if not daily_appointments.get(date):
            daily_appointments[date] = []

        daily_appointments[date].append(appointment)

    return {
        'timeslots': timeslots,
        'daily_appointments': daily_appointments,
        'days': list(timeslots.keys())
    }

def get_common_gaps(data: list[ProcessedAppointments], sticky_hours: int = 0) -> dict[str, list[dict[str, int]]]:
    common_dates: set = set.intersection(*[set(user_data['days']) for user_data in data])
    common_dates: list[str] = sorted(list(common_dates))

    merged_days: dict[str, dict] = {}

    # Merge data into dates
    for date in common_dates:
        # Process each common date
        logging.info(f'Processing date: {date}')

        merged_days[date] = {}

        for user_data in data:
            day = user_data.get('daily_appointments').get(date)

            for appointment in day:

                for i in range(appointment.get('startTimeSlot'), appointment.get('endTimeSlot') + 1):
                    if not merged_days[date].get(i):
                        merged_days[date][i] = {
                            'start': appointment.get('start'),
                            'end': appointment.get('end')
                        }
                    else:
                        merged_days[date][i]['start'] = min(merged_days[date][i]['start'], appointment.get('start'))
                        merged_days[date][i]['end'] = max(merged_days[date][i]['end'], appointment.get('end'))


    minimum_day_slots: dict[str, dict] = {}

    for date in common_dates:
        for user_data in data:
            slot = user_data.get('timeslots').get(date)

            if not minimum_day_slots.get(date):
                minimum_day_slots[date] = slot
            else:
                minimum_day_slots[date]['start'] = max(minimum_day_slots[date]['start'], slot['start'])
                minimum_day_slots[date]['end'] = min(minimum_day_slots[date]['end'], slot['end'])

    gaps: dict[str, list[dict[str, int]]] = {}

    for date in sorted(merged_days.keys()):
        logging.info(f'Processing common gaps: {date}')
        previous_slot_number: int | None = None
        for slot_number in sorted(merged_days[date].keys()):

            if previous_slot_number is None:
                pass
            elif slot_number - previous_slot_number > 1:

                start_slot = previous_slot_number + 1
                end_slot = slot_number - 1

                logging.info(f'Gap found at slot {start_slot} - {end_slot}')

                # Make sure the gap is not outside the minimum day slots
                if not minimum_day_slots[date]['start'] - sticky_hours <= start_slot:
                    logging.info(f'Gap start {start_slot} is lower than minimum {minimum_day_slots[date]['start'] - sticky_hours} on date {date}')
                    continue
                if not start_slot <= minimum_day_slots[date]['end'] + sticky_hours:
                    logging.info(f'Gap start {start_slot} is higher than maximum {minimum_day_slots[date]['end'] + sticky_hours} on date {date}')
                    continue

                if not minimum_day_slots[date]['start'] - sticky_hours <= end_slot:
                    logging.info(
                        f'Gap end {end_slot} is lower than minimum {minimum_day_slots[date]['start'] - sticky_hours} on date {date}')
                    continue
                if not end_slot <= minimum_day_slots[date]['end'] + sticky_hours:
                    logging.info(
                        f'Gap end {end_slot} is higher than maximum {minimum_day_slots[date]['end'] + sticky_hours} on date {date}')
                    continue

                if not gaps.get(date):
                    gaps[date] = []

                gaps[date].append({
                    'start_slot': start_slot,
                    'end_slot': end_slot,
                    'start_time': merged_days[date][previous_slot_number]['end'],
                    'end_time': merged_days[date][slot_number]['start']
                })

            previous_slot_number = slot_number

    return gaps

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