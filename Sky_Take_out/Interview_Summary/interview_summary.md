## 苍穹外卖简介

**主要工作:**

1. 使用Nginx作为HTTP服务器，部署静态资源，反向代理和负载均衡
2. 登录及身份验证使用JWT令牌技术，以完成用户认证，通过ThreadLocal配合拦截器来进行Token的校验，判断用户是否处于登录状态，解决HTTP请求无状态的问题。
3. 使用Redis缓存高频数据，缓解高并发环境下频繁访问数据库造成的性能下降。
4. 通过WebSocket实现客户端与服务端的长连接，实现来单提醒及客户催单等功能。
5. 使用SpringTask实现订单状态的定时处理，超时自动取消订单等功能

**个人收获：**
1. 熟悉了在 SpringBoot框架下开发项目的整体流程。
2. 熟悉了常用数据库 Redis和 MySOL的区别及适用场景。
3. 学会优化代码细节，编写代码注重可读性。如在登录功能中，将员工表的密码从明文存储转为MD5加密存储。

**项目的基础功能有哪些：**
- 管理端能在网页上对菜品、订单、员工等进行管理修改，
- 用户端能在微信小程序上在线浏览菜品、修改购物车，下单支付、催单等等。

**遇到的问题?如何解决?：**
最开始没有考虑到实际上线后的情况，没有用redis进行缓存，统一用的mysql，业务增多的话会造成数据库访问量很大，数据库宕机且每次查询磁盘而不是缓存会使得速度比较慢，这些都不适用于实际情况。

---

## WebSocket服务端组件

```java
package com.sky.websocket;

import org.springframework.stereotype.Component;
import javax.websocket.OnClose;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.PathParam;
import javax.websocket.server.ServerEndpoint;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

/**
 * WebSocket服务
 */
@Component
@ServerEndpoint("/ws/{sid}")
public class WebSocketServer {

    //存放会话对象
    private static Map<String, Session> sessionMap = new HashMap();

    /**
     * 连接建立成功调用的方法
     */
    @OnOpen
    public void onOpen(Session session, @PathParam("sid") String sid) {
        System.out.println("客户端：" + sid + "建立连接");
        sessionMap.put(sid, session);
    }

    /**
     * 收到客户端消息后调用的方法
     *
     * @param message 客户端发送过来的消息
     */
    @OnMessage
    public void onMessage(String message, @PathParam("sid") String sid) {
        System.out.println("收到来自客户端：" + sid + "的信息:" + message);
    }

    /**
     * 连接关闭调用的方法
     *
     * @param sid
     */
    @OnClose
    public void onClose(@PathParam("sid") String sid) {
        System.out.println("连接断开:" + sid);
        sessionMap.remove(sid);
    }

    /**
     * 群发
     *
     * @param message
     */
    public void sendToAllClient(String message) {
        Collection<Session> sessions = sessionMap.values();
        for (Session session : sessions) {
            try {
                //服务器向客户端发送消息
                session.getBasicRemote().sendText(message);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

}
```

1. sid是什么：
- sid（Session ID），在你的服务端实现中，是客户端连接WebSocket时URL携带的唯一标识。
- 用于区分不同的连接（客户端），实现点对点通信、消息定向推送。
- 你可以通过sid快速定位到某个用户的Session（会话），比如精确推送消息给指定用户。

2. WebSocket里的Session是什么意思？
- 代表一次客户端和服务端之间的WebSocket连接，每当有一个 WebSocket 连接建立时，服务器端就会为该连接分配一个 Session 对象。

3. @OnOpen是什么？回调是什么意思？
- @OnOpen是Java WebSocket标准注解，用来标记“当有客户端和服务端建立连接时会自动调用的方法”。
- 回调（callback） 指的是：某个事件发生后，系统自动帮你调用你指定的方法，而不是你自己主动去调用。
- 当客户端第一次连接WebSocket服务端时，框架会自动触发带有@OnOpen注解的方法，并把本次连接的Session对象和路径参数（如sid）传进来。

4. 消息推送能力：
- @OnOpen：客户端连接建立时回调，保存Session。
- @OnMessage：接收客户端消息，打印日志（可扩展业务逻辑）。
- @OnClose：连接关闭时移除Session。
- sendToAllClient：遍历所有Session，群发文本消息。

---

## 苍穹外卖中的跨域场景

**什么是跨域：**
跨域（Cross-Origin）是指浏览器中，一个网页试图去请求另一个源（域名、协议、端口不同）的资源。同源策略（Same-Origin Policy）是浏览器的重要安全机制，它规定了“同源”的两个页面可以互相访问数据，不同源的则受到限制。
**受限于浏览器，前端代码（如 Ajax、fetch、axios）无法直接访问非同源的后端接口**

**同源的定义（满足全部三项）：**
- 协议相同（如 http、https）
- 域名相同（如 www.example.com）
- 端口号相同（如 :80、:8080）
只要有一项不同，就属于跨域。

<br>

**解决方案：Nginx反向代理**
前端发送请求和后端接口地址不一样，通过 Nginx 配置，将前端的请求代理到后端服务，表现上看是同一个源，解决跨域。
例如，将前端应用部署在某个域名或端口下，后端服务部署在另一个域名或端口下，通过 Nginx 配置反向代理规则，将Nginx代理后端服务器，将前端请求通过Nginx转发到后端服务，并将后端服务的响应返回给前端，这样就避免了浏览器直接跨域请求后端服务时产生的跨域问题​​。

---

## Nginx的负载均衡与静态资源处理

**将Nginx作为Http服务器的作用：**
Nginx 作为 HTTP 服务器，擅长高效地处理静态资源(如前端页面、图片、CSS、JS文件等)，响应速度快、并发能力强，非常适合外卖系统的前端页面访问、商品图片加载等需求。

