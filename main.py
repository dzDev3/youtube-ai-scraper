import os
import time
import requests
import re
import pandas as pd
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
except ImportError:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)

DEBUG_MODE = False
try:
    init(autoreset=True)
except ImportError:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)

# Muat variabel environment dari file .env di direktori yang sama
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"), override=True)

# =============================================================================
# 1. KONFIGURASI
# =============================================================================

SPREADSHEET_ID = "13TzQG2FKkRJxto1cMVVwIHxdq3ZLhde2k96xjqmzr-Q"
MAX_VIDEOS_PER_KEYWORD = 5
REQUEST_DELAY = 2.0  # Jeda diperlama agar hemat kuota
DATASET_FILE = "dataset_komentar_youtube_ai.csv"
VIDEO_LIST_FILE = "daftar_video_ai.csv"

# =============================================================================
# 2. FUNGSI-FUNGSI UTAMA
# =============================================================================

def load_api_key():
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"), override=True)
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key: api_key = api_key.strip().strip("\"'").strip()
    if not api_key or api_key == "ISI_API_KEY_KAMU":
        raise ValueError("API key YouTube tidak ditemukan di file .env.")
    return api_key

def get_google_sheets_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials_file = os.path.join(SCRIPT_DIR, "service_account.json")
    if not os.path.exists(credentials_file):
        print(f"\n[WARNING] File '{credentials_file}' tidak ditemukan.")
        return None
    try:
        credentials = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"\n[ERROR] Gagal otorisasi Google Sheets: {e}")
        return None

def load_keywords(filename="keywords.txt"):
    filepath = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"\n[ERROR] File '{filename}' tidak ditemukan. Silakan buat file tersebut dengan daftar kata kunci.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]
    return keywords

def load_nim(filename="nim.txt"):
    filepath = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"\n[WARNING] File '{filename}' tidak ditemukan. Kolom NIM akan kosong.")
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        nim = f.read().strip()
    return nim
def load_spreadsheet_id(filename="spreadsheet_url.txt"):
    filepath = os.path.join(SCRIPT_DIR, filename)
    url = ""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            url = f.read().strip()
            
    if not url:
        print("\n  >> Masukkan URL Google Sheets Anda (contoh: https://docs.google.com/spreadsheets/d/1sx3OvWHiXs1kOg75qLyE43VloSJJIENpCJ9kac56h9k/edit...): ")
        url = input(f"{Fore.MAGENTA}  URL: ").strip()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(url)
            
    # Ekstrak ID dari URL
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    return url


def log_info(msg): print(f"{Fore.CYAN}{Style.BRIGHT}[INFO] {Style.NORMAL}{msg}")
def log_success(msg): print(f"{Fore.GREEN}{Style.BRIGHT}[OK] {Style.NORMAL}{msg}")
def log_warn(msg): print(f"{Fore.YELLOW}{Style.BRIGHT}[WARNING] {Style.NORMAL}{msg}")
def log_error(msg): print(f"{Fore.RED}{Style.BRIGHT}[ERROR] {Style.NORMAL}{msg}")
def log_step(msg): print(f"\n{Back.CYAN}{Fore.WHITE}{Style.BRIGHT}  {msg}  {Style.RESET_ALL}")



