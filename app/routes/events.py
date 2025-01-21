# app/routes/events.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app.models.event import Event
from app import db
import json
from datetime import datetime
import qrcode
from io import BytesIO
import os
from fpdf import FPDF

bp = Blueprint('events', __name__)

@bp.route('/')
def index():
    public_events = Event.query.filter_by(is_public=True).all()
    return render_template('index.html', events=public_events)


@bp.route('/dashboard')
@login_required
def dashboard():
    user_events = Event.query.filter_by(user_id=current_user.id).all()
    return render_template('events/dashboard.html', events=user_events)

@bp.route('/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        # Handling date and time input
        event_date_str = request.form['event_date']
        event_time_str = request.form['event_time']
        event_date = datetime.strptime(f"{event_date_str} {event_time_str}", '%Y-%m-%d %H:%M')
        
        event = Event(
            title=request.form['event_name'],
            description=request.form['event_description'],
            date=event_date,
            location=request.form['event_location'],
            theme=request.form['event_theme'],
            is_public=bool(request.form.get('is_public')),
            user_id=current_user.id,
            custom_fields=json.loads(request.form.get('custom_fields', '{}'))
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully')
        return redirect(url_for('events.dashboard'))
    
    return render_template('events/create.html')
@bp.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Ensure only the event owner can edit the event
    if event.user_id != current_user.id:
        flash('You do not have permission to edit this event')
        return redirect(url_for('events.index'))
    
    if request.method == 'POST':
        # Handle date and time input
        event_date_str = request.form['event_date']
        event_time_str = request.form['event_time']
        event_date = datetime.strptime(f"{event_date_str} {event_time_str}", '%Y-%m-%d %H:%M')
        
        event.title = request.form['event_name']
        event.description = request.form['event_description']
        event.date = event_date
        event.location = request.form['event_location']
        event.theme = request.form['event_theme']
        event.is_public = bool(request.form.get('is_public'))
        event.custom_fields = json.loads(request.form.get('custom_fields', '{}'))
        
        db.session.commit()
        flash('Event updated successfully')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    return render_template('events/edit.html', event=event)


@bp.route('/event/<int:event_id>/download')
@login_required
def download_event(event_id):
    event = Event.query.get_or_404(event_id)

    # Ensure the event belongs to the current user
    if event.user_id != current_user.id:
        flash('You do not have permission to download this event data.')
        return redirect(url_for('events.index'))

    try:
        # Define file name and path
        file_name = f'event_{event.id}_file.pdf'
        file_folder = os.path.join(current_app.root_path, 'static', 'files')

        # Ensure the folder exists
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)

        file_path = os.path.join(file_folder, file_name)

        # Check if the file exists, if not, create or save it
        if not os.path.exists(file_path):
            # Create PDF file with event details
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', size=12)

            # Event details in the PDF
            pdf.cell(200, 10, txt=f"Event: {event.title}", ln=True)
            pdf.cell(200, 10, txt=f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}", ln=True)
            pdf.cell(200, 10, txt=f"Location: {event.location}", ln=True)
            pdf.cell(200, 10, txt=f"Description: {event.description}", ln=True)
            pdf.cell(200, 10, txt=f"Theme: {event.theme}", ln=True)
            pdf.cell(200, 10, txt=f"Public Event: {'Yes' if event.is_public else 'No'}", ln=True)

            # Save the generated PDF
            pdf.output(file_path)

        # Serve the file for download
        return send_file(file_path, as_attachment=True, download_name=file_name)

    except Exception as e:
        flash(f'Error downloading the event file: {e}')
        return redirect(url_for('events.view_event', event_id=event.id))
    
@bp.route('/event/<int:event_id>')
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not event.is_public and (not current_user.is_authenticated or event.user_id != current_user.id):
        flash('You do not have permission to view this event')
        return redirect(url_for('events.index'))
    return render_template('events/view.html', event=event)

@bp.route('/event/<int:event_id>/share')
def share_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not event.is_public and (not current_user.is_authenticated or event.user_id != current_user.id):
        flash('You do not have permission to share this event')
        return redirect(url_for('events.index'))
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    share_url = url_for('events.view_event', event_id=event.id, _external=True)
    qr.add_data(share_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')