**负载均衡：**
将请求分发到多个服务器，以提高性能

---

## Token

**token 里的id是从哪来的：**
token，尤其是JWT(JSON Web Token)，是在用户登录成功时由后端生成的。
登录流程：
- 用户提交账号和密码 >后端验证成功
- 后端查到该用户的真实id(比如数据库里的主键id)
- 生成JWT token，把用户id和其他信息作为 payload 写进token
- token返回给前端，前端保存(如localStorage、cookie)

**后续如何获取id?：**
每次前端发请求时，会把token放在请求头(如Authorization)里。
后端收到请求后:
- 拦截器/过滤器解析token，取出 payload 里的userld
- 通常会把userld放入ThreadLocal或上下文，业务代码直接获取
所以，token里的id，其实就是用户登录时查库得到的id。

**id和用户名不一样：**
- 用户名是作为用户登录时的凭证之一（通常配合密码/验证码等）。
- 用户ID是数据库中为每个用户分配的唯一数字（如自增主键、UUID），是系统内部唯一标识用户的主键。
- 在实际场景里，后端接口收到登录请求后，会根据用户名去数据库查询用户信息，查询到用户后，会拿到该用户的 id（如：10086）。后续所有的数据操作、业务流程、权限判断、日志记录，内部都用用户ID唯一标识该用户，而不是用用户名。

**Session-Cookie机制的缺点：**

用户登录成功后，服务端生成一份session数据，并分配一个sessionId。浏览器自动把sessionId存到cookie，后续请求自动带上，服务器通过sessionId找到用户身份。
- 服务端存储压力大:每个用户都需要在服务器保存一份 session，用户多了压力大，
- 分布式困难:如果你有N台服务器，每台各存一份session，负载均衡时同一个用户可能每次请求到不同服务器，导致session丢失或不同步。因此需要额外引入 session共享(如Redis)，增加系统复杂度和开销。

**cookie和session：**

cookie用于在client和server间传递状态信息，sessionID常存放在cookie里，客户端请求时自动携带cookie（包含sessionID），并通过该sessionID找到存在服务器里的session。
- cookie存在客户端
- 每一个sessionID都对应着一份独立的会话数据，（通常存在内存、Redis缓存里）
- 用户第一次访问时没有sessionID,服务端生成并用set—cookie将sessionID放入客户端cookie里
- cookie丢失，则在服务器找不到对应的session，会被当成新用户重新登录。

**JWT无状态的含义：**
- 传统的session-cookie机制需要在服务端存储会话状态，客户端通过cookie里的sessionID关联会话。
- 而JWT中服务端不存储任何会话信息，所有必要数据直接编码到Token里（**也就是自包含**），服务端只需要验证签名和有效期

**JWT的结构：**
- header：声明签名算法和token类型。
- payload：业务数据
- signature：对前两部分进行签名

**Token优劣：**
- 横向扩展方便：无需Session共享，适合分布式架构
- 减少数据库压力：无需频繁查询会话状态
- 无法主动失效，需依赖短期有效期或Redis黑名单机制
- Token的体积大

---

## 两种统一拦截技术

**区别**

1. **过滤器和拦截器其实都是AOP编程思想的实现**
2. **归属不同**： 
    - Filter是Servlet规范的一部分，只能用于web程序中;
    - Interceptor是SpringMVC的一部分，既可以用在web层，又可以用在Application和 Swing程序中
3. **实现方法不同**：
    - 过滤器可以使用 Servlet 3.0提供的@WebFilter 注解，配置过滤 URL规则或者去 web.xml中配置自定义过滤器实现 Filter接口，重写 doFilter方法。
    - 拦截器的实现分为两步，第一步，创建一个普通的挡截器，实现 Handlerlinterceptor接口，并重写接口中的 preHandle/postHandle/aftercompletion 方法;创建的拦截器加入到 Spring Boot 的配置文件，指定拦截的路径。
4. **拦截范围不同:**
    - 过滤器Filter会拦截所有的资源，而Interceptor只会拦截Spring环境中的资源
5. **执行时机不同:**
    - 过滤器会先执行，然后才会执行拦截器，最后进入真正的要调用的方法。
    - 拦截器更接近业务系统，所以拦截器主要用来实现项目中的业务判断，比如:登录判断、权限判断、日志记录等业务。
    - 过滤器通常是用来实现通用功能过滤的，比如:敏感词过滤、字符集编码设置、响应数据压缩等功能。

**总结：**
| 特点         | 过滤器（Filter）                        | 拦截器（Interceptor）                   |
|--------------|-----------------------------------------|-----------------------------------------|
| **所属规范** | Servlet 规范（Java EE标准）             | Spring MVC 框架                         |
| **作用阶段** | Servlet 前后（处理所有进入容器的请求）   | DispatcherServlet与Controller之间       |
| **作用范围** | 几乎所有请求，包括静态资源（如js/css/img/html等） | 只拦截被Controller处理的请求（不包括静态资源） |
| **配置方式** | web.xml 或 @WebFilter 注解              | 实现HandlerInterceptor接口并注册到Spring配置 |
| **使用场景** | 通用任务，如编码、日志、权限、跨域、压缩等 | 业务相关任务，如登录校验、权限检查、日志等 |
| **生命周期** | 由Servlet容器管理                      | 由Spring容器管理                        |
| **执行次数** | 只要经过Servlet，都会被执行              | 只拦截被Spring MVC处理的请求            |
| **技术依赖** | 与Spring无关，任何Java Web项目都可用     | 仅限Spring MVC项目                      |

