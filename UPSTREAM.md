# 上游与差异

## 上游参考

- [Anthropic Human Resources Plugin](https://github.com/anthropics/knowledge-work-plugins/tree/658e077ffd7bdd50a12c19ec5ff36fe34c88be8a/human-resources) 的 `comp-analysis`：提供薪酬对标、带宽位置与股权建模的基础任务定义。
- [SAP compa-ratio 文档](https://help.sap.com/docs/successfactors-employee-central/implementing-employee-compensation-data/compa-ratio)：确认 compa-ratio 与带宽中点的计算关系。
- [EEOC Compensation Discrimination 指引](https://www.eeoc.gov/laws/guidance/section-10-compensation-discrimination)：强调可比群与可解释因素需要审慎分析。

## 本项目的改造

上游 Skill 面向其连接器生态，且允许泛化的市场研究与建议。本项目把可复用部分收窄为：本地脱敏输入、明确指标、来源时效、待复核队列和通用 Agent 契约。

它不连接薪酬数据服务，不产生个人薪酬建议，不自动判断公平或合规，也不处理原始个人身份信息。

## 许可证

上游仓库以 Apache License 2.0 发布。本项目保留来源声明，并以 Apache License 2.0 发布；Anthropic 名称仅用于事实性来源说明，不表示关联或背书。