def parse_duration(iso_duration):
    # Mengubah format PT5M30S atau PT1H15M20S menjadi HH:MM:SS
    if not iso_duration: return "00:00:00"
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match: return "00:00:00"
    hours = match.group(1) or "0"
    minutes = match.group(2) or "0"
    seconds = match.group(3) or "0"
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def search_videos(keyword, min_comments=100, max_videos=MAX_VIDEOS_PER_KEYWORD, nim=""):
    api_key = load_api_key()
    base_url = "https://www.googleapis.com/youtube/v3/search"
    videos = []
    
    # 1. Cari video
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": min(max_videos * 2, 25), # Dikurangi agar tidak kena limit # Ambil lebih banyak untuk cadangan jika difilter
        "relevanceLanguage": "id",
        "key": api_key,
    }

    try:
        print(f"  {Fore.YELLOW}[SEARCH]{Style.RESET_ALL} Mencari video untuk keyword: '{keyword}'")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
        if not video_ids: return []
        
        # 2. Cek statistik video (ambil commentCount)
        stat_url = "https://www.googleapis.com/youtube/v3/videos"
        stat_params = {
            "part": "statistics,snippet,contentDetails",
            "id": ",".join(video_ids),
            "key": api_key
        }
        
        stat_response = requests.get(stat_url, params=stat_params)
        stat_response.raise_for_status()
        stat_data = stat_response.json()
        
        for item in stat_data.get("items", []):
            if len(videos) >= max_videos:
                break
                
            stats = item.get("statistics", {})
            # DEBUG: Lihat apa yang dikirim YouTube
            # print(f"      [DEBUG] Stats Video {item['id']}: {stats}") 
            comment_count = int(stats.get("commentCount", 0))
            
            if comment_count >= min_comments:
                # Mengubah durasi ISO 8601 (misal PT5M30S) ke format HH:MM:SS
                duration = parse_duration(item.get("contentDetails", {}).get("duration", ""))
                
                # FIX: Tangani jika likeCount disembunyikan (None) atau dibatasi
                v_likes_raw = stats.get("likeCount", 0)
                try: view_count = int(stats.get("viewCount", 0))
                except: view_count = 0
                try: like_count = int(v_likes_raw)
                except: like_count = 0
                
                if DEBUG_MODE and len(videos) == 0:
                    print(f"\n      [DEBUG] Raw Stats untuk video '{item['snippet']['title'][:30]}...' : {stats}")
                    print(f"      [DEBUG] likeCount raw: {v_likes_raw} (tipe: {type(v_likes_raw)})\n")
                
                video = {
                "NIM": nim,  # Tambahkan NIM di posisi pertama
                "Video_ID": item["id"],
                "Judul_Video": item["snippet"]["title"],
                "Channel": item["snippet"]["channelTitle"],
                "Durasi": duration,
                "Jumlah View": view_count,
                "Jumlah Like": like_count,
                "Jumlah Komentar": comment_count,
                "Topik": keyword,
                "Tanggal_Video": item["snippet"]["publishedAt"][:10], # Ambil YYYY-MM-DD saja
                "URL_Video": f"https://www.youtube.com/watch?v={item['id']}"
            }
                videos.append(video)
                
        print(f"    {Fore.GREEN}==>{Style.RESET_ALL} Ditemukan {len(videos)} video yang aktif (syarat: >= {min_comments} komentar di YouTube).")

    except requests.exceptions.RequestException as e:
        if "429" in str(e):
            print(f"    [ERROR] LIMIT KUOTA (429)! YouTube membatasi request. Menunggu 10 detik sebelum lanjut...")
            time.sleep(10)
        else:
            print(f"    [ERROR] Gagal mencari video: {e}")

    return videos

    
    # Kriteria 1: Minimal jumlah kata
    words = text.split()
    if len(words) < min_words: return False
    
    # Kriteria 2: Minimal jumlah like
    if like_count < min_likes: return False
    
    # Kriteria 3: Tidak mengandung link (spam)
    if "http://" in text or "https://" in text or "www." in text: return False
    
    # Kriteria 4: Bukan spam hashtag berlebihan
    if text.count("#") > 3: return False
    
    return True

