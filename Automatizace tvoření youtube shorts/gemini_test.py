import os
import requests
import re
import moviepy.config as cfg
from moviepy.video.fx.all import crop
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip
from pydub import AudioSegment, silence
from google.cloud import texttospeech
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

os.environ["PATH"] += os.pathsep + r"D:\Short Machine Gun\ffmpeg-7.1-essentials_build\bin"

# Nastavení cesty k ffmpeg
AudioSegment.converter = r"ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"ffmpeg-7.1-essentials_build\bin\ffprobe.exe"

print("Cesta k ffmpeg:", AudioSegment.converter)
print("Existuje soubor ffmpeg?", os.path.isfile(AudioSegment.converter))

print("Cesta k ffprobe:", AudioSegment.ffprobe)
print("Existuje soubor ffprobe?", os.path.isfile(AudioSegment.ffprobe))


#print("Pydub ffmpeg version test...")
#audio = AudioSegment.from_file("output/voiceover.mp3", format="mp3")
#print("Audio loaded successfully!")

# Nastavení cesty k ImageMagick
cfg.IMAGEMAGICK_BINARY = r"ImageMagick-7.1.1-Q16-HDRI\magick.exe"

# Nastavení API klíčů
PEXELS_API_KEY = "YOUR_PEXELS_API_KEY"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "JSON_FILE_WITH_GOOGLE_APP_CREDS"

# Vytvoření složek pro soubory
os.makedirs("videos", exist_ok=True)
os.makedirs("output", exist_ok=True)

