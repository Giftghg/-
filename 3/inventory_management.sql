-- 供应商表
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 修改products表，添加需要的字段
ALTER TABLE products
ADD COLUMN IF NOT EXISTS cost DECIMAL(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS stock INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT '',
ADD COLUMN IF NOT EXISTS barcode VARCHAR(50) DEFAULT '',
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 确保products表中有数据，如果没有则添加
INSERT IGNORE INTO products (name, price, cost, stock, category, barcode) VALUES
('智能手机A', 2999.00, 1999.00, 50, '电子产品', 'SP001'),
('笔记本电脑B', 5999.00, 4500.00, 30, '电子产品', 'NB002'),
('办公椅C', 599.00, 299.00, 100, '家居', 'CH003'),
('矿泉水D', 2.00, 1.00, 1000, '饮料', 'WT004'),
('巧克力E', 15.00, 8.00, 200, '零食', 'CH005');

-- 库存表（如果不存在）
CREATE TABLE IF NOT EXISTS inventory (
    product_id INT NOT NULL PRIMARY KEY,
    quantity INT NOT NULL DEFAULT 0,
    min_stock_level INT DEFAULT 10,
    max_stock_level INT DEFAULT 100,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 库存日志表（记录所有库存变动）
CREATE TABLE IF NOT EXISTS inventory_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    change_type ENUM('in', 'out', 'adjustment', 'sale') NOT NULL,
    quantity INT NOT NULL,
    reference_id INT,
    reference_type ENUM('stock_in', 'stock_out', 'adjustment', 'sales_order') NOT NULL,
    before_quantity INT NOT NULL,
    after_quantity INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 入库记录表
CREATE TABLE IF NOT EXISTS stock_in (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    reference_no VARCHAR(50),
    total_amount DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- 入库明细表
CREATE TABLE IF NOT EXISTS stock_in_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_in_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    cost_price DECIMAL(10, 2) NOT NULL,
    total_cost DECIMAL(10, 2) NOT NULL,
    notes VARCHAR(255),
    FOREIGN KEY (stock_in_id) REFERENCES stock_in(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 出库记录表（非销售出库，如损耗、赠品等）
CREATE TABLE IF NOT EXISTS stock_out (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_no VARCHAR(50),
    reason ENUM('damage', 'gift', 'internal_use', 'return', 'other') NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50)
);

-- 出库明细表
CREATE TABLE IF NOT EXISTS stock_out_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_out_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    notes VARCHAR(255),
    FOREIGN KEY (stock_out_id) REFERENCES stock_out(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 初始化库存数据
INSERT INTO inventory (product_id, quantity, min_stock_level, max_stock_level)
SELECT id, stock, 10, 100 FROM products
ON DUPLICATE KEY UPDATE 
    quantity = products.stock,
    min_stock_level = 10,
    max_stock_level = 100;

-- 添加示例数据
-- 插入供应商数据
INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES
('优质电子供应商', '张经理', '13800138001', 'zhang@supplier.com', '北京市海淀区科技园区123号'),
('全球食品批发', '李总', '13900139002', 'li@foods.com', '上海市浦东新区张江高科技园区456号'),
('家居用品批发商', '王经理', '13700137003', 'wang@home.com', '广州市天河区天河路789号');

-- 创建示例入库单
INSERT INTO stock_in (supplier_id, reference_no, total_amount, notes, status) VALUES
(1, 'IN-20230501-001', 10000.00, '5月第一批电子产品入库', 'completed'),
(2, 'IN-20230510-002', 2000.00, '5月食品饮料入库', 'completed'),
(3, 'IN-20230520-003', 3000.00, '5月家居用品入库', 'pending');

-- 创建入库明细
INSERT INTO stock_in_items (stock_in_id, product_id, quantity, cost_price, total_cost) VALUES
(1, 1, 20, 1999.00, 39980.00),
(1, 2, 10, 4500.00, 45000.00),
(2, 4, 500, 1.00, 500.00),
(2, 5, 100, 8.00, 800.00),
(3, 3, 50, 299.00, 14950.00);

-- 创建示例出库单
INSERT INTO stock_out (reference_no, reason, notes, created_by) VALUES
('OUT-20230605-001', 'damage', '损坏商品出库', '系统管理员'),
('OUT-20230610-002', 'gift', '赠品出库', '系统管理员');

-- 创建出库明细
INSERT INTO stock_out_items (stock_out_id, product_id, quantity, notes) VALUES
(1, 1, 2, '运输过程中损坏'),
(1, 3, 5, '仓库存放不当损坏'),
(2, 4, 50, '促销活动赠品'),
(2, 5, 20, '新客户赠品');

-- 创建视图：库存状态视图（包含预警信息）
CREATE OR REPLACE VIEW product_inventory_status AS
SELECT 
    p.id,
    p.name,
    p.category,
    p.barcode,
    IFNULL(i.quantity, 0) AS current_stock,
    IFNULL(i.min_stock_level, 10) AS min_stock_level,
    IFNULL(i.max_stock_level, 100) AS max_stock_level,
    CASE 
        WHEN IFNULL(i.quantity, 0) <= IFNULL(i.min_stock_level, 10) THEN '库存不足'
        WHEN IFNULL(i.quantity, 0) >= IFNULL(i.max_stock_level, 100) THEN '库存过多'
        ELSE '库存正常'
    END AS stock_status,
    p.price,
    p.cost,
    i.last_updated
FROM 
    products p
LEFT JOIN 
    inventory i ON p.id = i.product_id;

-- 创建存储过程：库存调整
DELIMITER //
CREATE PROCEDURE adjust_inventory(
    IN p_product_id INT,
    IN p_quantity INT,
    IN p_notes TEXT
)
BEGIN
    DECLARE current_qty INT;
    
    -- 获取当前库存
    SELECT IFNULL(quantity, 0) INTO current_qty 
    FROM inventory 
    WHERE product_id = p_product_id;
    
    -- 更新库存
    INSERT INTO inventory (product_id, quantity)
    VALUES (p_product_id, p_quantity)
    ON DUPLICATE KEY UPDATE 
        quantity = p_quantity;
    
    -- 记录库存日志
    INSERT INTO inventory_logs (
        product_id, 
        change_type, 
        quantity, 
        reference_type,
        before_quantity,
        after_quantity,
        notes
    )
    VALUES (
        p_product_id,
        'adjustment',
        p_quantity - current_qty,
        'adjustment',
        current_qty,
        p_quantity,
        p_notes
    );
END //
DELIMITER ;

-- 创建触发器：销售订单创建后自动减少库存
DELIMITER //
CREATE TRIGGER IF NOT EXISTS after_sales_order_item_insert
AFTER INSERT ON sales_order_items
FOR EACH ROW
BEGIN
    -- 更新库存
    UPDATE inventory 
    SET quantity = quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
    
    -- 记录库存日志
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
END //
DELIMITER ;

-- 创建触发器：入库完成后自动增加库存
DELIMITER //
CREATE TRIGGER IF NOT EXISTS after_stock_in_complete
AFTER UPDATE ON stock_in
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- 将所有入库明细项添加到库存中
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
        
        -- 更新库存数量
        INSERT INTO inventory (product_id, quantity)
        SELECT sii.product_id, sii.quantity
        FROM stock_in_items sii
        WHERE sii.stock_in_id = NEW.id
        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity);
    END IF;
END //
DELIMITER ;

-- 创建触发器：出库后自动减少库存
DELIMITER //
CREATE TRIGGER IF NOT EXISTS after_stock_out_item_insert
AFTER INSERT ON stock_out_items
FOR EACH ROW
BEGIN
    -- 更新库存
    UPDATE inventory 
    SET quantity = quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
    
    -- 记录库存日志
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
END //
DELIMITER ; 