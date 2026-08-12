#!/usr/bin/env python3
"""Validate and render a de-identified compensation structure analysis."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SENSITIVE = {
    "name", "full_name", "employee_name", "email", "phone", "mobile", "address",
    "age", "gender", "sex", "ethnicity", "race", "religion", "health", "disability",
    "medical", "family", "marital", "pregnancy", "salary_history", "previous_salary",
    "姓名", "邮箱", "电话", "住址", "年龄", "性别", "民族", "宗教", "健康", "家庭",
    "婚姻", "怀孕", "薪酬历史", "前薪",
}
ALLOWED_FACTORS = {"time_in_level", "time_in_role", "job_scope", "scarce_skill", "location_policy", "approved_exception"}


def reject_unknown_fields(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(str(key) for key in value if str(key) not in allowed)
    if unknown:
        raise ValueError(f"{label} contains unsupported fields: " + ", ".join(unknown))


def normalized_key(value: Any) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def sensitive_paths(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            current = f"{path}.{key}" if path else str(key)
            if normalized_key(key) in SENSITIVE:
                hits.append(current)
            hits.extend(sensitive_paths(child, current))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(sensitive_paths(child, f"{path}[{index}]"))
    return hits


def require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def require_amount(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    try:
        amount = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number") from exc
    if amount < 0:
        raise ValueError(f"{label} cannot be negative")
    return amount


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise ValueError("input root must be an object")
    reject_unknown_fields(spec, {"analysis_scope", "source_materials", "bands", "people", "market_benchmarks"}, "input root")
    hits = sensitive_paths(spec)
    if hits:
        raise ValueError("sensitive fields are not allowed: " + ", ".join(hits))
    scope = spec.get("analysis_scope")
    if not isinstance(scope, dict):
        raise ValueError("analysis_scope is required")
    reject_unknown_fields(scope, {"purpose", "currency", "period"}, "analysis_scope")
    currency = require_text(scope.get("currency"), "analysis_scope.currency")
    period = require_text(scope.get("period"), "analysis_scope.period")
    purpose = require_text(scope.get("purpose"), "analysis_scope.purpose")
    sources = spec.get("source_materials") or []
    if not isinstance(sources, list):
        raise ValueError("source_materials must be a list")
    for index, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            raise ValueError(f"source_materials[{index}] must be an object")
        reject_unknown_fields(source, {"id", "type", "label", "as_of"}, f"source_materials[{index}]")
        for field in ("id", "type", "label", "as_of"):
            require_text(source.get(field), f"source_materials[{index}].{field}")
        if {"content", "body", "raw", "path", "token", "access_token"}.intersection(map(normalized_key, source)):
            raise ValueError(f"source_materials[{index}] must contain metadata only")
    bands = spec.get("bands")
    if not isinstance(bands, list) or not bands:
        raise ValueError("bands must contain at least one band")
    band_map: dict[str, dict[str, Any]] = {}
    for index, band in enumerate(bands, 1):
        if not isinstance(band, dict):
            raise ValueError(f"bands[{index}] must be an object")
        reject_unknown_fields(band, {"band_id", "job_family", "level", "location", "minimum", "midpoint", "maximum"}, f"bands[{index}]")
        band_id = require_text(band.get("band_id"), f"bands[{index}].band_id")
        if band_id in band_map:
            raise ValueError(f"duplicate band_id: {band_id}")
        for field in ("job_family", "level", "location"):
            require_text(band.get(field), f"bands[{index}].{field}")
        minimum = require_amount(band.get("minimum"), f"bands[{index}].minimum")
        midpoint = require_amount(band.get("midpoint"), f"bands[{index}].midpoint")
        maximum = require_amount(band.get("maximum"), f"bands[{index}].maximum")
        if not minimum < midpoint < maximum:
            raise ValueError(f"bands[{index}] must satisfy minimum < midpoint < maximum")
        band_map[band_id] = {**band, "minimum": minimum, "midpoint": midpoint, "maximum": maximum}
    people = spec.get("people")
    if not isinstance(people, list) or not people:
        raise ValueError("people must contain at least one de-identified record")
    refs: set[str] = set()
    normalized_people: list[dict[str, Any]] = []
    for index, person in enumerate(people, 1):
        if not isinstance(person, dict):
            raise ValueError(f"people[{index}] must be an object")
        reject_unknown_fields(person, {"person_ref", "band_id", "base_salary", "explained_factors"}, f"people[{index}]")
        ref = require_text(person.get("person_ref"), f"people[{index}].person_ref")
        if ref in refs:
            raise ValueError(f"duplicate person_ref: {ref}")
        refs.add(ref)
        band_id = require_text(person.get("band_id"), f"people[{index}].band_id")
        if band_id not in band_map:
            raise ValueError(f"people[{index}] references unknown band_id: {band_id}")
        base_salary = require_amount(person.get("base_salary"), f"people[{index}].base_salary")
        factors = person.get("explained_factors") or []
        if not isinstance(factors, list) or any(normalized_key(item) not in ALLOWED_FACTORS for item in factors):
            raise ValueError(f"people[{index}].explained_factors must use approved neutral factor labels")
        normalized_people.append({"person_ref": ref, "band_id": band_id, "base_salary": base_salary, "explained_factors": factors})
    benchmarks = spec.get("market_benchmarks") or []
    if not isinstance(benchmarks, list):
        raise ValueError("market_benchmarks must be a list")
    for index, benchmark in enumerate(benchmarks, 1):
        if not isinstance(benchmark, dict):
            raise ValueError(f"market_benchmarks[{index}] must be an object")
        reject_unknown_fields(benchmark, {"source_label", "as_of", "job_family", "level", "location", "currency", "period", "p25", "p50", "p75"}, f"market_benchmarks[{index}]")
        for field in ("source_label", "as_of", "job_family", "level", "location", "currency", "period"):
            require_text(benchmark.get(field), f"market_benchmarks[{index}].{field}")
        for field in ("p25", "p50", "p75"):
            require_amount(benchmark.get(field), f"market_benchmarks[{index}].{field}")
        if not float(benchmark["p25"]) <= float(benchmark["p50"]) <= float(benchmark["p75"]):
            raise ValueError(f"market_benchmarks[{index}] must satisfy p25 <= p50 <= p75")
    return {"scope": {"currency": currency, "period": period, "purpose": purpose}, "bands": band_map, "people": normalized_people, "sources": sources, "benchmarks": benchmarks}


def classify(salary: float, band: dict[str, Any]) -> str:
    if salary < band["minimum"]:
        return "低于带宽"
    if salary > band["maximum"]:
        return "高于带宽"
    return "区间内"


def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    data = validate_spec(spec)
    rows: list[dict[str, Any]] = []
    for person in data["people"]:
        band = data["bands"][person["band_id"]]
        salary = person["base_salary"]
        rows.append({
            **person,
            "job_family": band["job_family"], "level": band["level"], "location": band["location"],
            "minimum": band["minimum"], "midpoint": band["midpoint"], "maximum": band["maximum"],
            "compa_ratio": round(salary / band["midpoint"], 4),
            "range_penetration": round((salary - band["minimum"]) / (band["maximum"] - band["minimum"]), 4),
            "position": classify(salary, band),
        })
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["band_id"]].append(row)
    summaries = []
    for band_id, members in sorted(grouped.items()):
        salaries = [member["base_salary"] for member in members]
        summaries.append({
            "band_id": band_id, "headcount": len(members), "average_base_salary": round(statistics.mean(salaries), 2),
            "median_base_salary": round(statistics.median(salaries), 2),
            "outside_band_count": sum(member["position"] != "区间内" for member in members),
        })
    review_queue = []
    for row in rows:
        if row["position"] != "区间内":
            review_queue.append({"person_ref": row["person_ref"], "reason": row["position"], "next_step": "核对带宽映射、数据周期与已批准业务因素"})
    for summary in summaries:
        if summary["headcount"] < 3:
            review_queue.append({"band_id": summary["band_id"], "reason": "样本量小于 3", "next_step": "仅作描述性呈现，不作群体比较结论"})
    return {"schema_version": "1.0", "skill": "hr-compensation-analysis", "display_name": "薪酬结构分析", "analysis_scope": data["scope"], "source_materials": data["sources"], "market_benchmarks": data["benchmarks"], "records": rows, "band_summaries": summaries, "review_queue": review_queue}


def number(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def render_markdown(report: dict[str, Any]) -> str:
    scope = report["analysis_scope"]
    lines = [f"# 薪酬结构分析｜{scope['purpose']}", "", f"- 货币：{scope['currency']}", f"- 周期：{scope['period']}", f"- 匿名记录：{len(report['records'])} 条", "", "## 材料来源与时效", "", "| 来源 | 类型 | 截止日期 |", "|---|---|---|"]
    lines.extend(f"| {source['label']} | {source['type']} | {source['as_of']} |" for source in report["source_materials"])
    lines.extend(["", "## 个体带宽位置（匿名）", "", "| 记录 | 带宽 | 基础薪资 | compa-ratio | range penetration | 位置 |", "|---|---|---:|---:|---:|---|"])
    for row in report["records"]:
        lines.append(f"| {row['person_ref']} | {row['band_id']} | {number(row['base_salary'])} | {row['compa_ratio']:.2f} | {row['range_penetration']:.1%} | {row['position']} |")
    lines.extend(["", "## 按带宽汇总", "", "| 带宽 | 样本 | 平均基础薪资 | 中位数 | 带宽外 |", "|---|---:|---:|---:|---:|"])
    for summary in report["band_summaries"]:
        lines.append(f"| {summary['band_id']} | {summary['headcount']} | {number(summary['average_base_salary'])} | {number(summary['median_base_salary'])} | {summary['outside_band_count']} |")
    if report["market_benchmarks"]:
        lines.extend(["", "## 市场数据（用户提供）", "", "| 来源 | 截止日期 | 岗位/级别/地点 | P25 | P50 | P75 |", "|---|---|---|---:|---:|---:|"])
        for benchmark in report["market_benchmarks"]:
            label = f"{benchmark['job_family']} / {benchmark['level']} / {benchmark['location']}"
            lines.append(f"| {benchmark['source_label']} | {benchmark['as_of']} | {label} | {number(float(benchmark['p25']))} | {number(float(benchmark['p50']))} | {number(float(benchmark['p75']))} |")
    lines.extend(["", "## 待复核队列", ""])
    if report["review_queue"]:
        for item in report["review_queue"]:
            target = item.get("person_ref") or item.get("band_id")
            lines.append(f"- `{target}`：{item['reason']}；{item['next_step']}。")
    else:
        lines.append("- 当前输入未发现需要自动标记的项目；这不构成定薪、合规或公平结论。")
    lines.extend(["", "## 人工决策边界", "", "- 本报告只描述已提供的脱敏数据与计算结果。", "- compa-ratio 和 range penetration 不能直接推导个人贡献、市场竞争力、调薪金额或法律结论。", "- 人类负责人需要确认可比范围、数据时效、业务解释与任何薪酬决定。", ""])
    return "\n".join(lines)


def load_spec(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON input: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv or sys.argv[1:])
    try:
        report = analyze(load_spec(args.input))
        output = render_markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
