import unittest
from database import create_default_admin, verify_credentials, change_password, add_user, get_user_full, admin_force_change_password
import sqlite3

DB = 'secure.db'

class AuthTests(unittest.TestCase):
    def setUp(self):
        # Ensure a fresh default admin (delete any existing admin then recreate)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username=?", ('admin',))
        conn.commit()
        conn.close()
        create_default_admin()

    def tearDown(self):
        # cleanup test users if present
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        for u in ('test_user_1', 'test_user_2', 'tester', 'temp_user'):
            c.execute("DELETE FROM users WHERE username=?", (u,))
        conn.commit()
        conn.close()

    def test_default_admin_must_change(self):
        ok, is_admin, must_change = verify_credentials('admin', 'admin123')
        self.assertTrue(ok)
        self.assertTrue(is_admin)
        self.assertTrue(must_change)

        # change admin password
        changed = change_password('admin', 'admin123', 'admin_new_pass')
        self.assertTrue(changed)

        ok2, is_admin2, must_change2 = verify_credentials('admin', 'admin_new_pass')
        self.assertTrue(ok2)
        self.assertTrue(is_admin2)
        self.assertFalse(must_change2)

    def test_user_change_password_flow(self):
        add_user('test_user_1', cert=b'c', password='p1')
        ok, is_admin, must_change = verify_credentials('test_user_1', 'p1')
        self.assertTrue(ok)
        self.assertFalse(is_admin)

        # change password
        changed = change_password('test_user_1', 'p1', 'p2')
        self.assertTrue(changed)
        ok2, _, _ = verify_credentials('test_user_1', 'p2')
        self.assertTrue(ok2)
        ok_old, _, _ = verify_credentials('test_user_1', 'p1')
        self.assertFalse(ok_old)

    def test_admin_force_change_password(self):
        add_user('test_user_2', cert=b'c2', password='abc')
        ok, _, _ = verify_credentials('test_user_2', 'abc')
        self.assertTrue(ok)
        admin_force_change_password('test_user_2', 'newabc')
        ok2, _, _ = verify_credentials('test_user_2', 'newabc')
        self.assertTrue(ok2)

if __name__ == '__main__':
    unittest.main()