# --- 1. Stažení videí z Pexels API ---
def download_videos(query, min_total_duration=60):
    print("Stahuji videa z Pexels...")
    headers = {"Authorization": PEXELS_API_KEY}
    total_duration = 0
    downloaded_files = []
    page = 1

    while total_duration < min_total_duration:
        # Načítání videí po stránkách
        response = requests.get(
            f"https://api.pexels.com/videos/search?query={query}&per_page=10&page={page}", 
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(f"Chyba při stahování videí: {response.status_code}")
        
        videos = response.json().get('videos', [])
        if not videos:
            print("Žádná další videa nebyla nalezena.")
            break

        # Stažení a přidání videí do seznamu
        for video in videos:
            video_url = video['video_files'][0]['link']
            file_path = f"videos/video_{len(downloaded_files)}.mp4"
            with open(file_path, "wb") as f:
                f.write(requests.get(video_url).content)

            clip = VideoFileClip(file_path)
            downloaded_files.append((file_path, clip.duration))
            total_duration += clip.duration
            print(f"  Staženo: {file_path}, délka: {clip.duration} sekund (celkem: {total_duration:.2f}s)")

            if total_duration >= min_total_duration:
                break
        page += 1

    return [f[0] for f in downloaded_files]

# --- 2. Generování hlasu pomocí Google TTS ---
def generate_voice(text, output_file, log_file="used_characters.txt"):
    from google.cloud import texttospeech
    print("Generuji hlasový komentář...")

    # Inicializace Google TTS klienta
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    # Volání Google TTS API
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    print(f"Hlas uložen do: {output_file}")

    # Počítání znaků
    num_characters = len(text)
    print(f"Počet znaků v aktuálním textu: {num_characters}")

    # Aktualizace souboru s počtem znaků
    total_characters = 0
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            total_characters = int(f.read().strip())
    
    total_characters += num_characters  # Přičtení nových znaků

    # Uložení aktualizovaného počtu znaků
    with open(log_file, "w") as f:
        f.write(str(total_characters))

    print(f"Celkový počet použitých znaků: {total_characters}")

def split_audio_by_pauses(audio_file, output_dir):
    """
    Rozdělí audio soubor na menší segmenty na základě detekovaných pauz.
    Každý segment uloží jako nový soubor.
    """
    print("Rozděluji audio soubor na úseky podle detekovaných pauz...")
    audio = AudioSegment.from_mp3(audio_file)

    min_silence_len = 300  # Minimální délka pauzy (v ms)
    silence_thresh = audio.dBFS - 16  # Práh hlasitosti

    pauses = silence.detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    pauses = [(start, end) for start, end in pauses]

    segment_starts = [0] + [end for _, end in pauses]
    segment_ends = [start for start, _ in pauses] + [len(audio)]

    os.makedirs(output_dir, exist_ok=True)

    segments = []
    for i, (start, end) in enumerate(zip(segment_starts, segment_ends)):
        segment = audio[start:end]
        output_path = os.path.join(output_dir, f"segment_{i+1}.mp3")
        segment.export(output_path, format="mp3")
        segments.append((output_path, (start / 1000, end / 1000)))
        print(f"Uložen segment {i+1}: {output_path}")
    return segments

def split_text_by_punctuation(text):
    """
    Rozdělí text na bloky podle interpunkčních znamének (!, ., :, ,).
    """
    segments = re.split(r'([!.,:?])', text)
    blocks = []
    for i in range(0, len(segments) - 1, 2):
        sentence = segments[i].strip() + segments[i + 1]
        if sentence.strip():
            blocks.append(sentence)
    return blocks

def analyze_audio_timing(audio_file, words):
    """
    Analyzuje audio soubor a přiřazuje bloky slov do pauz.
    Vrátí seznam tuple (textový blok, start_time, end_time).
    """
    print("Analyzuji časování audia...")
    from pydub import AudioSegment, silence

    # Načtení audio souboru
    audio = AudioSegment.from_mp3(audio_file)

    # Parametry pro detekci pauz
    min_silence_len = 300  # Minimální délka pauzy (v ms)
    silence_thresh = audio.dBFS - 16  # Práh hlasitosti (ticho je 16 dB pod hlasitostí audia)

    # Detekce pauz
    pauses = silence.detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    pauses = [(start / 1000, end / 1000) for start, end in pauses]  # Převod na sekundy
    total_duration = audio.duration_seconds

    print(f"Nalezeno {len(pauses)} pauz v audionahrávce.")

    # Rozdělení slov na bloky podle počtu pauz
    num_pauses = len(pauses)
    words_per_pause = len(words) // num_pauses if num_pauses > 0 else len(words)

    timestamps = []
    current_index = 0

    for start, end in pauses:
        # Sesbíráme slova pro aktuální pauzu
        block_words = words[current_index:current_index + words_per_pause]
        if not block_words:
            break

        text_block = "\n".join(block_words)  # Spojíme slova do víceřádkového textu
        timestamps.append((text_block, start, end))
        current_index += words_per_pause

    return timestamps

def number_to_words(num_str):
    # Jednoduchá funkce pro převod čísla na anglický "slovní" tvar pro účely časování.
    # Pro démonstrační účely pojmeme jednoduše:
    # - Pokud je jednociferné číslo, použijeme jednoduchý slovník.
    # - Pokud vícemístné, hrubý odhad: převedeme každou číslici na slovo a spojíme.

    single_digits = {
        '0': 'zero',
        '1': 'one',
        '2': 'two',
        '3': 'three',
        '4': 'four',
        '5': 'five',
        '6': 'six',
        '7': 'seven',
        '8': 'eight',
        '9': 'nine'
    }

    if num_str.isdigit():
        # Převedeme každou cifru na slovo a spojíme
        spelled_out = "".join(single_digits[d] for d in num_str)
        return spelled_out
    else:
        return num_str
    
def create_video_with_segments(video_files, audio_file, audio_segments, subtitles_blocks, output_file):
    """
    Vytvoří finální video s "karaoke" efektem, vícero řádky a s upraveným počítáním délky slov:
    - Text se zalomí do více řádků tak, aby nepřesáhl šířku videa.
    - Časování slov zohlední čísla, která jsou pro účely časování převedena do slova.
    """
    print("Vytvářím finální video s karaoke titulky (více řádků a úprava čísel)...")

    # 1. Načtení videoklipů
    clips = [VideoFileClip(f).resize(height=1920, width=1080) for f in video_files]
    combined_clip = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_file)

    # Omezení videa podle délky audia
    combined_clip = combined_clip.set_duration(audio.duration)
    cropped_clip = crop(combined_clip, width=1080, height=1920, 
                        x_center=combined_clip.w / 2, y_center=combined_clip.h / 2)

    subtitle_clips = []
    video_width = 1080
    video_height = 1920
    max_line_width = 900  # maximální šířka textu na řádku
    spacing = 20  # mezera mezi slovy
    line_spacing = 10  # mezera mezi řádky

    for i, ((_, (segment_start, segment_end)), subtitle_block) in enumerate(zip(audio_segments, subtitles_blocks)):
        words = subtitle_block.split()
        if not words:
            continue

        # Upravit slova pro časování: čísla na slovní ekvivalent
        timing_words = [number_to_words(w) for w in words]

        # Spočítat celkový počet znaků pro časování
        total_chars = sum(len(tw) for tw in timing_words)
        if total_chars == 0:
            continue
        segment_duration = segment_end - segment_start

        # Vypočítat timing pro každé slovo
        current_start = segment_start
        word_timings = []
        for w, tw in zip(words, timing_words):
            w_len = len(tw)
            w_duration = (w_len / total_chars) * segment_duration
            w_end = current_start + w_duration
            word_timings.append((w, current_start, w_end))
            current_start = w_end

        # Při generování karaoke efektu:
        # Pro každý "stav" (kdy je jedno slovo aktivní) zobrazíme všechny slova.
        # Tentokrát ale musíme text rozdělit do více řádků.

        for word_index, (active_word, w_start, w_end) in enumerate(word_timings):
            # Nejprve vytvoříme TextClip pro každé slovo v jeho barvě
            word_clips = []
            for j, (orig_word, _) in enumerate(zip(words, word_timings)):
                color = 'red' if j == word_index else 'white'
                wc = TextClip(
                    orig_word,
                    fontsize=70,
                    color=color,
                    stroke_color='black',
                    stroke_width=3,
                    font='Atma-Bold.ttf',
                    method='caption'
                )
                word_clips.append(wc)

            # Nyní word_clips máme jako seznam všech slov. Musíme je zalomit do řádků.
            lines = []
            current_line = []
            current_line_width = 0

            for wc in word_clips:
                if current_line:
                    new_width = current_line_width + wc.w + spacing
                else:
                    new_width = wc.w
                if new_width <= max_line_width:
                    # Přidáme slovo do stávajícího řádku
                    current_line.append(wc)
                    current_line_width = new_width
                else:
                    # Začneme nový řádek
                    if current_line:
                        lines.append(current_line)
                    current_line = [wc]
                    current_line_width = wc.w
            # poslední řádek pokud není prázdný
            if current_line:
                lines.append(current_line)

            # Máme nyní seznam řádků (list of list of word_clips)
            # Spočítáme celkovou výšku textu
            line_heights = [max(wc.h for wc in line) for line in lines]
            total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)

            # Vycentrujeme text svisle
            start_y = (video_height - total_text_height) / 2

            positioned_clips = []
            current_y = start_y
            for line in lines:
                # Výška tohoto řádku
                lh = max(wc.h for wc in line)
                # Celková šířka řádku
                line_width = sum(wc.w for wc in line) + spacing * (len(line)-1)
                start_x = (video_width - line_width) / 2
                current_x = start_x
                for wc in line:
                    positioned_clips.append(wc.set_position((current_x, current_y)))
                    current_x += wc.w + spacing
                current_y += lh + line_spacing

            # Složíme do jednoho klipu
            line_clip = CompositeVideoClip(positioned_clips, size=(video_width, video_height))\
                .set_start(w_start)\
                .set_duration(w_end - w_start)

            subtitle_clips.append(line_clip)

    final_video = CompositeVideoClip([cropped_clip] + subtitle_clips).set_audio(audio)
    final_video.write_videofile(output_file, fps=24, codec="libx264")

    print(f"Finální video uloženo do: {output_file}")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("JSON_GOOGLE_CLIENT_SECRET", SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def get_and_increment_episode_number(file_name="episode_number.txt"):
    # Pokud soubor neexistuje, začneme od 1
    if not os.path.exists(file_name):
        current_episode = 1
    else:
        with open(file_name, "r") as f:
            current_episode = int(f.read().strip())

    # Vrátíme aktuální číslo epizody a hned ho inkrementujeme pro příští běh
    next_episode = current_episode + 1

    with open(file_name, "w") as f:
        f.write(str(next_episode))

    return current_episode

def upload_video(video_file, title, description, tags, category_id="22", privacy_status="public"):
    youtube = get_authenticated_service()
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/*")

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload Progress: {int(status.progress() * 100)}%")

    print("Video bylo nahráno!")
    print("Video ID:", response.get("id"))


# --- 4. Hlavní část programu ---
if __name__ == "__main__":
    try:
        # Manuální zadání tématu a textu
        topic = "sharks"
        text ="""Welcome to another jaw-dropping video! Here are the Top 5 Amazing Facts About Sharks.
        Fact number one: Sharks have been around for over 400 million years, making them older than dinosaurs.
        Fact number two: The largest shark in the world, the Whale Shark, can grow up to 12 meters long.
        Fact number three: Sharks have an incredible sense of smell and can detect a single drop of blood from hundreds of meters away.
        Fact number four: Some sharks, like the Great White, can swim at speeds of up to 50 kilometers per hour.
        Fact number five: Sharks do not have bones. Their skeletons are made of cartilage, which is lighter and more flexible.
        Which shark fact amazed you the most? Let us know in the comments!"""


        # Krok 1: Stažení videí
        video_files = download_videos(topic)

        # Krok 2: Generování hlasu
        audio_file = "output/voiceover.mp3"
        generate_voice(text, audio_file)
        output_dir = "output/audio_segments"  # Složka pro uložení segmentů
        audio_segments_dir = "output/audio_segments"

        # Krok 1: Rozdělení textu na bloky
        subtitles_blocks = split_text_by_punctuation(text)
        print("Rozdělené bloky textu:")
        for i, block in enumerate(subtitles_blocks, 1):
            print(f"  Segment {i}: {block}")

        # Krok 2: Rozdělení audia na segmenty
        audio_segments = split_audio_by_pauses(audio_file, audio_segments_dir)
        
        # Krok 3: Vytvoření finálního videa s titulky
        output_file = "output/final_video.mp4"
        #create_video(video_files, audio_file, output_file, script)
        create_video_with_segments(video_files, audio_file, audio_segments, subtitles_blocks, output_file)

        VIDEO_FILE = "output/final_video.mp4"  # cesta k vašemu finálnímu videu
        episode_number = get_and_increment_episode_number("episode_number.txt")
        TITLE = f"Random Daily Facts #{episode_number}"
        TAGS = [
            "shorts",
            "viral",
            "trending",
            "amazing",
            "interesting",
            "awesome",
            "fun",
            "cool",
            "wow",
            "daily",
            "facts",
            "today",
            "new",
            "2024",
            "inspiration",
            "entertainment",
            "random",
            "knowledge",
            "learning",
            "world",
            "life",
            "discover",
            "curiosity",
            "informative",
            "ai"
        ]
        DESCRIPTION = "Daily interesting facts about everything. #Shorts\n\n" + " ".join([f"#{tag}" for tag in TAGS])
        CATEGORY_ID = "24"

        upload_video(VIDEO_FILE, TITLE, DESCRIPTION, TAGS, CATEGORY_ID, "public")
    except Exception as e:
        print(f"Chyba v programu: {e}")
