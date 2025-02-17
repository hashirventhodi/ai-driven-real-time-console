from typing import Dict, Any, List
import re
import sqlparse
from ..core.logging import setup_logging

logger = setup_logging(__name__)

class VisualizationAnalyzer:
    """Analyzes queries to determine appropriate visualizations."""
    
    def __init__(self):
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
        Analyze query to determine all possible visualization options.
        
        Args:
            query_text: Original natural language query.
            sql_query: Generated SQL query.
            
        Returns:
            Dictionary with an "options" key containing a list of visualization configurations.
        """
        options = []
        
        # Always include the default table visualization.
        default_config = {
            "type": "table",
            "settings": {
                "pagination": True,
                "sortable": True,
                "searchable": True
            },
            "axes": {},
            "annotations": [],
        }
        options.append(default_config)
        
        query_lower = query_text.lower()
        # Iterate over each visualization pattern.
        for viz_type, pattern_info in self.viz_patterns.items():
            if re.search(pattern_info["pattern"], query_lower):
                # Create a copy of the configuration.
                config_option = {
                    "type": pattern_info["config"]["type"],
                    "settings": pattern_info["config"].get("settings", {}).copy(),
                    "axes": {},
                    "annotations": [],
                }
                # For non-table visualizations, detect axes and generate annotations.
                if config_option["type"] != "table":
                    config_option["axes"] = await self._detect_axes(sql_query)
                    config_option["annotations"] = await self._generate_annotations(
                        query_text, sql_query, config_option
                    )
                options.append(config_option)
                logger.debug(f"Added visualization option: {config_option['type']}")
        
        return {"options": options}
    
    async def _detect_axes(self, sql_query: str) -> Dict[str, str]:
        """Detect appropriate axes from SQL query."""
        parsed = sqlparse.parse(sql_query)[0]
        
        axes = {
            "x": None,
            "y": None,
            "group": None
        }
        
        # Extract GROUP BY columns
        group_by_columns = []
        group_by_found = False
        for token in parsed.tokens:
            if group_by_found:
                if isinstance(token, sqlparse.sql.IdentifierList):
                    group_by_columns.extend([str(t).strip() for t in token.get_identifiers()])
                elif isinstance(token, sqlparse.sql.Identifier):
                    group_by_columns.append(str(token).strip())
                elif isinstance(token, sqlparse.sql.Token) and token.ttype == sqlparse.tokens.Punctuation and token.value == ',':
                    continue
                else:
                    break
            if isinstance(token, sqlparse.sql.Token) and token.value.lower() == 'group by':
                group_by_found = True

        # Process SELECT clause
        select_columns = []
        in_select = False
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.Token) and token.value.upper() == 'SELECT':
                in_select = True
                continue
            if in_select:
                if isinstance(token, sqlparse.sql.IdentifierList):
                    select_columns.extend(token.get_identifiers())
                elif isinstance(token, sqlparse.sql.Identifier):
                    select_columns.append(token)
                elif isinstance(token, sqlparse.sql.Token) and token.value.upper() == 'FROM':
                    break

        # Classify SELECT columns as dimensions or measures
        dimensions = []
        measures = []
        for col in select_columns:
            col_str = str(col).lower()
            # Check if column is an aggregate function
            if re.search(r'\b(sum|count|avg|min|max)\s*\(', col_str):
                match = re.search(r'\((.*?)\)', col_str)
                if match:
                    measure_col = match.group(1).strip().split()[-1]  # Get column inside aggregate
                    measures.append(measure_col)
                else:
                    measures.append(col_str)
            else:
                dimensions.append(str(col).strip())

        # Assign axes based on GROUP BY and SELECT analysis
        if group_by_columns:
            axes['x'] = group_by_columns[0]
            if len(group_by_columns) > 1:
                axes['group'] = group_by_columns[1]
        elif dimensions:
            axes['x'] = dimensions[0]
            if len(dimensions) > 1:
                axes['group'] = dimensions[1]

        # Assign y-axis from measures
        if measures:
            axes['y'] = measures[0]

        # Fallback to keyword detection if axes not detected
        for col in select_columns + group_by_columns:
            col_str = str(col).lower()
            # Check for x-axis keywords (expanded list)
            x_keywords = ['date', 'time', 'year', 'month', 'day', 'name', 'department', 'category', 'product', 'employee']
            if not axes['x'] and any(kw in col_str for kw in x_keywords):
                axes['x'] = str(col)
            # Check for y-axis keywords
            y_keywords = ['count', 'sum', 'avg', 'total', 'amount', 'sales']
            if not axes['y'] and any(kw in col_str for kw in y_keywords):
                axes['y'] = str(col)
            # Check for group keywords
            group_keywords = ['category', 'type', 'status', 'group', 'region']
            if not axes['group'] and any(kw in col_str for kw in group_keywords):
                axes['group'] = str(col)

        return axes
    
    async def _generate_annotations(
        self,
        query_text: str,
        sql_query: str,
        viz_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate smart annotations for the visualization."""
        annotations = []
        
        # For line charts, add a trend line.
        if viz_config["type"] == "line":
            annotations.append({
                "type": "line",
                "mode": "trend",
                "style": {
                    "stroke": "rgba(255, 0, 0, 0.5)",
                    "strokeWidth": 2,
                    "strokeDasharray": "5,5"
                }
            })
        
        # For bar charts, add an average line.
        elif viz_config["type"] == "bar":
            annotations.append({
                "type": "line",
                "mode": "average",
                "label": "Average",
                "style": {
                    "stroke": "#666",
                    "strokeWidth": 1
                }
            })
        
        # For scatter charts, add a regression line.
        elif viz_config["type"] == "scatter":
            annotations.append({
                "type": "line",
                "mode": "regression",
                "label": "Regression Line",
                "style": {
                    "stroke": "rgba(0, 0, 255, 0.5)",
                    "strokeWidth": 2,
                    "strokeDasharray": "3,3"
                }
            })
        
        # If the query mentions a threshold, add a region highlight.
        if "threshold" in query_text.lower():
            annotations.append({
                "type": "region",
                "start": 0,  # Placeholder for actual threshold detection.
                "style": {
                    "fill": "rgba(255, 0, 0, 0.1)"
                }
            })
        
        return annotations
