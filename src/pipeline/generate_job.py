from datetime import datetime, timezone

def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    print(f"[generate_job] OK - placeholder run at {now}")
    # Next steps will create a real job JSON in /jobs

if __name__ == "__main__":
    main()