**拦截器实例：**
```java
//典型场景：接口请求的权限校验
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        //从 Session 中取出键为 "user" 的属性。
        Object user = request.getSession().getAttribute("user");
        if (user == null) {
            response.sendRedirect("/login");
            return false; // 不通过，后续Controller方法不会被执行
        }
        return true; // 允许通过，执行Controller方法
    }

    // 省略postHandle和afterCompletion方法
}

//注册拦截器：
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new AuthInterceptor())
                .addPathPatterns("/**"); // 拦截所有Controller请求
    }
}
```

**过滤器实例：**
```java
import javax.servlet.*;
import javax.servlet.annotation.WebFilter;
import java.io.IOException;

@WebFilter("/*") // 拦截所有请求
public class EncodingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        // 1. 设置请求体的编码为UTF-8
        request.setCharacterEncoding("UTF-8");
        // 2. 设置响应体的编码为UTF-8
        response.setCharacterEncoding("UTF-8");
        // 3. 继续执行下一个过滤器或目标资源
        chain.doFilter(request, response);
    }
}
/*
@WebFilter("/*") 表示这个过滤器会拦截所有的请求。
request.setCharacterEncoding("UTF-8") 保证客户端传来的参数不会乱码。
response.setCharacterEncoding("UTF-8") 保证服务端返回的数据不会乱码。
chain.doFilter(request, response) 让请求继续往下走（到下一个过滤器或Controller）。
*/
```
---

## MySQL MVCC & ReadView 
ReadView 是 MySQL InnoDB 的 MVCC（多版本并发控制）实现核心。其本质是一个快照，用于实现事务的可重复读，保证同一事务中多次 select 看到的一致性数据（快照读）。

**ReadView 主要字段：**
- m_ids：生成 ReadView 时当前活跃的事务ID列表（未提交的事务）。
- min_trx_id：m_ids 中最小的事务ID。
- max_trx_id：历史上分配出的最大事务ID的下一个值（即新事务分配ID会从这里开始）。
- creator_trx_id：当前生成 ReadView 的事务ID。

**InnoDB每条记录(每个叶子节点)的隐藏字段：**
- trx_id：最近一次修改这条记录的事务ID。
- roll_pointer：回滚指针，指向 undo log，支持历史版本回溯。

**可见性规则：**
假如当前检查某条记录的 trx_id（该版本的修改者ID）：
- trx_id < min_trx_id<br>
    该事务在 ReadView 生成前已提交，可见。
- trx_id > max_trx_id<br>
    该事务在 ReadView 生成后才开启，不可见。
- trx_id ∈ m_ids（活跃事务列表）<br>
    该事务未提交，不可见。
- trx_id 不在 m_ids 且 min_trx_id ≤ trx_id < max_trx_id<br>
    该事务已经提交，可见。
- trx_id = creator_trx_id<br>
    该事务本身对自己的修改可见。

**MVCC 下快照读和当前读的区别？**
- 快照读（Snapshot Read）：select 普通查询，走 MVCC。
- 当前读（Current Read）：for update、insert、update、delete，读的是最新版本，并加锁。


**读已提交的readview:**<br>
每次执行select时生成新的readview,能看到所有在查询前已提交的数据版本。

**可重复读：**<br>
仅在事务第一次select时生成，事务仅能看到第一次查询时的数据快照

---

**upload的原子性**<br>
单条update语句的原子性：
无论是InnoDB还是其他主流数据库引擎，单条DML（如update、insert、delete）语句本身就是一个最小的事务单元，数据库会保证其原子性。<br>
update操作本质：行锁+undolog实现。<br>
如果发生回滚，用undolog回滚。<br>
行锁粒度细，支持高并发。<br>
如果修改较多行，锁粒度依然是行锁，undolog记录旧值。<br>
**应用层批量update（多条SQL）：**
只有在同一个事务里提交，才具备整体原子性，否则每条SQL是独立原子的。

**锁的类型:**<br>
- 全局锁：如flush tables with read lock，用于备份，全库只读。<br>
- 表级锁：如lock tables，MyISAM引擎使用，阻塞其他线程对表的操作。<br>
- 元数据锁（MDL）：用于防止表结构被并发修改，DML、DDL操作会自动加MDL。<br>
- 意向锁：用于标记事务即将在某些行上加锁的类型，，实际上并不阻止其他事务访问具体的行。<br>
- 行级锁：InnoDB支持，Myisam不支持。
    - 记录锁：记录锁是InnoDB行级锁（行锁）的一种，是最基础的行级锁实现。锁定的是B+树索引的叶子节点上的某一条记录（也就是一行数据）。
    - InnoDB的数据表，每一行数据都存储在B+树的叶子节点上，无论是主键索引还是二级索引。
- 间隙锁：锁两条记录之间的范围，而不是具体的某条记录。
    - 比如，表中有主键值 10 和 20，间隙锁可以锁住 (10, 20) 这个区间，但不包含10和20本身。
    - 防止“幻读”，即防止在事务执行过程中，有其他事务在“间隙”内插入新数据。
    - 主要用于可重复读（RR）隔离级别下的范围查询（如SELECT ... FOR UPDATE、UPDATE ... WHERE ...等）。
    ```sql
    SELECT * FROM user WHERE id > 10 AND id < 20 FOR UPDATE;
    ```
- 临键锁
    - 临键锁是**“记录锁”+“间隙锁”**的组合，即锁住了某条索引记录本身及其前面的间隙。
    - 例如，(10,20]，即锁住了大于10小于等于20的部分，包括20本身和 (10,20) 的间隙。
    - 彻底防止幻读，确保范围内的所有数据都被锁住，包括现有记录和“未来可能插入”的记录。
    - InnoDB在RR隔离级别下的大多数范围查询加锁操作，默认使用临键锁。
    ```sql
    SELECT * FROM user WHERE id >= 10 AND id < 20 FOR UPDATE;
    ```
    此时会对 (10,20) 区间加间隙锁，并对 id=10 也加上记录锁，实际效果是 (10,20) 区间和10本身都被锁住。

