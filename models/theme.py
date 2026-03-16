from database.db_config import get_db

class Theme:
    @staticmethod
    def get_all():
        """Get all active themes"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT * FROM Themes WHERE is_active = 1 ORDER BY theme_id")
            
            # Check if we have results
            if cursor.description is None:
                return []
            
            columns = [column[0] for column in cursor.description]
            themes = []
            
            for row in cursor.fetchall():
                themes.append(dict(zip(columns, row)))
            
            return themes
        except Exception as e:
            print(f"Error in get_all themes: {e}")
            return []
        finally:
            cursor.close()
    
    @staticmethod
    def get_by_id(theme_id):
        """Get theme by ID"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT * FROM Themes WHERE theme_id = ?", (theme_id,))
            
            if cursor.description is None:
                return None
            
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in get_by_id themes: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_default():
        """Get default theme"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT * FROM Themes WHERE is_default = 1")
            
            if cursor.description is None:
                # Return hardcoded default if no theme in database
                return {
                    'theme_id': 1,
                    'theme_name_ar': 'أرجواني',
                    'theme_name_en': 'Purple',
                    'primary_color': '#875A7B',
                    'secondary_color': '#6a4b5f',
                    'accent_color': '#9B6B8C',
                    'success_color': '#28A745',
                    'danger_color': '#DC3545',
                    'warning_color': '#FFC107',
                    'info_color': '#17A2B8',
                    'sidebar_bg': None,
                    'header_bg': None,
                    'is_default': 1
                }
            
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            
            # Return hardcoded default if no default theme found
            return {
                'theme_id': 1,
                'theme_name_ar': 'أرجواني',
                'theme_name_en': 'Purple',
                'primary_color': '#875A7B',
                'secondary_color': '#6a4b5f',
                'accent_color': '#9B6B8C',
                'success_color': '#28A745',
                'danger_color': '#DC3545',
                'warning_color': '#FFC107',
                'info_color': '#17A2B8',
                'sidebar_bg': None,
                'header_bg': None,
                'is_default': 1
            }
        except Exception as e:
            print(f"Error in get_default themes: {e}")
            # Return hardcoded default on error
            return {
                'theme_id': 1,
                'theme_name_ar': 'أرجواني',
                'theme_name_en': 'Purple',
                'primary_color': '#875A7B',
                'secondary_color': '#6a4b5f',
                'accent_color': '#9B6B8C',
                'success_color': '#28A745',
                'danger_color': '#DC3545',
                'warning_color': '#FFC107',
                'info_color': '#17A2B8',
                'sidebar_bg': None,
                'header_bg': None,
                'is_default': 1
            }
        finally:
            cursor.close()
    
    @staticmethod
    def set_user_theme(user_id, theme_id):
        """Set theme for a user"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("UPDATE Users SET theme_id = ? WHERE user_id = ?", (theme_id, user_id))
            db.commit()
            return True
        except Exception as e:
            print(f"Error in set_user_theme: {e}")
            db.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_user_theme(user_id):
        """Get theme for a user"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("""
            SELECT t.* FROM Themes t
            JOIN Users u ON u.theme_id = t.theme_id
            WHERE u.user_id = ?
            """, (user_id,))
            
            if cursor.description and cursor.description is not None:
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()
                
                if row:
                    return dict(zip(columns, row))
            
            # Return default theme if user has no theme set
            return Theme.get_default()
            
        except Exception as e:
            print(f"Error in get_user_theme: {e}")
            return Theme.get_default()
        finally:
            cursor.close()