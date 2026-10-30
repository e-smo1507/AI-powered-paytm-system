import subprocess
result = subprocess.run(
    [
        "python", "-m", "backend.test_journeys"
    ],
    timeout=60
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)
