import gitlab
import time
import traceback

# Configuration
DEST_GITLAB_URL = 'your_destination_gitlab_url'
DEST_TOKEN = 'your_destination_private_token'
TARGET_GROUP_PATH = 'your_gitlab_group_path'
TARGET_PROJECT_NAME = 'your_gitlab_project_name'  # 🔧 Change this to the specific project

print("🚀 Starting GitLab branch management script")
print(f"Target group: {TARGET_GROUP_PATH}")
print(f"Target project: {TARGET_PROJECT_NAME}")

# Initialize GitLab API
gl = gitlab.Gitlab(DEST_GITLAB_URL, private_token=DEST_TOKEN)
gl.auth()

# Get target group
try:
    group = gl.groups.get(TARGET_GROUP_PATH)
    print(f"✅ Found target group: {group.full_path} (ID: {group.id})")
except gitlab.exceptions.GitlabGetError:
    print(f"❌ Target group '{TARGET_GROUP_PATH}' not found!")
    exit(1)

# Get all projects in the group
projects = group.projects.list(all=True, include_subgroups=True)
print(f"Found {len(projects)} projects in group")

# Find target project
target_project = None
for project in projects:
    if project.name.lower() == TARGET_PROJECT_NAME.lower():
        target_project = project
        break

if not target_project:
    print(f"❌ Project '{TARGET_PROJECT_NAME}' not found in group '{TARGET_GROUP_PATH}'")
    exit(1)

# Process the specific project
full_project = gl.projects.get(target_project.id)
print(f"\n{'='*50}")
print(f"🔧 Processing project: {full_project.name} (ID: {full_project.id})")

try:
    # Get all branches with full details
    branches = full_project.branches.list(all=True)
    branch_names = [b.name for b in branches]
    print(f"Found branches: {', '.join(branch_names)}")

    # Check if 'demo' branch exists
    demo_branch_exists = any(b.name == 'demo' for b in branches)
    if not demo_branch_exists:
        print("❌ 'demo' branch not found, exiting")
        exit(1)

    print("✅ 'demo' branch found")

    # Delete all branches except 'demo'
    branches_to_delete = [b for b in branches if b.name != 'demo']

    if not branches_to_delete:
        print("✅ No branches to delete (only 'demo' exists)")
    else:
        print(f"🗑️ Deleting {len(branches_to_delete)} branches...")
        for branch in branches_to_delete:
            try:
                # Unprotect branch if needed
                if branch.protected:
                    print(f"  🔓 Unprotecting branch: {branch.name}")
                    protections = full_project.protectedbranches.list()
                    for protection in protections:
                        if protection.name == branch.name:
                            protection.delete()
                            print(f"  ⛓️ Removed protection for {branch.name}")
                            time.sleep(0.5)
                            break

                print(f"  ❌ Deleting branch: {branch.name}")
                branch.delete()
                time.sleep(0.5)
            except gitlab.exceptions.GitlabDeleteError as e:
                print(f"  ⚠️ Failed to delete branch {branch.name}: {e}")
            except Exception as e:
                print(f"  ⚠️ Unexpected error deleting branch {branch.name}: {e}")

    # Create 'demo2' branch from 'demo'
    new_branch_name = 'demo2'
    print(f"\n➕ Creating new branch: {new_branch_name} from 'demo'")
    try:
        existing_branches = [b.name for b in full_project.branches.list()]
        if new_branch_name in existing_branches:
            print(f"  ⚠️ Branch '{new_branch_name}' already exists, skipping creation")
        else:
            full_project.branches.create({
                'branch': new_branch_name,
                'ref': 'demo'
            })
            print(f"  ✅ Created branch '{new_branch_name}' from 'demo'")
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"  ❌ Failed to create branch '{new_branch_name}': {e}")

    # Set 'demo' as default branch
    print(f"\n⭐ Setting 'demo' as default branch")
    try:
        if full_project.default_branch == 'demo':
            print("  ✅ 'demo' is already the default branch")
        else:
            full_project.default_branch = 'demo'
            full_project.save()
            print("  ✅ Changed default branch to 'demo'")
    except Exception as e:
        print(f"  ❌ Failed to set 'demo' as default branch: {e}")
        print("  ⚠️ You may need to manually set the default branch in GitLab UI")

except Exception as e:
    print(f"❌ Critical error processing project: {str(e)}")
    traceback.print_exc()

print("\n🎉 Branch management completed for the target project.")