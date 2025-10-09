"""
Utility script to cancel stuck Replicate predictions
Run this to clean up predictions that are stuck in "starting" or "processing" status
"""
import os
import sys
import replicate
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil import parser

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

def list_and_cancel_stuck_predictions():
    """
    Lists all recent predictions and cancels any stuck in 'starting' or 'processing'
    """
    client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    print("=" * 80)
    print("REPLICATE PREDICTION CLEANUP UTILITY")
    print("=" * 80)
    print()

    try:
        # Get recent predictions (last 100)
        predictions = list(client.predictions.list())

        if not predictions:
            print("✅ No predictions found")
            return

        print(f"Found {len(predictions)} recent predictions\n")

        # Filter stuck predictions (older than 10 minutes and still starting/processing)
        stuck_predictions = []
        cutoff_time = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=10)

        for pred in predictions:
            status = pred.status
            created_at = pred.created_at

            # Parse created_at if it's a string
            if isinstance(created_at, str):
                try:
                    created_at = parser.parse(created_at)
                except:
                    created_at = None

            # Check if prediction is stuck
            is_old_enough = created_at < cutoff_time if created_at else True
            is_stuck_status = status in ["starting", "processing"]

            if is_old_enough and is_stuck_status:
                stuck_predictions.append(pred)

        if not stuck_predictions:
            print("✅ No stuck predictions found!")
            print("\nRecent predictions status:")
            for pred in predictions[:10]:  # Show last 10
                print(f"  {pred.id}: {pred.status} (created: {pred.created_at})")
            return

        print(f"⚠️  Found {len(stuck_predictions)} STUCK predictions:\n")

        for pred in stuck_predictions:
            print(f"Prediction ID: {pred.id}")
            print(f"  Status: {pred.status}")
            print(f"  Model: {pred.model}")
            print(f"  Created: {pred.created_at}")
            print()

        print("\nCancelling stuck predictions...\n")

        success_count = 0
        error_count = 0

        for pred in stuck_predictions:
            try:
                pred.cancel()
                print(f"✅ Canceled: {pred.id}")
                success_count += 1
            except Exception as e:
                # 404 errors mean prediction is too old to cancel (will timeout naturally)
                if "404" in str(e):
                    print(f"ℹ️  {pred.id}: Too old to cancel (will timeout naturally)")
                else:
                    print(f"❌ Failed to cancel {pred.id}: {e}")
                error_count += 1

        print()
        print("=" * 80)
        print(f"SUMMARY: {success_count} canceled, {error_count} failed")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error accessing Replicate API: {e}")
        print("\nMake sure REPLICATE_API_TOKEN is set in .env file")

def cancel_specific_prediction(prediction_id):
    """
    Cancel a specific prediction by ID
    """
    client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    try:
        prediction = client.predictions.get(prediction_id)

        print(f"\nPrediction: {prediction_id}")
        print(f"Status: {prediction.status}")
        print(f"Model: {prediction.model}")
        print(f"Created: {prediction.created_at}")
        print()

        if prediction.status in ["succeeded", "failed", "canceled"]:
            print(f"⚠️  Prediction already in terminal state: {prediction.status}")
            return

        try:
            prediction.cancel()
            print(f"✅ Canceled: {prediction_id}")
        except Exception as cancel_error:
            if "404" in str(cancel_error):
                print(f"ℹ️  Too old to cancel (will timeout naturally)")
            else:
                print(f"❌ Error canceling: {cancel_error}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Cancel specific prediction ID provided as argument
        prediction_id = sys.argv[1]
        print(f"Canceling specific prediction: {prediction_id}\n")
        cancel_specific_prediction(prediction_id)
    else:
        # List and cancel all stuck predictions
        list_and_cancel_stuck_predictions()
