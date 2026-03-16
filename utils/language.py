class Language:
    def __init__(self, language='ar'):
        self.language = language
        self.translations = self.load_translations()
    
    def load_translations(self):
        """Load translations dictionary"""
        return {
            'dashboard': {'ar': 'لوحة التحكم', 'en': 'Dashboard'},
            'students': {'ar': 'الطلاب', 'en': 'Students'},
            'teachers': {'ar': 'المعلمين', 'en': 'Teachers'},
            'classes': {'ar': 'الفصول', 'en': 'Classes'},
            'attendance': {'ar': 'الحضور', 'en': 'Attendance'},
            'exams': {'ar': 'الامتحانات', 'en': 'Exams'},
            'fees': {'ar': 'الرسوم', 'en': 'Fees'},
            'reports': {'ar': 'التقارير', 'en': 'Reports'},
            'settings': {'ar': 'الإعدادات', 'en': 'Settings'},
            'welcome': {'ar': 'مرحباً', 'en': 'Welcome'},
            'login': {'ar': 'تسجيل الدخول', 'en': 'Login'},
            'logout': {'ar': 'تسجيل الخروج', 'en': 'Logout'},
            'register': {'ar': 'تسجيل جديد', 'en': 'Register'},
            'save': {'ar': 'حفظ', 'en': 'Save'},
            'cancel': {'ar': 'إلغاء', 'en': 'Cancel'},
            'delete': {'ar': 'حذف', 'en': 'Delete'},
            'edit': {'ar': 'تعديل', 'en': 'Edit'},
            'search': {'ar': 'بحث', 'en': 'Search'},
            'actions': {'ar': 'الإجراءات', 'en': 'Actions'},
            'status': {'ar': 'الحالة', 'en': 'Status'},
            'active': {'ar': 'نشط', 'en': 'Active'},
            'inactive': {'ar': 'غير نشط', 'en': 'Inactive'},
            'student_name': {'ar': 'اسم الطالب', 'en': 'Student Name'},
            'teacher_name': {'ar': 'اسم المعلم', 'en': 'Teacher Name'},
            'class_name': {'ar': 'اسم الفصل', 'en': 'Class Name'},
            'subject': {'ar': 'المادة', 'en': 'Subject'},
            'date': {'ar': 'التاريخ', 'en': 'Date'},
            'amount': {'ar': 'المبلغ', 'en': 'Amount'},
            'payment': {'ar': 'الدفع', 'en': 'Payment'},
            'receipt': {'ar': 'إيصال', 'en': 'Receipt'},
            'total': {'ar': 'الإجمالي', 'en': 'Total'},
            'print': {'ar': 'طباعة', 'en': 'Print'},
            'export': {'ar': 'تصدير', 'en': 'Export'},
            'backup': {'ar': 'نسخ احتياطي', 'en': 'Backup'},
            'restore': {'ar': 'استعادة', 'en': 'Restore'},
            'profile': {'ar': 'الملف الشخصي', 'en': 'Profile'},
        }
    
    def get(self, key):
        """Get translation for key in current language"""
        if key in self.translations:
            return self.translations[key].get(self.language, key)
        return key
    
    def get_direction(self):
        """Get text direction based on language"""
        return 'rtl' if self.language == 'ar' else 'ltr'