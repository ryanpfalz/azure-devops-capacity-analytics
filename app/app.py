import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta
import os

# assumes the below days are considered working days
WORKING_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


# Description: Calculates the number of working days in a given sprint.
# Parameters:
# - sprint_name (str): The name of the sprint.
# - data (dict): The sprint data.
# Returns:
# - int: The number of working days in the sprint if the sprint is found and has valid start and finish dates.
# - str: A message indicating missing dates or that the sprint was not found.
def get_days_in_sprint(sprint_name, data):
    for sprint in data['value']:
        if sprint['name'].lower() == sprint_name.lower():
            if sprint['attributes']['startDate'] and sprint['attributes']['finishDate']:
                start_date = datetime.strptime(sprint['attributes']['startDate'], '%Y-%m-%dT%H:%M:%SZ')
                finish_date = datetime.strptime(sprint['attributes']['finishDate'], '%Y-%m-%dT%H:%M:%SZ')
                days_in_sprint = 0
                current_date = start_date
                while current_date <= finish_date:
                    # Check if the current day is a working day
                    if current_date.strftime('%A') in WORKING_DAYS:
                        days_in_sprint += 1
                    # Move to the next day
                    current_date += timedelta(days=1)
                return days_in_sprint
            else:
                return "Start date or finish date is missing for the sprint."
    return "Sprint not found."


# Description: Calculates the total and remaining sprint hours for each team member.
# Parameters:
# - sprint_data (dict): The sprint data.
# - team_members_data (dict): The team members data.
# - sprint_name (str): The name of the sprint.
# - remaining_availability (bool): Flag to calculate remaining availability. Default is False.
# Returns:
# - list: A list of dictionaries with each team member's name, total sprint hours, and remaining sprint hours.
# - None: If the sprint is not found.
# TODO review functionality that accounts for days off
def get_team_member_availability(sprint_data, team_members_data, sprint_name, remaining_availability=False):
    for sprint in sprint_data['value']:
        if sprint['name'] == sprint_name:
            start_date = datetime.strptime(sprint['attributes']['startDate'], "%Y-%m-%dT%H:%M:%SZ")
            finish_date = datetime.strptime(sprint['attributes']['finishDate'], "%Y-%m-%dT%H:%M:%SZ")
            break
    else:
        return None  # Return None if the sprint is not found

    days_in_sprint = 0
    current_date = start_date
    while current_date <= finish_date:
        # Check if the current day is a working day
        if current_date.strftime('%A') in WORKING_DAYS:
            days_in_sprint += 1
        # Move to the next day
        current_date += timedelta(days=1)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate remaining working days in the sprint
    remaining_days_in_sprint = 0
    current_date = max(start_date, today)
    while current_date <= finish_date:
        if current_date.strftime('%A') in WORKING_DAYS:
            remaining_days_in_sprint += 1
        current_date += timedelta(days=1)

    user_info = []
    for team_member in team_members_data['value']:
        member_name = team_member['teamMember']['uniqueName']
        capacity_per_day = team_member['activities'][0]['capacityPerDay']

        total_sprint_hours = capacity_per_day * days_in_sprint

        days_off = [
            (datetime.strptime(d['start'], "%Y-%m-%dT%H:%M:%SZ"), datetime.strptime(d['end'], "%Y-%m-%dT%H:%M:%SZ"))
            for d in team_member['daysOff']
        ]

        available_days = remaining_days_in_sprint
        for start, end in days_off:
            while start <= end:
                if start.strftime('%A') in WORKING_DAYS and start >= today:
                    available_days -= 1
                start += timedelta(days=1)

        remaining_sprint_hours = capacity_per_day * max(0, available_days)

        user_info.append({
            'name': member_name,
            'total_sprint_hours': total_sprint_hours,
            'remaining_sprint_hours': remaining_sprint_hours
        })

    return user_info


# Description: Updates the 'currently_assigned' hours for each team member in the availability_dict based on the work_items_list.
# Parameters:
# - availability_dict (list): A list of dictionaries representing team members and their available hours.
# - work_items_list (dict): A dictionary containing work items with assigned hours and assignees.
# Returns:
# - list: The updated availability_dict with 'currently_assigned' hours for each team member.
def get_hours_assigned(availability_dict, work_items_list):
    # Initialize 'currently_assigned' to 0 for each item in availability_dict
    for item in availability_dict:
        item['currently_assigned'] = 0

    # Iterate through each item in the 'value' array of work_items_list if 'value' is in work_items_list
    if 'value' in work_items_list:
        for item in work_items_list['value']:
            # Check if 'Microsoft.VSTS.Scheduling.RemainingWork' is present
            if 'Microsoft.VSTS.Scheduling.RemainingWork' in item['fields'] and 'System.AssignedTo' in item['fields']:
                assigned_hours = item['fields']['Microsoft.VSTS.Scheduling.RemainingWork']
                assigned_to = item['fields']['System.AssignedTo']['uniqueName']

                # Find the corresponding item in availability_dict and add the assigned hours
                for availability_item in availability_dict:
                    if availability_item['name'] == assigned_to:
                        availability_item['currently_assigned'] += assigned_hours

    return availability_dict


