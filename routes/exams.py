from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.exam import Exam, ExamType, ExamResults, GradeScale
from models.class_ import Class
from models.subject import Subject
from models.student import Student
from database.db_config import get_db
from datetime import datetime
from utils.permission_decorator import role_required

exams_bp = Blueprint('exams', __name__)

@exams_bp.route('/')
def list_exams():
    """List all exams"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get filter parameters
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')
    term = request.args.get('term')
    
    filters = {}
    if class_id:
        filters['class_id'] = class_id
    if subject_id:
        filters['subject_id'] = subject_id
    if term:
        filters['term'] = term
    
    exams = Exam.get_all(filters)
    
    # Get classes and subjects for filters
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT class_id, class_name_ar FROM Classes ORDER BY class_name_ar")
    classes = [{'class_id': row[0], 'class_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.execute("SELECT subject_id, subject_name_ar FROM Subjects WHERE is_active = 1 ORDER BY subject_name_ar")
    subjects = [{'subject_id': row[0], 'subject_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    
    return render_template('exams/list.html',
                         exams=exams,
                         classes=classes,
                         subjects=subjects,
                         selected_class=class_id,
                         selected_subject=subject_id,
                         selected_term=term)

@exams_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin', 'supervisor', 'teacher')
def create_exam():
    """Create new exam"""
    
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Get current academic year
            cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
            academic_year = cursor.fetchone()
            year_id = academic_year[0] if academic_year else 1
            
            data = {
                'exam_name_ar': request.form['exam_name_ar'],
                'exam_name_en': request.form.get('exam_name_en', ''),
                'exam_type_id': request.form['exam_type_id'],
                'subject_id': request.form['subject_id'],
                'class_id': request.form['class_id'],
                'academic_year_id': year_id,
                'term': request.form.get('term', 1),
                'exam_date': request.form['exam_date'],
                'start_time': request.form.get('start_time'),
                'end_time': request.form.get('end_time'),
                'duration_minutes': request.form.get('duration_minutes'),
                'total_marks': float(request.form['total_marks']),
                'passing_marks': float(request.form['passing_marks']),
                'description': request.form.get('description', ''),
                'created_by': session['user_id']
            }
            
            exam_id = Exam.create(data)
            flash('Exam created successfully', 'success')
            return redirect(url_for('exams.view_exam', exam_id=exam_id))
            
        except Exception as e:
            flash(f'Error creating exam: {str(e)}', 'danger')
            print(f"Error details: {e}")
    
    # Get form data
    exam_types = ExamType.get_all()
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT class_id, class_name_ar FROM Classes ORDER BY class_name_ar")
    classes = [{'class_id': row[0], 'class_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.execute("SELECT subject_id, subject_name_ar FROM Subjects WHERE is_active = 1 ORDER BY subject_name_ar")
    subjects = [{'subject_id': row[0], 'subject_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('exams/create.html',
                         exam_types=exam_types,
                         classes=classes,
                         subjects=subjects,
                         today=today)

@exams_bp.route('/<int:exam_id>')
def view_exam(exam_id):
    """View exam details"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    exam = Exam.get_by_id(exam_id)
    if not exam:
        flash('Exam not found', 'danger')
        return redirect(url_for('exams.list_exams'))
    
    # FIXED: Changed ExamResult to ExamResults
    results = ExamResults.get_exam_results(exam_id)
    
    # Calculate statistics
    total_students = len(results)
    passed = sum(1 for r in results if r['marks_obtained'] >= exam['passing_marks'])
    failed = total_students - passed
    average = sum(r['marks_obtained'] for r in results) / total_students if total_students > 0 else 0
    highest = max([r['marks_obtained'] for r in results]) if results else 0
    lowest = min([r['marks_obtained'] for r in results]) if results else 0
    
    stats = {
        'total': total_students,
        'passed': passed,
        'failed': failed,
        'pass_percentage': round((passed / total_students * 100) if total_students > 0 else 0, 1),
        'average': round(average, 2),
        'highest': highest,
        'lowest': lowest
    }
    
    return render_template('exams/view.html',
                         exam=exam,
                         results=results,
                         stats=stats)

