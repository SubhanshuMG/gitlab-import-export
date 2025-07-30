import gitlab

DEST_GITLAB_URL = 'your_destination_gitlab_url'
DEST_PRIVATE_TOKEN = 'your_private_token'

WRONG_NAMESPACE_PATHS = ['root', 'Administrator']  # adjust if needed

def main():
    gl = gitlab.Gitlab(DEST_GITLAB_URL, private_token=DEST_PRIVATE_TOKEN)
    gl.auth()

    for ns_path in WRONG_NAMESPACE_PATHS:
        print(f"Checking projects under namespace: {ns_path}")
        # List projects under this namespace
        projects = gl.projects.list(search=ns_path, all=True)
        for proj in projects:
            # Confirm project is under the wrong namespace exactly
            if proj.namespace['path'] == ns_path:
                print(f"Deleting project: {proj.name_with_namespace}")
                try:
                    project_obj = gl.projects.get(proj.id)
                    project_obj.delete()
                    print(f"Deleted {proj.name_with_namespace}")
                except Exception as e:
                    print(f"Failed to delete {proj.name_with_namespace}: {e}")

if __name__ == '__main__':
    main()