**什么是索引：**
- 数据库索引是一种数据结构，加速数据查询和更新。
- 常用B+树作为底层实现。
- 类似于书的目录，查找更快。
- 在innoDB里，一个索引就是一棵B+树。每个二级索引也会构建一棵独立的B+树，叶子结点存索引字段值+主键值。

**索引的创建和管理：**
```sql
-- 创建表时建索引
CREATE TABLE user (
    id INT PRIMARY KEY,
    INDEX idx_name(name),
    UNIQUE INDEX idx_email(email)
);

-- 单独创建索引
CREATE INDEX idx_name ON user(name);

-- 删除索引
DROP INDEX idx_name ON user;
```

**索引的作用：**
- 加速查询。
- 唯一索引保证唯一性。
- 组合索引可加速多条件查询。

**InnoDB索引类型：**
- 主键索引（聚簇索引）：数据存储与主键耦合在一起，B+树叶子节点存储整行数据。
- 二级索引（辅助索引）：叶子节点存储主键值及索引字段值。

---

**变量存储的位置：**
- 局部变量：它们通常存储在栈内存中。栈内存主要用于存储方法的参数和局部变量。
- 实例变量：实例变量是对象的一部分，每个对象都有自己的实例变量副本。当创建对象时，实例变量在堆内存中分配内存，随着对象被垃圾回收而销毁。
- 类变量（也就是静态变量）：**类变量是用static修饰的基本类型变量**，它是类的全局变量，被类的所有实例共享。**类变量在方法区中存储**，但实际在运行时，它和类的其他静态成员（如静态方法）相关联。
- 数组中的基本类型元素：数组本身是一个对象，存储在堆内存中。数组中的基本类型元素作为数组对象的一部分，也存储在堆内存中。

---
## ThreadLocal

**ThreadLocal 核心定位**
- 线程隔离而非线程共享：每个线程都有变量 **副本**，避免竞争、无须加锁。  
- 典型应用：用户会话信息、`SimpleDateFormat`、DB/Redis 连接、分布式 TraceId 等。

**数据结构总览**
```
Thread      ──┐
             │   ThreadLocalMap (每个线程 1 份)
             │   ┌───────────────────────────────┐
             └──►│ Entry[ ] (开放寻址 + 线性探测) │
                 └───────────────────────────────┘
                               │
                               ├─ key  : WeakReference<ThreadLocal<?>>
                               └─ value: Object        (强引用)
```

**set / get / remove 流程：**
1. `set(T val)`
   1. 计算 key.hashCode()  
   2. 在线程自己的 `ThreadLocalMap` 查找空槽或同 key 槽  
   3. 写入 value；如遇替换 & 发现 **stale entry** ⇒ 触发 `expungeStaleEntry()` 清理
2. `get()`
   1. 定位槽位；若 key 匹配直接返回  
   2. 若 slot.key 已被 GC ⇒ **找不到** → 调用 `set(initialValue)`
3. `remove()`
   1. 将槽位 value 设 null，key 设 null  
   2. `expungeStaleEntry()` 连带清理 cluster

<br>

**内存泄漏原因:**

• key 弱引用：`ThreadLocal` 对象被 GC 后，`Entry.key == null`。  
• value 强引用：只要线程活着，value 就跟随 `ThreadLocalMap` 活着。  
• 在线程池场景中，线程长期不销毁，**遗留 value** ⇒ 堆占用持续增长。  

解决：
1. 业务结束立即 `remove()`  
2. 将 `ThreadLocal` 声明为 **static final**（生命周期与 JVM 同步） 
    - static final 变量生命周期和类加载器、JVM 一样长，只要类还在，ThreadLocal 实例就不会被回收为 null。
这样 ThreadLocalMap 的 entry 的 key 永远不是 null，不会出现孤儿 value 悬挂，GC 能正常回收 value（GC root可达）。

---

## SpringMVC 是什么东西？
SpringMVC 是 Spring Framework 提供的一个基于 MVC（Model-View-Controller，模型-视图-控制器）设计模式的 Web 框架。它用于帮助开发者高效、灵活地构建 Web 应用，属于 Java EE 技术体系中的表现层（Web 层）解决方案。

**核心流程**
- 用户通过浏览器发起 HTTP 请求；
- 前端控制器 DispatcherServlet 拦截所有请求（配置在 web.xml 或 Spring Boot 自动配置）；
- DispatcherServlet 根据 HandlerMapping 找到处理该请求的 Controller 方法（Handler）；
- HandlerAdapter 调用具体的 Controller 方法处理业务逻辑；
- Controller 方法返回 ModelAndView（模型和视图）或直接返回数据（如 @ResponseBody 支持的 JSON）；
- ViewResolver 解析视图名，生成最终的视图（如 JSP、Thymeleaf 等）；
- DispatcherServlet 响应数据或页面给浏览器。

**核心注解：**
1. **控制器相关注解**
- @Controller
    声明一个控制器类，交由Spring IOC容器管理，通常用于返回视图（页面）。
    面试延伸：和@RestController的区别？

- @RestController
    组合注解，相当于@Controller + @ResponseBody，返回JSON等数据，常用于前后端分离项目。

2. **请求映射相关**
- @RequestMapping
    作用于类或方法，映射HTTP请求路径和方法（GET/POST等）。
    <br>属性：value（路径），method（请求方式），consumes，produces等。
    <br>面试延伸：可否作用于类和方法？映射优先级？

