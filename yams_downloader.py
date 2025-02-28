import requests
import time
import zipfile
import os
import re

def log_message(message, start_time, end="\n"):
    elapsed_time = time.time() - start_time
    print(f"[{elapsed_time:.2f}s] {message}", end=end, flush=True)

def clear_console():
    os.system('cls' if os.name=='nt' else 'clear')
    
def download_song(url):
    start_time = time.time()
    client = requests.Session()
    log_message("Telling yams.tf to start preparing the song...", start_time)
    first_request = client.post(
        "https://yams.tf/api", json={
            "url": url,
            "quality": 4,
            "host": "buzzheavier",
            "account": "none"
        },
        headers={
            "User-Agent": "yams.tf-downloader/v1",
        }
    ).json()
    log_message("Got yams id!", start_time)
    return first_request

def check_status(client, request_id):
    start_time = time.time()
    while True:
        second_request = client.get(f"https://yams.tf/api?id={request_id}").json()
        status = second_request["status"]
        current = second_request["current"]
        progress = second_request["progress"]
        total = second_request["total"]

        clear_console()
        log_message(f"{status} - {current} ({progress} / {total})", start_time, end="\r")
        
        if status == "done":
            clear_console() 
            log_message("Got download link!", start_time)
            return second_request["url"]
        if status == "error":
            log_message(f"yams.tf failed: {second_request['error']}", start_time)
            raise SystemExit(0)
        
        time.sleep(3)

def download_file(client, download_url, referrer_url):
    start_time = time.time()
    third_request = client.get(
        f"{download_url}/download",
        headers={
            "referrer": referrer_url,
            "User-Agent": "yams.tf-downloader/v1",
        }
    )
    redirect = third_request.headers.get('Hx-Redirect')
    fourth_request = client.get(
        "https://buzzheavier.com" + redirect,
        headers={
            "referrer": referrer_url,
            "User-Agent": "yams.tf-downloader/v1",
        },
        stream=True
    )
    
    total_size = int(fourth_request.headers.get('content-length', 0))
    total_size_mb = total_size / (1024 * 1024)
    downloaded_size = 0
    chunk_size = 1024 * 1024  # 1 MB
    with open("downloaded.zip", "wb") as f:
        for chunk in fourth_request.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded_size += len(chunk)
                remaining_size = (total_size - downloaded_size) / (1024 * 1024)
                clear_console()
                log_message(f"Remaining: {remaining_size:.2f} MB / {total_size_mb:.2f} MB", start_time, end="\r")
    
    log_message("Download completed.", start_time)
    return fourth_request

def save_file(content):
    with open("downloaded.zip", "wb") as f:
        f.write(content)

def extract_zip():
    start_time = time.time()
    with zipfile.ZipFile("downloaded.zip", "r") as zip_ref:
        zip_ref.extractall("extracted")
    os.remove("downloaded.zip")
    log_message("Extracted to extracted/.", start_time)

    if input("Do you want to remove the last numbers on the extracted folder? eg: [293182312] [2023] (y/n): ").lower() == "y":
        for folder_name in os.listdir("extracted"):
            new_name = re.sub(r' \[\d+\] \[\d+\]$', '', folder_name)
            os.rename(os.path.join("extracted", folder_name), os.path.join("extracted", new_name))
        log_message("Renamed extracted folders.", start_time)

def main():
    url = input("Enter the URL: ")
    client = requests.Session()
    
    first_request = download_song(url)
    download_url = check_status(client, first_request['id'])
    
    log_message("Attempting to download...", time.time())
    fourth_request = download_file(client, download_url, download_url)
    
    if fourth_request.status_code == 200:
        log_message("Downloaded, saving to file...", time.time())
        
        if input("Do you want to extract the zip file? (y/n): ").lower() == "y":
            extract_zip()
    else:
        log_message("Failed to download", time.time())
    
    log_message("Done", time.time())

if __name__ == "__main__":
    main()
