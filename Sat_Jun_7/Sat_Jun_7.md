# 八股精要整理

## 乐观锁与悲观锁使用场景
- **乐观锁**  
  - 适用场景：读多写少、并发冲突概率低的场景（如订单状态更新、用户信息修改）  
  - 实现方式：CAS操作、版本号机制（MySQL的version字段）  
  - 特点：冲突时才重试，冲突概率低时性能更好  

- **悲观锁**  
  - 适用场景：写多或冲突概率高的场景（如银行转账、库存扣减）  
  - 实现方式：数据库行锁/表锁、分布式锁（Redis/Zookeeper）  
  - 特点：数据一致性要求高时优先使用  

<br>
note: Mysql是悲观锁，Redis是乐观锁。

---

## 缓存删除失败问题及解决方案
- **问题**：数据更新成功但缓存未删除 → 用户读取旧数据（脏读）  
- **解决方案**：  
  1. **延时双删**：  
     - 更新DB后先删缓存  
     - 延迟一定时间（如500ms）再次删除缓存（防止并发读导致旧值回写）  
  2. **数据旁路模式**：  
     - 读请求：缓存命中直接返回；未命中则查DB并回填缓存  
     - 写请求：更新DB后删除缓存  

---

## 大规模用户共同关注计算
- **小规模方案**：集合取交集（如Redis的`SINTER`命令）  
- **百万级关注解决方案**：  
  1. **压缩位图**：  
     - 使用`Bitmap`或`RoaringBitmap`存储关注列表  
     - 优点：内存占用低，支持高效交集/并集运算  
  2. **分布式计算**：  
     - 通过`MapReduce`或`Spark`分片计算交集  
     - 适用超大规模数据（如十亿级用户）  

---

## Redis Sorted Set选型排行榜原因
- **核心优势**：  
  - 按分数（score）自动排序，天然适合排行榜场景  
  - 高效操作：  
    - `ZADD`更新分数：O(log N)  
    - `ZRANGE`获取排名：O(log N + M)（M为返回元素数）  
    - `ZRANK`查询用户排名：O(log N)  
  - 支持区间查询、实时更新  

---

## Prompt编写范式
1. **清晰具体**：避免歧义，明确需求细节  
2. **分步指令**：复杂任务拆解为多步骤  
3. **上下文补充**：提供必要背景信息  
4. **示例引导**：给出输入/输出样例  
5. **约束格式**：如"JSON输出"或"列出要点"  
6. **角色扮演**：指定回答风格/身份  
7. **多轮交互**：根据反馈动态调整Prompt  

---

## MySQL索引与优化
### 索引结构（B+树）
- **层高影响因素**：  
  - 数据总量（数据量↑ → 层高↑）  
  - 页大小（默认16KB，页大小↑ → 单页存储索引项↑ → 层高↓）  
  - 索引项大小（主键长度↑ → 单页存储索引项↓ → 层高↑）  

### 索引类型
| 类型         | 特点                                                                 |
|--------------|----------------------------------------------------------------------|
| 聚簇索引     | 数据与索引一起存储（主键索引），叶子节点存数据行                     |
| 非聚簇索引   | 叶子节点存主键值，需回表查询                                         |
| 唯一索引     | 强制列值唯一，加速唯一值查询                                         |
| 联合索引     | 多列组合索引，遵循最左匹配原则                                       |

### Mysql查询分析与优化
- **分析流程**：  
  1. `EXPLAIN`分析执行计划（索引使用/回表/全表扫描）  
  2. 检查慢查询日志定位慢SQL  
  3. 审查表结构与索引设计  
  4. 优化SQL语句（避免`SELECT *`、`LIKE '%xx'`等）  
  5. 检查数据量与统计信息  
  6. 监控硬件资源（CPU/IO/内存）  
  7. 排查锁竞争问题  

- **常见优化手段**：  
  - 合理添加索引  
  - SQL重写  
  - 分库分表  
  - 读写分离  
  - 热点数据缓存  

---

