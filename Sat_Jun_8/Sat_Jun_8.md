## NoSQL
- 不保证关系数据的ACID特性
    - 原子性：事务是不可分割的最小操作单元，事务中的所有操作要么全部完成，要么全部不完成。
      - 例如，在银行转账业务中，假设用户 A 要向用户 B 转账 100 元。这个转账事务包括两个主要操作：从 A 的账户中扣除 100 元和向 B 的账户中存入 100 元。原子性要求这两个操作必须作为一个整体来执行，不能只执行其中一个操作。如果在操作过程中出现系统故障等情况，要么两个操作都完成，要么都不完成，这样可以保证账户数据的正确性。
  <br>
    - 连续性：数据库中的数据在事务开始之前和事务结束之后都必须保持是符合数据库完整性约束的。
      - 还是以银行转账为例，假设银行规定账户余额不能为负数。在转账事务执行之前，A 和 B 的账户余额都符合这一约束（假设都大于 100 元）。事务执行后，A 的账户余额减少 100 元，B 的账户余额增加 100 元，这两个账户余额依然符合余额不能为负数的约束，这就保持了数据库的一致性。
  <br>
    - 隔离性：多个事务并发执行时，事务之间是相互隔离的，一个事务的执行不能被其他事务干扰。
      - 例如，在一个网上书店系统中，用户 A 和用户 B 同时购买同一本书。如果没有隔离性，可能会出现超卖的情况。但在具有隔离性的事务处理机制下，当用户 A 开始购买这本书并生成一个事务时，这个事务会对这本书的库存进行锁定（或者采用其他隔离机制），用户 B 的购买事务在尝试操作这本书的库存时就会被阻塞或者采用其他合适的方式处理，直到用户 A 的事务完成（提交或回滚），这样可以保证两个事务之间的相互独立性，确保数据的正确性。 
  <br>
    - 持久性：事务一旦提交，它对数据库的改变就应该是永久性的，即使在事务完成后出现系统故障（如停电、服务器崩溃等），数据库也能保证事务执行的结果不会丢失。
      -  例如，当用户在电商平台上完成一笔订单支付事务后，系统会将订单和支付信息存储到数据库中。一旦事务提交成功，这些数据就会被写入到存储设备（如磁盘）上，并且即使后续服务器出现故障，再次启动后仍然能够从存储设备中恢复这些数据，保证用户订单和支付信息的持久保存。
- 消除数据之间关联性：
   - 例如，在 MyBatis 中可以使用 SQL 的 join 语句来关联查询用户和用户的角色信息，但在 Redis 中，如果要获取用户和角色信息，需要分别去查询对应的 key，然后在应用代码中将这些数据组合起来，它不会像 MyBatis 那样通过数据库层面的关联操作自动获取相关联的数据。
   - 例如，在一个电商系统中，商品信息经常被访问，为了减轻数据库压力，会将商品信息缓存到 Redis 中。在 Redis 中存储的商品信息只是简单的 key - value 对，它不考虑商品与其他数据（如订单、库存等）之间的关联，而这些关联在数据库中（使用 MyBatis 操作）是被维护的。
---
### 外键和联表查询的关系

外键可以用于建立表之间的关系，但 MySQL 中的数据表之间的关系并不全是通过外键维系的。dish_flavor.id = meal.id 是用于联表查询的条件，但并不一定意味着 flavor.id 是外键。
<br>

**1. 无外键的联表查询**
可以仅通过字段值的关联来实现联表查询，而这些字段之间没有外键约束。例如，假设有一个 orders 表和一个 customers 表，orders 表中有一个 customer_id 字段，customers 表中有一个 id 字段。虽然 customer_id 没有被定义为外键，我们仍然可以通过 orders.customer_id = customers.id 这样的条件进行联表查询，来获取订单和对应的客户信息。这种情况下，表之间的关联只是基于字段值相等的逻辑关系，而不是数据库层面的外键约束。

**2. 外键的作用**
外键主要用于维护数据的完整性和一致性。当设置外键时，数据库会自动进行一些约束检查。

---
## 外键作用和优势的例子：<br>
**表结构**
假设我们有两个表，一个是 orders（订单）表，一个是 customers（客户）表：
- customers 表：存储客户信息
    1. customer_id（客户编号，主键）
    2. customer_name（客户姓名）
- orders 表：存储订单信息
    1. order_id（订单编号，主键）
    2. customer_id（客户编号，外键，指向 customers.customer_id）
    3. order_date（订单日期）
    4. order_amount（订单金额）

**维护数据完整性**
场景：现在有一个客户在 customers 表中，编号为1，姓名为“张三”。我们想在 orders 表中插入一条该客户的订单。
```sql
INSERT INTO orders (order_id, customer_id, order_date, order_amount)
VALUES (1001, 1, '2025-06-08', 1000);
```
结果：由于 orders.customer_id 是外键，指向 customers.customer_id，数据库会自动检查 customers 表中是否存在编号为1的客户。因为存在，所以这条记录可以成功插入。
优势体现：如果试图插入一个不存在的客户编号（如2）到 orders 表中，数据库会拒绝插入，防止出现孤立的订单记录，即一个不存在的客户对应的订单，从而维护了数据的完整性。

**级联更新和删除**
设置级联操作：假设我们在创建表时，为 orders.customer_id 外键设置了级联更新和删除。
```sql
ALTER TABLE orders
ADD CONSTRAINT fk_customer
FOREIGN KEY (customer_id)
REFERENCES customers(customer_id)
-- REFERENCES customers(customer_id) 
-- 表示 orders.customer_id 列的值必须在 
-- customers.customer_id 列中存在。
ON UPDATE CASCADE
ON DELETE CASCADE;
```
级联更新场景：
```sql
UPDATE customers
SET customer_id = 2
WHERE customer_id = 1;
```
结果：customers 表中编号为1的客户更新为编号2。由于设置了级联更新，orders 表中对应的 customer_id 也会自动更新为2。
优势体现：当客户编号需要变更时，只需要更新 customers 表，相关订单表中的客户编号会自动同步更新，无需手动去 orders 表中修改，减少了人工操作的错误和遗漏。

**级联删除场景：**
```sql
DELETE FROM customers
WHERE customer_id = 2;
```
结果：customers 表中编号为2的客户被删除。由于设置了级联删除，orders 表中所有 customer_id 为2的订单记录也会被自动删除。
优势体现：当删除一个客户时，与该客户相关的订单也会被自动清理，避免出现无效的订单数据，保持了数据库的整洁和一致性。