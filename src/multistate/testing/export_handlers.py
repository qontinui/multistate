"""Export Handlers - Handles export of tracking results to various formats.

This module provides export functionality separated from the main PathTracker
to improve modularity and maintainability.
"""

import csv
import json
import logging
from collections.abc import Sequence
from typing import Literal

from multistate.testing.models import (
    CoverageMetrics,
    Deficiency,
    PathHistory,
    TransitionExecution,
    TransitionStatistics,
)

logger = logging.getLogger(__name__)


class ExportHandlers:
    """Handles export of tracking results to various formats.

    This class provides export functionality for:
    - JSON export with configurable detail levels
    - HTML reports with styling
    - CSV export for data analysis
    - Markdown reports for documentation

    Thread Safety:
        Individual export operations are atomic file writes.
    """

    def export_results(
        self,
        output_path: str,
        format: Literal["json", "html", "csv", "markdown"],
        metrics: CoverageMetrics,
        executions: Sequence[TransitionExecution],
        statistics: Sequence[TransitionStatistics],
        deficiencies: Sequence[Deficiency],
        paths: Sequence[PathHistory],
        include_screenshots: bool = True,
        include_variables: bool = False,
    ) -> None:
        """Export tracking results to file.

        Args:
            output_path: Path to output file
            format: Export format (json, html, csv, markdown)
            metrics: Coverage metrics to export
            executions: Execution records
            statistics: Transition statistics
            deficiencies: Detected deficiencies
            paths: Path histories
            include_screenshots: Include screenshot references (JSON/HTML only)
            include_variables: Include variable snapshots (JSON only)

        Raises:
            ValueError: If format is not supported
        """
        if format == "json":
            self._export_json(
                output_path,
                metrics,
                executions,
                statistics,
                deficiencies,
                paths,
                include_screenshots,
                include_variables,
            )
        elif format == "html":
            self._export_html(output_path, metrics, deficiencies, include_screenshots)
        elif format == "csv":
            self._export_csv(output_path, executions)
        elif format == "markdown":
            self._export_markdown(output_path, metrics, deficiencies)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported results to {output_path} ({format})")

    def _export_json(
        self,
        output_path: str,
        metrics: CoverageMetrics,
        executions: Sequence[TransitionExecution],
        statistics: Sequence[TransitionStatistics],
        deficiencies: Sequence[Deficiency],
        paths: Sequence[PathHistory],
        include_screenshots: bool,
        include_variables: bool,
    ) -> None:
        """Export results to JSON."""
        data = {
            "metrics": metrics.to_dict(),
            "executions": [e.to_dict() for e in executions],
            "statistics": [s.to_dict() for s in statistics],
            "deficiencies": [d.to_dict() for d in deficiencies],
            "paths": [p.to_dict() for p in paths],
        }

        # Remove screenshots/variables if requested
        execution_list: list[dict] = data["executions"]  # type: ignore[assignment]
        if not include_screenshots:
            for execution in execution_list:
                execution.pop("screenshot_path", None)

        if not include_variables:
            for execution in execution_list:
                execution.pop("variables_snapshot", None)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _export_html(
        self,
        output_path: str,
        metrics: CoverageMetrics,
        deficiencies: Sequence[Deficiency],
        include_screenshots: bool,  # noqa: ARG002 - Reserved for future use
    ) -> None:
        """Export results to HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PathTracker Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .metric {{ margin: 10px 0; }}
        .metric-label {{ font-weight: bold; }}
        .deficiency {{ border: 1px solid #ddd; padding: 10px; margin: 10px 0; }}
        .critical {{ border-color: #f44336; }}
        .high {{ border-color: #ff9800; }}
        .medium {{ border-color: #ffeb3b; }}
    </style>
</head>
<body>
    <h1>PathTracker Coverage Report</h1>

    <h2>Coverage Metrics</h2>
    <div class="metric">
        <span class="metric-label">State Coverage:</span> {metrics.state_coverage_percent:.1f}%
    </div>
    <div class="metric">
        <span class="metric-label">Transition Coverage:</span> {metrics.transition_coverage_percent:.1f}%
    </div>
    <div class="metric">
        <span class="metric-label">Success Rate:</span> {metrics.success_rate_percent:.1f}%
    </div>

    <h2>Deficiencies ({len(deficiencies)})</h2>
"""

        for deficiency in deficiencies:
            html += f"""
    <div class="deficiency {deficiency.severity.value}">
        <h3>[{deficiency.severity.value.upper()}] {deficiency.title}</h3>
        <p>{deficiency.description}</p>
        <p><strong>Occurrences:</strong> {deficiency.occurrence_count}</p>
    </div>
"""

        html += """
</body>
</html>
"""

        with open(output_path, "w") as f:
            f.write(html)

    def _export_csv(
        self,
        output_path: str,
        executions: Sequence[TransitionExecution],
    ) -> None:
        """Export execution results to CSV."""
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "execution_id",
                    "from_state",
                    "to_state",
                    "status",
                    "duration_ms",
                    "timestamp",
                ]
            )

            for execution in executions:
                writer.writerow(
                    [
                        execution.execution_id,
                        execution.from_state,
                        execution.to_state,
                        execution.status.value,
                        execution.duration_ms,
                        execution.timestamp.isoformat(),
                    ]
                )

    def _export_markdown(
        self,
        output_path: str,
        metrics: CoverageMetrics,
        deficiencies: Sequence[Deficiency],
    ) -> None:
        """Export results to Markdown."""
        md = f"""# PathTracker Report

## Coverage Metrics

- **State Coverage**: {metrics.state_coverage_percent:.1f}%
- **Transition Coverage**: {metrics.transition_coverage_percent:.1f}%
- **Success Rate**: {metrics.success_rate_percent:.1f}%

## Deficiencies

"""
        for deficiency in deficiencies:
            md += f"### [{deficiency.severity.value.upper()}] {deficiency.title}\n\n"
            md += f"{deficiency.description}\n\n"

        with open(output_path, "w") as f:
            f.write(md)
