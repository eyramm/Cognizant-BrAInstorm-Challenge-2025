"""
Workflow Configuration
Define which steps are enabled for each workflow
"""

# Product Scan Workflow Configuration
PRODUCT_SCAN_WORKFLOW = {
    "steps": {
        "check_database": {
            "enabled": True,
            "description": "Check if product exists in internal database"
        },
        "fetch_external_api": {
            "enabled": True,
            "description": "Fetch from Open Food Facts if not in database"
        },
        "update_database": {
            "enabled": True,
            "description": "Save fetched product data to database"
        },
        "calculate_scores": {
            "enabled": True,  # Set to False to skip scoring
            "description": "Calculate sustainability scores"
        },
        "find_similar_products": {
            "enabled": True,  # Set to False to skip similar products
            "description": "Find similar products in same category"
        },
        "make_recommendations": {
            "enabled": True,  # Set to False to skip recommendations
            "description": "Generate product recommendations"
        }
    },

    # Workflow behavior settings
    "settings": {
        "similar_products_limit": 5,
        "recommendations_limit": 3,
        "cache_ttl_seconds": 3600,  # How long to cache results
        "fail_on_api_error": False,  # Continue workflow if API fails
    }
}


def is_step_enabled(workflow_name: str, step_name: str) -> bool:
    """Check if a workflow step is enabled"""
    if workflow_name == "product_scan":
        config = PRODUCT_SCAN_WORKFLOW
        return config["steps"].get(step_name, {}).get("enabled", False)
    return False


def get_workflow_setting(workflow_name: str, setting_name: str):
    """Get a workflow setting value"""
    if workflow_name == "product_scan":
        config = PRODUCT_SCAN_WORKFLOW
        return config["settings"].get(setting_name)
    return None