## MySQL事务与锁
### 隔离级别
- **默认隔离级别**：可重复读（Repeatable Read）  
- **可重复读问题**：  
  - 幻读（当前读操作可能读到新插入行）  
  - **解决方案**：  
    - 快照读：通过MVCC+undo log保证一致性视图  
    - 当前读：通过间隙锁（Gap Lock）阻止区间插入  

### 间隙锁原理
- **锁定范围**：索引记录的区间（左开右开区间）  
- **作用**：阻止区间内的插入/删除操作（仅RR隔离级别生效）  
- **临键锁（Next-Key Lock）**：行锁 + 间隙锁组合，锁定记录及前后间隙  

---

## Java锁机制
### 底层实现
- **synchronized**：  
  - 对象头Mark Word实现锁升级（无锁 → 偏向锁 → 轻量级锁 → 重量级锁）  
  - 编译后对应`monitorenter`/`monitorexit`指令  

- **ReentrantLock**：  
  - 基于AQS（AbstractQueuedSynchronizer）实现  
  - 支持公平/非公平锁、可中断、条件变量  

- **CAS**：  
  - 底层CPU指令（如`CMPXCHG`）  
  - 核心方法：`Unsafe.compareAndSwapInt()`  

### synchronized使用方式
| 方式                | 锁对象                     | 示例                          |
|---------------------|----------------------------|-------------------------------|
| 实例方法            | 当前实例（`this`）         | `synchronized void foo()`     |
| 静态方法            | 类对象（`ClassName.class`）| `static synchronized void bar()`|
| 代码块              | 指定对象                   | `synchronized(obj){...}`      |

### AtomicInteger
- 基于CAS实现的线程安全整数操作
- 可以实现原子操作的自增  
- 适用场景：计数器、状态标志等轻量级同步  

---

## 事务控制场景与目标
- **典型场景**：  
  - 银行转账（A扣款/B入账原子性）  
  - 订单系统（扣库存/减余额/生成订单）  
  - 支付结算等多步骤操作  

- **核心目标**：  
  - 保证**ACID特性**：  
    - **A**tomicity（原子性）：操作全成功或全失败  
    - **C**onsistency（一致性）：数据状态合法  
    - **I**solation（隔离性）：并发操作互不干扰  
    - **D**urability（持久性）：提交后数据永久保存  

---

## 集群Key管理原理
  - **分片机制**：
    - Redis集群内部把所有数据空间划分成16384个“槽”（slot），每个槽相当于一个小的数据分区。
    - 每插入一条数据时，先对Key做CRC16哈希运算，得到一个整数。
    然后用这个整数对16384取模，结果就是该Key应该归属的槽编号（0~16383）。
    - 这16384个槽会被分配到集群中的各个主节点上。
    每个节点负责管理它分配到的那些槽中的所有Key和数据。
    - 比如有3个节点，可能每个节点负责约5461个槽。
    - eg: 假设有10万个Key，Redis会自动根据Key的哈希值，把这些Key均匀分配到各个节点上，应用端无感知。
  - 数据、槽（slot）、节点（node）之间的关系：
    - <small><span style="color:orange;">槽的作用：解耦Key和节点，简化数据迁移</span></small>
    - **数据（Key-Value）**：就是我们实际存储的业务数据，比如订单、商品、用户信息等。
    - **槽（Slot）**：Redis Cluster把整个Key空间分成16384个槽（slot），每个槽的编号是0~16383。
    - **节点（Node）**：集群中的每一台Redis实例称为一个节点，节点可以是主节点（master）或从节点（slave）。

---

## Redis的key常用淘汰策略：
 * **noeviction（默认）** ：内存不足时，返回错误，不再淘汰任何 key（适合只做持久化存储，不适合缓存）。
  * **allkeys - lru** ：所有 key 中，淘汰最近最少使用的 key（LRU）。
  * **volatile - lru** ：只在设置了过期时间的 key 中，淘汰最近最少使用的 key。
  * **allkeys - random** ：所有 key 中，随机淘汰。
  * **volatile - random** ：只在设置了过期时间的 key 中，随机淘汰。
  * **volatile - ttl** ：只在设置了过期时间的 key 中，优先淘汰即将过期的 key。


### 生产环境建议:
- 通常allkeys-lru最常用，能保证缓存命中率。<br>
- Redis的内存管理是惰性机制+定期删除结合，能避免频繁全量遍历。
---

