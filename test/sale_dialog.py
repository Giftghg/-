from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QGridLayout, QSpinBox, QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import Qt
import sqlite3
from datetime import datetime

class AddSaleDialog(QDialog):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("记录销售")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()
        
    def get_db_connection(self):
        """创建数据库连接"""
        return sqlite3.connect(self.db_path)
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 使用网格布局来对齐标签和输入框
        form_layout = QGridLayout()
        
        # 商品选择
        product_label = QLabel("选择商品:")
        product_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.product_combo = QComboBox()
        self.load_products()
        form_layout.addWidget(product_label, 0, 0)
        form_layout.addWidget(self.product_combo, 0, 1)
        
        # 销售数量
        quantity_label = QLabel("销售数量:")
        quantity_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 999999)
        self.quantity_input.setSingleStep(1)
        self.quantity_input.setSuffix(" 件")
        form_layout.addWidget(quantity_label, 1, 0)
        form_layout.addWidget(self.quantity_input, 1, 1)
        
        # 总价显示
        total_label = QLabel("总价:")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_display = QLabel("¥ 0.00")
        form_layout.addWidget(total_label, 2, 0)
        form_layout.addWidget(self.total_display, 2, 1)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.setDefault(True)
        cancel_button = QPushButton("取消")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # 添加所有布局
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # 连接信号
        save_button.clicked.connect(self.save_sale)
        cancel_button.clicked.connect(self.reject)
        self.product_combo.currentIndexChanged.connect(self.update_total)
        self.quantity_input.valueChanged.connect(self.update_total)
        
    def load_products(self):
        """加载商品列表到下拉框"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, price, stock 
                FROM products 
                WHERE stock > 0 
                ORDER BY name
            """)
            
            self.products = cur.fetchall()
            self.product_combo.clear()
            
            if not self.products:
                QMessageBox.warning(self, "警告", "没有可销售的商品！")
                self.reject()
                return
                
            for product in self.products:
                self.product_combo.addItem(
                    f"{product[1]} (库存: {product[3]}件, 单价: ¥{product[2]:.2f})",
                    product[0]
                )
            
            cur.close()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"加载商品列表失败：\n{str(e)}")
            self.reject()
            
    def update_total(self):
        """更新总价显示"""
        if not self.products:
            return
            
        current_index = self.product_combo.currentIndex()
        if current_index < 0:
            return
            
        product = self.products[current_index]
        quantity = self.quantity_input.value()
        
        # 更新数量上限
        self.quantity_input.setMaximum(product[3])
        
        # 计算并显示总价
        total = product[2] * quantity
        self.total_display.setText(f"¥ {total:.2f}")
        
    def validate_inputs(self):
        """验证输入数据"""
        if not self.products:
            return False
            
        current_index = self.product_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "请选择商品")
            return False
            
        product = self.products[current_index]
        quantity = self.quantity_input.value()
        
        if quantity <= 0:
            QMessageBox.warning(self, "警告", "销售数量必须大于0")
            self.quantity_input.setFocus()
            return False
            
        if quantity > product[3]:
            QMessageBox.warning(self, "警告", f"库存不足！当前库存: {product[3]}件")
            self.quantity_input.setFocus()
            return False
            
        return True
        
    def save_sale(self):
        if not self.validate_inputs():
            return
            
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            current_index = self.product_combo.currentIndex()
            product = self.products[current_index]
            quantity = self.quantity_input.value()
            total = product[2] * quantity
            
            # 开始事务
            cur.execute("BEGIN TRANSACTION")
            
            try:
                # 添加销售记录
                cur.execute("""
                    INSERT INTO sales (product_id, quantity, total_price, sale_date)
                    VALUES (?, ?, ?, ?)
                """, (product[0], quantity, total, datetime.now()))
                
                # 更新库存
                cur.execute("""
                    UPDATE products 
                    SET stock = stock - ? 
                    WHERE id = ?
                """, (quantity, product[0]))
                
                # 提交事务
                conn.commit()
                
                QMessageBox.information(self, "成功", "销售记录已保存！")
                self.accept()
                
            except Exception as e:
                # 回滚事务
                conn.rollback()
                raise e
                
            finally:
                cur.close()
                conn.close()
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"保存失败：\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：\n{str(e)}") 