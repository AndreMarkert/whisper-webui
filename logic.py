from shutil import move, copy2
import gradio as gr
import os
from pathlib import Path
from datetime import datetime
from environment import YT_SAVE_AUDIO, YT_USE_CACHE, CACHE_FILE, TEMP_PATH, OUTPUT_PATH, DOWNLOAD_PATH, RECORDING_PATH, DEFAULT_LANGUAGE
from functions import *


def get_yt_default_options():
    options = []
    if YT_SAVE_AUDIO:
        options.append("Save Audio")
    if YT_USE_CACHE:
        options.append("Use Cache")
    return options


def set_yt_preview(url):
    data = get_video_data(url)
    if data is not None:
        thumbnail_url, author, title, length, publish_date = data
        preview = f"""
        #### {title}<br>
        by **{author}**<br><br>
        **Duration**: {length//3600:0>2}:{(length//60)%60:0>2}:{length%60:0>2}<br>
        **Published**: {publish_date.date()}"""

        return [gr.update(value=thumbnail_url),
                gr.update(value=preview)]
    return [gr.update(value=None),
            gr.update(value=None)]


def youtube_to_subtitles(url, model_language, model, language, yt_options):
    cached_file = None
    if "Use Cache" in yt_options:
        cached_file = find_in_cache(CACHE_FILE, url)

    if cached_file is None:
        # download YT video
        try:
            video_filename = download_yt_video(url, str(TEMP_PATH.absolute()))
            # print("Downloaded video as " + filename)
        except:
            raise Exception("Not a valid link.")
        # convert video to mp3
        try:
            video_filepath = str(TEMP_PATH.absolute() / video_filename)
            audio_filename = video_filename.rsplit(".", 1)[0] + ".mp3"
            audio_filepath = str(TEMP_PATH.absolute() / audio_filename)
            convert_to_mp3(video_filepath, audio_filepath)
            # delete video file
            remove_file(TEMP_PATH / video_filename)
            # write to cache file
            if "Use Cache" in yt_options:
                with open(CACHE_FILE, "a") as f:
                    f.write(f'{url}\t{audio_filepath}\n')
        except:
            raise Exception("Error converting video to mp3")

    audio_filepath = cached_file if cached_file is not None \
        else str(TEMP_PATH.absolute() / audio_filename)

    # generate subtitles
    outputs, files = audio_to_text(
        audio_filepath,
        model_language,
        model,
        language,
        OUTPUT_PATH)

    # save audio in DOWNLOAD_PATH if checkbox is set
    if "Save Audio" in yt_options:
        audio_filename = audio_filename if cached_file is None \
            else Path(cached_file).name
        dst = str(DOWNLOAD_PATH.absolute() / audio_filename)
        if os.path.exists(dst):
            os.remove(dst)
        copy2(audio_filepath, dst)

    #! does not work, because the audio filepath is used in the return statement
    # # delete tmp files
    # if "Use Cache" not in yt_options:
    #     # remove_file(TEMP_PATH / audio_filename)
    #     remove_file(audio_filepath)

    # return formatted solution
    return outputs + [files, gr.update(visible=True, value=audio_filepath)]


def save_recording(filepath):
    if filepath is not None:
        filename = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{filepath.rsplit(".", 1)[-1]}'
        move(filepath, RECORDING_PATH/filename)
        return gr.update(value=f"Saved recording under {str(RECORDING_PATH.absolute() / filename)}")
    else:
        return gr.update(value="Please record audio first.")


def mp3_to_subtitles(filepath, model_language, model, language):
    outputs, files = audio_to_text(filepath, model_language,
                                   model, language, OUTPUT_PATH)
    remove_file(filepath)
    return outputs + [files]


def video_to_subtitles(filepath, model_language, model, language):
    # convert video to mp3
    try:
        convert_to_mp3(filepath, str(TEMP_PATH.absolute()))
        # print("Converted video to mp3")
    except:
        raise Exception("Error converting video to mp3")
    # generate subtitles
    outputs, files = audio_to_text(
        filepath.rsplit(".", 1)[0] + ".mp3",
        model_language,
        model,
        language,
        OUTPUT_PATH)
    # delete files
    remove_file(filepath)
    remove_file(filepath.rsplit(".", 1)[0] + ".mp3")
    return outputs + [files]


def change_model_options(choice, model):
    if choice == "multilingual":
        return gr.update(choices=["tiny", "base", "small", "medium", "large"])
    elif choice == "english-only":
        return gr.update(
            choices=["tiny", "base", "small", "medium"],
            value=model if model != "large" else "medium")
    else:
        raise ValueError("Unexpected Error.")


def change_language_options(choice):
    if choice == "multilingual":
        return gr.update(
            choices=list(LANGUAGES.keys()),
            value=DEFAULT_LANGUAGE,
            interactive=True)
    elif choice == "english-only":
        return gr.update(
            choices=["english"],
            value="english",
            interactive=False)
    else:
        raise ValueError("Unexpected Error.")


def reset_value():
    return gr.update(value=None)


def reset_value_not_visible():
    return gr.update(value=None, visible=False)


def get_css():
    try:
        with open("style.css", "r") as f:
            return f.read()
    except:
        raise Exception("style.css could not be found.")
