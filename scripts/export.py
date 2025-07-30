import gitlab
import time

SOURCE_GITLAB_URL = 'your_source_gitlab_url'
SOURCE_TOKEN = 'your_source_private_token'

gl = gitlab.Gitlab(SOURCE_GITLAB_URL, private_token=SOURCE_TOKEN)
gl.auth()

group = gl.groups.get("back-office")
projects = group.projects.list(all=True, include_subgroups=True)

print(f"Found {len(projects)} projects in 'back-office' to export.")

for project in projects:
    print(f"\n📦 Exporting project: {project.name}")

    try:
        full_project = gl.projects.get(project.id)
        export = full_project.exports.create()

        export_status = full_project.exports.get()
        while export_status.export_status != 'finished':
            print(f"⏳ Waiting for export of {project.name} to complete...")
            time.sleep(5)
            export_status = full_project.exports.get()

        with open(f"{project.path}.tar.gz", "wb") as f:
            export.download(streamed=True, chunk_size=1024, action=f.write)
        print(f"✅ {project.name} export complete.")

    except Exception as e:
        print(f"❌ Failed for {project.name}: {e}")

print("\n🎉 All exports completed successfully.")