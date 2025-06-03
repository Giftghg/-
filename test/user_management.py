from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QGridLayout, QComboBox)
from PyQt6.QtCore import Qt
import sqlite3
import hashlib
from enum import Enum, auto

class UserRole(Enum):
    GENERAL_MANAGER = "总经理"
    WAREHOUSE_MANAGER = "仓库总监"
    SALES_MANAGER = "销售总监"
    PRODUCT_MANAGER = "商品开发总监"

class Permission(Enum):
    MANAGE_USERS = auto()      # 用户管理权限
    MANAGE_INVENTORY = auto()  # 库存管理权限
    MANAGE_SUPPLIERS = auto()  # 供应商管理权限
    MANAGE_CUSTOMERS = auto()  # 客户管理权限
    MANAGE_PRODUCTS = auto()   # 商品管理权限
    VIEW_REPORTS = auto()      # 查看报表权限
    ALL = auto()              # 所有权限

# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.GENERAL_MANAGER: [Permission.ALL],
    UserRole.WAREHOUSE_MANAGER: [Permission.MANAGE_INVENTORY, Permission.MANAGE_SUPPLIERS],
    UserRole.SALES_MANAGER: [Permission.MANAGE_CUSTOMERS, Permission.VIEW_REPORTS],
    UserRole.PRODUCT_MANAGER: [Permission.MANAGE_PRODUCTS]
}

def init_user_database(db_path):
    """初始化用户数据库"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 创建用户表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 检查是否需要创建默认管理员账户
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            # 创建默认管理员账户
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, ("admin", password_hash, UserRole.GENERAL_MANAGER.value))
            
        conn.commit()
        cur.close()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"数据库初始化失败：{str(e)}")
        raise

class LoginDialog(QDialog):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.user_role = None
        self.username = None  # 添加用户名属性
        self.setWindowTitle("系统登录")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 使用网格布局来对齐标签和输入框
        form_layout = QGridLayout()
        
        # 用户名输入
        username_label = QLabel("用户名:")
        username_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)
        
        # 密码输入
        password_label = QLabel("密码:")
        password_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_input, 1, 1)
        
        # 按钮
        button_layout = QHBoxLayout()
        login_button = QPushButton("登录")
        login_button.setDefault(True)
        cancel_button = QPushButton("取消")
        button_layout.addWidget(login_button)
        button_layout.addWidget(cancel_button)
        
        # 添加所有布局
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # 连接信号
        login_button.clicked.connect(self.login)
        cancel_button.clicked.connect(self.reject)
        
        # 设置初始焦点
        self.username_input.setFocus()
        
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # 验证用户名和密码
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cur.execute("""
                SELECT role FROM users 
                WHERE username = ? AND password_hash = ?
            """, (username, password_hash))
            
            result = cur.fetchone()
            if result:
                self.user_role = result[0]
                self.username = username  # 保存用户名
                QMessageBox.information(self, "成功", "登录成功！")
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "用户名或密码错误")
                
            cur.close()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"登录失败：\n{str(e)}")

class UserManagementDialog(QDialog):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("用户管理")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 使用网格布局来对齐标签和输入框
        form_layout = QGridLayout()
        
        # 用户名输入
        username_label = QLabel("用户名:")
        username_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)
        
        # 密码输入
        password_label = QLabel("密码:")
        password_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_input, 1, 1)
        
        # 角色选择
        role_label = QLabel("角色:")
        role_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value)
        form_layout.addWidget(role_label, 2, 0)
        form_layout.addWidget(self.role_combo, 2, 1)
        
        # 按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加用户")
        add_button.setDefault(True)
        cancel_button = QPushButton("取消")
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        
        # 添加所有布局
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # 连接信号
        add_button.clicked.connect(self.add_user)
        cancel_button.clicked.connect(self.reject)
        
    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentText()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # 添加新用户
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, (username, password_hash, role))
            
            conn.commit()
            cur.close()
            conn.close()
            
            QMessageBox.information(self, "成功", "用户添加成功！")
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "错误", "用户名已存在")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"添加用户失败：\n{str(e)}") 