- @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
    @RequestMapping的语法糖，分别对应GET、POST等HTTP方法。
    <br>推荐RESTful风格开发时使用。

3. **参数绑定和数据获取**
- @RequestParam
获取请求参数（query、form），支持默认值、是否必填。
例：
```java
@RequestParam(name = "id", required = false, defaultValue = "0") Integer id
```

- @PathVariable
获取路径中的变量（如/rest/{id}），常用于RESTful API。
例：
```java
@PathVariable("id") Long id
```

- @RequestBody
绑定请求体（通常是JSON），自动反序列化为Java对象，常用于POST/PUT。
例：
```java
@RequestBody UserDTO user
```

- @ModelAttribute
用于表单提交，参数绑定到对象，用于复杂类型接收，支持前置处理方法。

- @RequestHeader
获取HTTP请求头参数。
例：
```java
@RequestHeader("token") String token
```

- @CookieValue
获取Cookie中的值。

4. **响应相关**
- @ResponseBody
方法返回值序列化为JSON/XML等数据格式，直接写到HTTP响应体，常用于API接口。
面试延伸：和@Controller/@RestController配合使用场景。

- @ResponseStatus
指定方法/类返回的HTTP状态码。
例：@ResponseStatus(HttpStatus.CREATED)


---

## 幂等性问题及其解决方案
**幂等性（Idempotence)**<br>
是指一个操作无论执行多少次，产生的结果与执行一次时相同。在后端开发中，幂等性设计尤为重要，主要原因有：
- 用户重复提交：如用户误操作或恶意攻击，导致同一请求多次发起。
- 网络重试机制：在分布式架构下，为保证数据一致性，服务间可能会因超时进行自动重试，导致接口被多次调用。<br>
因此，数据变更类接口（如下单、支付、转账等）必须保证幂等性，即多次调用只会影响数据一次。

**常见解决方案**
- 数据库唯一约束<br>
通过数据库唯一键（如订单号、流水号）保证数据唯一性。
多次插入相同数据时，数据库抛出唯一约束异常，避免重复数据写入。<br>
适用场景：订单创建、用户注册等。

- Redis分布式锁（setnx/setIfAbsent）<br>
利用setnx命令为每个操作生成唯一key，只有首次请求能成功写入并处理，后续请求因key已存在而被拒绝。<br>
常用于消息队列消费、接口防重等场景。

- 状态机机制<br>
通过数据的状态流转控制幂等性，如订单状态只能从“待支付”变为“已支付”，再次提交不会重复变更。<br>
适用需要多阶段、状态不可逆的业务流程。

- Token机制<br>
前端请求前先向后端获取唯一token，每次操作时携带token，后端校验后立即失效，确保同一token只处理一次。<br>
适合防止表单重复提交等场景。

- 乐观锁<br>
通过版本号（version）或时间戳字段控制并发修改，保证数据只被成功修改一次。<br>
适合高并发场景下的数据更新操作。
<br>

<span style="color=red">**实现幂等性的核心思想有两类：**</span>
- 接口只允许执行一次：如唯一约束、分布式锁、token机制等。
- 数据变更只产生一次影响：如状态机、乐观锁、去重表等。

---

## Java线程状态

Java线程一共有6种状态，它们在java.lang.Thread.State枚举中被正式定义。如下：

| 状态名         | 说明                                                                                 |
|----------------|-----------------------------------------------------------------------------------------------------|
| NEW            | 新建状态，线程对象已创建，但尚未调用`start()`启动。                                                   |
| RUNNABLE       | 可运行状态，包括“正在运行”和“就绪等待CPU调度”。                                                      |
| BLOCKED        | 阻塞状态，等待获取某个对象的排它锁（synchronized），比如进入同步块时被其他线程占用。                   |
| WAITING        | 等待状态，线程主动等待（如`Object.wait()`、`Thread.join()`、`LockSupport.park()`），没有超时时间，需被唤醒。|
| TIMED_WAITING  | 超时等待，和WAITING类似，但有超时时间（如`Thread.sleep(ms)`、`wait(ms)`、`join(ms)`等）。              |
| TERMINATED     | 终止状态，线程已经执行完毕或抛出未捕获异常。                                                          |

**常考点：**<br>

**sleep和wait的区别**
- **sleep**<br>
属于Thread类的静态方法（Thread.sleep(ms)）。
让当前线程“睡眠”指定时间，不释放锁，时间到自动恢复运行。<br>
- **wait**<br>
属于Object类的实例方法（obj.wait()）。<br>
让当前线程进入等待状态，同时释放所持有的对象锁（monitor），必须在synchronized块/方法内调用，需用notify/notifyAll或时间超时唤醒。

  - 线程在synchronized块内部调用obj.wait()时，会释放obj的monitor锁，并进入WAITING状态，等待被notify()/notifyAll()唤醒。
  释放锁后，其他线程可以获得obj的锁，进入synchronized(obj)块执行代码。
  - 当线程被notify()或notifyAll()唤醒后，不是立刻恢复执行，而是进入“就绪队列”，等待重新获得锁。


**线程池的线程生命周期和普通线程的区别**
- **普通线程**
  - 生命周期短：一般是new Thread()后start()，执行完run()方法就TERMINATED，线程对象被GC回收。
  - 一次性：每个线程只能用一次，不能复用。
  - 频繁创建销毁：大量并发任务时，频繁创建和销毁线程，带来较大系统开销（线程栈、上下文切换等）。
