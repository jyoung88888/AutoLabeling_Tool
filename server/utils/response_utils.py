"""응답 생성 관련 유틸리티"""

from typing import Dict, Any, Optional


def create_response_with_notification(
    success: bool = True,
    message: str = "",
    data: Optional[Dict[str, Any]] = None,
    notification_type: str = "success"
) -> Dict[str, Any]:
    """일관된 응답 형식을 생성합니다."""
    colors = {
        "success": "#2E7D32",
        "error": "#D32F2F",
        "warning": "#FF9800"
    }
    
    response = {
        "success": success,
        "message": message,
        "showNotification": False,
        "noDefaultNotification": True,
        "topNotification": {
            "show": True,
            "message": message,
            "type": notification_type,
            "style": {
                "backgroundColor": colors.get(notification_type, colors["success"]),
                "color": "white",
                "padding": "12px 30px",
                "borderRadius": "8px",
                "fontWeight": "bold",
                "fontSize": "16px",
                "boxShadow": "0 4px 20px rgba(0,0,0,0.4)",
                "border": "1px solid rgba(255,255,255,0.2)"
            }
        }
    }
    
    if data:
        response.update(data)
    
    return response


def create_success_response(message: str = "", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """성공 응답을 생성합니다."""
    return create_response_with_notification(
        success=True,
        message=message,
        data=data,
        notification_type="success"
    )


def create_error_response(message: str = "", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """오류 응답을 생성합니다."""
    return create_response_with_notification(
        success=False,
        message=message,
        data=data,
        notification_type="error"
    )


def create_warning_response(message: str = "", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """경고 응답을 생성합니다."""
    return create_response_with_notification(
        success=True,
        message=message,
        data=data,
        notification_type="warning"
    ) 