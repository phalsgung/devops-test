import requests
import configparser
from datetime import datetime, timedelta


"""
TODO:
Delete inactive branches with unmerged changes?
PROTECTED_BRANCHES iwth regexp for sake of matching any future dev branches
is_branch_merged() wrong condition
find_uncommitted_changes() needs more understanding
"""

global_config = configparser.ConfigParser()
global_config.read('Global.config')


def get_headers():
    return {
        "Authorization": f"token {global_config['github']['TOKEN']}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_branches():
    url = f"{global_config['github']['GITHUB_API_URL']}/repos/{global_config['github']['ORG']}/{global_config['github']['REPO_NAME']}/branches"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def get_branch_info(branch_name):
    url = f"{global_config['github']['GITHUB_API_URL']}/repos/{global_config['github']['ORG']}/{global_config['github']['REPO_NAME']}/branches/{branch_name}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def get_commit_info(commit_sha):
    url = f"{global_config['github']['GITHUB_API_URL']}/repos/{global_config['github']['ORG']}/{global_config['github']['REPO_NAME']}/commits/{commit_sha}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def delete_branch(branch_name):
    url = f"{global_config['github']['GITHUB_API_URL']}/repos/{global_config['github']['ORG']}/{global_config['github']['REPO_NAME']}/git/refs/heads/{branch_name}"
    # REVIEW MOCK
    # response = requests.delete(url, headers=get_headers())
    # response.raise_for_status()
    print(f"Deleted branch: {branch_name}")

def is_branch_merged(branch_name):
    url = f"{global_config['github']['GITHUB_API_URL']}/repos/{global_config['github']['ORG']}/{global_config['github']['REPO_NAME']}/compare/{global_config['cleanup']['DEFAULT_BRANCH']}...{branch_name}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    compare_info = response.json()
    return compare_info["status"] == "behind"  # this condition does not mean actually branch is merged

def is_branch_inactive(branch_name, threshold_days):
    branch_info = get_branch_info(branch_name)
    commit_sha = branch_info["commit"]["sha"]
    commit_info = get_commit_info(commit_sha)
    commit_date = commit_info["commit"]["committer"]["date"]
    commit_datetime = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
    # return (datetime.utcnow() - commit_datetime).days > threshold_days
    # REVIEW MOCK
    return True

def branch_matches_pattern(branch_name, pattern):
    return pattern in branch_name

def list_all_branches():
    branches = get_branches()
    print("All branches:")
    for branch in branches:
        print(f"- {branch['name']}")

def list_inactive_branches(threshold_days):
    branches = get_branches()
    print(f"Branches inactive for more than {threshold_days} days:")
    for branch in branches:
        branch_name = branch['name']
        if is_branch_inactive(branch_name, threshold_days):
            print(f"- {branch_name}")

def list_merged_branches():
    branches = get_branches()
    print("Merged branches:")
    for branch in branches:
        branch_name = branch['name']
        if is_branch_merged(branch_name):
            print(f"- {branch_name}")

def find_uncommitted_changes(branch_name):
    url = f"{global_config['github']['GITHUB_API_URL']}/repos/{global_config['github']['ORG']}/{global_config['github']['REPO_NAME']}/branches/{branch_name}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    branch_info = response.json()
    return branch_info['commit']['commit']['tree']['sha'] != branch_info['commit']['sha']

def list_uncommitted_changes():
    branches = get_branches()
    print("Branches with uncommitted changes:")
    for branch in branches:
        branch_name = branch['name']
        if find_uncommitted_changes(branch_name):
            print(f"- {branch_name}")

def cleanup_branches():
    branches = get_branches()
    for branch in branches:
        branch_name = branch["name"]
        if branch_name in global_config['cleanup']['PROTECTED_BRANCHES']:
            print(f"Skipping protected branch: {branch_name}")
            continue
        
        if is_branch_merged(branch_name):
            delete_branch(branch_name)
        elif is_branch_inactive(branch_name, int(global_config["cleanup"]["INACTIVE_DAYS_THRESHOLD"])):
            delete_branch(branch_name)
        elif branch_matches_pattern(branch_name, global_config["cleanup"]["FEAT_BRANCH_PATTERN"]):
            delete_branch(branch_name)

def main():
    list_all_branches()
    list_inactive_branches(int(global_config["cleanup"]["INACTIVE_DAYS_THRESHOLD"]))
    list_merged_branches()
    list_uncommitted_changes()
    cleanup_branches()

if __name__ == "__main__":
    main()