- **线程池中的线程（Worker线程）**
  - 生命周期长：线程池创建一定数量的工作线程（Worker），线程不会在每次任务结束后立即销毁，而是长时间存活，等待后续任务。
  - 可复用：一个线程可以被多次复用，循环从任务队列中取任务并执行。
  - 统一管理：线程的创建、调度、回收都被线程池自动管理，避免系统资源浪费。
  - 线程状态变化：线程空闲时处于WAITING或TIMED_WAITING（阻塞在任务队列），有任务时进入RUNNABLE，只有线程池关闭或特殊场景才会真正TERMINATED。

**线程池的线程什么时候会被销毁？**
- **线程池主动关闭**
调用shutdown()或shutdownNow()，线程池不再接受新任务，已完成的任务处理完后线程终止。
- **空闲线程超时销毁**（非核心线程，或corePoolSize=0时核心线程也可超时）
  - ThreadPoolExecutor有corePoolSize和maximumPoolSize两个参数。 超过corePoolSize的线程（也就是“非核心线程”）如果空闲时间超过keepAliveTime，会被回收销毁。

**线程的三种实现方式：**
- 继承 Thread 类:
直接继承java.lang.Thread，重写run()方法。
缺点：单继承局限，不推荐用于实际生产。
- 实现 Runnable 接口:
推荐方式之一，解耦任务与线程，适合与线程池配合。
- 实现 Callable 接口 + Future:
可以有返回值和异常，配合线程池和Future一起用，是最推荐的现代方式。
    - Future的作用<br>
Future 表示一个“未来可以获取的结果”，用于异步任务的结果接收、状态查询和取消控制。可以在任务还没执行完的时候，对Future做轮询或等待，等任务结果出来之后再获取。
    ```java
        // 阻塞直到任务执行完毕，获取返回值
        Integer result = future.get(); 
        // 用于轮询判断任务是否完成。
        boolean isDone = future.isDone();
        // 尝试中断任务线程
        future.cancel(true);
    ```


**线程池提交任务的类型**
Runnable和Callable。
- Runnable无返回值且不能抛出受检异常，适合只需执行任务的场景。
- Callable有返回值且可抛出异常，适合需要结果或异常处理的任务。

---

**HashMap 的 put 方法流程**
- 判断表是否初始化<br>
如果 table（数组）为空，调用 resize() 初始化默认容量（16）。
- 计算 key 的 hash 值<br>
通过 hash(key) 方法，扰动运算，减少哈希冲突。
- 定位数组下标<br>
通过 (n - 1) & hash 计算数组索引。
- 查找桶，处理冲突<br>
如果该桶为空，直接插入新节点。
如果桶已存在节点（哈希冲突）：
- 遍历链表/红黑树<br>看是否存在“相同key”，存在则覆盖 value。
否则，尾插新节点。
- 链表转红黑树（JDK8 新特性）<br>
如果链表长度超过阈值（默认8），且数组容量>=64，链表转为红黑树，提升查询效率。
- 扩容判断<br>
插入后如果 size 超过 threshold（容量*负载因子），调用 resize() 扩容。

---

**字节码的好处**<br>
javac将.java编译成.class，一次编译到处可以运行，
但是对于不同的操作系统，将字节码转为机器码的解释器也不同，

---

**Java 异常体系**
- **Throwable**：所有错误和异常的父类
    - **Error**：严重错误，程序无法处理（如内存溢出 `OutOfMemoryError`、栈溢出 `StackOverflowError`）
    - **Exception**：可捕获异常
        - **RuntimeException**（运行时异常，非受检异常，往往是逻辑错误）：非强制捕获，常见有
            - `NullPointerException`
            - `ArrayIndexOutOfBoundsException`
            - `ClassCastException`
            - `ArithmeticException`
        - **CheckedException**（受检异常，编译时异常）：编译器强制处理，需显式 `try-catch` 或 `throws`
            - 如：`IOException`、`SQLException`
- **异常处理关键字**
    - `throws`：用于方法声明，通知调用者该方法可能抛出异常
    - `try-catch`：用于捕获并处理异常

---

**类加载机制（双亲委派模型）**
- **类加载器加载类的流程**
    1. 先检查父加载器是否已加载该类（向上委托）
    2. 父类加载器无法加载时，才由当前加载器加载
- **优势**
    - 避免类的重复加载和安全问题
- **常见类加载器**
    - 启动类加载器（Bootstrap ClassLoader）：JVM内置加载器，负责加载 Java 核心类库。
    - 扩展类加载器（Extension ClassLoader）：负责加载 Java 扩展类库
    - 应用类加载器（App ClassLoader）

---

**JVM存储空间**

| 区域         | 作用                                                         |
|--------------|--------------------------------------------------------------|
| 程序计数器   | 记录当前线程所执行的字节码行号指示器，是线程私有的。        |
| 虚拟机栈     | 存储局部变量表、操作数栈、方法出口等，随线程生命周期创建/销毁。 |
| 本地方法栈   | 为 Native 方法服务，与虚拟机栈类似。                        |
| 堆（Heap）   | 对象实例和数组的主要存储区，GC 管理的主要区域（线程共享）。   |
| 方法区       | 存储类的结构信息、常量、静态变量、JIT 编译后的代码等。       |

**程序计数器为什么是线程私有？**
每个线程都有自己的程序计数器，用于记录该线程正在执行的字节码指令的地址。这是为了确保每个线程能够独立地执行代码，避免线程之间的相互干扰。

**什么是栈帧？溢出怎么发生？**
栈帧是虚拟机栈中的一个逻辑单元，用于存储方法的**局部变量表**、**操作数栈**、**方法出口**等信息。每个方法的调用都会创建一个新的栈帧，并将其压入虚拟机栈中。当栈帧的大小超过虚拟机栈的限制，或者线程的栈深度超过 JVM 的限制时，就会发生栈溢出（StackOverflowError）。

