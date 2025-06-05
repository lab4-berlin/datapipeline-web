import os
import shutil
import re
import yaml

CONTENT_DIR = "content"
OUTPUT_DIR = "html"
SITE_TITLE = "Data PipeLine"
TEMPLATES_DIR = "templates"

def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_file_content(file_path, default=""):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return default

def find_first_file_with_extensions(base_path, extensions):
    for ext in extensions:
        if os.path.exists(f"{base_path}.{ext}"):
            return f"{base_path}.{ext}"
    return None

# --- HTML Generation Functions ---

def generate_video_html(video_data):
    """Generates HTML for a single video page using a template."""
    template_path = os.path.join(TEMPLATES_DIR, "video_template.html")
    if not os.path.exists(template_path):
        print(f"Error: Video template not found at {template_path}")
        return ""
        
    template_content = read_file_content(template_path)

    video_id = video_data.get('youtube_video_id')
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        youtube_player_html = f'<div class="video-container"><iframe width="560" height="315" src="{embed_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'
    else:
        youtube_player_html = '<p>YouTube video ID not provided or invalid.</p>'
    
    description_section_html = ""
    if video_data.get('description'):
        formatted_description = video_data['description'].strip().replace('\n', '<br>\n')
        description_section_html = f"""
        <h3>Description</h3>
        <div class="video-description">
            <p>{formatted_description}</p>
        </div>"""

    audio_section_html = ""
    if video_data.get("audio_path_relative"):
        audio_section_html = f'<h3>Audio</h3>\n<audio controls src="{video_data["audio_path_relative"]}"></audio><p><a href="{video_data["audio_path_relative"]}" download>Download MP3</a></p>'
    else:
        audio_section_html = '<h3>Audio</h3>\n<p>No audio file provided.</p>'
        
    transcript_content = video_data.get('transcript', 'No transcript provided.').strip()
    transcript_content_escaped = transcript_content.replace("<", "&lt;").replace(">", "&gt;")
    transcript_section_html = f"""
    <h3>Transcript</h3>
    <div class="transcript">
        <pre>{transcript_content_escaped}</pre>
    </div>"""

    html_content = template_content.replace("{PAGE_TITLE}", f"{video_data['title']} - {SITE_TITLE}")
    html_content = html_content.replace("{SITE_TITLE}", SITE_TITLE)
    html_content = html_content.replace("{VIDEO_TITLE}", video_data['title'])
    html_content = html_content.replace("{YOUTUBE_PLAYER_HTML}", youtube_player_html)
    html_content = html_content.replace("{DESCRIPTION_SECTION_HTML}", description_section_html)
    html_content = html_content.replace("{AUDIO_SECTION_HTML}", audio_section_html)
    html_content = html_content.replace("{TRANSCRIPT_SECTION_HTML}", transcript_section_html)
    
    return html_content

def generate_index_html(videos_data):
    """Generates the main index.html page using a template, with videos grouped by category."""
    template_path = os.path.join(TEMPLATES_DIR, "index_template.html")
    if not os.path.exists(template_path):
        print(f"Error: Index template not found at {template_path}")
        return ""
        
    template_content = read_file_content(template_path)
    
    videos_by_category = {}
    for video in videos_data:
        category = video.get('category', 'Uncategorized')
        if category not in videos_by_category:
            videos_by_category[category] = []
        videos_by_category[category].append(video)

    all_categories_html = ""
    sorted_category_names = sorted(videos_by_category.keys())

    if not videos_by_category:
        all_categories_html = "<p>No videos found. Add content to the 'content' folder.</p>"
    else:
        for category_name in sorted_category_names:
            display_category_name = category_name.replace("_", " ").title()
            
            # Start category block
            all_categories_html += '<div class="category-block">\n'
            # Category header with toggle icon
            all_categories_html += f'    <div class="category-header">\n        <h2>{display_category_name}</h2>\n        <span class="toggle-icon">&gt;</span>\n    </div>\n'
            # Category content (collapsible part)
            all_categories_html += '    <div class="category-content">\n'
            
            video_list_items = ""
            for video in sorted(videos_by_category[category_name], key=lambda x: x['slug']):
                thumbnail_html = f'<img src="{video["thumbnail_path_relative"]}" alt="{video["title"]} Thumbnail" class="thumbnail">' if video.get("thumbnail_path_relative") else '<div class="thumbnail-placeholder">No Thumbnail</div>'
                video_list_items += f"""
                <li class="video-item">
                    <a href="{video['html_filename']}">
                        {thumbnail_html}
                        <h3>{video['title']}</h3>
                    </a>
                </li>"""
            
            list_content_for_f_string = video_list_items if video_list_items else f"<p>No videos found in {display_category_name}.</p>"
            all_categories_html += f'        <ul class="video-list">\n{list_content_for_f_string}\n        </ul>\n'
            
            all_categories_html += '    </div>\n' # End category-content
            all_categories_html += '</div>\n' # End category-block

    html_content = template_content.replace("{SITE_TITLE}", SITE_TITLE)
    html_content = html_content.replace("{VIDEO_LIST_HTML}", all_categories_html)
    
    return html_content

