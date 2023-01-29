import pytube
import json
import whisper
import os.path
from datetime import datetime
from moviepy.editor import VideoFileClip
from pytube.exceptions import RegexMatchError
from options import LANGUAGES
from pathlib import Path


def whisper_to_text(whisper_output):
    return whisper_output["text"]


def whisper_to_timestamp_view(whisper_output):
    output = [
        "| Start | End | Text |",
        "|----|----|----|"
    ]
    for segment in whisper_output['segments']:
        output.append(
            f"| {segment['start']:.2f} | {segment['end']:.2f} | {segment['text']} |")
    return "\n".join(output)


def whisper_to_timestamp_table(whisper_output):
    return [[round(segment['start'], 2), round(segment['end'], 2), segment['text']]
            for segment in whisper_output['segments']]


def whisper_to_json(whisper_output):
    output = []
    for segment in whisper_output['segments']:
        output.append({
            # 'id': segment['id'],
            'start': round(segment['start'], 2),
            'end': round(segment['end'], 2),
            'text': segment['text'],
            # 'seek': segment['seek'],
            # 'tokens': segment['tokens'],
            # 'temperature': segment['temperature'],
            # 'avg_logprob': segment['avg_logprob'],
            # 'compression_ratio': segment['compression_ratio'],
            # 'no_speech_prob': segment['no_speech_prob'],
        })
    return output


def whisper_to_json_raw(whisper_output):
    output = []
    for segment in whisper_output['segments']:
        output.append({
            'id': segment['id'],
            'start': round(segment['start'], 2),
            'end': round(segment['end'], 2),
            'text': segment['text'],
            'seek': segment['seek'],
            # 'tokens': segment['tokens'],
            'temperature': segment['temperature'],
            'avg_logprob': segment['avg_logprob'],
            'compression_ratio': segment['compression_ratio'],
            'no_speech_prob': segment['no_speech_prob'],
        })
    return output


def combo_formatter(result):
    return whisper_to_text(result), whisper_to_timestamp_view(result), whisper_to_timestamp_table(result), whisper_to_json(result), whisper_to_json_raw(result)


def get_video_data(url):
    if url == "" or url is None:
        return None
    try:
        video = pytube.YouTube(url)
        return video.thumbnail_url, video.author, video.title, video.length, video.publish_date
    except RegexMatchError:
        return None


def download_yt_video(url, output_path):
    video = pytube.YouTube(url)
    stream = video.streams.get_by_itag(18)
    stream.download(output_path)
    return stream.default_filename


def convert_to_mp3(input_filepath, output_filepath):
    clip = VideoFileClip(input_filepath)
    clip.audio.write_audiofile(output_filepath)
    clip.close()


def audio_to_text(filepath, model_language="multilingual", model="base", language=None, output_path=None):
    # load the choosen model
    lang_code = LANGUAGES[language]
    model_name = model + (".en" if model_language == "english-only" else "")
    model = whisper.load_model(model_name)

    # return the transcript of the given audio
    result = model.transcribe(filepath, language=lang_code)

    # remove all surrounding whitespace characters
    result["text"] = result["text"].strip()
    for i, items in enumerate(result['segments']):
        result['segments'][i]["text"] = items["text"].strip()

    # format result
    text, md, table, jsn, jsn_raw = combo_formatter(result)

    # create files
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = Path(filepath).stem[:-8]
    txt_path = output_path / current_date / f'{filename}.txt'
    md_path = output_path / current_date/f'{filename}.md'
    json_path = output_path / current_date / f'{filename}.json'
    json_raw_path = output_path / current_date / f'{filename}_raw.json'
    if output_path is not None:
        (output_path / current_date).mkdir(exist_ok=True)
        with open(txt_path, "w") as f:
            f.write(text)
        with open(md_path, "w") as f:
            f.write(md)
        with open(json_path, "w") as f:
            f.write(json.dumps(jsn, indent=4, ensure_ascii=False))
        with open(json_raw_path, "w") as f:
            f.write(json.dumps(jsn_raw, indent=4, ensure_ascii=False))

    return [text, md, table, jsn, jsn_raw], [txt_path, md_path, json_path, json_raw_path]


def remove_file(filepath):
    try:
        os.remove(filepath)
    except:
        print(f"File {filepath} couldn't be removed.")


def update_cachefile(cache_file):
    if os.path.exists(cache_file):
        data = []
        with open(cache_file, "r") as f:
            data = [(line.split("\t")[0], line.split("\t")[1])
                    for line in f.read().strip().split("\n") if line != ""]
        new_data = []
        for url, filepath in data:
            if os.path.exists(filepath):
                new_data.append((url, filepath))

        with open(cache_file, "w") as f:
            f.write("\n".join("\t".join(item) for item in new_data) + "\n")

    else:
        with open(cache_file, "w") as f:
            f.write("")


def find_in_cache(cache_file, url):
    new_file = []
    found_expired_value = False

    with open(cache_file, "r") as f:
        file_content = f.read()
        cached_audio = [(item.split("\t", 1)[0], item.split("\t", 1)[1])
                        for item in file_content.strip().split("\n") if item != ""]
        for cached_url, filepath in cached_audio:
            if cached_url == url:
                if os.path.exists(filepath):
                    return filepath
                found_expired_value = True
            else:
                new_file.append([cached_url, filepath])

    if found_expired_value:
        with open(cache_file, "w") as f:
            f.write("\n".join(["\t".join(item) for item in new_file]) + "\n")

    return None