## 拦截器对JWT令牌校验是在哪个环节？
- JWT令牌校验一般在服务端收到请求后、业务处理前，通过拦截器（如Spring的Filter/Interceptor）进行。
- 典型流程是：<span style="color:orange;">请求 -> 网关/服务端拦截器 -> 解析JWT并校验签名、过期、权限等 -> 合法则放行到后端业务逻辑，不合法则直接返回<big> 401 </big>等错误。</span>

---

## 地址栏输入网址到页面展示的流程

### 1. DNS 解析
输入网址后，浏览器首先将域名通过 DNS 解析为 IP 地址（会查询本地 DNS 缓存、系统缓存、hosts 文件，若未命中则递归到权威 DNS 服务器）。

### 2. 建立 TCP 连接（三次握手）
浏览器与目标服务器建立 TCP 连接（如果是 HTTPS，还要额外进行 TLS 握手，协商加密方式、证书校验等）。

### 3. 发送 HTTP/HTTPS 请求
浏览器根据输入的网址拼装 HTTP 请求（GET/POST 等）发送到服务端，包括请求头、Cookie 等。

### 4. 服务器处理请求
服务器收到请求，经过反向代理（如 Nginx）、负载均衡，路由分发到后端服务，后端进行业务处理（查数据库、逻辑运算等）。过程中可能会有鉴权（如 JWT 校验）、缓存命中、限流等操作。

### 5. 服务器响应
服务器将处理结果（HTML、JSON、图片等）作为 HTTP 响应返回。

### 6. 浏览器渲染页面
浏览器解析 HTML、CSS、JS 等静态资源，构建 DOM 树、CSSOM、渲染页面。遇到外部资源（图片、JS、CSS、字体等），继续发起请求。JS 引擎执行脚本、页面交互、首屏渲染、异步加载等。

## ThreadLocal 使用场景
在项目中，通常在拦截器/过滤器里将用户信息等上下文信息存入 ThreadLocal，后续业务代码随时取用，提升代码整洁和可维护性。

## 消息转换器使用场景
在 RESTful API 的开发中，使用 JSON 格式进行前后端数据的传输。通过配置消息转换器，能够自动将 Controller 的方法返回的 Java 对象转换成 JSON 格式响应给客户端。

## AOP（面向切面编程）

### （一）定义与作用
AOP 是一种编程范式，主要用于将横切关注点（如日志、事务、安全、监控等）从业务逻辑中分离出来，提高代码的可复用性和可维护性，在 Spring 等主流框架中有广泛应用。
- **关注点**：横切关注点是多个业务模块都会涉及的通用逻辑。
- **切面**：用于将像日志记录、事务管理这样的通用逻辑集中处理，避免代码重复，提升可维护性和可读性。
- **Weaving（织入）**：将切面应用到目标对象，形成代理对象的过程。

### （二）Spring AOP 的实现方式

#### 1. 基于 JDK 动态代理（接口代理）
目标实现了接口，Spring 会为接口创建代理对象。
```java
public static Object getProxy(Object target) {
    return Proxy.newProxyInstance(
        target.getClass().getClassLoader(),     // 1. 类加载器
        target.getClass().getInterfaces(),      // 2. 代理实现哪些接口
        (proxy, method, args) -> {              // 3. 方法拦截器（InvocationHandler）
            System.out.println(">>> 前置增强");
            Object result = method.invoke(target, args);
            System.out.println("<<< 后置增强");
            return result;
        }
    );
}
```
#### 2. 基于 CGLIB 动态代理（子类代理）
目标没有实现接口，Spring 会基于 CGLIB 为目标类创建子类实现代理。

```java
public static Object getProxy(Class<?> clazz) {
    Enhancer enhancer = new Enhancer();                  // 1. 创建增强器
    enhancer.setSuperclass(clazz);                       // 2. 设置父类 = 目标类，代理类会变成这个类的子类。
    enhancer.setCallback((MethodInterceptor) (obj, method, args, proxy) -> { // 3. 方法拦截器
        System.out.println(">>> 前置增强");
        Object result = proxy.invokeSuper(obj, args);    // 4. 调用父类原始方法
        System.out.println("<<< 后置增强");
        return result;
    });
    return enhancer.create();                            // 5. 生成代理对象（子类）
}
```

