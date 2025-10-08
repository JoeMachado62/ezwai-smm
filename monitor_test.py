"""Monitor test progress"""
import time
import os
import sys

log_file = "test_output.log"
last_size = 0
no_change_count = 0

print("Monitoring test progress...")
print("=" * 80)

while True:
    time.sleep(10)

    if os.path.exists(log_file):
        current_size = os.path.getsize(log_file)

        if current_size > last_size:
            # New content added
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Show last 5 lines
                for line in lines[-5:]:
                    print(line.strip())
                print("-" * 40)

            last_size = current_size
            no_change_count = 0
        else:
            no_change_count += 1
            print(f"Waiting... ({no_change_count * 10}s)")

            # Check if test completed
            if no_change_count > 30:  # 5 minutes no change
                print("\nTest appears to be stuck or completed.")
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "TEST PASSED" in content:
                        print("\n🎉 SUCCESS! Test completed successfully!")
                        sys.exit(0)
                    elif "ERROR" in content or "EXCEPTION" in content:
                        print("\n❌ Test failed with errors. Check test_output.log for details.")
                        sys.exit(1)
                break
    else:
        print(f"Waiting for {log_file} to be created...")