@exams_bp.route('/<int:exam_id>/edit', methods=['GET', 'POST'])
@role_required('admin', 'supervisor')
def edit_exam(exam_id):
    """Edit exam"""
    
    exam = Exam.get_by_id(exam_id)
    if not exam:
        flash('Exam not found', 'danger')
        return redirect(url_for('exams.list_exams'))
    
    if request.method == 'POST':
        try:
            data = {
                'exam_name_ar': request.form['exam_name_ar'],
                'exam_name_en': request.form.get('exam_name_en', ''),
                'exam_type_id': request.form['exam_type_id'],
                'subject_id': request.form['subject_id'],
                'class_id': request.form['class_id'],
                'term': request.form.get('term', 1),
                'exam_date': request.form['exam_date'],
                'start_time': request.form.get('start_time'),
                'end_time': request.form.get('end_time'),
                'duration_minutes': request.form.get('duration_minutes'),
                'total_marks': float(request.form['total_marks']),
                'passing_marks': float(request.form['passing_marks']),
                'description': request.form.get('description', '')
            }
            
            if Exam.update(exam_id, data):
                flash('Exam updated successfully', 'success')
                return redirect(url_for('exams.view_exam', exam_id=exam_id))
            else:
                flash('No changes made', 'info')
                
        except Exception as e:
            flash(f'Error updating exam: {str(e)}', 'danger')
    
    exam_types = ExamType.get_all()
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT class_id, class_name_ar FROM Classes ORDER BY class_name_ar")
    classes = [{'class_id': row[0], 'class_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.execute("SELECT subject_id, subject_name_ar FROM Subjects WHERE is_active = 1 ORDER BY subject_name_ar")
    subjects = [{'subject_id': row[0], 'subject_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    
    return render_template('exams/edit.html',
                         exam=exam,
                         exam_types=exam_types,
                         classes=classes,
                         subjects=subjects)

@exams_bp.route('/<int:exam_id>/enter-results', methods=['GET', 'POST'])
@role_required('admin', 'supervisor', 'teacher')
def enter_results(exam_id):
    """Enter exam results"""

    
    exam = Exam.get_by_id(exam_id)
    if not exam:
        flash('Exam not found', 'danger')
        return redirect(url_for('exams.list_exams'))
    
    if request.method == 'POST':
        try:
            student_ids = request.form.getlist('student_id[]')
            marks = request.form.getlist('marks[]')
            remarks = request.form.getlist('remarks[]')
            
            count = 0
            for i, student_id in enumerate(student_ids):
                if marks[i] and marks[i].strip():
                    # FIXED: Changed ExamResult to ExamResults
                    data = {
                        'exam_id': exam_id,
                        'student_id': student_id,
                        'marks_obtained': float(marks[i]),
                        'total_marks': exam['total_marks'],
                        'remarks': remarks[i] if i < len(remarks) else '',
                        'entered_by': session['user_id']
                    }
                    ExamResults.create_or_update(data)
                    count += 1
            
            flash(f'Results saved for {count} students', 'success')
            return redirect(url_for('exams.view_exam', exam_id=exam_id))
            
        except Exception as e:
            flash(f'Error saving results: {str(e)}', 'danger')
    
    # Get students in this class
    students = Class.get_students(exam['class_id'])
    
    # FIXED: Changed ExamResult to ExamResults
    existing_results = ExamResults.get_exam_results(exam_id)
    results_dict = {r['student_id']: r for r in existing_results}
    
    return render_template('exams/enter_results.html',
                         exam=exam,
                         students=students,
                         results_dict=results_dict)

@exams_bp.route('/<int:exam_id>/publish', methods=['POST'])
@role_required('admin', 'supervisor')
def publish_exam(exam_id):
    """Publish exam results"""

    
    if Exam.publish(exam_id):
        flash('Exam results published successfully', 'success')
    else:
        flash('Error publishing results', 'danger')
    
    return redirect(url_for('exams.view_exam', exam_id=exam_id))

@exams_bp.route('/<int:exam_id>/delete', methods=['POST'])
@role_required('admin')
def delete_exam(exam_id):
    """Delete exam"""
       
    if Exam.delete(exam_id):
        flash('Exam deleted successfully', 'success')
    else:
        flash('Error deleting exam', 'danger')
    
    return redirect(url_for('exams.list_exams'))

@exams_bp.route('/student/<int:student_id>')
def student_results(student_id):
    """View student results"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    student = Student.get_by_id(student_id)
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('students.list_students'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    cursor.close()
    
    # FIXED: Changed ExamResult to ExamResults
    results = ExamResults.get_student_results(student_id, year_id)
    
    # Group results by subject
    subjects = {}
    for result in results:
        subject = result['subject_name_ar']
        if subject not in subjects:
            subjects[subject] = []
        subjects[subject].append(result)
    
    return render_template('exams/student_results.html',
                         student=student,
                         results=results,
                         subjects=subjects)

@exams_bp.route('/grade-scale')
def grade_scale():
    """View grade scale"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    scales = GradeScale.get_all()
    return render_template('exams/grade_scale.html', scales=scales)
@exams_bp.route('/<int:exam_id>/export')
def export_results(exam_id):
    """Export exam results to CSV"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    exam = Exam.get_by_id(exam_id)
    if not exam:
        flash('Exam not found', 'danger')
        return redirect(url_for('exams.list_exams'))
    
    results = ExamResults.get_exam_results(exam_id)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = [
        'الرقم الدراسي',
        'اسم الطالب',
        'الدرجة',
        'النسبة المئوية',
        'التقدير',
        'الملاحظات'
    ]
    writer.writerow(headers)
    
    # Write data
    for result in results:
        writer.writerow([
            result['student_number'],
            f"{result['first_name_ar']} {result['last_name_ar']}",
            result['marks_obtained'],
            f"{result.get('percentage', 0):.1f}%",
            result.get('grade_letter', ''),
            result.get('remarks', '')
        ])
    
    output.seek(0)
    
    # Generate filename
    from datetime import datetime
    filename = f"exam_{exam_id}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
@exams_bp.route('/<int:exam_id>/export-excel')
def export_results_excel(exam_id):
    """Export exam results to Excel"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        import pandas as pd
    except ImportError:
        flash('Please install pandas: pip install pandas openpyxl', 'danger')
        return redirect(url_for('exams.view_exam', exam_id=exam_id))
    
    exam = Exam.get_by_id(exam_id)
    if not exam:
        flash('Exam not found', 'danger')
        return redirect(url_for('exams.list_exams'))
    
    results = ExamResults.get_exam_results(exam_id)
    
    # Prepare data for DataFrame
    data = []
    for r in results:
        data.append({
            'الرقم الدراسي': r['student_number'],
            'اسم الطالب': f"{r['first_name_ar']} {r['last_name_ar']}",
            'الدرجة': r['marks_obtained'],
            'النسبة المئوية': f"{r.get('percentage', 0):.1f}%",
            'التقدير': r.get('grade_letter', ''),
            'الملاحظات': r.get('remarks', '')
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Exam Results', index=False)
        
        # Add exam info
        workbook = writer.book
        worksheet = writer.sheets['Exam Results']
        
        # Insert title
        worksheet.insert_rows(0)
        worksheet.cell(row=1, column=1, value=f"نتائج الامتحان: {exam['exam_name_ar']}")
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
    
    output.seek(0)
    
    filename = f"exam_{exam_id}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )