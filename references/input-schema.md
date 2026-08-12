# 输入结构

生成器读取一个脱敏 JSON。

```json
{
  "analysis_scope": {
    "purpose": "年度薪酬结构复核",
    "currency": "CNY",
    "period": "annual base salary"
  },
  "source_materials": [
    {"id": "band-v1", "type": "local-sheet", "label": "薪酬带宽", "as_of": "2026-07-01"}
  ],
  "bands": [
    {"band_id": "ENG-4-CN", "job_family": "工程", "level": "4", "location": "中国", "minimum": 360000, "midpoint": 450000, "maximum": 540000}
  ],
  "people": [
    {"person_ref": "P-001", "band_id": "ENG-4-CN", "base_salary": 405000, "explained_factors": ["time_in_level"]}
  ],
  "market_benchmarks": [
    {"source_label": "HR 提供的市场调研", "as_of": "2026-06-30", "job_family": "工程", "level": "4", "location": "中国", "currency": "CNY", "period": "annual base salary", "p25": 390000, "p50": 450000, "p75": 510000}
  ]
}
```

`market_benchmarks` 可为空。生成器不联网补市场数据；每条市场数据都必须提供来源、日期、币种和周期。

允许的 `explained_factors`：`time_in_level`、`time_in_role`、`job_scope`、`scarce_skill`、`location_policy`、`approved_exception`。它们只是待人工复核的标签，不能替代事实说明。