- JDK 动态代理特点：基于接口，适合有接口的类，代理的是接口的实现类对象（代理生成的对象类型是接口类型，而不是目标类类型）、速度快、依赖少。
- CGLIB 动态代理特点：基于继承，适合无接口的类，代理的是普通类（即没有实现接口也没关系，只要不是 final 类），生成慢、调用快。
- Spring 代理策略：实际开发中，Spring 优先用 JDK 代理，无接口时自动切换 CGLIB。

## 反射

反射就是在运行时，动态地获取类的结构（如类名、属性、方法、构造器等），并可以对对象进行实例化、方法调用、属性赋值等操作。类加载器在运行时分阶段加载字节码到内存的机制。只有类被加载到 JVM 之后，才可以通过 Class<?> 对象获取它的结构信息（字段、方法、注解等），这就是反射的基础。动态创建和管理 Bean 本质是通过反射实现的。

## 外键设置

逻辑外键（Foreign Key）在“多”的一方表里。“一” 的一方表用主键（如 department_id）唯一标识。“多” 的一方表（Employee）里，增加一个字段（如 department_id），指向“一” 的一方表的主键。

## @ConfigurationProperties 注解
@ConfigurationProperties 是 Spring Boot 提供的一个常用注解，<big>**用于将配置文件中的属性自动映射到 Java Bean 的属性上**。</big>


例如：将配置文件（application.yml 或 application.properties）中以 sky.alioss 开头的配置项，自动绑定到 Java Bean 的属性上。

在配置文件中写：

```yaml
sky:
  alioss:
    endpoint: https://oss-cn-beijing.aliyuncs.com
    access-key-id: yourAccessKeyId
    access-key-secret: yourAccessKeySecret
bucket-name: yourBucketName

```

Java Bean这样写

```java
@Component
@ConfigurationProperties(prefix = "sky.alioss")
public class AliOssProperties {
    private String endpoint;
    private String accessKeyId;
    private String accessKeySecret;
    private String bucketName;

    // getters and setters...
}
```
- Spring Boot 启动时，会自动加载你的配置文件（application.yml 或 application.properties）。
- 遇到带有 @ConfigurationProperties("sky.alioss") 的Bean，会自动从配置文件中找 sky.alioss 下的所有属性（如 endpoint、access-key-id 等）。
- Spring 会将这些配置项的值，通过反射机制，自动映射到你的 Java Bean 对应的字段上。
- YAML里的 access-key-id 通过驼峰映射，自动绑定到 Java 的 accessKeyId 属性上。

## collection和association的区别
- <association> 标签用于处理一对一的关联关系。例如，在实际的数据库场景中，一个班级对应一个班主任（假设每个班级只有一个班主任），这种班级和班主任的一对一关系就可以通过 <association> 来映射。
- <collection> 标签用于处理一对多的关联关系。以订单系统为例，一个订单可以包含多个订单详情（如购买了多种商品），这时订单和订单详情就是一对多的关系，可以通过 <collection> 来映射这种关系。

## AOP解决了什么问题？
AOP 主要解决了横切关注点和核心业务逻辑耦合的问题。例如：
  - 日志记录
  - 权限校验
  - 性能监控
  - 事务管理
  
如果没有AOP，这些逻辑就会散落在各个业务代码中，导致代码膨胀、可维护性差、难以复用。AOP通过统一的切面实现，将这些横切逻辑抽离出来，业务代码只关注自身本职功能。

**AOP应用场景**
- 统一日志处理（如接口调用日志、异常日志）
- 权限校验和认证
- 数据库事务统一处理

## AOP中切面可以有多个吗？可以作用于同一个切入点方法吗？
可以！
- 一个系统中可以有多个切面（Aspect）。
- 多个切面可以作用于同一个切入点（Pointcut）方法。
- 多个切面同时作用于同一方法时，执行顺序由切面的优先级（如@Order注解）决定。
- 同一个切面内部可以有多个通知（Advice），如前置、后置、异常、最终、环绕通知。




