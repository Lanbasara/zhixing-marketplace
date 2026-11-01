# 知行插件市场

本仓只维护知行的 Claude Code、Codex 和 DSH 分发索引。
产品源码与发布物位于 [Lanbasara/zhixing](https://github.com/Lanbasara/zhixing)。

目前索引为空，首个正式版本进入市场后才提供可安装条目。市场存在不代表产品已发布。

- Claude Code 与 Codex：添加 `Lanbasara/zhixing-marketplace`。
- DSH：添加 `https://raw.githubusercontent.com/Lanbasara/zhixing-marketplace/main/dsh/index.json`。

`releases.json` 保存不可改写的发行历史。三端索引由源码仓的市场候选生成，固定
源提交和 plugin 子目录。维护者只在源 Release 成功后，通过本仓独立 PR 更新
四个索引文件；CI 核对源标签、版本、调用包元数据以及历史保留。

开发与恢复步骤见源码仓的
[RELEASING.md](https://github.com/Lanbasara/zhixing/blob/main/RELEASING.md)。
