# 飞书可选读取

飞书不是本 Skill 的必要依赖。用户明确要求读取飞书材料时，先确认当前身份：

```bash
lark-cli auth status --json --verify
```

只读取用户指定的脱敏带宽表或市场数据表：

```bash
lark-cli sheets +cells-get --url "https://example.feishu.cn/sheets/shtXXXX" \
  --sheet-name "脱敏薪酬带宽" --range "A1:Z200" --include value,formula --as user --json
```

先向用户展示将读取的范围，再将内容转换为本地脱敏 JSON。不要默认搜索“薪酬”相关全库文档，不要读取个人薪酬明细、审批、聊天或其他非必要内容。

本 Skill 默认没有写入能力。需要更新表格、发消息、创建审批或同步 HRIS 时，先输出草案、获取单独确认、调用对应系统能力，并读取目标记录验证。