**本地方法栈和虚拟机栈的区别？**
本地方法栈和虚拟机栈在功能上类似，都用于存储方法的局部变量、操作数栈等信息。但本地方法栈主要为 Native 方法服务，即用于**执行非 Java 代码的本地方法**。Native 方法通常用于调用操作系统原生 API 或其他低级操作，这些方法的执行不受 Java 虚拟机的管理，因此需要单独的栈来处理。

**新生代/老年代区别？**
堆是 Java 内存中最大的一块，用于存储对象实例和数组。新生代是堆中用于存储新创建对象的区域，垃圾回收在此区域频繁发生。老年代用于存储经过多次垃圾回收仍然存活的对象。

---

## 多态
多态指的是父类引用或接口引用在不同子类对象上表现出不同的行为。

**接口多态：**
```java
interface Animal {
    void speak();
}
class Dog implements Animal {
    public void speak() { System.out.println("Woof!"); }
}
class Cat implements Animal {
    public void speak() { System.out.println("Meow!"); }
}

Animal a1 = new Dog();
Animal a2 = new Cat();
a1.speak(); // 输出 Woof!
a2.speak(); // 输出 Meow!
```

**父类多态:**
```java
class Animal {
    void speak() { System.out.println("Animal sound"); }
}
class Dog extends Animal {
    void speak() { System.out.println("Woof!"); }
}
class Cat extends Animal {
    void speak() { System.out.println("Meow!"); }
}

Animal a = new Dog();
a.speak(); // 输出 Woof!
a = new Cat();
a.speak(); // 输出 Meow!
```

多态的实现依赖于方法的重写（override），和方法的动态绑定。<br>
多态只适用于“非静态、非私有、非final”的实例方法。

**动态绑定**<br>
多态的实现依赖于动态绑定（Dynamic Binding），也叫运行时绑定——即方法调用在运行时，根据对象的实际类型确定要执行的方法体。
Java对实例方法采用动态绑定，对静态方法、私有方法、final方法采用静态绑定（编译期绑定）。
- 静态方法属于类，不属于对象，方法调用在编译时就确定了。
- 私有方法只在当前类可见，子类无法访问和重写，谈不上“多态”。
- final方法不允许被子类重写，只有一个实现，不存在“多种表现”。

**为什么说多态“使解耦”**
- 调用方只依赖接口/父类，不关心具体实现类。
- 代码只面向抽象层，具体实现可以自由替换、扩展，调用方无需修改，极大提升了灵活性和可扩展性。

---

**怎么保证Redis和数据库(MySQL)的数据一致性？**
- **方案一：Cache Aside Pattern（旁路缓存/主动失效）**
  - **写操作（更新数据）**<br>
    先写数据库
    <br>再删除/更新缓存
  - **读操作**<br>
    先查缓存，没有再查数据库并回写缓存<br>
优点：实现简单，适合大多数场景<br>
缺点：极端情况下会有短暂不一致

  - **延迟双删策略**<br>
写数据库→删缓存→延迟一段时间再删缓存，降低并发下缓存脏数据风险。
- **方案二：先删除缓存，后写数据库**<br>
先删缓存，再写数据库，防止并发脏读，但如果写数据库失败会导致缓存被清空但数据没更新。

---

**SQL 占位符与参数注入**
- **#{}**：MyBatis语法，JDBC预编译，防止SQL注入，推荐使用
- **${}**：字符串直接替换，容易注入风险，慎用
- 示例：  
  ```sql
  select * from ${tableName} where id = #{id}
  ```

**注入风险演示**<br>
假如接口允许用户传tableName参数为：

```sql
user; drop table user; --
```
整个SQL会变成：

```sql
select * from user; drop table user; -- where id = ?
```
这样攻击者就能删除表！

---

**为什么用Redis而不用本地缓存？**
- 本地缓存的特点：
本地缓存指的是将数据缓存在应用服务器的内存中（比如用Guava、Caffeine、Ehcache等）。
  - 优点：读取速度极快，毫无网络开销，实现简单。
  - 缺点：
    - 数据一致性差：各节点缓存各自维护，更新后数据很难实时同步，容易出现脏数据。
    - 容量受限：受限于单机内存，缓存空间有限且扩展困难。
    - 无法支撑分布式场景：应用部署在多台服务器时，缓存内容不共享，数据极易不一致。
    - 容灾性差：单机宕机缓存全部丢失，无法自动恢复。

- Redis的优势
  - 分布式共享：所有节点都可以访问同一个Redis实例，实现数据共享，天然适配分布式部署。
  - 高性能：Redis基于内存，QPS极高，远远优于数据库。
  - 数据一致性好：数据集中存储，更新同步及时，有效避免本地缓存导致的脏读问题。
  - 可扩展性强：支持持久化、主从、集群，易于横向扩展和容灾。
  - 丰富的数据结构：支持String、Hash、List、Set、SortedSet等多种结构，功能丰富。
  - 原子操作/分布式锁：支持原子性的操作和分布式锁，便于复杂业务场景的实现。

**Redis分布式锁的实现原理**
- 基本实现（SETNX/SET+EX）
  - SETNX（set if not exists）或SET key value NX PX/EX 只在key不存在时设置key，并可加过期时间。
  - 防止死锁：务必加过期时间（EX/PX），防止因进程/节点宕机导致锁无法释放。
    ```shell
    SET lock-key unique-value NX PX 30000
    ```
    - lock-key：锁的唯一标识（如业务类型+资源ID）。
    - unique-value：锁归属者（当前客户端）的唯一标识（如UUID），防止误删他人锁。
    - NX：只有key不存在时才设置
    - PX：锁在30秒后自动过期（防死锁）