def get_video_comments(video, target_comments):
    api_key = load_api_key()
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    next_page_token = None
    
    try:
        while len(comments) < target_comments:
            params = {
                "part": "snippet",
                "videoId": video["Video_ID"],
                "maxResults": 100, # Selalu minta maksimal per halaman
                "textFormat": "plainText",
                "key": api_key,
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                if len(comments) >= target_comments:
                    break

                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet["textDisplay"]
                
                comment = {
                "NIM": video["NIM"],
                "Video_ID": video["Video_ID"],
                "Judul_Video": video["Judul_Video"],
                "Channel": video["Channel"],
                "Durasi": video["Durasi"],
                "Jumlah View": video["Jumlah View"],
                "Jumlah Like": video["Jumlah Like"],
                "Jumlah Komentar": video["Jumlah Komentar"],
                "Topik": video["Topik"],
                "Tanggal_Video": video["Tanggal_Video"],
                "URL_Video": video["URL_Video"],
                "Nama_Komentator": snippet.get("authorDisplayName", "Anonim"),
                "Teks_Komentar": text,
                "Tanggal_Komentar": snippet["publishedAt"][:10],
                "Label_Kualitas": ""
            }
                comments.append(comment)

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
                
            time.sleep(REQUEST_DELAY)

        print(f"    {Fore.GREEN}==>{Style.RESET_ALL} {len(comments)} komentar berkualitas.")
        
    except requests.exceptions.RequestException as e:
        print(f"    [ERROR] Gagal mengambil komentar: {e}")

    return comments

def clean_dataset(df):
    if df.empty: return df
    df["Teks_Komentar"] = df["Teks_Komentar"].astype(str)
    df["Teks_Komentar"] = df["Teks_Komentar"].apply(lambda x: re.sub(r'[\r\n]+', ' ', x).strip())
    df = df.drop_duplicates(subset=["Nama_Komentator", "Teks_Komentar"], keep="first")
    df = df.sort_values(by=["Topik", "Judul_Video"], ascending=[True, True])
    return df

def save_to_csv(df, filename):
    if df.empty: return
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"  - Disimpan ke: {filename}")

def save_to_google_sheets(client, df, spreadsheet_id, sheet_name, column_order=None):
    if client is None or df.empty: return
    try:
        print(f"\n[INFO] Mengirim data ke Google Sheets ({sheet_name})...")
        sheet = client.open_by_key(spreadsheet_id)
        
        # Susun ulang kolom sesuai urutan yang benar
        if column_order:
            available_cols = [col for col in column_order if col in df.columns]
            df = df[available_cols]
        
        # Cek apakah worksheet ada, jika tidak maka buat baru
        try:
            worksheet = sheet.worksheet(sheet_name)
            print(f"  - Worksheet '{sheet_name}' ditemukan. Membersihkan data lama...")
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            print(f"  - Membuat worksheet baru: {sheet_name}")
            worksheet = sheet.add_worksheet(title=sheet_name, rows=str(len(df) + 100), cols=str(len(df.columns) + 2))
            
        df = df.fillna("")
        data_to_write = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(range_name="A1", values=data_to_write)
        
        # Format header (baris pertama) menjadi Bold
        try:
            from gspread_formatting import get_default_format, format_cell_range, CellFormat, TextFormat
            fmt = CellFormat(textFormat=TextFormat(bold=True))
            format_cell_range(worksheet, "A1:Z1", fmt)
        except ImportError:
            pass
            
        print(f"  [OK] Berhasil menulis {len(df)} baris ke Google Sheets.")
    except Exception as e:
        print(f"  [ERROR] {e}")

# =============================================================================
# 3. FUNGSI UTAMA (MAIN)
# =============================================================================

