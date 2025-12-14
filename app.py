# PATH: image-merger-app/app.py
from flask import Flask, request, send_file, render_template, url_for, jsonify, send_from_directory
from PIL import Image
from tinydb import TinyDB, Query
import io
import os
import datetime 
import re 

# --- CONFIGURATION ---
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
DB_PATH = os.path.join(app.root_path, 'settings.json')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 

db = TinyDB(DB_PATH)
Settings = Query()

# 💡 ADMIN PANEL CONFIGURATION - CHANGE THESE VARIABLES ONLY 💡
ADMIN_ROUTE_NAME = 'alibaba' 
ADMIN_TEMPLATE_NAME = 'alibaba.html'
ADMIN_SECONDARY_PASSWORD_KEY = 'my_logo_secondary_password' 

# Super Admin 
SUPER_ADMIN_ROUTE_NAME = 'daddy'
SUPER_ADMIN_TEMPLATE_NAME = 'daddy.html' 
# ------------------------------------------------------------------

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set initial default settings if the database is empty
if not db.get(Settings.type == 'global'):
    db.insert({
        'type': 'global',
        'event_name': 'Sample Event Name',
        'venue': 'Virtual / Event Hall',
        'date_time': 'January 1, 2026, 10:00 AM',
        'description': 'Upload a photo and frame it with the slider!',
        'event_logo_filename': '', 
        'my_logo_filename': '',    
        'template_filename': '',
        'background_filename': '', 
        'show_sponsors': False, 
        'sponsor_logo_filename': '',
        'admin_password': '123',                    
        'super_admin_password': 'daddy123',          
        ADMIN_SECONDARY_PASSWORD_KEY: 'ImInZu'       
    })

# Helper functions for file validation
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_template(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'png'

# --- ROUTE TO SERVE UPLOADED FILES ---
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- FRONT-END ROUTES ---

@app.route(f'/{ADMIN_ROUTE_NAME}')
def admin_page():
    return render_template(ADMIN_TEMPLATE_NAME)

@app.route(f'/{SUPER_ADMIN_ROUTE_NAME}') 
def super_admin_page():
    return send_from_directory(app.root_path, SUPER_ADMIN_TEMPLATE_NAME) 

@app.route('/')
def home():
    return render_template('index.html') 

# --- ADMIN API ROUTES ---

@app.route('/check_secondary_password', methods=['POST'])
def check_secondary_password():
    """Securely checks the secondary password before allowing logo update."""
    submitted_password = request.form.get('secondary_password')
    settings = db.get(Settings.type == 'global')
    
    if not settings:
        return jsonify({'success': False, 'message': 'Configuration not found.'}), 404
        
    correct_password = settings.get(ADMIN_SECONDARY_PASSWORD_KEY, 'ImInZu') 
    
    if submitted_password == correct_password:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'message': 'Secondary password incorrect.'}), 401

@app.route('/admin_login_check', methods=['POST'])
def admin_login_check():
    """Server-side check for Coordinator Admin login."""
    submitted_password = request.form.get('password')
    settings = db.get(Settings.type == 'global')
    
    if not settings:
        return jsonify({'success': False, 'message': 'Configuration not found.'}), 404
        
    correct_password = settings.get('admin_password', '123') 
    
    if submitted_password == correct_password:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid password.'}), 401

@app.route('/super_admin_login_check', methods=['POST'])
def super_admin_login_check():
    """Server-side check for Super Admin login."""
    submitted_password = request.form.get('password')
    settings = db.get(Settings.type == 'global')
    
    if not settings:
        return jsonify({'success': False, 'message': 'Configuration not found.'}), 404
        
    correct_password = settings.get('super_admin_password', 'daddy123') 
    
    if submitted_password == correct_password:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid password.'}), 401

@app.route('/change_admin_password', methods=['POST'])
def change_admin_password():
    """Handles Coordinator Admin password change request (by Coordinator)."""
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    settings = db.get(Settings.type == 'global')
    if not settings:
        return jsonify({'success': False, 'message': 'Configuration not found.'}), 404

    current_password = settings.get('admin_password', '123')
    
    if old_password != current_password:
        return jsonify({'success': False, 'message': 'Current password incorrect.'}), 401

    if not new_password or len(new_password) < 3:
        return jsonify({'success': False, 'message': 'New password must be at least 3 characters long.'}), 400

    settings['admin_password'] = new_password
    db.update(settings, Settings.type == 'global')
    
    return jsonify({'success': True, 'message': 'Coordinator password changed successfully!'}), 200

