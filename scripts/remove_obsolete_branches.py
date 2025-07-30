import gitlab
import time

# Configuration
DEST_GITLAB_URL = 'your_destination_gitlab_url'
DEST_TOKEN = 'your_destination_private_token'
TARGET_GROUP_PATH = 'your_gitlab_group_path'  # Use group path instead of ID (optional)

print("🚀 Starting GitLab branch management script")
print(f"Target group: {TARGET_GROUP_PATH}")

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

for project in projects:
    # Convert to full project object
    full_project = gl.projects.get(project.id)
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
            print("❌ 'demo' branch not found, skipping project")
            continue
            
        print("✅ 'demo' branch found")
        
        # 1. Delete all branches except 'demo'
        branches_to_delete = [b for b in branches if b.name != 'demo']
        
        if not branches_to_delete:
            print("✅ No branches to delete (only 'demo' exists)")
        else:
            print(f"🗑️ Deleting {len(branches_to_delete)} branches...")
            for branch in branches_to_delete:
                try:
                    # Check if branch is protected
                    if branch.protected:
                        print(f"  🔓 Unprotecting branch: {branch.name}")
                        # Get protection rules
                        protections = full_project.protectedbranches.list()
                        for protection in protections:
                            if protection.name == branch.name:
                                protection.delete()
                                print(f"  ⛓️ Removed protection for {branch.name}")
                                time.sleep(0.5)
                                break
                    
                    # Delete branch
                    print(f"  ❌ Deleting branch: {branch.name}")
                    branch.delete()
                    time.sleep(0.5)  # Short delay to avoid rate limiting
                except gitlab.exceptions.GitlabDeleteError as e:
                    if "protected branch" in str(e).lower():
                        print(f"  ⚠️ Could not delete protected branch {branch.name}: {e}")
                    else:
                        print(f"  ⚠️ Failed to delete branch {branch.name}: {e}")
                except Exception as e:
                    print(f"  ⚠️ Unexpected error deleting branch {branch.name}: {e}")
        
        # 2. Create 'demo2' branch from 'demo'
        new_branch_name = 'demo2'
        print(f"\n➕ Creating new branch: {new_branch_name} from 'demo'")
        try:
            # Check if branch already exists
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
        
        # 3. Set 'demo' as default branch
        print(f"\n⭐ Setting 'demo' as default branch")
        try:
            if full_project.default_branch == 'demo':
                print("  ✅ 'demo' is already the default branch")
            else:
                # First set the default branch to something else if needed
                # (GitLab requires setting to an existing branch)
                full_project.default_branch = 'demo2' if 'demo2' in existing_branches else 'demo'
                full_project.save()
                
                # Now set to demo
                full_project.default_branch = 'demo'
                full_project.save()
                print("  ✅ Changed default branch to 'demo'")
        except Exception as e:
            print(f"  ❌ Failed to set 'demo' as default branch: {e}")
            print("  ⚠️ You may need to manually set the default branch in GitLab UI")
    
    except Exception as e:
        print(f"❌ Critical error processing project: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n🎉 Branch management completed for all projects.")