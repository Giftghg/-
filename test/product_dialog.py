from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QGridLayout, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
import sqlite3

class AddProductDialog(QDialog):
    def __init__(self, db_path, parent=None, product_data=None):
        super().__init__(parent)
        self.db_path = db_path
        self.product_data = product_data
        self.setWindowTitle("编辑商品" if product_data else "添加商品")
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
        
        # 商品名称
        name_label = QLabel("商品名称:")
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入商品名称")
        form_layout.addWidget(name_label, 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        
        # 商品价格
        price_label = QLabel("商品价格:")
        price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.1)
        self.price_input.setPrefix("¥ ")
        form_layout.addWidget(price_label, 1, 0)
        form_layout.addWidget(self.price_input, 1, 1)
        
        # 库存数量
        stock_label = QLabel("库存数量:")
        stock_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        self.stock_input.setSingleStep(1)
        self.stock_input.setSuffix(" 件")
        form_layout.addWidget(stock_label, 2, 0)
        form_layout.addWidget(self.stock_input, 2, 1)
        
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
        
        # 如果是编辑模式，填充现有数据
        if self.product_data:
            self.name_input.setText(self.product_data[1])
            self.price_input.setValue(float(self.product_data[2]))
            self.stock_input.setValue(int(self.product_data[3]))
        
        # 连接信号
        save_button.clicked.connect(self.save_product)
        cancel_button.clicked.connect(self.reject)
        
        # 设置初始焦点
        self.name_input.setFocus()
        
    def validate_inputs(self):
        """验证输入数据"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入商品名称")
            self.name_input.setFocus()
            return False
            
        if len(name) > 100:
            QMessageBox.warning(self, "警告", "商品名称不能超过100个字符")
            self.name_input.setFocus()
            return False
            
        price = self.price_input.value()
        if price <= 0:
            QMessageBox.warning(self, "警告", "商品价格必须大于0")
            self.price_input.setFocus()
            return False
            
        return True
        
    def save_product(self):
        if not self.validate_inputs():
            return
            
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            name = self.name_input.text().strip()
            price = self.price_input.value()
            stock = self.stock_input.value()
            
            if self.product_data:  # 更新现有商品
                cur.execute("""
                    UPDATE products 
                    SET name = ?, price = ?, stock = ?
                    WHERE id = ?
                """, (name, price, stock, self.product_data[0]))
                message = "商品更新成功！"
            else:  # 添加新商品
                cur.execute("""
                    INSERT INTO products (name, price, stock)
                    VALUES (?, ?, ?)
                """, (name, price, stock))
                message = "商品添加成功！"
            
            conn.commit()
            cur.close()
            conn.close()
            
            QMessageBox.information(self, "成功", message)
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "错误", "商品名称已存在，请使用其他名称")
            self.name_input.setFocus()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "错误", f"保存失败：\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：\n{str(e)}") 