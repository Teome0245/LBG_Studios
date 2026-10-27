import subprocess
import sys
import os

cd_dir = "/home/lbg/projects/LBG_Studios/packages/compagnon-desktop"
cmd = [
    "npx", "--yes", "esbuild",
    "overlay/vrm/vrm_pet.js",
    "--bundle",
    "--outfile=overlay/vrm/vrm_pet.bundle.js",
    "--format=iife",
    "--global-name=VrmPetMod"
]

res = subprocess.run(cmd, cwd=cd_dir, capture_output=True, text=True)
print("RETURNCODE", res.returncode)
print("STDOUT", res.stdout)
print("STDERR", res.stderr)
