/*
 Navicat Premium Dump SQL

 Source Server         : MySQL
 Source Server Type    : MySQL
 Source Server Version : 90300 (9.3.0)
 Source Host           : localhost:3306
 Source Schema         : aa

 Target Server Type    : MySQL
 Target Server Version : 90300 (9.3.0)
 File Encoding         : 65001

 Date: 07/06/2025 18:32:23
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for customers
-- ----------------------------
DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `address` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `points` int NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `phone`(`phone` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of customers
-- ----------------------------
INSERT INTO `customers` VALUES (1, '张三', '13800138001', 'zhangsan@example.com', NULL, 500, '2025-06-06 00:25:19');
INSERT INTO `customers` VALUES (2, '李四', '13800138002', 'lisi@example.com', NULL, 200, '2025-06-06 00:25:19');
INSERT INTO `customers` VALUES (3, '王五', '13800138003', 'wangwu@example.com', NULL, 0, '2025-06-06 00:25:19');
INSERT INTO `customers` VALUES (4, '赵六', '13800138004', 'zhaoliu@example.com', NULL, 800, '2025-06-06 00:25:19');
INSERT INTO `customers` VALUES (5, '钱七', '13800138005', 'qianqi@example.com', NULL, 300, '2025-06-06 00:25:19');
INSERT INTO `customers` VALUES (6, '张力', '14725803556', 'zhangli@qq.com', '', 0, '2025-06-07 18:22:31');

-- ----------------------------
-- Table structure for inventory
-- ----------------------------
DROP TABLE IF EXISTS `inventory`;
CREATE TABLE `inventory`  (
  `product_id` int NOT NULL,
  `quantity` int NOT NULL DEFAULT 0,
  `min_stock_level` int NULL DEFAULT 10,
  `max_stock_level` int NULL DEFAULT 100,
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`) USING BTREE,
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of inventory
-- ----------------------------
INSERT INTO `inventory` VALUES (1, 50, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (2, 30, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (3, 30, 10, 100, '2025-06-07 17:36:06');
INSERT INTO `inventory` VALUES (4, 40, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (5, 14, 10, 100, '2025-06-07 18:15:23');
INSERT INTO `inventory` VALUES (6, 50, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (7, 50, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (8, 30, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (9, 99, 10, 100, '2025-06-07 18:31:18');
INSERT INTO `inventory` VALUES (10, 1000, 10, 100, '2025-06-07 16:40:05');
INSERT INTO `inventory` VALUES (11, 200, 10, 100, '2025-06-07 16:40:05');

-- ----------------------------
-- Table structure for inventory_logs
-- ----------------------------
DROP TABLE IF EXISTS `inventory_logs`;
CREATE TABLE `inventory_logs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `change_type` enum('in','out','adjustment','sale') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `quantity` int NOT NULL,
  `quantity_change` int NOT NULL,
  `reference_id` int NULL DEFAULT NULL,
  `reference_type` enum('stock_in','stock_out','adjustment','sales_order') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `before_quantity` int NOT NULL,
  `after_quantity` int NOT NULL,
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `product_id`(`product_id` ASC) USING BTREE,
  CONSTRAINT `inventory_logs_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of inventory_logs
-- ----------------------------
INSERT INTO `inventory_logs` VALUES (1, 2, 'adjustment', 0, 0, NULL, 'adjustment', 30, 30, '入库', '2025-06-07 16:48:19');
INSERT INTO `inventory_logs` VALUES (2, 3, 'adjustment', 10, 0, NULL, 'adjustment', 20, 30, '入库', '2025-06-07 17:36:06');
INSERT INTO `inventory_logs` VALUES (3, 5, 'sale', 1, -1, 6, 'sales_order', 15, 14, '销售订单 #6', '2025-06-07 18:15:23');
INSERT INTO `inventory_logs` VALUES (4, 9, 'sale', 1, -1, 7, 'sales_order', 100, 99, '销售订单 #7', '2025-06-07 18:31:18');

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `price` decimal(10, 2) NOT NULL,
  `cost` decimal(10, 2) NULL DEFAULT NULL,
  `stock` int NULL DEFAULT 0,
  `category` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `barcode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `barcode`(`barcode` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 17 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES (1, 'iPhone 14', 8999.00, 7500.00, 50, '手机', '100001', '2025-06-06 00:24:21');
INSERT INTO `products` VALUES (2, '华为 Mate 50', 6999.00, 5800.00, 30, '手机', '100002', '2025-06-06 00:24:21');
INSERT INTO `products` VALUES (3, '小米 Air 笔记本', 4999.00, 4200.00, 20, '电脑', '100003', '2025-06-06 00:24:21');
INSERT INTO `products` VALUES (4, 'Apple Watch Series 8', 3199.00, 2700.00, 40, '智能穿戴', '100004', '2025-06-06 00:24:21');
INSERT INTO `products` VALUES (5, '三星 Galaxy S23', 7999.00, 6800.00, 15, '手机', '100005', '2025-06-06 00:24:21');
INSERT INTO `products` VALUES (6, '方法', 30.00, 5.00, 50, '食品', '100009', '2025-06-06 00:38:33');
INSERT INTO `products` VALUES (7, '智能手机A', 2999.00, 1999.00, 50, '电子产品', 'SP001', '2025-06-06 19:20:23');
INSERT INTO `products` VALUES (8, '笔记本电脑B', 5999.00, 4500.00, 30, '电子产品', 'NB002', '2025-06-06 19:20:23');
INSERT INTO `products` VALUES (9, '办公椅C', 599.00, 299.00, 100, '家居', 'CH003', '2025-06-06 19:20:23');
INSERT INTO `products` VALUES (10, '矿泉水D', 2.00, 1.00, 1000, '饮料', 'WT004', '2025-06-06 19:20:23');
INSERT INTO `products` VALUES (11, '巧克力E', 15.00, 8.00, 200, '零食', 'CH005', '2025-06-06 19:20:23');

-- ----------------------------
-- Table structure for sales_order_items
-- ----------------------------
DROP TABLE IF EXISTS `sales_order_items`;
CREATE TABLE `sales_order_items`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  `price` decimal(10, 2) NOT NULL,
  `subtotal` decimal(10, 2) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `order_id`(`order_id` ASC) USING BTREE,
  INDEX `product_id`(`product_id` ASC) USING BTREE,
  CONSTRAINT `sales_order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `sales_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `sales_order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sales_order_items
-- ----------------------------
INSERT INTO `sales_order_items` VALUES (8, 6, 5, 1, 7999.00, 7999.00);
INSERT INTO `sales_order_items` VALUES (9, 7, 9, 1, 599.00, 599.00);

-- ----------------------------
-- Table structure for sales_orders
-- ----------------------------
DROP TABLE IF EXISTS `sales_orders`;
CREATE TABLE `sales_orders`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NULL DEFAULT NULL,
  `total_amount` decimal(10, 2) NOT NULL,
  `discount` decimal(10, 2) NULL DEFAULT NULL,
  `final_amount` decimal(10, 2) NOT NULL,
  `payment_method` enum('cash','card','online') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('pending','completed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `customer_id`(`customer_id` ASC) USING BTREE,
  CONSTRAINT `sales_orders_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sales_orders
-- ----------------------------
INSERT INTO `sales_orders` VALUES (1, 1, 12198.00, 100.00, 12098.00, 'online', 'completed', '2025-06-06 00:25:19');
INSERT INTO `sales_orders` VALUES (2, 1, 12198.00, 100.00, 12098.00, 'online', 'completed', '2025-06-06 00:25:30');
INSERT INTO `sales_orders` VALUES (3, 2, 6999.00, 0.00, 6999.00, 'card', 'completed', '2025-06-06 00:25:40');
INSERT INTO `sales_orders` VALUES (6, 3, 7999.00, 0.00, 7999.00, 'cash', 'completed', '2025-06-07 18:15:23');
INSERT INTO `sales_orders` VALUES (7, 2, 599.00, 0.00, 599.00, 'cash', 'completed', '2025-06-07 18:31:18');

-- ----------------------------
-- Table structure for suppliers
-- ----------------------------
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `contact_person` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of suppliers
-- ----------------------------
INSERT INTO `suppliers` VALUES (1, '王妈食品厂', '李丽', '17755366858', '46548', '南宁市', '2025-06-07 16:28:00', '2025-06-07 16:28:00');

-- ----------------------------
-- View structure for product_inventory_status
-- ----------------------------
DROP VIEW IF EXISTS `product_inventory_status`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `product_inventory_status` AS select `p`.`id` AS `product_id`,`p`.`name` AS `product_name`,`p`.`price` AS `price`,`p`.`category` AS `category`,`i`.`quantity` AS `current_stock`,(case when (`i`.`quantity` = 0) then '缺货' when (`i`.`quantity` < 10) then '库存不足' else '库存充足' end) AS `stock_status` from (`products` `p` join `inventory` `i` on((`p`.`id` = `i`.`product_id`)));

-- ----------------------------
-- Procedure structure for adjust_inventory
-- ----------------------------
DROP PROCEDURE IF EXISTS `adjust_inventory`;
delimiter ;;
CREATE PROCEDURE `adjust_inventory`(IN p_product_id INT,
                        IN p_quantity INT,
                        IN p_notes TEXT)
BEGIN
                        DECLARE current_qty INT;
                        
                        SELECT IFNULL(quantity, 0) INTO current_qty 
                        FROM inventory 
                        WHERE product_id = p_product_id;
                        
                        INSERT INTO inventory (product_id, quantity)
                        VALUES (p_product_id, p_quantity)
                        ON DUPLICATE KEY UPDATE 
                            quantity = p_quantity;
                        
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
                    END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table sales_order_items
-- ----------------------------
DROP TRIGGER IF EXISTS `sales_reduce_inventory`;
delimiter ;;
CREATE TRIGGER `sales_reduce_inventory` AFTER INSERT ON `sales_order_items` FOR EACH ROW BEGIN
                    UPDATE inventory 
                    SET quantity = quantity - NEW.quantity
                    WHERE product_id = NEW.product_id;
                END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table sales_order_items
-- ----------------------------
DROP TRIGGER IF EXISTS `after_sales_order_item_insert_log`;
delimiter ;;
CREATE TRIGGER `after_sales_order_item_insert_log` AFTER INSERT ON `sales_order_items` FOR EACH ROW BEGIN
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
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table sales_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `after_sales_order_cancel`;
delimiter ;;
CREATE TRIGGER `after_sales_order_cancel` AFTER UPDATE ON `sales_orders` FOR EACH ROW BEGIN
    IF OLD.status != 'cancelled' AND NEW.status = 'cancelled' THEN
        -- 恢复库存
        UPDATE inventory i
        JOIN sales_order_items soi ON i.product_id = soi.product_id
        SET i.quantity = i.quantity + soi.quantity
        WHERE soi.order_id = NEW.id;
        
        -- 记录库存日志
        INSERT INTO inventory_logs (product_id, quantity_change, remaining_quantity, operation_type, note)
        SELECT 
            soi.product_id,
            soi.quantity,
            i.quantity,
            'adjustment',
            CONCAT('订单取消恢复库存，订单ID:', NEW.id)
        FROM sales_order_items soi
        JOIN inventory i ON soi.product_id = i.product_id
        WHERE soi.order_id = NEW.id;
    END IF;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