@app.route('/super_admin_password_reset', methods=['POST'])
def super_admin_password_reset():
    """Handles resetting ALL passwords (by Super Admin)."""
    
    new_admin_pass = request.form.get('new_admin_pass')
    new_secondary_pass = request.form.get('new_secondary_pass')

    settings = db.get(Settings.type == 'global')
    if not settings:
        return jsonify({'success': False, 'message': 'Configuration not found.'}), 404
        
    if not new_admin_pass or len(new_admin_pass) < 3:
        return jsonify({'success': False, 'message': 'New Coordinator Admin password must be at least 3 characters long.'}), 400

    if not new_secondary_pass or len(new_secondary_pass) < 3:
        return jsonify({'success': False, 'message': 'New Secondary Logo password must be at least 3 characters long.'}), 400

    settings['admin_password'] = new_admin_pass
    settings[ADMIN_SECONDARY_PASSWORD_KEY] = new_secondary_pass
    db.update(settings, Settings.type == 'global')
    
    return jsonify({'success': True, 'message': 'Admin and Secondary passwords updated successfully!'}), 200


@app.route('/get_settings') 
def get_settings():
    settings = db.get(Settings.type == 'global')
    if not settings:
        return jsonify({'message': 'Configuration not found.'}), 404

    data = {
        'event_name': settings['event_name'],
        'venue': settings['venue'],
        'date_time': settings['date_time'],
        'description': settings['description'],
        'event_logo_filename': settings.get('event_logo_filename', ''),
        'my_logo_filename': settings.get('my_logo_filename', ''),
        'template_filename': settings.get('template_filename', ''),
        'background_filename': settings.get('background_filename', ''),
        'show_sponsors': settings.get('show_sponsors', False),
        'sponsor_logo_filename': settings.get('sponsor_logo_filename', ''),
    }
    return jsonify(data)

# --- ADMIN ROUTES (File Management) ---

@app.route('/update_settings', methods=['POST']) 
def update_settings():
    settings = db.get(Settings.type == 'global')
    if not settings:
        return jsonify({'message': 'Configuration not found.'}), 404
    
    # 1. Handle TEXT and BOOLEAN updates
    settings['event_name'] = request.form.get('event_name', settings['event_name'])
    settings['venue'] = request.form.get('venue', settings['venue'])
    settings['date_time'] = request.form.get('date_time', settings['date_time'])
    settings['description'] = request.form.get('description', settings['description'])
    
    settings['show_sponsors'] = 'show_sponsors' in request.form
    
    # 2. Handle FILE uploads
    def handle_file_upload(file_key, setting_key_prefix, allowed_func, settings):
        if file_key in request.files:
            file = request.files[file_key]
            
            if file.filename != '':
                if allowed_func(file.filename):
                    
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    
                    if setting_key_prefix == 'template':
                        constant_filename = f"template.png"
                    elif setting_key_prefix == 'event_logo':
                        constant_filename = f"event_logo.{ext}" 
                    elif setting_key_prefix == 'my_logo':
                        constant_filename = f"my_logo.{ext}"    
                    elif setting_key_prefix == 'background':
                        constant_filename = f"website_background.{ext}" 
                    elif setting_key_prefix == 'sponsor_logo':
                        constant_filename = f"sponsor_logo.{ext}" 
                    else:
                        return False, "Invalid file key prefix."

                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], constant_filename)
                    old_filename_key = f'{setting_key_prefix}_filename'
                    
                    old_filename = settings.get(old_filename_key)
                    if old_filename and old_filename.startswith(setting_key_prefix):
                         old_filepath_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                         if os.path.exists(old_filepath_to_delete):
                              try:
                                  os.remove(old_filepath_to_delete)
                              except OSError as e:
                                  pass
                    
                    file.save(filepath)
                    settings[old_filename_key] = constant_filename 
                    
                    return True, f"Updated {setting_key_prefix}."
                else:
                    return False, f"Invalid file type for {setting_key_prefix}."
        
        return True, ""

    success, msg = handle_file_upload('event_logo', 'event_logo', allowed_file, settings)
    if not success: return jsonify({'message': msg}), 400
    
    success, msg = handle_file_upload('my_logo', 'my_logo', allowed_file, settings)
    if not success: return jsonify({'message': msg}), 400

    success, msg = handle_file_upload('template_file', 'template', allowed_template, settings)
    if not success: return jsonify({'message': msg}), 400
    
    success, msg = handle_file_upload('website_background', 'background', allowed_file, settings)
    if not success: return jsonify({'message': msg}), 400
    
    success, msg = handle_file_upload('sponsor_logo_file', 'sponsor_logo', allowed_file, settings)
    if not success: return jsonify({'message': msg}), 400
    
    if not settings.get('template_filename') and (not request.files.get('template_file') or request.files.get('template_file').filename == ''):
        return jsonify({'message': 'Template PNG file is required for initial setup.'}), 400

    db.update(settings, Settings.type == 'global')

    return jsonify({'message': 'Settings and files updated successfully!'}), 200


