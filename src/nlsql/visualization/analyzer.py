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
            "annotations": []
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
                    "annotations": []
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
        
        # Find SELECT columns.
        select_tokens = []
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                select_tokens.extend(token.get_identifiers())
            elif isinstance(token, sqlparse.sql.Identifier):
                select_tokens.append(token)
        
        for token in select_tokens:
            token_str = str(token).lower()
            
            # Time-based columns for x-axis.
            if any(term in token_str for term in ['date', 'time', 'year', 'month']):
                axes['x'] = str(token)
            
            # Numeric columns for y-axis.
            elif any(term in token_str for term in ['count', 'sum', 'avg', 'amount', 'total']):
                axes['y'] = str(token)
            
            # Categorical columns for grouping.
            elif any(term in token_str for term in ['category', 'type', 'status', 'group']):
                axes['group'] = str(token)
        
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
