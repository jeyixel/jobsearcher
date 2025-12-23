# -------------------------------------------------------------------
# STEP 1: Base Image
# -------------------------------------------------------------------
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# -------------------------------------------------------------------
# STEP 2: Copy & Install Python Deps (As Root)
# -------------------------------------------------------------------
COPY Backend/requirements.txt ./requirements.txt
COPY Backend/scraper/ .

RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------------
# STEP 3: SECURITY FIX (The "Choreo" User)
# We create a user with UID 10014 to satisfy the security scanner.
# -------------------------------------------------------------------
RUN useradd -u 10014 -m choreouser

# Give this user permission to own the /app folder
RUN chown -R 10014:10014 /app

# -------------------------------------------------------------------
# STEP 4: Switch User & Install Browsers
# We switch to the user NOW, so browsers install in the user's home folder.
# -------------------------------------------------------------------
USER 10014

RUN playwright install chromium

# -------------------------------------------------------------------
# STEP 5: Run
# -------------------------------------------------------------------
CMD ["python", "bot.py"]