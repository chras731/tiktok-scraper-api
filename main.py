import time
from pagedata import run_metadata_jobs

while True:
    run_metadata_jobs()
    time.sleep(10)