def main():
    
    print(f"{Fore.CYAN}{Style.BRIGHT}" + "="*65 + f"\n  YOUTUBE AI COMMENTS SCRAPER + GOOGLE SHEETS\n" + "="*65)
    

    log_step("TAHAP 1: PERSIAPAN & KONFIGURASI")
    
    # Input kustomisasi jumlah video
    try:
        total_target_videos = int(input(f"{Fore.MAGENTA}{Style.BRIGHT}  >> {Style.NORMAL}Berapa jumlah video YouTube yang ingin diambil? (Misal: 10): "))
        if total_target_videos <= 0: total_target_videos = 5
    except ValueError:
        print("  [WARNING] Input tidak valid. Menggunakan default 5 video.")
        total_target_videos = 5

    # Input kustomisasi jumlah komentar per video
    try:
        comments_per_video = int(input(f"{Fore.MAGENTA}{Style.BRIGHT}  >> {Style.NORMAL}Berapa target KOMENTAR BERKUALITAS per video? (Misal: 100): "))
        if comments_per_video <= 0: comments_per_video = 100
    except ValueError:
        print("  [WARNING] Input tidak valid. Menggunakan default 100 komentar/video.")
        comments_per_video = 100
    total_target_comments = total_target_videos * comments_per_video


    try:
        api_key = load_api_key()
        log_success("YouTube API Key termuat.")
    except ValueError as e:
        print(f"  [ERROR] {e}")
        return
        
    spreadsheet_id = load_spreadsheet_id()
    log_success(f"Spreadsheet ID: {spreadsheet_id}")
    
    gsheets_client = get_google_sheets_client()
    keywords = load_keywords()
    nim = load_nim()
    log_success(f"NIM termuat: {nim}")
    
    if not keywords:
        return

    print("\n" + "=" * 65)
    log_step(f"TAHAP 2: MENCARI VIDEO (TARGET: {total_target_comments} KOMENTAR)")
    

    all_videos = []
    # Asumsikan tiap keyword dapat video yang berbeda, bagi rata dengan kelipatan
    per_keyword_limit = max(1, (total_target_videos // len(keywords)) + 3)
    
    for keyword in keywords:
        if len(all_videos) >= total_target_videos:
            break
        
        # Cari video sebanyak mungkin
        videos = search_videos(keyword, min_comments=100, max_videos=per_keyword_limit, nim=nim)
        all_videos.extend(videos)
        time.sleep(REQUEST_DELAY)

    if not all_videos:
        print("\n[INFO] Tidak ada video yang ditemukan. Program selesai.")
        return

    df_videos = pd.DataFrame(all_videos)
    df_videos = df_videos.drop_duplicates(subset=["Video_ID"], keep="first")
    all_videos = df_videos.to_dict("records")

    print("\n" + "=" * 65)
    log_step(f"TAHAP 3: PENGAMBILAN KOMENTAR (TARGET: {total_target_comments})")
    

    all_comments = []
    video_list = df_videos.to_dict("records")

    for i, video in enumerate(video_list, 1):
        print(f"\n  {Fore.CYAN}{Style.BRIGHT}[{i}/{len(video_list)}]{Style.RESET_ALL} Video: {video['Judul_Video'][:40]}...")
        
        # Ambil komentar sesuai target PER VIDEO
        # Buffer +30 untuk cadangan jika banyak yang tidak lolos filter
        batas_ambil = comments_per_video + 30
        
        comments = get_video_comments(video, batas_ambil)
        all_comments.extend(comments)
        time.sleep(REQUEST_DELAY)

    # Potong agar pas dengan target yang diminta
    if len(all_comments) > total_target_comments:
        all_comments = all_comments[:total_target_comments]

    if not all_comments:
        print("\n[INFO] Tidak ada komentar berkualitas yang berhasil diambil.")
        return

    print("\n" + "=" * 65)
    print("[TAHAP 4] Membersihkan Dataset...")
    

    df_comments = pd.DataFrame(all_comments)
    df_comments = clean_dataset(df_comments)

    print("\n" + "=" * 65)
    print("[TAHAP 5] Menyimpan Data...")
    

    # save_to_csv(df_videos, VIDEO_LIST_FILE)
    save_to_csv(df_comments, "hasil_scraping_youtube.csv")
    
    if gsheets_client:
        final_col_order = [
            "NIM", "Video_ID", "Judul_Video", "Channel", "Durasi", 
            "Jumlah View", "Jumlah Like", "Jumlah Komentar", "Topik", "Tanggal_Video", "URL_Video",
            "Nama_Komentator", "Teks_Komentar", "Tanggal_Komentar"
        ]
        save_to_google_sheets(gsheets_client, df_comments, spreadsheet_id, "Sheet1", column_order=final_col_order)

    print("\n" + "=" * 65)
    print("  PROSES SELESAI!")
    

if __name__ == "__main__":
    main()
