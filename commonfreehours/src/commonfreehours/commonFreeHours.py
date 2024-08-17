from datetime import datetime

from commonfreehours.zapi import Zermelo


def process_appointments(appointments):
    # Preprocesses the appointments for getting the gaps
    days = {}
    gaps = {}

    previous_slot = None
    previous_time = None

    appointments.sort(key=lambda arr: arr.get('start'))

    for a in appointments:
        # Check if list is empty
        if not a.get('groups'):
            continue

        s = a["startTimeSlot"]
        e = a["endTimeSlot"]

        st = datetime.fromtimestamp(a.get('start'))
        et = datetime.fromtimestamp(a.get('end'))

        d = str(datetime.fromtimestamp(a.get('start')).date())

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

def get_common_gaps(*gaps):
    # Returns common gaps between gap lists in a days dict

    # Return the first element of gaps when only one or less is supplied
    # Throws an indexerror if no args are supplied
    if len(gaps) <= 1:
        return gaps[0]

    common_gaps = {}

    # Convert tuple to list for popping
    gaps = list(gaps)

    gaps_a = gaps.pop()
    gaps_b = gaps.pop()

    # Iter through all days
    for date in set(gaps_a.keys()).union(set(gaps_b.keys())):
        if not gaps_a.get(date):
            continue
        for gap_a in gaps_a.get(date):
            if not gaps_b.get(date):
                continue
            for gap_b in gaps_b.get(date):
                overlap_start_slot = max(gap_a[0][0], gap_b[0][0])
                overlap_end_slot = min(gap_a[0][1], gap_b[0][1])

                if overlap_start_slot <= overlap_end_slot:

                    # Create day if it does not exist
                    if common_gaps.get(date) is None:
                        common_gaps[date] = []

                    # Add gap to list
                    common_gaps[date].append([[overlap_start_slot, overlap_end_slot], [max(gap_a[1][0], gap_b[1][0]), min(gap_a[1][1], gap_b[1][1])]])

    if len(gaps) >= 1:
        return get_common_gaps(common_gaps, *gaps)

    return common_gaps

def get_accounts(zermelo: Zermelo, schoolInSchoolYear: int):
    students = zermelo.get_students(schoolInSchoolYear, "firstName,prefix,lastName,student")
    teachers = zermelo.get_teachers(schoolInSchoolYear, "employee,prefix,lastName")

    accounts = []

    for teacher in teachers:
        name = f"{teacher['prefix']} {teacher['lastName']}" if teacher['prefix'] else f"{teacher['lastName']}"
        accounts.append({"name": f"{name} ({teacher['employee']})", "id": teacher['employee'], 'teacher': True})

    # Process the student list
    for student in students:
        name = f"{student['firstName']} {student['prefix']} {student['lastName']}" if student['prefix'] else f"{student['firstName']} {student['lastName']}"
        accounts.append({"name": f"{name} ({student['student']})", "id": student['student'], 'teacher': False})

    return accounts