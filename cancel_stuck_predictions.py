"""
Utility script to cancel stuck Replicate predictions
Run this to clean up predictions that are stuck in "starting" or "processing" status
"""
import os
import replicate
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
        cutoff_time = datetime.now() - timedelta(minutes=10)

        for pred in predictions:
            status = pred.status
            created_at = pred.created_at

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

        # Ask for confirmation
        response = input(f"Cancel all {len(stuck_predictions)} stuck predictions? (yes/no): ").strip().lower()

        if response not in ['yes', 'y']:
            print("\n❌ Cancelled by user")
            return

        print("\nCancelling stuck predictions...\n")

        success_count = 0
        error_count = 0

        for pred in stuck_predictions:
            try:
                pred.cancel()
                print(f"✅ Canceled: {pred.id}")
                success_count += 1
            except Exception as e:
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

        response = input("Cancel this prediction? (yes/no): ").strip().lower()

        if response in ['yes', 'y']:
            prediction.cancel()
            print(f"✅ Canceled: {prediction_id}")
        else:
            print("❌ Cancelled by user")

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