# --- Main Script Logic ---

def main():
    print("Starting website generation...")

    create_dir(OUTPUT_DIR)
    assets_dir_abs = os.path.join(OUTPUT_DIR, "assets")
    create_dir(assets_dir_abs)

    all_videos_data = []

    if not os.path.exists(CONTENT_DIR) or not os.listdir(CONTENT_DIR):
        print(f"Warning: Content directory '{CONTENT_DIR}' is empty or does not exist.")
    else:
        for video_slug in os.listdir(CONTENT_DIR):
            video_content_path = os.path.join(CONTENT_DIR, video_slug)
            if os.path.isdir(video_content_path):
                print(f"Processing video: {video_slug}...")
                video_data = {'slug': video_slug}
                
                metadata_path = os.path.join(video_content_path, "metadata.yaml")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = yaml.safe_load(f)
                        video_data['title'] = metadata.get('title', video_slug.replace("_", " ").title())
                        video_data['youtube_video_id'] = metadata.get('youtube_video_id')
                        video_data['description'] = metadata.get('description', '')
                        video_data['category'] = metadata.get('category', 'Uncategorized') # Read category here
                        if not video_data['youtube_video_id']:
                             print(f"  Warning: 'youtube_video_id' not found or empty in metadata.yaml for {video_slug}.")
                    except yaml.YAMLError as e:
                        print(f"  Error parsing metadata.yaml for {video_slug}: {e}")
                        video_data['title'] = video_slug.replace("_", " ").title()
                        video_data['youtube_video_id'] = None
                        video_data['description'] = ''
                        video_data['category'] = 'Uncategorized' # Default category on error
                else:
                    print(f"  Warning: metadata.yaml not found for {video_slug}. Using defaults.")
                    video_data['title'] = video_slug.replace("_", " ").title()
                    video_data['youtube_video_id'] = None
                    video_data['description'] = ''
                    video_data['category'] = 'Uncategorized' # Default category if no metadata file

                video_data['transcript'] = read_file_content(os.path.join(video_content_path, "transcript.txt"), default='').strip()

                video_assets_dir_abs = os.path.join(assets_dir_abs, video_slug)
                create_dir(video_assets_dir_abs)

                audio_src_path = find_first_file_with_extensions(os.path.join(video_content_path, "audio"), ["mp3"])
                if audio_src_path:
                    audio_filename = os.path.basename(audio_src_path)
                    audio_dest_path_abs = os.path.join(video_assets_dir_abs, audio_filename)
                    shutil.copy2(audio_src_path, audio_dest_path_abs)
                    video_data['audio_path_relative'] = os.path.join("assets", video_slug, audio_filename).replace("\\", "/")
                else:
                    print(f"  Info: No audio file found for {video_slug}.")

                thumbnail_src_path = find_first_file_with_extensions(os.path.join(video_content_path, "thumbnail"), ["jpg", "jpeg", "png"])
                if thumbnail_src_path:
                    thumbnail_filename = os.path.basename(thumbnail_src_path)
                    thumbnail_dest_path_abs = os.path.join(video_assets_dir_abs, thumbnail_filename)
                    shutil.copy2(thumbnail_src_path, thumbnail_dest_path_abs)
                    video_data['thumbnail_path_relative'] = os.path.join("assets", video_slug, thumbnail_filename).replace("\\", "/")
                else:
                    print(f"  Info: No thumbnail found for {video_slug}.")

                video_html_content = generate_video_html(video_data)
                if video_html_content:
                    video_data['html_filename'] = f"{video_slug}.html"
                    with open(os.path.join(OUTPUT_DIR, video_data['html_filename']), 'w', encoding='utf-8') as f:
                        f.write(video_html_content)
                    all_videos_data.append(video_data)

    index_html_content = generate_index_html(all_videos_data)
    if index_html_content:
        with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
            f.write(index_html_content)
        print(f"Generated index.html")

    source_css_path = os.path.join(TEMPLATES_DIR, "style.css")
    dest_css_path = os.path.join(OUTPUT_DIR, "style.css")
    if os.path.exists(source_css_path):
        shutil.copy2(source_css_path, dest_css_path)
        print(f"Copied style.css")
    else:
        print(f"Warning: style.css not found at {source_css_path}")

    print(f"Website generation complete! Files are in '{OUTPUT_DIR}' directory.")

def generate_video_list_page(videos):
    video_list_items = ""
    if videos:
        for video in videos:
            # Make sure the path is relative to the HTML file's location
            relative_video_path = os.path.join('..', video['path'])
            video_list_items += f'<li><a href="{relative_video_path}" target="_blank">{video["title"]}</a></li>\n'
    
    # Pre-calculate the content for the list
    if video_list_items:
        list_content = video_list_items
    else:
        list_content = "<p>No videos found. Add content to the 'content' folder.</p>"

    video_list_html = f'<ul class="video-list">\n{list_content}\n</ul>'
    
    # Ensure the 'html' directory exists
    os.makedirs("html", exist_ok=True)
    
    with open(os.path.join("html", "video_list.html"), "w") as f:
        f.write(video_list_html)
    print("Generated video_list.html")

if __name__ == "__main__":
    main()