## Glados 青龙自动签到

感谢不知名大佬的glados签到脚本，源码只进行对失效部分进行修复处理，其余注释并未改动删除

#### 修复点：

解决glados域名更换导致的签到失败

### 青龙面板使用步骤

1. 青龙面板创建订阅，然后复制以下命令到名称中：  
   ​`ql repo https://github.com/JackieBan/Glados-checkin-repair.git "checkin.py" "" ""`​  
   订阅管理--创建订阅--copy指令--填写名称和定时规则--确定（图片前两个步骤反了，不要在意这些细节）  
   ​<img width="1874" height="962" alt="image-20260130213506-6eqos2y" src="https://github.com/user-attachments/assets/2bf843d5-315b-49c1-ac54-4c6b521399b0" />
2. 添加依赖  
   ​<img width="1874" height="962" alt="image-20260128093704-41087jx" src="https://github.com/user-attachments/assets/daba7efe-9f45-4553-b20a-ce5e27b88dfc" />
3. 运行订阅  
   ​<img width="1874" height="962" alt="image-20260128093704-41087jx" src="https://github.com/user-attachments/assets/e51b1b6c-6eb0-4832-ac94-bb5792731871" />
4. 创建环境变量  
   环境变量--创建变量--名称HIFINI_COOKIE--cookie路径依旧是F12中去寻找  
   在官网F12，按照流程所示找到相对应位置：网络--文档，按ctrl+R，进行刷新，第一行便是cookie的位置，进行全部复制  
   <img width="1874" height="962" alt="image-20260131201827-uirzqtz" src="https://github.com/user-attachments/assets/7c93484c-bd65-451a-81c0-174d7b61e8f6" />
5. 等待运行（第一次在定时任务找到此任务手动运行进行检查）
