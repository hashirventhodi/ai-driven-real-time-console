import re
import sqlparse
from typing import Dict, Any, List, Optional

from ..core.logging import setup_logging
logger = setup_logging(__name__)

class VisualizationAnalyzer:
    """Analyzes queries to determine appropriate visualizations, axes, and annotations."""

    def __init__(self):
        # Patterns to detect certain chart "intents" in the user query
        self.viz_patterns = {
            "time_series": {
                "pattern": r"\b(date|time|timestamp)\b.*\b(trend|over\s+time|evolution|growth)\b",
                "config": {
                    "type": "line",
                    "settings": {
                        "interpolation": "monotone",
                        "showPoints": True,
                        "grid": True,
                        "animations": True
                    }
                }
            },
            "distribution": {
                "pattern": r"\b(distribution|breakdown|proportion|percentage|ratio)\b",
                "config": {
                    "type": "pie",
                    "settings": {
                        "donut": True,
                        "showLabels": True,
                        "showLegend": True,
                        "gradients": True
                    }
                }
            },
            "comparison": {
                "pattern": r"\b(compare|versus|vs|difference|between)\b",
                "config": {
                    "type": "bar",
                    "settings": {
                        "grouped": True,
                        "horizontal": False,
                        "showValues": True,
                        "animations": True
                    }
                }
            },
            "correlation": {
                "pattern": r"\b(correlation|relationship|scatter|plot)\b",
                "config": {
                    "type": "scatter",
                    "settings": {
                        "showTrendline": True,
                        "showPoints": True,
                        "regressionLine": True
                    }
                }
            }
        }

    async def analyze(self, query_text: str, sql_query: str) -> Dict[str, Any]:
        """
        Analyze the user query & final SQL to propose a set of visualization configs.
        
        Returns a dict of:
            {
              "options": [
                 { type: "...", axes: {...}, annotations: [...], settings: {...} },
                 ...
              ]
            }
        """
        # Always start with a default table as the baseline
        options = [
            {
                "type": "table",
                "axes": {},
                "annotations": [],
                "settings": {
                    "pagination": True,
                    "sortable": True,
                    "searchable": True
                }
            }
        ]

        # Identify possible chart types via patterns in the user query text
        matched_types = []
        query_lower = query_text.lower()
        for viz_type, pattern_info in self.viz_patterns.items():
            if re.search(pattern_info["pattern"], query_lower):
                matched_types.append(pattern_info["config"])

        # If no patterns matched, you might still guess from the SQL structure or just keep table
        if not matched_types:
            logger.debug("No explicit chart pattern matched; returning table only.")
            return {"options": options}

        # Next, parse the SQL to detect columns, axes, etc.
        axis_info = await self._detect_axes(sql_query)

        # For each matched chart type, build a config and possibly add advanced annotations
        for chart_conf in matched_types:
            viz_config = {
                "type": chart_conf["type"],
                "settings": chart_conf.get("settings", {}).copy(),
                "axes": axis_info["axes"],  # your best guess for x, y, group
                "annotations": []
            }

            # Optionally add advanced annotations
            annotations = await self._generate_annotations(query_text, sql_query, viz_config)
            viz_config["annotations"] = annotations

            options.append(viz_config)

        return {"options": options}

    async def _detect_axes(self, sql_query: str) -> Dict[str, Any]:
        """
        Parse SQL to detect:
          - dimensions (non-aggregate columns)
          - measures (aggregate columns)
          - group-by columns
        Then guess X-axis, Y-axis, group, etc. for charting.
        """
        parsed_stmt = sqlparse.parse(sql_query)
        if not parsed_stmt:
            return {"axes": {"x": None, "y": None, "group": None}}

        stmt = parsed_stmt[0]
        axes = {"x": None, "y": None, "group": None}

        # 1. Identify GROUP BY columns
        group_by_columns = self._extract_groupby_columns(stmt)

        # 2. Identify SELECT columns (dimensions vs. measures)
        select_dims, select_measures = self._extract_select_columns(stmt)

        # 3. Basic assignment to axes
        #    - If there's a GROUP BY, that might be your X or "group" axis
        #    - If there's at least one measure, that might be Y
        if group_by_columns:
            axes["x"] = group_by_columns[0]
            if len(group_by_columns) > 1:
                axes["group"] = group_by_columns[1]
        # if no group but we have dimensions, pick the first dimension as x
        elif select_dims:
            axes["x"] = select_dims[0]
            if len(select_dims) > 1:
                axes["group"] = select_dims[1]

        # for measures, pick the first as y
        if select_measures:
            axes["y"] = select_measures[0]
        
        # Optionally refine based on known keywords or partial name matches
        # e.g. if a dimension is named "date" or "year", it's likely the x-axis
        axes = self._refine_axis_guesses(axes, select_dims + group_by_columns, select_measures)

        return {"axes": axes}

    def _extract_groupby_columns(self, stmt) -> List[str]:
        """Return all columns listed in GROUP BY from a parsed statement."""
        group_by_cols = []
        group_by_found = False

        for token in stmt.tokens:
            # Check if we hit 'GROUP BY'
            if token.ttype and token.value.lower() == 'group by':
                group_by_found = True
                continue

            if group_by_found:
                if isinstance(token, sqlparse.sql.IdentifierList):
                    for sub_token in token.get_identifiers():
                        group_by_cols.append(str(sub_token).strip())
                elif isinstance(token, sqlparse.sql.Identifier):
                    group_by_cols.append(str(token).strip())
                elif token.ttype:  # maybe punctuation
                    # stop if next clause starts
                    if token.value.lower() in ['order', 'limit', 'having', 'where', 'union', 'group']:
                        break

        return group_by_cols

    def _extract_select_columns(self, stmt) -> (List[str], List[str]):
        """
        Parse the SELECT clause to separate dimension columns vs. measure (aggregates).
        
        Returns:
          (dimension_columns, measure_columns)
        """
        in_select = False
        select_dims = []
        select_measures = []

        for token in stmt.tokens:
            if token.ttype and token.value.upper() == 'SELECT':
                in_select = True
                continue

            # End if we hit FROM or other major clause
            if in_select and token.ttype and token.value.upper() in ['FROM', 'WHERE', 'GROUP', 'ORDER', 'LIMIT']:
                break

            # If we are in SELECT, parse columns
            if in_select:
                if isinstance(token, sqlparse.sql.IdentifierList):
                    for sub_token in token.get_identifiers():
                        self._classify_column(sub_token, select_dims, select_measures)
                elif isinstance(token, sqlparse.sql.Identifier):
                    self._classify_column(token, select_dims, select_measures)

        return select_dims, select_measures

    def _classify_column(self, token, select_dims, select_measures):
        """Classify a single column token into dimension or measure."""
        col_str = str(token).lower()
        # e.g. SUM(), COUNT(), AVG(), MIN(), MAX() => measure
        if re.search(r'\b(sum|count|avg|min|max)\s*\(', col_str):
            # Attempt to find the alias if present
            # e.g. "SUM(sales) as total_sales" => measure "total_sales"
            alias_match = re.search(r'\bas\s+(\w+)$', col_str)
            if alias_match:
                measure_col = alias_match.group(1).strip()
                select_measures.append(measure_col)
            else:
                # fallback, e.g. pick entire col_str or inside the function
                func_match = re.search(r'\((.*?)\)', col_str)
                measure_col = func_match.group(1).strip() if func_match else col_str
                select_measures.append(measure_col)
        else:
            # treat as dimension
            # also check for an alias => "region as reg"
            alias_match = re.search(r'\bas\s+(\w+)$', col_str)
            if alias_match:
                dim_col = alias_match.group(1).strip()
                select_dims.append(dim_col)
            else:
                # fallback
                dim_col = str(token).strip()
                select_dims.append(dim_col)

    def _refine_axis_guesses(self, axes, dimensions, measures) -> Dict[str, Optional[str]]:
        """
        Further refine axis choices based on known keywords (e.g. 'date', 'year' => x-axis).
        This is optional, but can help pick better defaults if the query didn't specify GROUP BY.
        """
        # If x is not set or is obviously not a date, but we see a dimension named 'date' or 'year', use that
        time_keywords = ['date', 'time', 'year', 'month', 'day', 'week']
        if not axes["x"]:
            for dim in dimensions:
                if any(kw in dim.lower() for kw in time_keywords):
                    axes["x"] = dim
                    break

        # If we still have no x but at least we have some dimension
        if not axes["x"] and dimensions:
            axes["x"] = dimensions[0]

        # If we still have no y but we do have measures
        if not axes["y"] and measures:
            axes["y"] = measures[0]

        return axes

    async def _generate_annotations(self, query_text: str, sql_query: str, viz_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate advanced annotations if the user requested e.g. thresholds, trends, etc.
        
        Example approach:
          - If the user mentions "threshold" => insert a region or line annotation.
          - If the user says "show me the average", we might add a line annotation at the average.
          - If the config or pattern says "showTrendline", we add a 'regression' annotation, etc.
        """
        annotations = []
        
        text_lower = query_text.lower()

        # Example: if the user explicitly said "threshold 100" => highlight region
        threshold_match = re.search(r'\bthreshold\s+(\d+(?:\.\d+)?)\b', text_lower)
        if threshold_match:
            threshold_value = float(threshold_match.group(1))
            annotations.append({
                "type": "line",
                "mode": "threshold",
                "y": threshold_value,
                "label": f"Threshold {threshold_value}",
                "style": {
                    "stroke": "rgba(255, 0, 0, 0.7)",
                    "strokeDasharray": "5,5"
                }
            })

        # If the chart config says "showTrendline" => add a trend line annotation
        if viz_config["settings"].get("showTrendline"):
            annotations.append({
                "type": "line",
                "mode": "trend",
                "style": {
                    "stroke": "rgba(0, 0, 255, 0.5)",
                    "strokeWidth": 2,
                    "strokeDasharray": "4,4"
                }
            })

        # If the chart config says "regressionLine" => add a regression line annotation
        if viz_config["settings"].get("regressionLine"):
            annotations.append({
                "type": "line",
                "mode": "regression",
                "label": "Regression",
                "style": {
                    "stroke": "#FF00FF",
                    "strokeDasharray": "3,3"
                }
            })

        return annotations
