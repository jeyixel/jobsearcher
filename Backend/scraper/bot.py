import asyncio
import logging
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore, messaging
from scraper import scrape_jobhub, scrape_itpro, scrape_Devjobs # Importing your functions
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env in this (or parent) folder
load_dotenv(find_dotenv())

# 1. INITIALIZE FIREBASE
if not firebase_admin._apps:
    # Directory where this script lives
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Prefer environment variable (for cloud), otherwise default to local secrets file
    env_key_path = os.getenv("FIREBASE_KEY_PATH")
    if env_key_path:
        # If env gives a relative path, resolve it relative to this file
        key_path = env_key_path
        if not os.path.isabs(key_path):
            key_path = os.path.join(base_dir, key_path)
    else:
        # Local default: ./secrets/serviceAccountKey.json next to this script
        print("⚠️ Warning: FIREBASE_KEY_PATH not set, stopping execution")
        # you can uncomment below to use local file by default, but be cautious about committing secrets
        # key_path = os.path.join()
        sys.exit(1)

    if not os.path.exists(key_path):
        print(f"❌ Error: Service Account Key not found at: {key_path}")
        # Print current directory to help debug in logs
        print(f"Current working directory: {os.getcwd()}") 
        sys.exit(1)
        
    try:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        print(f"✅ Firebase initialized using key at: {key_path}")
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        sys.exit(1)

db = firestore.client()

def get_existing_job_ids():
    """
    Fetches all document IDs from the 'internships' collection.
    Returns a set of IDs for fast comparison.
    """
    print("Fetching existing jobs from Firestore...")
    
    try:
        docs = db.collection("internships").stream()
        # We use a set() because looking up items in a set is instant (O(1))
        return {doc.id for doc in docs}
    except Exception as e:
        print(f"❌ Error fetching existing jobs: {e}")
        return set() # Return empty set on error

def send_push_notification(new_jobs_count, sample_job):
    """
    Sends a push notification to all devices subscribed to the 'internships' topic.
    """
    topic = "internships"
    
    # Custom message logic
    if new_jobs_count == 1:
        title = "New Internship Alert! 🚀"
        body = f"{sample_job['company']} is looking for a {sample_job['job_title']}"
    else:
        title = f"{new_jobs_count} New Internships Found!"
        body = f"Check out roles at {sample_job['company']} and others."

    # Create the message payload
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "screen": "Home", # Example: Tell app to open Home screen
        },
        topic=topic,
    )

    # Send
    try:
        response = messaging.send(message)
        print(f"✅ Notification sent: {response}")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

async def run_bot():
    print("\n=== STARTING BOT ORCHESTRATOR ===")
    
    # 1. GET OLD STATE
    try:
        existing_ids = get_existing_job_ids()
        print(f"Existing jobs in DB: {len(existing_ids)}")
    except Exception as e:
        print(f"❌ Failed to get existing job IDs: {e}")
        existing_ids = set()  # Fallback to empty set
        print("Proceeding with empty existing IDs set.")

    # 2. GET NEW STATE (Scrape)
    print("Running scrapers...")
    results = await asyncio.gather(
        scrape_jobhub(),
        scrape_itpro(),
        scrape_Devjobs()
    )
    # Combine lists
    scraped_jobs = results[0] + results[1] + results[2]
    print(f"Total new jobs scraped: {len(scraped_jobs)}")

    # 3. COMPARE (Diffing)
    new_jobs_found = []
    
    # Batch write for performance (commit in chunks to avoid limits)
    batch = db.batch()
    batch_counter = 0
    
    for job in scraped_jobs:
        job_id = job.get('id')
        if not job_id:
            continue
        
        # If this ID is NOT in our existing set, it's NEW.
        if job_id not in existing_ids:
            new_jobs_found.append(job)
            
            # Add to Firestore Batch
            doc_ref = db.collection("internships").document(job_id)
            batch.set(doc_ref, job)
            batch_counter += 1
            
            # Commit periodically to respect Firestore limits (500 ops)
            if batch_counter >= 400:
                try:
                    batch.commit()
                    print(f"🔁 Committed a chunk of {batch_counter} writes to Firestore.")
                except Exception as e:
                    print(f"❌ Error committing batch chunk: {e}")
                batch = db.batch()
                batch_counter = 0

    # 4. SAVE & NOTIFY
    if new_jobs_found:
        print(f"🚀 Found {len(new_jobs_found)} NEW jobs!")
        
        # Commit any remaining writes
        if batch_counter > 0:
            try:
                batch.commit()
                print(f"✅ Committed final chunk of {batch_counter} writes to Firestore.")
            except Exception as e:
                print(f"❌ Error committing final batch: {e}")

        # Trigger FCM Notification
        # We send one notification summarizing the update
        send_push_notification(len(new_jobs_found), new_jobs_found[0])
        
    else:
        print("💤 No new jobs found. Database is up to date.")

if __name__ == "__main__":
    asyncio.run(run_bot())