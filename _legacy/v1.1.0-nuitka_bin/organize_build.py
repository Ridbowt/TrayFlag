# organize_build.py
import os
import shutil

core_build_dir = os.path.join('build', 'core', 'TrayFlag_core.dist')
launcher_exe = os.path.join('build', 'launcher', 'TrayFlag.exe')
final_dist_dir = 'dist'
bin_dir = os.path.join(final_dist_dir, 'bin')

print("Organizing files...")
os.makedirs(bin_dir, exist_ok=True)

shutil.move(launcher_exe, final_dist_dir)
print(f"  -> Launcher moved to '{final_dist_dir}'")

for item in os.listdir(core_build_dir):
    shutil.move(os.path.join(core_build_dir, item), bin_dir)
print(f"  -> Core app and DLLs moved to '{bin_dir}'")

assets_src = os.path.join(bin_dir, 'assets')
assets_dst = os.path.join(final_dist_dir, 'assets')
if os.path.exists(assets_src):
    shutil.move(assets_src, assets_dst)
    print(f"  -> Assets folder moved to '{final_dist_dir}'")

shutil.rmtree('build')
print("\nOrganization complete.")