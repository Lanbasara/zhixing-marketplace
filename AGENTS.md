# 知行市场维护

本仓只有分发索引，不维护或复制技能正文。只操作 zhixing 与 zhixing-marketplace。
从最新 origin/main 创建任务分支，通过 PR 和必需 catalog 检查更新 main。

正式更新使用源码仓 scripts/marketplace.py 对不可变 tag 生成的候选；确认源
GitHub Release 成功，candidate.json 的市场基线仍等于当前 origin/main。
只更新 releases.json、.claude-plugin/marketplace.json、
.agents/plugins/marketplace.json、dsh/index.json。candidate.json 留作外部证据。
运行 python3 scripts/check.py --source <源码 checkout> --base <市场 base SHA>。
新源提交须由 annotated tag 固定、可达源码 origin/main；历史记录不得改写。
不得直接 push main、强推、移动标签或改动其他产品。