# --- IMAGE PROCESSING ROUTE (Unchanged) ---
@app.route('/merge_images', methods=['POST'])
def merge_and_download():
    settings = db.get(Settings.type == 'global')
    template_filename = settings.get('template_filename')
    event_name = settings.get('event_name', 'EventBanner') 

    if not template_filename:
        return 'Template file not specified. Please upload it via the Admin Panel.', 500

    TEMPLATE_PATH = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)
    
    if not os.path.exists(TEMPLATE_PATH):
        return 'Template file not found at expected location. Please re-upload.', 500

    uploaded_file = request.files.get('image_upload')
    
    try:
        scale = float(request.form.get('scale', 1.0))
        x_offset_px = int(request.form.get('x_offset', 0))
        y_offset_px = int(request.form.get('y_offset', 0))
    except ValueError:
        return 'Invalid transformation data received (scale/offset not numbers).', 400

    if not uploaded_file or uploaded_file.filename == '':
        return 'No selected file', 400

    try:
        backside_img = Image.open(uploaded_file.stream).convert("RGB")
        template_img = Image.open(TEMPLATE_PATH) 
        
        TARGET_SIZE = 800
        PREVIEW_WIDTH = 600
        
        min_required_dim = int(TARGET_SIZE * scale)
        
        width, height = backside_img.size
        
        if width < height:
            new_width = min_required_dim
            new_height = int(height * (new_width / width))
        else:
            new_height = min_required_dim
            new_width = int(width * (new_height / height))

        backside_img_resized = backside_img.resize((new_width, new_height))
        
        PIXELS_PER_SCREEN_UNIT = new_width / PREVIEW_WIDTH 

        image_offset_x = x_offset_px * PIXELS_PER_SCREEN_UNIT
        image_offset_y = y_offset_px * PIXELS_PER_SCREEN_UNIT
        
        center_x = new_width / 2
        center_y = new_height / 2
        
        crop_x1 = center_x - (TARGET_SIZE / 2) - image_offset_x
        crop_y1 = center_y - (TARGET_SIZE / 2) - image_offset_y
        crop_x2 = center_x + (TARGET_SIZE / 2) - image_offset_x
        crop_y2 = center_y + (TARGET_SIZE / 2) - image_offset_y
        
        cropped_backside = backside_img_resized.crop((int(crop_x1), int(crop_y1), int(crop_x2), int(crop_y2)))

        template_img = template_img.resize((TARGET_SIZE, TARGET_SIZE)).convert("RGBA")
        cropped_backside = cropped_backside.resize((TARGET_SIZE, TARGET_SIZE)).convert("RGBA")
        
        merged_img = Image.alpha_composite(cropped_backside, template_img)
        
        white_background = Image.new('RGB', (TARGET_SIZE, TARGET_SIZE), 'white')
        white_background.paste(merged_img, (0, 0), merged_img)
        
        current_time_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        cleaned_event_name = re.sub(r'[^a-zA-Z0-9\s]+', '', event_name).strip()
        cleaned_event_name = cleaned_event_name.replace(' ', '_')
        
        if not cleaned_event_name:
            cleaned_event_name = "EventBanner"
        
        download_filename = f"{cleaned_event_name}-{current_time_str}-Techtical.jpg"
        
        img_io = io.BytesIO()
        white_background.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=download_filename 
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        return f'Processing Error: {e}', 500

if __name__ == '__main__':
    app.run(debug=True)