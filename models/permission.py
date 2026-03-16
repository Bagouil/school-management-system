from database.db_config import get_db

class ResourceCategory:
    @staticmethod
    def get_all():
        """Get all resource categories"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT * FROM ResourceCategories 
        WHERE is_active = 1 
        ORDER BY sort_order
        """)
        
        columns = [column[0] for column in cursor.description]
        categories = []
        
        for row in cursor.fetchall():
            categories.append(dict(zip(columns, row)))
        
        cursor.close()
        return categories
    
    @staticmethod
    def get_with_resources():
        """Get all categories with their resources"""
        db = get_db()
        cursor = db.cursor()
        
        # First, get all categories
        cursor.execute("""
        SELECT category_id, category_name_ar, category_name_en, icon, sort_order
        FROM ResourceCategories 
        WHERE is_active = 1 
        ORDER BY sort_order
        """)
        
        categories = []
        for cat_row in cursor.fetchall():
            category = {
                'category_id': cat_row[0],
                'category_name_ar': cat_row[1],
                'category_name_en': cat_row[2],
                'icon': cat_row[3],
                'sort_order': cat_row[4],
                'resources': []
            }
            
            # Get resources for this category
            cursor.execute("""
            SELECT resource_id, resource_name_ar, resource_name_en, 
                   resource_code, description, route_pattern, icon, sort_order
            FROM Resources
            WHERE category_id = ? AND is_active = 1
            ORDER BY sort_order
            """, (cat_row[0],))
            
            for res_row in cursor.fetchall():
                category['resources'].append({
                    'resource_id': res_row[0],
                    'resource_name_ar': res_row[1],
                    'resource_name_en': res_row[2],
                    'resource_code': res_row[3],
                    'description': res_row[4],
                    'route_pattern': res_row[5],
                    'icon': res_row[6],
                    'sort_order': res_row[7]
                })
            
            categories.append(category)
        
        cursor.close()
        return categories


class Permission:
    @staticmethod
    def get_role_permissions(role):
        """Get all permissions for a specific role"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT p.*, r.resource_name_ar, r.resource_name_en, r.resource_code,
               rc.category_name_ar as category_name
        FROM Permissions p
        JOIN Resources r ON p.resource_id = r.resource_id
        JOIN ResourceCategories rc ON r.category_id = rc.category_id
        WHERE p.role = ?
        ORDER BY rc.sort_order, r.sort_order
        """, (role,))
        
        columns = [column[0] for column in cursor.description]
        permissions = []
        
        for row in cursor.fetchall():
            permissions.append(dict(zip(columns, row)))
        
        cursor.close()
        return permissions
    
    @staticmethod
    def get_user_permissions(user_id):
        """Get all permissions for a specific user (role-based + user-specific)"""
        db = get_db()
        cursor = db.cursor()
        
        # Get user's role
        cursor.execute("SELECT role FROM Users WHERE user_id = ?", (user_id,))
        user_role_result = cursor.fetchone()
        if not user_role_result:
            cursor.close()
            return {}
        
        user_role = user_role_result[0]
        
        # Get role-based permissions
        cursor.execute("""
        SELECT r.resource_id, r.resource_code, 
               p.can_access, p.can_create, p.can_edit, p.can_delete
        FROM Permissions p
        JOIN Resources r ON p.resource_id = r.resource_id
        WHERE p.role = ?
        """, (user_role,))
        
        role_perms = {}
        for row in cursor.fetchall():
            role_perms[row[1]] = {
                'resource_id': row[0],
                'can_access': row[2],
                'can_create': row[3],
                'can_edit': row[4],
                'can_delete': row[5]
            }
        
        # Get user-specific overrides
        cursor.execute("""
        SELECT r.resource_code, up.can_access, up.can_create, up.can_edit, up.can_delete
        FROM UserPermissions up
        JOIN Resources r ON up.resource_id = r.resource_id
        WHERE up.user_id = ? AND (up.expiry_date IS NULL OR up.expiry_date >= GETDATE())
        """, (user_id,))
        
        for row in cursor.fetchall():
            if row[0] in role_perms:
                if row[1] is not None:
                    role_perms[row[0]]['can_access'] = row[1]
                if row[2] is not None:
                    role_perms[row[0]]['can_create'] = row[2]
                if row[3] is not None:
                    role_perms[row[0]]['can_edit'] = row[3]
                if row[4] is not None:
                    role_perms[row[0]]['can_delete'] = row[4]
        
        cursor.close()
        return role_perms
    
    @staticmethod
    def check_permission(user_id, resource_code, action='access'):
        """Check if user has permission for a specific resource and action"""
        perms = Permission.get_user_permissions(user_id)
        
        if resource_code not in perms:
            return False
        
        if action == 'access':
            return perms[resource_code]['can_access']
        elif action == 'create':
            return perms[resource_code]['can_create']
        elif action == 'edit':
            return perms[resource_code]['can_edit']
        elif action == 'delete':
            return perms[resource_code]['can_delete']
        
        return False
    
    @staticmethod
    def update_role_permission(role, resource_id, can_access, can_create, can_edit, can_delete):
        """Update permission for a role"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if permission exists
        cursor.execute("SELECT permission_id FROM Permissions WHERE role = ? AND resource_id = ?", 
                      (role, resource_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
            UPDATE Permissions 
            SET can_access = ?, can_create = ?, can_edit = ?, can_delete = ?, updated_at = GETDATE()
            WHERE role = ? AND resource_id = ?
            """, (can_access, can_create, can_edit, can_delete, role, resource_id))
        else:
            cursor.execute("""
            INSERT INTO Permissions (role, resource_id, can_access, can_create, can_edit, can_delete)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (role, resource_id, can_access, can_create, can_edit, can_delete))
        
        db.commit()
        cursor.close()
        return True
    
    @staticmethod
    def update_user_permission(user_id, resource_id, can_access, can_create, can_edit, can_delete, granted_by, expiry_date=None):
        """Update user-specific permission"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if permission exists
        cursor.execute("SELECT user_permission_id FROM UserPermissions WHERE user_id = ? AND resource_id = ?", 
                      (user_id, resource_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
            UPDATE UserPermissions 
            SET can_access = ?, can_create = ?, can_edit = ?, can_delete = ?, 
                granted_by = ?, expiry_date = ?, granted_at = GETDATE()
            WHERE user_id = ? AND resource_id = ?
            """, (can_access, can_create, can_edit, can_delete, granted_by, expiry_date, user_id, resource_id))
        else:
            cursor.execute("""
            INSERT INTO UserPermissions (user_id, resource_id, can_access, can_create, can_edit, can_delete, granted_by, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, resource_id, can_access, can_create, can_edit, can_delete, granted_by, expiry_date))
        
        db.commit()
        cursor.close()
        return True
    
    @staticmethod
    def remove_user_permission(user_id, resource_id):
        """Remove user-specific permission"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM UserPermissions WHERE user_id = ? AND resource_id = ?", 
                      (user_id, resource_id))
        db.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0