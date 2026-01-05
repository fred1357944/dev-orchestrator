"""
Dev Orchestrator Dashboard - Streamlit UI for managing development projects
"""

import streamlit as st
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.project_registry import ProjectRegistry, ProjectExistsError
from src.core.process_controller import ProcessController
from src.core.port_manager import PortManager

# Page config
st.set_page_config(
    page_title="Dev Orchestrator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


@st.cache_resource
def get_registry():
    return ProjectRegistry(DATA_DIR)


@st.cache_resource
def get_controller():
    return ProcessController(DATA_DIR)


@st.cache_resource
def get_port_manager():
    return PortManager(DATA_DIR / "projects.json")


def refresh_data():
    """Clear cache and refresh data"""
    st.cache_resource.clear()


def main():
    # Sidebar
    with st.sidebar:
        st.title("Dev Orchestrator")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "導航",
            ["專案列表", "Log 監控", "新增專案", "系統狀態"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Quick actions
        st.subheader("快速操作")
        col1, col2 = st.columns(2)

        controller = get_controller()

        with col1:
            if st.button("全部啟動", use_container_width=True):
                with st.spinner("啟動中..."):
                    results = controller.start_all()
                    success = sum(1 for r in results if r.success)
                    st.success(f"已啟動 {success}/{len(results)} 個專案")
                    refresh_data()
                    time.sleep(1)
                    st.rerun()

        with col2:
            if st.button("全部停止", use_container_width=True):
                with st.spinner("停止中..."):
                    results = controller.stop_all()
                    success = sum(1 for r in results if r.success)
                    st.success(f"已停止 {success}/{len(results)} 個專案")
                    refresh_data()
                    time.sleep(1)
                    st.rerun()

        # Refresh button
        st.markdown("---")
        if st.button("重新整理", use_container_width=True):
            refresh_data()
            st.rerun()

    # Main content based on page selection
    if page == "專案列表":
        render_project_list()
    elif page == "Log 監控":
        render_log_viewer()
    elif page == "新增專案":
        render_add_project()
    elif page == "系統狀態":
        render_system_status()


def render_project_list():
    """Render the project list page"""
    st.header("專案列表")

    controller = get_controller()
    statuses = controller.get_all_status()

    if not statuses:
        st.info("還沒有註冊任何專案。點擊左側「新增專案」來開始。")
        return

    # Summary
    running = sum(1 for s in statuses if s.overall_status == "running")
    stopped = sum(1 for s in statuses if s.overall_status in ["stopped", "partial"])
    error = sum(1 for s in statuses if s.overall_status == "error")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總專案數", len(statuses))
    col2.metric("運行中", running, delta=None)
    col3.metric("已停止", stopped)
    col4.metric("錯誤", error, delta=None if error == 0 else error, delta_color="inverse")

    st.markdown("---")

    # Project cards
    for status in statuses:
        render_project_card(status, controller)


def render_project_card(status, controller):
    """Render a single project card"""
    # Determine status indicator
    if status.overall_status == "running":
        status_indicator = "[ON]"
        status_text = "運行中"
    elif status.overall_status == "stopped":
        status_indicator = "[OFF]"
        status_text = "已停止"
    elif status.overall_status == "partial":
        status_indicator = "[PARTIAL]"
        status_text = "部分運行"
    else:
        status_indicator = "[ERR]"
        status_text = "錯誤"

    with st.container():
        col1, col2, col3 = st.columns([3, 4, 2])

        with col1:
            st.subheader(f"{status_indicator} {status.display_name}")
            st.caption(f"名稱: {status.name}")

        with col2:
            # Service details
            if status.frontend:
                fe_status = "[ON]" if status.frontend.status == "online" else "[OFF]"
                st.markdown(f"**Frontend** {fe_status}: `{status.frontend.url}`")

            if status.backend:
                be_status = "[ON]" if status.backend.status == "online" else "[OFF]"
                st.markdown(f"**Backend** {be_status}: `{status.backend.url}`")

        with col3:
            # Action buttons
            if status.overall_status == "running":
                if st.button("停止", key=f"stop_{status.name}", use_container_width=True):
                    with st.spinner("停止中..."):
                        result = controller.stop_project(status.name)
                        if result.success:
                            st.success("已停止")
                        else:
                            st.error(result.message)
                        refresh_data()
                        time.sleep(0.5)
                        st.rerun()

                if st.button("重啟", key=f"restart_{status.name}", use_container_width=True):
                    with st.spinner("重啟中..."):
                        result = controller.restart_project(status.name)
                        if result.success:
                            st.success("已重啟")
                        else:
                            st.error(result.message)
                        refresh_data()
                        time.sleep(0.5)
                        st.rerun()
            else:
                if st.button("啟動", key=f"start_{status.name}", use_container_width=True):
                    with st.spinner("啟動中..."):
                        result = controller.start_project(status.name)
                        if result.success:
                            st.success("已啟動")
                        else:
                            st.error(result.message)
                        refresh_data()
                        time.sleep(0.5)
                        st.rerun()

        st.markdown("---")


def render_log_viewer():
    """Render the log viewer page"""
    st.header("Log 監控")

    registry = get_registry()
    controller = get_controller()
    projects = registry.list_projects()

    if not projects:
        st.info("還沒有註冊任何專案。")
        return

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        project_names = [p.name for p in projects]
        selected_project = st.selectbox(
            "選擇專案",
            project_names,
            key="log_project"
        )

    with col2:
        service = st.selectbox(
            "服務",
            ["backend", "frontend", "both"],
            key="log_service"
        )

    with col3:
        lines = st.number_input(
            "行數",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="log_lines"
        )

    # Auto refresh toggle
    auto_refresh = st.checkbox("自動刷新 (每 5 秒)", value=False)

    if auto_refresh:
        st.empty()  # Placeholder for auto-refresh

    # Get and display logs
    if selected_project:
        logs = controller.get_logs(selected_project, service, int(lines))

        st.code(logs, language="text")

        if auto_refresh:
            time.sleep(5)
            st.rerun()


def render_add_project():
    """Render the add project form"""
    st.header("新增專案")

    registry = get_registry()

    with st.form("add_project_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "專案名稱 *",
                placeholder="my-project",
                help="英文小寫，可用連字號"
            )

            display_name = st.text_input(
                "顯示名稱",
                placeholder="My Project",
                help="可選，用於 Dashboard 顯示"
            )

            path = st.text_input(
                "專案路徑 *",
                placeholder="/Users/you/projects/my-project",
                help="專案根目錄的絕對路徑"
            )

        with col2:
            frontend_command = st.text_input(
                "前端啟動指令",
                placeholder="npm run dev 或 streamlit run app.py",
                help="留空表示不需要前端服務"
            )

            backend_command = st.text_input(
                "後端啟動指令",
                placeholder="python main.py 或 uvicorn main:app",
                help="留空表示不需要後端服務"
            )

            tags = st.text_input(
                "標籤",
                placeholder="python, dashboard, api",
                help="用逗號分隔"
            )

        description = st.text_area(
            "描述",
            placeholder="專案描述...",
            help="可選"
        )

        submitted = st.form_submit_button("註冊專案", use_container_width=True)

        if submitted:
            if not name or not path:
                st.error("請填寫專案名稱和路徑")
            elif not frontend_command and not backend_command:
                st.error("請至少填寫一個啟動指令（前端或後端）")
            else:
                try:
                    # Parse tags
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

                    project = registry.register_project(
                        name=name.strip().lower(),
                        path=path.strip(),
                        display_name=display_name.strip() if display_name else None,
                        description=description.strip() if description else None,
                        frontend_command=frontend_command.strip() if frontend_command else None,
                        backend_command=backend_command.strip() if backend_command else None,
                        tags=tag_list
                    )

                    st.success(f"專案 '{project.name}' 已註冊！")

                    # Show allocated ports
                    if project.frontend:
                        st.info(f"前端端口: {project.frontend.port}")
                    if project.backend:
                        st.info(f"後端端口: {project.backend.port}")

                    refresh_data()

                except ProjectExistsError:
                    st.error(f"專案 '{name}' 已存在")
                except Exception as e:
                    st.error(f"註冊失敗: {e}")


def render_system_status():
    """Render the system status page"""
    st.header("系統狀態")

    port_manager = get_port_manager()
    registry = get_registry()
    controller = get_controller()

    # Port status
    st.subheader("端口使用情況")
    port_status = port_manager.get_port_status()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Frontend 端口範圍**")
        st.markdown(f"`{port_status['frontend_range']}`")
        st.markdown(f"使用率: {port_status['utilization']['frontend']}")
        st.markdown(f"已用端口: {port_status['used_ports']['frontend']}")
        st.markdown(f"下一個可用: `{port_status['next_available']['frontend']}`")

    with col2:
        st.markdown("**Backend 端口範圍**")
        st.markdown(f"`{port_status['backend_range']}`")
        st.markdown(f"使用率: {port_status['utilization']['backend']}")
        st.markdown(f"已用端口: {port_status['used_ports']['backend']}")
        st.markdown(f"下一個可用: `{port_status['next_available']['backend']}`")

    st.markdown("---")

    # Project management
    st.subheader("專案管理")

    projects = registry.list_projects()

    if projects:
        for project in projects:
            with st.expander(f"{project.display_name or project.name}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**名稱**: {project.name}")
                    st.markdown(f"**路徑**: `{project.path}`")
                    st.markdown(f"**標籤**: {', '.join(project.tags)}")

                    if project.frontend:
                        st.markdown(f"**前端**: `{project.frontend.command}` (Port: {project.frontend.port})")
                    if project.backend:
                        st.markdown(f"**後端**: `{project.backend.command}` (Port: {project.backend.port})")

                with col2:
                    if st.button("移除", key=f"remove_{project.name}", use_container_width=True):
                        # Stop first
                        controller.stop_project(project.name)
                        # Remove
                        registry.remove_project(project.name)
                        st.success(f"已移除 {project.name}")
                        refresh_data()
                        time.sleep(0.5)
                        st.rerun()
    else:
        st.info("還沒有註冊任何專案")

    st.markdown("---")

    # PM2 Status
    st.subheader("PM2 狀態")

    try:
        import subprocess
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            processes = json.loads(result.stdout)
            if processes:
                for proc in processes:
                    pm2_env = proc.get("pm2_env", {})
                    status = pm2_env.get("status", "unknown")
                    status_indicator = "[ON]" if status == "online" else "[OFF]"
                    st.markdown(f"{status_indicator} **{proc.get('name')}** - {status}")
            else:
                st.info("沒有運行中的 PM2 進程")
        else:
            st.warning("無法取得 PM2 狀態")
    except Exception as e:
        st.error(f"PM2 錯誤: {e}")


if __name__ == "__main__":
    main()