# Description: Generates a snapshot of the current state of a sprint including team member availability and work items.
# Parameters:
# - organization (str): The name of the organization.
# - project (str): The name of the project.
# - team (str): The name of the team.
# - target_sprint_name (str): The name of the target sprint.
# - pat (str): Personal Access Token for API authentication.
# Returns:
# - DataFrame: A pandas DataFrame containing the snapshot data.
def generate_snapshot(organization, project, team, target_sprint_name, pat):

    # construct snapshot by sprint/team/project/org
    snapshot = {
        'sprint': target_sprint_name,
        'team': team,
        'project': project,
        'organization': organization,
        'snapshot_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # https://learn.microsoft.com/en-us/rest/api/azure/devops/work/iterations/list?view=azure-devops-rest-7.1&tabs=HTTP
    # 1. Get Iteration ID
    iteration_url = f'https://dev.azure.com/{organization}/{project}/{team}/_apis/work/teamsettings/iterations?api-version=7.1-preview.1'
    iter_response = requests.get(iteration_url, auth=HTTPBasicAuth('', pat))
    iter_response_dict = iter_response.json()
    iteration_id = next(
        (sprint['id'] for sprint in iter_response_dict['value'] if sprint['name'] == target_sprint_name), None)

    num_days_in_sprint = get_days_in_sprint(target_sprint_name, iter_response_dict)

    # add num_days_in_sprint to snapshot
    snapshot['num_days_in_sprint'] = num_days_in_sprint

    # 2. Get Capacity by Iteration ID
    # https://learn.microsoft.com/en-us/rest/api/azure/devops/work/capacities/list?view=azure-devops-rest-6.0&viewFallbackFrom=azure-devops-rest-7.1&tabs=HTTP
    capacity_url = f'https://dev.azure.com/{organization}/{project}/{team}/_apis/work/teamsettings/iterations/{iteration_id}/capacities?api-version=6.0'
    cap_response = requests.get(capacity_url, auth=HTTPBasicAuth('', pat))
    cap_response_dict = cap_response.json()

    team_member_availability = get_team_member_availability(sprint_data=iter_response_dict,
                                                            team_members_data=cap_response_dict,
                                                            sprint_name=target_sprint_name)

    # 3. Get iteration work items
    # https://learn.microsoft.com/en-us/rest/api/azure/devops/work/iterations/get-iteration-work-items?view=azure-devops-rest-7.2&tabs=HTTP
    workitems_url = f'https://dev.azure.com/{organization}/{project}/{team}/_apis/work/teamsettings/iterations/{iteration_id}/workitems?api-version=7.2-preview.1'
    workitems_response = requests.get(workitems_url, auth=HTTPBasicAuth('', pat))
    workitems_response_dict = workitems_response.json()

    # TODO you will need to refactor this to fit what you're looking to extract
    # This example parses out IDs from targets with a source (tasks), not from the assumed Product Backlog Item (targets without a source)
    target_ids_with_non_null_source = [
        relation['target']['id']
        for relation in workitems_response_dict['workItemRelations']
        if relation.get('source') is not None
    ]

    # 4. Use iteration ids to get work item fields (ID, owner, remaining work, status)
    # https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/get-work-items-batch?view=azure-devops-rest-7.0&tabs=HTTP
    wi_batch_url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/workitemsbatch?api-version=7.0'
    wi_batch_response = requests.post(wi_batch_url, auth=HTTPBasicAuth('', pat), json={
        'ids': target_ids_with_non_null_source,
        'fields': ['System.Id', 'System.AssignedTo', "Microsoft.VSTS.Scheduling.RemainingWork", "System.State"]
    })
    wi_batch_response_dict = wi_batch_response.json()

    hours_assigned_by_member = get_hours_assigned(availability_dict=team_member_availability,
                                                  work_items_list=wi_batch_response_dict)

    # 5. Construct dataframe of data snapshot
    # add hours_assigned_by_member to snapshot
    snapshot['members'] = hours_assigned_by_member

    # Extracting member data
    snapshot_df = pd.DataFrame(snapshot['members'])

    # Adding other data as new columns
    for key in snapshot:
        if key != 'members':
            snapshot_df[key] = snapshot[key]

    return snapshot_df


def main():
    # TODO handle multiple PATs
    # read PAT from environment variable
    pat = os.environ['AZDO_PAT']

    snapshot_dataframes = [
        generate_snapshot(organization='<your-organization>', project='<your-project>', team='<your-team>',
                          target_sprint_name='<your-sprint>', pat=pat)
    ]

    combined_df = pd.concat(snapshot_dataframes)

    # TODO export to a database
    # save snapshot to csv
    combined_df.to_csv(f'snapshot.csv', index=False)


if __name__ == '__main__':
    main()
