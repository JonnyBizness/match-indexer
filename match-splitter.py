import re
from moviepy.video.io.VideoFileClip import VideoFileClip

def parse_match_data(line):
    # Define the regex pattern to match the format
    match = re.match(r"(\d+:\d+:\d+) - (.+?) vs (.+?) \((\d+:\d+:\d+)\)", line)
    
    # If a match is found, extract and return the components
    if match:
        start_time = match.group(1)
        player1 = match.group(2)
        player2 = match.group(3)
        duration = match.group(4)
        return start_time, player1, player2, duration
    else:
        # If the line doesn't match the format, print or log an error
        print(f"Line format incorrect or does not match: {line}")
        return None

def convert_time_to_seconds(time_str):
    # Converts a time format (HH:MM:SS) to seconds
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds

def split_video(input_video_path, match_data_file):
    print('splitting video', input_video_path)
    print('splitting matches', match_data_file)
    # Load the video
    video = VideoFileClip(input_video_path)

    # Read the match data
    with open(match_data_file, 'r', encoding='utf-16') as f:
        lines = [line.strip() for line in f.readlines()]

    for i, line in enumerate(lines):
        print('match:', line)
        start_time, char1, char2, duration = parse_match_data(line)

        print('start_time:', start_time)
        print('char1:', char1)
        print('char2:', char2)
        print('duration:', duration)

        if start_time and duration:
            start_seconds = convert_time_to_seconds(start_time)
            duration_seconds = convert_time_to_seconds(duration)
            end_seconds = start_seconds + duration_seconds

            # Extract match clip
            match_clip = video.subclip(start_seconds, end_seconds)
            match_clip_filename = f"{char1}_vs_{char2}_match_{i + 1}.mp4"
            match_clip.write_videofile(match_clip_filename, codec="libx264")
            print(f"Saved match: {match_clip_filename}")

    video.close()

# Example usage
input_video_path = r"D:\Videos\Ranbats\2024-11-03 - Trim.mkv"  # Path to your input video file
match_data_file = 'output.txt'       # File with match data (the format you provided)
split_video(input_video_path, match_data_file)