- key（锁名）：唯一标识你要保护的资源。比如：lock:order:123、lock:product:456。只要key在，说明这个资源已经被某个客户端“锁住”了，别人不能再获得这把锁。
- value（客户端唯一标识）：标记当前是谁占有这把锁。
只有value等于自己的客户端才有权释放这把锁，防止误删。

- Note: 
    - 该语句唯一地原子地在Redis里创建一个代表资源的Key，Value为获得锁的客户端的唯一标识
    - 解锁操作：
      - 用Get lock_key拿到value
      - 如果是自己的标识则Del lock_key
      - 以上操作都放入Lua写成一条命令
    - 针对同一个业务资源，都用同一个库存做锁标识，谁把这个key先写入Redis，谁就获得这把锁，从而确保分布式系统中同一资源同一时刻只有一个客户端能操作

**Redis限流实现（Lua+Redis）**
- 使用唯一标识（如userId:api:minute）作为key。
- 用户访问时INCR key，首次会创建key并初始化为1。
- 第一次访问时顺带EXPIRE key设置过期时间（比如60秒）。
- 若计数超限，拒绝访问。


**Redis的数据类型*
- String：
  - 最基本类型，适合存储简单数据，如Session、Token、计数器、缓存对象的序列化结果。
  - 业务常见用法：SET key value、GET key、INCR key等。
- List：链表结构，底层是**双向链表**，支持两端插入、弹出，常用于消息队列、任务队列。
- Set：
  - 适合存储无序、唯一元素集合，如点赞、标签、黑名单。
  - 底层是**字典+哈希**。
  - 支持集合运算（交、并、差），常用于社交关系、推荐系统。
  - 典型操作：SADD key member、SREM key member、SISMEMBER key member。
  - 随机弹出元素：SPOP key count。
- Hash：
  - 键值对集合，适合存储对象属性，如用户信息、商品信息等，适合字段更新频繁的场景。
  - 典型用法：HSET key field value、HGET key field。
  - 删除field不会影响其他字段，field删空后key自动被删除。
- ZSet（Sorted Set）：
  - 有序集合，每个元素带一个score，支持排序，常用于排行榜、延时队列。
  - 每个元素带score，支持范围查询和排序。
  - 典型操作：ZADD key score member、ZRANGE key start stop、ZREM key member。
- HyperLogLog：基数统计，用于快速统计海量数据的唯一元素个数，占用内存极小。
- Bitmap：位图，适合海量布尔状态的统计（如签到、在线状态）。
- Geospatial：地理位置相关，支持地理坐标存储与范围、距离计算。

**重点问题**
- **Sorted Set底层为什么用跳表？**
  - 跳表（skiplist）插入、删除、范围查询效率高，且实现简单，适合有序集合频繁操作的场景。这方面要优于平衡树和红黑树。
  - 跳表支持高效的区间范围查找，且并发友好。
  - Redis中的ZSet同时维护了一个跳表和一个字典，保证查找和排序的高性能。
  - B+树更适合存储大量数据由数据库或文件系统的索引结构。

- **Redis常见的key过期删除策略**
  - 主动删除
    - 主动、定时DEL key，或业务逻辑删除，最直接。
  - 惰性删除
    - 只有在访问key时才检查其是否过期，过期则删除。
    - 优点：节省CPU，缺点：不访问可能占内存。
  - 定期删除
    - Redis后台定期随机采样部分key，发现过期则删除。
    - 适中方式，防止内存积压。
  - 惰性+定期结合
      - Redis实际采用“定期+惰性”混合策略：定期批量删除部分过期key，访问时再做惰性删除。

**大量key集中过期的影响**
- 定期删除线程压力大，CPU占用高，可能影响正常服务。
- 内存短时暴涨，风险增大。
- 实际生产建议错开key过期时间，避免“雪崩”。

**为什么不直接“到期就删？**
Redis是高性能KV数据库，为了避免到期瞬间删除大量key造成主线程阻塞（阻塞单线程，影响响应），采用了惰性+定期的渐进清理策略。

**Hash和String存对象的区别**
- 用String存对象
  - 做法：把整个对象序列化（如JSON、Protobuf等），然后以一个String类型保存到Redis。
  ```shell
  set user:1001 '{"id":1001,"name":"Tom","age":18}'
  ```
- 用Hash存对象
  - 做法：对象的每个字段作为hash的field，属性值作为field的value。
  ```shell
  hmset user:1001 id 1001 name Tom age 18
  ```

**总结**



| 方面               | String 存对象                          | Hash 存对象                            |
|--------------------|----------------------------------------|----------------------------------------|
| 读写性能           | 一次读/写整个对象                      | 可单独读/写某个字段，粒度更细          |
| 内存占用           | 适合小对象，序列化后压缩更优           | 小对象 Redis 有专门优化，hash 内存更节省（ziplist 优化） |
| 可维护性           | 改字段需整体反序列化和序列化           | 直接 HSET 某字段，灵活高效             |
| 原子性             | 操作整体，原子性好                     | 单字段操作也具备原子性                 |
| 网络开销           | 取全部字段时网络开销更小               | 只需某字段时，可以只传一部分数据，节省网络带宽 |
| 可读性/可监控性    | value 是串，难以直接分析               | 可直接读到每个字段，便于监控和分析     |
| 灵活性             | 业务变更时需整体改动                   | 字段增删方便，支持动态扩展             |


**用hash做苍穹外卖的购物车：**
- 在 Redis 中，可以使用 Hash 结构来存储这些数据。每个用户的购物车存储在一个独立的 Hash 中，用户 ID 作为 Redis 的键，商品 ID 作为 Hash 的字段，field对应商品ID，而value对应商品数量。
- 用户添加商品是在hash里对应的key里加上一对Key-value
- 查是遍历哈希
- 更是修改value
- 删是删field
- 清空购物车：删key