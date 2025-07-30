import gitlab
import os
import time

# Configuration
DEST_GITLAB_URL = 'your_destination_gitlab_url'
DEST_TOKEN = 'your_destination_private_token'
TARGET_GROUP_PATH = 'your_gitlab_group_path'  # Use group path instead of ID (optional)
EXPORTS_DIR = 'directory_path_where_export_files_are_stored'  # Path to your export files

# List of specific projects to import (without .tar.gz extension)
SELECTED_PROJECTS = [
    "project-1"
    # Add more project names as needed
]

print("🚀 Starting GitLab import script for selected projects")
print(f"Target group: {TARGET_GROUP_PATH}")
print(f"Selected projects: {', '.join(SELECTED_PROJECTS) or 'None'}")

# Initialize GitLab API
gl_dest = gitlab.Gitlab(DEST_GITLAB_URL, private_token=DEST_TOKEN)
gl_dest.auth()

# Get target group
try:
    dest_group = gl_dest.groups.get(TARGET_GROUP_PATH)
    print(f"✅ Found target group: {dest_group.full_path} (ID: {dest_group.id})")
except gitlab.exceptions.GitlabGetError:
    print(f"❌ Target group '{TARGET_GROUP_PATH}' not found!")
    exit(1)

# Process selected projects
for project_name in SELECTED_PROJECTS:
    export_file = f"{project_name}.tar.gz"
    file_path = os.path.join(EXPORTS_DIR, export_file)
    
    print(f"\n{'='*50}")
    print(f"🚀 Processing project: {project_name}")
    
    # Check if export file exists
    if not os.path.exists(file_path):
        print(f"❌ Export file not found: {export_file}")
        continue

    try:
        # NEW: Check for exact name match in target group
        project_exists = False
        for project in gl_dest.projects.list(group=dest_group.id, all=True):
            if project.name == project_name:
                project_exists = True
                break
        
        if project_exists:
            print(f"⚠️ Project '{project_name}' already exists in {dest_group.full_path}, skipping.")
            continue

        # Import project
        print(f"📦 Importing from: {export_file}")
        with open(file_path, 'rb') as f:
            project_import = gl_dest.projects.import_project(
                f, 
                path=project_name,
                namespace_id=dest_group.id
            )
            project_id = project_import['id']
            print(f"🆔 Import started with ID: {project_id}")

        # Monitor import progress
        start_time = time.time()
        while True:
            project = gl_dest.projects.get(project_id)
            status = project.import_status
            ns_path = project.namespace['full_path'] if project.namespace else 'Unknown'
            
            # Print status every 5 seconds
            if status not in ['finished', 'failed']:
                elapsed = int(time.time() - start_time)
                print(f"⏳ Status: {status} | Namespace: {ns_path} | Time: {elapsed}s", end='\r')
                time.sleep(5)
                continue
                
            # Final status handling
            print(f"\n{'='*30}")
            if status == 'finished':
                if ns_path == dest_group.full_path:
                    print(f"✅ Successfully imported to {dest_group.full_path}!")
                else:
                    print(f"⚠️ Imported to WRONG namespace: {ns_path}")
            else:
                error = getattr(project, 'import_error', 'No error message')
                print(f"❌ Import failed! Error: {error}")
            break

    except Exception as e:
        print(f"\n❌ Critical error importing '{project_name}': {str(e)}")
        import traceback
        traceback.print_exc()

print("\n🎉 Import process completed for selected projects.")