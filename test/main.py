import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                           QTableWidget, QTableWidgetItem, QMessageBox,
                           QMenu, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import sqlite3
from datetime import datetime
from product_dialog import AddProductDialog
from sale_dialog import AddSaleDialog
from user_management import (LoginDialog, UserManagementDialog, init_user_database,
                           UserRole, Permission, ROLE_PERMISSIONS)

class RetailManagementSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("零售商品销售管理系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 数据库文件路径
        self.db_path = 'retail.db'
        
        # 当前用户信息
        self.current_role = None
        self.current_username = None
        
        # 初始化数据库
        self.init_database()
        
        # 显示登录对话框
        if not self.show_login():
            sys.exit()
            
        self.init_ui()
        self.current_view = 'products'  # 当前视图：products 或 sales
        
    def show_login(self):
        """显示登录对话框"""
        dialog = LoginDialog(self.db_path)
        if dialog.exec():
            self.current_role = dialog.user_role
            self.current_username = dialog.username
            return True
        return False
        
    def switch_user(self):
        """切换用户"""
        if self.show_login():
            # 重新初始化界面
            # 保存当前窗口位置和大小
            geometry = self.geometry()
            
            # 清除旧的中心部件
            old_widget = self.centralWidget()
            if old_widget:
                old_widget.deleteLater()
                
            # 重新初始化界面
            self.init_ui()
            
            # 恢复窗口位置和大小
            self.setGeometry(geometry)
            
            # 显示切换成功消息
            QMessageBox.information(self, "成功", f"已切换到用户：{self.current_username}")
        
    def has_permission(self, permission):
        """检查当前用户是否有指定权限"""
        if not self.current_role:
            return False
            
        # 获取用户角色对应的权限列表
        role = UserRole(self.current_role)
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        # 如果用户有 ALL 权限或指定的权限，返回 True
        return Permission.ALL in permissions or permission in permissions
        
    def init_ui(self):
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 商品管理按钮组
        product_group = QHBoxLayout()
        if self.has_permission(Permission.MANAGE_PRODUCTS):
            self.add_product_btn = QPushButton("添加商品")
            product_group.addWidget(self.add_product_btn)
            self.add_product_btn.clicked.connect(self.show_add_product)
            
        self.view_products_btn = QPushButton("商品列表")
        product_group.addWidget(self.view_products_btn)
        self.view_products_btn.clicked.connect(self.show_products)
        
        # 库存管理按钮组
        inventory_group = QHBoxLayout()
        if self.has_permission(Permission.MANAGE_INVENTORY):
            self.add_inventory_btn = QPushButton("添加库存")
            inventory_group.addWidget(self.add_inventory_btn)
            self.add_inventory_btn.clicked.connect(self.show_add_inventory)
        
        # 销售管理按钮组
        sale_group = QHBoxLayout()
        if self.has_permission(Permission.MANAGE_CUSTOMERS):
            self.add_sale_btn = QPushButton("记录销售")
            sale_group.addWidget(self.add_sale_btn)
            self.add_sale_btn.clicked.connect(self.show_add_sale)
            
        if self.has_permission(Permission.VIEW_REPORTS):
            self.view_sales_btn = QPushButton("销售记录")
            sale_group.addWidget(self.view_sales_btn)
            self.view_sales_btn.clicked.connect(self.show_sales)
            
        # 用户管理按钮组
        user_group = QHBoxLayout()
        if self.has_permission(Permission.MANAGE_USERS):
            self.manage_users_btn = QPushButton("用户管理")
            user_group.addWidget(self.manage_users_btn)
            self.manage_users_btn.clicked.connect(self.show_user_management)
            
        # 用户切换按钮
        self.switch_user_btn = QPushButton("切换用户")
        user_group.addWidget(self.switch_user_btn)
        self.switch_user_btn.clicked.connect(self.switch_user)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入商品名称搜索...")
        self.search_btn = QPushButton("搜索")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        
        # 将按钮组添加到工具栏
        toolbar_layout.addLayout(product_group)
        toolbar_layout.addLayout(inventory_group)
        toolbar_layout.addLayout(sale_group)
        toolbar_layout.addLayout(user_group)
        toolbar_layout.addLayout(search_layout)
        toolbar_layout.addStretch()
        
        # 添加当前用户信息显示
        user_info = QLabel(f"当前用户：{self.current_username} ({self.current_role})")
        toolbar_layout.addWidget(user_info)
        
        # 添加表格
        self.table = QTableWidget()
        self.setup_products_table()
        
        # 将布局添加到主布局
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.table)
        
        # 连接按钮信号
        self.search_btn.clicked.connect(self.search_products)
        self.search_input.returnPressed.connect(self.search_products)
        
        # 设置表格上下文菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 显示初始数据
        self.show_products()
        
    def setup_products_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "商品名称", "价格", "库存"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def setup_sales_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "商品名称", "数量", "总价", "日期", "时间"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def show_context_menu(self, position):
        if self.current_view != 'products':
            return
            
        menu = QMenu()
        
        if self.has_permission(Permission.MANAGE_PRODUCTS):
            edit_action = QAction("编辑", self)
            delete_action = QAction("删除", self)
            menu.addAction(edit_action)
            menu.addAction(delete_action)
            
        if self.has_permission(Permission.MANAGE_INVENTORY):
            adjust_stock_action = QAction("调整库存", self)
            menu.addAction(adjust_stock_action)
            
        if not menu.actions():
            return
            
        # 获取选中的行
        row = self.table.rowAt(position.y())
        if row >= 0:
            self.table.selectRow(row)
            action = menu.exec(self.table.mapToGlobal(position))
            
            if action == edit_action and self.has_permission(Permission.MANAGE_PRODUCTS):
                self.edit_product(row)
            elif action == delete_action and self.has_permission(Permission.MANAGE_PRODUCTS):
                self.delete_product(row)
            elif action == adjust_stock_action and self.has_permission(Permission.MANAGE_INVENTORY):
                self.adjust_stock(row)
                
    def edit_product(self, row):
        item = self.table.item(row, 0)
        if not item:
            return
        product_id = int(item.text())
        
        item = self.table.item(row, 1)
        if not item:
            return
        name = item.text()
        
        item = self.table.item(row, 2)
        if not item:
            return
        price = float(item.text().replace('¥', '').strip())
        
        item = self.table.item(row, 3)
        if not item:
            return
        stock = int(item.text())
        
        dialog = AddProductDialog(self.db_path, self, (product_id, name, price, stock))
        if dialog.exec():
            self.show_products()
            
    def delete_product(self, row):
        item = self.table.item(row, 0)
        if not item:
            return
        product_id = int(item.text())
        
        item = self.table.item(row, 1)
        if not item:
            return
        name = item.text()
        
        reply = QMessageBox.question(self, '确认删除', 
                                   f'确定要删除商品 "{name}" 吗？\n此操作不可撤销！',
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = self.get_db_connection()
                cur = conn.cursor()
                
                # 检查是否有相关的销售记录
                cur.execute("SELECT COUNT(*) FROM sales WHERE product_id = ?", (product_id,))
                if cur.fetchone()[0] > 0:
                    QMessageBox.warning(self, "警告", 
                                      "无法删除此商品，因为存在相关的销售记录。\n" +
                                      "如果确实需要删除，请先删除相关的销售记录。")
                    return
                
                cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
                cur.close()
                conn.close()
                
                self.show_products()
                QMessageBox.information(self, "成功", "商品已删除！")
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "错误", f"删除失败：\n{str(e)}")
                
    def adjust_stock(self, row):
        item = self.table.item(row, 0)
        if not item:
            return
        product_id = int(item.text())
        
        item = self.table.item(row, 1)
        if not item:
            return
        name = item.text()
        
        item = self.table.item(row, 3)
        if not item:
            return
        current_stock = int(item.text())
        
        adjustment, ok = QInputDialog.getInt(
            self, "调整库存",
            f"当前库存: {current_stock}\n" +
            "请输入调整数量（正数增加，负数减少）:",
            0, -current_stock, 999999, 1
        )
        
        if ok:
            try:
                conn = self.get_db_connection()
                cur = conn.cursor()
                
                cur.execute("""
                    UPDATE products 
                    SET stock = stock + ? 
                    WHERE id = ?
                """, (adjustment, product_id))
                
                conn.commit()
                cur.close()
                conn.close()
                
                self.show_products()
                QMessageBox.information(self, "成功", 
                    f"库存已调整！\n新库存数量: {current_stock + adjustment}")
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "错误", f"库存调整失败：\n{str(e)}")
                
    def search_products(self):
        search_text = self.search_input.text().strip()
        if not search_text and self.current_view == 'products':
            self.show_products()
            return
            
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, price, stock 
                FROM products 
                WHERE name LIKE ? 
                ORDER BY id
            """, (f'%{search_text}%',))
            
            products = cur.fetchall()
            
            self.table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                for col, value in enumerate(product):
                    if col == 2:  # 价格列
                        value = f"¥{value:.2f}"
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)
            
            cur.close()
            conn.close()
            
            if len(products) == 0:
                QMessageBox.information(self, "搜索结果", "未找到匹配的商品")
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"搜索失败：\n{str(e)}")
            
    def get_db_connection(self):
        """创建数据库连接"""
        return sqlite3.connect(self.db_path)
        
    def init_database(self):
        """初始化数据库"""
        try:
            # 初始化用户数据库
            init_user_database(self.db_path)
            
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # 创建商品表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL
                )
            """)
            
            # 创建销售记录表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_price REAL NOT NULL,
                    sale_date TIMESTAMP NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"数据库初始化失败：\n{str(e)}")
            sys.exit(1)
    
    def show_add_product(self):
        dialog = AddProductDialog(self.db_path, self)
        if dialog.exec():
            self.show_products()
    
    def show_products(self):
        self.current_view = 'products'
        self.setup_products_table()
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT id, name, price, stock FROM products ORDER BY id")
            products = cur.fetchall()
            
            self.table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                for col, value in enumerate(product):
                    if col == 2:  # 价格列
                        value = f"¥{value:.2f}"
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)
            
            # 调整列宽
            self.table.resizeColumnsToContents()
            
            cur.close()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"获取商品列表失败：\n{str(e)}")
    
    def show_add_sale(self):
        dialog = AddSaleDialog(self.db_path, self)
        if dialog.exec():
            if self.current_view == 'sales':
                self.show_sales()
            else:
                self.show_products()
    
    def show_sales(self):
        self.current_view = 'sales'
        self.setup_sales_table()
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT s.id, p.name, s.quantity, s.total_price, 
                       date(s.sale_date), time(s.sale_date)
                FROM sales s
                JOIN products p ON s.product_id = p.id
                ORDER BY s.sale_date DESC
            """)
            sales = cur.fetchall()
            
            self.table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                for col, value in enumerate(sale):
                    if col == 3:  # 总价列
                        value = f"¥{value:.2f}"
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)
            
            # 调整列宽
            self.table.resizeColumnsToContents()
            
            cur.close()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"获取销售记录失败：\n{str(e)}")
    
    def show_user_management(self):
        """显示用户管理对话框"""
        if not self.has_permission(Permission.MANAGE_USERS):
            QMessageBox.warning(self, "警告", "您没有用户管理权限")
            return
            
        dialog = UserManagementDialog(self.db_path, self)
        dialog.exec()

    def show_add_inventory(self):
        """显示添加库存对话框"""
        if not self.has_permission(Permission.MANAGE_INVENTORY):
            QMessageBox.warning(self, "警告", "您没有库存管理权限")
            return
        
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # 获取所有商品列表
            cur.execute("SELECT id, name, stock FROM products ORDER BY name")
            products = cur.fetchall()
            
            if not products:
                QMessageBox.warning(self, "警告", "没有可用的商品，请先添加商品")
                return
            
            # 让用户选择商品
            product_names = [f"{p[1]} (当前库存: {p[2]})" for p in products]
            product_name, ok = QInputDialog.getItem(
                self, "选择商品", "请选择要添加库存的商品：",
                product_names, 0, False
            )
            
            if ok and product_name:
                # 获取选中的商品ID
                index = product_names.index(product_name)
                product_id = products[index][0]
                current_stock = products[index][2]
                
                # 让用户输入要添加的库存数量
                quantity, ok = QInputDialog.getInt(
                    self, "添加库存",
                    f"当前库存: {current_stock}\n请输入要添加的数量：",
                    1, 1, 999999, 1
                )
                
                if ok:
                    # 更新库存
                    cur.execute("""
                        UPDATE products 
                        SET stock = stock + ? 
                        WHERE id = ?
                    """, (quantity, product_id))
                    
                    conn.commit()
                    QMessageBox.information(self, "成功", 
                        f"库存已更新！\n新库存数量: {current_stock + quantity}")
                    
                    # 刷新商品列表显示
                    self.show_products()
        
            cur.close()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"添加库存失败：\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = RetailManagementSystem()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 