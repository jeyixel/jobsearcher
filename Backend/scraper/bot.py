import asyncio
import firebase_admin
from firebase_admin import credentials, firestore, messaging
from scraper import scrape_jobhub, scrape_itpro, scrape_Devjobs # Importing your functions

# 1. INITIALIZE FIREBASE
# You must have 'serviceAccountKey.json' in this folder.
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

async def get_existing_job_ids():
    """
    Fetches all document IDs from the 'internships' collection.
    Returns a set of IDs for fast comparison.
    """
    print("Fetching existing jobs from Firestore...")
    docs = db.collection("internships").stream()
    # We use a set() because looking up items in a set is instant (O(1))
    return {doc.id for doc in docs}

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
    existing_ids = await asyncio.to_thread(get_existing_job_ids)
    print(f"Existing jobs in DB: {len(existing_ids)}")

    # 2. GET NEW STATE (Scrape)
    print("Running scrapers...")
    results = await asyncio.gather(
        scrape_jobhub(),
        scrape_itpro(),
        scrape_Devjobs()
    )
    # Combine lists
    scraped_jobs = results[0] + results[1] + results[2]
    print(f"Total jobs scraped: {len(scraped_jobs)}")

    # 3. COMPARE (Diffing)
    new_jobs_found = []
    
    # Batch write for performance
    batch = db.batch()
    batch_counter = 0
    
    for job in scraped_jobs:
        job_id = job['id']
        
        # If this ID is NOT in our existing set, it's NEW.
        if job_id not in existing_ids:
            new_jobs_found.append(job)
            
            # Add to Firestore Batch
            doc_ref = db.collection("internships").document(job_id)
            batch.set(doc_ref, job)
            batch_counter += 1

    # 4. SAVE & NOTIFY
    if new_jobs_found:
        print(f"🚀 Found {len(new_jobs_found)} NEW jobs!")
        
        # Commit the batch to Firestore
        batch.commit()
        print("✅ New jobs saved to Firestore.")

        # Trigger FCM Notification
        # We send one notification summarizing the update
        send_push_notification(len(new_jobs_found), new_jobs_found[0])
        
    else:
        print("💤 No new jobs found. Database is up to date.")

if __name__ == "__main__":
    asyncio.run(run_bot())