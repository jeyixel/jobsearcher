# -------------------------------------------------------------------
# STEP 1: The Base Image
# We use the official Microsoft Playwright image.
# It includes Python AND the browsers (Chromium, Firefox, Webkit).
# This saves us hours of installing system dependencies manually.
# -------------------------------------------------------------------
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# -------------------------------------------------------------------
# STEP 2: Setup the Working Directory
# This creates a folder named 'app' inside the container 
# and makes it the "home base" for all future commands.
# -------------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------------- 
# STEP 3: Copy Files 
# We copy specifically from the Backend/scraper folder to the container root.
# This ensures bot.py and scraper.py are in /app/
# ------------------------------------------------------------------- 
COPY Backend/scraper/ .

# -------------------------------------------------------------------
# STEP 4: Install Dependencies
# Install the python libraries from your requirements.txt
# -------------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------------
# STEP 5: Install Browsers (Safety Net)
# Even though the base image has browsers, we run this to ensure
# the specific version Playwright expects is linked correctly.
# -------------------------------------------------------------------
RUN playwright install chromium

# -------------------------------------------------------------------
# STEP 6: The Command
# This is what runs every 30 mins when Choreo wakes up the container.
# -------------------------------------------------------------------
CMD ["python", "bot.py"]