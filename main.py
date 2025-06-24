print("🚨 This print is running — main.py is starting.")  # Top of file
from pagedata import run_metadata_jobs

if __name__ == "__main__":
    print("🚀 Cron job started.")
    try:
        run_metadata_jobs()
    except Exception as e:
        print(f"❌ Error during metadata job: {e}")
    print("✅ Cron job finished.")
