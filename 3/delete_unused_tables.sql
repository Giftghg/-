-- 删除未使用的表
-- 首先删除有外键约束的表

-- 删除出库明细表
DROP TABLE IF EXISTS stock_out_items;

-- 删除出库记录表
DROP TABLE IF EXISTS stock_out;

-- 删除入库明细表
DROP TABLE IF EXISTS stock_in_items;

-- 删除入库记录表
DROP TABLE IF EXISTS stock_in;

-- 删除视图
DROP VIEW IF EXISTS sales_order_details;

-- 确认删除成功
SELECT 'Unused tables have been deleted.' AS message; 