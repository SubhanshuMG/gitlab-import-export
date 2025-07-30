import gitlab
import os
import time

DEST_GITLAB_URL = 'your_destination_gitlab_url'
DEST_TOKEN = 'your_destination_private_token'
TARGET_GROUP_PATH = 'your_gitlab_group_path'  # Use group path instead of ID (optional)
EXPORTS_DIR = 'directory_path_where_export_files_are_stored'  # Path to your export files

gl_dest = gitlab.Gitlab(DEST_GITLAB_URL, private_token=DEST_TOKEN)
gl_dest.auth()

# Get the target group explicitly
try:
    dest_group = gl_dest.groups.get(TARGET_GROUP_PATH)
    print(f"✅ Found target group: {dest_group.full_path} (ID: {dest_group.id})")
except gitlab.exceptions.GitlabGetError:
    print(f"❌ Target group '{TARGET_GROUP_PATH}' not found!")
    exit(1)

export_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith('.tar.gz')]
print(f"Found {len(export_files)} export files to import into '{dest_group.full_path}'")

for export_file in export_files:
    project_name = export_file.replace('.tar.gz', '')
    print(f"\n🚀 Importing project: {project_name}")

    try:
        # Check if project exists in target group
        existing_projects = gl_dest.projects.list(search=project_name, group=dest_group.id)
        if existing_projects:
            print(f"⚠️ Project '{project_name}' already exists in {dest_group.full_path}, skipping.")
            continue

        # Import project with explicit namespace parameters
        with open(os.path.join(EXPORTS_DIR, export_file), 'rb') as f:
            import_params = {
                'path': project_name,
                'namespace': dest_group.full_path,  # Use full path
                'namespace_id': dest_group.id,      # And ID for redundancy
                'overwrite': True,
            }
            
            # Debug print
            print(f"Importing with params: {import_params}")
            
            project_import = gl_dest.projects.import_project(f, **import_params)
            project_id = project_import['id']

        # Poll for completion
        start_time = time.time()
        while True:
            project = gl_dest.projects.get(project_id)
            ns_path = project.namespace['full_path'] if project.namespace else 'Unknown'
            
            print(f"Status: {project.import_status} | "
                  f"Namespace: {ns_path} | "
                  f"Elapsed: {int(time.time() - start_time)}s")
            
            if project.import_status == 'finished':
                if ns_path == dest_group.full_path:
                    print(f"✅ Project imported successfully to {dest_group.full_path}!")
                else:
                    print(f"⚠️ Project imported to WRONG namespace: {ns_path}")
                break
            elif project.import_status == 'failed':
                print(f"❌ Import failed! Error: {project.import_error if hasattr(project, 'import_error') else 'Unknown'}")
                break
                
            time.sleep(5)

    except Exception as e:
        print(f"❌ Critical error importing '{project_name}': {str(e)}")
        # Print full exception traceback for debugging
        import traceback
        traceback.print_exc()

print("\n🎉 All imports attempted.")