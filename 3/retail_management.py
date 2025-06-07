import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
import datetime
import os

class RetailManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("商品零售管理系统")
        self.root.geometry("1000x600")
        
        # 数据库连接配置
        self.db_config = {
            'host': 'localhost',
            'database': 'aa',
            'user': 'root',
            'password': '123123'
        }
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建状态变量
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        
        # 创建状态栏
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        
        # 创建标签页
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # 商品管理标签页
        self.product_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.product_tab, text="商品管理")
        
        # 客户管理标签页
        self.customer_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.customer_tab, text="客户管理")
        
        # 订单管理标签页
        self.order_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.order_tab, text="订单管理")
        
        # 库存管理标签页
        self.inventory_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.inventory_tab, text="库存管理")
        
        # 供应商管理标签页
        self.supplier_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.supplier_tab, text="供应商管理")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # 初始化各标签页
        self.init_product_tab()
        self.init_customer_tab()
        self.init_order_tab()
        self.init_inventory_tab()
        self.init_supplier_tab()
        
        # 连接数据库
        self.connect_to_database()
    
    def connect_to_database(self):
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            
            if self.connection.is_connected():
                self.status_var.set("数据库连接成功")
                
                # 初始化数据库结构
                self.init_database_structure()
                
                # 修复触发器
                self.fix_triggers()
                
                # 加载初始数据
                self.load_products()
                self.load_customers()
                self.load_orders()
                self.load_inventory_status()
                self.load_suppliers()
                
                return True
            else:
                self.status_var.set("数据库连接失败")
                return False
        except Error as e:
            self.status_var.set(f"数据库连接错误: {e}")
            messagebox.showerror("数据库连接错误", str(e))
            return False
    
    def init_database_structure(self):
        """初始化数据库结构，确保所有必要的表和视图都存在"""
        try:
            # 检查suppliers表是否存在
            self.cursor.execute("SHOW TABLES LIKE 'suppliers'")
            if not self.cursor.fetchone():
                # 创建suppliers表
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suppliers (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        contact_person VARCHAR(100),
                        phone VARCHAR(20),
                        email VARCHAR(100),
                        address VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
            
            # 检查products表是否有必要的字段
            self.cursor.execute("DESCRIBE products")
            fields = self.cursor.fetchall()
            field_names = [field['Field'] for field in fields]
            
            # 如果没有cost、stock等字段，则添加
            if 'cost' not in field_names or 'stock' not in field_names or 'category' not in field_names or 'barcode' not in field_names:
                self.cursor.execute("""
                    ALTER TABLE products
                    ADD COLUMN IF NOT EXISTS cost DECIMAL(10,2) DEFAULT 0.00,
                    ADD COLUMN IF NOT EXISTS stock INT DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT '',
                    ADD COLUMN IF NOT EXISTS barcode VARCHAR(50) DEFAULT '',
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
            
            # 检查inventory表是否存在
            self.cursor.execute("SHOW TABLES LIKE 'inventory'")
            if not self.cursor.fetchone():
                # 创建inventory表
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory (
                        product_id INT NOT NULL PRIMARY KEY,
                        quantity INT NOT NULL DEFAULT 0,
                        min_stock_level INT DEFAULT 10,
                        max_stock_level INT DEFAULT 100,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                """)
                
                # 初始化库存数据
                self.cursor.execute("""
                    INSERT INTO inventory (product_id, quantity, min_stock_level, max_stock_level)
                    SELECT id, stock, 10, 100 FROM products
                    ON DUPLICATE KEY UPDATE 
                        quantity = products.stock,
                        min_stock_level = 10,
                        max_stock_level = 100
                """)
            
            # 检查inventory_logs表是否存在
            self.cursor.execute("SHOW TABLES LIKE 'inventory_logs'")
            if not self.cursor.fetchone():
                # 创建inventory_logs表
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_id INT NOT NULL,
                        change_type ENUM('in', 'out', 'adjustment', 'sale') NOT NULL,
                        quantity INT NOT NULL,
                        quantity_change INT NOT NULL,
                        reference_id INT,
                        reference_type ENUM('stock_in', 'stock_out', 'adjustment', 'sales_order') NOT NULL,
                        before_quantity INT NOT NULL,
                        after_quantity INT NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)
            
            # 检查inventory_logs表是否有quantity_change字段
            self.cursor.execute("DESCRIBE inventory_logs")
            fields = self.cursor.fetchall()
            field_names = [field['Field'] for field in fields]
            
            # 如果没有quantity_change字段，则添加
            if 'quantity_change' not in field_names:
                self.cursor.execute("""
                    ALTER TABLE inventory_logs
                    ADD COLUMN quantity_change INT NOT NULL AFTER quantity
                """)
            
            # 检查product_inventory_status视图是否存在
            self.cursor.execute("SHOW TABLES LIKE 'product_inventory_status'")
            if not self.cursor.fetchone():
                # 创建product_inventory_status视图 - 使用与现有视图相同的列名
                self.cursor.execute("""
                    CREATE OR REPLACE VIEW product_inventory_status AS
                    SELECT 
                        p.id AS product_id,
                        p.name AS product_name,
                        p.price AS price,
                        p.category AS category,
                        IFNULL(i.quantity, 0) AS current_stock,
                        CASE 
                            WHEN IFNULL(i.quantity, 0) <= IFNULL(i.min_stock_level, 10) THEN '不足'
                            WHEN IFNULL(i.quantity, 0) >= IFNULL(i.max_stock_level, 100) THEN '过多'
                            ELSE '充足'
                        END AS stock_status
                    FROM 
                        products p
                    LEFT JOIN 
                        inventory i ON p.id = i.product_id
                """)
            
            # 检查sales_order_items表是否存在
            self.cursor.execute("SHOW TABLES LIKE 'sales_order_items'")
            if not self.cursor.fetchone():
                # 创建sales_order_items表
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sales_order_items (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id INT NOT NULL,
                        product_id INT NOT NULL,
                        quantity INT NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        subtotal DECIMAL(10, 2) NOT NULL,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)
            
            # 创建触发器：销售订单创建后自动减少库存
            self.cursor.execute("SHOW TRIGGERS LIKE 'after_sales_order_item_insert'")
            if not self.cursor.fetchone():
                try:
                    # 使用单独的语句执行触发器创建
                    self.cursor.execute("""
                        CREATE TRIGGER after_sales_order_item_insert
                        AFTER INSERT ON sales_order_items
                        FOR EACH ROW
                        BEGIN
                            UPDATE inventory 
                            SET quantity = quantity - NEW.quantity
                            WHERE product_id = NEW.product_id;
                            
                            INSERT INTO inventory_logs (
                                product_id, 
                                change_type, 
                                quantity, 
                                reference_id, 
                                reference_type,
                                before_quantity,
                                after_quantity,
                                notes
                            )
                            SELECT 
                                NEW.product_id,
                                'sale',
                                NEW.quantity,
                                NEW.order_id,
                                'sales_order',
                                quantity + NEW.quantity,
                                quantity,
                                CONCAT('销售订单 #', NEW.order_id)
                            FROM inventory
                            WHERE product_id = NEW.product_id;
                        END
                    """)
                except Error as e:
                    # 尝试使用另一种方式创建触发器
                    try:
                        # 使用多条语句创建触发器
                        self.cursor.execute("""
                            CREATE TRIGGER after_sales_order_item_insert
                            AFTER INSERT ON sales_order_items
                            FOR EACH ROW
                            BEGIN
                                UPDATE inventory 
                                SET quantity = quantity - NEW.quantity
                                WHERE product_id = NEW.product_id;
                            END
                        """)
                        
                        # 创建一个辅助触发器来记录日志
                        self.cursor.execute("""
                            CREATE TRIGGER after_sales_order_item_insert_log
                            AFTER INSERT ON sales_order_items
                            FOR EACH ROW
                            BEGIN
                                INSERT INTO inventory_logs (
                                    product_id, 
                                    change_type, 
                                    quantity, 
                                    quantity_change,
                                    reference_id, 
                                    reference_type,
                                    before_quantity,
                                    after_quantity,
                                    notes
                                )
                                SELECT 
                                    NEW.product_id,
                                    'sale',
                                    NEW.quantity,
                                    -NEW.quantity,
                                    NEW.order_id,
                                    'sales_order',
                                    quantity + NEW.quantity,
                                    quantity,
                                    CONCAT('销售订单 #', NEW.order_id)
                                FROM inventory
                                WHERE product_id = NEW.product_id;
                            END
                        """)
                    except Error as e2:
                        pass
            
            # 创建触发器：入库完成后自动增加库存
            self.cursor.execute("SHOW TRIGGERS LIKE 'after_stock_in_complete'")
            if not self.cursor.fetchone():
                try:
                    self.cursor.execute("""
                        CREATE TRIGGER after_stock_in_complete
                        AFTER UPDATE ON stock_in
                        FOR EACH ROW
                        BEGIN
                            IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
                                INSERT INTO inventory_logs (
                                    product_id, 
                                    change_type, 
                                    quantity, 
                                    reference_id, 
                                    reference_type,
                                    before_quantity,
                                    after_quantity,
                                    notes
                                )
                                SELECT 
                                    sii.product_id,
                                    'in',
                                    sii.quantity,
                                    NEW.id,
                                    'stock_in',
                                    IFNULL(i.quantity, 0),
                                    IFNULL(i.quantity, 0) + sii.quantity,
                                    CONCAT('入库单 #', NEW.id)
                                FROM stock_in_items sii
                                LEFT JOIN inventory i ON i.product_id = sii.product_id
                                WHERE sii.stock_in_id = NEW.id;
                                
                                INSERT INTO inventory (product_id, quantity)
                                SELECT sii.product_id, sii.quantity
                                FROM stock_in_items sii
                                WHERE sii.stock_in_id = NEW.id
                                ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity);
                            END IF;
                        END
                    """)
                except Error as e:
                    # 尝试使用另一种方式创建触发器
                    try:
                        # 使用多条语句创建触发器
                        self.cursor.execute("""
                            CREATE TRIGGER after_stock_in_complete
                            AFTER UPDATE ON stock_in
                            FOR EACH ROW
                            BEGIN
                                IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
                                    INSERT INTO inventory (product_id, quantity)
                                    SELECT sii.product_id, sii.quantity
                                    FROM stock_in_items sii
                                    WHERE sii.stock_in_id = NEW.id
                                    ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity);
                                END IF;
                            END
                        """)
                        
                        # 创建一个辅助触发器来记录日志
                        self.cursor.execute("""
                            CREATE TRIGGER after_stock_in_complete_log
                            AFTER UPDATE ON stock_in
                            FOR EACH ROW
                            BEGIN
                                IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
                                    INSERT INTO inventory_logs (
                                        product_id, 
                                        change_type, 
                                        quantity, 
                                        reference_id, 
                                        reference_type,
                                        before_quantity,
                                        after_quantity,
                                        notes
                                    )
                                    SELECT 
                                        sii.product_id,
                                        'in',
                                        sii.quantity,
                                        NEW.id,
                                        'stock_in',
                                        IFNULL(i.quantity, 0),
                                        IFNULL(i.quantity, 0) + sii.quantity,
                                        CONCAT('入库单 #', NEW.id)
                                    FROM stock_in_items sii
                                    LEFT JOIN inventory i ON i.product_id = sii.product_id
                                    WHERE sii.stock_in_id = NEW.id;
                                END IF;
                            END
                        """)
                    except Error as e2:
                        pass
            
            # 创建触发器：出库后自动减少库存
            self.cursor.execute("SHOW TRIGGERS LIKE 'after_stock_out_item_insert'")
            if not self.cursor.fetchone():
                try:
                    self.cursor.execute("""
                        CREATE TRIGGER after_stock_out_item_insert
                        AFTER INSERT ON stock_out_items
                        FOR EACH ROW
                        BEGIN
                            UPDATE inventory 
                            SET quantity = quantity - NEW.quantity
                            WHERE product_id = NEW.product_id;
                            
                            INSERT INTO inventory_logs (
                                product_id, 
                                change_type, 
                                quantity, 
                                reference_id, 
                                reference_type,
                                before_quantity,
                                after_quantity,
                                notes
                            )
                            SELECT 
                                NEW.product_id,
                                'out',
                                NEW.quantity,
                                NEW.stock_out_id,
                                'stock_out',
                                quantity + NEW.quantity,
                                quantity,
                                CONCAT('出库单 #', NEW.stock_out_id)
                            FROM inventory
                            WHERE product_id = NEW.product_id;
                        END
                    """)
                except Error as e:
                    # 尝试使用另一种方式创建触发器
                    try:
                        # 使用多条语句创建触发器
                        self.cursor.execute("""
                            CREATE TRIGGER after_stock_out_item_insert
                            AFTER INSERT ON stock_out_items
                            FOR EACH ROW
                            BEGIN
                                UPDATE inventory 
                                SET quantity = quantity - NEW.quantity
                                WHERE product_id = NEW.product_id;
                            END
                        """)
                        
                        # 创建一个辅助触发器来记录日志
                        self.cursor.execute("""
                            CREATE TRIGGER after_stock_out_item_insert_log
                            AFTER INSERT ON stock_out_items
                            FOR EACH ROW
                            BEGIN
                                INSERT INTO inventory_logs (
                                    product_id, 
                                    change_type, 
                                    quantity, 
                                    reference_id, 
                                    reference_type,
                                    before_quantity,
                                    after_quantity,
                                    notes
                                )
                                SELECT 
                                    NEW.product_id,
                                    'out',
                                    NEW.quantity,
                                    NEW.stock_out_id,
                                    'stock_out',
                                    quantity + NEW.quantity,
                                    quantity,
                                    CONCAT('出库单 #', NEW.stock_out_id)
                                FROM inventory
                                WHERE product_id = NEW.product_id;
                            END
                        """)
                    except Error as e2:
                        pass
            
            # 创建存储过程：库存调整
            try:
                self.cursor.execute("DROP PROCEDURE IF EXISTS adjust_inventory")
                self.cursor.execute("""
                    CREATE PROCEDURE adjust_inventory(
                        IN p_product_id INT,
                        IN p_quantity INT,
                        IN p_notes TEXT
                    )
                    BEGIN
                        DECLARE current_qty INT;
                        DECLARE qty_change INT;
                        
                        SELECT IFNULL(quantity, 0) INTO current_qty 
                        FROM inventory 
                        WHERE product_id = p_product_id;
                        
                        SET qty_change = p_quantity - current_qty;
                        
                        -- 更新库存表
                        INSERT INTO inventory (product_id, quantity)
                        VALUES (p_product_id, p_quantity)
                        ON DUPLICATE KEY UPDATE 
                            quantity = p_quantity;
                        
                        -- 同步更新商品表中的库存字段
                        UPDATE products 
                        SET stock = p_quantity 
                        WHERE id = p_product_id;
                        
                        -- 记录库存日志
                        INSERT INTO inventory_logs (
                            product_id, 
                            change_type, 
                            quantity,
                            quantity_change,
                            reference_type,
                            before_quantity,
                            after_quantity,
                            notes
                        )
                        VALUES (
                            p_product_id,
                            'adjustment',
                            p_quantity,
                            qty_change,
                            'adjustment',
                            current_qty,
                            p_quantity,
                            p_notes
                        );
                    END
                """)
            except Error as e:
                pass
            
            self.connection.commit()
            
            # 更新状态栏而不是显示弹窗
            self.status_var.set("数据库结构初始化完成")
            
        except Error as e:
            messagebox.showerror("错误", f"初始化数据库结构失败: {e}")
    
    def init_product_tab(self):
        """初始化商品管理标签页"""
        # 顶部按钮框架
        top_frame = ttk.Frame(self.product_tab)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_frame, text="添加商品", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="编辑商品", command=self.edit_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="删除商品", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="刷新", command=self.load_products).pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.product_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.product_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_products).pack(side=tk.LEFT)
        
        # 商品表格
        columns = ("id", "name", "price", "cost", "stock", "category", "barcode", "created_at")
        self.product_tree = ttk.Treeview(self.product_tab, columns=columns, show="headings")
        
        for col in columns:
            self.product_tree.heading(col, text=col.capitalize().replace("_", " "))
            # 根据列名设置列宽
            if col == "name":
                self.product_tree.column(col, width=150)
            elif col == "description":
                self.product_tree.column(col, width=200)
            elif col == "created_at":
                self.product_tree.column(col, width=150)
            else:
                self.product_tree.column(col, width=100)
        
        self.product_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 状态栏
        self.product_status_var = tk.StringVar()
        ttk.Label(self.product_tab, textvariable=self.product_status_var).pack(side=tk.LEFT, pady=5)
    
    def init_customer_tab(self):
        """初始化客户管理标签页"""
        # 顶部按钮框架
        top_frame = ttk.Frame(self.customer_tab)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_frame, text="添加客户", command=self.add_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="编辑客户", command=self.edit_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="删除客户", command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="刷新", command=self.load_customers).pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.customer_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.customer_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_customers).pack(side=tk.LEFT)
        
        # 客户表格
        columns = ("id", "name", "phone", "email", "address", "points", "created_at")
        self.customer_tree = ttk.Treeview(self.customer_tab, columns=columns, show="headings")
        
        for col in columns:
            self.customer_tree.heading(col, text=col.capitalize().replace("_", " "))
            # 根据列名设置列宽
            if col == "name" or col == "phone":
                self.customer_tree.column(col, width=120)
            elif col == "address":
                self.customer_tree.column(col, width=200)
            elif col == "created_at":
                self.customer_tree.column(col, width=150)
            else:
                self.customer_tree.column(col, width=100)
        
        self.customer_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 状态栏
        self.customer_status_var = tk.StringVar()
        ttk.Label(self.customer_tab, textvariable=self.customer_status_var).pack(side=tk.LEFT, pady=5)
    
    def init_order_tab(self):
        """初始化订单管理标签页"""
        # 顶部按钮框架
        top_frame = ttk.Frame(self.order_tab)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_frame, text="创建订单", command=self.create_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="查看订单详情", command=self.view_order_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="更新订单状态", command=self.update_order_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="刷新", command=self.load_orders).pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.order_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.order_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_orders).pack(side=tk.LEFT)
        
        # 订单表格
        columns = ("id", "customer_name", "total_amount", "discount", "final_amount", "payment_method", "status", "created_at")
        self.order_tree = ttk.Treeview(self.order_tab, columns=columns, show="headings")
        
        for col in columns:
            self.order_tree.heading(col, text=col.capitalize().replace("_", " "))
            # 根据列名设置列宽
            if col == "customer_name":
                self.order_tree.column(col, width=120)
            elif col == "status" or col == "payment_method":
                self.order_tree.column(col, width=100)
            elif col == "created_at":
                self.order_tree.column(col, width=150)
            else:
                self.order_tree.column(col, width=90)
        
        self.order_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 状态栏
        self.order_status_var = tk.StringVar()
        ttk.Label(self.order_tab, textvariable=self.order_status_var).pack(side=tk.LEFT, pady=5)
    
    def init_inventory_tab(self):
        """初始化库存管理标签页"""
        # 创建子标签页
        inventory_notebook = ttk.Notebook(self.inventory_tab)
        inventory_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 库存状态子标签页
        inventory_status_tab = ttk.Frame(inventory_notebook)
        inventory_notebook.add(inventory_status_tab, text="库存状态")
        
        # 库存日志子标签页
        inventory_log_tab = ttk.Frame(inventory_notebook)
        inventory_notebook.add(inventory_log_tab, text="库存日志")
        
        # 初始化各子标签页
        self.init_inventory_status_tab(inventory_status_tab)
        self.init_inventory_log_tab(inventory_log_tab)
    
    def init_inventory_status_tab(self, parent_tab):
        """初始化库存状态子标签页"""
        # 顶部按钮框架
        top_frame = ttk.Frame(parent_tab)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_frame, text="刷新", command=self.load_inventory_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="库存调整", command=self.adjust_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="导出库存报表", command=self.export_inventory_report).pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.inventory_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.inventory_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_inventory).pack(side=tk.LEFT)
        
        # 库存状态表格
        columns = ("id", "name", "category", "barcode", "current_stock", "min_stock_level", 
                   "max_stock_level", "stock_status", "price", "cost", "last_updated")
        self.inventory_tree = ttk.Treeview(parent_tab, columns=columns, show="headings")
        
        for col in columns:
            display_name = col.capitalize().replace("_", " ")
            if col == "current_stock":
                display_name = "当前库存"
            elif col == "min_stock_level":
                display_name = "最小库存"
            elif col == "max_stock_level":
                display_name = "最大库存"
            elif col == "stock_status":
                display_name = "库存状态"
            elif col == "last_updated":
                display_name = "最后更新"
            elif col == "name":
                display_name = "商品名称"
            elif col == "category":
                display_name = "分类"
            elif col == "barcode":
                display_name = "条码"
            elif col == "price":
                display_name = "售价"
            elif col == "cost":
                display_name = "成本"
                
            self.inventory_tree.heading(col, text=display_name)
            
            # 根据列名设置列宽
            if col == "name":
                self.inventory_tree.column(col, width=150)
            elif col == "stock_status":
                self.inventory_tree.column(col, width=80)
            elif col == "last_updated":
                self.inventory_tree.column(col, width=150)
            else:
                self.inventory_tree.column(col, width=80)
        
        # 设置行颜色
        self.inventory_tree.tag_configure('不足', background='#FFCCCC')
        self.inventory_tree.tag_configure('过多', background='#CCFFCC')
        self.inventory_tree.tag_configure('充足', background='white')
        
        self.inventory_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent_tab, orient="vertical", command=self.inventory_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        # 状态栏
        self.inventory_status_var = tk.StringVar()
        ttk.Label(parent_tab, textvariable=self.inventory_status_var).pack(side=tk.LEFT, pady=5)
    
    def init_inventory_log_tab(self, parent_tab):
        """初始化库存日志子标签页"""
        # 顶部按钮框架
        top_frame = ttk.Frame(parent_tab)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_frame, text="刷新", command=self.load_inventory_logs).pack(side=tk.LEFT, padx=5)
        
        # 日期过滤
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(filter_frame, text="开始日期:").pack(side=tk.LEFT)
        self.start_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="结束日期:").pack(side=tk.LEFT)
        self.end_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="筛选", command=self.filter_inventory_logs).pack(side=tk.LEFT, padx=5)
        
        # 库存日志表格
        columns = ("id", "product_name", "change_type", "quantity", "quantity_change", "reference_type", 
                   "before_quantity", "after_quantity", "notes", "created_at")
        self.inventory_log_tree = ttk.Treeview(parent_tab, columns=columns, show="headings")
        
        for col in columns:
            display_name = col.capitalize().replace("_", " ")
            if col == "product_name":
                display_name = "商品名称"
            elif col == "change_type":
                display_name = "变动类型"
            elif col == "quantity":
                display_name = "当前数量"
            elif col == "quantity_change":
                display_name = "变动数量"
            elif col == "reference_type":
                display_name = "引用类型"
            elif col == "before_quantity":
                display_name = "变动前数量"
            elif col == "after_quantity":
                display_name = "变动后数量"
            elif col == "notes":
                display_name = "备注"
            elif col == "created_at":
                display_name = "创建时间"
                
            self.inventory_log_tree.heading(col, text=display_name)
            
            # 根据列名设置列宽
            if col == "product_name":
                self.inventory_log_tree.column(col, width=150)
            elif col == "notes":
                self.inventory_log_tree.column(col, width=200)
            elif col == "created_at":
                self.inventory_log_tree.column(col, width=150)
            else:
                self.inventory_log_tree.column(col, width=80)
        
        self.inventory_log_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent_tab, orient="vertical", command=self.inventory_log_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.inventory_log_tree.configure(yscrollcommand=scrollbar.set)
        
        # 状态栏
        self.inventory_log_status_var = tk.StringVar()
        ttk.Label(parent_tab, textvariable=self.inventory_log_status_var).pack(side=tk.LEFT, pady=5)
    
    def init_supplier_tab(self):
        """初始化供应商管理标签页"""
        # 顶部按钮框架
        top_frame = ttk.Frame(self.supplier_tab)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_frame, text="添加供应商", command=self.add_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="编辑供应商", command=self.edit_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="删除供应商", command=self.delete_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="刷新", command=self.load_suppliers).pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.supplier_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.supplier_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_suppliers).pack(side=tk.LEFT)
        
        # 供应商表格
        columns = ("id", "name", "contact_person", "phone", "email", "address", "created_at")
        self.supplier_tree = ttk.Treeview(self.supplier_tab, columns=columns, show="headings")
        
        for col in columns:
            display_name = col.capitalize().replace("_", " ")
            if col == "name":
                display_name = "供应商名称"
            elif col == "contact_person":
                display_name = "联系人"
            elif col == "phone":
                display_name = "电话"
            elif col == "email":
                display_name = "邮箱"
            elif col == "address":
                display_name = "地址"
            elif col == "created_at":
                display_name = "创建时间"
                
            self.supplier_tree.heading(col, text=display_name)
            
            # 根据列名设置列宽
            if col == "name" or col == "contact_person":
                self.supplier_tree.column(col, width=120)
            elif col == "address":
                self.supplier_tree.column(col, width=200)
            elif col == "created_at":
                self.supplier_tree.column(col, width=150)
            else:
                self.supplier_tree.column(col, width=100)
        
        self.supplier_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.supplier_tab, orient="vertical", command=self.supplier_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.supplier_tree.configure(yscrollcommand=scrollbar.set)
        
        # 状态栏
        self.supplier_status_var = tk.StringVar()
        ttk.Label(self.supplier_tab, textvariable=self.supplier_status_var).pack(side=tk.LEFT, pady=5)
    
    def load_products(self):
        """加载商品数据"""
        # 清空现有数据
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        try:
            query = "SELECT * FROM products ORDER BY id DESC"
            self.cursor.execute(query)
            products = self.cursor.fetchall()
            
            for product in products:
                self.product_tree.insert("", "end", values=(
                    product['id'], 
                    product['name'], 
                    product['price'],
                    product['cost'],
                    product['stock'],
                    product['category'],
                    product['barcode'],
                    product['created_at']
                ))
            
            self.product_status_var.set(f"共加载 {len(products)} 条商品数据")
        except Error as e:
            messagebox.showerror("错误", f"加载商品数据失败: {e}")
    
    def load_customers(self):
        """加载客户数据"""
        # 清空现有数据
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        
        try:
            query = "SELECT * FROM customers ORDER BY id DESC"
            self.cursor.execute(query)
            customers = self.cursor.fetchall()
            
            for customer in customers:
                self.customer_tree.insert("", "end", values=(
                    customer['id'], 
                    customer['name'], 
                    customer['phone'],
                    customer['email'],
                    customer['address'],
                    customer['points'],
                    customer['created_at']
                ))
            
            self.customer_status_var.set(f"共加载 {len(customers)} 条客户数据")
        except Error as e:
            messagebox.showerror("错误", f"加载客户数据失败: {e}")
    
    def load_orders(self):
        """加载订单数据"""
        # 清空现有数据
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        try:
            query = """
                SELECT 
                    so.id,
                    c.name AS customer_name,
                    so.total_amount,
                    so.discount,
                    so.final_amount,
                    so.payment_method,
                    so.status,
                    so.created_at
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.id
                ORDER BY so.id DESC
            """
            self.cursor.execute(query)
            orders = self.cursor.fetchall()
            
            for order in orders:
                self.order_tree.insert("", "end", values=(
                    order['id'], 
                    order['customer_name'], 
                    order['total_amount'],
                    order['discount'],
                    order['final_amount'],
                    order['payment_method'],
                    order['status'],
                    order['created_at']
                ))
            
            self.order_status_var.set(f"共加载 {len(orders)} 条订单数据")
        except Error as e:
            messagebox.showerror("错误", f"加载订单数据失败: {e}")
    
    def search_products(self):
        """搜索商品"""
        search_text = self.product_search_var.get().strip().lower()
        if not search_text:
            self.load_products()
            return
        
        # 清空现有数据
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        try:
            query = """
                SELECT * FROM products 
                WHERE LOWER(name) LIKE %s OR LOWER(category) LIKE %s
                ORDER BY id DESC
            """
            search_pattern = f"%{search_text}%"
            self.cursor.execute(query, (search_pattern, search_pattern))
            products = self.cursor.fetchall()
            
            for product in products:
                self.product_tree.insert("", "end", values=(
                    product['id'], 
                    product['name'], 
                    product['price'],
                    product['cost'],
                    product['stock'],
                    product['category'],
                    product['barcode'],
                    product['created_at']
                ))
            
            self.product_status_var.set(f"找到 {len(products)} 条匹配商品")
        except Error as e:
            messagebox.showerror("错误", f"搜索商品失败: {e}")
    
    def search_customers(self):
        """搜索客户"""
        search_text = self.customer_search_var.get().strip().lower()
        if not search_text:
            self.load_customers()
            return
        
        # 清空现有数据
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        
        try:
            query = """
                SELECT * FROM customers 
                WHERE LOWER(name) LIKE %s OR LOWER(phone) LIKE %s
                ORDER BY id DESC
            """
            search_pattern = f"%{search_text}%"
            self.cursor.execute(query, (search_pattern, search_pattern))
            customers = self.cursor.fetchall()
            
            for customer in customers:
                self.customer_tree.insert("", "end", values=(
                    customer['id'], 
                    customer['name'], 
                    customer['phone'],
                    customer['email'],
                    customer['address'],
                    customer['points'],
                    customer['created_at']
                ))
            
            self.customer_status_var.set(f"找到 {len(customers)} 条匹配客户")
        except Error as e:
            messagebox.showerror("错误", f"搜索客户失败: {e}")
    
    def search_orders(self):
        """搜索订单"""
        search_text = self.order_search_var.get().strip().lower()
        if not search_text:
            self.load_orders()
            return
        
        # 清空现有数据
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        try:
            query = """
                SELECT 
                    so.id,
                    c.name AS customer_name,
                    so.total_amount,
                    so.discount,
                    so.final_amount,
                    so.payment_method,
                    so.status,
                    so.created_at
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.id
                WHERE LOWER(c.name) LIKE %s OR so.id = %s
                ORDER BY so.id DESC
            """
            search_pattern = f"%{search_text}%"
            # 尝试将搜索文本转换为整数（用于订单ID搜索）
            try:
                order_id = int(search_text)
            except ValueError:
                order_id = None
            
            if order_id:
                self.cursor.execute(query, (search_pattern, order_id))
            else:
                self.cursor.execute(query, (search_pattern, None))
            
            orders = self.cursor.fetchall()
            
            for order in orders:
                self.order_tree.insert("", "end", values=(
                    order['id'], 
                    order['customer_name'], 
                    order['total_amount'],
                    order['discount'],
                    order['final_amount'],
                    order['payment_method'],
                    order['status'],
                    order['created_at']
                ))
            
            self.order_status_var.set(f"找到 {len(orders)} 条匹配订单")
        except Error as e:
            messagebox.showerror("错误", f"搜索订单失败: {e}")
    
    def add_product(self):
        """添加商品"""
        product_window = tk.Toplevel(self.root)
        product_window.title("添加商品")
        product_window.geometry("400x300")
        product_window.resizable(False, False)
        
        # 商品信息框架
        frame = ttk.Frame(product_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 商品名称
        ttk.Label(frame, text="商品名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5)
        
        # 价格
        ttk.Label(frame, text="价格:").grid(row=1, column=0, sticky=tk.W, pady=5)
        price_var = tk.DoubleVar()
        ttk.Entry(frame, textvariable=price_var, width=30).grid(row=1, column=1, pady=5)
        
        # 成本
        ttk.Label(frame, text="成本:").grid(row=2, column=0, sticky=tk.W, pady=5)
        cost_var = tk.DoubleVar()
        ttk.Entry(frame, textvariable=cost_var, width=30).grid(row=2, column=1, pady=5)
        
        # 库存
        ttk.Label(frame, text="库存:").grid(row=3, column=0, sticky=tk.W, pady=5)
        stock_var = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=stock_var, width=30).grid(row=3, column=1, pady=5)
        
        # 分类
        ttk.Label(frame, text="分类:").grid(row=4, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar()
        ttk.Entry(frame, textvariable=category_var, width=30).grid(row=4, column=1, pady=5)
        
        # 条码
        ttk.Label(frame, text="条码:").grid(row=5, column=0, sticky=tk.W, pady=5)
        barcode_var = tk.StringVar()
        ttk.Entry(frame, textvariable=barcode_var, width=30).grid(row=5, column=1, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(product_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def save_product():
            name = name_var.get().strip()
            price = price_var.get()
            cost = cost_var.get()
            stock = stock_var.get()
            category = category_var.get().strip()
            barcode = barcode_var.get().strip()
            
            if not name:
                messagebox.showerror("错误", "商品名称不能为空")
                return
            
            try:
                query = """
                    INSERT INTO products (name, price, cost, stock, category, barcode)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (name, price, cost, stock, category, barcode))
                self.connection.commit()
                messagebox.showinfo("成功", "商品添加成功")
                product_window.destroy()
                self.load_products()
            except Error as e:
                messagebox.showerror("错误", f"添加商品失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=product_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def edit_product(self):
        """编辑商品"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要编辑的商品")
            return
        
        item = self.product_tree.item(selected_item[0])
        values = item['values']
        
        product_id = values[0]
        
        product_window = tk.Toplevel(self.root)
        product_window.title("编辑商品")
        product_window.geometry("400x300")
        product_window.resizable(False, False)
        
        # 商品信息框架
        frame = ttk.Frame(product_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 商品名称
        ttk.Label(frame, text="商品名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=values[1])
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5)
        
        # 价格
        ttk.Label(frame, text="价格:").grid(row=1, column=0, sticky=tk.W, pady=5)
        price_var = tk.DoubleVar(value=values[2])
        ttk.Entry(frame, textvariable=price_var, width=30).grid(row=1, column=1, pady=5)
        
        # 成本
        ttk.Label(frame, text="成本:").grid(row=2, column=0, sticky=tk.W, pady=5)
        cost_var = tk.DoubleVar(value=values[3])
        ttk.Entry(frame, textvariable=cost_var, width=30).grid(row=2, column=1, pady=5)
        
        # 库存
        ttk.Label(frame, text="库存:").grid(row=3, column=0, sticky=tk.W, pady=5)
        stock_var = tk.IntVar(value=values[4])
        ttk.Entry(frame, textvariable=stock_var, width=30).grid(row=3, column=1, pady=5)
        
        # 分类
        ttk.Label(frame, text="分类:").grid(row=4, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar(value=values[5])
        ttk.Entry(frame, textvariable=category_var, width=30).grid(row=4, column=1, pady=5)
        
        # 条码
        ttk.Label(frame, text="条码:").grid(row=5, column=0, sticky=tk.W, pady=5)
        barcode_var = tk.StringVar(value=values[6])
        ttk.Entry(frame, textvariable=barcode_var, width=30).grid(row=5, column=1, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(product_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def update_product():
            name = name_var.get().strip()
            price = price_var.get()
            cost = cost_var.get()
            stock = stock_var.get()
            category = category_var.get().strip()
            barcode = barcode_var.get().strip()
            
            if not name:
                messagebox.showerror("错误", "商品名称不能为空")
                return
            
            try:
                query = """
                    UPDATE products 
                    SET name = %s, price = %s, cost = %s, stock = %s, 
                        category = %s, barcode = %s 
                    WHERE id = %s
                """
                self.cursor.execute(query, (name, price, cost, stock, category, barcode, product_id))
                self.connection.commit()
                messagebox.showinfo("成功", "商品更新成功")
                product_window.destroy()
                self.load_products()
            except Error as e:
                messagebox.showerror("错误", f"更新商品失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=product_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def delete_product(self):
        """删除商品"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要删除的商品")
            return
        
        item = self.product_tree.item(selected_item[0])
        values = item['values']
        
        product_id = values[0]
        product_name = values[1]
        
        confirm = messagebox.askyesno("确认", f"确定要删除商品 '{product_name}' 吗？")
        if not confirm:
            return
        
        try:
            # 检查是否有关联订单
            query = "SELECT COUNT(*) as count FROM sales_order_items WHERE product_id = %s"
            self.cursor.execute(query, (product_id,))
            result = self.cursor.fetchone()
            
            if result['count'] > 0:
                messagebox.showerror("错误", "该商品有关联订单，不能删除")
                return
            
            query = "DELETE FROM products WHERE id = %s"
            self.cursor.execute(query, (product_id,))
            self.connection.commit()
            messagebox.showinfo("成功", "商品删除成功")
            self.load_products()
        except Error as e:
            messagebox.showerror("错误", f"删除商品失败: {e}")
    
    def add_customer(self):
        """添加客户"""
        customer_window = tk.Toplevel(self.root)
        customer_window.title("添加客户")
        customer_window.geometry("400x300")
        customer_window.resizable(False, False)
        
        # 客户信息框架
        frame = ttk.Frame(customer_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 客户名称
        ttk.Label(frame, text="客户名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5)
        
        # 电话
        ttk.Label(frame, text="电话:").grid(row=1, column=0, sticky=tk.W, pady=5)
        phone_var = tk.StringVar()
        ttk.Entry(frame, textvariable=phone_var, width=30).grid(row=1, column=1, pady=5)
        
        # 邮箱
        ttk.Label(frame, text="邮箱:").grid(row=2, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar()
        ttk.Entry(frame, textvariable=email_var, width=30).grid(row=2, column=1, pady=5)
        
        # 地址
        ttk.Label(frame, text="地址:").grid(row=3, column=0, sticky=tk.W, pady=5)
        address_var = tk.StringVar()
        ttk.Entry(frame, textvariable=address_var, width=30).grid(row=3, column=1, pady=5)
        
        # 积分
        ttk.Label(frame, text="积分:").grid(row=4, column=0, sticky=tk.W, pady=5)
        points_var = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=points_var, width=30).grid(row=4, column=1, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(customer_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def save_customer():
            name = name_var.get().strip()
            phone = phone_var.get().strip()
            email = email_var.get().strip()
            address = address_var.get().strip()
            points = points_var.get()
            
            if not name:
                messagebox.showerror("错误", "客户名称不能为空")
                return
            
            if not phone:
                messagebox.showerror("错误", "客户电话不能为空")
                return
            
            try:
                query = """
                    INSERT INTO customers (name, phone, email, address, points)
                    VALUES (%s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (name, phone, email, address, points))
                self.connection.commit()
                messagebox.showinfo("成功", "客户添加成功")
                customer_window.destroy()
                self.load_customers()
            except Error as e:
                messagebox.showerror("错误", f"添加客户失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=customer_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def edit_customer(self):
        """编辑客户"""
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要编辑的客户")
            return
        
        item = self.customer_tree.item(selected_item[0])
        values = item['values']
        
        customer_id = values[0]
        
        customer_window = tk.Toplevel(self.root)
        customer_window.title("编辑客户")
        customer_window.geometry("400x300")
        customer_window.resizable(False, False)
        
        # 客户信息框架
        frame = ttk.Frame(customer_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 客户名称
        ttk.Label(frame, text="客户名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=values[1])
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5)
        
        # 电话
        ttk.Label(frame, text="电话:").grid(row=1, column=0, sticky=tk.W, pady=5)
        phone_var = tk.StringVar(value=values[2])
        ttk.Entry(frame, textvariable=phone_var, width=30).grid(row=1, column=1, pady=5)
        
        # 邮箱
        ttk.Label(frame, text="邮箱:").grid(row=2, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=values[3])
        ttk.Entry(frame, textvariable=email_var, width=30).grid(row=2, column=1, pady=5)
        
        # 地址
        ttk.Label(frame, text="地址:").grid(row=3, column=0, sticky=tk.W, pady=5)
        address_var = tk.StringVar(value=values[4])
        ttk.Entry(frame, textvariable=address_var, width=30).grid(row=3, column=1, pady=5)
        
        # 积分
        ttk.Label(frame, text="积分:").grid(row=4, column=0, sticky=tk.W, pady=5)
        points_var = tk.IntVar(value=values[5])
        ttk.Entry(frame, textvariable=points_var, width=30).grid(row=4, column=1, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(customer_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def update_customer():
            name = name_var.get().strip()
            phone = phone_var.get().strip()
            email = email_var.get().strip()
            address = address_var.get().strip()
            points = points_var.get()
            
            if not name:
                messagebox.showerror("错误", "客户名称不能为空")
                return
            
            if not phone:
                messagebox.showerror("错误", "客户电话不能为空")
                return
            
            try:
                query = """
                    UPDATE customers 
                    SET name = %s, phone = %s, email = %s, address = %s, points = %s 
                    WHERE id = %s
                """
                self.cursor.execute(query, (name, phone, email, address, points, customer_id))
                self.connection.commit()
                messagebox.showinfo("成功", "客户更新成功")
                customer_window.destroy()
                self.load_customers()
            except Error as e:
                messagebox.showerror("错误", f"更新客户失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=update_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=customer_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def delete_customer(self):
        """删除客户"""
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要删除的客户")
            return
        
        item = self.customer_tree.item(selected_item[0])
        values = item['values']
        
        customer_id = values[0]
        customer_name = values[1]
        
        confirm = messagebox.askyesno("确认", f"确定要删除客户 '{customer_name}' 吗？")
        if not confirm:
            return
        
        try:
            # 检查是否有关联订单
            query = "SELECT COUNT(*) as count FROM sales_orders WHERE customer_id = %s"
            self.cursor.execute(query, (customer_id,))
            result = self.cursor.fetchone()
            
            if result['count'] > 0:
                messagebox.showerror("错误", "该客户有关联订单，不能删除")
                return
            
            query = "DELETE FROM customers WHERE id = %s"
            self.cursor.execute(query, (customer_id,))
            self.connection.commit()
            messagebox.showinfo("成功", "客户删除成功")
            self.load_customers()
        except Error as e:
            messagebox.showerror("错误", f"删除客户失败: {e}")
    
    def create_order(self):
        """创建订单"""
        order_window = tk.Toplevel(self.root)
        order_window.title("创建订单")
        order_window.geometry("800x600")
        order_window.resizable(True, True)
        
        # 客户选择框架
        customer_frame = ttk.LabelFrame(order_window, text="选择客户", padding=10)
        customer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(customer_frame, text="客户:").pack(side=tk.LEFT, padx=5)
        
        # 加载客户下拉框
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(customer_frame, textvariable=customer_var, width=30)
        customer_combo.pack(side=tk.LEFT, padx=5)
        
        # 加载客户数据
        try:
            query = "SELECT id, name FROM customers ORDER BY name"
            self.cursor.execute(query)
            customers = self.cursor.fetchall()
            
            customer_dict = {f"{c['name']} ({c['id']})": c['id'] for c in customers}
            customer_combo['values'] = list(customer_dict.keys())
            
            if customers:
                customer_combo.current(0)
        except Error as e:
            messagebox.showerror("错误", f"加载客户数据失败: {e}")
        
        # 商品选择框架
        product_frame = ttk.LabelFrame(order_window, text="添加商品", padding=10)
        product_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(product_frame, text="商品:").pack(side=tk.LEFT, padx=5)
        
        # 加载商品下拉框
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(product_frame, textvariable=product_var, width=25)
        product_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(product_frame, text="数量:").pack(side=tk.LEFT, padx=5)
        
        quantity_var = tk.IntVar(value=1)
        ttk.Entry(product_frame, textvariable=quantity_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # 加载商品数据
        try:
            query = "SELECT id, name, price FROM products ORDER BY name"
            self.cursor.execute(query)
            products = self.cursor.fetchall()
            
            product_dict = {f"{p['name']} - ¥{p['price']} ({p['id']})": (p['id'], p['price']) for p in products}
            product_combo['values'] = list(product_dict.keys())
            
            if products:
                product_combo.current(0)
        except Error as e:
            messagebox.showerror("错误", f"加载商品数据失败: {e}")
        
        # 添加商品按钮
        def add_product_to_order():
            product_text = product_combo.get()
            if not product_text:
                return
                
            quantity = quantity_var.get()
            if quantity <= 0:
                messagebox.showinfo("提示", "数量必须大于0")
                return
                
            product_id, price = product_dict[product_text]
            product_name = product_text.split(" - ")[0]
            
            # 检查是否已添加该商品
            for item in order_items_tree.get_children():
                if order_items_tree.item(item)['values'][0] == product_id:
                    messagebox.showinfo("提示", "该商品已添加到订单中")
                    return
            
            # 检查库存是否足够
            try:
                self.cursor.execute("""
                    SELECT IFNULL(quantity, 0) AS current_stock 
                    FROM inventory 
                    WHERE product_id = %s
                """, (product_id,))
                
                result = self.cursor.fetchone()
                if not result:
                    messagebox.showinfo("提示", f"商品 '{product_name}' 库存信息不存在")
                    return
                    
                current_stock = result['current_stock']
                
                if current_stock < quantity:
                    messagebox.showinfo("库存不足", f"商品 '{product_name}' 库存不足\n需要: {quantity}, 当前库存: {current_stock}")
                    return
            except Error as e:
                messagebox.showerror("错误", f"检查库存失败: {e}")
                return
            
            order_items_tree.insert("", "end", values=(
                product_id, 
                product_name, 
                price,
                quantity,
                price * quantity
            ))
            
            update_order_total()
        
        ttk.Button(product_frame, text="添加", command=add_product_to_order).pack(side=tk.LEFT, padx=5)
        
        # 订单商品表格
        columns = ("product_id", "product_name", "price", "quantity", "subtotal")
        order_items_tree = ttk.Treeview(order_window, columns=columns, show="headings")
        
        for col in columns:
            if col == "product_id":
                order_items_tree.heading(col, text="ID")
                order_items_tree.column(col, width=40)
            elif col == "product_name":
                order_items_tree.heading(col, text="商品名称")
                order_items_tree.column(col, width=180)
            elif col == "price":
                order_items_tree.heading(col, text="单价")
                order_items_tree.column(col, width=70)
            elif col == "quantity":
                order_items_tree.heading(col, text="数量")
                order_items_tree.column(col, width=70)
            else:
                order_items_tree.heading(col, text="小计")
                order_items_tree.column(col, width=80)
        
        order_items_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 删除选中商品
        def remove_selected_product():
            selected_item = order_items_tree.selection()
            if not selected_item:
                return
                
            order_items_tree.delete(selected_item[0])
            update_order_total()
        
        ttk.Button(order_window, text="删除选中商品", command=remove_selected_product).pack(anchor=tk.W, padx=10, pady=5)
        
        # 订单总计框架
        total_frame = ttk.Frame(order_window)
        total_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(total_frame, text="折扣:").pack(side=tk.LEFT, padx=5)
        
        discount_var = tk.DoubleVar(value=0)
        ttk.Entry(total_frame, textvariable=discount_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(total_frame, text="总计:").pack(side=tk.RIGHT, padx=5)
        
        total_var = tk.StringVar(value="¥0.00")
        ttk.Label(total_frame, textvariable=total_var, font=("Arial", 12, "bold")).pack(side=tk.RIGHT, padx=5)
        
        def update_order_total():
            total = 0
            for item in order_items_tree.get_children():
                subtotal = float(order_items_tree.item(item)['values'][4])
                total += subtotal
                
            discount = discount_var.get()
            final_total = total - discount
            
            total_var.set(f"¥{final_total:.2f}")
        
        # 支付方式
        payment_frame = ttk.Frame(order_window)
        payment_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(payment_frame, text="支付方式:").pack(side=tk.LEFT, padx=5)
        
        payment_var = tk.StringVar(value="cash")
        payment_methods = ["cash", "card", "online"]
        
        for method in payment_methods:
            ttk.Radiobutton(payment_frame, text=method.capitalize(), variable=payment_var, value=method).pack(side=tk.LEFT, padx=10)
        
        # 保存订单
        def save_order():
            customer_text = customer_combo.get()
            if not customer_text:
                messagebox.showerror("错误", "请选择客户")
                return
                
            customer_id = customer_dict[customer_text]
            
            items = order_items_tree.get_children()
            if not items:
                messagebox.showerror("错误", "订单不能为空")
                return
                
            total = 0
            for item in items:
                subtotal = float(order_items_tree.item(item)['values'][4])
                total += subtotal
                
            discount = discount_var.get()
            final_total = total - discount
            
            if final_total < 0:
                messagebox.showerror("错误", "折扣不能大于商品总价")
                return
                
            payment_method = payment_var.get()
            
            try:
                # 在开始新事务前先回滚任何未完成的事务
                try:
                    self.connection.rollback()
                except:
                    pass
                
                # 开始事务
                self.connection.start_transaction()
                
                # 检查库存是否足够
                insufficient_stock = []
                
                for item in items:
                    values = order_items_tree.item(item)['values']
                    product_id = values[0]
                    product_name = values[1]
                    quantity = values[3]
                    
                    # 查询当前库存
                    self.cursor.execute("""
                        SELECT IFNULL(quantity, 0) AS current_stock 
                        FROM inventory 
                        WHERE product_id = %s
                    """, (product_id,))
                    
                    result = self.cursor.fetchone()
                    if not result:
                        insufficient_stock.append(f"{product_name} - 库存信息不存在")
                        continue
                        
                    current_stock = result['current_stock']
                    
                    if current_stock < quantity:
                        insufficient_stock.append(f"{product_name} - 需要: {quantity}, 库存: {current_stock}")
                
                # 如果有库存不足的商品，显示错误并终止
                if insufficient_stock:
                    self.connection.rollback()
                    error_message = "以下商品库存不足:\n\n" + "\n".join(insufficient_stock)
                    messagebox.showerror("库存不足", error_message)
                    return
                
                # 插入订单头
                query = """
                    INSERT INTO sales_orders (customer_id, total_amount, discount, final_amount, payment_method, status)
                    VALUES (%s, %s, %s, %s, %s, 'completed')
                """
                self.cursor.execute(query, (customer_id, total, discount, final_total, payment_method))
                
                order_id = self.cursor.lastrowid
                
                # 插入订单明细
                for item in items:
                    values = order_items_tree.item(item)['values']
                    product_id = values[0]
                    quantity = values[3]
                    price = values[2]
                    subtotal = values[4]
                    
                    query = """
                        INSERT INTO sales_order_items (order_id, product_id, quantity, price, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(query, (order_id, product_id, quantity, price, subtotal))
                    
                    # 更新商品库存
                    self.cursor.execute("""
                        UPDATE inventory 
                        SET quantity = quantity - %s 
                        WHERE product_id = %s
                    """, (quantity, product_id))
                    
                    # 更新products表中的stock字段，保持一致性
                    self.cursor.execute("""
                        UPDATE products 
                        SET stock = (SELECT quantity FROM inventory WHERE product_id = %s) 
                        WHERE id = %s
                    """, (product_id, product_id))
                
                # 提交事务
                self.connection.commit()
                messagebox.showinfo("成功", f"订单创建成功，订单号: {order_id}")
                order_window.destroy()
                self.load_orders()
                # 刷新库存状态
                self.load_inventory_status()
            except Error as e:
                # 回滚事务
                self.connection.rollback()
                messagebox.showerror("错误", f"创建订单失败: {e}")
        
        # 按钮框架
        button_frame = ttk.Frame(order_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="保存订单", command=save_order).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=order_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def view_order_details(self):
        """查看订单详情"""
        selected_item = self.order_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要查看的订单")
            return
        
        item = self.order_tree.item(selected_item[0])
        values = item['values']
        
        order_id = values[0]
        
        try:
            # 获取订单基本信息
            query = """
                SELECT 
                    so.*,
                    c.name AS customer_name,
                    c.phone AS customer_phone
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.id
                WHERE so.id = %s
            """
            self.cursor.execute(query, (order_id,))
            order = self.cursor.fetchone()
            
            if not order:
                messagebox.showinfo("提示", "订单不存在")
                return
                
            # 获取订单商品明细
            query = """
                SELECT 
                    soi.*,
                    p.name AS product_name
                FROM sales_order_items soi
                JOIN products p ON soi.product_id = p.id
                WHERE soi.order_id = %s
            """
            self.cursor.execute(query, (order_id,))
            items = self.cursor.fetchall()
            
            # 创建订单详情窗口
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"订单详情 #{order_id}")
            detail_window.geometry("800x600")
            detail_window.resizable(True, True)
            
            # 订单基本信息
            info_frame = ttk.LabelFrame(detail_window, text="订单信息", padding=10)
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(info_frame, text=f"订单号: {order['id']}").grid(row=0, column=0, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=f"客户: {order['customer_name']} ({order['customer_phone']})").grid(row=0, column=1, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=f"创建时间: {order['created_at']}").grid(row=1, column=0, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=f"支付方式: {order['payment_method'].capitalize()}").grid(row=1, column=1, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=f"状态: {order['status'].capitalize()}").grid(row=2, column=0, sticky=tk.W, pady=2)
            
            ttk.Label(info_frame, text=f"商品总价: ¥{order['total_amount']:.2f}").grid(row=2, column=1, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=f"折扣: ¥{order['discount']:.2f}").grid(row=3, column=0, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=f"实付金额: ¥{order['final_amount']:.2f}", font=("Arial", 10, "bold")).grid(row=3, column=1, sticky=tk.W, pady=2)
            
            # 订单商品表格
            columns = ("product_id", "product_name", "price", "quantity", "subtotal")
            items_tree = ttk.Treeview(detail_window, columns=columns, show="headings")
            
            for col in columns:
                if col == "product_id":
                    items_tree.heading(col, text="ID")
                    items_tree.column(col, width=40)
                elif col == "product_name":
                    items_tree.heading(col, text="商品名称")
                    items_tree.column(col, width=250)
                elif col == "price":
                    items_tree.heading(col, text="单价")
                    items_tree.column(col, width=80)
                elif col == "quantity":
                    items_tree.heading(col, text="数量")
                    items_tree.column(col, width=80)
                else:
                    items_tree.heading(col, text="小计")
                    items_tree.column(col, width=80)
            
            items_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 填充商品数据
            for item in items:
                items_tree.insert("", "end", values=(
                    item['product_id'],
                    item['product_name'],
                    item['price'],
                    item['quantity'],
                    item['subtotal']
                ))
            
            ttk.Button(detail_window, text="关闭", command=detail_window.destroy).pack(pady=10)
            
        except Error as e:
            messagebox.showerror("错误", f"获取订单详情失败: {e}")
    
    def update_order_status(self):
        """更新订单状态"""
        selected_item = self.order_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要更新的订单")
            return
        
        item = self.order_tree.item(selected_item[0])
        values = item['values']
        
        order_id = values[0]
        current_status = values[6]
        
        if current_status == "cancelled":
            messagebox.showinfo("提示", "已取消的订单不能再更新状态")
            return
            
        new_status = simpledialog.askstring(
            "更新订单状态", 
            "请输入新状态 (pending/completed):",
            initialvalue=current_status
        )
        
        if not new_status:
            return
            
        new_status = new_status.lower().strip()
        if new_status not in ["pending", "completed", "cancelled"]:
            messagebox.showinfo("提示", "无效的订单状态")
            return
            
        if new_status == current_status:
            messagebox.showinfo("提示", "新状态与当前状态相同")
            return
            
        confirm = messagebox.askyesno("确认", f"确定要将订单状态从 '{current_status}' 更新为 '{new_status}' 吗？")
        if not confirm:
            return
            
        try:
            # 开始事务
            self.connection.start_transaction()
            
            # 如果是取消订单，需要恢复库存
            if new_status == "cancelled" and current_status != "cancelled":
                # 获取订单项
                self.cursor.execute("""
                    SELECT product_id, quantity FROM sales_order_items
                    WHERE order_id = %s
                """, (order_id,))
                order_items = self.cursor.fetchall()
                
                # 恢复库存
                for item in order_items:
                    product_id = item['product_id']
                    quantity = item['quantity']
                    
                    # 更新库存
                    self.cursor.execute("""
                        UPDATE inventory SET quantity = quantity + %s
                        WHERE product_id = %s
                    """, (quantity, product_id))
                    
                    # 记录库存日志
                    self.cursor.execute("""
                        INSERT INTO inventory_logs (
                            product_id, 
                            change_type, 
                            quantity, 
                            quantity_change,
                            reference_id, 
                            reference_type,
                            before_quantity,
                            after_quantity,
                            notes
                        )
                        SELECT 
                            %s,
                            'adjustment',
                            quantity,
                            %s,
                            %s,
                            'sales_order',
                            quantity - %s,
                            quantity,
                            CONCAT('订单 #', %s, ' 已取消')
                        FROM inventory
                        WHERE product_id = %s
                    """, (product_id, quantity, order_id, quantity, order_id, product_id))
            
            # 更新订单状态
            self.cursor.execute("UPDATE sales_orders SET status = %s WHERE id = %s", (new_status, order_id))
            
            # 提交事务
            self.connection.commit()
            messagebox.showinfo("成功", "订单状态更新成功")
            self.load_orders()
        except Error as e:
            # 回滚事务
            self.connection.rollback()
            messagebox.showerror("错误", f"更新订单状态失败: {e}")
            
            # 显示详细错误信息并尝试修复
            error_msg = str(e)
            if "remaining_quantity" in error_msg:
                try:
                    # 删除可能存在问题的触发器
                    self.cursor.execute("SHOW TRIGGERS WHERE `Table` = 'sales_orders'")
                    triggers = self.cursor.fetchall()
                    for trigger in triggers:
                        trigger_name = trigger.get('Trigger')
                        if trigger_name:
                            self.cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                    
                    self.connection.commit()
                    messagebox.showinfo("提示", "检测到问题触发器并已尝试移除，请再次尝试更新订单状态")
                except Error as e2:
                    messagebox.showerror("错误", f"尝试修复触发器失败: {e2}")
    
    def load_inventory_status(self):
        """加载库存状态数据"""
        # 清空现有数据
        try:
            for item in self.inventory_tree.get_children():
                self.inventory_tree.delete(item)
            
            # 检查数据库连接
            if not self.connection.is_connected():
                try:
                    self.connection = mysql.connector.connect(**self.db_config)
                    self.cursor = self.connection.cursor(dictionary=True)
                except Error as e:
                    messagebox.showerror("错误", f"数据库重新连接失败: {e}")
                    return
            
            # 检查视图是否存在
            try:
                self.cursor.execute("SHOW TABLES LIKE 'product_inventory_status'")
                if not self.cursor.fetchone():
                    # 创建product_inventory_status视图 - 使用与现有视图相同的列名
                    self.cursor.execute("""
                        CREATE OR REPLACE VIEW product_inventory_status AS
                        SELECT 
                            p.id AS product_id,
                            p.name AS product_name,
                            p.price AS price,
                            p.category AS category,
                            IFNULL(i.quantity, 0) AS current_stock,
                            CASE 
                                WHEN IFNULL(i.quantity, 0) <= IFNULL(i.min_stock_level, 10) THEN '不足'
                                WHEN IFNULL(i.quantity, 0) >= IFNULL(i.max_stock_level, 100) THEN '过多'
                                ELSE '充足'
                            END AS stock_status
                        FROM 
                            products p
                        LEFT JOIN 
                            inventory i ON p.id = i.product_id
                    """)
                    self.connection.commit()
            except Error as e:
                messagebox.showerror("错误", f"检查或创建视图失败: {e}")
                return
            
            # 检查inventory表是否有数据
            try:
                self.cursor.execute("SELECT COUNT(*) as count FROM inventory")
                count = self.cursor.fetchone()['count']
                
                if count == 0:
                    # 初始化库存数据
                    self.cursor.execute("""
                        INSERT INTO inventory (product_id, quantity, min_stock_level, max_stock_level)
                        SELECT id, stock, 10, 100 FROM products
                        ON DUPLICATE KEY UPDATE 
                            quantity = products.stock,
                            min_stock_level = 10,
                            max_stock_level = 100
                    """)
                    self.connection.commit()
            except Error as e:
                messagebox.showerror("错误", f"检查或初始化库存表失败: {e}")
                return
            
            # 加载数据
            try:
                # 不使用ORDER BY子句
                query = "SELECT * FROM product_inventory_status"
                self.cursor.execute(query)
                inventory_items = self.cursor.fetchall()
                
                if not inventory_items:
                    self.inventory_status_var.set("没有库存数据")
                    return
                
                for item in inventory_items:
                    # 使用正确的列名
                    values = (
                        item['product_id'],
                        item['product_name'],
                        item['category'] if 'category' in item else '',
                        '',  # barcode列不存在，使用空字符串
                        item['current_stock'],
                        10,  # min_stock_level列不存在，使用默认值
                        100,  # max_stock_level列不存在，使用默认值
                        item['stock_status'],
                        item['price'],
                        0.0,  # cost列不存在，使用默认值
                        None  # last_updated列不存在，使用None
                    )
                    
                    # 根据库存状态设置行颜色
                    tag = item['stock_status']
                    self.inventory_tree.insert("", "end", values=values, tags=(tag,))
                
                self.inventory_status_var.set(f"共 {len(inventory_items)} 条记录")
            except Error as e:
                messagebox.showerror("错误", f"查询库存数据失败: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"加载库存状态时发生未知错误: {e}")
    
    def search_inventory(self):
        """搜索库存"""
        search_term = self.inventory_search_var.get().strip()
        if not search_term:
            self.load_inventory_status()
            return
        
        # 清空现有数据
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        try:
            # 使用正确的列名进行查询
            query = """
                SELECT * FROM product_inventory_status 
                WHERE product_name LIKE %s OR category LIKE %s OR stock_status LIKE %s
                ORDER BY product_id
            """
            search_pattern = f"%{search_term}%"
            self.cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            inventory_items = self.cursor.fetchall()
            
            for item in inventory_items:
                # 使用正确的列名构建显示值
                values = (
                    item['product_id'],
                    item['product_name'],
                    item['category'],
                    '',  # barcode列不存在，使用空字符串
                    item['current_stock'],
                    10,  # min_stock_level列不存在，使用默认值
                    100,  # max_stock_level列不存在，使用默认值
                    item['stock_status'],
                    item['price'],
                    0.0,  # cost列不存在，使用默认值
                    None  # last_updated列不存在，使用None
                )
                
                # 根据库存状态设置行颜色
                tag = item['stock_status']
                self.inventory_tree.insert("", "end", values=values, tags=(tag,))
            
            self.inventory_status_var.set(f"找到 {len(inventory_items)} 条记录")
        except Error as e:
            messagebox.showerror("错误", f"搜索库存失败: {e}")
    
    def adjust_inventory(self):
        """调整库存"""
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要调整的商品")
            return
        
        item = self.inventory_tree.item(selected_item[0])
        values = item['values']
        
        product_id = values[0]
        product_name = values[1]
        current_stock = values[4]
        
        # 创建调整库存窗口
        adjust_window = tk.Toplevel(self.root)
        adjust_window.title(f"调整库存 - {product_name}")
        adjust_window.geometry("400x250")
        adjust_window.resizable(False, False)
        
        # 当前库存
        ttk.Label(adjust_window, text=f"当前库存: {current_stock}").pack(pady=10)
        
        # 新库存数量
        quantity_frame = ttk.Frame(adjust_window)
        quantity_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(quantity_frame, text="新库存数量:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        quantity_var = tk.IntVar(value=current_stock)
        quantity_entry = ttk.Entry(quantity_frame, textvariable=quantity_var, width=10)
        quantity_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 调整原因
        notes_frame = ttk.Frame(adjust_window)
        notes_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(notes_frame, text="调整原因:").grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)
        notes_var = tk.StringVar()
        notes_entry = ttk.Entry(notes_frame, textvariable=notes_var, width=30)
        notes_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        def save_adjustment():
            new_quantity = quantity_var.get()
            notes = notes_var.get().strip()
            
            if new_quantity < 0:
                messagebox.showinfo("提示", "库存数量不能为负数")
                return
                
            if not notes:
                messagebox.showinfo("提示", "请输入调整原因")
                return
            
            try:
                # 调用存储过程调整库存
                query = "CALL adjust_inventory(%s, %s, %s)"
                self.cursor.execute(query, (product_id, new_quantity, notes))
                self.connection.commit()
                messagebox.showinfo("成功", "库存调整成功")
                adjust_window.destroy()
                
                # 刷新库存状态和商品列表
                self.load_inventory_status()
                self.load_products()  # 添加刷新商品列表
            except Error as e:
                messagebox.showerror("错误", f"库存调整失败: {e}")
        
        # 按钮框架
        button_frame = ttk.Frame(adjust_window)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="保存", command=save_adjustment).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=adjust_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def export_inventory_report(self):
        """导出库存报表"""
        # 创建导出窗口
        export_window = tk.Toplevel(self.root)
        export_window.title("导出库存报表")
        export_window.geometry("600x450")  # 进一步增加窗口尺寸
        export_window.resizable(True, True)  # 允许调整大小
        
        # 报表类型
        report_frame = ttk.Frame(export_window)
        report_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(report_frame, text="报表类型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        report_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(report_frame, text="所有商品", variable=report_type_var, value="all").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(report_frame, text="库存不足", variable=report_type_var, value="low").grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(report_frame, text="库存过多", variable=report_type_var, value="high").grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 文件名和路径
        file_frame = ttk.Frame(export_window)
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(file_frame, text="文件名:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        filename_var = tk.StringVar(value=f"inventory_report_{datetime.datetime.now().strftime('%Y%m%d')}.csv")
        filename_entry = ttk.Entry(file_frame, textvariable=filename_var, width=30)
        filename_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 显示完整文件路径
        path_var = tk.StringVar(value=os.path.abspath(os.path.join(os.getcwd(), filename_var.get())))
        ttk.Label(file_frame, text="保存位置:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        path_label = ttk.Label(file_frame, textvariable=path_var, foreground="blue")
        path_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 当文件名变化时更新路径显示
        def update_path(*args):
            path_var.set(os.path.abspath(os.path.join(os.getcwd(), filename_var.get())))
        
        filename_var.trace("w", update_path)
        
        # 添加选择保存位置按钮
        def select_save_path():
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv")],
                initialfile=filename_var.get()
            )
            if file_path:
                filename_var.set(os.path.basename(file_path))
                path_var.set(file_path)
        
        ttk.Button(file_frame, text="选择位置", command=select_save_path).grid(row=0, column=2, padx=5, pady=5)
        
        def confirm_export():
            """确认导出前的操作"""
            report_type = report_type_var.get()
            filename = path_var.get().strip()  # 使用完整路径
            
            if not filename:
                messagebox.showinfo("提示", "请输入文件名")
                return
                
            try:
                # 根据报表类型获取数据
                if report_type == "all":
                    query = "SELECT * FROM product_inventory_status ORDER BY product_id"
                    self.cursor.execute(query)
                elif report_type == "low":
                    query = "SELECT * FROM product_inventory_status WHERE stock_status = '不足' ORDER BY product_id"
                    self.cursor.execute(query)
                else:  # high
                    query = "SELECT * FROM product_inventory_status WHERE stock_status = '过多' ORDER BY product_id"
                    self.cursor.execute(query)
                    
                inventory_items = self.cursor.fetchall()
                
                if not inventory_items:
                    messagebox.showinfo("提示", "没有符合条件的数据")
                    return
                
                # 显示确认按钮并禁用其他按钮
                confirm_button.config(state=tk.NORMAL)
                export_button.config(state=tk.DISABLED)
                
                # 显示数据预览信息
                preview_text = f"找到 {len(inventory_items)} 条记录，点击确认导出"
                messagebox.showinfo("数据预览", preview_text)
                
                # 保存数据到预览区域
                preview_area.config(state=tk.NORMAL)
                preview_area.delete(1.0, tk.END)
                preview_area.insert(tk.END, f"预览: 共找到 {len(inventory_items)} 条记录\n\n")
                
                # 显示前5条记录
                preview_count = min(5, len(inventory_items))
                for i in range(preview_count):
                    item = inventory_items[i]
                    preview_area.insert(tk.END, f"{item['product_id']} - {item['product_name']} - {item['current_stock']}个 - {item['stock_status']}\n")
                
                if len(inventory_items) > 5:
                    preview_area.insert(tk.END, "...\n")
                
                preview_area.config(state=tk.DISABLED)
                
            except Exception as e:
                messagebox.showerror("错误", f"获取数据失败: {e}")
        
        def do_export():
            """执行导出操作"""
            report_type = report_type_var.get()
            filename = path_var.get().strip()  # 使用完整路径
            
            try:
                # 根据报表类型获取数据
                if report_type == "all":
                    query = "SELECT * FROM product_inventory_status ORDER BY product_id"
                    self.cursor.execute(query)
                elif report_type == "low":
                    query = "SELECT * FROM product_inventory_status WHERE stock_status = '不足' ORDER BY product_id"
                    self.cursor.execute(query)
                else:  # high
                    query = "SELECT * FROM product_inventory_status WHERE stock_status = '过多' ORDER BY product_id"
                    self.cursor.execute(query)
                    
                inventory_items = self.cursor.fetchall()
                
                # 导出为CSV
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    # 使用视图中实际存在的字段名
                    fieldnames = ['product_id', 'product_name', 'price', 'category', 'current_stock', 'stock_status']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # 写入自定义的表头
                    writer.writerow({
                        'product_id': '商品ID',
                        'product_name': '商品名称',
                        'price': '价格',
                        'category': '分类',
                        'current_stock': '当前库存',
                        'stock_status': '库存状态'
                    })
                    
                    # 写入数据行
                    for item in inventory_items:
                        writer.writerow(item)
                
                messagebox.showinfo("成功", f"报表已导出至:\n{filename}")
                
                # 询问是否打开文件
                if messagebox.askyesno("提示", "是否打开导出的文件?"):
                    import os
                    os.startfile(filename)
                
                export_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"导出报表失败: {e}")
        
        # 添加预览区域
        preview_frame = ttk.LabelFrame(export_window, text="数据预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        preview_area = tk.Text(preview_frame, height=5, width=50, state=tk.DISABLED)
        preview_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按钮框架 - 修改布局方式，确保按钮可见
        button_frame = ttk.Frame(export_window)
        button_frame.pack(fill=tk.X, padx=20, pady=20)  # 移除side=tk.BOTTOM
        
        # 使用pack布局替代grid，并调整顺序确保所有按钮都可见
        confirm_button = ttk.Button(button_frame, text="确认导出", command=do_export, state=tk.DISABLED)
        confirm_button.pack(side=tk.RIGHT, padx=5)
        
        export_button = ttk.Button(button_frame, text="预览", command=confirm_export)
        export_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="取消", command=export_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def load_inventory_logs(self):
        """加载库存日志"""
        # 清空现有数据
        for item in self.inventory_log_tree.get_children():
            self.inventory_log_tree.delete(item)
        
        try:
            # 获取库存日志
            query = """
                SELECT 
                    il.*,
                    p.name AS product_name
                FROM inventory_logs il
                JOIN products p ON il.product_id = p.id
                ORDER BY il.created_at DESC
                LIMIT 1000
            """
            self.cursor.execute(query)
            logs = self.cursor.fetchall()
            
            for log in logs:
                change_type_display = {
                    'in': '入库',
                    'out': '出库',
                    'adjustment': '调整',
                    'sale': '销售'
                }.get(log['change_type'], log['change_type'])
                
                reference_type_display = {
                    'stock_in': '入库单',
                    'stock_out': '出库单',
                    'adjustment': '库存调整',
                    'sales_order': '销售订单'
                }.get(log['reference_type'], log['reference_type'])
                
                values = (
                    log['id'],
                    log['product_name'],
                    change_type_display,
                    log['quantity'],
                    log['quantity_change'] if 'quantity_change' in log else 0,
                    reference_type_display,
                    log['before_quantity'],
                    log['after_quantity'],
                    log['notes'],
                    log['created_at']
                )
                
                self.inventory_log_tree.insert("", "end", values=values)
            
            self.inventory_log_status_var.set(f"显示最近 {len(logs)} 条记录")
        except Error as e:
            messagebox.showerror("错误", f"加载库存日志失败: {e}")
    
    def filter_inventory_logs(self):
        """筛选库存日志"""
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        
        # 清空现有数据
        for item in self.inventory_log_tree.get_children():
            self.inventory_log_tree.delete(item)
        
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if start_date:
                conditions.append("DATE(il.created_at) >= %s")
                params.append(start_date)
                
            if end_date:
                conditions.append("DATE(il.created_at) <= %s")
                params.append(end_date)
                
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 获取库存日志
            query = f"""
                SELECT 
                    il.*,
                    p.name AS product_name
                FROM inventory_logs il
                JOIN products p ON il.product_id = p.id
                WHERE {where_clause}
                ORDER BY il.created_at DESC
                LIMIT 1000
            """
            self.cursor.execute(query, params)
            logs = self.cursor.fetchall()
            
            for log in logs:
                change_type_display = {
                    'in': '入库',
                    'out': '出库',
                    'adjustment': '调整',
                    'sale': '销售'
                }.get(log['change_type'], log['change_type'])
                
                reference_type_display = {
                    'stock_in': '入库单',
                    'stock_out': '出库单',
                    'adjustment': '库存调整',
                    'sales_order': '销售订单'
                }.get(log['reference_type'], log['reference_type'])
                
                values = (
                    log['id'],
                    log['product_name'],
                    change_type_display,
                    log['quantity'],
                    log['quantity_change'] if 'quantity_change' in log else 0,
                    reference_type_display,
                    log['before_quantity'],
                    log['after_quantity'],
                    log['notes'],
                    log['created_at']
                )
                
                self.inventory_log_tree.insert("", "end", values=values)
            
            self.inventory_log_status_var.set(f"显示 {len(logs)} 条记录")
        except Error as e:
            messagebox.showerror("错误", f"筛选库存日志失败: {e}")
    
    def load_suppliers(self):
        """加载供应商数据"""
        # 清空现有数据
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)
        
        try:
            query = "SELECT * FROM suppliers ORDER BY id DESC"
            self.cursor.execute(query)
            suppliers = self.cursor.fetchall()
            
            for supplier in suppliers:
                values = (
                    supplier['id'],
                    supplier['name'],
                    supplier['contact_person'],
                    supplier['phone'],
                    supplier['email'],
                    supplier['address'],
                    supplier['created_at']
                )
                
                self.supplier_tree.insert("", "end", values=values)
            
            self.supplier_status_var.set(f"共 {len(suppliers)} 条记录")
        except Error as e:
            messagebox.showerror("错误", f"加载供应商数据失败: {e}")
    
    def search_suppliers(self):
        """搜索供应商"""
        search_term = self.supplier_search_var.get().strip()
        if not search_term:
            self.load_suppliers()
            return
        
        # 清空现有数据
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)
        
        try:
            query = """
                SELECT * FROM suppliers 
                WHERE name LIKE %s OR contact_person LIKE %s OR phone LIKE %s OR email LIKE %s OR address LIKE %s
                ORDER BY id DESC
            """
            search_pattern = f"%{search_term}%"
            self.cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
            suppliers = self.cursor.fetchall()
            
            for supplier in suppliers:
                values = (
                    supplier['id'],
                    supplier['name'],
                    supplier['contact_person'],
                    supplier['phone'],
                    supplier['email'],
                    supplier['address'],
                    supplier['created_at']
                )
                
                self.supplier_tree.insert("", "end", values=values)
            
            self.supplier_status_var.set(f"找到 {len(suppliers)} 条记录")
        except Error as e:
            messagebox.showerror("错误", f"搜索供应商失败: {e}")
    
    def add_supplier(self):
        """添加供应商"""
        # 创建添加供应商窗口
        add_window = tk.Toplevel(self.root)
        add_window.title("添加供应商")
        add_window.geometry("500x300")
        add_window.resizable(False, False)
        
        # 创建表单
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 供应商名称
        ttk.Label(form_frame, text="供应商名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 联系人
        ttk.Label(form_frame, text="联系人:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        contact_person_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=contact_person_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 电话
        ttk.Label(form_frame, text="电话:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        phone_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=phone_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 邮箱
        ttk.Label(form_frame, text="邮箱:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 地址
        ttk.Label(form_frame, text="地址:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        address_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=address_var, width=30).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        def save_supplier():
            name = name_var.get().strip()
            contact_person = contact_person_var.get().strip()
            phone = phone_var.get().strip()
            email = email_var.get().strip()
            address = address_var.get().strip()
            
            if not name:
                messagebox.showinfo("提示", "请输入供应商名称")
                return
            
            try:
                query = """
                    INSERT INTO suppliers (name, contact_person, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (name, contact_person, phone, email, address))
                self.connection.commit()
                
                messagebox.showinfo("成功", "供应商添加成功")
                add_window.destroy()
                self.load_suppliers()
            except Error as e:
                messagebox.showerror("错误", f"添加供应商失败: {e}")
        
        # 按钮框架
        button_frame = ttk.Frame(add_window)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="保存", command=save_supplier).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=add_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def edit_supplier(self):
        """编辑供应商"""
        selected_item = self.supplier_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要编辑的供应商")
            return
        
        item = self.supplier_tree.item(selected_item[0])
        values = item['values']
        
        supplier_id = values[0]
        
        try:
            # 获取供应商信息
            query = "SELECT * FROM suppliers WHERE id = %s"
            self.cursor.execute(query, (supplier_id,))
            supplier = self.cursor.fetchone()
            
            if not supplier:
                messagebox.showinfo("提示", "供应商不存在")
                return
            
            # 创建编辑供应商窗口
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"编辑供应商 - {supplier['name']}")
            edit_window.geometry("500x300")
            edit_window.resizable(False, False)
            
            # 创建表单
            form_frame = ttk.Frame(edit_window, padding=20)
            form_frame.pack(fill=tk.BOTH, expand=True)
            
            # 供应商名称
            ttk.Label(form_frame, text="供应商名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            name_var = tk.StringVar(value=supplier['name'])
            ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            # 联系人
            ttk.Label(form_frame, text="联系人:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            contact_person_var = tk.StringVar(value=supplier['contact_person'] if supplier['contact_person'] else "")
            ttk.Entry(form_frame, textvariable=contact_person_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            
            # 电话
            ttk.Label(form_frame, text="电话:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            phone_var = tk.StringVar(value=supplier['phone'] if supplier['phone'] else "")
            ttk.Entry(form_frame, textvariable=phone_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
            
            # 邮箱
            ttk.Label(form_frame, text="邮箱:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            email_var = tk.StringVar(value=supplier['email'] if supplier['email'] else "")
            ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
            
            # 地址
            ttk.Label(form_frame, text="地址:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            address_var = tk.StringVar(value=supplier['address'] if supplier['address'] else "")
            ttk.Entry(form_frame, textvariable=address_var, width=30).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
            
            def update_supplier():
                name = name_var.get().strip()
                contact_person = contact_person_var.get().strip()
                phone = phone_var.get().strip()
                email = email_var.get().strip()
                address = address_var.get().strip()
                
                if not name:
                    messagebox.showinfo("提示", "请输入供应商名称")
                    return
                
                try:
                    query = """
                        UPDATE suppliers 
                        SET name = %s, contact_person = %s, phone = %s, email = %s, address = %s
                        WHERE id = %s
                    """
                    self.cursor.execute(query, (name, contact_person, phone, email, address, supplier_id))
                    self.connection.commit()
                    
                    messagebox.showinfo("成功", "供应商更新成功")
                    edit_window.destroy()
                    self.load_suppliers()
                except Error as e:
                    messagebox.showerror("错误", f"更新供应商失败: {e}")
            
            # 按钮框架
            button_frame = ttk.Frame(edit_window)
            button_frame.pack(fill=tk.X, padx=20, pady=20)
            
            ttk.Button(button_frame, text="保存", command=update_supplier).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="取消", command=edit_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Error as e:
            messagebox.showerror("错误", f"获取供应商信息失败: {e}")
    
    def delete_supplier(self):
        """删除供应商"""
        selected_item = self.supplier_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要删除的供应商")
            return
        
        item = self.supplier_tree.item(selected_item[0])
        values = item['values']
        
        supplier_id = values[0]
        supplier_name = values[1]
        
        confirm = messagebox.askyesno("确认", f"确定要删除供应商 '{supplier_name}' 吗？")
        if not confirm:
            return
        
        try:
            query = "DELETE FROM suppliers WHERE id = %s"
            self.cursor.execute(query, (supplier_id,))
            self.connection.commit()
            
            messagebox.showinfo("成功", "供应商删除成功")
            self.load_suppliers()
        except Error as e:
            messagebox.showerror("错误", f"删除供应商失败: {e}")
    
    def create_triggers(self):
        """创建触发器"""
        try:
            # 检查并创建销售减库存触发器
            self.cursor.execute("SHOW TRIGGERS LIKE 'sales_reduce_inventory'")
            if not self.cursor.fetchone():
                try:
                    self.cursor.execute("""
                        CREATE TRIGGER sales_reduce_inventory
                        AFTER INSERT ON sales_order_items
                        FOR EACH ROW
                        BEGIN
                            UPDATE inventory SET quantity = quantity - NEW.quantity
                            WHERE product_id = NEW.product_id;
                        END
                    """)
                except Error:
                    pass
            
            self.connection.commit()
        except Error:
            # 触发器创建失败不影响系统运行
            pass
    
    def debug_database(self):
        """调试数据库问题"""
        debug_window = tk.Toplevel(self.root)
        debug_window.title("数据库调试")
        debug_window.geometry("800x600")
        
        # 创建文本区域
        text_area = tk.Text(debug_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text_area, orient="vertical", command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        def append_text(text):
            text_area.insert(tk.END, text + "\n")
            text_area.see(tk.END)
        
        try:
            # 检查数据库连接
            append_text("检查数据库连接...")
            if not self.connection.is_connected():
                append_text("数据库连接已断开，尝试重新连接...")
                try:
                    self.connection = mysql.connector.connect(**self.db_config)
                    self.cursor = self.connection.cursor(dictionary=True)
                    append_text("重新连接成功")
                except Error as e:
                    append_text(f"数据库重新连接失败: {e}")
                    return
            else:
                append_text("数据库连接正常")
            
            # 检查表是否存在
            tables = ["inventory", "inventory_logs"]
            append_text("\n检查表是否存在...")
            
            for table in tables:
                self.cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if self.cursor.fetchone():
                    append_text(f"表 {table} 存在")
                    
                    # 检查表结构
                    append_text(f"检查 {table} 表结构...")
                    self.cursor.execute(f"DESCRIBE {table}")
                    columns = self.cursor.fetchall()
                    for col in columns:
                        append_text(f"  {col['Field']} - {col['Type']} - {col['Key']}")
                    
                    # 检查表中的数据
                    append_text(f"检查 {table} 数据量...")
                    self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = self.cursor.fetchone()['count']
                    append_text(f"  {table} 表中有 {count} 条记录")
                else:
                    append_text(f"表 {table} 不存在")
            
            # 检查触发器
            append_text("\n检查触发器...")
            self.cursor.execute("SHOW TRIGGERS")
            triggers = self.cursor.fetchall()
            if triggers:
                for trigger in triggers:
                    append_text(f"触发器: {trigger['Trigger']} - {trigger['Event']} - {trigger['Table']}")
            else:
                append_text("没有找到触发器")
            
        except Error as e:
            append_text(f"调试过程中出错: {e}")
        
        # 添加创建表按钮
        def create_missing_tables():
            try:
                # 创建inventory表
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory (
                        product_id INT NOT NULL PRIMARY KEY,
                        quantity INT NOT NULL DEFAULT 0,
                        min_stock_level INT DEFAULT 10,
                        max_stock_level INT DEFAULT 100,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                """)
                
                # 初始化库存数据
                self.cursor.execute("""
                    INSERT INTO inventory (product_id, quantity, min_stock_level, max_stock_level)
                    SELECT id, stock, 10, 100 FROM products
                    ON DUPLICATE KEY UPDATE 
                        quantity = products.stock,
                        min_stock_level = 10,
                        max_stock_level = 100
                """)
                
                # 创建inventory_logs表
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_id INT NOT NULL,
                        change_type ENUM('in', 'out', 'adjustment', 'sale') NOT NULL,
                        quantity INT NOT NULL,
                        quantity_change INT NOT NULL,
                        reference_id INT,
                        reference_type ENUM('stock_in', 'stock_out', 'adjustment', 'sales_order') NOT NULL,
                        before_quantity INT NOT NULL,
                        after_quantity INT NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)
                
                self.connection.commit()
                append_text("\n所有缺失的表已创建")
                
                # 刷新调试信息
                text_area.delete(1.0, tk.END)
                self.debug_database()
                
            except Error as e:
                append_text(f"\n创建表失败: {e}")
        
        button_frame = ttk.Frame(debug_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="创建缺失的表", command=create_missing_tables).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="修复触发器", command=self.fix_triggers).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新", command=lambda: [text_area.delete(1.0, tk.END), self.debug_database()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=debug_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def fix_triggers(self):
        """检查和修复触发器问题"""
        try:
            # 检查数据库连接
            if not self.connection.is_connected():
                try:
                    self.connection = mysql.connector.connect(**self.db_config)
                    self.cursor = self.connection.cursor(dictionary=True)
                except Error as e:
                    messagebox.showerror("错误", f"数据库连接失败: {e}")
                    return
            
            # 删除可能存在问题的触发器
            triggers_to_drop = [
                "sales_reduce_inventory", 
                "sales_reduce_inventory_step",
                "after_sales_order_item_insert",
                "after_sales_order_item_insert_log"
            ]
            
            for trigger in triggers_to_drop:
                try:
                    self.cursor.execute(f"DROP TRIGGER IF EXISTS {trigger}")
                except:
                    pass
            
            # 创建销售订单触发器
            self.cursor.execute("""
                CREATE TRIGGER sales_reduce_inventory
                AFTER INSERT ON sales_order_items
                FOR EACH ROW
                BEGIN
                    UPDATE inventory 
                    SET quantity = quantity - NEW.quantity
                    WHERE product_id = NEW.product_id;
                END
            """)
            
            # 创建库存日志触发器
            self.cursor.execute("""
                CREATE TRIGGER after_sales_order_item_insert_log
                AFTER INSERT ON sales_order_items
                FOR EACH ROW
                BEGIN
                    INSERT INTO inventory_logs (
                        product_id, 
                        change_type, 
                        quantity, 
                        quantity_change,
                        reference_id, 
                        reference_type,
                        before_quantity,
                        after_quantity,
                        notes
                    )
                    SELECT 
                        NEW.product_id,
                        'sale',
                        NEW.quantity,
                        -NEW.quantity,
                        NEW.order_id,
                        'sales_order',
                        quantity + NEW.quantity,
                        quantity,
                        CONCAT('销售订单 #', NEW.order_id)
                    FROM inventory
                    WHERE product_id = NEW.product_id;
                END
            """)
            
            self.connection.commit()
            # 更新状态栏而不是显示弹窗
            self.status_var.set("触发器已修复")
            
        except Error as e:
            messagebox.showerror("错误", f"修复触发器失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RetailManagementSystem(root)
    root.mainloop()    